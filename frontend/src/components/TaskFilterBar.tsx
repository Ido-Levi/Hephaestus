import React, { useState, useMemo, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Search,
  X,
  Filter,
  Calendar,
  User,
  Flag,
  Sparkles
} from 'lucide-react';
import { Task } from '@/types';

export interface TaskFilters {
  searchText: string;
  status: string;
  phase: string;
  priority: string;
  assignment: string;
  dateRange: string;
}

interface PhaseData {
  name: string;
  order: number;
  count: number;
}

interface TaskFilterBarProps {
  tasks: Task[];
  filters: TaskFilters;
  onFiltersChange: (filters: TaskFilters) => void;
  filteredCount: number;
}

const TaskFilterBar: React.FC<TaskFilterBarProps> = ({
  tasks,
  filters,
  onFiltersChange,
  filteredCount,
}) => {
  const [showAdvanced, setShowAdvanced] = useState(false);

  // Calculate filter counts
  const filterCounts = useMemo(() => {
    const counts = {
      status: {} as Record<string, number>,
      phase: {} as Record<string, number>,
      priority: {} as Record<string, number>,
      assignment: {} as Record<string, number>,
    };

    tasks.forEach(task => {
      // Status counts
      counts.status[task.status] = (counts.status[task.status] || 0) + 1;

      // Phase counts
      if (task.phase_name) {
        counts.phase[task.phase_name] = (counts.phase[task.phase_name] || 0) + 1;
      } else {
        counts.phase['no-phase'] = (counts.phase['no-phase'] || 0) + 1;
      }

      // Priority counts
      counts.priority[task.priority] = (counts.priority[task.priority] || 0) + 1;

      // Assignment counts
      if (task.assigned_agent_id) {
        counts.assignment['assigned'] = (counts.assignment['assigned'] || 0) + 1;
      } else {
        counts.assignment['unassigned'] = (counts.assignment['unassigned'] || 0) + 1;
      }
    });

    return counts;
  }, [tasks]);

  // Get sorted phases with order numbers
  const sortedPhases = useMemo(() => {
    const phasesMap = new Map<string, PhaseData>();

    tasks.forEach(task => {
      if (task.phase_name && !phasesMap.has(task.phase_name)) {
        phasesMap.set(task.phase_name, {
          name: task.phase_name,
          order: task.phase_order ?? 999,
          count: 0,
        });
      }
    });

    // Update counts
    tasks.forEach(task => {
      if (task.phase_name) {
        const phase = phasesMap.get(task.phase_name);
        if (phase) phase.count++;
      }
    });

    return Array.from(phasesMap.values()).sort((a, b) => a.order - b.order);
  }, [tasks]);

  // Count active filters
  const activeFiltersCount = useMemo(() => {
    let count = 0;
    if (filters.searchText) count++;
    if (filters.status !== 'all') count++;
    if (filters.phase !== 'all') count++;
    if (filters.priority !== 'all') count++;
    if (filters.assignment !== 'all') count++;
    if (filters.dateRange !== 'all') count++;
    return count;
  }, [filters]);

  // Active filters display
  const activeFiltersList = useMemo(() => {
    const list: Array<{ label: string; value: string; key: keyof TaskFilters }> = [];

    if (filters.searchText) {
      list.push({ label: 'Search', value: `"${filters.searchText}"`, key: 'searchText' });
    }
    if (filters.status !== 'all') {
      list.push({ label: 'Status', value: filters.status.replace('_', ' '), key: 'status' });
    }
    if (filters.phase !== 'all') {
      const phase = sortedPhases.find(p => p.name === filters.phase);
      const displayName = phase
        ? `Phase ${phase.order}: ${phase.name}`
        : filters.phase === 'no-phase' ? 'No Phase' : filters.phase;
      list.push({ label: 'Phase', value: displayName, key: 'phase' });
    }
    if (filters.priority !== 'all') {
      list.push({ label: 'Priority', value: filters.priority, key: 'priority' });
    }
    if (filters.assignment !== 'all') {
      list.push({ label: 'Assignment', value: filters.assignment, key: 'assignment' });
    }
    if (filters.dateRange !== 'all') {
      list.push({ label: 'Created', value: filters.dateRange, key: 'dateRange' });
    }

    return list;
  }, [filters, sortedPhases]);

  // Clear all filters
  const clearAllFilters = () => {
    onFiltersChange({
      searchText: '',
      status: 'all',
      phase: 'all',
      priority: 'all',
      assignment: 'all',
      dateRange: 'all',
    });
    setShowAdvanced(false);
  };

  // Remove individual filter
  const removeFilter = (key: keyof TaskFilters) => {
    const defaultValue = key === 'searchText' ? '' : 'all';
    onFiltersChange({
      ...filters,
      [key]: defaultValue,
    });
  };

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyPress = (e: KeyboardEvent) => {
      // Focus search bar on "/" or Ctrl+F
      if ((e.key === '/' || (e.ctrlKey && e.key === 'f')) && !e.metaKey) {
        e.preventDefault();
        document.getElementById('task-search-input')?.focus();
      }

      // Clear all filters on Alt+C
      if (e.altKey && e.key === 'c') {
        e.preventDefault();
        clearAllFilters();
      }

      // Toggle advanced on Alt+A
      if (e.altKey && e.key === 'a') {
        e.preventDefault();
        setShowAdvanced(prev => !prev);
      }

      // Quick status filters Alt+1-8
      if (e.altKey && e.key >= '1' && e.key <= '8') {
        e.preventDefault();
        const statuses = ['all', 'pending', 'queued', 'blocked', 'assigned', 'in_progress', 'done', 'failed'];
        const index = parseInt(e.key) - 1;
        if (statuses[index]) {
          onFiltersChange({ ...filters, status: statuses[index] });
        }
      }
    };

    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, [filters, onFiltersChange]);

  const statuses = [
    { value: 'all', label: 'All', emoji: '📋' },
    { value: 'pending', label: 'Pending', emoji: '⏳' },
    { value: 'queued', label: 'Queued', emoji: '📥' },
    { value: 'blocked', label: 'Blocked', emoji: '🔒' },
    { value: 'assigned', label: 'Assigned', emoji: '👤' },
    { value: 'in_progress', label: 'In Progress', emoji: '▶️' },
    { value: 'done', label: 'Done', emoji: '✅' },
    { value: 'failed', label: 'Failed', emoji: '❌' },
  ];

  const priorities = [
    { value: 'all', label: 'All' },
    { value: 'high', label: 'High' },
    { value: 'medium', label: 'Medium' },
    { value: 'low', label: 'Low' },
  ];

  const assignments = [
    { value: 'all', label: 'All' },
    { value: 'assigned', label: 'Assigned' },
    { value: 'unassigned', label: 'Unassigned' },
  ];

  const dateRanges = [
    { value: 'all', label: 'All Time' },
    { value: 'last-hour', label: 'Last Hour' },
    { value: 'today', label: 'Today' },
    { value: 'this-week', label: 'This Week' },
    { value: 'this-month', label: 'This Month' },
  ];

  return (
    <div className="bg-gradient-to-br from-white via-blue-50/30 to-purple-50/20 rounded-xl shadow-lg border border-gray-200/50 overflow-hidden">
      {/* Header with Search */}
      <div className="bg-white/80 backdrop-blur-sm border-b border-gray-200/50 p-5">
        <div className="relative">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
          <input
            id="task-search-input"
            type="text"
            placeholder="Search tasks, agents, or IDs... (Press / to focus)"
            value={filters.searchText}
            onChange={(e) => onFiltersChange({ ...filters, searchText: e.target.value })}
            className="w-full pl-12 pr-12 py-3.5 border-2 border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all text-sm placeholder:text-gray-400 bg-white"
          />
          {filters.searchText && (
            <button
              onClick={() => onFiltersChange({ ...filters, searchText: '' })}
              className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 transition-colors"
              title="Clear search"
            >
              <X className="w-5 h-5" />
            </button>
          )}
        </div>
      </div>

      {/* Filter Status Bar */}
      {(activeFiltersCount > 0 || filteredCount !== tasks.length) && (
        <div className="bg-blue-50/50 backdrop-blur-sm border-b border-blue-100 px-5 py-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Sparkles className="w-4 h-4 text-blue-600" />
              <span className="text-sm font-semibold text-blue-900">
                Showing {filteredCount} of {tasks.length} tasks
              </span>
              {activeFiltersCount > 0 && (
                <span className="px-2.5 py-0.5 bg-blue-500 text-white rounded-full text-xs font-bold">
                  {activeFiltersCount} filter{activeFiltersCount !== 1 ? 's' : ''}
                </span>
              )}
            </div>
            {activeFiltersCount > 0 && (
              <button
                onClick={clearAllFilters}
                className="text-sm font-medium text-blue-600 hover:text-blue-700 transition-colors"
              >
                Clear All
              </button>
            )}
          </div>

          {/* Active Filters Pills */}
          <AnimatePresence>
            {activeFiltersList.length > 0 && (
              <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: 'auto', opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                transition={{ duration: 0.2 }}
                className="flex flex-wrap gap-2 mt-3 overflow-hidden"
              >
                {activeFiltersList.map((filter) => (
                  <motion.div
                    key={filter.key}
                    initial={{ scale: 0.9, opacity: 0 }}
                    animate={{ scale: 1, opacity: 1 }}
                    exit={{ scale: 0.9, opacity: 0 }}
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-white border border-blue-200 rounded-full text-xs font-medium shadow-sm"
                  >
                    <span className="text-blue-600 font-bold">{filter.label}:</span>
                    <span className="text-gray-700">{filter.value}</span>
                    <button
                      onClick={() => removeFilter(filter.key)}
                      className="ml-0.5 hover:bg-blue-100 rounded-full p-0.5 transition-colors"
                      title="Remove filter"
                    >
                      <X className="w-3 h-3 text-blue-600" />
                    </button>
                  </motion.div>
                ))}
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      )}

      {/* Main Filters */}
      <div className="p-5 space-y-5">
        {/* Status Filter */}
        <div>
          <div className="flex items-center gap-2 mb-3">
            <Filter className="w-4 h-4 text-gray-600" />
            <h3 className="text-sm font-bold text-gray-900 uppercase tracking-wide">Status</h3>
          </div>
          <div className="flex flex-wrap gap-2">
            {statuses.map((status) => {
              const count = status.value === 'all' ? tasks.length : filterCounts.status[status.value] || 0;
              const isActive = filters.status === status.value;
              const isEmpty = count === 0 && status.value !== 'all';

              return (
                <button
                  key={status.value}
                  onClick={() => onFiltersChange({ ...filters, status: status.value })}
                  disabled={isEmpty}
                  className={`
                    px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200
                    ${isActive
                      ? 'bg-gradient-to-r from-blue-500 to-blue-600 text-white shadow-md scale-105 ring-2 ring-blue-300'
                      : isEmpty
                      ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                      : 'bg-white text-gray-700 hover:bg-gray-50 border border-gray-200 hover:border-blue-300 hover:shadow-sm'
                    }
                  `}
                >
                  <span className="mr-1.5">{status.emoji}</span>
                  {status.label}
                  <span className={`ml-2 ${isActive ? 'text-blue-100' : 'text-gray-500'} font-bold`}>
                    {count}
                  </span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Phase Filter */}
        <div>
          <div className="flex items-center gap-2 mb-3">
            <Sparkles className="w-4 h-4 text-gray-600" />
            <h3 className="text-sm font-bold text-gray-900 uppercase tracking-wide">Phase</h3>
          </div>
          <div className="flex flex-wrap gap-2">
            <button
              onClick={() => onFiltersChange({ ...filters, phase: 'all' })}
              className={`
                px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200
                ${filters.phase === 'all'
                  ? 'bg-gradient-to-r from-green-500 to-green-600 text-white shadow-md scale-105 ring-2 ring-green-300'
                  : 'bg-white text-gray-700 hover:bg-gray-50 border border-gray-200 hover:border-green-300 hover:shadow-sm'
                }
              `}
            >
              All Phases
              <span className={`ml-2 ${filters.phase === 'all' ? 'text-green-100' : 'text-gray-500'} font-bold`}>
                {tasks.length}
              </span>
            </button>
            <button
              onClick={() => onFiltersChange({ ...filters, phase: 'no-phase' })}
              className={`
                px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200
                ${filters.phase === 'no-phase'
                  ? 'bg-gradient-to-r from-green-500 to-green-600 text-white shadow-md scale-105 ring-2 ring-green-300'
                  : 'bg-white text-gray-700 hover:bg-gray-50 border border-gray-200 hover:border-green-300 hover:shadow-sm'
                }
              `}
            >
              No Phase
              <span className={`ml-2 ${filters.phase === 'no-phase' ? 'text-green-100' : 'text-gray-500'} font-bold`}>
                {filterCounts.phase['no-phase'] || 0}
              </span>
            </button>
            {sortedPhases.map((phase) => {
              const isActive = filters.phase === phase.name;
              return (
                <button
                  key={phase.name}
                  onClick={() => onFiltersChange({ ...filters, phase: phase.name })}
                  className={`
                    px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200
                    ${isActive
                      ? 'bg-gradient-to-r from-green-500 to-green-600 text-white shadow-md scale-105 ring-2 ring-green-300'
                      : 'bg-white text-gray-700 hover:bg-gray-50 border border-gray-200 hover:border-green-300 hover:shadow-sm'
                    }
                  `}
                >
                  Phase {phase.order}: {phase.name}
                  <span className={`ml-2 ${isActive ? 'text-green-100' : 'text-gray-500'} font-bold`}>
                    {phase.count}
                  </span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Advanced Filters Toggle */}
        <div className="pt-3 border-t border-gray-200">
          <button
            onClick={() => setShowAdvanced(!showAdvanced)}
            className="flex items-center gap-2 text-sm font-semibold text-gray-700 hover:text-gray-900 transition-colors group"
          >
            <Filter className={`w-4 h-4 transition-transform ${showAdvanced ? 'rotate-180' : ''}`} />
            <span>Advanced Filters</span>
            {(filters.priority !== 'all' || filters.assignment !== 'all' || filters.dateRange !== 'all') && (
              <span className="px-2 py-0.5 bg-purple-500 text-white rounded-full text-xs font-bold">
                Active
              </span>
            )}
          </button>
        </div>

        {/* Advanced Filters Content */}
        <AnimatePresence>
          {showAdvanced && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              transition={{ duration: 0.3 }}
              className="space-y-5 overflow-hidden"
            >
              {/* Priority */}
              <div>
                <div className="flex items-center gap-2 mb-3">
                  <Flag className="w-4 h-4 text-gray-600" />
                  <h3 className="text-sm font-bold text-gray-900 uppercase tracking-wide">Priority</h3>
                </div>
                <div className="flex flex-wrap gap-2">
                  {priorities.map((priority) => {
                    const count = priority.value === 'all' ? tasks.length : filterCounts.priority[priority.value] || 0;
                    const isActive = filters.priority === priority.value;
                    const isEmpty = count === 0 && priority.value !== 'all';

                    const colors = {
                      high: 'from-red-500 to-red-600 ring-red-300',
                      medium: 'from-yellow-500 to-yellow-600 ring-yellow-300',
                      low: 'from-gray-500 to-gray-600 ring-gray-300',
                      all: 'from-purple-500 to-purple-600 ring-purple-300',
                    };

                    return (
                      <button
                        key={priority.value}
                        onClick={() => onFiltersChange({ ...filters, priority: priority.value })}
                        disabled={isEmpty}
                        className={`
                          px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200
                          ${isActive
                            ? `bg-gradient-to-r ${colors[priority.value as keyof typeof colors]} text-white shadow-md scale-105 ring-2`
                            : isEmpty
                            ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                            : 'bg-white text-gray-700 hover:bg-gray-50 border border-gray-200 hover:border-purple-300 hover:shadow-sm'
                          }
                        `}
                      >
                        {priority.label}
                        <span className={`ml-2 ${isActive ? 'opacity-80' : 'text-gray-500'} font-bold`}>
                          {count}
                        </span>
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Assignment */}
              <div>
                <div className="flex items-center gap-2 mb-3">
                  <User className="w-4 h-4 text-gray-600" />
                  <h3 className="text-sm font-bold text-gray-900 uppercase tracking-wide">Assignment</h3>
                </div>
                <div className="flex flex-wrap gap-2">
                  {assignments.map((assignment) => {
                    const count = assignment.value === 'all' ? tasks.length : filterCounts.assignment[assignment.value] || 0;
                    const isActive = filters.assignment === assignment.value;
                    const isEmpty = count === 0 && assignment.value !== 'all';

                    return (
                      <button
                        key={assignment.value}
                        onClick={() => onFiltersChange({ ...filters, assignment: assignment.value })}
                        disabled={isEmpty}
                        className={`
                          px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200
                          ${isActive
                            ? 'bg-gradient-to-r from-purple-500 to-purple-600 text-white shadow-md scale-105 ring-2 ring-purple-300'
                            : isEmpty
                            ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                            : 'bg-white text-gray-700 hover:bg-gray-50 border border-gray-200 hover:border-purple-300 hover:shadow-sm'
                          }
                        `}
                      >
                        {assignment.label}
                        <span className={`ml-2 ${isActive ? 'text-purple-100' : 'text-gray-500'} font-bold`}>
                          {count}
                        </span>
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Date Range */}
              <div>
                <div className="flex items-center gap-2 mb-3">
                  <Calendar className="w-4 h-4 text-gray-600" />
                  <h3 className="text-sm font-bold text-gray-900 uppercase tracking-wide">Created</h3>
                </div>
                <div className="flex flex-wrap gap-2">
                  {dateRanges.map((range) => {
                    const isActive = filters.dateRange === range.value;
                    return (
                      <button
                        key={range.value}
                        onClick={() => onFiltersChange({ ...filters, dateRange: range.value })}
                        className={`
                          px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200
                          ${isActive
                            ? 'bg-gradient-to-r from-purple-500 to-purple-600 text-white shadow-md scale-105 ring-2 ring-purple-300'
                            : 'bg-white text-gray-700 hover:bg-gray-50 border border-gray-200 hover:border-purple-300 hover:shadow-sm'
                          }
                        `}
                      >
                        {range.label}
                      </button>
                    );
                  })}
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

    </div>
  );
};

export default TaskFilterBar;
