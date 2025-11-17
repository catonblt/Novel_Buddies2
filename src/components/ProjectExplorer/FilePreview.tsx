import { useState, useEffect } from 'react';
import { useStore } from '@/lib/store';
import { api } from '@/lib/api';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Button } from '@/components/ui/button';
import { FileText, History } from 'lucide-react';
import { countWords } from '@/lib/utils';

export default function FilePreview() {
  const { selectedFile } = useStore();
  const [content, setContent] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (selectedFile && !selectedFile.isDirectory) {
      loadFileContent();
    } else {
      setContent('');
    }
  }, [selectedFile]);

  const loadFileContent = async () => {
    if (!selectedFile) return;

    setIsLoading(true);
    try {
      const fileContent = await api.readFile(selectedFile.path);
      setContent(fileContent);
    } catch (error) {
      console.error('Failed to load file:', error);
      setContent('Error loading file');
    } finally {
      setIsLoading(false);
    }
  };

  if (!selectedFile) {
    return (
      <div className="flex h-full items-center justify-center text-muted-foreground">
        <div className="text-center">
          <FileText className="mx-auto h-12 w-12 opacity-20" />
          <p className="mt-2 text-sm">Select a file to preview</p>
        </div>
      </div>
    );
  }

  if (selectedFile.isDirectory) {
    return (
      <div className="flex h-full items-center justify-center text-muted-foreground">
        <p className="text-sm">This is a directory</p>
      </div>
    );
  }

  const wordCount = countWords(content);

  return (
    <div className="flex h-full flex-col">
      {/* Preview Header */}
      <div className="flex items-center justify-between border-b border-border px-4 py-2">
        <div className="flex-1 truncate">
          <p className="text-sm font-medium">{selectedFile.name}</p>
          <p className="text-xs text-muted-foreground">{wordCount} words</p>
        </div>
        <Button variant="ghost" size="sm" title="View History">
          <History className="h-4 w-4" />
        </Button>
      </div>

      {/* Content */}
      <ScrollArea className="flex-1">
        {isLoading ? (
          <div className="flex h-full items-center justify-center">
            <p className="text-sm text-muted-foreground">Loading...</p>
          </div>
        ) : (
          <div className="p-4">
            <pre className="whitespace-pre-wrap font-sans text-sm">
              {content}
            </pre>
          </div>
        )}
      </ScrollArea>
    </div>
  );
}
