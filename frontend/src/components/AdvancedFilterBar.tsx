import React, { useState, useCallback } from 'react';
import { Filter, X, Clock, Activity, AlertCircle, CheckCircle } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

export interface FilterOptions {
  status: string[];
  activityThreshold: number | null; // minutes
  searchPattern: string;
  hideIdle: boolean;
}

interface AdvancedFilterBarProps {
  onFilterChange: (filters: FilterOptions) => void;
  agentCount: { total: number; filtered: number };
}

const AdvancedFilterBar: React.FC<AdvancedFilterBarProps> = ({
  onFilterChange,
  agentCount,
}) => {
  const [filters, setFilters] = useState<FilterOptions>({
    status: [],
    activityThreshold: null,
    searchPattern: '',
    hideIdle: false,
  });
  const [showAdvanced, setShowAdvanced] = useState(false);

  const statusOptions = [
    { value: 'working', label: 'Working', icon: Activity, color: 'text-green-600' },
    { value: 'idle', label: 'Idle', icon: Clock, color: 'text-gray-600' },
    { value: 'stuck', label: 'Stuck', icon: AlertCircle, color: 'text-red-600' },
    { value: 'terminated', label: 'Terminated', icon: CheckCircle, color: 'text-gray-500' },
  ];

  const activityOptions = [
    { value: 1, label: 'Last 1 minute' },
    { value: 5, label: 'Last 5 minutes' },
    { value: 15, label: 'Last 15 minutes' },
    { value: 30, label: 'Last 30 minutes' },
    { value: 60, label: 'Last hour' },
  ];

  const handleStatusToggle = useCallback((status: string) => {
    const newFilters = { ...filters };
    if (newFilters.status.includes(status)) {
      newFilters.status = newFilters.status.filter(s => s !== status);
    } else {
      newFilters.status = [...newFilters.status, status];
    }
    setFilters(newFilters);
    onFilterChange(newFilters);
  }, [filters, onFilterChange]);

  const handleActivityChange = useCallback((minutes: number | null) => {
    const newFilters = { ...filters, activityThreshold: minutes };
    setFilters(newFilters);
    onFilterChange(newFilters);
  }, [filters, onFilterChange]);

  const handlePatternChange = useCallback((pattern: string) => {
    const newFilters = { ...filters, searchPattern: pattern };
    setFilters(newFilters);
    onFilterChange(newFilters);
  }, [filters, onFilterChange]);

  const handleHideIdleToggle = useCallback(() => {
    const newFilters = { ...filters, hideIdle: !filters.hideIdle };
    setFilters(newFilters);
    onFilterChange(newFilters);
  }, [filters, onFilterChange]);

  const clearFilters = useCallback(() => {
    const newFilters: FilterOptions = {
      status: [],
      activityThreshold: null,
      searchPattern: '',
      hideIdle: false,
    };
    setFilters(newFilters);
    onFilterChange(newFilters);
  }, [onFilterChange]);

  const hasActiveFilters = filters.status.length > 0 ||
    filters.activityThreshold !== null ||
    filters.searchPattern !== '' ||
    filters.hideIdle;

  return (
    <div className="bg-white border-b">
      {/* Main Filter Bar */}
      <div className="px-4 py-2 flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            <Filter className="w-4 h-4 text-gray-600" />
            <span className="text-sm font-medium text-gray-700">Filters:</span>
          </div>

          {/* Status Filters */}
          <div className="flex items-center space-x-2">
            {statusOptions.map(option => {
              const Icon = option.icon;
              const isActive = filters.status.includes(option.value);
              return (
                <button
                  key={option.value}
                  onClick={() => handleStatusToggle(option.value)}
                  className={`px-3 py-1 text-xs rounded-full transition-all flex items-center space-x-1 ${
                    isActive
                      ? 'bg-blue-100 text-blue-700 ring-2 ring-blue-300'
                      : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                  }`}
                >
                  <Icon className="w-3 h-3" />
                  <span>{option.label}</span>
                </button>
              );
            })}
          </div>

          {/* Activity Filter */}
          <div className="flex items-center space-x-2">
            <select
              value={filters.activityThreshold || ''}
              onChange={(e) => handleActivityChange(e.target.value ? parseInt(e.target.value) : null)}
              className="text-xs border border-gray-300 rounded px-2 py-1 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="">All activity</option>
              {activityOptions.map(option => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>

          {/* Hide Idle Toggle */}
          <div className="flex items-center">
            <label className="flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={filters.hideIdle}
                onChange={handleHideIdleToggle}
                className="mr-2"
              />
              <span className="text-xs text-gray-600">Hide idle agents</span>
            </label>
          </div>
        </div>

        <div className="flex items-center space-x-3">
          {/* Agent Count */}
          <div className="text-xs text-gray-600">
            Showing <span className="font-medium">{agentCount.filtered}</span> of{' '}
            <span className="font-medium">{agentCount.total}</span> agents
          </div>

          {/* Clear Filters */}
          {hasActiveFilters && (
            <button
              onClick={clearFilters}
              className="px-3 py-1 text-xs bg-red-100 text-red-700 hover:bg-red-200 rounded transition-colors flex items-center"
            >
              <X className="w-3 h-3 mr-1" />
              Clear Filters
            </button>
          )}

          {/* Advanced Toggle */}
          <button
            onClick={() => setShowAdvanced(!showAdvanced)}
            className="px-3 py-1 text-xs bg-gray-100 text-gray-700 hover:bg-gray-200 rounded transition-colors"
          >
            {showAdvanced ? 'Hide' : 'Show'} Advanced
          </button>
        </div>
      </div>

      {/* Advanced Filter Panel */}
      <AnimatePresence>
        {showAdvanced && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="border-t bg-gray-50 px-4 py-3 overflow-hidden"
          >
            <div className="flex items-center space-x-4">
              {/* Regex Pattern Filter */}
              <div className="flex-1">
                <label className="block text-xs font-medium text-gray-700 mb-1">
                  Output Pattern (Regex)
                </label>
                <input
                  type="text"
                  value={filters.searchPattern}
                  onChange={(e) => handlePatternChange(e.target.value)}
                  placeholder="e.g., ERROR.*failed|WARN.*timeout"
                  className="w-full px-3 py-1.5 text-sm border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>

              {/* Quick Patterns */}
              <div className="flex items-center space-x-2">
                <span className="text-xs text-gray-600">Quick:</span>
                <button
                  onClick={() => handlePatternChange('ERROR')}
                  className="px-2 py-1 text-xs bg-red-100 text-red-700 hover:bg-red-200 rounded transition-colors"
                >
                  Errors
                </button>
                <button
                  onClick={() => handlePatternChange('WARN|WARNING')}
                  className="px-2 py-1 text-xs bg-yellow-100 text-yellow-700 hover:bg-yellow-200 rounded transition-colors"
                >
                  Warnings
                </button>
                <button
                  onClick={() => handlePatternChange('SUCCESS|COMPLETE')}
                  className="px-2 py-1 text-xs bg-green-100 text-green-700 hover:bg-green-200 rounded transition-colors"
                >
                  Success
                </button>
              </div>
            </div>

            {/* Filter Summary */}
            {hasActiveFilters && (
              <div className="mt-3 flex items-center space-x-2 text-xs text-gray-600">
                <span>Active filters:</span>
                {filters.status.length > 0 && (
                  <span className="px-2 py-0.5 bg-blue-100 text-blue-700 rounded">
                    Status: {filters.status.join(', ')}
                  </span>
                )}
                {filters.activityThreshold && (
                  <span className="px-2 py-0.5 bg-green-100 text-green-700 rounded">
                    Active in last {filters.activityThreshold}m
                  </span>
                )}
                {filters.searchPattern && (
                  <span className="px-2 py-0.5 bg-purple-100 text-purple-700 rounded">
                    Pattern: {filters.searchPattern}
                  </span>
                )}
                {filters.hideIdle && (
                  <span className="px-2 py-0.5 bg-gray-100 text-gray-700 rounded">
                    Hiding idle
                  </span>
                )}
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default AdvancedFilterBar;