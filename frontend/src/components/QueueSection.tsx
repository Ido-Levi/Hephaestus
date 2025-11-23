import React, { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { motion, AnimatePresence } from 'framer-motion';
import {
  ChevronDown,
  ChevronUp,
  Zap,
  XCircle,
  Eye,
  Loader2,
  Trash2
} from 'lucide-react';
import { apiService } from '@/services/api';
import { Agent } from '@/types';
import { useWebSocket } from '@/context/WebSocketContext';
import { useWorkflow } from '@/context/WorkflowContext';
import StatusBadge from '@/components/StatusBadge';
import { formatDistanceToNow } from 'date-fns';

interface QueueSectionProps {
  onViewTaskDetails: (taskId: string) => void;
  onRefreshTasks: () => void;
}

const QueueSection: React.FC<QueueSectionProps> = ({
  onViewTaskDetails,
  onRefreshTasks
}) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const { subscribe } = useWebSocket();
  const { selectedExecutionId } = useWorkflow();

  // Fetch queue status
  const { data: queueStatus, refetch: refetchQueue } = useQuery({
    queryKey: ['queue-status', selectedExecutionId],
    queryFn: () => apiService.getQueueStatus(selectedExecutionId || undefined),
    refetchInterval: 3000,
    enabled: !!selectedExecutionId,
  });

  // Fetch active agents
  const { data: agents, refetch: refetchAgents } = useQuery({
    queryKey: ['agents-for-queue'],
    queryFn: apiService.getAgents,
    refetchInterval: 3000,
    select: (data) => data.filter((a: Agent) => a.status !== 'terminated'),
  });

  // Subscribe to WebSocket events
  useEffect(() => {
    const unsubscribeTaskCreated = subscribe('task_created', () => {
      refetchQueue();
      onRefreshTasks();
    });

    const unsubscribeTaskCompleted = subscribe('task_completed', () => {
      refetchQueue();
      refetchAgents();
      onRefreshTasks();
    });

    const unsubscribeAgentCreated = subscribe('agent_created', () => {
      refetchQueue();
      refetchAgents();
    });

    const unsubscribeAgentStatusChanged = subscribe('agent_status_changed', () => {
      refetchQueue();
      refetchAgents();
    });

    const unsubscribePriorityBumped = subscribe('task_priority_bumped', () => {
      refetchQueue();
      onRefreshTasks();
    });

    return () => {
      unsubscribeTaskCreated();
      unsubscribeTaskCompleted();
      unsubscribeAgentCreated();
      unsubscribeAgentStatusChanged();
      unsubscribePriorityBumped();
    };
  }, [subscribe, refetchQueue, refetchAgents, onRefreshTasks]);

  const activeAgents = agents || [];
  const hasQueue = (queueStatus?.queued_tasks_count || 0) > 0;
  const atCapacity = queueStatus?.at_capacity || false;

  // Only show if there's a queue OR at capacity
  if (!hasQueue && !atCapacity) {
    return null;
  }

  const handleBumpTask = async (taskId: string) => {
    const confirmed = window.confirm(
      'Start this task immediately? This will bypass the agent limit and create a new agent right away.'
    );
    if (!confirmed) return;

    try {
      await apiService.bumpTaskPriority(taskId);
      refetchQueue();
      onRefreshTasks();
    } catch (error) {
      console.error('Failed to bump task:', error);
      alert('Failed to bump task.');
    }
  };

  const handleCancelTask = async (taskId: string) => {
    const confirmed = window.confirm(
      'Cancel this task? It will be marked as failed and removed from the queue.'
    );
    if (!confirmed) return;

    try {
      await apiService.cancelQueuedTask(taskId);
      refetchQueue();
      onRefreshTasks();
    } catch (error) {
      console.error('Failed to cancel task:', error);
      alert('Failed to cancel task.');
    }
  };

  const handleKillAgent = async (agentId: string) => {
    const confirmed = window.confirm(
      'Terminate this agent? Task will be marked as failed.'
    );
    if (!confirmed) return;

    try {
      await apiService.terminateAgent(agentId);
      refetchQueue();
      refetchAgents();
      onRefreshTasks();
    } catch (error) {
      console.error('Failed to terminate agent:', error);
      alert('Failed to terminate agent.');
    }
  };

  const utilizationPercentage = queueStatus
    ? (queueStatus.active_agents / queueStatus.max_concurrent_agents) * 100
    : 0;

  const nextUpTask = queueStatus?.queued_tasks[0];

  return (
    <motion.div
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      className="mb-4"
    >
      <div className="bg-white dark:bg-gray-900 rounded-lg border border-gray-300 dark:border-gray-700 shadow-sm">
        {/* Collapsed Header */}
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="w-full px-4 py-3 flex items-center justify-between hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors rounded-lg"
        >
          <div className="flex items-center space-x-3 flex-1 min-w-0">
            <Loader2 className="w-4 h-4 text-blue-600 flex-shrink-0" />

            <div className="flex items-center space-x-2 flex-1 min-w-0">
              {/* Utilization bar */}
              <div className="flex items-center space-x-2">
                <div className="w-16 h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                  <div
                    className={`h-full transition-all ${
                      atCapacity ? 'bg-orange-500' : 'bg-blue-500'
                    }`}
                    style={{ width: `${utilizationPercentage}%` }}
                  />
                </div>
                <span className={`text-xs font-medium ${atCapacity ? 'text-orange-600' : 'text-blue-600'}`}>
                  {queueStatus?.active_agents}/{queueStatus?.max_concurrent_agents}
                </span>
              </div>

              {/* Next up preview */}
              {nextUpTask && (
                <>
                  <span className="text-gray-400">·</span>
                  <span className="text-sm text-gray-600 dark:text-gray-400 truncate">
                    Next: <span className="font-medium text-gray-900 dark:text-gray-200">{nextUpTask.description}</span>
                  </span>
                </>
              )}

              {/* Waiting count */}
              {hasQueue && (
                <>
                  <span className="text-gray-400">·</span>
                  <span className="text-xs font-medium text-orange-600">
                    {queueStatus?.queued_tasks_count} waiting
                  </span>
                </>
              )}
            </div>
          </div>

          {isExpanded ? (
            <ChevronUp className="w-4 h-4 text-gray-500 flex-shrink-0" />
          ) : (
            <ChevronDown className="w-4 h-4 text-gray-500 flex-shrink-0" />
          )}
        </button>

        {/* Expanded Content */}
        <AnimatePresence>
          {isExpanded && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              transition={{ duration: 0.2 }}
              className="overflow-hidden border-t border-gray-200 dark:border-gray-700"
            >
              <div className="px-4 py-3 space-y-3">
                {/* Running Agents */}
                {activeAgents.length > 0 && (
                  <div className="space-y-1.5">
                    <h4 className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Running ({activeAgents.length})
                    </h4>
                    <div className="space-y-1">
                      {activeAgents.map((agent) => (
                        <div
                          key={agent.id}
                          className="flex items-center justify-between py-1.5 px-2 rounded hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors group"
                        >
                          <div className="flex items-center space-x-2 flex-1 min-w-0">
                            <StatusBadge status={agent.status} size="sm" />
                            <span className="text-xs text-gray-500 font-mono">
                              {agent.id.substring(0, 6)}
                            </span>
                            {agent.current_task ? (
                              <>
                                <span className="text-sm text-gray-700 dark:text-gray-300 truncate">
                                  {agent.current_task.description}
                                </span>
                                <span className="text-xs text-gray-500 flex-shrink-0">
                                  {agent.current_task.runtime_seconds > 0
                                    ? `${Math.floor(agent.current_task.runtime_seconds / 60)}m`
                                    : '<1m'
                                  }
                                </span>
                              </>
                            ) : (
                              <span className="text-sm text-gray-400 italic">No task</span>
                            )}
                          </div>
                          <div className="flex items-center space-x-1 opacity-0 group-hover:opacity-100 transition-opacity">
                            {agent.current_task && (
                              <button
                                onClick={() => onViewTaskDetails(agent.current_task!.id)}
                                className="p-1 hover:bg-blue-100 dark:hover:bg-blue-900/30 rounded text-blue-600 dark:text-blue-400"
                                title="View task"
                              >
                                <Eye className="w-3.5 h-3.5" />
                              </button>
                            )}
                            <button
                              onClick={() => handleKillAgent(agent.id)}
                              className="p-1 hover:bg-red-100 dark:hover:bg-red-900/30 rounded text-red-600 dark:text-red-400"
                              title="Terminate"
                            >
                              <XCircle className="w-3.5 h-3.5" />
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Queued Tasks */}
                {hasQueue && (
                  <div className="space-y-1.5">
                    <h4 className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Queued ({queueStatus?.queued_tasks_count})
                    </h4>
                    <div className="max-h-[200px] overflow-y-auto space-y-1 pr-1">
                      {queueStatus!.queued_tasks.map((task, index) => (
                        <motion.div
                          key={task.task_id}
                          initial={{ opacity: 0, x: -10 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ delay: index * 0.03 }}
                          className={`flex items-center justify-between py-1.5 px-2 rounded transition-colors group ${
                            index === 0
                              ? 'bg-orange-50 dark:bg-orange-900/20 hover:bg-orange-100 dark:hover:bg-orange-900/30'
                              : 'hover:bg-gray-50 dark:hover:bg-gray-800'
                          }`}
                        >
                          <div className="flex items-center space-x-2 flex-1 min-w-0">
                            <div className={`w-5 h-5 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0 ${
                              index === 0
                                ? 'bg-orange-500 text-white'
                                : 'bg-gray-200 dark:bg-gray-700 text-gray-600 dark:text-gray-400'
                            }`}>
                              {task.priority_boosted ? <Zap className="w-3 h-3" /> : task.queue_position}
                            </div>
                            <span className="text-sm text-gray-700 dark:text-gray-300 truncate">
                              {task.description}
                            </span>
                            <span className={`text-xs px-1.5 py-0.5 rounded flex-shrink-0 ${
                              task.priority === 'high' ? 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400' :
                              task.priority === 'medium' ? 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400' :
                              'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400'
                            }`}>
                              {task.priority}
                            </span>
                            <span className="text-xs text-gray-500 flex-shrink-0">
                              {task.queued_at ? formatDistanceToNow(new Date(task.queued_at), { addSuffix: true }) : 'now'}
                            </span>
                          </div>
                          <div className="flex items-center space-x-1 opacity-0 group-hover:opacity-100 transition-opacity">
                            <button
                              onClick={() => onViewTaskDetails(task.task_id)}
                              className="p-1 hover:bg-blue-100 dark:hover:bg-blue-900/30 rounded text-blue-600 dark:text-blue-400"
                              title="View details"
                            >
                              <Eye className="w-3.5 h-3.5" />
                            </button>
                            <button
                              onClick={() => handleBumpTask(task.task_id)}
                              className="p-1 hover:bg-orange-100 dark:hover:bg-orange-900/30 rounded text-orange-600 dark:text-orange-400"
                              title="Start immediately (bypasses limit)"
                            >
                              <Zap className="w-3.5 h-3.5" />
                            </button>
                            <button
                              onClick={() => handleCancelTask(task.task_id)}
                              className="p-1 hover:bg-red-100 dark:hover:bg-red-900/30 rounded text-red-600 dark:text-red-400"
                              title="Cancel task"
                            >
                              <Trash2 className="w-3.5 h-3.5" />
                            </button>
                          </div>
                        </motion.div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </motion.div>
  );
};

export default QueueSection;
