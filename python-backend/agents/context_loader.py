"""
Project Context Loader Module

This module provides efficient loading of project files to give agents
comprehensive context about the story being written. It includes smart
routing to load relevant files based on agent type and request content.
"""

import os
from typing import Dict, List, Optional, Tuple
from pathlib import Path


# Maximum characters per file to prevent token overflow
MAX_FILE_CHARS = 15000
# Maximum total context characters
MAX_TOTAL_CONTEXT_CHARS = 50000
# File extensions to load
LOADABLE_EXTENSIONS = {'.md', '.txt', '.json'}


class ProjectContextLoader:
    """
    Loads and formats project files as context for agents.

    Provides intelligent loading based on agent role and request type,
    ensuring agents have the information they need without overwhelming
    the context window.
    """

    def __init__(self, project_path: str):
        self.project_path = project_path
        self._file_cache: Dict[str, str] = {}

    def _read_file_content(self, file_path: str, max_chars: int = MAX_FILE_CHARS) -> Optional[str]:
        """Read file content with size limit."""
        try:
            if not os.path.exists(file_path):
                return None
            if os.path.isdir(file_path):
                return None

            # Check extension
            ext = os.path.splitext(file_path)[1].lower()
            if ext not in LOADABLE_EXTENSIONS:
                return None

            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            if len(content) > max_chars:
                content = content[:max_chars] + "\n\n[... content truncated ...]"

            return content
        except Exception:
            return None

    def _get_relative_path(self, full_path: str) -> str:
        """Get path relative to project root."""
        return os.path.relpath(full_path, self.project_path)

    def _list_directory_files(self, dir_path: str, recursive: bool = True) -> List[str]:
        """List all loadable files in a directory."""
        files = []
        full_path = os.path.join(self.project_path, dir_path)

        if not os.path.exists(full_path):
            return files

        try:
            for item in os.listdir(full_path):
                item_path = os.path.join(full_path, item)

                # Skip hidden files
                if item.startswith('.'):
                    continue

                if os.path.isdir(item_path) and recursive:
                    # Recurse into subdirectories
                    sub_dir = os.path.join(dir_path, item)
                    files.extend(self._list_directory_files(sub_dir, recursive))
                else:
                    ext = os.path.splitext(item)[1].lower()
                    if ext in LOADABLE_EXTENSIONS:
                        files.append(os.path.join(dir_path, item))
        except Exception:
            pass

        return files

    def _format_file_for_context(self, rel_path: str, content: str) -> str:
        """Format a file's content for inclusion in context."""
        return f"""### File: {rel_path}
```
{content}
```
"""

    def load_file(self, rel_path: str) -> Optional[str]:
        """Load a specific file by relative path."""
        full_path = os.path.join(self.project_path, rel_path)
        return self._read_file_content(full_path)

    def load_directory(self, dir_path: str, max_files: int = 10) -> Dict[str, str]:
        """Load all files from a directory."""
        files = self._list_directory_files(dir_path)
        result = {}

        for file_path in files[:max_files]:
            content = self.load_file(file_path)
            if content:
                result[file_path] = content

        return result

    def load_critical_files(self) -> Dict[str, str]:
        """
        Load essential files that all agents should have access to.

        Returns:
            Dict mapping relative file paths to their content
        """
        critical_files = {}

        # Priority files that should always be loaded if they exist
        priority_paths = [
            'planning/story-outline.md',
            'planning/chapter-breakdown.md',
            'planning/themes.md',
            'story-bible/continuity.md',
            'story-bible/timeline.md',
        ]

        for rel_path in priority_paths:
            content = self.load_file(rel_path)
            if content:
                critical_files[rel_path] = content

        # Load all character files (usually essential)
        character_files = self.load_directory('characters', max_files=10)
        critical_files.update(character_files)

        return critical_files

    def load_recent_chapters(self, num_chapters: int = 2) -> Dict[str, str]:
        """Load the most recent chapter files."""
        chapter_dir = 'manuscript/chapters'
        chapter_files = self._list_directory_files(chapter_dir, recursive=False)

        # Sort to get most recent (assuming chapter-XX naming)
        chapter_files.sort(reverse=True)

        result = {}
        for chapter_path in chapter_files[:num_chapters]:
            content = self.load_file(chapter_path)
            if content:
                result[chapter_path] = content

        return result

    def load_for_agent(self, agent_type: str, user_message: str = "") -> Dict[str, str]:
        """
        Load context files appropriate for a specific agent type.

        Args:
            agent_type: The type of agent (e.g., 'architect', 'prose_stylist')
            user_message: The user's request (used for additional relevance filtering)

        Returns:
            Dict mapping relative file paths to their content
        """
        files = {}

        # All agents get critical files
        if agent_type != "general":
            # Start with a subset of critical files for specialized agents
            critical = self.load_critical_files()

            # Agent-specific loading strategies
            if agent_type in ['architect']:
                # Architect needs planning docs primarily
                files.update(critical)

            elif agent_type in ['prose_stylist']:
                # Prose stylist needs recent chapters and character voices
                files.update(critical)
                recent = self.load_recent_chapters(3)
                files.update(recent)
                # Also load scenes
                scenes = self.load_directory('manuscript/scenes', max_files=5)
                files.update(scenes)

            elif agent_type in ['character_psychologist']:
                # Character psychologist needs character files primarily
                files.update(critical)
                # Make sure we have all character files
                all_chars = self.load_directory('characters', max_files=20)
                files.update(all_chars)

            elif agent_type in ['atmosphere']:
                # Atmosphere needs settings and world-building
                files.update(critical)
                settings = self.load_directory('story-bible', max_files=10)
                files.update(settings)
                recent = self.load_recent_chapters(2)
                files.update(recent)

            elif agent_type in ['research']:
                # Research agent needs research files and story bible
                files.update(critical)
                research = self.load_directory('research', max_files=15)
                files.update(research)
                story_bible = self.load_directory('story-bible', max_files=10)
                files.update(story_bible)

            elif agent_type in ['continuity']:
                # Continuity needs timeline, established facts, and chapters
                files.update(critical)
                recent = self.load_recent_chapters(5)
                files.update(recent)

            elif agent_type in ['redundancy', 'beta_reader']:
                # Reviewers need recent content to review
                files.update(critical)
                recent = self.load_recent_chapters(3)
                files.update(recent)
                scenes = self.load_directory('manuscript/scenes', max_files=5)
                files.update(scenes)

            else:
                # Default: load critical files
                files.update(critical)
        else:
            # General requests get full critical context
            files = self.load_critical_files()
            recent = self.load_recent_chapters(2)
            files.update(recent)

        return files

    def load_full_project_context(self, max_files: int = 30) -> Dict[str, str]:
        """
        Load comprehensive project context (all major files).

        Use this for general requests where the user wants full context.
        """
        files = {}

        # Load from all main directories
        directories = [
            ('planning', 10),
            ('characters', 15),
            ('manuscript/chapters', 10),
            ('manuscript/scenes', 10),
            ('story-bible', 10),
            ('research', 10),
            ('feedback', 5),
        ]

        for dir_path, limit in directories:
            dir_files = self.load_directory(dir_path, max_files=limit)
            files.update(dir_files)

            if len(files) >= max_files:
                break

        return files

    def format_context_for_prompt(self, files: Dict[str, str], max_total_chars: int = MAX_TOTAL_CONTEXT_CHARS) -> str:
        """
        Format loaded files into a string suitable for inclusion in a prompt.

        Args:
            files: Dict mapping file paths to content
            max_total_chars: Maximum total characters to include

        Returns:
            Formatted string with all file contents
        """
        if not files:
            return ""

        sections = []
        total_chars = 0

        # Sort files by type for better organization
        sorted_files = sorted(files.items(), key=lambda x: x[0])

        for rel_path, content in sorted_files:
            formatted = self._format_file_for_context(rel_path, content)

            if total_chars + len(formatted) > max_total_chars:
                # Check if we can fit a truncated version
                remaining = max_total_chars - total_chars
                if remaining > 500:  # Only include if meaningful space remains
                    truncated_content = content[:remaining - 200]
                    formatted = self._format_file_for_context(
                        rel_path,
                        truncated_content + "\n[... truncated ...]"
                    )
                    sections.append(formatted)
                break

            sections.append(formatted)
            total_chars += len(formatted)

        if sections:
            header = f"""
## EXISTING PROJECT FILES ({len(sections)} files loaded)

The following files exist in your project. Use this content to maintain consistency and build upon existing work.

"""
            return header + "\n".join(sections)

        return ""

    def get_file_index(self) -> str:
        """
        Get an index of all files in the project without loading content.

        Useful for giving agents awareness of what exists without loading everything.
        """
        index_lines = ["## PROJECT FILE INDEX\n"]

        directories = [
            'planning',
            'characters',
            'manuscript/chapters',
            'manuscript/scenes',
            'story-bible',
            'research',
            'feedback',
        ]

        for dir_path in directories:
            files = self._list_directory_files(dir_path)
            if files:
                index_lines.append(f"\n### {dir_path}/")
                for f in sorted(files):
                    # Get file size
                    full_path = os.path.join(self.project_path, f)
                    try:
                        size = os.path.getsize(full_path)
                        size_str = f"{size:,} bytes" if size < 1024 else f"{size/1024:.1f} KB"
                    except:
                        size_str = "unknown size"
                    index_lines.append(f"- {os.path.basename(f)} ({size_str})")

        return "\n".join(index_lines)


def build_project_context(
    project_path: str,
    agent_type: str = "general",
    user_message: str = "",
    include_file_index: bool = True
) -> str:
    """
    Convenience function to build complete project context for an agent.

    Args:
        project_path: Path to the project directory
        agent_type: Type of agent that will receive this context
        user_message: The user's request
        include_file_index: Whether to include an index of all project files

    Returns:
        Formatted context string ready for inclusion in a prompt
    """
    loader = ProjectContextLoader(project_path)

    # Load appropriate files for the agent
    files = loader.load_for_agent(agent_type, user_message)

    # Format the context
    context = loader.format_context_for_prompt(files)

    # Optionally add file index so agent knows what else exists
    if include_file_index:
        index = loader.get_file_index()
        context = index + "\n\n" + context

    return context
