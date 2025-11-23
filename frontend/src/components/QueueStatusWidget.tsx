import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import { Users, Clock, Zap, AlertCircle, ChevronRight } from 'lucide-react';
import { apiService } from '@/services/api';
import { useWorkflow } from '@/context/WorkflowContext';
import { formatDistanceToNow } from 'date-fns';

const QueueStatusWidget: React.FC = () => {
  const { selectedExecutionId } = useWorkflow();

  const { data: queueStatus, isLoading } = useQuery({
    queryKey: ['queueStatus', selectedExecutionId],
    queryFn: () => apiService.getQueueStatus(selectedExecutionId || undefined),
    refetchInterval: 3000, // Poll every 3 seconds
    enabled: !!selectedExecutionId,
  });

  if (isLoading || !queueStatus) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 rounded w-1/3 mb-4"></div>
          <div className="h-20 bg-gray-200 rounded"></div>
        </div>
      </div>
    );
  }

  const utilizationPercentage =
    (queueStatus.active_agents / queueStatus.max_concurrent_agents) * 100;

  const getUtilizationColor = (percentage: number) => {
    if (percentage >= 100) return 'bg-red-500';
    if (percentage >= 75) return 'bg-yellow-500';
    return 'bg-green-500';
  };

  const getUtilizationTextColor = (percentage: number) => {
    if (percentage >= 100) return 'text-red-700';
    if (percentage >= 75) return 'text-yellow-700';
    return 'text-green-700';
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-white rounded-lg shadow-md overflow-hidden"
    >
      {/* Header */}
      <div className="bg-gradient-to-r from-indigo-500 to-purple-600 p-4">
        <div className="flex items-center justify-between text-white">
          <div className="flex items-center space-x-2">
            <Users className="w-5 h-5" />
            <h3 className="font-semibold text-lg">Agent Queue</h3>
          </div>
          {queueStatus.at_capacity && (
            <motion.div
              initial={{ scale: 0.8 }}
              animate={{ scale: 1 }}
              transition={{ repeat: Infinity, duration: 1.5, repeatType: 'reverse' }}
              className="flex items-center space-x-1 bg-white/20 rounded-full px-3 py-1"
            >
              <AlertCircle className="w-4 h-4" />
              <span className="text-sm font-medium">At Capacity</span>
            </motion.div>
          )}
        </div>
      </div>

      {/* Stats Section */}
      <div className="p-6 space-y-4">
        {/* Utilization Bar */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-700">
              Active Agents
            </span>
            <span className={`text-sm font-bold ${getUtilizationTextColor(utilizationPercentage)}`}>
              {queueStatus.active_agents} / {queueStatus.max_concurrent_agents}
            </span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${utilizationPercentage}%` }}
              transition={{ duration: 0.5 }}
              className={`h-3 rounded-full ${getUtilizationColor(utilizationPercentage)} transition-all`}
            />
          </div>
          <div className="flex items-center justify-between mt-1 text-xs text-gray-500">
            <span>{utilizationPercentage.toFixed(0)}% utilized</span>
            <span>{queueStatus.slots_available} slots available</span>
          </div>
        </div>

        {/* Queued Tasks Summary */}
        <div className="grid grid-cols-2 gap-4">
          <div className="bg-blue-50 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-blue-600 font-medium">Queued Tasks</p>
                <p className="text-2xl font-bold text-blue-900">
                  {queueStatus.queued_tasks_count}
                </p>
              </div>
              <Clock className="w-8 h-8 text-blue-400" />
            </div>
          </div>
          <div className="bg-purple-50 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-purple-600 font-medium">Priority Boosted</p>
                <p className="text-2xl font-bold text-purple-900">
                  {queueStatus.queued_tasks.filter((t) => t.priority_boosted).length}
                </p>
              </div>
              <Zap className="w-8 h-8 text-purple-400" />
            </div>
          </div>
        </div>

        {/* Queued Tasks List */}
        {queueStatus.queued_tasks.length > 0 && (
          <div className="mt-4">
            <h4 className="text-sm font-semibold text-gray-700 mb-3 flex items-center">
              <ChevronRight className="w-4 h-4 mr-1" />
              Queue (Next {Math.min(5, queueStatus.queued_tasks.length)})
            </h4>
            <div className="space-y-2 max-h-64 overflow-y-auto">
              {queueStatus.queued_tasks.slice(0, 5).map((task, index) => (
                <motion.div
                  key={task.task_id}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.05 }}
                  className={`p-3 rounded-lg border ${
                    task.priority_boosted
                      ? 'bg-purple-50 border-purple-300'
                      : task.priority === 'high'
                      ? 'bg-red-50 border-red-200'
                      : task.priority === 'medium'
                      ? 'bg-yellow-50 border-yellow-200'
                      : 'bg-gray-50 border-gray-200'
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-2 mb-1">
                        <span
                          className={`px-2 py-0.5 rounded text-xs font-medium ${
                            task.priority_boosted
                              ? 'bg-purple-200 text-purple-800'
                              : task.priority === 'high'
                              ? 'bg-red-200 text-red-800'
                              : task.priority === 'medium'
                              ? 'bg-yellow-200 text-yellow-800'
                              : 'bg-gray-200 text-gray-800'
                          }`}
                        >
                          {task.priority_boosted ? (
                            <span className="flex items-center">
                              <Zap className="w-3 h-3 mr-1" />
                              Boosted
                            </span>
                          ) : (
                            task.priority
                          )}
                        </span>
                        <span className="text-xs text-gray-500">
                          Position: {task.queue_position}
                        </span>
                      </div>
                      <p className="text-sm text-gray-700 line-clamp-2">
                        {task.description}
                      </p>
                      {task.queued_at && (
                        <p className="text-xs text-gray-500 mt-1">
                          Queued {formatDistanceToNow(new Date(task.queued_at), { addSuffix: true })}
                        </p>
                      )}
                    </div>
                  </div>
                </motion.div>
              ))}
            </div>
            {queueStatus.queued_tasks.length > 5 && (
              <p className="text-xs text-gray-500 mt-2 text-center">
                + {queueStatus.queued_tasks.length - 5} more tasks in queue
              </p>
            )}
          </div>
        )}

        {/* Empty State */}
        {queueStatus.queued_tasks.length === 0 && (
          <div className="text-center py-6">
            <Clock className="w-12 h-12 text-gray-300 mx-auto mb-2" />
            <p className="text-sm text-gray-500">No tasks in queue</p>
          </div>
        )}
      </div>
    </motion.div>
  );
};

export default QueueStatusWidget;
