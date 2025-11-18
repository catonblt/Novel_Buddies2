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

interface SettingsDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export default function SettingsDialog({ open, onOpenChange }: SettingsDialogProps) {
  const { settings, updateSettings } = useStore();
  const [apiKey, setApiKey] = useState(settings.apiKey);
  const [model, setModel] = useState(settings.model);
  const [autonomyLevel, setAutonomyLevel] = useState(settings.autonomyLevel);

  useEffect(() => {
    setApiKey(settings.apiKey);
    setModel(settings.model);
    setAutonomyLevel(settings.autonomyLevel);
  }, [settings]);

  const handleSave = () => {
    updateSettings({
      apiKey,
      model,
      autonomyLevel,
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

          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <Label>Agent Autonomy Level</Label>
              <span className="text-sm text-muted-foreground">
                {autonomyLevel < 33 ? 'Low' : autonomyLevel < 66 ? 'Medium' : 'High'}
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
              {autonomyLevel < 33
                ? 'Agents always ask before making changes'
                : autonomyLevel < 66
                ? 'Agents make minor changes automatically'
                : 'Agents work autonomously (you can undo via version history)'}
            </p>
          </div>

          <Button onClick={handleSave} className="w-full">
            Save Settings
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
