from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.orm import Session
import os
import re
import subprocess
from typing import List, Optional, Tuple
from datetime import datetime
from difflib import SequenceMatcher

from models.database import get_db, Project
from utils.logger import logger
from services.memory_service import get_memory_service

router = APIRouter()


def _index_file_to_memory_background(project_id: str, file_path: str, rel_path: str, project_path: str):
    """
    Background task to index a file into project memory after file operations.

    This is wrapped in try/except to ensure file operations never fail due to memory indexing errors.
    """
    try:
        memory_service = get_memory_service()
        if not memory_service.is_available():
            return

        # Read the file content
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        memory_service.index_file(project_path, project_id, rel_path, content)
        logger.debug(f"Indexed file {rel_path} to memory for project {project_id}")
    except Exception as e:
        # Log error but don't propagate - file operation must succeed even if indexing fails
        logger.error(f"Memory indexing failed for {file_path}: {str(e)}")


def normalize_whitespace(text: str) -> str:
    """
    Normalize whitespace in text for fuzzy matching.
    - Strips leading/trailing whitespace
    - Collapses multiple spaces/tabs into single space
    - Normalizes line endings
    - Collapses multiple newlines into single newline
    """
    # Strip leading/trailing whitespace
    text = text.strip()
    # Normalize line endings to \n
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    # Collapse multiple spaces/tabs into single space (but preserve newlines)
    lines = text.split('\n')
    normalized_lines = []
    for line in lines:
        # Collapse multiple spaces/tabs within the line
        normalized_line = re.sub(r'[ \t]+', ' ', line.strip())
        normalized_lines.append(normalized_line)
    # Collapse multiple blank lines into single blank line
    text = '\n'.join(normalized_lines)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text


def find_best_match(content: str, find_text: str) -> Optional[Tuple[int, int, float]]:
    """
    Find the best matching substring in content for find_text.

    Returns:
        Tuple of (start_index, end_index, similarity_score) or None if no good match.
    """
    normalized_find = normalize_whitespace(find_text)
    normalized_content = normalize_whitespace(content)

    # First, try exact match on normalized text
    if normalized_find in normalized_content:
        # Find the corresponding position in original content
        # We need to map back to original positions
        pass

    # Use sliding window with SequenceMatcher to find best match
    find_len = len(normalized_find)
    best_match = None
    best_ratio = 0.0

    # Split content into chunks roughly the size of find_text
    # with some tolerance for length variation
    min_len = max(1, int(find_len * 0.7))
    max_len = int(find_len * 1.5)

    # Scan through content with overlapping windows
    i = 0
    content_len = len(content)

    while i < content_len:
        for window_size in range(min_len, min(max_len, content_len - i) + 1, max(1, (max_len - min_len) // 10)):
            window = content[i:i + window_size]
            normalized_window = normalize_whitespace(window)

            # Quick length check
            if abs(len(normalized_window) - len(normalized_find)) > len(normalized_find) * 0.3:
                continue

            ratio = SequenceMatcher(None, normalized_find, normalized_window).ratio()

            if ratio > best_ratio and ratio > 0.85:  # Threshold for "good enough" match
                best_ratio = ratio
                best_match = (i, i + window_size, ratio)

                # If we found a very good match, we can stop early
                if ratio > 0.98:
                    return best_match

        # Move forward, but use smaller steps for better accuracy
        i += max(1, min_len // 4)

    return best_match


def fuzzy_patch(file_content: str, find_text: str, replace_text: str) -> Tuple[bool, str, str]:
    """
    Perform a fuzzy patch operation that tolerates whitespace differences.

    This function tries to find and replace text even when there are minor
    whitespace differences between the search text and the actual content.

    Args:
        file_content: The original file content
        find_text: The text to find (may have whitespace differences)
        replace_text: The text to replace with

    Returns:
        Tuple of (success, new_content, message)
    """
    # Step 1: Try exact match first
    if find_text in file_content:
        new_content = file_content.replace(find_text, replace_text, 1)
        return True, new_content, "Exact match found and replaced"

    # Step 2: Try with stripped whitespace
    stripped_find = find_text.strip()
    if stripped_find in file_content:
        new_content = file_content.replace(stripped_find, replace_text, 1)
        return True, new_content, "Match found after stripping whitespace"

    # Step 3: Try normalized match
    normalized_find = normalize_whitespace(find_text)
    normalized_content = normalize_whitespace(file_content)

    if normalized_find in normalized_content:
        # Find the position in normalized content
        norm_start = normalized_content.find(normalized_find)
        norm_end = norm_start + len(normalized_find)

        # Map back to original content positions
        # This is approximate - we find the corresponding region
        original_start = find_original_position(file_content, normalized_content, norm_start)
        original_end = find_original_position(file_content, normalized_content, norm_end)

        if original_start is not None and original_end is not None:
            new_content = file_content[:original_start] + replace_text + file_content[original_end:]
            return True, new_content, "Match found using normalized whitespace comparison"

    # Step 4: Try fuzzy matching with similarity threshold
    best_match = find_best_match(file_content, find_text)

    if best_match:
        start, end, ratio = best_match
        matched_text = file_content[start:end]
        new_content = file_content[:start] + replace_text + file_content[end:]
        return True, new_content, f"Fuzzy match found (similarity: {ratio:.1%}). Matched text: '{matched_text[:50]}...'"

    return False, file_content, "Target text not found. Please quote the text EXACTLY as it appears in the file, including all whitespace, newlines, and punctuation."


def find_original_position(original: str, normalized: str, norm_pos: int) -> Optional[int]:
    """
    Map a position in normalized text back to the original text.

    This is an approximation that works by comparing character ratios.
    """
    if norm_pos == 0:
        return 0
    if norm_pos >= len(normalized):
        return len(original)

    # Calculate approximate position ratio
    ratio = norm_pos / len(normalized)
    approx_pos = int(ratio * len(original))

    # Adjust to find a reasonable boundary (avoid splitting words)
    # Search nearby for whitespace boundaries
    search_range = min(50, len(original) // 10)

    best_pos = approx_pos
    min_diff = float('inf')

    for offset in range(-search_range, search_range + 1):
        test_pos = approx_pos + offset
        if 0 <= test_pos <= len(original):
            # Check if this position gives us a good normalized match
            test_normalized = normalize_whitespace(original[:test_pos])
            diff = abs(len(test_normalized) - norm_pos)
            if diff < min_diff:
                min_diff = diff
                best_pos = test_pos

    return best_pos


class FileOperation(BaseModel):
    type: str  # 'create', 'update', 'delete', 'append', 'insert', 'patch'
    path: str
    content: Optional[str] = None
    reason: str
    project_id: str
    agent_type: str
    find_text: Optional[str] = None  # For patch operations
    position: Optional[str] = None  # For insert operations (e.g., "after:## Section" or "before:## Section" or line number)


class FileOperationResult(BaseModel):
    success: bool
    path: str
    message: str
    operation: str
    content: Optional[str] = None  # For read operations


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
        find_text_match = re.search(r'<find_text>(.*?)</find_text>', match, re.DOTALL)
        position_match = re.search(r'<position>(.*?)</position>', match, re.DOTALL)

        if type_match and path_match:
            op['type'] = type_match.group(1).strip()
            op['path'] = path_match.group(1).strip()
            op['content'] = content_match.group(1).strip() if content_match else ''
            op['reason'] = reason_match.group(1).strip() if reason_match else 'No reason provided'
            op['find_text'] = find_text_match.group(1).strip() if find_text_match else None
            op['position'] = position_match.group(1).strip() if position_match else None
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
    background_tasks: BackgroundTasks,
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

        elif operation.type == "append":
            # Append content to end of file
            if not os.path.exists(full_path):
                # Create file if it doesn't exist
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write(operation.content or '')
                message = f"Created {operation.path} with appended content"
            else:
                with open(full_path, 'a', encoding='utf-8') as f:
                    f.write(operation.content or '')
                message = f"Appended content to {operation.path}"

            logger.info(message)

        elif operation.type == "insert":
            # Insert content at specified position
            if not os.path.exists(full_path):
                return FileOperationResult(
                    success=False,
                    path=operation.path,
                    message=f"File not found: {operation.path}. Cannot insert into non-existent file.",
                    operation=operation.type
                )

            with open(full_path, 'r', encoding='utf-8') as f:
                existing_content = f.read()

            new_content = existing_content
            position = operation.position or "end"

            if position == "start":
                new_content = (operation.content or '') + existing_content
            elif position == "end":
                new_content = existing_content + (operation.content or '')
            elif position.startswith("after:"):
                marker = position[6:]
                if marker in existing_content:
                    new_content = existing_content.replace(marker, marker + (operation.content or ''), 1)
                else:
                    return FileOperationResult(
                        success=False,
                        path=operation.path,
                        message=f"Marker text not found: '{marker}'",
                        operation=operation.type
                    )
            elif position.startswith("before:"):
                marker = position[7:]
                if marker in existing_content:
                    new_content = existing_content.replace(marker, (operation.content or '') + marker, 1)
                else:
                    return FileOperationResult(
                        success=False,
                        path=operation.path,
                        message=f"Marker text not found: '{marker}'",
                        operation=operation.type
                    )
            elif position.isdigit():
                # Insert at specific line number
                lines = existing_content.split('\n')
                line_num = int(position) - 1  # Convert to 0-indexed
                if 0 <= line_num <= len(lines):
                    lines.insert(line_num, operation.content or '')
                    new_content = '\n'.join(lines)
                else:
                    return FileOperationResult(
                        success=False,
                        path=operation.path,
                        message=f"Invalid line number: {position}",
                        operation=operation.type
                    )

            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            message = f"Inserted content in {operation.path}"

            logger.info(message)

        elif operation.type == "patch":
            # Replace specific text in file using fuzzy matching
            if not os.path.exists(full_path):
                return FileOperationResult(
                    success=False,
                    path=operation.path,
                    message=f"File not found: {operation.path}. Cannot patch non-existent file.",
                    operation=operation.type
                )

            if not operation.find_text:
                return FileOperationResult(
                    success=False,
                    path=operation.path,
                    message="Patch operation requires find_text to specify what to replace.",
                    operation=operation.type
                )

            with open(full_path, 'r', encoding='utf-8') as f:
                existing_content = f.read()

            # Use fuzzy_patch for whitespace-tolerant matching
            success, new_content, match_message = fuzzy_patch(
                existing_content,
                operation.find_text,
                operation.content or ''
            )

            if not success:
                return FileOperationResult(
                    success=False,
                    path=operation.path,
                    message=f"Text to replace not found in file: '{operation.find_text[:50]}...'. {match_message}",
                    operation=operation.type
                )

            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            message = f"Patched {operation.path}. {match_message}"

            logger.info(message)

        else:
            raise HTTPException(status_code=400, detail=f"Invalid operation type: {operation.type}")

        # Index file to memory in background for operations that modify content
        # (create, update, append, insert, patch - but not delete)
        if operation.type != "delete":
            background_tasks.add_task(
                _index_file_to_memory_background,
                operation.project_id,
                full_path,
                operation.path,
                project.path
            )

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
    background_tasks: BackgroundTasks,
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
            result = await execute_file_operation(op, background_tasks, db)
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
            "agent_type": request.agent_type,
            "find_text": op.get('find_text'),
            "position": op.get('position')
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
