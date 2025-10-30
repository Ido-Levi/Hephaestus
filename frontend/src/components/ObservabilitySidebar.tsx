import React, { useMemo } from 'react';
import { motion } from 'framer-motion';
import {
  Eye,
  EyeOff,
  Bot,
  Activity,
  AlertCircle,
  CheckSquare,
  Square,
  ChevronDown,
  ChevronRight,
  Clock
} from 'lucide-react';
import { Agent } from '@/types';
import { formatDistanceToNow } from 'date-fns';
import ClickableTaskCard from '@/components/ClickableTaskCard';
import TaskDetailModal from '@/components/TaskDetailModal';

interface ObservabilitySidebarProps {
  agents: Agent[];
  visibleAgents: Set<string>;
  onToggleAgent: (agentId: string) => void;
  onSelectAll: () => void;
  onDeselectAll: () => void;
  onTaskClick?: (taskId: string) => void;
}

const ObservabilitySidebar: React.FC<ObservabilitySidebarProps> = ({
  agents,
  visibleAgents,
  onToggleAgent,
  onSelectAll,
  onDeselectAll,
}) => {
  const [selectedTaskId, setSelectedTaskId] = React.useState<string | null>(null);

  // Group agents by status
  const agentsByStatus = useMemo(() => {
    const groups = {
      working: [] as Agent[],
      idle: [] as Agent[],
      stuck: [] as Agent[],
      terminated: [] as Agent[],
    };

    agents.forEach(agent => {
      const status = agent.status as keyof typeof groups;
      if (groups[status]) {
        groups[status].push(agent);
      }
    });

    return groups;
  }, [agents]);

  // Status colors and icons
  const getStatusConfig = (status: string) => {
    switch (status) {
      case 'working':
        return {
          color: 'text-green-600 bg-green-50',
          icon: <Activity className="w-3 h-3" />,
          label: 'Working',
        };
      case 'idle':
        return {
          color: 'text-gray-600 bg-gray-50',
          icon: <Clock className="w-3 h-3" />,
          label: 'Idle',
        };
      case 'stuck':
        return {
          color: 'text-red-600 bg-red-50',
          icon: <AlertCircle className="w-3 h-3" />,
          label: 'Stuck',
        };
      case 'terminated':
        return {
          color: 'text-gray-500 bg-gray-100',
          icon: <Bot className="w-3 h-3" />,
          label: 'Terminated',
        };
      default:
        return {
          color: 'text-gray-600 bg-gray-50',
          icon: <Bot className="w-3 h-3" />,
          label: status,
        };
    }
  };

  const [expandedGroups, setExpandedGroups] = React.useState<Set<string>>(
    new Set(['working', 'stuck'])
  );

  const toggleGroup = (group: string) => {
    setExpandedGroups(prev => {
      const newSet = new Set(prev);
      if (newSet.has(group)) {
        newSet.delete(group);
      } else {
        newSet.add(group);
      }
      return newSet;
    });
  };

  const AgentItem: React.FC<{ agent: Agent }> = ({ agent }) => {
    const isVisible = visibleAgents.has(agent.id);
    const statusConfig = getStatusConfig(agent.status);

    return (
      <motion.div
        initial={{ opacity: 0, x: -20 }}
        animate={{ opacity: 1, x: 0 }}
        className={`px-3 py-2 hover:bg-gray-50 cursor-pointer transition-colors ${
          isVisible ? 'bg-blue-50 hover:bg-blue-100' : ''
        }`}
        onClick={() => onToggleAgent(agent.id)}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2 flex-1 min-w-0">
            <button
              className="flex-shrink-0"
              onClick={(e) => {
                e.stopPropagation();
                onToggleAgent(agent.id);
              }}
            >
              {isVisible ? (
                <CheckSquare className="w-4 h-4 text-blue-600" />
              ) : (
                <Square className="w-4 h-4 text-gray-400" />
              )}
            </button>

            <Bot className="w-4 h-4 text-gray-500 flex-shrink-0" />

            <div className="flex-1 min-w-0">
              <div className="flex items-center space-x-2">
                <span className="text-sm font-medium text-gray-800 truncate">
                  {agent.id.substring(0, 8)}
                </span>
                <span className={`px-1.5 py-0.5 rounded text-xs font-medium flex-shrink-0 ${statusConfig.color}`}>
                  {agent.status}
                </span>
              </div>

              {agent.current_task_id && (
                <div className="mt-1 -mx-1">
                  <ClickableTaskCard
                    taskId={agent.current_task_id}
                    onClick={(e: any) => {
                      e.stopPropagation();
                      setSelectedTaskId(agent.current_task_id);
                    }}
                    compact
                    showPhaseInfo={false}
                    className="text-xs"
                  />
                </div>
              )}

              {agent.last_activity && (
                <div className="flex items-center mt-0.5 text-xs text-gray-400">
                  <Clock className="w-3 h-3 mr-1 flex-shrink-0" />
                  <span>{formatDistanceToNow(new Date(agent.last_activity), { addSuffix: true })}</span>
                </div>
              )}
            </div>
          </div>

          <div className="flex-shrink-0 ml-2">
            {isVisible ? (
              <Eye className="w-4 h-4 text-blue-600" />
            ) : (
              <EyeOff className="w-4 h-4 text-gray-400" />
            )}
          </div>
        </div>
      </motion.div>
    );
  };

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="px-4 py-3 border-b bg-gray-50">
        <div className="flex items-center justify-between mb-2">
          <h3 className="text-sm font-semibold text-gray-800">Agent List</h3>
          <span className="text-xs text-gray-500">
            {visibleAgents.size} / {agents.length} selected
          </span>
        </div>

        {/* Quick Actions */}
        <div className="flex items-center space-x-2">
          <button
            onClick={onSelectAll}
            className="flex-1 px-2 py-1 text-xs bg-blue-100 text-blue-700 rounded hover:bg-blue-200 transition-colors"
          >
            Select All
          </button>
          <button
            onClick={onDeselectAll}
            className="flex-1 px-2 py-1 text-xs bg-gray-100 text-gray-700 rounded hover:bg-gray-200 transition-colors"
          >
            Deselect All
          </button>
        </div>
      </div>

      {/* Agent Groups */}
      <div className="flex-1 overflow-y-auto">
        {Object.entries(agentsByStatus).map(([status, statusAgents]) => {
          if (statusAgents.length === 0) return null;

          const statusConfig = getStatusConfig(status);
          const isExpanded = expandedGroups.has(status);

          return (
            <div key={status} className="border-b">
              {/* Group Header */}
              <div
                className="px-3 py-2 bg-gray-50 hover:bg-gray-100 cursor-pointer transition-colors flex items-center justify-between"
                onClick={() => toggleGroup(status)}
              >
                <div className="flex items-center space-x-2">
                  {isExpanded ? (
                    <ChevronDown className="w-3 h-3 text-gray-500" />
                  ) : (
                    <ChevronRight className="w-3 h-3 text-gray-500" />
                  )}
                  {statusConfig.icon}
                  <span className="text-sm font-medium text-gray-700">
                    {statusConfig.label}
                  </span>
                  <span className="text-xs text-gray-500">
                    ({statusAgents.length})
                  </span>
                </div>

                <div className="text-xs text-gray-500">
                  {statusAgents.filter(a => visibleAgents.has(a.id)).length} visible
                </div>
              </div>

              {/* Group Items */}
              {isExpanded && (
                <div>
                  {statusAgents.map(agent => (
                    <AgentItem key={agent.id} agent={agent} />
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Footer */}
      <div className="px-4 py-3 border-t bg-gray-50 text-xs text-gray-600">
        <div className="space-y-1">
          <div className="flex justify-between">
            <span>Working:</span>
            <span className="font-medium">{agentsByStatus.working.length}</span>
          </div>
          <div className="flex justify-between">
            <span>Idle:</span>
            <span className="font-medium">{agentsByStatus.idle.length}</span>
          </div>
          <div className="flex justify-between">
            <span>Stuck:</span>
            <span className="font-medium text-red-600">{agentsByStatus.stuck.length}</span>
          </div>
        </div>
      </div>

      {/* Task Detail Modal */}
      <TaskDetailModal
        taskId={selectedTaskId}
        onClose={() => setSelectedTaskId(null)}
        onNavigateToTask={(taskId) => setSelectedTaskId(taskId)}
      />
    </div>
  );
};

export default ObservabilitySidebar;