import { useState } from 'react';
import { useStore } from '@/lib/store';
import { api } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Settings, Save, FolderOpen, Loader2, Check } from 'lucide-react';

interface HeaderProps {
  onOpenSettings: () => void;
  onBackToWelcome?: () => void;
}

export default function Header({ onOpenSettings, onBackToWelcome }: HeaderProps) {
  const { currentProject, messages, settings, addNotification } = useStore();
  const [isSaving, setIsSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);

  const handleSave = async () => {
    if (!currentProject) return;

    try {
      setIsSaving(true);
      setSaveSuccess(false);

      await api.saveProjectState(
        currentProject.id,
        settings.apiKey,
        messages.map(msg => ({
          id: msg.id,
          content: msg.content,
          role: msg.role,
          timestamp: msg.timestamp,
          agentType: msg.agentType,
        }))
      );

      setSaveSuccess(true);
      addNotification({
        id: Date.now().toString(),
        type: 'success',
        message: 'Project saved successfully',
        timestamp: Date.now(),
      });

      // Reset success indicator after 2 seconds
      setTimeout(() => setSaveSuccess(false), 2000);
    } catch (error) {
      console.error('Failed to save project:', error);
      addNotification({
        id: Date.now().toString(),
        type: 'error',
        message: 'Failed to save project',
        timestamp: Date.now(),
      });
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <header className="flex h-14 items-center justify-between border-b border-border px-6">
      <div className="flex items-center gap-3">
        {onBackToWelcome && (
          <Button
            variant="ghost"
            size="sm"
            onClick={onBackToWelcome}
            title="Switch Project"
            className="mr-2"
          >
            <FolderOpen className="h-4 w-4 mr-1" />
            Projects
          </Button>
        )}
        <div className="text-xl font-semibold">📚 {currentProject?.title || 'Novel Writer'}</div>
      </div>

      <div className="flex items-center gap-2">
        <Button
          variant="ghost"
          size="icon"
          onClick={handleSave}
          disabled={isSaving || !currentProject}
          title="Save Project"
        >
          {isSaving ? (
            <Loader2 className="h-5 w-5 animate-spin" />
          ) : saveSuccess ? (
            <Check className="h-5 w-5 text-green-500" />
          ) : (
            <Save className="h-5 w-5" />
          )}
        </Button>
        <Button variant="ghost" size="icon" onClick={onOpenSettings} title="Settings">
          <Settings className="h-5 w-5" />
        </Button>
      </div>
    </header>
  );
}
