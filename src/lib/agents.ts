import { Agent } from './types';

// Story Advocate is the single user-facing agent
export const STORY_ADVOCATE: Agent = {
  name: 'Story Advocate',
  icon: '🎭',
  color: '#8b5cf6',
  description: 'Your writing partner - coordinates all agents to help you create your story',
};

// Agent info for display in status messages
export const AGENT_INFO: Record<string, { name: string; icon: string; color: string }> = {
  story_advocate: {
    name: 'Story Advocate',
    icon: '🎭',
    color: '#8b5cf6',
  },
  architect: {
    name: 'Architect',
    icon: '🏛️',
    color: '#6366f1',
  },
  prose_stylist: {
    name: 'Prose Stylist',
    icon: '✍️',
    color: '#06b6d4',
  },
  character_psychologist: {
    name: 'Character Psychologist',
    icon: '👤',
    color: '#ec4899',
  },
  atmosphere: {
    name: 'Atmosphere',
    icon: '🌅',
    color: '#f59e0b',
  },
  research: {
    name: 'Research',
    icon: '📚',
    color: '#10b981',
  },
  continuity: {
    name: 'Continuity',
    icon: '🔗',
    color: '#8b5cf6',
  },
  redundancy: {
    name: 'Redundancy',
    icon: '🔄',
    color: '#f43f5e',
  },
  beta_reader: {
    name: 'Beta Reader',
    icon: '📖',
    color: '#0ea5e9',
  },
};
