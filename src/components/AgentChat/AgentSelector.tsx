import { AgentType } from '@/lib/types';
import { AGENTS } from '@/lib/agents';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

interface AgentSelectorProps {
  selected: AgentType;
  onSelect: (agent: AgentType) => void;
}

export default function AgentSelector({ selected, onSelect }: AgentSelectorProps) {
  const agentTypes = Object.keys(AGENTS) as AgentType[];

  return (
    <div className="flex flex-wrap gap-2">
      {agentTypes.map((type) => {
        const agent = AGENTS[type];
        const isSelected = selected === type;

        return (
          <Button
            key={type}
            variant={isSelected ? 'default' : 'outline'}
            size="sm"
            onClick={() => onSelect(type)}
            className={cn(
              'gap-2',
              isSelected && 'border-2'
            )}
            style={
              isSelected
                ? {
                    backgroundColor: agent.color + '20',
                    borderColor: agent.color,
                    color: agent.color,
                  }
                : undefined
            }
          >
            <span>{agent.icon}</span>
            <span className="text-xs font-medium">{agent.name}</span>
          </Button>
        );
      })}
    </div>
  );
}
