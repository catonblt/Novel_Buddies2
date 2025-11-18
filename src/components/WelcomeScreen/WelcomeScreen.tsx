import { useState, useEffect } from 'react';
import { api } from '@/lib/api';
import { Project } from '@/lib/types';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Loader2, Plus, FolderOpen, BookOpen, Calendar, User } from 'lucide-react';

interface WelcomeScreenProps {
  onSelectProject: (project: Project) => void;
  onCreateNew: () => void;
}

export default function WelcomeScreen({ onSelectProject, onCreateNew }: WelcomeScreenProps) {
  const [projects, setProjects] = useState<Project[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadProjects();
  }, []);

  const loadProjects = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const projectList = await api.listProjects();
      setProjects(projectList);
    } catch (err) {
      console.error('Failed to load projects:', err);
      setError('Failed to load projects. Please ensure the backend is running.');
    } finally {
      setIsLoading(false);
    }
  };

  const formatDate = (timestamp: number) => {
    return new Date(timestamp).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center bg-background">
        <div className="text-center">
          <Loader2 className="mx-auto h-12 w-12 animate-spin text-primary" />
          <p className="mt-4 text-muted-foreground">Loading projects...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-background p-4">
      <div className="w-full max-w-3xl">
        <div className="mb-8 text-center">
          <h1 className="text-4xl font-bold mb-2">Novel Writer</h1>
          <p className="text-muted-foreground">Your AI-powered writing companion</p>
        </div>

        {error && (
          <Card className="mb-6 border-destructive">
            <CardContent className="pt-6">
              <p className="text-destructive">{error}</p>
              <Button variant="outline" className="mt-2" onClick={loadProjects}>
                Retry
              </Button>
            </CardContent>
          </Card>
        )}

        <Card>
          <CardHeader>
            <CardTitle>Welcome</CardTitle>
            <CardDescription>
              Open an existing project or start a new one
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* New Project Button */}
            <Button
              onClick={onCreateNew}
              className="w-full h-14 text-lg"
              size="lg"
            >
              <Plus className="mr-2 h-5 w-5" />
              Create New Project
            </Button>

            {/* Existing Projects */}
            {projects.length > 0 && (
              <div className="mt-6">
                <h3 className="text-sm font-medium text-muted-foreground mb-3 flex items-center">
                  <FolderOpen className="mr-2 h-4 w-4" />
                  Recent Projects
                </h3>
                <div className="space-y-2 max-h-80 overflow-y-auto">
                  {projects.map((project) => (
                    <button
                      key={project.id}
                      onClick={() => onSelectProject(project)}
                      className="w-full text-left p-4 rounded-lg border border-border hover:border-primary hover:bg-accent transition-colors"
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2">
                            <BookOpen className="h-4 w-4 text-primary shrink-0" />
                            <span className="font-medium truncate">{project.title}</span>
                          </div>
                          <div className="flex items-center gap-4 mt-1 text-sm text-muted-foreground">
                            <span className="flex items-center gap-1">
                              <User className="h-3 w-3" />
                              {project.author}
                            </span>
                            <span>{project.genre}</span>
                          </div>
                        </div>
                        <div className="text-xs text-muted-foreground flex items-center gap-1 shrink-0 ml-4">
                          <Calendar className="h-3 w-3" />
                          {formatDate(project.updatedAt)}
                        </div>
                      </div>
                      {project.premise && (
                        <p className="mt-2 text-sm text-muted-foreground line-clamp-2">
                          {project.premise}
                        </p>
                      )}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {projects.length === 0 && !error && (
              <div className="text-center py-8 text-muted-foreground">
                <BookOpen className="mx-auto h-12 w-12 mb-4 opacity-50" />
                <p>No projects yet. Create your first novel project!</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
