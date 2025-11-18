from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
import anthropic
import uuid
import time
import os
import json
from typing import AsyncGenerator

from models.database import Project, Message, AgentAnalysis, ContentVersion, get_db
from agents.orchestrator import (
    StoryOrchestrator,
    STORY_ADVOCATE_ORCHESTRATOR_PROMPT,
    classify_request,
    get_reviewers_for_content,
    GENERATOR_PROMPTS,
    REVIEWER_PROMPTS
)
from agents.prompts import FILE_OPERATION_INSTRUCTIONS
from agents.context_loader import build_project_context
from utils.logger import logger
from routes.file_operations import parse_file_operations

router = APIRouter()


class ChatRequest(BaseModel):
    project_id: str
    message: str
    api_key: str
    model: str = "claude-sonnet-4-5-20250929"
    autonomy_level: int = 50


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

        # Build project context with metadata
        project_context = f"""

PROJECT CONTEXT:
- Title: {project.title}
- Author: {project.author}
- Genre: {project.genre}
- Project Path: {project.path}
- Premise: {project.premise or 'Not yet defined'}
- Themes: {project.themes or 'Not yet defined'}
- Setting: {project.setting or 'Not yet defined'}

You can read and write files in the project directory. When you create or update files, specify the full path relative to the project root.
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
        system_prompt = STORY_ADVOCATE_ORCHESTRATOR_PROMPT + FILE_OPERATION_INSTRUCTIONS + project_context

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
                    "agent_type": "story_advocate"
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
