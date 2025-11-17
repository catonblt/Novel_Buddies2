from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import subprocess
import os

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
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=cwd,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=f"Git command failed: {e.stderr}")


@router.post("/init")
async def init_repo(request: GitInitRequest):
    """Initialize a git repository"""
    if not os.path.exists(request.repo_path):
        raise HTTPException(status_code=404, detail="Directory not found")

    try:
        run_git_command(request.repo_path, "init")
        run_git_command(request.repo_path, "add", ".")
        run_git_command(
            request.repo_path,
            "commit",
            "-m",
            "Initial commit: Project structure created"
        )
        return {"success": True, "message": "Repository initialized"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to initialize repository: {str(e)}")


@router.post("/commit")
async def commit_changes(request: GitCommitRequest):
    """Commit changes to the repository"""
    if not os.path.exists(request.repo_path):
        raise HTTPException(status_code=404, detail="Repository not found")

    try:
        # Add all changes
        run_git_command(request.repo_path, "add", ".")

        # Check if there are changes to commit
        status = run_git_command(request.repo_path, "status", "--porcelain")
        if not status.strip():
            return {"success": True, "message": "No changes to commit"}

        # Configure user (local to this repo)
        run_git_command(request.repo_path, "config", "user.name", request.author_name)
        run_git_command(request.repo_path, "config", "user.email", request.author_email)

        # Commit
        run_git_command(request.repo_path, "commit", "-m", request.message)

        return {"success": True, "message": "Changes committed"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to commit: {str(e)}")


@router.post("/log", response_model=List[CommitInfo])
async def get_log(request: GitLogRequest):
    """Get commit history"""
    if not os.path.exists(request.repo_path):
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

        return commits
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get log: {str(e)}")


@router.post("/restore")
async def restore_file(request: GitRestoreRequest):
    """Restore a file to a previous version"""
    if not os.path.exists(request.repo_path):
        raise HTTPException(status_code=404, detail="Repository not found")

    try:
        run_git_command(
            request.repo_path,
            "checkout",
            request.commit_id,
            "--",
            request.file_path
        )
        return {"success": True, "message": "File restored"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to restore file: {str(e)}")


@router.post("/status")
async def get_status(request: GitInitRequest):
    """Get repository status"""
    if not os.path.exists(request.repo_path):
        raise HTTPException(status_code=404, detail="Repository not found")

    try:
        status = run_git_command(request.repo_path, "status", "--porcelain")
        files = [line[3:] for line in status.strip().split('\n') if line]
        return {"changed_files": files}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}")
