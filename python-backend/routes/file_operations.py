from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
import os
import re
import subprocess
from typing import List, Optional
from datetime import datetime

from models.database import get_db, Project
from utils.logger import logger

router = APIRouter()


class FileOperation(BaseModel):
    type: str  # 'create', 'update', 'delete'
    path: str
    content: Optional[str] = None
    reason: str
    project_id: str
    agent_type: str


class FileOperationResult(BaseModel):
    success: bool
    path: str
    message: str
    operation: str


class BatchFileOperations(BaseModel):
    operations: List[FileOperation]
    project_id: str


class ParseOperationsRequest(BaseModel):
    response_text: str
    project_id: str
    agent_type: str
    autonomy_level: int


def parse_file_operations(text: str) -> List[dict]:
    """Extract file operations from agent response text"""
    operations = []
    pattern = r'<file_operation>(.*?)</file_operation>'
    matches = re.findall(pattern, text, re.DOTALL)

    for match in matches:
        op = {}
        type_match = re.search(r'<type>(.*?)</type>', match, re.DOTALL)
        path_match = re.search(r'<path>(.*?)</path>', match, re.DOTALL)
        content_match = re.search(r'<content>(.*?)</content>', match, re.DOTALL)
        reason_match = re.search(r'<reason>(.*?)</reason>', match, re.DOTALL)

        if type_match and path_match:
            op['type'] = type_match.group(1).strip()
            op['path'] = path_match.group(1).strip()
            op['content'] = content_match.group(1).strip() if content_match else ''
            op['reason'] = reason_match.group(1).strip() if reason_match else 'No reason provided'
            operations.append(op)

    return operations


def validate_path(project_path: str, file_path: str) -> str:
    """Validate and sanitize file path to prevent directory traversal"""
    # Remove any leading slashes or dots
    clean_path = file_path.lstrip('/').lstrip('.')

    # Build full path
    full_path = os.path.normpath(os.path.join(project_path, clean_path))

    # Ensure path is within project directory
    if not full_path.startswith(os.path.normpath(project_path)):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid path: {file_path}. Path must be within project directory."
        )

    return full_path


def commit_changes(project_path: str, message: str, agent_type: str):
    """Commit file changes to git if enabled"""
    try:
        # Check if git repo exists
        git_dir = os.path.join(project_path, '.git')
        if not os.path.exists(git_dir):
            logger.info(f"No git repo found at {project_path}, skipping commit")
            return

        # Add all changes
        subprocess.run(
            ['git', 'add', '-A'],
            cwd=project_path,
            check=True,
            capture_output=True
        )

        # Commit with message
        commit_message = f"[{agent_type}] {message}"
        result = subprocess.run(
            ['git', 'commit', '-m', commit_message],
            cwd=project_path,
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            logger.info(f"Git commit successful: {commit_message}")
        else:
            # No changes to commit is not an error
            if "nothing to commit" in result.stdout or "nothing to commit" in result.stderr:
                logger.info("No changes to commit")
            else:
                logger.warning(f"Git commit failed: {result.stderr}")

    except subprocess.CalledProcessError as e:
        logger.error(f"Git operation failed: {e.stderr}")
    except Exception as e:
        logger.error(f"Failed to commit changes: {str(e)}")


@router.post("/execute", response_model=FileOperationResult)
async def execute_file_operation(
    operation: FileOperation,
    db: Session = Depends(get_db)
):
    """Execute a single file operation"""
    logger.info(f"Executing file operation: {operation.type} on {operation.path}")

    # Get project
    project = db.query(Project).filter(Project.id == operation.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Validate and build full path
    full_path = validate_path(project.path, operation.path)

    try:
        if operation.type == "create":
            # Create parent directories if needed
            os.makedirs(os.path.dirname(full_path), exist_ok=True)

            # Check if file already exists
            if os.path.exists(full_path):
                return FileOperationResult(
                    success=False,
                    path=operation.path,
                    message=f"File already exists: {operation.path}. Use 'update' to modify it.",
                    operation=operation.type
                )

            # Write file
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(operation.content or '')

            message = f"Created {operation.path}"
            logger.info(message)

        elif operation.type == "update":
            # Check if file exists
            if not os.path.exists(full_path):
                # Create it instead
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write(operation.content or '')
                message = f"Created {operation.path} (file did not exist)"
            else:
                # Update file
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write(operation.content or '')
                message = f"Updated {operation.path}"

            logger.info(message)

        elif operation.type == "delete":
            if os.path.exists(full_path):
                os.remove(full_path)
                message = f"Deleted {operation.path}"
            else:
                message = f"File not found (already deleted?): {operation.path}"

            logger.info(message)

        else:
            raise HTTPException(status_code=400, detail=f"Invalid operation type: {operation.type}")

        return FileOperationResult(
            success=True,
            path=operation.path,
            message=message,
            operation=operation.type
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"File operation failed: {str(e)}")
        return FileOperationResult(
            success=False,
            path=operation.path,
            message=f"Operation failed: {str(e)}",
            operation=operation.type
        )


@router.post("/batch")
async def execute_batch_operations(
    batch: BatchFileOperations,
    auto_commit: bool = True,
    db: Session = Depends(get_db)
):
    """Execute multiple file operations and optionally commit to git"""
    logger.info(f"Executing batch of {len(batch.operations)} file operations")

    # Get project for git commit
    project = db.query(Project).filter(Project.id == batch.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    results = []
    successful_ops = []

    for op in batch.operations:
        try:
            result = await execute_file_operation(op, db)
            results.append(result.dict())
            if result.success:
                successful_ops.append(op)
        except Exception as e:
            results.append({
                "success": False,
                "path": op.path,
                "message": str(e),
                "operation": op.type
            })

    # Commit all changes if auto_commit is enabled
    if auto_commit and successful_ops:
        # Create commit message from operations
        if len(successful_ops) == 1:
            commit_msg = successful_ops[0].reason
        else:
            commit_msg = f"Multiple file operations ({len(successful_ops)} files)"

        agent_type = batch.operations[0].agent_type if batch.operations else "unknown"
        commit_changes(project.path, commit_msg, agent_type)

    return {
        "results": results,
        "total": len(batch.operations),
        "successful": len([r for r in results if r.get("success", False)])
    }


@router.post("/parse")
async def parse_operations_from_response(
    request: ParseOperationsRequest,
    db: Session = Depends(get_db)
):
    """Parse file operations from agent response text"""
    logger.info(f"Parsing file operations from response for project {request.project_id}")

    # Get project
    project = db.query(Project).filter(Project.id == request.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Parse operations from response
    operations = parse_file_operations(request.response_text)

    if not operations:
        return {
            "operations": [],
            "require_confirmation": False,
            "message": "No file operations found in response"
        }

    # Determine if confirmation is needed based on autonomy level
    # < 50 = always confirm, >= 50 = auto-execute
    require_confirmation = request.autonomy_level < 50

    # Format operations for frontend
    formatted_ops = []
    for op in operations:
        formatted_ops.append({
            "type": op['type'],
            "path": op['path'],
            "content": op.get('content', ''),
            "reason": op['reason'],
            "project_id": request.project_id,
            "agent_type": request.agent_type
        })

    logger.info(f"Found {len(formatted_ops)} file operations, require_confirmation={require_confirmation}")

    return {
        "operations": formatted_ops,
        "require_confirmation": require_confirmation,
        "message": f"Found {len(formatted_ops)} file operation(s)"
    }


@router.get("/validate/{project_id}")
async def validate_project_path(
    project_id: str,
    file_path: str,
    db: Session = Depends(get_db)
):
    """Validate if a file path is valid within the project"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    try:
        full_path = validate_path(project.path, file_path)
        exists = os.path.exists(full_path)
        is_directory = os.path.isdir(full_path) if exists else False

        return {
            "valid": True,
            "full_path": full_path,
            "exists": exists,
            "is_directory": is_directory
        }
    except HTTPException as e:
        return {
            "valid": False,
            "error": e.detail
        }
