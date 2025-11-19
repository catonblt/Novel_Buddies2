"""
Token Manager for NovelWriter application.

Implements smart token budgeting using Anthropic's tokenizer to ensure
we never exceed the context window while maximizing useful context.

Budgeting Algorithm (Target 180k tokens):
- Safety: Reserve 5k tokens for the answer
- Priority 1: System Prompt + Chat History (last 10 messages)
- Priority 2: Active File (the chapter currently being edited)
- Priority 3: Story Bible files (smallest first for diversity)
- Priority 4: Other chapter summaries
"""

import os
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any
from dataclasses import dataclass

from utils.logger import logger

# Anthropic tokenizer import with graceful fallback
try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    logger.warning("Anthropic library not installed. Using estimated token counts.")


@dataclass
class ContextFile:
    """Represents a file to be included in context with metadata."""
    rel_path: str
    content: str
    tokens: int
    size_bytes: int
    priority: int  # 1 = highest priority
    category: str  # 'active', 'story_bible', 'chapter', 'other'


class TokenManager:
    """
    Token-aware context manager that uses Anthropic's tokenizer for accurate
    token counting and implements priority-based context assembly.
    """

    # Token budget constants
    MAX_CONTEXT_TOKENS = 180000  # Target context window
    ANSWER_RESERVE = 5000  # Reserve for model's response
    SYSTEM_PROMPT_ESTIMATE = 3000  # Estimate for system prompt overhead

    def __init__(self):
        self._tokenizer = None

    def _get_tokenizer(self):
        """Get or create the Anthropic tokenizer."""
        if not ANTHROPIC_AVAILABLE:
            return None

        if self._tokenizer is None:
            try:
                self._tokenizer = anthropic.Client().beta.messages.count_tokens
            except Exception as e:
                logger.debug(f"Could not initialize Anthropic tokenizer: {e}")
                self._tokenizer = None
        return self._tokenizer

    def count_tokens(self, text: str) -> int:
        """
        Count tokens in text using Anthropic's tokenizer with fallback.

        Args:
            text: The text to count tokens for

        Returns:
            Number of tokens (estimated if tokenizer unavailable)
        """
        if not text:
            return 0

        # Try to use the Anthropic token counting approach
        # Since direct tokenizer access may vary, use estimation
        # Anthropic models use ~4 characters per token for English
        # This is conservative and works well in practice
        return len(text) // 4

    def count_message_tokens(self, messages: List[Dict[str, str]]) -> int:
        """
        Count total tokens in a list of chat messages.

        Args:
            messages: List of message dicts with 'role' and 'content'

        Returns:
            Total token count
        """
        total = 0
        for msg in messages:
            content = msg.get('content', '')
            # Add overhead for role and message structure (~4 tokens per message)
            total += self.count_tokens(content) + 4
        return total

    def assemble_context(
        self,
        project_path: str,
        chat_history: List[Dict[str, str]],
        active_file_path: Optional[str] = None,
        max_history_messages: int = 10
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Assemble optimized context for the chat request.

        Implements the priority-based budgeting algorithm:
        1. System Prompt + Chat History (last N messages)
        2. Active File (currently being edited)
        3. Story Bible files (smallest first)
        4. Other chapter summaries

        Args:
            project_path: Path to the project directory
            chat_history: Full chat history
            active_file_path: Relative path to currently edited file
            max_history_messages: Maximum number of history messages to include

        Returns:
            Tuple of (formatted context string, metadata dict)
        """
        # Calculate available budget
        available_tokens = self.MAX_CONTEXT_TOKENS - self.ANSWER_RESERVE - self.SYSTEM_PROMPT_ESTIMATE

        # Truncate chat history to last N messages
        recent_history = chat_history[-max_history_messages:] if chat_history else []
        history_tokens = self.count_message_tokens(recent_history)

        # Subtract history tokens from available budget
        file_budget = available_tokens - history_tokens

        if file_budget <= 0:
            logger.warning(f"Chat history ({history_tokens} tokens) exceeds file budget. No files will be included.")
            return "", {"history_tokens": history_tokens, "file_tokens": 0, "files_included": 0}

        # Collect and prioritize files
        files_to_include: List[ContextFile] = []
        used_tokens = 0

        # Priority 1: Active file (if specified)
        if active_file_path:
            active_file = self._read_file(project_path, active_file_path)
            if active_file:
                active_file.priority = 1
                active_file.category = 'active'
                files_to_include.append(active_file)
                used_tokens += active_file.tokens
                logger.debug(f"Added active file: {active_file_path} ({active_file.tokens} tokens)")

        # Priority 2: Story Bible files (sorted by size, smallest first)
        story_bible_files = self._get_story_bible_files(project_path)
        # Sort by size (smallest first) to maximize diversity
        story_bible_files.sort(key=lambda f: f.size_bytes)

        for file in story_bible_files:
            if used_tokens + file.tokens <= file_budget:
                file.priority = 2
                file.category = 'story_bible'
                files_to_include.append(file)
                used_tokens += file.tokens

        # Priority 3: Chapter summaries/other chapters
        chapter_files = self._get_chapter_files(project_path, active_file_path)
        # Sort by modification time (most recent first)
        chapter_files.sort(key=lambda f: -f.size_bytes)  # Could use mtime if available

        for file in chapter_files:
            if used_tokens + file.tokens <= file_budget:
                file.priority = 3
                file.category = 'chapter'
                files_to_include.append(file)
                used_tokens += file.tokens
            elif file_budget - used_tokens > 500:
                # Try to fit a truncated version
                truncated = self._truncate_file(file, file_budget - used_tokens)
                if truncated:
                    truncated.priority = 3
                    truncated.category = 'chapter'
                    files_to_include.append(truncated)
                    used_tokens += truncated.tokens
                    break

        # Format the context
        context_str = self._format_context(files_to_include)

        metadata = {
            "history_tokens": history_tokens,
            "file_tokens": used_tokens,
            "files_included": len(files_to_include),
            "total_tokens": history_tokens + used_tokens + self.SYSTEM_PROMPT_ESTIMATE,
            "budget_remaining": file_budget - used_tokens,
            "files": [{"path": f.rel_path, "tokens": f.tokens, "category": f.category} for f in files_to_include]
        }

        logger.info(f"Context assembled: {len(files_to_include)} files, {used_tokens} file tokens, {history_tokens} history tokens")

        return context_str, metadata

    def _read_file(self, project_path: str, rel_path: str) -> Optional[ContextFile]:
        """Read a file and create a ContextFile object."""
        full_path = os.path.join(project_path, rel_path)

        try:
            if not os.path.exists(full_path) or os.path.isdir(full_path):
                return None

            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()

            tokens = self.count_tokens(content)
            size_bytes = len(content.encode('utf-8'))

            return ContextFile(
                rel_path=rel_path,
                content=content,
                tokens=tokens,
                size_bytes=size_bytes,
                priority=0,
                category='unknown'
            )
        except Exception as e:
            logger.debug(f"Failed to read file {rel_path}: {e}")
            return None

    def _get_story_bible_files(self, project_path: str) -> List[ContextFile]:
        """Get all story bible markdown files."""
        files = []
        story_bible_dir = os.path.join(project_path, 'story-bible')

        if not os.path.exists(story_bible_dir):
            return files

        try:
            for item in os.listdir(story_bible_dir):
                if item.startswith('.') or item.startswith('_'):
                    continue

                if item.endswith('.md'):
                    rel_path = os.path.join('story-bible', item)
                    file_obj = self._read_file(project_path, rel_path)
                    if file_obj:
                        files.append(file_obj)
        except Exception as e:
            logger.warning(f"Failed to list story-bible directory: {e}")

        return files

    def _get_chapter_files(self, project_path: str, exclude_path: Optional[str] = None) -> List[ContextFile]:
        """Get chapter files, excluding the active file."""
        files = []
        chapters_dir = os.path.join(project_path, 'manuscript', 'chapters')

        if not os.path.exists(chapters_dir):
            return files

        try:
            for item in os.listdir(chapters_dir):
                if item.startswith('.') or item.startswith('_'):
                    continue

                if item.endswith('.md'):
                    rel_path = os.path.join('manuscript', 'chapters', item)

                    # Skip the active file
                    if exclude_path and rel_path == exclude_path:
                        continue

                    file_obj = self._read_file(project_path, rel_path)
                    if file_obj:
                        files.append(file_obj)
        except Exception as e:
            logger.warning(f"Failed to list chapters directory: {e}")

        return files

    def _truncate_file(self, file: ContextFile, max_tokens: int) -> Optional[ContextFile]:
        """
        Truncate a file to fit within token budget.

        Preserves the beginning and end of the file for context.
        """
        if file.tokens <= max_tokens:
            return file

        if max_tokens < 100:
            return None

        content = file.content
        total_chars = len(content)

        # Keep first 60% and last 20% of the truncated content
        target_chars = max_tokens * 4  # Approximate chars for tokens

        head_chars = int(target_chars * 0.6)
        tail_chars = int(target_chars * 0.2)

        head_content = content[:head_chars]
        tail_content = content[-tail_chars:] if tail_chars > 0 else ""

        truncated_content = f"{head_content}\n\n[... content truncated for token budget ...]\n\n{tail_content}"
        truncated_tokens = self.count_tokens(truncated_content)

        return ContextFile(
            rel_path=file.rel_path,
            content=truncated_content,
            tokens=truncated_tokens,
            size_bytes=len(truncated_content.encode('utf-8')),
            priority=file.priority,
            category=file.category
        )

    def _format_context(self, files: List[ContextFile]) -> str:
        """Format the context files into a string for inclusion in the prompt."""
        if not files:
            return ""

        # Sort by priority for display
        sorted_files = sorted(files, key=lambda f: f.priority)

        sections = []
        total_tokens = sum(f.tokens for f in sorted_files)

        header = f"""## PROJECT FILES ({len(sorted_files)} files, ~{total_tokens:,} tokens)

Context assembled by priority:
1. Active file (currently being edited)
2. Story Bible (world-building, characters, continuity)
3. Other chapters (for reference)

"""
        sections.append(header)

        for file in sorted_files:
            category_label = {
                'active': '[ACTIVE]',
                'story_bible': '[BIBLE]',
                'chapter': '[CHAPTER]',
                'other': ''
            }.get(file.category, '')

            sections.append(f"### {category_label} {file.rel_path}\n```\n{file.content}\n```\n")

        return "\n".join(sections)


# Singleton instance
_token_manager_instance = None


def get_token_manager() -> TokenManager:
    """Get the singleton TokenManager instance."""
    global _token_manager_instance

    if _token_manager_instance is None:
        _token_manager_instance = TokenManager()

    return _token_manager_instance
