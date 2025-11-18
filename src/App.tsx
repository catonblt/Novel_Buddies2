import { useState } from 'react';
import { useStore } from './lib/store';
import SetupWizard from './components/SetupWizard/SetupWizard';
import Workspace from './components/Workspace/Workspace';
import WelcomeScreen from './components/WelcomeScreen/WelcomeScreen';
import { Project } from './lib/types';

function App() {
  const { currentProject, setCurrentProject } = useStore();
  const [showSetup, setShowSetup] = useState(false);
  const [showWelcome, setShowWelcome] = useState(true);

  const handleSelectProject = (project: Project) => {
    setCurrentProject(project);
    setShowWelcome(false);
    setShowSetup(false);
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
