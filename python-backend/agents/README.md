# Literary Fiction Agents System

## Overview

The Literary Fiction Agents system provides sophisticated analysis and enhancement of story content through nine specialized AI agents. Each agent focuses on a specific aspect of literary fiction craft and works together through a coordinated pipeline to provide comprehensive feedback.

This system runs invisibly in the backend - the frontend continues to work with the five simple agents while this system enhances the output with detailed literary analysis.

## Architecture

### Agent Types

1. **Architect Agent** - Narrative Structure & Thematic Orchestrator
   - Story architecture and act structure design
   - Character arc mapping
   - Thematic coherence analysis
   - Pacing orchestration
   - *Personality: thoughtful, strategic, big-picture focused*

2. **Prose Stylist Agent** - Sentence-Level Craftsperson & Voice Keeper
   - Word choice precision
   - Sentence rhythm and music
   - Voice development
   - Sensory richness evaluation
   - *Personality: precise, attentive to language, artistic*

3. **Character Psychologist Agent** - Interior Life Architect & Dialogue Specialist
   - Psychological complexity
   - Motivation architecture
   - Defense mechanisms and self-deception patterns
   - Dialogue authenticity and subtext
   - *Personality: empathetic, insightful, depth-oriented*

4. **Atmosphere & Setting Agent** - Environmental Designer & Sensory World Builder
   - Sensory immersion
   - Atmospheric mood creation
   - Thematic embodiment in settings
   - Psychological reflection through environment
   - *Personality: sensory, immersive, mood-focused*

5. **Research & Accuracy Agent** - Fact Investigator & Verisimilitude Guarantor
   - Historical accuracy
   - Technical accuracy
   - Cultural accuracy
   - Geographic and professional accuracy
   - *Personality: thorough, factual, detail-oriented*

6. **Continuity & Logic Editor Agent** - Internal Consistency Guardian
   - Timeline tracking
   - Character consistency monitoring
   - Plot logic verification
   - World-building consistency
   - *Personality: logical, systematic, consistency-focused*

7. **Redundancy Editor Agent** - Repetition Detector & Variation Enforcer
   - Word and phrase repetition detection
   - Scene redundancy analysis
   - Thematic redundancy identification
   - Cliché detection
   - *Personality: sharp, economical, variation-focused*

8. **Beta Reader Agent** - Critical Reader & Narrative Effectiveness Analyst
   - Reader experience analysis
   - Emotional resonance testing
   - Pacing assessment
   - Engagement measurement
   - *Personality: honest, reader-focused, engagement-oriented*

9. **Story Advocate Agent** - Human Liaison & Narrative Plausibility Counselor
   - Synthesis of all agent analyses
   - Prioritized recommendations
   - Trade-off navigation
   - Quality advocacy
   - *Personality: diplomatic, communicative, balance-focused*

## Processing Pipeline

### Execution Order

The agents process content in a specific order to maximize effectiveness:

**Parallel Batch 1** (run simultaneously):
- Architect
- Character Psychologist
- Prose Stylist
- Atmosphere

**Parallel Batch 2** (run simultaneously):
- Research
- Continuity
- Redundancy

**Final Agents** (run sequentially):
- Beta Reader
- Story Advocate (synthesizes all previous analyses)

### Content Type Detection

The system automatically detects what type of content is being processed:

- `outline` - Story structure and plot planning
- `chapter` - Full chapter content
- `scene` - Individual scenes
- `character` - Character profiles and development
- `dialogue` - Conversation and speech
- `description` - Setting and atmosphere descriptions
- `revision` - Editing and rewriting tasks
- `general` - Other content types

### When Agents Run

The literary agents pipeline activates when:
1. `enable_literary_agents` is true for the project (default)
2. The content type is substantial (outline, chapter, scene, character, dialogue, description, or revision)
3. The message is longer than 50 characters

## Integration

### Chat Endpoint

The agents integrate with the existing `/api/chat` endpoint. When literary analysis is enabled:

1. The simple agent generates its response
2. The pipeline analyzes the response
3. Results are streamed to the frontend in additional events:
   - `literary_analysis_start` - Analysis beginning
   - `literary_analysis` - Complete analysis results
   - `literary_analysis_error` - If analysis fails

### Database Storage

Analyses are stored in two tables:

**agent_analyses** - Individual agent results
- `id` - Unique identifier
- `project_id` - Associated project
- `content_id` - Groups analyses of the same content
- `content_type` - Type of content analyzed
- `agent_type` - Which agent performed analysis
- `analysis_result` - JSON analysis data
- `timestamp` - When analysis occurred

**content_versions** - Content with analysis references
- `id` - Unique identifier
- `project_id` - Associated project
- `content_type` - Type of content
- `original_content` - The content that was analyzed
- `enhanced_content` - Optional enhanced version
- `agent_analyses_id` - Link to analysis group
- `timestamp` - When created

### Project Settings

Projects have configuration options for literary agents:

```python
# In Project model
enable_literary_agents = Boolean, default=True
agent_intervention_level = String, default="moderate"  # 'light', 'moderate', 'intensive'
auto_apply_suggestions = Boolean, default=False
```

## Usage

### Python API

```python
from agents.pipeline import pipeline, detect_content_type

# Detect content type
content_type = detect_content_type(user_message, context)

# Process through pipeline
result = await pipeline.process_story_content(
    content=story_content,
    content_type=content_type,
    project_context={
        "title": "My Novel",
        "author": "Author Name",
        "genre": "Literary Fiction",
        "premise": "Story premise...",
        "themes": "Main themes...",
        "setting": "Story setting..."
    },
    api_key=api_key,
    parallel=True  # Run independent agents in parallel
)

# Result structure
{
    "original_content": str,
    "content_type": str,
    "agent_analyses": {
        "architect": {...},
        "prose_stylist": {...},
        # ... all 9 agents
    },
    "synthesis": str,
    "suggested_improvements": [...],
    "critical_issues": [...],
    "processing_time_seconds": float
}
```

### Single Agent Analysis

```python
result = await pipeline.run_single_agent(
    agent_type="prose_stylist",
    content=content,
    context=project_context,
    previous_analyses={},  # Results from earlier agents
    api_key=api_key,
    content_type="chapter"
)
```

## Output Format

### Formatted Display

Use `format_analysis_for_display()` to get human-readable output:

```markdown
---

## Literary Agent Analysis

*Analysis completed in 15.2s*

### Strengths Identified
- Strong thematic development (Architect)
- Vivid sensory details (Atmosphere)
- Authentic dialogue (Character Psychologist)

### Areas for Improvement
- Pacing lags in middle section (Beta Reader)
- Two scenes serve similar function (Redundancy)

### Priority Suggestions
1. **Consider cutting the dinner scene**
   - It retreads the revelation from the prior scene
   - *Source: Redundancy Editor*

### Overall Assessment
[Synthesis from Story Advocate]
```

### JSON Analysis Structure

Each agent returns structured JSON with:
- `strengths` - What works well
- `concerns` - Issues to address
- `suggestions` - Specific improvements with priority levels (high/medium/low)
- Agent-specific analysis sections

## Configuration

### Environment Variables

No additional environment variables required. Uses existing:
- `DATABASE_URL` - Database connection
- API key passed in chat request

### Performance

- **Caching**: Analyses are stored in database
- **Parallel Processing**: Independent agents run concurrently
- **Selective Processing**: Only substantial content triggers analysis
- **Timeout**: Uses Claude API default timeouts

## Error Handling

- Pipeline failures don't interrupt simple agent response
- Individual agent failures are logged but don't stop pipeline
- Errors are reported in `literary_analysis_error` event
- Graceful degradation if any agent fails

## Development

### Adding New Agents

1. Add prompt to `LITERARY_AGENT_PROMPTS` in `literary_agents.py`
2. Add personality to `AGENT_PERSONALITIES`
3. Update `AGENT_PROCESSING_ORDER` in `pipeline.py`
4. Consider if agent can run in parallel batches

### Testing

```python
# Test content type detection
assert detect_content_type("write chapter 1", {}) == "chapter"

# Test pipeline
result = await pipeline.process_story_content(...)
assert "architect" in result["agent_analyses"]
assert "synthesis" in result
```

## Best Practices

### For Writers

1. **Review synthesis first** - Story Advocate provides prioritized recommendations
2. **Focus on high-priority suggestions** - These have the most impact
3. **Consider trade-offs** - Some suggestions may conflict
4. **Trust your judgment** - Agents advise, you decide

### For Developers

1. **Monitor performance** - Check processing times
2. **Handle errors gracefully** - Don't let agent failures break the app
3. **Cache appropriately** - Avoid redundant analysis
4. **Respect rate limits** - Multiple agent calls use API quota

## Troubleshooting

### Common Issues

1. **Pipeline timeout**
   - Check API key validity
   - Reduce content size
   - Check network connectivity

2. **Invalid JSON response**
   - Agent returned non-JSON format
   - Raw response available in `raw_analysis`

3. **Missing analyses**
   - Check agent_analyses for error entries
   - Review logs for exceptions

### Logs

Pipeline logs to the application logger:
- Agent interaction start/complete
- Processing time
- Errors and exceptions
- Database operations

## Future Enhancements

Planned improvements:
- Agent voting on suggestions
- Learning from user feedback
- Genre-specific agent variants
- Custom agent configurations per project
