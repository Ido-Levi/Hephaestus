import React, { useEffect, useState } from 'react';
import { GitBranch, Layers, Activity } from 'lucide-react';
import { apiService } from '@/services/api';

interface TaskTreeStatsProps {
  taskId: string;
  parentTaskId?: string | null;
  childTasksCount: number;
}

interface TreeStats {
  totalTasks: number;
  depth: number;
  breadth: number;
  completedTasks: number;
  failedTasks: number;
  inProgressTasks: number;
}

const TaskTreeStats: React.FC<TaskTreeStatsProps> = ({ taskId, parentTaskId, childTasksCount }) => {
  const [stats, setStats] = useState<TreeStats>({
    totalTasks: 1,
    depth: 1,
    breadth: childTasksCount,
    completedTasks: 0,
    failedTasks: 0,
    inProgressTasks: 0
  });
  const [isCalculating, setIsCalculating] = useState(false);

  useEffect(() => {
    const calculateTreeStats = async () => {
      setIsCalculating(true);

      try {
        // Calculate depth by traversing up to the root
        let depth = 1;
        let currentId = parentTaskId;
        const visitedUp = new Set<string>();

        while (currentId && !visitedUp.has(currentId)) {
          visitedUp.add(currentId);
          try {
            const taskDetails = await apiService.getTaskFullDetails(currentId);
            depth++;
            currentId = taskDetails.parent_task?.id || null;
          } catch {
            break;
          }
        }

        // Calculate total tasks in the tree by traversing down
        const countDescendants = async (taskId: string, visited: Set<string>): Promise<{ total: number, completed: number, failed: number, inProgress: number }> => {
          if (visited.has(taskId)) return { total: 0, completed: 0, failed: 0, inProgress: 0 };
          visited.add(taskId);

          try {
            const taskDetails = await apiService.getTaskFullDetails(taskId);
            let total = 1;
            let completed = taskDetails.status === 'done' ? 1 : 0;
            let failed = taskDetails.status === 'failed' ? 1 : 0;
            let inProgress = taskDetails.status === 'in_progress' ? 1 : 0;

            for (const child of taskDetails.child_tasks || []) {
              const childStats = await countDescendants(child.id, visited);
              total += childStats.total;
              completed += childStats.completed;
              failed += childStats.failed;
              inProgress += childStats.inProgress;
            }

            return { total, completed, failed, inProgress };
          } catch {
            return { total: 1, completed: 0, failed: 0, inProgress: 0 };
          }
        };

        const visited = new Set<string>();
        const treeStats = await countDescendants(taskId, visited);

        setStats({
          totalTasks: treeStats.total,
          depth,
          breadth: childTasksCount,
          completedTasks: treeStats.completed,
          failedTasks: treeStats.failed,
          inProgressTasks: treeStats.inProgress
        });
      } catch (error) {
        console.error('Failed to calculate tree stats:', error);
      } finally {
        setIsCalculating(false);
      }
    };

    calculateTreeStats();
  }, [taskId, parentTaskId, childTasksCount]);

  const completionRate = stats.totalTasks > 0
    ? Math.round((stats.completedTasks / stats.totalTasks) * 100)
    : 0;

  return (
    <div className="bg-gradient-to-r from-purple-50 to-pink-50 dark:from-purple-900/20 dark:to-pink-900/20 rounded-lg p-4 border border-purple-200 dark:border-purple-800">
      <h4 className="text-sm font-semibold text-purple-800 dark:text-purple-200 mb-3 flex items-center">
        <GitBranch className="w-4 h-4 mr-2" />
        Task Tree Statistics
      </h4>

      {isCalculating ? (
        <div className="flex items-center justify-center py-4">
          <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-purple-500"></div>
        </div>
      ) : (
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
          <div className="flex items-center space-x-2">
            <Layers className="w-4 h-4 text-purple-600" />
            <div>
              <p className="text-xs text-gray-600 dark:text-gray-400">Depth</p>
              <p className="text-sm font-bold text-purple-700 dark:text-purple-300">
                Level {stats.depth}
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            <Activity className="w-4 h-4 text-purple-600" />
            <div>
              <p className="text-xs text-gray-600 dark:text-gray-400">Total Tasks</p>
              <p className="text-sm font-bold text-purple-700 dark:text-purple-300">
                {stats.totalTasks}
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            <div className="w-4 h-4 rounded-full bg-green-500"></div>
            <div>
              <p className="text-xs text-gray-600 dark:text-gray-400">Completion</p>
              <p className="text-sm font-bold text-green-700 dark:text-green-300">
                {completionRate}%
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            <div className="w-4 h-4 rounded-full bg-green-500 animate-pulse"></div>
            <div>
              <p className="text-xs text-gray-600 dark:text-gray-400">Completed</p>
              <p className="text-sm font-bold text-gray-700 dark:text-gray-300">
                {stats.completedTasks}
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            <div className="w-4 h-4 rounded-full bg-yellow-500 animate-pulse"></div>
            <div>
              <p className="text-xs text-gray-600 dark:text-gray-400">In Progress</p>
              <p className="text-sm font-bold text-gray-700 dark:text-gray-300">
                {stats.inProgressTasks}
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            <div className="w-4 h-4 rounded-full bg-red-500"></div>
            <div>
              <p className="text-xs text-gray-600 dark:text-gray-400">Failed</p>
              <p className="text-sm font-bold text-gray-700 dark:text-gray-300">
                {stats.failedTasks}
              </p>
            </div>
          </div>
        </div>
      )}

      {!isCalculating && stats.totalTasks > 1 && (
        <div className="mt-3 pt-3 border-t border-purple-200 dark:border-purple-700">
          <div className="flex items-center justify-between text-xs">
            <span className="text-purple-600 dark:text-purple-400">
              {parentTaskId ? 'Part of larger hierarchy' : 'Root task'}
            </span>
            <span className="text-purple-600 dark:text-purple-400">
              {childTasksCount > 0 ? `${childTasksCount} direct children` : 'No children'}
            </span>
          </div>
        </div>
      )}
    </div>
  );
};

export default TaskTreeStats;