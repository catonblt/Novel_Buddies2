import { useState } from 'react';
import { useStore } from '@/lib/store';
import { api } from '@/lib/api';
import { logger } from '@/lib/logger';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Loader2, AlertCircle } from 'lucide-react';
import { invoke } from '@tauri-apps/api/tauri';
import { Alert, AlertDescription } from '@/components/ui/alert';

interface SetupWizardProps {
  onComplete: () => void;
}

const GENRES = [
  'Fantasy',
  'Science Fiction',
  'Mystery',
  'Thriller',
  'Romance',
  'Historical Fiction',
  'Literary Fiction',
  'Horror',
  'Young Adult',
  'Contemporary',
  'Other',
];

export default function SetupWizard({ onComplete }: SetupWizardProps) {
  const [step, setStep] = useState(1);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { setCurrentProject } = useStore();

  // Form state
  const [title, setTitle] = useState('');
  const [author, setAuthor] = useState('');
  const [genre, setGenre] = useState('');
  const [targetWordCount, setTargetWordCount] = useState('80000');
  const [projectPath, setProjectPath] = useState('');

  const [premise, setPremise] = useState('');
  const [themes, setThemes] = useState('');
  const [setting, setSetting] = useState('');
  const [keyCharacters, setKeyCharacters] = useState('');

  const handleSelectPath = async () => {
    logger.userAction('select_project_path', { title });
    setError(null);

    try {
      // Use Tauri dialog to select directory
      const selected = await invoke<string>('select_directory');
      if (selected) {
        // Append project name to path
        const sanitizedTitle = title.replace(/[^a-z0-9]/gi, '-').toLowerCase();
        const fullPath = `${selected}/${sanitizedTitle}`;
        setProjectPath(fullPath);
        logger.info('Project path selected', { path: fullPath });
      }
    } catch (error) {
      logger.error('Failed to select directory', error as Error);

      // Try to get home directory as fallback
      try {
        const homeDir = await invoke<string>('get_home_dir');
        const sanitizedTitle = title.replace(/[^a-z0-9]/gi, '-').toLowerCase();
        const fallbackPath = `${homeDir}/NovelProjects/${sanitizedTitle}`;
        setProjectPath(fallbackPath);
        logger.info('Using fallback project path', { path: fallbackPath });
      } catch (homeDirError) {
        logger.error('Failed to get home directory', homeDirError as Error);
        setError('Could not determine project location. Please enter path manually.');
      }
    }
  };

  const handleCreateProject = async () => {
    setIsLoading(true);
    setError(null);
    logger.userAction('create_project_start', { title, author, genre });

    try {
      // Generate project path if not set
      let finalPath = projectPath;
      if (!finalPath) {
        logger.info('No project path set, determining default path');
        const sanitizedTitle = title.replace(/[^a-z0-9]/gi, '-').toLowerCase();

        try {
          // Use Tauri command to get home directory
          const homeDir = await invoke<string>('get_home_dir');
          finalPath = `${homeDir}/NovelProjects/${sanitizedTitle}`;
          logger.info('Using home directory for project', { path: finalPath });
        } catch (homeDirError) {
          logger.error('Failed to get home directory', homeDirError as Error);
          throw new Error('Could not determine project location. Please select a path manually.');
        }
      }

      logger.info('Creating project', { title, path: finalPath });

      const project = await api.createProject({
        title,
        author,
        genre,
        targetWordCount: parseInt(targetWordCount),
        path: finalPath,
        premise,
        themes,
        setting,
        keyCharacters,
      });

      logger.info('Project created successfully', { projectId: project.id });

      // Initialize git repository (don't fail project creation if this fails)
      try {
        logger.info('Initializing git repository', { path: finalPath });
        const response = await fetch('http://localhost:8000/git/init', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ repo_path: finalPath }),
        });

        if (!response.ok) {
          logger.warn('Failed to initialize git repository', { status: response.status });
        } else {
          logger.info('Git repository initialized successfully');
        }
      } catch (gitError) {
        logger.warn('Git initialization error (non-fatal)', gitError as Error);
        // Don't fail the entire project creation if git init fails
      }

      setCurrentProject(project);
      logger.userAction('create_project_success', { projectId: project.id });
      onComplete();
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
      logger.error('Failed to create project', error as Error, {
        title,
        author,
        genre,
      });
      setError(`Failed to create project: ${errorMessage}`);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-background p-4">
      <Card className="w-full max-w-2xl">
        <CardHeader>
          <CardTitle className="text-3xl">
            {step === 1 ? 'Create Your Novel Project' : 'Tell Me About Your Story'}
          </CardTitle>
          <CardDescription>
            {step === 1
              ? 'Set up the basics for your novel project'
              : 'Optional: Provide some initial context for your AI agents'}
          </CardDescription>
        </CardHeader>

        <CardContent className="space-y-6">
          {error && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          {step === 1 ? (
            <>
              <div className="space-y-2">
                <Label htmlFor="title">Novel Title *</Label>
                <Input
                  id="title"
                  placeholder="The Great Adventure"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="author">Author Name *</Label>
                <Input
                  id="author"
                  placeholder="Your Name"
                  value={author}
                  onChange={(e) => setAuthor(e.target.value)}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="genre">Genre *</Label>
                <Select value={genre} onValueChange={setGenre}>
                  <SelectTrigger id="genre">
                    <SelectValue placeholder="Select a genre" />
                  </SelectTrigger>
                  <SelectContent>
                    {GENRES.map((g) => (
                      <SelectItem key={g} value={g}>
                        {g}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="wordCount">Target Word Count *</Label>
                <Input
                  id="wordCount"
                  type="number"
                  placeholder="80000"
                  value={targetWordCount}
                  onChange={(e) => setTargetWordCount(e.target.value)}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="path">Project Location</Label>
                <div className="flex gap-2">
                  <Input
                    id="path"
                    placeholder="~/NovelProjects/my-novel"
                    value={projectPath}
                    onChange={(e) => setProjectPath(e.target.value)}
                  />
                  <Button type="button" variant="outline" onClick={handleSelectPath}>
                    Browse
                  </Button>
                </div>
              </div>
            </>
          ) : (
            <>
              <div className="space-y-2">
                <Label htmlFor="premise">Core Premise</Label>
                <Textarea
                  id="premise"
                  placeholder="A brief description of your story's central idea..."
                  className="min-h-[100px]"
                  value={premise}
                  onChange={(e) => setPremise(e.target.value)}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="themes">Themes</Label>
                <Textarea
                  id="themes"
                  placeholder="The main themes you want to explore..."
                  className="min-h-[80px]"
                  value={themes}
                  onChange={(e) => setThemes(e.target.value)}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="setting">Setting</Label>
                <Textarea
                  id="setting"
                  placeholder="Where and when does your story take place..."
                  className="min-h-[80px]"
                  value={setting}
                  onChange={(e) => setSetting(e.target.value)}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="characters">Key Characters</Label>
                <Textarea
                  id="characters"
                  placeholder="Main characters and their basic traits..."
                  className="min-h-[80px]"
                  value={keyCharacters}
                  onChange={(e) => setKeyCharacters(e.target.value)}
                />
              </div>
            </>
          )}
        </CardContent>

        <CardFooter className="flex justify-between">
          {step === 2 && (
            <Button variant="outline" onClick={() => setStep(1)}>
              Back
            </Button>
          )}
          {step === 1 ? (
            <Button
              onClick={() => setStep(2)}
              disabled={!title || !author || !genre || !targetWordCount}
              className="ml-auto"
            >
              Next
            </Button>
          ) : (
            <Button onClick={handleCreateProject} disabled={isLoading} className="ml-auto">
              {isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              Create Project
            </Button>
          )}
        </CardFooter>
      </Card>
    </div>
  );
}
