from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional
import os
import aiofiles
import time

from utils.logger import logger
from services.memory_service import get_memory_service

router = APIRouter()


class FileInfo(BaseModel):
    name: str
    path: str
    isDirectory: bool
    size: Optional[int] = None
    children: Optional[List['FileInfo']] = None


# Update forward reference for recursive type
FileInfo.model_rebuild()


class FileReadRequest(BaseModel):
    path: str


class FileWriteRequest(BaseModel):
    path: str
    content: str
    project_id: Optional[str] = None  # Optional project ID for memory indexing


class FileListRequest(BaseModel):
    path: str


class FileResponse(BaseModel):
    content: str


def build_file_tree(path: str, recursive: bool = True) -> List[FileInfo]:
    """Build a file tree for the given directory

    Args:
        path: Directory path to list
        recursive: If True, recursively build children for directories
    """
    items = []

    if not os.path.exists(path):
        return items

    try:
        for item in os.listdir(path):
            item_path = os.path.join(path, item)

            # Skip hidden files and git directory
            if item.startswith('.') and item != '.novel-project.json':
                continue

            is_dir = os.path.isdir(item_path)
            size = None if is_dir else os.path.getsize(item_path)

            # Recursively build children for directories
            children = None
            if is_dir and recursive:
                children = build_file_tree(item_path, recursive=True)

            items.append(FileInfo(
                name=item,
                path=item_path,
                isDirectory=is_dir,
                size=size,
                children=children
            ))

        # Sort: directories first, then files, both alphabetically
        items.sort(key=lambda x: (not x.isDirectory, x.name.lower()))

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list directory: {str(e)}")

    return items


@router.post("/list")
async def list_files(request: FileListRequest):
    """List files in a directory"""
    start_time = time.time()
    logger.log_request("POST", "/api/files/list", body={"path": request.path})

    try:
        result = build_file_tree(request.path)
        logger.log_file_operation("list", request.path, True, {"items_count": len(result)})

        duration_ms = (time.time() - start_time) * 1000
        logger.log_response("POST", "/api/files/list", 200, duration_ms)
        return result
    except Exception as e:
        logger.log_exception(e, {"path": request.path}, "list_files")
        duration_ms = (time.time() - start_time) * 1000
        logger.log_response("POST", "/api/files/list", 500, duration_ms, str(e))
        raise


@router.post("/read", response_model=FileResponse)
async def read_file(request: FileReadRequest):
    """Read a file's contents"""
    start_time = time.time()
    logger.log_request("POST", "/api/files/read", body={"path": request.path})

    if not os.path.exists(request.path):
        logger.warning(f"File not found: {request.path}")
        logger.log_file_operation("read", request.path, False, error="File not found")
        raise HTTPException(status_code=404, detail="File not found")

    if os.path.isdir(request.path):
        logger.warning(f"Attempted to read directory as file: {request.path}")
        logger.log_file_operation("read", request.path, False, error="Path is a directory")
        raise HTTPException(status_code=400, detail="Path is a directory, not a file")

    try:
        async with aiofiles.open(request.path, 'r', encoding='utf-8') as f:
            content = await f.read()

        logger.log_file_operation("read", request.path, True, {"size": len(content)})
        duration_ms = (time.time() - start_time) * 1000
        logger.log_response("POST", "/api/files/read", 200, duration_ms)
        return FileResponse(content=content)
    except Exception as e:
        logger.log_exception(e, {"path": request.path}, "read_file")
        logger.log_file_operation("read", request.path, False, error=str(e))
        duration_ms = (time.time() - start_time) * 1000
        logger.log_response("POST", "/api/files/read", 500, duration_ms, str(e))
        raise HTTPException(status_code=500, detail=f"Failed to read file: {str(e)}")


def _index_file_to_memory(project_id: str, file_path: str, content: str, project_path: str):
    """
    Background task to index a file into project memory.

    This is wrapped in try/except to ensure file saves never fail due to memory indexing errors.
    """
    try:
        memory_service = get_memory_service()
        if not memory_service.is_available():
            return

        # Get relative path from project root
        if project_path and file_path.startswith(project_path):
            rel_path = os.path.relpath(file_path, project_path)
        else:
            rel_path = os.path.basename(file_path)

        memory_service.index_file(project_id, rel_path, content)
        logger.debug(f"Indexed file {rel_path} to memory for project {project_id}")
    except Exception as e:
        # Log error but don't propagate - file save must succeed even if indexing fails
        logger.error(f"Memory indexing failed for {file_path}: {str(e)}")


@router.post("/write")
async def write_file(request: FileWriteRequest, background_tasks: BackgroundTasks):
    """Write content to a file"""
    start_time = time.time()
    logger.log_request("POST", "/api/files/write", body={"path": request.path, "content_size": len(request.content)})

    try:
        # Ensure parent directory exists
        parent_dir = os.path.dirname(request.path)
        if parent_dir:
            os.makedirs(parent_dir, exist_ok=True)

        async with aiofiles.open(request.path, 'w', encoding='utf-8') as f:
            await f.write(request.content)

        logger.log_file_operation("write", request.path, True, {"size": len(request.content)})

        # Index file to memory in background (if project_id is provided)
        # This runs AFTER the response is sent, so failures don't affect the save
        if request.project_id:
            # Extract project path from file path (assume project_id maps to a parent directory)
            # For more robust handling, we'd query the database for the project path
            project_path = parent_dir
            background_tasks.add_task(
                _index_file_to_memory,
                request.project_id,
                request.path,
                request.content,
                project_path
            )

        duration_ms = (time.time() - start_time) * 1000
        logger.log_response("POST", "/api/files/write", 200, duration_ms)
        return {"success": True, "message": "File written successfully"}
    except Exception as e:
        logger.log_exception(e, {"path": request.path}, "write_file")
        logger.log_file_operation("write", request.path, False, {"size": len(request.content)}, str(e))
        duration_ms = (time.time() - start_time) * 1000
        logger.log_response("POST", "/api/files/write", 500, duration_ms, str(e))
        raise HTTPException(status_code=500, detail=f"Failed to write file: {str(e)}")


@router.post("/delete")
async def delete_file(request: FileReadRequest):
    """Delete a file"""
    start_time = time.time()
    logger.log_request("POST", "/api/files/delete", body={"path": request.path})

    if not os.path.exists(request.path):
        logger.warning(f"File not found for deletion: {request.path}")
        logger.log_file_operation("delete", request.path, False, error="File not found")
        raise HTTPException(status_code=404, detail="File not found")

    try:
        is_dir = os.path.isdir(request.path)
        if is_dir:
            os.rmdir(request.path)
        else:
            os.remove(request.path)

        logger.log_file_operation("delete", request.path, True, {"type": "directory" if is_dir else "file"})
        duration_ms = (time.time() - start_time) * 1000
        logger.log_response("POST", "/api/files/delete", 200, duration_ms)
        return {"success": True, "message": "File deleted successfully"}
    except Exception as e:
        logger.log_exception(e, {"path": request.path}, "delete_file")
        logger.log_file_operation("delete", request.path, False, error=str(e))
        duration_ms = (time.time() - start_time) * 1000
        logger.log_response("POST", "/api/files/delete", 500, duration_ms, str(e))
        raise HTTPException(status_code=500, detail=f"Failed to delete file: {str(e)}")
