from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
import anthropic
import uuid
import time
import os
import json
from typing import AsyncGenerator, List, Dict, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path

from models.database import Project, Message, AgentAnalysis, ContentVersion, get_db
from agents.orchestrator import (
    StoryOrchestrator,
    STORY_ADVOCATE_ORCHESTRATOR_PROMPT,
    classify_request,
    get_reviewers_for_content,
    GENERATOR_PROMPTS,
    REVIEWER_PROMPTS
)
from agents.prompts import FILE_OPERATION_INSTRUCTIONS, LONG_CONTENT_INSTRUCTIONS, MEMORY_TOOL_INSTRUCTIONS
from agents.context_loader import build_project_context
from utils.logger import logger
from utils.token_manager import get_token_manager
from routes.file_operations import parse_file_operations
from services.memory_service import get_memory_service
import re

router = APIRouter()


@dataclass
class FileEntry:
    """Represents a file entry with metadata for bucket prioritization."""
    rel_path: str
    content: str
    tokens: int
    mtime: float
    bucket: str  # 'critical', 'context', 'reference'


class TokenBudgetLoader:
    """
    Token-aware context loader that uses Anthropic's tokenizer for accurate
    token counting and implements Smart Bucket priority loading.

    Bucket A (Critical): Always include planning/story-outline.md and most recently
                         modified .md file in manuscript/chapters
    Bucket B (Context): Include story-bible files until 80% of budget
    Bucket C (Reference): Include other chapters if space permits
    """

    # Default token budget for Claude Sonnet (leaving room for response)
    DEFAULT_MAX_TOKENS = 150000

    def __init__(self, project_path: str, max_tokens: int = None):
        self.project_path = project_path
        self.max_tokens = max_tokens or self.DEFAULT_MAX_TOKENS
        self._tokenizer = None

    def _get_tokenizer(self):
        """Get or create the Anthropic tokenizer."""
        if self._tokenizer is None:
            try:
                self._tokenizer = anthropic.Tokenizer()
            except Exception as e:
                logger.warning(f"Failed to create Anthropic tokenizer: {e}. Using estimate.")
                self._tokenizer = None
        return self._tokenizer

    def count_tokens(self, text: str) -> int:
        """Count tokens in text using Anthropic's tokenizer with fallback."""
        tokenizer = self._get_tokenizer()
        if tokenizer:
            try:
                return tokenizer.count_tokens(text)
            except Exception:
                pass
        # Fallback: estimate ~4 chars per token (conservative for English)
        return len(text) // 4

    def _read_file(self, rel_path: str) -> Optional[Tuple[str, float]]:
        """Read file content and return (content, modification_time)."""
        full_path = os.path.join(self.project_path, rel_path)
        try:
            if not os.path.exists(full_path) or os.path.isdir(full_path):
                return None

            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()

            mtime = os.path.getmtime(full_path)
            return content, mtime
        except Exception as e:
            logger.debug(f"Failed to read {rel_path}: {e}")
            return None

    def _truncate_file_tail_preserved(self, content: str, max_tokens: int) -> str:
        """
        Truncate file content but preserve the last 20%.
        The end of files is usually more relevant for continuity.
        """
        current_tokens = self.count_tokens(content)
        if current_tokens <= max_tokens:
            return content

        # Calculate how much to keep
        total_chars = len(content)
        # Keep last 20% always
        tail_start = int(total_chars * 0.8)
        tail_content = content[tail_start:]
        tail_tokens = self.count_tokens(tail_content)

        # Remaining budget for head
        head_tokens = max_tokens - tail_tokens - 50  # Reserve 50 tokens for markers

        if head_tokens <= 0:
            # Tail alone exceeds budget, just truncate tail
            return content[-int(total_chars * 0.3):] + "\n\n[... content truncated, showing last 30% ...]"

        # Binary search for head cutoff
        head_chars = int(head_tokens * 4)  # Estimate
        head_content = content[:head_chars]

        # Adjust if needed
        while self.count_tokens(head_content) > head_tokens and head_chars > 100:
            head_chars = int(head_chars * 0.9)
            head_content = content[:head_chars]

        return f"{head_content}\n\n[... middle content truncated ...]\n\n{tail_content}"

    def _list_md_files(self, directory: str) -> List[Tuple[str, float]]:
        """List all .md files in directory with their modification times."""
        full_dir = os.path.join(self.project_path, directory)
        files = []

        if not os.path.exists(full_dir):
            return files

        try:
            for item in os.listdir(full_dir):
                if item.startswith('.') or item.startswith('_'):
                    continue

                full_path = os.path.join(full_dir, item)
                if os.path.isfile(full_path) and item.endswith('.md'):
                    rel_path = os.path.join(directory, item)
                    mtime = os.path.getmtime(full_path)
                    files.append((rel_path, mtime))
        except Exception as e:
            logger.warning(f"Failed to list directory {directory}: {e}")

        return files

    def _get_most_recent_chapter(self) -> Optional[str]:
        """Get the most recently modified .md file in manuscript/chapters."""
        chapter_files = self._list_md_files('manuscript/chapters')
        if not chapter_files:
            return None

        # Sort by modification time, most recent first
        chapter_files.sort(key=lambda x: x[1], reverse=True)
        return chapter_files[0][0]

    def load_with_budget(self) -> str:
        """
        Load project files using Smart Bucket prioritization with token budget.

        Returns formatted context string for inclusion in prompts.
        """
        entries: List[FileEntry] = []

        # ===== BUCKET A: Critical files (always include) =====
        critical_files = [
            'planning/story-outline.md',
        ]

        # Add most recently modified chapter
        recent_chapter = self._get_most_recent_chapter()
        if recent_chapter:
            critical_files.append(recent_chapter)

        for rel_path in critical_files:
            result = self._read_file(rel_path)
            if result:
                content, mtime = result
                tokens = self.count_tokens(content)
                entries.append(FileEntry(rel_path, content, tokens, mtime, 'critical'))

        # ===== BUCKET B: Context files (story-bible, characters, planning) =====
        context_dirs = [
            ('story-bible', ['continuity.md', 'timeline.md', 'world-notes.md']),
            ('planning', ['chapter-breakdown.md', 'themes.md']),
            ('characters', None),  # All files in characters
        ]

        for directory, priority_files in context_dirs:
            if priority_files:
                # Load specific files first
                for filename in priority_files:
                    rel_path = os.path.join(directory, filename)
                    if rel_path not in [e.rel_path for e in entries]:
                        result = self._read_file(rel_path)
                        if result:
                            content, mtime = result
                            tokens = self.count_tokens(content)
                            entries.append(FileEntry(rel_path, content, tokens, mtime, 'context'))

            # Load other files from directory
            all_files = self._list_md_files(directory)
            for rel_path, mtime in all_files:
                if rel_path not in [e.rel_path for e in entries]:
                    result = self._read_file(rel_path)
                    if result:
                        content, _ = result
                        tokens = self.count_tokens(content)
                        entries.append(FileEntry(rel_path, content, tokens, mtime, 'context'))

        # ===== BUCKET C: Reference files (other chapters) =====
        chapter_files = self._list_md_files('manuscript/chapters')
        for rel_path, mtime in chapter_files:
            if rel_path not in [e.rel_path for e in entries]:
                result = self._read_file(rel_path)
                if result:
                    content, _ = result
                    tokens = self.count_tokens(content)
                    entries.append(FileEntry(rel_path, content, tokens, mtime, 'reference'))

        # Also add scenes as reference
        scene_files = self._list_md_files('manuscript/scenes')
        for rel_path, mtime in scene_files:
            result = self._read_file(rel_path)
            if result:
                content, _ = result
                tokens = self.count_tokens(content)
                entries.append(FileEntry(rel_path, content, tokens, mtime, 'reference'))

        # ===== Apply budget and build output =====
        return self._apply_budget_and_format(entries)

    def _apply_budget_and_format(self, entries: List[FileEntry]) -> str:
        """Apply token budget to entries and format output."""
        # Sort entries by bucket priority and modification time
        bucket_priority = {'critical': 0, 'context': 1, 'reference': 2}
        entries.sort(key=lambda e: (bucket_priority[e.bucket], -e.mtime))

        selected_entries: List[FileEntry] = []
        total_tokens = 0
        context_budget = int(self.max_tokens * 0.8)  # 80% for context bucket

        for entry in entries:
            # Always include critical bucket
            if entry.bucket == 'critical':
                # Truncate if necessary
                if entry.tokens > self.max_tokens // 3:
                    entry.content = self._truncate_file_tail_preserved(
                        entry.content,
                        self.max_tokens // 3
                    )
                    entry.tokens = self.count_tokens(entry.content)

                selected_entries.append(entry)
                total_tokens += entry.tokens

            # Context bucket fills up to 80% of budget
            elif entry.bucket == 'context':
                if total_tokens + entry.tokens <= context_budget:
                    selected_entries.append(entry)
                    total_tokens += entry.tokens
                elif total_tokens < context_budget:
                    # Truncate to fit
                    available = context_budget - total_tokens
                    if available > 500:  # Only include if meaningful
                        entry.content = self._truncate_file_tail_preserved(entry.content, available)
                        entry.tokens = self.count_tokens(entry.content)
                        selected_entries.append(entry)
                        total_tokens += entry.tokens

            # Reference bucket uses remaining space
            elif entry.bucket == 'reference':
                if total_tokens + entry.tokens <= self.max_tokens:
                    selected_entries.append(entry)
                    total_tokens += entry.tokens
                elif total_tokens < self.max_tokens:
                    # Truncate to fit
                    available = self.max_tokens - total_tokens
                    if available > 500:
                        entry.content = self._truncate_file_tail_preserved(entry.content, available)
                        entry.tokens = self.count_tokens(entry.content)
                        selected_entries.append(entry)
                        total_tokens += entry.tokens

        # Format output
        if not selected_entries:
            return ""

        sections = []
        for entry in selected_entries:
            sections.append(f"### File: {entry.rel_path}\n```\n{entry.content}\n```\n")

        header = f"""## PROJECT FILES ({len(selected_entries)} files, ~{total_tokens:,} tokens)

Loaded with Smart Bucket Priority:
- Critical: planning/story-outline.md + most recent chapter
- Context: story-bible, characters, planning
- Reference: other chapters and scenes

"""
        return header + "\n".join(sections)


def get_project_file_contents(project_path: str, max_tokens: int = 150000) -> str:
    """
    Read and return contents of key project files for agent context.

    Uses token-based budgeting with Smart Bucket priority:
    - Bucket A (Critical): Always include planning/story-outline.md and most recent chapter
    - Bucket B (Context): Fill to 80% with story-bible, characters, planning
    - Bucket C (Reference): Fill remainder with other chapters

    Large files are truncated but preserve the last 20% for continuity.
    """
    loader = TokenBudgetLoader(project_path, max_tokens)
    return loader.load_with_budget()


def parse_memory_searches(text: str) -> List[dict]:
    """Extract memory search requests from agent response text."""
    searches = []
    pattern = r'<memory_search>(.*?)</memory_search>'
    matches = re.findall(pattern, text, re.DOTALL)

    for match in matches:
        search = {}
        query_match = re.search(r'<query>(.*?)</query>', match, re.DOTALL)
        reason_match = re.search(r'<reason>(.*?)</reason>', match, re.DOTALL)

        if query_match:
            search['query'] = query_match.group(1).strip()
            search['reason'] = reason_match.group(1).strip() if reason_match else ''
            searches.append(search)

    return searches


def execute_memory_searches(project_path: str, project_id: str, searches: List[dict]) -> str:
    """
    Execute memory searches and return formatted results.

    Args:
        project_path: Path to the project directory
        project_id: The project identifier
        searches: List of search dictionaries with 'query' and 'reason' keys

    Returns:
        Formatted string with all search results
    """
    if not searches:
        return ""

    memory_service = get_memory_service()
    if not memory_service.is_available():
        return "\n[Memory search unavailable - ChromaDB not initialized]\n"

    results = []
    for search in searches:
        query = search.get('query', '')
        reason = search.get('reason', '')

        if not query:
            continue

        try:
            search_results = memory_service.query_project(project_path, project_id, query, n_results=5)
            results.append(f"**Memory Search: {query}**")
            if reason:
                results.append(f"*Reason: {reason}*")
            results.append(search_results)
            results.append("---")
        except Exception as e:
            logger.error(f"Memory search failed for query '{query}': {str(e)}")
            results.append(f"**Memory Search: {query}** - Error: {str(e)}")
            results.append("---")

    if results:
        return "\n\n**MEMORY SEARCH RESULTS:**\n\n" + "\n".join(results)
    return ""


class ChatRequest(BaseModel):
    project_id: str
    message: str
    api_key: str
    model: str = "claude-sonnet-4-5-20250929"
    autonomy_level: int = 50


def build_file_tree_for_agent(path: str, prefix: str = "") -> str:
    """Build a text representation of the file tree for agent context"""
    if not os.path.exists(path):
        return ""

    result = []
    try:
        items = sorted(os.listdir(path))
        # Filter hidden files except .novel-project.json
        items = [item for item in items if not item.startswith('.') or item == '.novel-project.json']

        dirs = [item for item in items if os.path.isdir(os.path.join(path, item))]
        files = [item for item in items if not os.path.isdir(os.path.join(path, item))]

        # Add directories first
        for i, dir_name in enumerate(dirs):
            is_last_dir = (i == len(dirs) - 1) and not files
            connector = "└── " if is_last_dir else "├── "
            result.append(f"{prefix}{connector}{dir_name}/")

            # Recursively add subdirectory contents
            new_prefix = prefix + ("    " if is_last_dir else "│   ")
            subtree = build_file_tree_for_agent(os.path.join(path, dir_name), new_prefix)
            if subtree:
                result.append(subtree)

        # Add files
        for i, file_name in enumerate(files):
            is_last = (i == len(files) - 1)
            connector = "└── " if is_last else "├── "
            result.append(f"{prefix}{connector}{file_name}")

    except Exception as e:
        logger.error(f"Error building file tree: {e}")

    return "\n".join(result)




async def stream_orchestrated_response(
    project: Project,
    user_message: str,
    api_key: str,
    model: str,
    autonomy_level: int,
    db: Session
) -> AsyncGenerator[str, None]:
    """Stream responses through the Story Advocate orchestrator"""
    start_time = time.time()
    logger.info(f"Starting orchestrated interaction for project {project.id}")

    try:
        client = anthropic.Anthropic(api_key=api_key)

        # Get conversation history
        messages = db.query(Message).filter(
            Message.project_id == project.id
        ).order_by(Message.timestamp.asc()).all()
        logger.log_database_operation("select", "messages", True, affected_rows=len(messages))

        conversation = []
        for msg in messages:
            conversation.append({
                "role": msg.role,
                "content": msg.content
            })

        # Add current user message
        conversation.append({
            "role": "user",
            "content": user_message
        })

        # Save user message to database
        user_msg = Message(
            id=str(uuid.uuid4()),
            project_id=project.id,
            role="user",
            content=user_message,
            timestamp=int(time.time())
        )
        db.add(user_msg)
        db.commit()
        logger.log_database_operation("insert", "messages", True)

        # Build project context with file tree and contents
        file_tree = build_file_tree_for_agent(project.path)

        # Use TokenManager for smart context assembly
        token_manager = get_token_manager()

        # Extract active file from user message if mentioned (e.g., "in chapter-01.md")
        active_file = None
        import re as re_module
        file_mention = re_module.search(r'\b(manuscript/chapters/[\w-]+\.md|story-bible/[\w-]+\.md)\b', user_message)
        if file_mention:
            active_file = file_mention.group(1)

        # Assemble context with token budgeting
        file_contents, context_metadata = token_manager.assemble_context(
            project_path=project.path,
            chat_history=conversation[:-1],  # Exclude current message
            active_file_path=active_file,
            max_history_messages=10
        )

        logger.info(f"Token budget: {context_metadata.get('total_tokens', 0)} total tokens, "
                   f"{context_metadata.get('files_included', 0)} files included")

        project_context = f"""

PROJECT CONTEXT:
- Title: {project.title}
- Author: {project.author}
- Genre: {project.genre}
- Project Path: {project.path}
- Premise: {project.premise or 'Not yet defined'}
- Themes: {project.themes or 'Not yet defined'}
- Setting: {project.setting or 'Not yet defined'}

PROJECT FILE STRUCTURE:
```
{file_tree}
```

EXISTING PROJECT FILES:
The following files exist in the project. Use this information to understand the current state of the project and to make informed updates.

{file_contents}

You can create, update, and delete files in the project directory. When you create or update files, specify the path relative to the project root.
To update an existing file, read its current content from the EXISTING PROJECT FILES section above, then provide the complete updated content in your file_operation.
"""

        # Load existing project files as context
        # Determine agent type for smart context loading
        _, primary_agents_for_context = classify_request(user_message)
        agent_type_for_context = primary_agents_for_context[0] if primary_agents_for_context else "general"

        try:
            file_context = build_project_context(
                project.path,
                agent_type=agent_type_for_context,
                user_message=user_message,
                include_file_index=True
            )
            if file_context:
                project_context += f"\n{file_context}"
                logger.info(f"Loaded project file context for agent type: {agent_type_for_context}")
        except Exception as e:
            logger.warning(f"Failed to load project file context: {str(e)}")

        # Classify the request to determine which agents to use
        content_type, primary_agents = classify_request(user_message)

        # Send initial status
        yield f"data: {json.dumps({'type': 'status', 'message': 'Story Advocate interpreting your request...', 'agent': 'story_advocate'})}\n\n"

        # Build the full system prompt for Story Advocate
        system_prompt = STORY_ADVOCATE_ORCHESTRATOR_PROMPT + FILE_OPERATION_INSTRUCTIONS + LONG_CONTENT_INSTRUCTIONS + MEMORY_TOOL_INSTRUCTIONS + project_context

        # Add routing context based on request classification
        if primary_agents:
            agent_list = ", ".join([a.replace("_", " ").title() for a in primary_agents])
            system_prompt += f"\n\nFor this request, consider utilizing: {agent_list}"

            # Send status about which agents are being engaged
            for agent in primary_agents:
                agent_name = agent.replace("_", " ").title()
                yield f"data: {json.dumps({'type': 'status', 'message': f'{agent_name} contributing...', 'agent': agent})}\n\n"

        # Get reviewers if this is substantial content
        reviewers = get_reviewers_for_content(content_type)
        if reviewers:
            reviewer_list = ", ".join([r.replace("_", " ").title() for r in reviewers])
            system_prompt += f"\n\nContent will be reviewed by: {reviewer_list}"

        # Stream response from Claude
        assistant_response = ""
        logger.log_agent_interaction("story_advocate", "stream_start", len(user_message))
        logger.info(f"Using model: {model}")

        # Send status that we're generating the response
        yield f"data: {json.dumps({'type': 'status', 'message': 'Generating response...', 'agent': 'story_advocate'})}\n\n"

        with client.messages.stream(
            model=model,
            max_tokens=4096,
            system=system_prompt,
            messages=conversation,
        ) as stream:
            for text in stream.text_stream:
                assistant_response += text
                yield f"data: {json.dumps({'type': 'content', 'content': text})}\n\n"

        duration_ms = (time.time() - start_time) * 1000
        logger.log_agent_interaction(
            "story_advocate",
            "stream_complete",
            len(user_message),
            len(assistant_response),
            duration_ms
        )

        # Save assistant message to database
        assistant_msg = Message(
            id=str(uuid.uuid4()),
            project_id=project.id,
            role="assistant",
            content=assistant_response,
            agent_type="story_advocate",
            timestamp=int(time.time())
        )
        db.add(assistant_msg)
        db.commit()
        logger.log_database_operation("insert", "messages", True)

        # Parse file operations from the response
        file_operations = parse_file_operations(assistant_response)
        if file_operations:
            # Determine if confirmation is needed based on autonomy level
            require_confirmation = autonomy_level < 50

            # Format operations for frontend
            formatted_ops = []
            for op in file_operations:
                formatted_ops.append({
                    "type": op['type'],
                    "path": op['path'],
                    "content": op.get('content', ''),
                    "reason": op['reason'],
                    "project_id": project.id,
                    "agent_type": "story_advocate",
                    "find_text": op.get('find_text'),
                    "position": op.get('position')
                })

            logger.info(f"Found {len(formatted_ops)} file operations in response, require_confirmation={require_confirmation}")

            # Send file operations to frontend
            yield f"data: {json.dumps({'type': 'file_operations', 'operations': formatted_ops, 'require_confirmation': require_confirmation})}\n\n"

        # Send completion signal
        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    except Exception as e:
        logger.log_agent_interaction("story_advocate", "stream_error", len(user_message), error=str(e))
        logger.log_exception(e, {"project_id": project.id}, "stream_orchestrated_response")
        yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"


@router.post("")
async def chat(request: ChatRequest, db: Session = Depends(get_db)):
    """Chat with the Story Advocate orchestrator"""
    logger.log_request("POST", "/api/chat", query_params={})

    project = db.query(Project).filter(Project.id == request.project_id).first()
    if not project:
        logger.warning(f"Project not found for chat: {request.project_id}")
        raise HTTPException(status_code=404, detail="Project not found")

    logger.info(f"Chat request for project {request.project_id} via Story Advocate")
    return StreamingResponse(
        stream_orchestrated_response(
            project,
            request.message,
            request.api_key,
            request.model,
            request.autonomy_level,
            db
        ),
        media_type="text/event-stream"
    )


@router.get("/{project_id}/messages")
async def get_messages(project_id: str, db: Session = Depends(get_db)):
    """Get conversation history for a project"""
    start_time = time.time()
    logger.log_request("GET", f"/api/chat/{project_id}/messages")

    try:
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            logger.warning(f"Project not found for messages: {project_id}")
            raise HTTPException(status_code=404, detail="Project not found")

        messages = db.query(Message).filter(
            Message.project_id == project_id
        ).order_by(Message.timestamp.asc()).all()
        logger.log_database_operation("select", "messages", True, affected_rows=len(messages))

        duration_ms = (time.time() - start_time) * 1000
        logger.log_response("GET", f"/api/chat/{project_id}/messages", 200, duration_ms)
        logger.info(f"Retrieved {len(messages)} messages for project {project_id}")

        return [
            {
                "id": msg.id,
                "role": msg.role,
                "content": msg.content,
                "agentType": msg.agent_type,
                "timestamp": msg.timestamp
            }
            for msg in messages
        ]
    except HTTPException:
        raise
    except Exception as e:
        logger.log_exception(e, {"project_id": project_id}, "get_messages")
        duration_ms = (time.time() - start_time) * 1000
        logger.log_response("GET", f"/api/chat/{project_id}/messages", 500, duration_ms, str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get messages: {str(e)}")
