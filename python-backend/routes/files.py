from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import os
import aiofiles
import time

from utils.logger import logger

router = APIRouter()


class FileInfo(BaseModel):
    name: str
    path: str
    isDirectory: bool
    size: Optional[int] = None


class FileReadRequest(BaseModel):
    path: str


class FileWriteRequest(BaseModel):
    path: str
    content: str


class FileListRequest(BaseModel):
    path: str


class FileResponse(BaseModel):
    content: str


def build_file_tree(path: str) -> List[FileInfo]:
    """Build a file tree for the given directory"""
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

            items.append(FileInfo(
                name=item,
                path=item_path,
                isDirectory=is_dir,
                size=size
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


@router.post("/write")
async def write_file(request: FileWriteRequest):
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
