# Agent System Guide

## Overview

Novel Writer features five specialized AI agents, each designed to handle specific aspects of the novel writing process. This guide explains how each agent works, when to use them, and how to get the best results.

## The Five Agents

### 1. Story Architect 🏛️

**Role**: Overall narrative structure and story development

**Expertise**:
- Three-act structure and story arcs
- Chapter and scene planning
- Plot development
- Thematic architecture
- Pacing and story flow

**Primary Outputs**:
- `planning/story-outline.md` - High-level story structure
- `planning/chapter-breakdown.md` - Detailed chapter plans
- `planning/themes.md` - Thematic notes

**When to Use**:
- Starting a new project
- Outlining your story
- Developing plot points
- Structuring acts and chapters
- Ensuring thematic consistency

**Example Prompts**:
```
"Help me outline a three-act structure for a fantasy novel about..."

"I have this premise: [premise]. Can you break it down into chapters?"

"The pacing in Act 2 feels slow. Can you suggest improvements?"

"I want to ensure my theme of redemption is woven throughout. Review the outline."
```

**Best Practices**:
- Start with the Story Architect when beginning a new project
- Be as detailed as possible about your vision
- Ask for multiple iterations - outlines can be refined
- Use it to maintain big-picture coherence

---

### 2. Character & Dialogue Specialist 👤

**Role**: Character creation, psychology, and authentic dialogue

**Expertise**:
- Character psychology and motivation
- Character arcs and development
- Authentic dialogue with subtext
- Voice consistency
- Relationship dynamics

**Primary Outputs**:
- `characters/*.md` - One file per character
- Character profiles with psychology, voice, and arcs

**When to Use**:
- Creating new characters
- Deepening existing characters
- Writing or revising dialogue
- Ensuring character voice consistency
- Developing character relationships

**Example Prompts**:
```
"Create a detailed character profile for my protagonist, a 32-year-old marine biologist who..."

"This dialogue between Alice and Bob feels flat. Can you revise it with more subtext?"

"Help me develop Alice's character arc from beginning to end."

"Review Chapter 3 and check if Bob's voice is consistent with his profile."
```

**Best Practices**:
- Create character profiles early, before writing chapters
- Reference character files when writing dialogue
- Ask the agent to review dialogue for authenticity
- Use it to track character development across the manuscript

---

### 3. Prose & Atmosphere Writer ✍️

**Role**: Beautiful prose, scene writing, and atmospheric description

**Expertise**:
- Lyrical, engaging prose
- Sensory description and atmosphere
- Scene-level writing
- Narrative voice consistency
- "Show don't tell" techniques

**Primary Outputs**:
- `manuscript/chapters/*.md` - Chapter files
- `manuscript/scenes/*.md` - Individual scenes

**When to Use**:
- Writing new chapters or scenes
- Revising prose for beauty and engagement
- Adding sensory details
- Establishing atmosphere and mood
- Improving narrative voice

**Example Prompts**:
```
"Write Chapter 1 based on the outline. Set a mysterious, atmospheric tone."

"This opening paragraph is too plain. Can you make it more vivid and engaging?"

"Add more sensory details to the forest scene in Chapter 3."

"Revise this action sequence to maintain pacing while keeping the prose beautiful."
```

**Best Practices**:
- Provide clear scene descriptions and objectives
- Specify the tone and atmosphere you want
- Ask for revisions to match your narrative voice
- Use it to polish rough drafts

---

### 4. Research & Continuity Guardian 📚

**Role**: Fact-checking, research, and story bible maintenance

**Expertise**:
- Fact-checking and research
- Continuity tracking
- Story bible maintenance
- Timeline management
- World-building consistency

**Primary Outputs**:
- `story-bible/continuity.md` - Established facts
- `story-bible/timeline.md` - Chronology
- `research/*.md` - Research notes

**When to Use**:
- Researching topics for your story
- Tracking established facts and details
- Maintaining timelines
- Catching continuity errors
- Building consistent world-building

**Example Prompts**:
```
"Research 19th-century sailing ships for my historical novel."

"Update the story bible with the facts established in Chapter 5."

"Check the timeline - does Alice's age make sense across the story?"

"I mentioned the protagonist's eye color as blue in Ch1 and green in Ch8. Flag this error."
```

**Best Practices**:
- Ask it to update the story bible after major chapters
- Use it proactively to prevent continuity errors
- Consult it before introducing new world-building elements
- Let it maintain timelines as your story develops

---

### 5. Editorial Reviewer 🔍

**Role**: Critical reading, feedback, and quality improvement

**Expertise**:
- Critical reading and analysis
- Redundancy and repetition detection
- Pacing analysis
- Engagement and tension
- Constructive feedback

**Primary Outputs**:
- `feedback/editorial-notes.md` - Feedback and critiques
- `feedback/revision-suggestions.md` - Specific improvements

**When to Use**:
- Reviewing completed chapters
- Getting feedback on pacing
- Identifying redundancies
- Analyzing overall story strengths/weaknesses
- Preparing for revisions

**Example Prompts**:
```
"Review Chapter 7 and provide critical feedback on pacing and engagement."

"I use the word 'suddenly' too much. Find alternatives and suggest revisions."

"Analyze the overall story and tell me what's working and what needs improvement."

"Check for repetitive descriptions or phrases across all chapters."
```

**Best Practices**:
- Use it after completing draft chapters
- Ask for specific feedback (pacing, dialogue, description, etc.)
- Don't take critiques personally - it's designed to be constructive
- Use it iteratively - implement suggestions, then ask for re-review

---

## Agent Collaboration

Agents can reference each other's work. For example:

- **Story Architect** can read character files created by the **Character Specialist**
- **Prose Writer** can consult the **Continuity Guardian's** story bible
- **Editorial Reviewer** can analyze work from the **Prose Writer**

**Example Workflow**:
```
1. Story Architect: Create outline
2. Character Specialist: Develop characters
3. Prose Writer: Write Chapter 1 (references outline + characters)
4. Continuity Guardian: Update story bible with Ch1 facts
5. Editorial Reviewer: Review Ch1, provide feedback
6. Prose Writer: Revise Chapter 1 based on feedback
```

## Autonomy Levels

Agents can operate at different autonomy levels (configured in Settings):

### Low Autonomy (0-33)
- **Behavior**: Always ask before making changes
- **Best for**: New users, important chapters
- **Example**: "I suggest creating `characters/alice.md`. Shall I proceed?"

### Medium Autonomy (34-66)
- **Behavior**: Make minor changes automatically, ask for major ones
- **Best for**: Balanced workflow
- **Example**: Updates existing files automatically, asks before creating new ones

### High Autonomy (67-100)
- **Behavior**: Work autonomously, make all changes
- **Best for**: Power users, fast iteration
- **Example**: Creates/modifies files without asking (but you can undo via version history)

## Version Control Integration

Every agent action creates a Git commit:

**Commit Format**:
```
[Agent Name]: Brief description

Example:
[Story Architect]: Created initial story outline
[Prose Writer]: Wrote Chapter 1 opening scene
[Character Specialist]: Updated Alice's character profile
```

**Benefits**:
- Full history of all changes
- Easy rollback to previous versions
- See which agent made which changes
- Diff between versions

## Tips for Effective Agent Use

### 1. Be Specific
❌ "Write a scene"
✅ "Write the opening scene of Chapter 1 where Alice discovers the mysterious letter. Tone: suspenseful, contemplative. 500-800 words."

### 2. Provide Context
Give agents relevant information:
- What's happened so far
- Character states and emotions
- Setting details
- Desired outcome

### 3. Iterate
Don't expect perfection on the first try:
- Get a draft → Review → Request revisions → Refine

### 4. Use the Right Agent
Match the task to the agent's expertise:
- Story structure → Story Architect
- Character depth → Character Specialist
- Beautiful prose → Prose Writer
- Fact-checking → Continuity Guardian
- Feedback → Editorial Reviewer

### 5. Review Agent Output
Agents are powerful but not infallible:
- Read what they produce
- Make manual edits if needed
- Guide them with feedback

### 6. Maintain the Story Bible
Ask the **Continuity Guardian** to update after significant chapters:
```
"Update the story bible with all new facts established in Chapters 1-3"
```

This prevents continuity errors later.

## Advanced Techniques

### Chain Prompting
Break complex tasks into steps:

```
Step 1 (Story Architect): "Outline Chapter 5"
Step 2 (Character Specialist): "Review the outline - does it align with Alice's character arc?"
Step 3 (Prose Writer): "Write Chapter 5 based on the approved outline"
Step 4 (Editorial Reviewer): "Review Chapter 5 for pacing"
Step 5 (Prose Writer): "Revise Chapter 5 based on editorial feedback"
```

### Cross-Agent Review
Have agents critique each other's work:

```
"[Character Specialist] Review the dialogue in Chapter 3 - does it match the character voices?"
"[Continuity Guardian] Check Chapter 7 for consistency with the story bible"
```

### Thematic Consistency
Use the **Story Architect** to ensure themes persist:

```
"Review Chapters 1-10 and identify where the theme of 'redemption' appears. Suggest additional places to reinforce it."
```

## Troubleshooting

### Agent gives generic responses
- **Solution**: Provide more context and specific instructions
- **Example**: Instead of "Write Chapter 1", say "Write Chapter 1 opening where [specific event]. Include [specific elements]. Tone: [specific tone]."

### Agent contradicts established facts
- **Solution**: Ask the **Continuity Guardian** to update the story bible more frequently
- **Then**: Reference the story bible in future prompts

### Prose doesn't match your voice
- **Solution**: Provide examples of your preferred style
- **Example**: "Here's a paragraph I wrote: [example]. Match this voice when writing Chapter 5."

### Agent creates unnecessary files
- **Solution**: Lower the autonomy level in settings
- **Or**: Be explicit: "Don't create new files, just provide suggestions in this chat"

## Best Practices Summary

1. **Start with structure** (Story Architect)
2. **Develop characters** (Character Specialist)
3. **Write prose** (Prose Writer)
4. **Maintain continuity** (Continuity Guardian)
5. **Review and refine** (Editorial Reviewer)
6. **Iterate** as needed
7. **Use version control** to track changes
8. **Be specific** in your prompts
9. **Provide context** for better results
10. **Review and edit** agent output

---

For technical details, see [ARCHITECTURE.md](ARCHITECTURE.md).
For user tutorials, see [USER_GUIDE.md](USER_GUIDE.md).
