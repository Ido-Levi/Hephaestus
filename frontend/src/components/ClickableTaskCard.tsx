import React, { useState, useEffect } from 'react';
import { FileText, ExternalLink, Clock, User } from 'lucide-react';
import { apiService } from '@/services/api';
import { TaskFullDetails } from '@/types';
import StatusBadge from './StatusBadge';
import { PhaseBadge } from './PhaseBadge';

interface ClickableTaskCardProps {
  taskId: string;
  onClick: (e?: React.MouseEvent) => void;
  compact?: boolean;
  className?: string;
  showPhaseInfo?: boolean;
}

const ClickableTaskCard: React.FC<ClickableTaskCardProps> = ({
  taskId,
  onClick,
  compact = false,
  className = '',
  showPhaseInfo = true,
}) => {
  const [task, setTask] = useState<TaskFullDetails | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let mounted = true;

    const fetchTask = async () => {
      try {
        const taskDetails = await apiService.getTaskFullDetails(taskId);
        if (mounted) {
          setTask(taskDetails);
          setLoading(false);
        }
      } catch (error) {
        if (mounted) {
          setLoading(false);
        }
      }
    };

    fetchTask();

    return () => {
      mounted = false;
    };
  }, [taskId]);

  if (loading) {
    return (
      <div className={`animate-pulse bg-gray-100 rounded-lg p-3 ${className}`}>
        <div className="h-4 bg-gray-200 rounded w-32 mb-2"></div>
        <div className="h-3 bg-gray-200 rounded w-40"></div>
      </div>
    );
  }

  if (!task) {
    return (
      <div className={`text-gray-500 text-sm font-mono ${className}`}>
        {taskId.substring(0, 8)}
      </div>
    );
  }

  if (compact) {
    return (
      <button
        onClick={onClick}
        className={`text-left hover:bg-green-50 rounded-lg p-2 transition-all group flex items-start gap-2 w-full ${className}`}
      >
        <FileText className="w-4 h-4 text-green-600 flex-shrink-0 mt-0.5" />
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-0.5">
            <p className="font-mono text-xs text-gray-500">{taskId.substring(0, 8)}</p>
            <StatusBadge status={task.status} />
          </div>
          <p className="text-sm text-gray-800 group-hover:text-green-600 transition-colors truncate">
            {task.enriched_description || task.raw_description}
          </p>
          {showPhaseInfo && task.phase_info && (
            <p className="text-xs text-gray-500 mt-0.5">
              Phase {task.phase_info.order}: {task.phase_info.name}
            </p>
          )}
        </div>
        <ExternalLink className="w-3 h-3 text-gray-400 group-hover:text-green-600 opacity-0 group-hover:opacity-100 transition-all flex-shrink-0 mt-1" />
      </button>
    );
  }

  return (
    <button
      onClick={onClick}
      className={`text-left w-full hover:bg-green-50 rounded-xl p-4 transition-all duration-200 border border-gray-200 hover:border-green-300 hover:shadow-md group ${className}`}
    >
      <div className="flex items-start gap-3">
        <div className="bg-green-100 p-2 rounded-lg group-hover:bg-green-200 transition-colors">
          <FileText className="w-5 h-5 text-green-600" />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-2 flex-wrap">
            <p className="font-mono text-xs text-gray-500">{taskId.substring(0, 12)}</p>
            <StatusBadge status={task.status} />
            <span className={`px-2 py-0.5 rounded-full text-xs font-semibold ${
              task.priority === 'high'
                ? 'bg-red-100 text-red-700'
                : task.priority === 'medium'
                ? 'bg-yellow-100 text-yellow-700'
                : 'bg-gray-100 text-gray-700'
            }`}>
              {task.priority}
            </span>
          </div>

          <p className="text-sm font-medium text-gray-800 group-hover:text-green-600 transition-colors line-clamp-2 mb-2">
            {task.enriched_description || task.raw_description}
          </p>

          {showPhaseInfo && task.phase_info && (
            <div className="mb-2">
              <PhaseBadge
                phaseOrder={task.phase_info.order}
                phaseName={task.phase_info.name}
                totalPhases={5}
              />
            </div>
          )}

          <div className="flex items-center gap-3 text-xs text-gray-500 flex-wrap">
            {task.created_at && (
              <span className="flex items-center gap-1">
                <Clock className="w-3 h-3" />
                {new Date(task.created_at).toLocaleString()}
              </span>
            )}
            {task.agent_info && (
              <span className="flex items-center gap-1">
                <User className="w-3 h-3" />
                Agent {task.agent_info.id.substring(0, 8)}
              </span>
            )}
            {task.runtime_seconds > 0 && (
              <span className="font-semibold">
                {Math.floor(task.runtime_seconds / 60)}m runtime
              </span>
            )}
          </div>
        </div>
        <ExternalLink className="w-4 h-4 text-gray-400 group-hover:text-green-600 opacity-0 group-hover:opacity-100 transition-all flex-shrink-0 mt-1" />
      </div>
    </button>
  );
};

export default ClickableTaskCard;
