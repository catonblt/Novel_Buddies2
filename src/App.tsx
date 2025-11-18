import { useState } from 'react';
import { useStore } from './lib/store';
import { api } from './lib/api';
import SetupWizard from './components/SetupWizard/SetupWizard';
import Workspace from './components/Workspace/Workspace';
import WelcomeScreen from './components/WelcomeScreen/WelcomeScreen';
import { Project } from './lib/types';

function App() {
  const { currentProject, setCurrentProject, clearMessages, addMessage, updateSettings } = useStore();
  const [showSetup, setShowSetup] = useState(false);
  const [showWelcome, setShowWelcome] = useState(true);

  const handleSelectProject = async (project: Project) => {
    setCurrentProject(project);
    setShowWelcome(false);
    setShowSetup(false);

    // Load saved state (messages and API key)
    try {
      const state = await api.getProjectState(project.id);

      // Clear existing messages and load saved ones
      clearMessages();
      if (state.messages && state.messages.length > 0) {
        state.messages.forEach((msg: any) => {
          addMessage({
            id: msg.id,
            content: msg.content,
            role: msg.role,
            timestamp: msg.timestamp,
            agentType: msg.agentType,
          });
        });
      }

      // Load saved API key if available
      if (state.api_key) {
        updateSettings({ apiKey: state.api_key });
      }
    } catch (error) {
      console.error('Failed to load project state:', error);
      // Continue anyway - project is still loaded
    }
  };

  const handleCreateNew = () => {
    setShowSetup(true);
    setShowWelcome(false);
  };

  const handleSetupComplete = () => {
    setShowSetup(false);
    setShowWelcome(false);
  };

  const handleBackToWelcome = () => {
    clearMessages();
    setCurrentProject(null);
    setShowWelcome(true);
    setShowSetup(false);
  };

  // Show welcome screen on startup
  if (showWelcome && !currentProject) {
    return (
      <WelcomeScreen
        onSelectProject={handleSelectProject}
        onCreateNew={handleCreateNew}
      />
    );
  }

  // Show setup wizard when creating a new project
  if (showSetup) {
    return <SetupWizard onComplete={handleSetupComplete} />;
  }

  // Show workspace when a project is loaded
  if (currentProject) {
    return <Workspace onBackToWelcome={handleBackToWelcome} />;
  }

  // Fallback to welcome screen
  return (
    <WelcomeScreen
      onSelectProject={handleSelectProject}
      onCreateNew={handleCreateNew}
    />
  );
}

export default App;
