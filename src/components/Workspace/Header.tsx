import { useStore } from '@/lib/store';
import { Button } from '@/components/ui/button';
import { Settings, BarChart3, Save, FolderOpen } from 'lucide-react';

interface HeaderProps {
  onOpenSettings: () => void;
  onBackToWelcome?: () => void;
}

export default function Header({ onOpenSettings, onBackToWelcome }: HeaderProps) {
  const { currentProject } = useStore();

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
        <Button variant="ghost" size="icon" title="Statistics">
          <BarChart3 className="h-5 w-5" />
        </Button>
        <Button variant="ghost" size="icon" title="Save">
          <Save className="h-5 w-5" />
        </Button>
        <Button variant="ghost" size="icon" onClick={onOpenSettings} title="Settings">
          <Settings className="h-5 w-5" />
        </Button>
      </div>
    </header>
  );
}
