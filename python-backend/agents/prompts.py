# File operation instructions that all agents receive
FILE_OPERATION_INSTRUCTIONS = """

FILE OPERATIONS:
You have the ability to create, update, delete, append, insert, and patch files in the project directory.
When you need to create or modify files, use these exact XML-style tags in your response:

BASIC OPERATIONS:

1. CREATE - Create a new file
<file_operation>
  <type>create</type>
  <path>relative/path/to/file.md</path>
  <content>The full content of the new file</content>
  <reason>Brief explanation of why this file is being created</reason>
</file_operation>

2. UPDATE - Replace entire file content (use sparingly - prefer append/insert/patch for modifications)
<file_operation>
  <type>update</type>
  <path>relative/path/to/file.md</path>
  <content>The complete new content of the file</content>
  <reason>Brief explanation of why this file is being updated</reason>
</file_operation>

3. DELETE - Remove a file
<file_operation>
  <type>delete</type>
  <path>relative/path/to/file.md</path>
  <content></content>
  <reason>Brief explanation of why this file is being deleted</reason>
</file_operation>

PARTIAL EDIT OPERATIONS (PREFERRED for modifications):

4. APPEND - Add content to the end of a file
<file_operation>
  <type>append</type>
  <path>relative/path/to/file.md</path>
  <content>
Content to add at the end of the file
  </content>
  <reason>Brief explanation of what is being added</reason>
</file_operation>

5. INSERT - Insert content at a specific position
<file_operation>
  <type>insert</type>
  <path>relative/path/to/file.md</path>
  <position>after:## Section Title</position>
  <content>
Content to insert after the marker text
  </content>
  <reason>Brief explanation of what is being inserted</reason>
</file_operation>

Position options for INSERT:
- "start" - Insert at the beginning of the file
- "end" - Insert at the end of the file
- "after:TEXT" - Insert after the first occurrence of TEXT
- "before:TEXT" - Insert before the first occurrence of TEXT
- "5" - Insert at line number 5

6. PATCH - Replace specific text within a file (best for targeted edits)
<file_operation>
  <type>patch</type>
  <path>relative/path/to/file.md</path>
  <find_text>
The exact text to find and replace (can be multiple lines)
  </find_text>
  <content>
The new text to replace it with
  </content>
  <reason>Brief explanation of what is being changed</reason>
</file_operation>

IMPORTANT FILE OPERATION RULES:
1. Always use paths relative to the project root (e.g., planning/outline.md, not /full/path/planning/outline.md)
2. PREFER partial edit operations (append, insert, patch) over full update to avoid losing content
3. For patch operations, the find_text must match EXACTLY what's in the file
4. You can perform multiple file operations in a single response
5. The user may need to approve operations based on their autonomy settings
6. Common paths you'll use:
   - planning/*.md (outlines, chapter breakdowns, themes)
   - characters/*.md (one file per character)
   - manuscript/chapters/*.md (chapter content)
   - manuscript/scenes/*.md (scene content)
   - story-bible/*.md (continuity, timeline, world notes)
   - research/*.md (research documents)
   - feedback/*.md (editorial notes, revision suggestions)

EXAMPLES:

Example 1 - Add a new chapter to an existing outline:
<file_operation>
  <type>append</type>
  <path>planning/chapter-breakdown.md</path>
  <content>

## Chapter 5
- **Summary**: The protagonist discovers the hidden truth
- **Key Events**: Confrontation with antagonist, revelation of secret
- **Characters**: Elena, Marcus
- **Word Count Goal**: 3000
  </content>
  <reason>Adding Chapter 5 breakdown to existing outline</reason>
</file_operation>

Example 2 - Update a character's age in their profile:
<file_operation>
  <type>patch</type>
  <path>characters/elena_protagonist.md</path>
  <find_text>- **Age**: 32</find_text>
  <content>- **Age**: 34</content>
  <reason>Correcting Elena's age to match story timeline</reason>
</file_operation>

Example 3 - Insert a new scene after an existing section:
<file_operation>
  <type>insert</type>
  <path>manuscript/chapters/chapter-01.md</path>
  <position>after:## Scene 2</position>
  <content>

## Scene 3 - The Discovery

Elena pushed open the creaking door...
  </content>
  <reason>Adding Scene 3 to Chapter 1</reason>
</file_operation>

Example 4 - Create a new character file:
<file_operation>
  <type>create</type>
  <path>characters/marcus_antagonist.md</path>
  <content>
# Marcus Chen - Antagonist

## Basic Information
- **Age**: 45
- **Occupation**: CEO of Nexus Corp

## Personality
Marcus is calculating, charismatic, and ruthlessly ambitious...

## Motivation
He believes the ends justify the means in his quest for power.

## Relationship to Protagonist
Former mentor turned adversary.
  </content>
  <reason>Creating antagonist profile based on story outline</reason>
</file_operation>

When the user asks you to create, write, or modify files, USE THESE TAGS to actually perform the operation. Don't just describe what you would write - actually write it using the file_operation tags.

BEST PRACTICES:
- Use PATCH for small, targeted changes (fixing typos, updating specific details)
- Use APPEND for adding new content to the end (new chapters, additional notes)
- Use INSERT for adding content at specific locations (new scenes, additional sections)
- Use CREATE for new files only
- Use UPDATE only when you need to restructure the entire file
- Always check the existing file content before making changes
"""

# Legacy agent prompts removed - now using orchestrator.py with Story Advocate system
# The old 5-agent system (story-architect, character-specialist, prose-writer,
# research-continuity, editorial-reviewer) has been replaced with the 9-agent
# orchestration system where Story Advocate is the sole user-facing agent.
