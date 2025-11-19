"""
Memory Routes - API endpoints for the Continuity Brain (RAG) system

Provides endpoints for:
- Re-indexing project files
- Querying project memory
- Getting memory statistics
- Resetting project memory
"""

import os
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional

from models.database import get_db, Project
from services.memory_service import get_memory_service
from utils.logger import logger

router = APIRouter()


class MemoryQueryRequest(BaseModel):
    query: str
    n_results: int = 5


class MemoryQueryResponse(BaseModel):
    results: str
    query: str


def _walk_project_files(project_path: str):
    """
    Walk project directory and yield markdown files for indexing.

    Excludes:
    - Hidden files and directories (starting with .)
    - System directories like node_modules, __pycache__, etc.
    """
    excluded_dirs = {
        '.git', '.svn', '.hg',
        'node_modules', '__pycache__', '.pytest_cache',
        'venv', 'env', '.venv',
        '.idea', '.vscode',
        'chroma_db'  # Don't index the vector DB itself
    }

    text_extensions = {'.md', '.txt', '.markdown', '.rst', '.org'}

    for root, dirs, files in os.walk(project_path):
        # Filter out excluded directories
        dirs[:] = [d for d in dirs if d not in excluded_dirs and not d.startswith('.')]

        for filename in files:
            # Skip hidden files
            if filename.startswith('.'):
                continue

            # Check extension
            _, ext = os.path.splitext(filename)
            if ext.lower() not in text_extensions:
                continue

            full_path = os.path.join(root, filename)
            # Get relative path from project root
            rel_path = os.path.relpath(full_path, project_path)

            yield full_path, rel_path


async def _reindex_project_background(project_id: str, project_path: str):
    """
    Background task to re-index all project files.
    """
    memory_service = get_memory_service()

    if not memory_service.is_available():
        logger.error(f"Memory service unavailable during reindex for project {project_id}")
        return

    logger.info(f"Starting full re-index for project {project_id} at {project_path}")

    # Optional: Reset the project memory for a clean slate
    # memory_service.reset_project_memory(project_id)

    indexed_count = 0
    error_count = 0

    for full_path, rel_path in _walk_project_files(project_path):
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()

            success = memory_service.index_file(project_path, project_id, rel_path, content)
            if success:
                indexed_count += 1
            else:
                error_count += 1

        except Exception as e:
            logger.error(f"Failed to index {rel_path}: {str(e)}")
            error_count += 1

    logger.info(f"Re-index complete for project {project_id}: {indexed_count} files indexed, {error_count} errors")


@router.post("/{project_id}/reindex")
async def reindex_project(
    project_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Start a background task to re-index all project files.

    This walks the project directory and indexes all markdown files
    into the vector database for semantic search.
    """
    # Verify project exists
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if not project.path or not os.path.exists(project.path):
        raise HTTPException(status_code=400, detail="Project path not set or does not exist")

    # Check if memory service is available
    memory_service = get_memory_service()
    if not memory_service.is_available():
        raise HTTPException(
            status_code=503,
            detail="Memory service is not available. ChromaDB may not be installed."
        )

    # Add background task
    background_tasks.add_task(_reindex_project_background, project_id, project.path)

    logger.info(f"Re-index task queued for project {project_id}")

    return {
        "status": "Re-indexing started",
        "project_id": project_id,
        "message": "Files are being indexed in the background. This may take a moment for large projects."
    }


@router.post("/{project_id}/query", response_model=MemoryQueryResponse)
async def query_project_memory(
    project_id: str,
    request: MemoryQueryRequest,
    db: Session = Depends(get_db)
):
    """
    Query the project's memory for relevant content.

    Uses semantic search to find text chunks that are relevant to the query.
    """
    # Verify project exists
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    memory_service = get_memory_service()
    if not memory_service.is_available():
        raise HTTPException(
            status_code=503,
            detail="Memory service is not available. ChromaDB may not be installed."
        )

    results = memory_service.query_project(
        project_path=project.path,
        project_id=project_id,
        query_text=request.query,
        n_results=request.n_results
    )

    return MemoryQueryResponse(
        results=results,
        query=request.query
    )


@router.get("/{project_id}/stats")
async def get_memory_stats(
    project_id: str,
    db: Session = Depends(get_db)
):
    """
    Get statistics about the project's indexed memory.
    """
    # Verify project exists
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    memory_service = get_memory_service()
    stats = memory_service.get_project_stats(project.path, project_id)

    return {
        "project_id": project_id,
        **stats
    }


@router.post("/{project_id}/reset")
async def reset_project_memory(
    project_id: str,
    db: Session = Depends(get_db)
):
    """
    Reset/wipe all memory for a project.

    This deletes the entire collection, requiring a full re-index afterward.
    """
    # Verify project exists
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    memory_service = get_memory_service()
    if not memory_service.is_available():
        raise HTTPException(
            status_code=503,
            detail="Memory service is not available. ChromaDB may not be installed."
        )

    success = memory_service.reset_project_memory(project.path, project_id)

    if success:
        return {
            "status": "Memory reset successful",
            "project_id": project_id,
            "message": "All indexed content has been cleared. Run /reindex to rebuild."
        }
    else:
        raise HTTPException(
            status_code=500,
            detail="Failed to reset project memory"
        )
