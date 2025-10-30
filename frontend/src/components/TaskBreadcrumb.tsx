import React, { useEffect, useState } from 'react';
import { ChevronRight, Home } from 'lucide-react';
import { apiService } from '@/services/api';

interface BreadcrumbTask {
  id: string;
  description: string;
  status: string;
}

interface TaskBreadcrumbProps {
  currentTaskId: string;
  onNavigateToTask: (taskId: string) => void;
}

const TaskBreadcrumb: React.FC<TaskBreadcrumbProps> = ({ currentTaskId, onNavigateToTask }) => {
  const [taskHierarchy, setTaskHierarchy] = useState<BreadcrumbTask[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const buildHierarchy = async () => {
      setIsLoading(true);
      const hierarchy: BreadcrumbTask[] = [];
      let currentId = currentTaskId;
      const visited = new Set<string>();

      try {
        while (currentId && !visited.has(currentId)) {
          visited.add(currentId);
          const taskDetails = await apiService.getTaskFullDetails(currentId);

          hierarchy.unshift({
            id: taskDetails.id,
            description: taskDetails.user_prompt || taskDetails.raw_description,
            status: taskDetails.status
          });

          if (taskDetails.parent_task) {
            currentId = taskDetails.parent_task.id;
          } else {
            break;
          }
        }
        setTaskHierarchy(hierarchy);
      } catch (error) {
        console.error('Failed to build task hierarchy:', error);
      } finally {
        setIsLoading(false);
      }
    };

    if (currentTaskId) {
      buildHierarchy();
    }
  }, [currentTaskId]);

  if (isLoading || taskHierarchy.length <= 1) {
    return null;
  }

  return (
    <div className="flex items-center space-x-2 text-sm bg-gray-50 dark:bg-gray-800 px-4 py-2 rounded-lg overflow-x-auto">
      <Home className="w-4 h-4 text-gray-500 flex-shrink-0" />
      {taskHierarchy.map((task, index) => (
        <React.Fragment key={task.id}>
          {index > 0 && (
            <ChevronRight className="w-4 h-4 text-gray-400 flex-shrink-0" />
          )}
          <button
            onClick={() => index < taskHierarchy.length - 1 && onNavigateToTask(task.id)}
            className={`
              ${index === taskHierarchy.length - 1
                ? 'text-gray-900 dark:text-white font-medium cursor-default'
                : 'text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 hover:underline cursor-pointer'
              }
              truncate max-w-xs
            `}
            disabled={index === taskHierarchy.length - 1}
            title={task.description}
          >
            {task.description.length > 30
              ? task.description.substring(0, 30) + '...'
              : task.description
            }
          </button>
        </React.Fragment>
      ))}
      <span className="text-xs text-gray-500 ml-2 flex-shrink-0">
        ({taskHierarchy.length} levels)
      </span>
    </div>
  );
};

export default TaskBreadcrumb;