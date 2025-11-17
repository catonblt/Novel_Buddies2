from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import subprocess
import os
import time

from utils.logger import logger

router = APIRouter()


class GitInitRequest(BaseModel):
    repo_path: str


class GitCommitRequest(BaseModel):
    repo_path: str
    message: str
    author_name: str = "Novel Writer"
    author_email: str = "writer@novelwriter.app"


class GitLogRequest(BaseModel):
    repo_path: str
    max_count: int = 20


class GitRestoreRequest(BaseModel):
    repo_path: str
    file_path: str
    commit_id: str


class CommitInfo(BaseModel):
    id: str
    message: str
    author: str
    timestamp: int


def run_git_command(cwd: str, *args) -> str:
    """Run a git command and return the output"""
    logger.debug(f"Running git command: git {' '.join(args)} in {cwd}")
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=cwd,
            capture_output=True,
            text=True,
            check=True
        )
        logger.debug(f"Git command succeeded: {result.stdout[:100]}")
        return result.stdout
    except subprocess.CalledProcessError as e:
        logger.error(f"Git command failed: {e.stderr}")
        raise HTTPException(status_code=500, detail=f"Git command failed: {e.stderr}")


@router.post("/init")
async def init_repo(request: GitInitRequest):
    """Initialize a git repository"""
    start_time = time.time()
    logger.log_request("POST", "/api/git/init", body={"repo_path": request.repo_path})

    if not os.path.exists(request.repo_path):
        logger.warning(f"Repository path not found: {request.repo_path}")
        raise HTTPException(status_code=404, detail="Directory not found")

    try:
        logger.info(f"Initializing git repository at: {request.repo_path}")
        run_git_command(request.repo_path, "init")
        run_git_command(request.repo_path, "add", ".")
        run_git_command(
            request.repo_path,
            "commit",
            "-m",
            "Initial commit: Project structure created"
        )

        logger.log_git_operation("init", request.repo_path, True)
        duration_ms = (time.time() - start_time) * 1000
        logger.log_response("POST", "/api/git/init", 200, duration_ms)
        return {"success": True, "message": "Repository initialized"}
    except Exception as e:
        logger.log_exception(e, {"repo_path": request.repo_path}, "init_repo")
        logger.log_git_operation("init", request.repo_path, False, error=str(e))
        duration_ms = (time.time() - start_time) * 1000
        logger.log_response("POST", "/api/git/init", 500, duration_ms, str(e))
        raise HTTPException(status_code=500, detail=f"Failed to initialize repository: {str(e)}")


@router.post("/commit")
async def commit_changes(request: GitCommitRequest):
    """Commit changes to the repository"""
    start_time = time.time()
    logger.log_request("POST", "/api/git/commit", body={"repo_path": request.repo_path, "message": request.message})

    if not os.path.exists(request.repo_path):
        logger.warning(f"Repository not found: {request.repo_path}")
        raise HTTPException(status_code=404, detail="Repository not found")

    try:
        # Add all changes
        run_git_command(request.repo_path, "add", ".")

        # Check if there are changes to commit
        status = run_git_command(request.repo_path, "status", "--porcelain")
        if not status.strip():
            logger.info("No changes to commit")
            logger.log_git_operation("commit", request.repo_path, True, {"details": "no_changes"})
            return {"success": True, "message": "No changes to commit"}

        # Configure user (local to this repo)
        run_git_command(request.repo_path, "config", "user.name", request.author_name)
        run_git_command(request.repo_path, "config", "user.email", request.author_email)

        # Commit
        run_git_command(request.repo_path, "commit", "-m", request.message)

        logger.log_git_operation("commit", request.repo_path, True, {"message": request.message})
        duration_ms = (time.time() - start_time) * 1000
        logger.log_response("POST", "/api/git/commit", 200, duration_ms)
        return {"success": True, "message": "Changes committed"}
    except Exception as e:
        logger.log_exception(e, {"repo_path": request.repo_path, "message": request.message}, "commit_changes")
        logger.log_git_operation("commit", request.repo_path, False, error=str(e))
        duration_ms = (time.time() - start_time) * 1000
        logger.log_response("POST", "/api/git/commit", 500, duration_ms, str(e))
        raise HTTPException(status_code=500, detail=f"Failed to commit: {str(e)}")


@router.post("/log", response_model=List[CommitInfo])
async def get_log(request: GitLogRequest):
    """Get commit history"""
    start_time = time.time()
    logger.log_request("POST", "/api/git/log", body={"repo_path": request.repo_path, "max_count": request.max_count})

    if not os.path.exists(request.repo_path):
        logger.warning(f"Repository not found: {request.repo_path}")
        raise HTTPException(status_code=404, detail="Repository not found")

    try:
        # Get log in a parseable format
        log_output = run_git_command(
            request.repo_path,
            "log",
            f"-{request.max_count}",
            "--format=%H|%s|%an|%at"
        )

        commits = []
        for line in log_output.strip().split('\n'):
            if not line:
                continue

            parts = line.split('|', 3)
            if len(parts) == 4:
                commits.append(CommitInfo(
                    id=parts[0],
                    message=parts[1],
                    author=parts[2],
                    timestamp=int(parts[3])
                ))

        logger.log_git_operation("log", request.repo_path, True, {"commits_count": len(commits)})
        duration_ms = (time.time() - start_time) * 1000
        logger.log_response("POST", "/api/git/log", 200, duration_ms)
        return commits
    except Exception as e:
        logger.log_exception(e, {"repo_path": request.repo_path}, "get_log")
        logger.log_git_operation("log", request.repo_path, False, error=str(e))
        duration_ms = (time.time() - start_time) * 1000
        logger.log_response("POST", "/api/git/log", 500, duration_ms, str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get log: {str(e)}")


@router.post("/restore")
async def restore_file(request: GitRestoreRequest):
    """Restore a file to a previous version"""
    start_time = time.time()
    logger.log_request("POST", "/api/git/restore", body={
        "repo_path": request.repo_path,
        "file_path": request.file_path,
        "commit_id": request.commit_id
    })

    if not os.path.exists(request.repo_path):
        logger.warning(f"Repository not found: {request.repo_path}")
        raise HTTPException(status_code=404, detail="Repository not found")

    try:
        run_git_command(
            request.repo_path,
            "checkout",
            request.commit_id,
            "--",
            request.file_path
        )

        logger.log_git_operation("restore", request.repo_path, True, {
            "file_path": request.file_path,
            "commit_id": request.commit_id
        })
        duration_ms = (time.time() - start_time) * 1000
        logger.log_response("POST", "/api/git/restore", 200, duration_ms)
        return {"success": True, "message": "File restored"}
    except Exception as e:
        logger.log_exception(e, {
            "repo_path": request.repo_path,
            "file_path": request.file_path,
            "commit_id": request.commit_id
        }, "restore_file")
        logger.log_git_operation("restore", request.repo_path, False, error=str(e))
        duration_ms = (time.time() - start_time) * 1000
        logger.log_response("POST", "/api/git/restore", 500, duration_ms, str(e))
        raise HTTPException(status_code=500, detail=f"Failed to restore file: {str(e)}")


@router.post("/status")
async def get_status(request: GitInitRequest):
    """Get repository status"""
    start_time = time.time()
    logger.log_request("POST", "/api/git/status", body={"repo_path": request.repo_path})

    if not os.path.exists(request.repo_path):
        logger.warning(f"Repository not found: {request.repo_path}")
        raise HTTPException(status_code=404, detail="Repository not found")

    try:
        status = run_git_command(request.repo_path, "status", "--porcelain")
        files = [line[3:] for line in status.strip().split('\n') if line]

        logger.log_git_operation("status", request.repo_path, True, {"changed_files_count": len(files)})
        duration_ms = (time.time() - start_time) * 1000
        logger.log_response("POST", "/api/git/status", 200, duration_ms)
        return {"changed_files": files}
    except Exception as e:
        logger.log_exception(e, {"repo_path": request.repo_path}, "get_status")
        logger.log_git_operation("status", request.repo_path, False, error=str(e))
        duration_ms = (time.time() - start_time) * 1000
        logger.log_response("POST", "/api/git/status", 500, duration_ms, str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}")
