import { useState, useEffect } from 'react';
import { useStore } from '@/lib/store';
import { api } from '@/lib/api';
import { FileNode } from '@/lib/types';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Input } from '@/components/ui/input';
import { Search, FileText, FolderOpen, Folder } from 'lucide-react';
import FilePreview from './FilePreview';

export default function ProjectExplorer() {
  const { currentProject, selectedFile, setSelectedFile } = useStore();
  const [files, setFiles] = useState<FileNode[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [expandedFolders, setExpandedFolders] = useState<Set<string>>(new Set());

  useEffect(() => {
    if (currentProject) {
      loadFiles();
    }
  }, [currentProject]);

  const loadFiles = async () => {
    if (!currentProject) return;

    try {
      const fileList = await api.listFiles(currentProject.path);
      setFiles(fileList);

      // Auto-expand planning and manuscript folders
      setExpandedFolders(new Set(['planning', 'manuscript', 'characters']));
    } catch (error) {
      console.error('Failed to load files:', error);
    }
  };

  const toggleFolder = (path: string) => {
    setExpandedFolders((prev) => {
      const next = new Set(prev);
      if (next.has(path)) {
        next.delete(path);
      } else {
        next.add(path);
      }
      return next;
    });
  };

  const handleFileClick = async (file: FileNode) => {
    if (file.isDirectory) {
      toggleFolder(file.name);
    } else {
      setSelectedFile(file);
    }
  };

  const renderFileTree = (nodes: FileNode[], depth = 0) => {
    return nodes.map((node) => {
      const isExpanded = expandedFolders.has(node.name);
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

  // Build file tree with children
  const buildTree = (fileList: FileNode[]): FileNode[] => {
    const root: FileNode[] = [];
    const dirs = fileList.filter((f) => f.isDirectory);
    const filesOnly = fileList.filter((f) => !f.isDirectory);

    dirs.forEach((dir) => {
      root.push({
        ...dir,
        children: [], // In a full implementation, you'd recursively load children
      });
    });

    filesOnly.forEach((file) => {
      root.push(file);
    });

    return root;
  };

  const tree = buildTree(files);

  return (
    <div className="flex h-full flex-col">
      {/* Search */}
      <div className="border-b border-border p-4">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Search files..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9"
          />
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
