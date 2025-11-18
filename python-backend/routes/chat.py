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
from agents.prompts import AGENT_SYSTEM_PROMPTS
from agents.pipeline import (
    pipeline,
    detect_content_type,
    should_enhance_with_literary_agents,
    format_analysis_for_display
)
from utils.logger import logger
from routes.file_operations import parse_file_operations

router = APIRouter()


class ChatRequest(BaseModel):
    project_id: str
    message: str
    agent_type: str
    api_key: str
    model: str = "claude-sonnet-4-5-20250929"  # Default to Sonnet 4.5
    autonomy_level: int = 50  # 0-100, controls file operation confirmations


async def stream_claude_response(
    project: Project,
    user_message: str,
    agent_type: str,
    api_key: str,
    model: str,
    autonomy_level: int,
    db: Session
) -> AsyncGenerator[str, None]:
    """Stream responses from Claude API"""
    start_time = time.time()
    logger.info(f"Starting agent interaction: {agent_type} for project {project.id}")

    if agent_type not in AGENT_SYSTEM_PROMPTS:
        logger.error(f"Invalid agent type requested: {agent_type}")
        raise HTTPException(status_code=400, detail=f"Invalid agent type: {agent_type}")

    system_prompt = AGENT_SYSTEM_PROMPTS[agent_type]

    # Add project context to the system prompt
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

    full_system_prompt = system_prompt + project_context

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

        # Stream response from Claude
        assistant_response = ""
        logger.log_agent_interaction(agent_type, "stream_start", len(user_message))
        logger.info(f"Using model: {model}")

        with client.messages.stream(
            model=model,
            max_tokens=4096,
            system=full_system_prompt,
            messages=conversation,
        ) as stream:
            for text in stream.text_stream:
                assistant_response += text
                # Send chunk to frontend
                yield f"data: {json.dumps({'type': 'content', 'content': text})}\n\n"

        duration_ms = (time.time() - start_time) * 1000
        logger.log_agent_interaction(
            agent_type,
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
            agent_type=agent_type,
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
                    "agent_type": agent_type
                })

            logger.info(f"Found {len(formatted_ops)} file operations in response, require_confirmation={require_confirmation}")

            # Send file operations to frontend
            yield f"data: {json.dumps({'type': 'file_operations', 'operations': formatted_ops, 'require_confirmation': require_confirmation})}\n\n"

        # Check if literary agents should process this content
        enable_literary = getattr(project, 'enable_literary_agents', True)
        content_type = detect_content_type(user_message, {})

        if enable_literary and should_enhance_with_literary_agents(content_type, assistant_response):
            try:
                logger.info(f"Running literary agents pipeline for content type: {content_type}")

                # Build project context for agents
                project_context = {
                    "title": project.title,
                    "author": project.author,
                    "genre": project.genre,
                    "premise": project.premise,
                    "themes": project.themes,
                    "setting": project.setting
                }

                # Notify that literary analysis is starting
                yield f"data: {json.dumps({'type': 'literary_analysis_start', 'content_type': content_type})}\n\n"

                # Run the pipeline
                analysis_result = await pipeline.process_story_content(
                    content=assistant_response,
                    content_type=content_type,
                    project_context=project_context,
                    api_key=api_key,
                    parallel=True
                )

                # Store analyses in database
                analysis_id = str(uuid.uuid4())
                for agent_type_name, analysis in analysis_result.get("agent_analyses", {}).items():
                    agent_analysis = AgentAnalysis(
                        id=str(uuid.uuid4()),
                        project_id=project.id,
                        content_id=analysis_id,
                        content_type=content_type,
                        agent_type=agent_type_name,
                        analysis_result=json.dumps(analysis),
                        timestamp=int(time.time())
                    )
                    db.add(agent_analysis)

                # Store content version
                content_version = ContentVersion(
                    id=str(uuid.uuid4()),
                    project_id=project.id,
                    content_type=content_type,
                    original_content=assistant_response,
                    agent_analyses_id=analysis_id,
                    timestamp=int(time.time())
                )
                db.add(content_version)
                db.commit()

                logger.log_database_operation("insert", "agent_analyses", True)
                logger.info(f"Literary analysis complete in {analysis_result.get('processing_time_seconds', 0)}s")

                # Format and send the analysis
                formatted_analysis = format_analysis_for_display(analysis_result)

                yield f"data: {json.dumps({'type': 'literary_analysis', 'analysis': formatted_analysis, 'raw_result': analysis_result})}\n\n"

            except Exception as e:
                logger.log_exception(e, {"project_id": project.id}, "literary_agents_pipeline")
                # Don't fail the entire request if literary analysis fails
                yield f"data: {json.dumps({'type': 'literary_analysis_error', 'error': str(e)})}\n\n"

        # Send completion signal
        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    except Exception as e:
        logger.log_agent_interaction(agent_type, "stream_error", len(user_message), error=str(e))
        logger.log_exception(e, {"project_id": project.id, "agent_type": agent_type}, "stream_claude_response")
        yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"


@router.post("")
async def chat(request: ChatRequest, db: Session = Depends(get_db)):
    """Chat with an AI agent"""
    logger.log_request("POST", "/api/chat", query_params={"agent_type": request.agent_type})

    project = db.query(Project).filter(Project.id == request.project_id).first()
    if not project:
        logger.warning(f"Project not found for chat: {request.project_id}")
        raise HTTPException(status_code=404, detail="Project not found")

    logger.info(f"Chat request for project {request.project_id} with agent {request.agent_type}")
    return StreamingResponse(
        stream_claude_response(
            project,
            request.message,
            request.agent_type,
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
