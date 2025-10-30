import React, { useRef, useEffect, useState, useCallback } from 'react';
import { motion } from 'framer-motion';
import {
  Copy,
  Maximize2,
  Minimize2,
  Pause,
  Play,
  AlertCircle,
  Bot,
  EyeOff,
  Clock,
  FileText,
  Search
} from 'lucide-react';
import PanelSearch, { HighlightedContent } from './PanelSearch';
import { formatDistanceToNow } from 'date-fns';
import { Agent } from '@/types';

interface OutputData {
  output: string;
  timestamp: string;
  isLoading: boolean;
  error: string | null;
  isConnected: boolean;
  lastUpdateTime: Date | null;
}

interface ObservabilityPanelProps {
  agent: Agent;
  output?: OutputData;
  isFullscreen?: boolean;
  onToggleFullscreen?: () => void;
  onHide?: () => void;
  onClose?: () => void;
  isPaused?: boolean;
}

const ObservabilityPanel: React.FC<ObservabilityPanelProps> = ({
  agent,
  output = {
    output: '',
    timestamp: '',
    isLoading: false,
    error: null,
    isConnected: false,
    lastUpdateTime: null,
  },
  isFullscreen = false,
  onToggleFullscreen,
  onHide,
  onClose,
  isPaused = false,
}) => {
  const [autoScroll, setAutoScroll] = useState(true);
  const [localPaused, setLocalPaused] = useState(false);
  const outputRef = useRef<HTMLPreElement>(null);
  const lastScrollPosition = useRef(0);
  const initialScrollDone = useRef(false);

  // Auto-scroll to bottom on initial mount
  useEffect(() => {
    if (outputRef.current && !initialScrollDone.current) {
      outputRef.current.scrollTop = outputRef.current.scrollHeight;
      initialScrollDone.current = true;
    }
  }, []);

  // Auto-scroll to bottom when new content arrives
  useEffect(() => {
    if (autoScroll && outputRef.current && !isPaused && !localPaused) {
      const element = outputRef.current;
      // Always scroll to bottom when auto-scroll is enabled
      element.scrollTop = element.scrollHeight;
    }
  }, [output.output, autoScroll, isPaused, localPaused]);

  // Handle scroll events
  const handleScroll = useCallback(() => {
    if (outputRef.current) {
      const element = outputRef.current;
      const isNearBottom = element.scrollTop + element.clientHeight >= element.scrollHeight - 50;
      setAutoScroll(isNearBottom);
      lastScrollPosition.current = element.scrollTop;
    }
  }, []);

  // Copy to clipboard
  const copyToClipboard = async () => {
    try {
      await navigator.clipboard.writeText(output.output);
    } catch (err) {
      console.error('Failed to copy to clipboard:', err);
    }
  };

  // Get status color
  const getStatusColor = () => {
    if (output.error) return 'bg-red-500';
    if (output.isConnected) return 'bg-green-500 animate-pulse';
    return 'bg-gray-400';
  };

  // Get agent status color
  const getAgentStatusColor = () => {
    switch (agent.status) {
      case 'working': return 'text-green-600 bg-green-50';
      case 'idle': return 'text-gray-600 bg-gray-50';
      case 'stuck': return 'text-red-600 bg-red-50';
      case 'terminated': return 'text-gray-500 bg-gray-100';
      default: return 'text-gray-600 bg-gray-50';
    }
  };

  // Calculate line count
  const lineCount = output.output ? output.output.split('\n').length : 0;

  // Calculate data size
  const dataSize = output.output ? (output.output.length / 1024).toFixed(1) : '0';

  const isPausedEffective = isPaused || localPaused;

  if (isFullscreen) {
    return (
      <div className="fixed inset-0 z-50 bg-gray-900 flex flex-col">
        {/* Fullscreen Header */}
        <div className="bg-gray-800 border-b border-gray-700 px-6 py-3 flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className={`w-2 h-2 rounded-full ${getStatusColor()}`} />
            <div className="flex items-center space-x-2">
              <Bot className="w-5 h-5 text-gray-400" />
              <h3 className="text-white font-semibold">
                Agent {agent.id.substring(0, 8)}
              </h3>
            </div>
            <span className={`px-2 py-0.5 rounded text-xs font-medium ${getAgentStatusColor()}`}>
              {agent.status.toUpperCase()}
            </span>
            {agent.current_task_id && (
              <div className="flex items-center text-xs text-gray-400">
                <FileText className="w-3 h-3 mr-1" />
                Task: {agent.current_task_id.substring(0, 8)}
              </div>
            )}
          </div>

          <div className="flex items-center space-x-3">
            {output.lastUpdateTime && (
              <div className="flex items-center text-xs text-gray-400">
                <Clock className="w-3 h-3 mr-1" />
                {formatDistanceToNow(output.lastUpdateTime, { addSuffix: true })}
              </div>
            )}

            <button
              onClick={copyToClipboard}
              className="p-2 rounded bg-gray-700 text-gray-300 hover:bg-gray-600 transition-colors"
              title="Copy output"
            >
              <Copy className="w-4 h-4" />
            </button>

            <button
              onClick={() => setLocalPaused(!localPaused)}
              className={`p-2 rounded transition-colors ${
                isPausedEffective
                  ? 'bg-green-700 text-green-300 hover:bg-green-600'
                  : 'bg-yellow-700 text-yellow-300 hover:bg-yellow-600'
              }`}
              title={isPausedEffective ? 'Resume' : 'Pause'}
            >
              {isPausedEffective ? <Play className="w-4 h-4" /> : <Pause className="w-4 h-4" />}
            </button>

            <button
              onClick={onClose}
              className="p-2 rounded text-gray-400 hover:text-white hover:bg-gray-700 transition-colors"
              title="Exit fullscreen"
            >
              <Minimize2 className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Fullscreen Output */}
        <div className="flex-1 relative bg-gray-900 min-h-0">
          <pre
            ref={outputRef}
            onScroll={handleScroll}
            className="absolute inset-0 p-4 overflow-auto font-mono text-xs text-green-400 whitespace-pre-wrap"
            style={{
              lineHeight: '1.4',
              fontFamily: 'Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace'
            }}
          >
            {output.output || 'Waiting for output...'}
          </pre>

          {!autoScroll && (
            <motion.button
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="absolute bottom-4 right-4 bg-blue-600 text-white px-3 py-1 rounded-full text-xs hover:bg-blue-700 transition-colors"
              onClick={() => {
                setAutoScroll(true);
                if (outputRef.current) {
                  outputRef.current.scrollTop = outputRef.current.scrollHeight;
                }
              }}
            >
              Scroll to bottom
            </motion.button>
          )}
        </div>

        {/* Fullscreen Footer */}
        <div className="bg-gray-800 border-t border-gray-700 px-6 py-2 flex justify-between items-center text-xs text-gray-400">
          <div className="flex space-x-4">
            <span>Lines: {lineCount}</span>
            <span>Size: {dataSize}KB</span>
          </div>
          <div className="flex items-center space-x-2">
            <span>Auto-scroll: {autoScroll ? 'ON' : 'OFF'}</span>
            {isPausedEffective && <span className="text-yellow-400">• PAUSED</span>}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 h-full flex flex-col">
      {/* Panel Header */}
      <div className="px-3 py-2 border-b border-gray-200 flex items-center justify-between bg-gray-50 rounded-t-lg">
        <div className="flex items-center space-x-2 flex-1 min-w-0">
          <div className={`w-2 h-2 rounded-full flex-shrink-0 ${getStatusColor()}`} />
          <Bot className="w-4 h-4 text-gray-500 flex-shrink-0" />
          <span className="text-sm font-medium text-gray-800 truncate">
            {agent.id.substring(0, 8)}
          </span>
          <span className={`px-1.5 py-0.5 rounded text-xs font-medium flex-shrink-0 ${getAgentStatusColor()}`}>
            {agent.status}
          </span>
        </div>

        <div className="flex items-center space-x-1">
          <button
            onClick={copyToClipboard}
            className="p-1 rounded hover:bg-gray-200 transition-colors"
            title="Copy"
          >
            <Copy className="w-3 h-3 text-gray-600" />
          </button>

          <button
            onClick={() => setLocalPaused(!localPaused)}
            className={`p-1 rounded hover:bg-gray-200 transition-colors ${
              isPausedEffective ? 'text-green-600' : 'text-yellow-600'
            }`}
            title={isPausedEffective ? 'Resume' : 'Pause'}
          >
            {isPausedEffective ? <Play className="w-3 h-3" /> : <Pause className="w-3 h-3" />}
          </button>

          {onToggleFullscreen && (
            <button
              onClick={onToggleFullscreen}
              className="p-1 rounded hover:bg-gray-200 transition-colors"
              title="Fullscreen"
            >
              <Maximize2 className="w-3 h-3 text-gray-600" />
            </button>
          )}

          {onHide && (
            <button
              onClick={onHide}
              className="p-1 rounded hover:bg-gray-200 transition-colors"
              title="Hide"
            >
              <EyeOff className="w-3 h-3 text-gray-600" />
            </button>
          )}
        </div>
      </div>

      {/* Task Info */}
      {agent.current_task_id && (
        <div className="px-3 py-1 bg-blue-50 border-b border-blue-100 text-xs text-blue-700">
          <FileText className="w-3 h-3 inline mr-1" />
          Task: {agent.current_task_id.substring(0, 12)}
        </div>
      )}

      {/* Error State */}
      {output.error && (
        <div className="px-3 py-2 bg-red-50 border-b border-red-100 flex items-center justify-between">
          <div className="flex items-center space-x-2 text-red-600 text-xs">
            <AlertCircle className="w-3 h-3" />
            <span>{output.error}</span>
          </div>
        </div>
      )}

      {/* Output Area */}
      <div className="flex-1 relative bg-gray-900 min-h-0">
        {output.isLoading && !output.output ? (
          <div className="flex items-center justify-center h-full">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-green-400"></div>
          </div>
        ) : (
          <pre
            ref={outputRef}
            onScroll={handleScroll}
            className="absolute inset-0 p-2 overflow-auto font-mono text-xs text-green-400 whitespace-pre-wrap"
            style={{
              lineHeight: '1.3',
              fontSize: '10px',
            }}
          >
            {output.output || 'No output yet...'}
          </pre>
        )}

        {!autoScroll && output.output && (
          <motion.button
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="absolute bottom-2 right-2 bg-blue-500 text-white px-2 py-0.5 rounded text-xs hover:bg-blue-600 transition-colors"
            onClick={() => {
              setAutoScroll(true);
              if (outputRef.current) {
                outputRef.current.scrollTop = outputRef.current.scrollHeight;
              }
            }}
          >
            ↓
          </motion.button>
        )}
      </div>

      {/* Panel Footer */}
      <div className="px-3 py-1 border-t border-gray-200 bg-gray-50 rounded-b-lg flex justify-between items-center text-xs text-gray-500">
        <div className="flex space-x-3">
          <span>{lineCount} lines</span>
          <span>{dataSize}KB</span>
        </div>
        {output.lastUpdateTime && (
          <div className="flex items-center">
            <Clock className="w-3 h-3 mr-1" />
            {formatDistanceToNow(output.lastUpdateTime, { addSuffix: true, includeSeconds: true })}
          </div>
        )}
      </div>
    </div>
  );
};

export default ObservabilityPanel;