from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
import uuid
import time
import os
import shutil
import json

from models.database import Project, get_db
from utils.logger import logger

router = APIRouter()


class ProjectCreate(BaseModel):
    title: str
    author: str
    genre: str
    targetWordCount: int
    path: str
    premise: Optional[str] = None
    themes: Optional[str] = None
    setting: Optional[str] = None
    keyCharacters: Optional[str] = None


class ProjectUpdate(BaseModel):
    title: Optional[str] = None
    author: Optional[str] = None
    genre: Optional[str] = None
    targetWordCount: Optional[int] = None
    premise: Optional[str] = None
    themes: Optional[str] = None
    setting: Optional[str] = None
    keyCharacters: Optional[str] = None


class ProjectLoad(BaseModel):
    path: str


class ProjectSave(BaseModel):
    project_id: str
    api_key: str
    messages: List[dict]


class ProjectResponse(BaseModel):
    id: str
    title: str
    author: str
    genre: str
    targetWordCount: int
    createdAt: int
    updatedAt: int
    path: str
    premise: Optional[str] = None
    themes: Optional[str] = None
    setting: Optional[str] = None
    keyCharacters: Optional[str] = None

    class Config:
        from_attributes = True


def create_project_structure(path: str, premise: str = "", themes: str = "", setting: str = "", key_characters: str = ""):
    """Create the project folder structure"""
    logger.info(f"Creating project structure at: {path}")

    try:
        os.makedirs(path, exist_ok=True)
        logger.log_file_operation("create_directory", path, True, {"type": "root"})
    except Exception as e:
        logger.log_file_operation("create_directory", path, False, {"type": "root"}, str(e))
        raise

    # Create directories
    dirs = [
        "planning",
        "characters",
        "manuscript/chapters",
        "manuscript/scenes",
        "story-bible",
        "research",
        "feedback",
        "exports"
    ]

    for dir_path in dirs:
        full_dir = os.path.join(path, dir_path)
        try:
            os.makedirs(full_dir, exist_ok=True)
            logger.log_file_operation("create_directory", full_dir, True, {"type": "subdirectory"})
        except Exception as e:
            logger.log_file_operation("create_directory", full_dir, False, {"type": "subdirectory"}, str(e))
            raise

    # Create initial files with content
    files = {
        ".novel-project.json": '{\n  "version": "1.0.0",\n  "type": "novel-project"\n}',
        "planning/story-outline.md": f"""# Story Outline

## Premise

{premise if premise else "To be developed..."}

## Themes

{themes if themes else "To be explored..."}

## Setting

{setting if setting else "To be defined..."}

## Key Characters

{key_characters if key_characters else "To be created..."}

## Act Structure

### Act 1 - Setup
-

### Act 2 - Confrontation
-

### Act 3 - Resolution
-
""",
        "planning/chapter-breakdown.md": """# Chapter Breakdown

## Chapter 1
- **Summary**:
- **Key Events**:
- **Characters**:
- **Word Count Goal**:

""",
        "planning/themes.md": f"""# Themes

{themes if themes else "To be explored..."}

## Primary Theme


## Secondary Themes

""",
        "characters/_character-template.md": """# Character Name

## Core Identity
- **Age**:
- **Occupation**:
- **Key Trait**:

## Psychology
Deep dive into motivations, fears, desires...

## Voice & Dialogue
Examples of how this character speaks...

## Arc
Where they start → transformation → where they end

## Relationships


## Appearance
Brief but vivid description...

## Notes

""",
        "manuscript/final-manuscript.md": """# Final Manuscript

This file will contain the compiled manuscript.

""",
        "story-bible/continuity.md": """# Continuity Bible

Track all established facts, details, and world-building elements here.

## Established Facts


## Character Details


## World-Building

""",
        "story-bible/timeline.md": """# Timeline

Track the chronology of events in your story.

## Story Timeline


## Character Timelines

""",
        "story-bible/world-notes.md": """# World Notes

Detailed notes about the setting and world.

""",
        "feedback/editorial-notes.md": """# Editorial Notes

Notes and feedback from the Editorial Reviewer will appear here.

""",
        "feedback/revision-log.md": """# Revision Log

Track changes and revisions made to the manuscript.

""",
    }

    for file_path, content in files.items():
        full_path = os.path.join(path, file_path)
        try:
            # Use UTF-8 encoding to support Unicode characters on all platforms (especially Windows)
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            logger.log_file_operation("write", full_path, True, {"size": len(content)})
        except Exception as e:
            logger.log_file_operation("write", full_path, False, {"size": len(content)}, str(e))
            raise


@router.post("", response_model=ProjectResponse)
async def create_project(project: ProjectCreate, db: Session = Depends(get_db)):
    start_time = time.time()
    logger.info(f"Creating new project: {project.title}")
    logger.log_request("POST", "/api/projects", query_params={"title": project.title, "genre": project.genre})

    # Check if path already exists
    if os.path.exists(project.path):
        logger.error(f"Project path already exists: {project.path}")
        raise HTTPException(
            status_code=400,
            detail=f"A project already exists at this location: {project.path}. Please choose a different name or delete the existing folder."
        )

    # Create project in database
    project_id = str(uuid.uuid4())
    db_project = Project(
        id=project_id,
        title=project.title,
        author=project.author,
        genre=project.genre,
        target_word_count=project.targetWordCount,
        created_at=int(time.time()),
        updated_at=int(time.time()),
        path=project.path,
        premise=project.premise,
        themes=project.themes,
        setting=project.setting,
        key_characters=project.keyCharacters
    )

    try:
        # Create project structure
        logger.info(f"Creating project structure for: {project_id}")
        create_project_structure(
            project.path,
            project.premise or "",
            project.themes or "",
            project.setting or "",
            project.keyCharacters or ""
        )

        logger.log_database_operation("insert", "projects", True)
        db.add(db_project)
        db.commit()
        db.refresh(db_project)

        duration_ms = (time.time() - start_time) * 1000
        logger.log_response("POST", "/api/projects", 200, duration_ms)
        logger.info(f"Project created successfully: {project_id} at {project.path}")

        return ProjectResponse(
            id=db_project.id,
            title=db_project.title,
            author=db_project.author,
            genre=db_project.genre,
            targetWordCount=db_project.target_word_count,
            createdAt=db_project.created_at,
            updatedAt=db_project.updated_at,
            path=db_project.path,
            premise=db_project.premise,
            themes=db_project.themes,
            setting=db_project.setting,
            keyCharacters=db_project.key_characters
        )
    except Exception as e:
        # Rollback and cleanup if something goes wrong
        logger.log_exception(e, {"project_id": project_id, "path": project.path}, "create_project")
        logger.log_database_operation("insert", "projects", False, error=str(e))

        db.rollback()
        if os.path.exists(project.path):
            logger.info(f"Cleaning up failed project directory: {project.path}")
            shutil.rmtree(project.path)

        duration_ms = (time.time() - start_time) * 1000
        logger.log_response("POST", "/api/projects", 500, duration_ms, str(e))
        raise HTTPException(status_code=500, detail=f"Failed to create project: {str(e)}")


@router.get("", response_model=List[ProjectResponse])
async def list_projects(db: Session = Depends(get_db)):
    start_time = time.time()
    logger.log_request("GET", "/api/projects")

    try:
        projects = db.query(Project).order_by(Project.updated_at.desc()).all()
        logger.log_database_operation("select", "projects", True, affected_rows=len(projects))

        duration_ms = (time.time() - start_time) * 1000
        logger.log_response("GET", "/api/projects", 200, duration_ms)
        logger.info(f"Listed {len(projects)} projects")

        return [
            ProjectResponse(
                id=p.id,
                title=p.title,
                author=p.author,
                genre=p.genre,
                targetWordCount=p.target_word_count,
                createdAt=p.created_at,
                updatedAt=p.updated_at,
                path=p.path,
                premise=p.premise,
                themes=p.themes,
                setting=p.setting,
                keyCharacters=p.key_characters
            )
            for p in projects
        ]
    except Exception as e:
        logger.log_exception(e, operation="list_projects")
        duration_ms = (time.time() - start_time) * 1000
        logger.log_response("GET", "/api/projects", 500, duration_ms, str(e))
        raise HTTPException(status_code=500, detail=f"Failed to list projects: {str(e)}")


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: str, db: Session = Depends(get_db)):
    start_time = time.time()
    logger.log_request("GET", f"/api/projects/{project_id}")

    try:
        project = db.query(Project).filter(Project.id == project_id).first()
        logger.log_database_operation("select", "projects", True, affected_rows=1 if project else 0)

        if not project:
            logger.warning(f"Project not found: {project_id}")
            duration_ms = (time.time() - start_time) * 1000
            logger.log_response("GET", f"/api/projects/{project_id}", 404, duration_ms, "Project not found")
            raise HTTPException(status_code=404, detail="Project not found")

        duration_ms = (time.time() - start_time) * 1000
        logger.log_response("GET", f"/api/projects/{project_id}", 200, duration_ms)

        return ProjectResponse(
            id=project.id,
            title=project.title,
            author=project.author,
            genre=project.genre,
            targetWordCount=project.target_word_count,
            createdAt=project.created_at,
            updatedAt=project.updated_at,
            path=project.path,
            premise=project.premise,
            themes=project.themes,
            setting=project.setting,
            keyCharacters=project.key_characters
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.log_exception(e, {"project_id": project_id}, "get_project")
        duration_ms = (time.time() - start_time) * 1000
        logger.log_response("GET", f"/api/projects/{project_id}", 500, duration_ms, str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get project: {str(e)}")


@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project(project_id: str, update: ProjectUpdate, db: Session = Depends(get_db)):
    start_time = time.time()
    logger.log_request("PATCH", f"/api/projects/{project_id}")

    try:
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            logger.warning(f"Project not found for update: {project_id}")
            duration_ms = (time.time() - start_time) * 1000
            logger.log_response("PATCH", f"/api/projects/{project_id}", 404, duration_ms, "Project not found")
            raise HTTPException(status_code=404, detail="Project not found")

        update_data = update.model_dump(exclude_unset=True)
        logger.info(f"Updating project {project_id} with fields: {list(update_data.keys())}")

        for field, value in update_data.items():
            # Convert camelCase to snake_case for database fields
            db_field = ''.join(['_' + c.lower() if c.isupper() else c for c in field]).lstrip('_')
            setattr(project, db_field, value)

        project.updated_at = int(time.time())
        db.commit()
        db.refresh(project)

        logger.log_database_operation("update", "projects", True, affected_rows=1)
        duration_ms = (time.time() - start_time) * 1000
        logger.log_response("PATCH", f"/api/projects/{project_id}", 200, duration_ms)

        return ProjectResponse(
            id=project.id,
            title=project.title,
            author=project.author,
            genre=project.genre,
            targetWordCount=project.target_word_count,
            createdAt=project.created_at,
            updatedAt=project.updated_at,
            path=project.path,
            premise=project.premise,
            themes=project.themes,
            setting=project.setting,
            keyCharacters=project.key_characters
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.log_exception(e, {"project_id": project_id}, "update_project")
        logger.log_database_operation("update", "projects", False, error=str(e))
        duration_ms = (time.time() - start_time) * 1000
        logger.log_response("PATCH", f"/api/projects/{project_id}", 500, duration_ms, str(e))
        raise HTTPException(status_code=500, detail=f"Failed to update project: {str(e)}")


@router.post("/load", response_model=ProjectResponse)
async def load_project(request: ProjectLoad, db: Session = Depends(get_db)):
    """Load an existing project from a folder path"""
    start_time = time.time()
    logger.info(f"Loading project from path: {request.path}")
    logger.log_request("POST", "/api/projects/load", body={"path": request.path})

    # Validate path exists
    if not os.path.exists(request.path):
        raise HTTPException(status_code=404, detail=f"Path not found: {request.path}")

    if not os.path.isdir(request.path):
        raise HTTPException(status_code=400, detail=f"Path is not a directory: {request.path}")

    # Check for .novel-project.json
    project_file = os.path.join(request.path, ".novel-project.json")
    if not os.path.exists(project_file):
        raise HTTPException(
            status_code=400,
            detail="Not a valid Novel Writer project. Missing .novel-project.json file."
        )

    # Check if project already exists in database
    existing = db.query(Project).filter(Project.path == request.path).first()
    if existing:
        # Return existing project
        duration_ms = (time.time() - start_time) * 1000
        logger.log_response("POST", "/api/projects/load", 200, duration_ms)
        return ProjectResponse(
            id=existing.id,
            title=existing.title,
            author=existing.author,
            genre=existing.genre,
            targetWordCount=existing.target_word_count,
            createdAt=existing.created_at,
            updatedAt=existing.updated_at,
            path=existing.path,
            premise=existing.premise,
            themes=existing.themes,
            setting=existing.setting,
            keyCharacters=existing.key_characters
        )

    # Try to load project metadata from saved state
    state_file = os.path.join(request.path, ".novel-state.json")
    project_metadata = {}
    if os.path.exists(state_file):
        try:
            with open(state_file, 'r', encoding='utf-8') as f:
                state = json.load(f)
                project_metadata = state.get('project', {})
        except Exception as e:
            logger.warning(f"Failed to load project state: {e}")

    # Extract folder name as default title
    folder_name = os.path.basename(request.path)

    # Create new project entry in database
    project_id = str(uuid.uuid4())
    db_project = Project(
        id=project_id,
        title=project_metadata.get('title', folder_name),
        author=project_metadata.get('author', 'Unknown Author'),
        genre=project_metadata.get('genre', 'Fiction'),
        target_word_count=project_metadata.get('targetWordCount', 50000),
        created_at=int(time.time()),
        updated_at=int(time.time()),
        path=request.path,
        premise=project_metadata.get('premise', ''),
        themes=project_metadata.get('themes', ''),
        setting=project_metadata.get('setting', ''),
        key_characters=project_metadata.get('keyCharacters', '')
    )

    try:
        db.add(db_project)
        db.commit()
        db.refresh(db_project)

        logger.log_database_operation("insert", "projects", True)
        duration_ms = (time.time() - start_time) * 1000
        logger.log_response("POST", "/api/projects/load", 200, duration_ms)
        logger.info(f"Project loaded successfully: {project_id}")

        return ProjectResponse(
            id=db_project.id,
            title=db_project.title,
            author=db_project.author,
            genre=db_project.genre,
            targetWordCount=db_project.target_word_count,
            createdAt=db_project.created_at,
            updatedAt=db_project.updated_at,
            path=db_project.path,
            premise=db_project.premise,
            themes=db_project.themes,
            setting=db_project.setting,
            keyCharacters=db_project.key_characters
        )
    except Exception as e:
        db.rollback()
        logger.log_exception(e, {"path": request.path}, "load_project")
        duration_ms = (time.time() - start_time) * 1000
        logger.log_response("POST", "/api/projects/load", 500, duration_ms, str(e))
        raise HTTPException(status_code=500, detail=f"Failed to load project: {str(e)}")


@router.post("/{project_id}/save")
async def save_project_state(project_id: str, request: ProjectSave, db: Session = Depends(get_db)):
    """Save project state including messages and API key"""
    start_time = time.time()
    logger.info(f"Saving project state for: {project_id}")
    logger.log_request("POST", f"/api/projects/{project_id}/save")

    # Get project
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    state_file = os.path.join(project.path, ".novel-state.json")

    try:
        # Build state object
        state = {
            "version": "1.0.0",
            "savedAt": int(time.time()),
            "project": {
                "title": project.title,
                "author": project.author,
                "genre": project.genre,
                "targetWordCount": project.target_word_count,
                "premise": project.premise,
                "themes": project.themes,
                "setting": project.setting,
                "keyCharacters": project.key_characters
            },
            "api_key": request.api_key,
            "messages": request.messages
        }

        # Write state file
        with open(state_file, 'w', encoding='utf-8') as f:
            json.dump(state, f, indent=2)

        logger.log_file_operation("write", state_file, True, {"size": len(json.dumps(state))})

        # Update project updated_at timestamp
        project.updated_at = int(time.time())
        db.commit()

        duration_ms = (time.time() - start_time) * 1000
        logger.log_response("POST", f"/api/projects/{project_id}/save", 200, duration_ms)

        return {"success": True, "message": "Project state saved successfully"}
    except Exception as e:
        logger.log_exception(e, {"project_id": project_id}, "save_project_state")
        duration_ms = (time.time() - start_time) * 1000
        logger.log_response("POST", f"/api/projects/{project_id}/save", 500, duration_ms, str(e))
        raise HTTPException(status_code=500, detail=f"Failed to save project state: {str(e)}")


@router.get("/{project_id}/state")
async def get_project_state(project_id: str, db: Session = Depends(get_db)):
    """Get saved project state including messages and API key"""
    start_time = time.time()
    logger.log_request("GET", f"/api/projects/{project_id}/state")

    # Get project
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    state_file = os.path.join(project.path, ".novel-state.json")

    try:
        if not os.path.exists(state_file):
            return {"api_key": "", "messages": []}

        with open(state_file, 'r', encoding='utf-8') as f:
            state = json.load(f)

        duration_ms = (time.time() - start_time) * 1000
        logger.log_response("GET", f"/api/projects/{project_id}/state", 200, duration_ms)

        return {
            "api_key": state.get("api_key", ""),
            "messages": state.get("messages", [])
        }
    except Exception as e:
        logger.log_exception(e, {"project_id": project_id}, "get_project_state")
        duration_ms = (time.time() - start_time) * 1000
        logger.log_response("GET", f"/api/projects/{project_id}/state", 500, duration_ms, str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get project state: {str(e)}")
