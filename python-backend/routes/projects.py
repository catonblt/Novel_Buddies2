from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
import uuid
import time
import os
import shutil

from models.database import Project, get_db

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
    os.makedirs(path, exist_ok=True)

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
        os.makedirs(os.path.join(path, dir_path), exist_ok=True)

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
        with open(full_path, 'w') as f:
            f.write(content)


@router.post("", response_model=ProjectResponse)
async def create_project(project: ProjectCreate, db: Session = Depends(get_db)):
    # Check if path already exists
    if os.path.exists(project.path):
        raise HTTPException(status_code=400, detail="Project path already exists")

    # Create project in database
    db_project = Project(
        id=str(uuid.uuid4()),
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
        create_project_structure(
            project.path,
            project.premise or "",
            project.themes or "",
            project.setting or "",
            project.keyCharacters or ""
        )

        db.add(db_project)
        db.commit()
        db.refresh(db_project)

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
        db.rollback()
        if os.path.exists(project.path):
            shutil.rmtree(project.path)
        raise HTTPException(status_code=500, detail=f"Failed to create project: {str(e)}")


@router.get("", response_model=List[ProjectResponse])
async def list_projects(db: Session = Depends(get_db)):
    projects = db.query(Project).order_by(Project.updated_at.desc()).all()
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


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: str, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

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


@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project(project_id: str, update: ProjectUpdate, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    update_data = update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        # Convert camelCase to snake_case for database fields
        db_field = ''.join(['_' + c.lower() if c.isupper() else c for c in field]).lstrip('_')
        setattr(project, db_field, value)

    project.updated_at = int(time.time())
    db.commit()
    db.refresh(project)

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
