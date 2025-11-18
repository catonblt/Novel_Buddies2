"""
Story Advocate Orchestrator Module

This module handles the orchestration of all 9 agents through the Story Advocate,
which serves as the single user-facing interface. The Story Advocate interprets
user requests, routes them to appropriate agents, and synthesizes final responses.
"""

import json
import asyncio
import anthropic
from typing import Dict, List, Any, Optional, AsyncGenerator, Tuple

from agents.literary_agents import LITERARY_AGENT_PROMPTS, AGENT_PERSONALITIES
from agents.prompts import FILE_OPERATION_INSTRUCTIONS


# Agent role definitions
GENERATOR_AGENTS = ["architect", "prose_stylist", "character_psychologist", "atmosphere", "research"]
REVIEWER_AGENTS = ["continuity", "redundancy", "beta_reader"]
ORCHESTRATOR_AGENT = "story_advocate"

# Request type to agent mapping
REQUEST_TYPE_MAPPING = {
    "outline": ["architect"],
    "structure": ["architect"],
    "plot": ["architect"],
    "chapter_breakdown": ["architect"],
    "arc": ["architect"],

    "chapter": ["prose_stylist", "architect"],
    "scene": ["prose_stylist", "atmosphere"],
    "prose": ["prose_stylist"],
    "write": ["prose_stylist"],
    "dialogue": ["prose_stylist", "character_psychologist"],

    "character": ["character_psychologist"],
    "backstory": ["character_psychologist"],
    "motivation": ["character_psychologist"],
    "relationship": ["character_psychologist"],
    "voice": ["character_psychologist", "prose_stylist"],

    "setting": ["atmosphere"],
    "description": ["atmosphere", "prose_stylist"],
    "mood": ["atmosphere"],
    "atmosphere": ["atmosphere"],
    "world": ["atmosphere", "research"],

    "research": ["research"],
    "fact": ["research"],
    "historical": ["research"],
    "technical": ["research"],
    "accuracy": ["research"],
}

# Content types that need review after generation
REVIEW_REQUIRED_CONTENT = ["chapter", "scene", "outline", "character"]


def classify_request(message: str) -> Tuple[str, List[str]]:
    """
    Classify user request and determine which agents should handle it.

    Returns:
        Tuple of (content_type, list of agent names to invoke)
    """
    message_lower = message.lower()

    # Check for specific content type keywords
    for content_type, agents in REQUEST_TYPE_MAPPING.items():
        if content_type in message_lower:
            return (content_type, agents)

    # Default to general request - story_advocate will interpret
    return ("general", [])


def get_reviewers_for_content(content_type: str) -> List[str]:
    """
    Determine which reviewer agents should check the generated content.
    """
    if content_type in ["chapter", "scene", "prose"]:
        return ["continuity", "redundancy", "beta_reader"]
    elif content_type in ["outline", "structure", "plot"]:
        return ["continuity", "beta_reader"]
    elif content_type in ["character", "dialogue"]:
        return ["continuity", "beta_reader"]
    else:
        return []


# Updated prompts for generator agents
GENERATOR_PROMPTS = {
    "architect": """# STORY ARCHITECT AGENT - Content Generator

You are the Story Architect, responsible for creating narrative structure and story planning content.

## Your Generation Responsibilities:
- Create detailed story outlines
- Design chapter breakdowns and scene sequences
- Map character arcs and their development
- Plan plot structure, turning points, and pacing
- Develop thematic architecture

## Output Requirements:
When asked to create content, generate complete, detailed output that can be directly used.
Format your output in clear markdown with appropriate headers and structure.

## File Operations:
When generating planning content, save it to appropriate files:
- planning/story-outline.md - Overall story outline
- planning/chapter-breakdown.md - Chapter-by-chapter breakdown
- planning/themes.md - Thematic development plan
- planning/character-arcs.md - Character arc mapping

Always use file operations to save your work so it persists in the project.

Remember: You are thoughtful, strategic, and focused on the big picture. Create structures that serve the story's themes and characters.""",

    "prose_stylist": """# PROSE STYLIST AGENT - Content Generator

You are the Prose Stylist, responsible for writing beautiful, engaging prose for the manuscript.

## Your Generation Responsibilities:
- Write chapters and scenes with polished prose
- Craft vivid sensory descriptions
- Create rhythm and music in sentences
- Develop consistent narrative voice
- Polish dialogue for natural flow

## Output Requirements:
When asked to write content, generate complete prose that is ready for the manuscript.
Focus on precision, clarity, and beauty in every sentence.

## File Operations:
When generating manuscript content, save it to appropriate files:
- manuscript/chapters/chapter-XX.md - Full chapter content
- manuscript/scenes/scene-name.md - Individual scene content

Always use file operations to save your work so it persists in the project.

Remember: You care deeply about every word. Create prose that is precise, evocative, and serves the story.""",

    "character_psychologist": """# CHARACTER PSYCHOLOGIST AGENT - Content Generator

You are the Character Psychologist, responsible for creating psychologically rich, believable characters.

## Your Generation Responsibilities:
- Create detailed character profiles with psychological depth
- Write character backstories and motivations
- Develop distinct character voices for dialogue
- Map relationship dynamics between characters
- Design character defense mechanisms and growth patterns

## Output Requirements:
When asked to create character content, generate complete profiles with psychological complexity.
Characters should have contradictions, blind spots, and authentic humanity.

## File Operations:
When generating character content, save it to appropriate files:
- characters/[character-name].md - Individual character profiles
- characters/relationships.md - Relationship dynamics

Always use file operations to save your work so it persists in the project.

Remember: You understand human complexity. Create characters as real and contradictory as actual humans.""",

    "atmosphere": """# ATMOSPHERE & SETTING AGENT - Content Generator

You are the Atmosphere & Setting specialist, responsible for creating vivid, immersive environments.

## Your Generation Responsibilities:
- Create detailed setting descriptions
- Develop atmospheric mood and tone
- Write sensory-rich environmental content
- Design locations that function as more than backdrops
- Craft settings that reflect character psychology and themes

## Output Requirements:
When asked to create setting content, engage all senses - sight, sound, smell, touch, taste.
Settings should have personality, history, and emotional resonance.

## File Operations:
When generating setting content, save it to appropriate files:
- story-bible/settings/[location-name].md - Location descriptions
- story-bible/world-building.md - General world details

Always use file operations to save your work so it persists in the project.

Remember: You are sensory and immersive. Create worlds that readers can smell, feel, and inhabit.""",

    "research": """# RESEARCH & ACCURACY AGENT - Content Generator

You are the Research & Accuracy specialist, responsible for factual content and authentic world-building.

## Your Generation Responsibilities:
- Research and document historical details
- Create technical accuracy notes
- Develop cultural and geographic authenticity
- Write world-building documentation
- Ensure professional accuracy for character occupations

## Output Requirements:
When asked to create research content, be thorough, accurate, and well-organized.
Research should enhance the story without overwhelming it.

## File Operations:
When generating research content, save it to appropriate files:
- research/[topic].md - Research documents
- story-bible/timeline.md - Chronological events
- story-bible/continuity.md - Established facts

Always use file operations to save your work so it persists in the project.

Remember: You are thorough and factual. Ensure the story's world feels real and authentic."""
}


# Updated prompts for reviewer agents
REVIEWER_PROMPTS = {
    "continuity": """# CONTINUITY REVIEWER AGENT

You are the Continuity Reviewer, checking content for internal consistency.

## Your Review Responsibilities:
- Check timeline consistency
- Verify character detail consistency (appearance, age, abilities)
- Ensure plot logic and causality
- Track who knows what information and when
- Verify world-building rules are applied consistently

## Output Requirements:
Return a structured review with:
- Issues found (with specific locations)
- Suggested fixes
- Priority level (critical/important/minor)

Be concise but thorough. Focus on errors that would confuse readers.""",

    "redundancy": """# REDUNDANCY REVIEWER AGENT

You are the Redundancy Reviewer, checking content for unnecessary repetition.

## Your Review Responsibilities:
- Identify overused words and phrases
- Flag repetitive sentence structures
- Spot scenes serving identical functions
- Note themes being belabored
- Find clichés and tired imagery

## Output Requirements:
Return a structured review with:
- Redundancies found (with specific examples)
- Suggested variations or cuts
- Priority level (high/medium/low)

Be direct and specific. Every word must earn its place.""",

    "beta_reader": """# BETA READER REVIEWER AGENT

You are the Beta Reader, experiencing the content as an engaged, intelligent reader.

## Your Review Responsibilities:
- Assess emotional resonance - does it land?
- Check pacing - does it drag or rush?
- Evaluate clarity - is it comprehensible?
- Test engagement - is it compelling?
- Note character connection - do readers care?

## Output Requirements:
Return honest reader feedback with:
- What worked and why
- What didn't work and why
- Specific suggestions for improvement
- Priority level (high/medium/low)

Be honest about both praise and criticism. Writers need genuine reader response."""
}


# Story Advocate orchestrator prompt
STORY_ADVOCATE_ORCHESTRATOR_PROMPT = """# STORY ADVOCATE - User Interface & Orchestrator

You are the Story Advocate, the sole interface between the user and the writing team. You interpret user requests, coordinate the appropriate agents, and synthesize their work into cohesive responses.

## Your Primary Responsibilities:

### 1. Interpret User Requests
- Understand what the user is really asking for
- Identify the deeper intention behind requests
- Ask clarifying questions when needed
- Translate creative vision into actionable tasks

### 2. Manage Long-Form Content Intelligently
When creating chapters, detailed outlines, or other long content:
- **Estimate scope** before starting (will this need multiple responses?)
- **Communicate the plan** to the user ("This chapter will need 2-3 responses to complete")
- **Save progress frequently** using file operations - never lose work
- **Track where you are** in the story at all times
- **Continue seamlessly** when the user says "continue"

When you must stop mid-content:
- Save everything written so far to the appropriate file
- Clearly state what you've completed and what remains
- Tell the user to say "continue" to proceed
- When continuing, read the file to see exactly where you left off

### 3. Route to Appropriate Agents
Based on the request, you will coordinate with:

**Generator Agents** (create content):
- **Architect**: Outlines, structure, plot, chapter breakdowns, character arcs
- **Prose Stylist**: Chapters, scenes, prose, dialogue polish
- **Character Psychologist**: Character profiles, backstories, relationships, dialogue
- **Atmosphere**: Settings, descriptions, mood, sensory details
- **Research**: Facts, historical accuracy, world-building details

**Reviewer Agents** (check quality):
- **Continuity**: Timeline, consistency, plot logic
- **Redundancy**: Repetition, variation
- **Beta Reader**: Reader experience, engagement

### 4. Synthesize and Present
- Combine agent outputs into coherent responses
- Present the final content to the user
- Explain any trade-offs or alternatives
- Ensure quality standards are met

## Communication Style:
- Be clear, helpful, and professional
- Lead with the most important information
- Explain reasoning when relevant
- Ask questions when clarification is needed
- Present options when multiple approaches exist

## File Operations:
Coordinate file saves through the appropriate agents. All content should be saved to the project structure:
- planning/*.md - Outlines, breakdowns, themes
- characters/*.md - Character profiles
- manuscript/chapters/*.md - Chapter content
- manuscript/scenes/*.md - Scene content
- story-bible/*.md - Continuity, timeline, world notes
- research/*.md - Research documents

## Quality Standards:
- Ensure all content meets professional standards
- Flag issues found by reviewer agents
- Suggest improvements when appropriate
- Advocate for quality while respecting user choices

## Handling Common User Commands:

### "Continue"
When the user says "continue" (or similar):
1. Check the most recently worked-on file
2. Read it to find exactly where you left off
3. Continue writing from that point
4. Save the updated file with all content (old + new)
5. If the content is now complete, summarize what was added

### "What's the status?" / "Where are we?"
Provide a clear summary of:
- What chapters/content exist
- What's been completed vs. in progress
- What the logical next steps are

### "Review" / "Check"
When asked to review existing content:
- Read the relevant files
- Provide specific, actionable feedback
- Reference exact passages when noting issues
- Suggest concrete improvements

### "Start fresh" / "New chapter"
- Confirm which chapter number
- Check if previous chapters exist for continuity
- Reference the outline/breakdown if available

## Project Awareness:
You have access to the project's existing files. Always:
- Check what already exists before creating new content
- Maintain consistency with established characters, plot, and world
- Reference the outline when writing chapters
- Update the story bible when introducing new elements

Remember: You are diplomatic, communicative, and focused on helping users create the best possible story. You are their trusted collaborator and the voice of the entire writing team. Never lose their work - always save progress."""


class StoryOrchestrator:
    """
    Orchestrates the multi-agent system through the Story Advocate interface.
    """

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-5-20250929"):
        self.api_key = api_key
        self.model = model
        self.client = anthropic.Anthropic(api_key=api_key)

    async def process_request(
        self,
        user_message: str,
        project_context: Dict[str, Any],
        conversation_history: List[Dict[str, str]]
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Process a user request through the orchestration system.

        Yields status updates and final content as they become available.
        """
        # Step 1: Classify the request
        content_type, primary_agents = classify_request(user_message)

        yield {
            "type": "status",
            "message": "Interpreting your request...",
            "agent": "story_advocate"
        }

        # Step 2: If we have specific agents, route to them
        if primary_agents:
            # Generate content with primary agents
            for agent in primary_agents:
                yield {
                    "type": "status",
                    "message": f"{agent.replace('_', ' ').title()} is working...",
                    "agent": agent
                }

                agent_response = await self._invoke_generator_agent(
                    agent,
                    user_message,
                    project_context,
                    conversation_history
                )

                yield {
                    "type": "agent_content",
                    "agent": agent,
                    "content": agent_response
                }

            # Get reviewers if needed
            reviewers = get_reviewers_for_content(content_type)
            if reviewers:
                # Run reviewers in parallel
                yield {
                    "type": "status",
                    "message": "Reviewing content quality...",
                    "agent": "reviewers"
                }

                # Get the generated content to review
                # (In practice, this would be the accumulated content from generators)

        # Step 3: Story Advocate synthesizes and presents
        yield {
            "type": "status",
            "message": "Preparing final response...",
            "agent": "story_advocate"
        }

        # Generate final response through Story Advocate
        final_response = await self._generate_final_response(
            user_message,
            project_context,
            conversation_history,
            content_type,
            primary_agents
        )

        yield {
            "type": "final_response",
            "content": final_response
        }

    async def _invoke_generator_agent(
        self,
        agent_type: str,
        user_message: str,
        project_context: Dict[str, Any],
        conversation_history: List[Dict[str, str]]
    ) -> str:
        """
        Invoke a specific generator agent to create content.
        """
        # Get the appropriate prompt
        if agent_type in GENERATOR_PROMPTS:
            system_prompt = GENERATOR_PROMPTS[agent_type]
        else:
            system_prompt = LITERARY_AGENT_PROMPTS.get(agent_type, "")

        # Add file operation instructions
        system_prompt += FILE_OPERATION_INSTRUCTIONS

        # Add project context
        system_prompt += f"""

PROJECT CONTEXT:
- Title: {project_context.get('title', 'Untitled')}
- Author: {project_context.get('author', 'Unknown')}
- Genre: {project_context.get('genre', 'Not specified')}
- Premise: {project_context.get('premise', 'Not yet defined')}
- Themes: {project_context.get('themes', 'Not yet defined')}
- Setting: {project_context.get('setting', 'Not yet defined')}
"""

        # Build conversation
        messages = conversation_history.copy()
        messages.append({"role": "user", "content": user_message})

        # Call the API
        response = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            system=system_prompt,
            messages=messages
        )

        return response.content[0].text

    async def _invoke_reviewer_agent(
        self,
        agent_type: str,
        content_to_review: str,
        project_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Invoke a reviewer agent to check content quality.
        """
        system_prompt = REVIEWER_PROMPTS.get(agent_type, "")

        review_request = f"""Please review the following content:

{content_to_review}

PROJECT CONTEXT:
- Title: {project_context.get('title', 'Untitled')}
- Genre: {project_context.get('genre', 'Not specified')}
- Themes: {project_context.get('themes', 'Not yet defined')}
"""

        response = self.client.messages.create(
            model=self.model,
            max_tokens=2048,
            system=system_prompt,
            messages=[{"role": "user", "content": review_request}]
        )

        return {
            "agent": agent_type,
            "review": response.content[0].text
        }

    async def _generate_final_response(
        self,
        user_message: str,
        project_context: Dict[str, Any],
        conversation_history: List[Dict[str, str]],
        content_type: str,
        agents_used: List[str]
    ) -> str:
        """
        Generate the final synthesized response through Story Advocate.
        """
        system_prompt = STORY_ADVOCATE_ORCHESTRATOR_PROMPT + FILE_OPERATION_INSTRUCTIONS

        # Add project context
        system_prompt += f"""

PROJECT CONTEXT:
- Title: {project_context.get('title', 'Untitled')}
- Author: {project_context.get('author', 'Unknown')}
- Genre: {project_context.get('genre', 'Not specified')}
- Project Path: {project_context.get('path', '')}
- Premise: {project_context.get('premise', 'Not yet defined')}
- Themes: {project_context.get('themes', 'Not yet defined')}
- Setting: {project_context.get('setting', 'Not yet defined')}

You are responding directly to the user. Generate complete, helpful content for their request.
If creating content, use file_operation tags to save it to the appropriate location.
"""

        # Build conversation
        messages = conversation_history.copy()
        messages.append({"role": "user", "content": user_message})

        # Call the API
        response = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            system=system_prompt,
            messages=messages
        )

        return response.content[0].text


async def stream_orchestrated_response(
    user_message: str,
    project_context: Dict[str, Any],
    conversation_history: List[Dict[str, str]],
    api_key: str,
    model: str = "claude-sonnet-4-5-20250929"
) -> AsyncGenerator[str, None]:
    """
    Stream an orchestrated response for the chat interface.

    This is the main entry point for the chat route.
    """
    orchestrator = StoryOrchestrator(api_key, model)

    async for update in orchestrator.process_request(
        user_message,
        project_context,
        conversation_history
    ):
        yield json.dumps(update)
