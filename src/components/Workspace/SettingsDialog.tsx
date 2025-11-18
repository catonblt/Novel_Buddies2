import { useState, useEffect } from 'react';
import { useStore } from '@/lib/store';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Slider } from '@/components/ui/slider';
import { Button } from '@/components/ui/button';
import { Switch } from '@/components/ui/switch';
import { Separator } from '@/components/ui/separator';

interface SettingsDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export default function SettingsDialog({ open, onOpenChange }: SettingsDialogProps) {
  const { settings, updateSettings } = useStore();
  const [apiKey, setApiKey] = useState(settings.apiKey);
  const [model, setModel] = useState(settings.model);
  const [autonomyLevel, setAutonomyLevel] = useState(settings.autonomyLevel);
  const [autoCommit, setAutoCommit] = useState(settings.autoCommit);

  useEffect(() => {
    setApiKey(settings.apiKey);
    setModel(settings.model);
    setAutonomyLevel(settings.autonomyLevel);
    setAutoCommit(settings.autoCommit);
  }, [settings]);

  const handleSave = () => {
    updateSettings({
      apiKey,
      model,
      autonomyLevel,
      autoCommit,
    });
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>Settings</DialogTitle>
          <DialogDescription>Configure your Novel Writer preferences</DialogDescription>
        </DialogHeader>

        <div className="space-y-6 py-4">
          <div className="space-y-2">
            <Label htmlFor="apiKey">Anthropic API Key</Label>
            <Input
              id="apiKey"
              type="password"
              placeholder="sk-ant-..."
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="model">Model</Label>
            <Select value={model} onValueChange={setModel}>
              <SelectTrigger id="model">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="claude-sonnet-4-5-20250929">Claude Sonnet 4.5</SelectItem>
                <SelectItem value="claude-haiku-4-5-20251001">Claude Haiku 4.5</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <Separator />

          <div className="space-y-4">
            <h4 className="text-sm font-medium">File Operations</h4>

            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label>Agent Autonomy Level</Label>
                <span className="text-sm text-muted-foreground">
                  {autonomyLevel < 50 ? 'Confirm' : 'Auto'}
                </span>
              </div>
              <Slider
                value={[autonomyLevel]}
                onValueChange={(value) => setAutonomyLevel(value[0])}
                max={100}
                step={1}
                className="w-full"
              />
              <p className="text-xs text-muted-foreground">
                {autonomyLevel < 50
                  ? 'Agents will ask for confirmation before creating, updating, or deleting files'
                  : 'Agents will automatically execute file operations without confirmation'}
              </p>
            </div>

            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label htmlFor="autoCommit">Auto-commit Changes</Label>
                <p className="text-xs text-muted-foreground">
                  Automatically commit file changes to Git
                </p>
              </div>
              <Switch
                id="autoCommit"
                checked={autoCommit}
                onCheckedChange={setAutoCommit}
              />
            </div>
          </div>

          <Separator />

          <Button onClick={handleSave} className="w-full">
            Save Settings
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
