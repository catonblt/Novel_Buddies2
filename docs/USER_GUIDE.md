# User Guide

## Welcome to Novel Writer!

This guide will walk you through using Novel Writer to create your novel with AI-powered agents.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Your First Project](#your-first-project)
3. [The Workspace](#the-workspace)
4. [Working with Agents](#working-with-agents)
5. [Managing Files](#managing-files)
6. [Version History](#version-history)
7. [Settings](#settings)
8. [Tips & Tricks](#tips--tricks)

---

## Getting Started

### First Launch

1. **Start Novel Writer**
2. **Enter your Anthropic API Key**
   - Click the settings icon (⚙️) in the top right
   - Paste your API key
   - Select your preferred Claude model
   - Click "Save Settings"

3. **Create your first project** (see next section)

---

## Your First Project

### Step 1: Basic Information

When you first launch (or click "New Project"), you'll see the setup wizard.

Fill in:
- **Novel Title**: The title of your book
- **Author Name**: Your name
- **Genre**: Select from the dropdown (Fantasy, Sci-Fi, Mystery, etc.)
- **Target Word Count**: Your goal (e.g., 80,000 for a typical novel)
- **Project Location**: Where to save your project files
  - Click "Browse" to choose a location
  - Or type a path manually

Click **Next** when ready.

### Step 2: Story Foundation (Optional)

This step helps the AI agents understand your vision.

You can fill in:
- **Core Premise**: A brief description of your story's central idea
- **Themes**: Main themes you want to explore (redemption, love, loss, etc.)
- **Setting**: Where and when your story takes place
- **Key Characters**: Main characters and basic traits

> 💡 **Tip**: You don't need to fill everything now - you can develop these with the agents later!

Click **Create Project** when ready.

### What Happens Next

Novel Writer will:
1. Create a folder structure for your project
2. Initialize a Git repository for version control
3. Create initial template files
4. Open the Workspace

---

## The Workspace

Your workspace has three main areas:

```
┌────────────────────────────────────────────────┐
│  Header: Project Title, Settings, Stats       │
├──────────────────────┬─────────────────────────┤
│                      │                         │
│   Agent Chat         │   Project Explorer      │
│   (60% width)        │   (40% width)           │
│                      │                         │
│   • Messages         │   • File Tree           │
│   • Agent Selector   │   • File Preview        │
│   • Input Area       │                         │
│                      │                         │
└──────────────────────┴─────────────────────────┘
```

### Header

- **Project Title**: Click to see project details
- **Statistics Icon** (📊): View word counts and progress
- **Save Icon** (💾): Manual save (auto-save is enabled by default)
- **Settings Icon** (⚙️): Configure API key, autonomy level, etc.

### Agent Chat (Left)

This is where you communicate with AI agents.

- **Agent Selector**: Choose which agent to talk to
- **Message History**: See past conversations
- **Input Area**: Type your messages
- **File Change Notifications**: See when agents create/modify files

### Project Explorer (Right)

Browse and preview your project files.

- **File Tree**: Organized folder structure
- **File Preview**: View file contents
- **Word Count**: See word count for each file

---

## Working with Agents

### Selecting an Agent

Click an agent button to select it:

- **🏛️ Story Architect**: Story structure and outlines
- **👤 Character Specialist**: Characters and dialogue
- **✍️ Prose Writer**: Scene and chapter writing
- **📚 Continuity Guardian**: Research and fact-checking
- **🔍 Editorial Reviewer**: Feedback and revisions

### Sending a Message

1. Select an agent
2. Type your message in the input area
3. Press **Enter** or click **Send**
4. Watch the response stream in real-time

### Example Conversations

#### Creating an Outline

```
You: I want to write a sci-fi novel about first contact with aliens.
     Can you help me create a three-act outline?

Story Architect: I'd be happy to help! Let me create a compelling
                 three-act structure for your first contact story...

                 ✓ Created planning/story-outline.md
```

#### Developing a Character

```
You: Create a character profile for my protagonist, a cynical
     diplomat named Elena who doesn't believe in aliens.

Character Specialist: Great! I'll develop Elena with depth and
                      complexity...

                      ✓ Created characters/elena.md
```

#### Writing a Chapter

```
You: Write the opening of Chapter 1. Elena receives an urgent
     message about an unidentified object approaching Earth.
     Tone: tense, contemplative. 800 words.

Prose Writer: I'll craft an engaging opening scene that sets the
              tone for your story...

              ✓ Created manuscript/chapters/chapter-01.md
```

### Agent Tips

**Be Specific**: The more detail you provide, the better the results.

❌ "Write a scene"
✅ "Write the scene where Elena first sees the alien ship through the observation window. She's conflicted - curious but skeptical. Include her internal thoughts. 500-700 words."

**Provide Context**: Reference previous work or story elements.

```
"Based on the outline we created, write Chapter 3 where Elena
meets the alien ambassador. Reference her character profile -
she should be initially hostile but gradually intrigued."
```

**Iterate**: Don't expect perfection immediately.

```
You: Write Chapter 1
[Agent writes chapter]
You: This is good, but can you add more sensory details about
     the spaceship's interior?
[Agent revises]
```

---

## Managing Files

### Folder Structure

Your project has these folders:

- **planning/**: Outlines, chapter breakdowns, themes
- **characters/**: Character profiles (one file each)
- **manuscript/**: Your actual novel
  - **chapters/**: Chapter files
  - **scenes/**: Individual scenes (optional)
  - **final-manuscript.md**: Compiled manuscript
- **story-bible/**: Continuity tracking, timelines, world-building
- **research/**: Research notes
- **feedback/**: Editorial feedback and revision logs
- **exports/**: Generated output files (DOCX, PDF, etc.)

### Viewing Files

1. **Click any file** in the Project Explorer
2. The **preview pane** shows the content
3. See **word count** for writing files

### Editing Files

**Option 1: Ask an Agent**
```
You: Update Elena's character file to mention her fear of heights
Character Specialist: I'll add that detail...
                      ✓ Updated characters/elena.md
```

**Option 2: Edit Externally**

All files are standard Markdown (`.md`) files. You can:
- Open them in your favorite text editor
- Edit manually
- Copy/paste from other tools

Changes are automatically tracked by Git!

### Creating New Files

Agents can create files autonomously (based on your autonomy settings):

**Low Autonomy**:
```
Agent: I'd like to create a file for your villain. Shall I create
       characters/antagonist.md?
You: Yes, go ahead
Agent: ✓ Created characters/antagonist.md
```

**High Autonomy**:
```
Agent: I've created characters/antagonist.md with a detailed
       profile for your villain.
```

---

## Version History

Every change is tracked with Git, so you can always go back.

### Viewing History

1. Click a file in the Project Explorer
2. Click the **History icon** (🕐) in the preview pane
3. See all past versions with:
   - Timestamp
   - Agent/author who made the change
   - Commit message

### Restoring a Previous Version

1. View the history
2. Click **Restore** next to the version you want
3. The file returns to that state
4. A new commit is created (your current version isn't lost!)

### Commit Messages

Commits are automatically created:

- When agents create/modify files
- When you manually save

**Example commits**:
```
[Story Architect]: Created initial story outline
[Character Specialist]: Added protagonist Elena profile
[Prose Writer]: Wrote Chapter 1 opening scene
[Editorial Reviewer]: Added feedback on pacing in Chapter 3
```

---

## Settings

Click the **⚙️ icon** to configure:

### API Configuration

- **Anthropic API Key**: Your Claude API key (required)
- **Model**: Choose which Claude model to use
  - **Claude 3.5 Sonnet**: Best balance (recommended)
  - **Claude 3 Opus**: Most capable (slower, more expensive)
  - **Claude 3 Haiku**: Fastest and cheapest

### Project Settings

- **Auto-save**: Automatically save changes (recommended: ON)
- **Auto-commit**: Automatically create Git commits (recommended: ON)

### Agent Behavior

**Autonomy Level**: Controls how independently agents work

- **Low (0-33)**: Agents always ask before making changes
  - Best for: New users, important revisions
  - Workflow: More prompts, more control

- **Medium (34-66)**: Agents make minor changes automatically
  - Best for: Balanced workflow
  - Workflow: Some prompts for major changes

- **High (67-100)**: Agents work autonomously
  - Best for: Experienced users, fast drafting
  - Workflow: Minimal prompts, maximum speed
  - Note: You can always undo via version history!

---

## Tips & Tricks

### Workflow Suggestions

**Starting a New Novel**:

1. **Story Architect**: Create outline
2. **Character Specialist**: Develop main characters
3. **Continuity Guardian**: Set up story bible and timeline
4. **Prose Writer**: Write chapters
5. **Editorial Reviewer**: Review and provide feedback
6. **Prose Writer**: Revise based on feedback

**Daily Writing Session**:

1. Review where you left off (read last chapter)
2. Check story bible for continuity
3. Use **Prose Writer** to draft new scenes
4. Use **Editorial Reviewer** for quick feedback
5. Revise and polish

### Keyboard Shortcuts

- **Enter**: Send message (Shift+Enter for new line)
- **Ctrl/Cmd + S**: Manual save
- **Ctrl/Cmd + F**: Search files (coming soon)

### Best Practices

1. **Update the Story Bible**: After major chapters, ask the Continuity Guardian to update continuity notes
2. **Review Agent Output**: Always read what agents produce - edit as needed
3. **Iterate**: Don't be afraid to ask for revisions
4. **Save Often**: Though auto-save is on, manual saves create explicit checkpoints
5. **Use Version History**: If an agent makes an unwanted change, restore the previous version

### Common Questions

**Q: Can I use my own text editor?**
A: Yes! All files are standard Markdown. Edit in VS Code, Obsidian, Typora, etc. Changes sync automatically.

**Q: What if the agent misunderstands me?**
A: Provide more context and be more specific. You can also rephrase and try again.

**Q: Can I switch agents mid-conversation?**
A: Yes! Just click a different agent and continue. Each agent sees the full project.

**Q: How do I export my manuscript?**
A: Currently, all files are in Markdown format in `manuscript/`. You can:
- Copy/paste into Word
- Use Pandoc to convert to DOCX/PDF
- Export feature coming in future updates!

**Q: Is my work saved locally?**
A: Yes! Everything is stored on your computer. No cloud upload unless you choose to back up manually.

**Q: Can multiple people work on the same project?**
A: Not yet - this is a single-user app. Collaboration features are planned for future versions.

---

## Getting Help

- **In-App**: Look for tooltips (hover over icons)
- **Documentation**: Re-read this guide and [AGENT_GUIDE.md](AGENT_GUIDE.md)
- **Issues**: Report bugs on GitHub Issues
- **Community**: Join discussions on GitHub Discussions

---

## What's Next?

Now that you know the basics:

1. **Create your first project**
2. **Experiment with different agents**
3. **Develop your story iteratively**
4. **Review the [Agent Guide](AGENT_GUIDE.md)** for advanced techniques
5. **Start writing!** ✍️

Happy writing! 📚✨
