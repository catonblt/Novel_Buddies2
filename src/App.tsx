import { useEffect, useState } from 'react';
import { useStore } from './lib/store';
import { api } from './lib/api';
import SetupWizard from './components/SetupWizard/SetupWizard';
import Workspace from './components/Workspace/Workspace';
import { Loader2 } from 'lucide-react';

function App() {
  const { currentProject, setCurrentProject } = useStore();
  const [isLoading, setIsLoading] = useState(true);
  const [showSetup, setShowSetup] = useState(false);

  useEffect(() => {
    // Load projects and open the most recent one
    const loadProjects = async () => {
      try {
        const projects = await api.listProjects();
        if (projects.length > 0) {
          // Load the most recently updated project
          setCurrentProject(projects[0]);
        } else {
          setShowSetup(true);
        }
      } catch (error) {
        console.error('Failed to load projects:', error);
        setShowSetup(true);
      } finally {
        setIsLoading(false);
      }
    };

    loadProjects();
  }, [setCurrentProject]);

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center bg-background">
        <div className="text-center">
          <Loader2 className="mx-auto h-12 w-12 animate-spin text-primary" />
          <p className="mt-4 text-muted-foreground">Loading Novel Writer...</p>
        </div>
      </div>
    );
  }

  if (showSetup || !currentProject) {
    return <SetupWizard onComplete={() => setShowSetup(false)} />;
  }

  return <Workspace />;
}

export default App;
