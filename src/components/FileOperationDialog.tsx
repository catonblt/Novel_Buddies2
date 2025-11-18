import { useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Badge } from '@/components/ui/badge';
import { FileText, FilePlus, FileEdit, Trash2, ChevronDown, ChevronRight } from 'lucide-react';
import { AGENTS } from '@/lib/agents';
import { AgentType } from '@/lib/types';

export interface FileOperation {
  type: 'create' | 'update' | 'delete';
  path: string;
  content?: string;
  reason: string;
  project_id: string;
  agent_type: string;
}

interface FileOperationDialogProps {
  operations: FileOperation[];
  isOpen: boolean;
  onConfirm: (operations: FileOperation[]) => void;
  onReject: () => void;
  agentType: AgentType;
}

export default function FileOperationDialog({
  operations,
  isOpen,
  onConfirm,
  onReject,
  agentType,
}: FileOperationDialogProps) {
  const [expandedOps, setExpandedOps] = useState<Set<number>>(new Set());

  const toggleExpand = (index: number) => {
    setExpandedOps((prev) => {
      const next = new Set(prev);
      if (next.has(index)) {
        next.delete(index);
      } else {
        next.add(index);
      }
      return next;
    });
  };

  const getOperationIcon = (type: string) => {
    switch (type) {
      case 'create':
        return <FilePlus className="h-4 w-4 text-green-500" />;
      case 'update':
        return <FileEdit className="h-4 w-4 text-blue-500" />;
      case 'delete':
        return <Trash2 className="h-4 w-4 text-red-500" />;
      default:
        return <FileText className="h-4 w-4" />;
    }
  };

  const getOperationBadge = (type: string) => {
    switch (type) {
      case 'create':
        return <Badge variant="outline" className="bg-green-500/10 text-green-500 border-green-500/20">Create</Badge>;
      case 'update':
        return <Badge variant="outline" className="bg-blue-500/10 text-blue-500 border-blue-500/20">Update</Badge>;
      case 'delete':
        return <Badge variant="outline" className="bg-red-500/10 text-red-500 border-red-500/20">Delete</Badge>;
      default:
        return <Badge variant="outline">{type}</Badge>;
    }
  };

  const agentInfo = AGENTS[agentType];

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && onReject()}>
      <DialogContent className="max-w-2xl max-h-[80vh] flex flex-col">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <span>{agentInfo?.icon}</span>
            {agentInfo?.name || 'Agent'} wants to modify files
          </DialogTitle>
          <DialogDescription>
            Review and approve the following {operations.length} file operation{operations.length !== 1 ? 's' : ''}
          </DialogDescription>
        </DialogHeader>

        <ScrollArea className="flex-1 pr-4 max-h-[50vh]">
          <div className="space-y-3">
            {operations.map((op, index) => (
              <div
                key={index}
                className="border rounded-lg overflow-hidden bg-card"
              >
                {/* Operation Header */}
                <div
                  className="flex items-center gap-3 p-3 cursor-pointer hover:bg-accent/50"
                  onClick={() => toggleExpand(index)}
                >
                  <button className="p-0.5">
                    {expandedOps.has(index) ? (
                      <ChevronDown className="h-4 w-4" />
                    ) : (
                      <ChevronRight className="h-4 w-4" />
                    )}
                  </button>
                  {getOperationIcon(op.type)}
                  <span className="font-mono text-sm flex-1 truncate">
                    {op.path}
                  </span>
                  {getOperationBadge(op.type)}
                </div>

                {/* Expanded Content */}
                {expandedOps.has(index) && (
                  <div className="border-t bg-muted/30 p-3 space-y-3">
                    <div>
                      <p className="text-xs font-medium text-muted-foreground mb-1">
                        Reason
                      </p>
                      <p className="text-sm">{op.reason}</p>
                    </div>

                    {op.content && op.type !== 'delete' && (
                      <div>
                        <p className="text-xs font-medium text-muted-foreground mb-1">
                          Content Preview ({op.content.length} characters)
                        </p>
                        <pre className="text-xs bg-background rounded p-2 overflow-x-auto max-h-40 overflow-y-auto font-mono">
                          {op.content.length > 1000
                            ? op.content.substring(0, 1000) + '\n\n... (truncated)'
                            : op.content}
                        </pre>
                      </div>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        </ScrollArea>

        <DialogFooter className="gap-2 sm:gap-0">
          <Button variant="outline" onClick={onReject}>
            Reject All
          </Button>
          <Button onClick={() => onConfirm(operations)}>
            Approve {operations.length} Operation{operations.length !== 1 ? 's' : ''}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
