from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import os
import aiofiles

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
    return build_file_tree(request.path)


@router.post("/read", response_model=FileResponse)
async def read_file(request: FileReadRequest):
    """Read a file's contents"""
    if not os.path.exists(request.path):
        raise HTTPException(status_code=404, detail="File not found")

    if os.path.isdir(request.path):
        raise HTTPException(status_code=400, detail="Path is a directory, not a file")

    try:
        async with aiofiles.open(request.path, 'r', encoding='utf-8') as f:
            content = await f.read()
        return FileResponse(content=content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read file: {str(e)}")


@router.post("/write")
async def write_file(request: FileWriteRequest):
    """Write content to a file"""
    try:
        # Ensure parent directory exists
        parent_dir = os.path.dirname(request.path)
        if parent_dir:
            os.makedirs(parent_dir, exist_ok=True)

        async with aiofiles.open(request.path, 'w', encoding='utf-8') as f:
            await f.write(request.content)

        return {"success": True, "message": "File written successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to write file: {str(e)}")


@router.post("/delete")
async def delete_file(request: FileReadRequest):
    """Delete a file"""
    if not os.path.exists(request.path):
        raise HTTPException(status_code=404, detail="File not found")

    try:
        if os.path.isdir(request.path):
            os.rmdir(request.path)
        else:
            os.remove(request.path)

        return {"success": True, "message": "File deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete file: {str(e)}")
