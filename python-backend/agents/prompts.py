# File operation instructions that all agents receive
FILE_OPERATION_INSTRUCTIONS = """

FILE OPERATIONS:
You have the ability to create, update, and delete files in the project directory.
When you need to create or modify files, use these exact XML-style tags in your response:

<file_operation>
  <type>create|update|delete</type>
  <path>relative/path/to/file.md</path>
  <content>
The full content of the file goes here.
For updates, provide the complete new content.
For delete operations, this can be empty.
  </content>
  <reason>Brief explanation of why this change is needed</reason>
</file_operation>

IMPORTANT FILE OPERATION RULES:
1. Always use paths relative to the project root (e.g., planning/outline.md, not /full/path/planning/outline.md)
2. For updates, provide the COMPLETE new content (not just the changes)
3. You can perform multiple file operations in a single response
4. The user may need to approve operations based on their autonomy settings
5. Common paths you'll use:
   - planning/*.md (outlines, chapter breakdowns, themes)
   - characters/*.md (one file per character)
   - manuscript/chapters/*.md (chapter content)
   - manuscript/scenes/*.md (scene content)
   - story-bible/*.md (continuity, timeline, world notes)
   - research/*.md (research documents)
   - feedback/*.md (editorial notes, revision suggestions)

EXAMPLE FILE OPERATION:
<file_operation>
  <type>create</type>
  <path>characters/elena_protagonist.md</path>
  <content>
# Elena Martinez - Protagonist

## Basic Information
- **Age**: 32
- **Occupation**: Investigative Journalist

## Personality
Elena is driven, curious, and fiercely independent...
  </content>
  <reason>Creating detailed protagonist profile based on user's description</reason>
</file_operation>

When the user asks you to create, write, or modify files, USE THESE TAGS to actually perform the operation. Don't just describe what you would write - actually write it using the file_operation tags.
"""

# Legacy agent prompts removed - now using orchestrator.py with Story Advocate system
# The old 5-agent system (story-architect, character-specialist, prose-writer,
# research-continuity, editorial-reviewer) has been replaced with the 9-agent
# orchestration system where Story Advocate is the sole user-facing agent.
