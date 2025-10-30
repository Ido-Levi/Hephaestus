import React from 'react';
import {
  Grid3x3,
  Grid2x2,
  Square,
  Search,
  Pause,
  Play,
  ChevronLeft,
  ChevronRight,
  Settings,
  Rows,
  LayoutGrid
} from 'lucide-react';
import type { LayoutPreset } from '@/pages/Observability';

interface ObservabilityControlsProps {
  selectedLayout: LayoutPreset;
  onLayoutChange: (layout: LayoutPreset) => void;
  searchTerm: string;
  onSearchChange: (term: string) => void;
  globalPaused: boolean;
  onTogglePause: () => void;
  onToggleSidebar: () => void;
  sidebarOpen?: boolean;
  agentCount: number;
  totalAgents: number;
}

const ObservabilityControls: React.FC<ObservabilityControlsProps> = ({
  selectedLayout,
  onLayoutChange,
  searchTerm,
  onSearchChange,
  globalPaused,
  onTogglePause,
  onToggleSidebar,
  sidebarOpen = true,
  agentCount,
  totalAgents,
}) => {
  const layoutOptions: { value: LayoutPreset; label: string; icon: React.ReactNode }[] = [
    { value: '1x1', label: '1×1', icon: <Square className="w-4 h-4" /> },
    { value: '2x2', label: '2×2', icon: <Grid2x2 className="w-4 h-4" /> },
    { value: '3x3', label: '3×3', icon: <Grid3x3 className="w-4 h-4" /> },
    { value: '2x3', label: '2×3', icon: <Rows className="w-4 h-4" /> },
    { value: 'custom', label: 'Custom', icon: <LayoutGrid className="w-4 h-4" /> },
  ];

  return (
    <div className="bg-white border-b shadow-sm px-4 py-3">
      <div className="flex items-center justify-between">
        {/* Left Section - Layout Controls */}
        <div className="flex items-center space-x-4">
          {/* Sidebar Toggle */}
          <button
            onClick={onToggleSidebar}
            className="p-2 rounded-lg hover:bg-gray-100 transition-colors"
            title={`${sidebarOpen ? 'Hide' : 'Show'} agent list`}
          >
            {sidebarOpen ? (
              <ChevronLeft className="w-4 h-4 text-gray-600" />
            ) : (
              <ChevronRight className="w-4 h-4 text-gray-600" />
            )}
          </button>

          {/* Layout Selector */}
          <div className="flex items-center space-x-2">
            <span className="text-sm text-gray-600 font-medium">Layout:</span>
            <div className="flex items-center bg-gray-100 rounded-lg p-0.5">
              {layoutOptions.map((option) => (
                <button
                  key={option.value}
                  onClick={() => onLayoutChange(option.value)}
                  className={`px-3 py-1.5 rounded-md text-sm font-medium transition-all flex items-center space-x-1 ${
                    selectedLayout === option.value
                      ? 'bg-white text-blue-600 shadow-sm'
                      : 'text-gray-600 hover:text-gray-900'
                  }`}
                  title={`${option.label} layout`}
                >
                  {option.icon}
                  <span className="hidden sm:inline">{option.label}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Agent Count */}
          <div className="text-sm text-gray-600">
            <span className="font-medium">{agentCount}</span>
            <span className="text-gray-400"> / {totalAgents} agents</span>
          </div>
        </div>

        {/* Right Section - Search and Controls */}
        <div className="flex items-center space-x-3">
          {/* Search */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => onSearchChange(e.target.value)}
              placeholder="Search agents..."
              className="pl-9 pr-3 py-1.5 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 w-48"
            />
            {searchTerm && (
              <button
                onClick={() => onSearchChange('')}
                className="absolute right-2 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
              >
                ×
              </button>
            )}
          </div>

          {/* Global Pause/Resume */}
          <button
            onClick={onTogglePause}
            className={`px-4 py-1.5 rounded-lg font-medium text-sm transition-colors flex items-center space-x-2 ${
              globalPaused
                ? 'bg-green-100 text-green-700 hover:bg-green-200'
                : 'bg-yellow-100 text-yellow-700 hover:bg-yellow-200'
            }`}
            title={globalPaused ? 'Resume all agents' : 'Pause all agents'}
          >
            {globalPaused ? (
              <>
                <Play className="w-4 h-4" />
                <span>Resume All</span>
              </>
            ) : (
              <>
                <Pause className="w-4 h-4" />
                <span>Pause All</span>
              </>
            )}
          </button>

          {/* Settings (placeholder for future features) */}
          <button
            className="p-2 rounded-lg hover:bg-gray-100 transition-colors"
            title="Settings"
          >
            <Settings className="w-4 h-4 text-gray-600" />
          </button>
        </div>
      </div>

      {/* Quick Stats Bar */}
      <div className="mt-3 flex items-center space-x-6 text-xs text-gray-600">
        <div className="flex items-center space-x-1">
          <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
          <span>Real-time updates active</span>
        </div>
        <div className="flex items-center space-x-1">
          <span>Update interval: 1s</span>
        </div>
        {globalPaused && (
          <div className="flex items-center space-x-1 text-yellow-600">
            <Pause className="w-3 h-3" />
            <span className="font-medium">All agents paused</span>
          </div>
        )}
        <div className="flex items-center space-x-1">
          <span>Press ESC to toggle fullscreen</span>
        </div>
      </div>
    </div>
  );
};

export default ObservabilityControls;