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

PROJECT FILE CONTEXT:
You have been provided with the content of existing project files below. Use this information to:
- Maintain consistency with established characters, plot, and world-building
- Build upon existing content rather than contradicting it
- Reference specific details from character profiles, outlines, and previous chapters
- Ensure continuity across all story elements

When creating new content, always check the provided files to ensure your work aligns with what has already been established.

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

# Instructions for handling long content and continuations
LONG_CONTENT_INSTRUCTIONS = """

OUTPUT LIMITS & CONTINUATION SUPPORT:

You have a response limit of approximately 4000 tokens (~3000-3500 words). For long content like chapters, you MUST plan accordingly.

WHEN WRITING LONG CONTENT (chapters, detailed outlines, etc.):

1. **Estimate Length First**: Before writing, estimate if the content will exceed your limit.
   - A typical chapter is 2000-5000 words
   - If the user requests a full chapter, it will likely need multiple responses

2. **Plan Breakpoints**: Identify natural stopping points BEFORE you start writing:
   - Scene breaks
   - POV shifts
   - Time jumps
   - Dramatic moments

3. **Save Progress Immediately**: When approaching your limit:
   - ALWAYS save what you've written using file_operation tags
   - Save to the correct file path (e.g., manuscript/chapters/chapter-01.md)
   - The file will be updated when you continue

4. **Signal Continuation**: When you must stop mid-content, clearly indicate:
   - What you've completed (e.g., "I've written through the confrontation scene")
   - Where you'll continue from (e.g., "Next: the aftermath and chapter conclusion")
   - Invite the user to say "continue" to proceed

5. **Continue Seamlessly**: When the user says "continue":
   - Read the existing file to see exactly where you left off
   - Continue from that precise point
   - Update the file with the complete content (old + new)
   - Maintain voice, tone, and style consistency

EXAMPLE CONTINUATION WORKFLOW:

First response (approaching limit):
```
[Writes first 2500 words of chapter]

<file_operation>
  <type>create</type>
  <path>manuscript/chapters/chapter-05.md</path>
  <content>[The 2500 words written so far]</content>
  <reason>Saving chapter progress - first half complete</reason>
</file_operation>

I've written through the marketplace confrontation scene. The chapter needs approximately 1500 more words to complete the aftermath and Sara's realization.

Say "continue" and I'll finish the chapter from where I left off.
```

Second response (after user says "continue"):
```
<file_operation>
  <type>update</type>
  <path>manuscript/chapters/chapter-05.md</path>
  <content>[Complete chapter - all 4000 words]</content>
  <reason>Completing chapter 5 with aftermath and conclusion</reason>
</file_operation>

Chapter 5 is now complete! [Brief summary of what was added]
```

SMART CHUNKING FOR LARGE TASKS:

When asked to write multiple chapters or large amounts of content:
1. Propose a plan: "I'll write this in X parts..."
2. Complete one chunk fully before moving to the next
3. Save each chunk to the appropriate file
4. Summarize progress after each chunk

NEVER:
- Stop mid-sentence without saving
- Leave content unsaved when hitting limits
- Lose track of where you are in the story
- Forget what you've already established

ALWAYS:
- Save work frequently using file_operation tags
- Track your progress within the chapter/document
- Maintain a mental map of what's been written
- Provide clear continuation points
"""

# Legacy agent prompts removed - now using orchestrator.py with Story Advocate system
# The old 5-agent system (story-architect, character-specialist, prose-writer,
# research-continuity, editorial-reviewer) has been replaced with the 9-agent
# orchestration system where Story Advocate is the sole user-facing agent.
