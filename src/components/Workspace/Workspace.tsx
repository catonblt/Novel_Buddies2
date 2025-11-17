import { useState } from 'react';
import { useStore } from '@/lib/store';
import AgentChat from '../AgentChat/AgentChat';
import ProjectExplorer from '../ProjectExplorer/ProjectExplorer';
import Header from './Header';
import SettingsDialog from './SettingsDialog';

export default function Workspace() {
  const { currentProject } = useStore();
  const [showSettings, setShowSettings] = useState(false);

  if (!currentProject) {
    return null;
  }

  return (
    <div className="flex h-screen flex-col bg-background">
      <Header onOpenSettings={() => setShowSettings(true)} />

      <div className="flex flex-1 overflow-hidden">
        {/* Agent Chat - 60% */}
        <div className="w-[60%] border-r border-border">
          <AgentChat />
        </div>

        {/* Project Explorer - 40% */}
        <div className="w-[40%]">
          <ProjectExplorer />
        </div>
      </div>

      <SettingsDialog open={showSettings} onOpenChange={setShowSettings} />
    </div>
  );
}
