"""
Agent Pipeline Module

This module provides the AgentPipeline class for processing story content
through all nine literary agents in sequence. It handles agent execution,
result synthesis, and recommendation prioritization.
"""

import json
import asyncio
import time
from typing import Dict, List, Optional, Any
from anthropic import AsyncAnthropic
from .literary_agents import LITERARY_AGENT_PROMPTS, get_agent_personality


# Processing order for agents
AGENT_PROCESSING_ORDER = [
    "architect",           # Structural analysis first
    "character_psychologist",  # Character depth and consistency
    "prose_stylist",       # Language and style review
    "atmosphere",          # Setting and mood analysis
    "research",            # Fact-checking and accuracy
    "continuity",          # Internal consistency check
    "redundancy",          # Repetition detection
    "beta_reader",         # Reader experience simulation
    "story_advocate"       # Synthesis and recommendation
]

# Agents that can run in parallel (no dependencies on each other)
PARALLEL_BATCH_1 = ["architect", "character_psychologist", "prose_stylist", "atmosphere"]
PARALLEL_BATCH_2 = ["research", "continuity", "redundancy"]
FINAL_AGENTS = ["beta_reader", "story_advocate"]


def detect_content_type(message: str, context: dict) -> str:
    """
    Determine what type of content is being created.

    Args:
        message: The user's message
        context: Additional context about the project

    Returns:
        Content type: 'outline', 'chapter', 'scene', 'character',
                     'dialogue', 'description', 'revision', or 'general'
    """
    message_lower = message.lower()

    # Check for explicit content type indicators
    if any(word in message_lower for word in ['outline', 'structure', 'plot', 'arc', 'plan']):
        return 'outline'

    if any(word in message_lower for word in ['chapter', 'write chapter']):
        return 'chapter'

    if any(word in message_lower for word in ['scene', 'write scene']):
        return 'scene'

    if any(word in message_lower for word in ['character', 'protagonist', 'antagonist', 'profile']):
        return 'character'

    if any(word in message_lower for word in ['dialogue', 'conversation', 'talk', 'speak']):
        return 'dialogue'

    if any(word in message_lower for word in ['describe', 'description', 'setting', 'atmosphere']):
        return 'description'

    if any(word in message_lower for word in ['revise', 'edit', 'improve', 'rewrite', 'fix']):
        return 'revision'

    # Default to general
    return 'general'


def should_enhance_with_literary_agents(content_type: str, message: str) -> bool:
    """
    Determine if content should be processed through the literary agents pipeline.

    Args:
        content_type: Type of content being created
        message: The original message

    Returns:
        True if content should go through literary analysis
    """
    # Content types that benefit from literary analysis
    substantial_types = {'outline', 'chapter', 'scene', 'character', 'dialogue', 'description', 'revision'}

    # Check if content type warrants analysis
    if content_type not in substantial_types:
        return False

    # Check message length - very short messages probably don't need full analysis
    if len(message) < 50:
        return False

    return True


class AgentPipeline:
    """
    Processes story content through all nine literary agents in sequence.
    Each agent analyzes, provides feedback, and suggests improvements.
    """

    def __init__(self):
        self.client = None

    def _get_client(self, api_key: str) -> AsyncAnthropic:
        """Get or create an Anthropic client."""
        if self.client is None or True:  # Always create new for different keys
            self.client = AsyncAnthropic(api_key=api_key)
        return self.client

    async def process_story_content(
        self,
        content: str,
        content_type: str,
        project_context: dict,
        api_key: str,
        parallel: bool = True
    ) -> dict:
        """
        Run content through all agents and return comprehensive analysis.

        Args:
            content: The story content to analyze
            content_type: Type of content ('outline', 'chapter', etc.)
            project_context: Project metadata and context
            api_key: Anthropic API key
            parallel: Whether to run independent agents in parallel

        Returns:
            Dictionary with all agent analyses and synthesis
        """
        start_time = time.time()

        agent_analyses = {}

        if parallel:
            # Run agents in parallel batches
            # Batch 1: Core analysis agents
            batch1_results = await asyncio.gather(
                *[
                    self.run_single_agent(
                        agent_type=agent,
                        content=content,
                        context=project_context,
                        previous_analyses={},
                        api_key=api_key,
                        content_type=content_type
                    )
                    for agent in PARALLEL_BATCH_1
                ],
                return_exceptions=True
            )

            for agent, result in zip(PARALLEL_BATCH_1, batch1_results):
                if isinstance(result, Exception):
                    agent_analyses[agent] = {"error": str(result)}
                else:
                    agent_analyses[agent] = result

            # Batch 2: Secondary analysis agents
            batch2_results = await asyncio.gather(
                *[
                    self.run_single_agent(
                        agent_type=agent,
                        content=content,
                        context=project_context,
                        previous_analyses=agent_analyses,
                        api_key=api_key,
                        content_type=content_type
                    )
                    for agent in PARALLEL_BATCH_2
                ],
                return_exceptions=True
            )

            for agent, result in zip(PARALLEL_BATCH_2, batch2_results):
                if isinstance(result, Exception):
                    agent_analyses[agent] = {"error": str(result)}
                else:
                    agent_analyses[agent] = result

            # Final agents run sequentially as they need previous results
            for agent in FINAL_AGENTS:
                try:
                    result = await self.run_single_agent(
                        agent_type=agent,
                        content=content,
                        context=project_context,
                        previous_analyses=agent_analyses,
                        api_key=api_key,
                        content_type=content_type
                    )
                    agent_analyses[agent] = result
                except Exception as e:
                    agent_analyses[agent] = {"error": str(e)}

        else:
            # Sequential processing
            for agent in AGENT_PROCESSING_ORDER:
                try:
                    result = await self.run_single_agent(
                        agent_type=agent,
                        content=content,
                        context=project_context,
                        previous_analyses=agent_analyses,
                        api_key=api_key,
                        content_type=content_type
                    )
                    agent_analyses[agent] = result
                except Exception as e:
                    agent_analyses[agent] = {"error": str(e)}

        # Generate synthesis from story_advocate's analysis
        synthesis = self._extract_synthesis(agent_analyses)

        # Extract prioritized suggestions
        suggestions = self._extract_suggestions(agent_analyses)

        # Identify critical issues
        critical_issues = self._extract_critical_issues(agent_analyses)

        processing_time = time.time() - start_time

        return {
            "original_content": content,
            "content_type": content_type,
            "agent_analyses": agent_analyses,
            "synthesis": synthesis,
            "suggested_improvements": suggestions,
            "critical_issues": critical_issues,
            "processing_time_seconds": round(processing_time, 2)
        }

    async def run_single_agent(
        self,
        agent_type: str,
        content: str,
        context: dict,
        previous_analyses: dict,
        api_key: str,
        content_type: str = "general"
    ) -> dict:
        """
        Run a single agent analysis.

        Args:
            agent_type: Type of agent to run
            content: Content to analyze
            context: Project context
            previous_analyses: Analyses from agents that ran before this one
            api_key: Anthropic API key
            content_type: Type of content being analyzed

        Returns:
            Dictionary with agent's analysis results
        """
        client = self._get_client(api_key)

        # Get the agent's system prompt
        system_prompt = LITERARY_AGENT_PROMPTS[agent_type]

        # Build the user message with context
        user_message = self._build_agent_message(
            content=content,
            content_type=content_type,
            context=context,
            previous_analyses=previous_analyses,
            agent_type=agent_type
        )

        try:
            response = await client.messages.create(
                model="claude-sonnet-4-5-20250929",
                max_tokens=4096,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_message}
                ]
            )

            # Extract the response text
            response_text = response.content[0].text

            # Try to parse as JSON
            try:
                # Find JSON in the response (it might be wrapped in markdown code blocks)
                json_text = self._extract_json(response_text)
                result = json.loads(json_text)
            except (json.JSONDecodeError, ValueError):
                # If not valid JSON, return as raw analysis
                result = {
                    "raw_analysis": response_text,
                    "parse_error": "Response was not valid JSON"
                }

            return result

        except Exception as e:
            return {
                "error": str(e),
                "agent_type": agent_type
            }

    def _build_agent_message(
        self,
        content: str,
        content_type: str,
        context: dict,
        previous_analyses: dict,
        agent_type: str
    ) -> str:
        """
        Build the message to send to an agent.

        Args:
            content: Content to analyze
            content_type: Type of content
            context: Project context
            previous_analyses: Previous agent analyses
            agent_type: Current agent type

        Returns:
            Formatted message string
        """
        # Build project context section
        project_info = []
        if context.get("title"):
            project_info.append(f"Title: {context['title']}")
        if context.get("author"):
            project_info.append(f"Author: {context['author']}")
        if context.get("genre"):
            project_info.append(f"Genre: {context['genre']}")
        if context.get("premise"):
            project_info.append(f"Premise: {context['premise']}")
        if context.get("themes"):
            project_info.append(f"Themes: {context['themes']}")
        if context.get("setting"):
            project_info.append(f"Setting: {context['setting']}")

        project_section = "\n".join(project_info) if project_info else "No project context available"

        # Build previous analyses section (only for agents that need it)
        prev_section = ""
        if previous_analyses and agent_type in ["beta_reader", "story_advocate"]:
            prev_insights = []
            for prev_agent, analysis in previous_analyses.items():
                if "error" not in analysis:
                    # Extract key insights from each agent
                    if "strengths" in analysis:
                        prev_insights.append(f"{prev_agent.upper()} strengths: {analysis['strengths']}")
                    if "concerns" in analysis:
                        prev_insights.append(f"{prev_agent.upper()} concerns: {analysis['concerns']}")

            if prev_insights:
                prev_section = f"""

## Previous Agent Insights
{chr(10).join(prev_insights)}
"""

        message = f"""## Project Context
{project_section}

## Content Type
{content_type}

## Content to Analyze

{content}
{prev_section}

Please analyze this content according to your role and provide your analysis in the JSON format specified in your instructions. Focus on providing specific, actionable feedback that will help improve this {content_type}.
"""

        return message

    def _extract_json(self, text: str) -> str:
        """
        Extract JSON from a response that might be wrapped in markdown code blocks.

        Args:
            text: Response text that may contain JSON

        Returns:
            Extracted JSON string
        """
        # Try to find JSON in code blocks
        if "```json" in text:
            start = text.find("```json") + 7
            end = text.find("```", start)
            if end != -1:
                return text[start:end].strip()

        if "```" in text:
            start = text.find("```") + 3
            end = text.find("```", start)
            if end != -1:
                return text[start:end].strip()

        # Try to find JSON object directly
        if "{" in text:
            start = text.find("{")
            # Find matching closing brace
            depth = 0
            for i, char in enumerate(text[start:], start):
                if char == "{":
                    depth += 1
                elif char == "}":
                    depth -= 1
                    if depth == 0:
                        return text[start:i+1]

        return text

    def _extract_synthesis(self, agent_analyses: dict) -> str:
        """
        Extract the synthesis from story_advocate's analysis.

        Args:
            agent_analyses: All agent analyses

        Returns:
            Synthesis string
        """
        advocate = agent_analyses.get("story_advocate", {})

        if "overall_assessment" in advocate:
            return advocate["overall_assessment"]

        if "executive_summary" in advocate:
            summary = advocate["executive_summary"]
            return summary.get("one_line_summary", "Analysis complete.")

        return "Analysis complete. See individual agent results for details."

    def _extract_suggestions(self, agent_analyses: dict) -> list:
        """
        Extract and prioritize suggestions from all agents.

        Args:
            agent_analyses: All agent analyses

        Returns:
            Prioritized list of suggestions
        """
        all_suggestions = []

        for agent_type, analysis in agent_analyses.items():
            if isinstance(analysis, dict) and "suggestions" in analysis:
                for suggestion in analysis["suggestions"]:
                    if isinstance(suggestion, dict):
                        suggestion["source_agent"] = agent_type
                        all_suggestions.append(suggestion)

        # Sort by priority
        priority_order = {"high": 0, "medium": 1, "low": 2}
        all_suggestions.sort(
            key=lambda x: priority_order.get(x.get("priority", "low"), 2)
        )

        return all_suggestions

    def _extract_critical_issues(self, agent_analyses: dict) -> list:
        """
        Extract critical issues that need immediate attention.

        Args:
            agent_analyses: All agent analyses

        Returns:
            List of critical issues
        """
        critical = []

        for agent_type, analysis in agent_analyses.items():
            if isinstance(analysis, dict):
                # Check for high priority suggestions
                if "suggestions" in analysis:
                    for suggestion in analysis["suggestions"]:
                        if isinstance(suggestion, dict):
                            if suggestion.get("priority") == "high":
                                critical.append({
                                    "agent": agent_type,
                                    "issue": suggestion.get("change") or suggestion.get("issue") or suggestion.get("recommendation"),
                                    "rationale": suggestion.get("rationale", "")
                                })

                # Check for concerns
                if "concerns" in analysis:
                    for concern in analysis["concerns"][:2]:  # Top 2 concerns per agent
                        if isinstance(concern, str):
                            critical.append({
                                "agent": agent_type,
                                "issue": concern
                            })

        # Deduplicate and limit
        seen = set()
        unique_critical = []
        for item in critical:
            key = item.get("issue", "")[:50]
            if key not in seen:
                seen.add(key)
                unique_critical.append(item)

        return unique_critical[:10]  # Top 10 critical issues


def format_analysis_for_display(analysis_result: dict) -> str:
    """
    Format the analysis result for display to the user.

    Args:
        analysis_result: Result from process_story_content

    Returns:
        Formatted string for display
    """
    lines = []

    # Header
    lines.append("\n---\n")
    lines.append("## Literary Agent Analysis\n")

    # Processing time
    time_taken = analysis_result.get("processing_time_seconds", 0)
    lines.append(f"*Analysis completed in {time_taken}s*\n")

    # Strengths section
    strengths = []
    for agent_type, analysis in analysis_result.get("agent_analyses", {}).items():
        if isinstance(analysis, dict) and "strengths" in analysis:
            for strength in analysis["strengths"][:2]:
                if isinstance(strength, str):
                    agent_name = agent_type.replace("_", " ").title()
                    strengths.append(f"- {strength} ({agent_name})")

    if strengths:
        lines.append("### Strengths Identified\n")
        lines.extend(strengths[:6])
        lines.append("")

    # Critical issues section
    critical = analysis_result.get("critical_issues", [])
    if critical:
        lines.append("\n### Areas for Improvement\n")
        for issue in critical[:5]:
            agent_name = issue.get("agent", "").replace("_", " ").title()
            issue_text = issue.get("issue", "")
            if issue_text:
                lines.append(f"- {issue_text} ({agent_name})")
        lines.append("")

    # Top suggestions
    suggestions = analysis_result.get("suggested_improvements", [])
    high_priority = [s for s in suggestions if s.get("priority") == "high"]

    if high_priority:
        lines.append("\n### Priority Suggestions\n")
        for i, suggestion in enumerate(high_priority[:3], 1):
            agent_name = suggestion.get("source_agent", "").replace("_", " ").title()
            change = suggestion.get("change") or suggestion.get("recommendation") or suggestion.get("issue", "")
            rationale = suggestion.get("rationale", "")

            lines.append(f"{i}. **{change}**")
            if rationale:
                lines.append(f"   - {rationale}")
            lines.append(f"   - *Source: {agent_name}*")
        lines.append("")

    # Synthesis
    synthesis = analysis_result.get("synthesis", "")
    if synthesis:
        lines.append("\n### Overall Assessment\n")
        lines.append(synthesis)

    return "\n".join(lines)


# Singleton instance for import
pipeline = AgentPipeline()
