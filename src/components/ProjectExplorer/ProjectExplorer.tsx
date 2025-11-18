import { useState, useEffect } from 'react';
import { useStore } from '@/lib/store';
import { api } from '@/lib/api';
import { FileNode } from '@/lib/types';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Input } from '@/components/ui/input';
import { Search, FileText, FolderOpen, Folder, RefreshCw } from 'lucide-react';
import { Button } from '@/components/ui/button';
import FilePreview from './FilePreview';

export default function ProjectExplorer() {
  const { currentProject, selectedFile, setSelectedFile, fileRefreshCounter } = useStore();
  const [files, setFiles] = useState<FileNode[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [expandedFolders, setExpandedFolders] = useState<Set<string>>(new Set());
  const [isRefreshing, setIsRefreshing] = useState(false);

  useEffect(() => {
    if (currentProject) {
      loadFiles();
    }
  }, [currentProject]);

  // Listen for refresh triggers from WebSocket file changes
  useEffect(() => {
    if (currentProject && fileRefreshCounter > 0) {
      loadFiles(true); // Refresh with visual feedback
    }
  }, [fileRefreshCounter]);

  // Auto-poll for file changes every 3 seconds
  useEffect(() => {
    if (!currentProject) return;

    const pollInterval = setInterval(() => {
      loadFiles(false); // Silent refresh without visual indicator
    }, 3000);

    return () => clearInterval(pollInterval);
  }, [currentProject]);

  const loadFiles = async (showRefreshIndicator = false) => {
    if (!currentProject) return;

    if (showRefreshIndicator) {
      setIsRefreshing(true);
    }

    try {
      const fileList = await api.listFiles(currentProject.path);
      setFiles(fileList);

      // Auto-expand planning and manuscript folders on initial load using full paths
      if (!showRefreshIndicator && expandedFolders.size === 0) {
        const basePath = currentProject.path;
        setExpandedFolders(new Set([
          `${basePath}/planning`,
          `${basePath}/manuscript`,
          `${basePath}/characters`
        ]));
      }
    } catch (error) {
      console.error('Failed to load files:', error);
    } finally {
      if (showRefreshIndicator) {
        // Brief delay to show the animation
        setTimeout(() => setIsRefreshing(false), 300);
      }
    }
  };

  const handleManualRefresh = () => {
    loadFiles(true);
  };

  const toggleFolder = (folderPath: string) => {
    setExpandedFolders((prev) => {
      const next = new Set(prev);
      if (next.has(folderPath)) {
        next.delete(folderPath);
      } else {
        next.add(folderPath);
      }
      return next;
    });
  };

  const handleFileClick = async (file: FileNode) => {
    if (file.isDirectory) {
      toggleFolder(file.path);
    } else {
      setSelectedFile(file);
    }
  };

  const renderFileTree = (nodes: FileNode[], depth = 0) => {
    return nodes.map((node) => {
      const isExpanded = expandedFolders.has(node.path);
      const isSelected = selectedFile?.path === node.path;

      return (
        <div key={node.path}>
          <div
            className={`flex cursor-pointer items-center gap-2 rounded px-2 py-1.5 text-sm hover:bg-accent ${
              isSelected ? 'bg-accent' : ''
            }`}
            style={{ paddingLeft: `${depth * 16 + 8}px` }}
            onClick={() => handleFileClick(node)}
          >
            {node.isDirectory ? (
              isExpanded ? (
                <FolderOpen className="h-4 w-4 text-primary" />
              ) : (
                <Folder className="h-4 w-4 text-muted-foreground" />
              )
            ) : (
              <FileText className="h-4 w-4 text-muted-foreground" />
            )}
            <span className={node.isDirectory ? 'font-medium' : ''}>
              {node.name}
            </span>
            {!node.isDirectory && node.size && (
              <span className="ml-auto text-xs text-muted-foreground">
                {(node.size / 1024).toFixed(1)}kb
              </span>
            )}
          </div>

          {node.isDirectory && isExpanded && node.children && (
            <div>{renderFileTree(node.children, depth + 1)}</div>
          )}
        </div>
      );
    });
  };

  // Build file tree - backend now provides children recursively
  const buildTree = (fileList: FileNode[]): FileNode[] => {
    // Backend already provides complete tree with children
    // Just ensure directories come first
    const dirs = fileList.filter((f) => f.isDirectory);
    const filesOnly = fileList.filter((f) => !f.isDirectory);
    return [...dirs, ...filesOnly];
  };

  const tree = buildTree(files);

  return (
    <div className="flex h-full flex-col">
      {/* Search */}
      <div className="border-b border-border p-4">
        <div className="flex gap-2">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              placeholder="Search files..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-9"
            />
          </div>
          <Button
            variant="outline"
            size="icon"
            onClick={handleManualRefresh}
            disabled={isRefreshing}
          >
            <RefreshCw className={`h-4 w-4 ${isRefreshing ? 'animate-spin' : ''}`} />
          </Button>
        </div>
      </div>

      {/* File Tree */}
      <div className="flex-1 overflow-hidden">
        <div className="flex h-full flex-col">
          <ScrollArea className="h-1/2 border-b border-border">
            <div className="p-2">{renderFileTree(tree)}</div>
          </ScrollArea>

          {/* File Preview */}
          <div className="h-1/2">
            <FilePreview />
          </div>
        </div>
      </div>
    </div>
  );
}
