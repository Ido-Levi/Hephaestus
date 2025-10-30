import React, { useMemo, useCallback } from 'react';
import GridLayout from 'react-grid-layout';
import ObservabilityPanel from './ObservabilityPanel';
import { Agent } from '@/types';
import 'react-grid-layout/css/styles.css';
import 'react-resizable/css/styles.css';
import '@/styles/observability-grid.css';

interface OutputData {
  output: string;
  timestamp: string;
  isLoading: boolean;
  error: string | null;
  isConnected: boolean;
  lastUpdateTime: Date | null;
}

interface ObservabilityGridLayoutProps {
  agents: Agent[];
  visibleAgents: Set<string>;
  agentOutputs: Record<string, OutputData>;
  cols: number;
  rows: number;
  globalPaused: boolean;
  onLayoutChange?: (layout: GridLayout.Layout[]) => void;
  onToggleFullscreen: (agentId: string) => void;
  onToggleAgent: (agentId: string) => void;
}

const ObservabilityGridLayout: React.FC<ObservabilityGridLayoutProps> = ({
  agents,
  visibleAgents,
  agentOutputs,
  cols,
  rows,
  globalPaused,
  onLayoutChange,
  onToggleFullscreen,
  onToggleAgent,
}) => {
  // Generate layout from visible agents
  const layout = useMemo(() => {
    const items: GridLayout.Layout[] = [];
    let index = 0;

    Array.from(visibleAgents).forEach((agentId) => {
      if (index >= cols * rows) return; // Don't exceed grid capacity

      items.push({
        i: agentId,
        x: index % cols,
        y: Math.floor(index / cols),
        w: 1,
        h: 1,
        minW: 1,
        minH: 1,
        maxW: cols,
        maxH: rows,
      });
      index++;
    });

    return items;
  }, [visibleAgents, cols, rows]);

  // Handle layout change (after drag/resize)
  const handleLayoutChange = useCallback((newLayout: GridLayout.Layout[]) => {
    if (onLayoutChange) {
      onLayoutChange(newLayout);
    }
  }, [onLayoutChange]);

  // Calculate grid dimensions
  const containerHeight = useMemo(() => {
    // Calculate based on viewport height minus header/controls
    return window.innerHeight - 250; // Adjust based on your header height
  }, []);

  const rowHeight = useMemo(() => {
    return (containerHeight - (rows - 1) * 10) / rows; // 10px gap between rows
  }, [containerHeight, rows]);

  return (
    <div className="h-full w-full p-4 bg-gray-50 overflow-auto">
      <GridLayout
        className="layout"
        layout={layout}
        cols={cols}
        rowHeight={rowHeight}
        width={window.innerWidth - 320} // Adjust for sidebar
        margin={[16, 16]}
        containerPadding={[16, 16]}
        onLayoutChange={handleLayoutChange}
        draggableHandle=".drag-handle"
        isDraggable={true}
        isResizable={true}
        compactType="vertical" // Allow vertical compacting and rearrangement
        preventCollision={false} // Allow items to push each other around
        useCSSTransforms={true}
      >
        {Array.from(visibleAgents).map((agentId) => {
          const agent = agents.find(a => a.id === agentId);
          if (!agent) return null;

          return (
            <div key={agentId} className="grid-item relative">
              <ObservabilityPanel
                agent={agent}
                output={agentOutputs[agentId]}
                onToggleFullscreen={() => onToggleFullscreen(agentId)}
                onHide={() => onToggleAgent(agentId)}
                isPaused={globalPaused}
              />
              {/* Drag handle positioned to avoid buttons - left side of header only */}
              <div className="drag-handle absolute top-2 left-3 w-14 h-7 cursor-grab active:cursor-grabbing flex items-center justify-center opacity-30 hover:opacity-80 transition-all z-20 rounded hover:bg-gray-200/50" title="Drag to reposition panel">
                <svg className="w-5 h-5 text-gray-600" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M9 3C9 2.44772 8.55228 2 8 2C7.44772 2 7 2.44772 7 3V21C7 21.5523 7.44772 22 8 22C8.55228 22 9 21.5523 9 21V3Z" />
                  <path d="M17 3C17 2.44772 16.5523 2 16 2C15.4477 2 15 2.44772 15 3V21C15 21.5523 15.4477 22 16 22C16.5523 22 17 21.5523 17 21V3Z" />
                </svg>
              </div>
            </div>
          );
        })}
      </GridLayout>
    </div>
  );
};

export default ObservabilityGridLayout;