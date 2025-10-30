import React, { useRef, useEffect, useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  X,
  Copy,
  Maximize2,
  Minimize2,
  Search,
  RefreshCw,
  Pause,
  Play,
  AlertCircle,
  Wifi,
  WifiOff,
  Clock,
  MessageCircle,
  Send,
  Check,
  XCircle
} from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { useRealTimeAgentOutput } from '@/hooks/useRealTimeAgentOutput';
import { Agent } from '@/types';
import { apiService } from '@/services/api';

interface RealTimeAgentOutputProps {
  agent: Agent | null;
  onClose: () => void;
  isFullscreen?: boolean;
}

const RealTimeAgentOutput: React.FC<RealTimeAgentOutputProps> = ({
  agent,
  onClose,
  isFullscreen: initialFullscreen = false,
}) => {
  const [isFullscreen, setIsFullscreen] = useState(initialFullscreen);
  const [searchTerm, setSearchTerm] = useState('');
  const [isPaused, setIsPaused] = useState(false);
  const [autoScroll, setAutoScroll] = useState(true);
  const [isSelecting, setIsSelecting] = useState(false);

  // Message input state
  const [messageText, setMessageText] = useState('');
  const [isSending, setIsSending] = useState(false);
  const [sendStatus, setSendStatus] = useState<'idle' | 'success' | 'error'>('idle');
  const [sendErrorMessage, setSendErrorMessage] = useState('');

  const outputRef = useRef<HTMLPreElement>(null);
  const messageInputRef = useRef<HTMLTextAreaElement>(null);
  const searchInputRef = useRef<HTMLInputElement>(null);
  const lastScrollPosition = useRef(0);

  const {
    output,
    isLoading,
    error,
    isConnected,
    lastUpdateTime,
    retry,
  } = useRealTimeAgentOutput(agent?.id || null, {
    enabled: !isPaused && !!agent,
    updateInterval: 1000,
  });

  // Auto-scroll to bottom when new content arrives
  useEffect(() => {
    if (autoScroll && outputRef.current && lastUpdateTime) {
      const element = outputRef.current;
      const isNearBottom = element.scrollTop + element.clientHeight >= element.scrollHeight - 100;

      if (isNearBottom || element.scrollHeight <= element.clientHeight) {
        element.scrollTop = element.scrollHeight;
      }
    }
  }, [output, autoScroll, lastUpdateTime]);

  // Handle scroll events to determine if user is at bottom
  const handleScroll = useCallback(() => {
    if (outputRef.current && !isSelecting) {
      const element = outputRef.current;
      const isNearBottom = element.scrollTop + element.clientHeight >= element.scrollHeight - 50;
      setAutoScroll(isNearBottom);
      lastScrollPosition.current = element.scrollTop;
    }
  }, [isSelecting]);

  // Handle text selection to pause auto-scroll
  const handleMouseDown = useCallback(() => {
    setIsSelecting(true);
  }, []);

  const handleMouseUp = useCallback(() => {
    setTimeout(() => setIsSelecting(false), 100);
  }, []);

  // Copy to clipboard functionality
  const copyToClipboard = async () => {
    try {
      const textToCopy = searchTerm ?
        output.split('\n').filter(line =>
          line.toLowerCase().includes(searchTerm.toLowerCase())
        ).join('\n') :
        output;

      await navigator.clipboard.writeText(textToCopy);
      // Could add toast notification here
    } catch (err) {
      console.error('Failed to copy to clipboard:', err);
    }
  };

  // Send message to agent
  const handleSendMessage = async () => {
    if (!messageText.trim() || !agent || isSending) return;

    if (agent.status === 'terminated') {
      setSendStatus('error');
      setSendErrorMessage('Cannot send message to terminated agent');
      setTimeout(() => {
        setSendStatus('idle');
        setSendErrorMessage('');
      }, 3000);
      return;
    }

    setIsSending(true);
    setSendStatus('idle');

    try {
      const response = await apiService.sendMessage(messageText, agent.id);

      if (response.success) {
        setSendStatus('success');
        setMessageText('');

        // Reset status after 2 seconds
        setTimeout(() => {
          setSendStatus('idle');
        }, 2000);
      } else {
        setSendStatus('error');
        setSendErrorMessage(response.message || 'Failed to send message');
        setTimeout(() => {
          setSendStatus('idle');
          setSendErrorMessage('');
        }, 3000);
      }
    } catch (error: any) {
      setSendStatus('error');
      setSendErrorMessage(error.response?.data?.detail || 'Failed to send message');
      setTimeout(() => {
        setSendStatus('idle');
        setSendErrorMessage('');
      }, 3000);
    } finally {
      setIsSending(false);
    }
  };

  // Filter output based on search
  const filteredOutput = searchTerm ?
    output.split('\n').filter(line =>
      line.toLowerCase().includes(searchTerm.toLowerCase())
    ).join('\n') :
    output;

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Don't interfere with message input
      const isMessageInputFocused = messageInputRef.current?.matches(':focus');

      if (e.key === 'Escape') {
        if (isMessageInputFocused) {
          messageInputRef.current?.blur();
        } else if (searchTerm) {
          setSearchTerm('');
          searchInputRef.current?.blur();
        } else {
          onClose();
        }
      } else if (e.ctrlKey || e.metaKey) {
        if (e.key === 'c' && !window.getSelection()?.toString() && !isMessageInputFocused) {
          e.preventDefault();
          copyToClipboard();
        } else if (e.key === 'f' && !isMessageInputFocused) {
          e.preventDefault();
          searchInputRef.current?.focus();
        } else if (e.key === 'r' && !isMessageInputFocused) {
          e.preventDefault();
          retry();
        }
      } else if (e.key === ' ' && !searchInputRef.current?.matches(':focus') && !isMessageInputFocused) {
        e.preventDefault();
        setIsPaused(!isPaused);
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [onClose, copyToClipboard, retry, isPaused, searchTerm]);

  if (!agent) return null;

  const modalClass = isFullscreen
    ? 'fixed inset-0 z-50 bg-gray-900'
    : 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50';

  const contentClass = isFullscreen
    ? 'w-full h-full flex flex-col'
    : 'bg-white dark:bg-gray-900 rounded-lg shadow-xl w-full max-w-6xl h-[80vh] flex flex-col';

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className={modalClass}
        onClick={isFullscreen ? undefined : onClose}
      >
        <motion.div
          initial={{ scale: isFullscreen ? 1 : 0.9 }}
          animate={{ scale: 1 }}
          className={contentClass}
          onClick={(e) => e.stopPropagation()}
        >
          {/* Header */}
          <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between bg-white dark:bg-gray-900 rounded-t-lg">
            <div className="flex items-center space-x-3">
              <div className="flex items-center space-x-2">
                <div className={`w-2 h-2 rounded-full ${
                  isConnected ? 'bg-green-500 animate-pulse' : 'bg-red-500'
                }`} />
                <h3 className="text-lg font-semibold text-gray-800 dark:text-white">
                  Agent {agent.id.substring(0, 8)} - Output
                </h3>
                {isConnected ? (
                  <Wifi className="w-4 h-4 text-green-500" />
                ) : (
                  <WifiOff className="w-4 h-4 text-red-500" />
                )}
              </div>

              {lastUpdateTime && (
                <div className="flex items-center text-sm text-gray-500 dark:text-gray-400">
                  <Clock className="w-3 h-3 mr-1" />
                  Updated {formatDistanceToNow(lastUpdateTime, { addSuffix: true })}
                </div>
              )}
            </div>

            <div className="flex items-center space-x-2">
              {/* Search */}
              <div className="relative">
                <Search className="absolute left-2 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
                <input
                  ref={searchInputRef}
                  type="text"
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  placeholder="Search output..."
                  className="pl-8 pr-3 py-1 text-sm border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                />
              </div>

              {/* Controls */}
              <button
                onClick={() => setIsPaused(!isPaused)}
                className={`p-2 rounded-lg transition-colors ${
                  isPaused
                    ? 'bg-green-100 text-green-700 hover:bg-green-200 dark:bg-green-800 dark:text-green-200'
                    : 'bg-yellow-100 text-yellow-700 hover:bg-yellow-200 dark:bg-yellow-800 dark:text-yellow-200'
                }`}
                title={isPaused ? 'Resume updates (Space)' : 'Pause updates (Space)'}
              >
                {isPaused ? <Play className="w-4 h-4" /> : <Pause className="w-4 h-4" />}
              </button>

              {error && (
                <button
                  onClick={retry}
                  className="p-2 rounded-lg bg-red-100 text-red-700 hover:bg-red-200 dark:bg-red-800 dark:text-red-200 transition-colors"
                  title="Retry connection (Ctrl+R)"
                >
                  <RefreshCw className="w-4 h-4" />
                </button>
              )}

              <button
                onClick={copyToClipboard}
                className="p-2 rounded-lg bg-gray-100 text-gray-700 hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-300 transition-colors"
                title="Copy output (Ctrl+C)"
              >
                <Copy className="w-4 h-4" />
              </button>

              <button
                onClick={() => setIsFullscreen(!isFullscreen)}
                className="p-2 rounded-lg bg-gray-100 text-gray-700 hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-300 transition-colors"
                title="Toggle fullscreen"
              >
                {isFullscreen ? <Minimize2 className="w-4 h-4" /> : <Maximize2 className="w-4 h-4" />}
              </button>

              {!isFullscreen && (
                <button
                  onClick={onClose}
                  className="p-2 rounded-lg text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 transition-colors"
                  title="Close (Escape)"
                >
                  <X className="w-4 h-4" />
                </button>
              )}
            </div>
          </div>

          {/* Error state */}
          {error && (
            <div className="px-6 py-3 bg-red-50 dark:bg-red-900/20 border-b border-red-200 dark:border-red-800">
              <div className="flex items-center space-x-2 text-red-700 dark:text-red-400">
                <AlertCircle className="w-4 h-4" />
                <span className="text-sm">{error}</span>
                <button
                  onClick={retry}
                  className="text-sm underline hover:no-underline"
                >
                  Retry
                </button>
              </div>
            </div>
          )}

          {/* Output content */}
          <div className="flex-1 min-h-0 relative bg-gray-50 dark:bg-gray-800">
            {isLoading && !output && (
              <div className="flex items-center justify-center h-32">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
              </div>
            )}

            <pre
              ref={outputRef}
              onScroll={handleScroll}
              onMouseDown={handleMouseDown}
              onMouseUp={handleMouseUp}
              className="absolute inset-0 p-6 overflow-auto font-mono text-xs bg-gray-900 text-green-400 whitespace-pre-wrap selection:bg-blue-500 selection:text-white"
              style={{
                lineHeight: '1.4',
                fontFamily: 'Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace'
              }}
            >
              {filteredOutput || (output ? 'No matching lines found' : 'No output available yet...')}
            </pre>

            {/* Scroll indicator */}
            {!autoScroll && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="absolute bottom-4 right-4 bg-blue-500 text-white px-3 py-1 rounded-full text-xs cursor-pointer hover:bg-blue-600 transition-colors"
                onClick={() => {
                  setAutoScroll(true);
                  if (outputRef.current) {
                    outputRef.current.scrollTop = outputRef.current.scrollHeight;
                  }
                }}
              >
                Scroll to bottom
              </motion.div>
            )}
          </div>

          {/* Message Input */}
          {agent.status !== 'terminated' && (
            <div className="px-6 py-3 border-t border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900">
              <div className="flex items-start space-x-3">
                <MessageCircle className="w-5 h-5 text-gray-400 mt-2 flex-shrink-0" />
                <div className="flex-1">
                  <textarea
                    ref={messageInputRef}
                    value={messageText}
                    onChange={(e) => setMessageText(e.target.value)}
                    onKeyDown={(e) => {
                      if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
                        e.preventDefault();
                        handleSendMessage();
                      }
                      // Don't interfere with other keyboard shortcuts
                      e.stopPropagation();
                    }}
                    placeholder="Send a message to this agent..."
                    rows={1}
                    disabled={isSending}
                    className="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none dark:bg-gray-800 dark:text-white disabled:opacity-50 disabled:cursor-not-allowed"
                    style={{
                      minHeight: '40px',
                      maxHeight: '120px',
                      height: 'auto',
                      overflowY: messageText.split('\n').length > 3 ? 'auto' : 'hidden'
                    }}
                    onInput={(e) => {
                      const target = e.target as HTMLTextAreaElement;
                      target.style.height = 'auto';
                      target.style.height = Math.min(target.scrollHeight, 120) + 'px';
                    }}
                  />
                  {sendStatus !== 'idle' && (
                    <motion.div
                      initial={{ opacity: 0, y: -5 }}
                      animate={{ opacity: 1, y: 0 }}
                      className="mt-2"
                    >
                      {sendStatus === 'success' ? (
                        <div className="flex items-center text-xs text-green-600 dark:text-green-400">
                          <Check className="w-3 h-3 mr-1" />
                          Message sent successfully
                        </div>
                      ) : (
                        <div className="flex items-center text-xs text-red-600 dark:text-red-400">
                          <XCircle className="w-3 h-3 mr-1" />
                          {sendErrorMessage || 'Failed to send message'}
                        </div>
                      )}
                    </motion.div>
                  )}
                </div>
                <button
                  onClick={handleSendMessage}
                  disabled={isSending || !messageText.trim()}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center space-x-2 flex-shrink-0"
                  title="Send message (Ctrl/Cmd + Enter)"
                >
                  {isSending ? (
                    <RefreshCw className="w-4 h-4 animate-spin" />
                  ) : (
                    <>
                      <Send className="w-4 h-4" />
                      <span className="text-sm">Send</span>
                    </>
                  )}
                </button>
              </div>
            </div>
          )}

          {/* Footer with stats */}
          <div className="px-6 py-2 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800 text-xs text-gray-500 dark:text-gray-400 flex justify-between items-center rounded-b-lg">
            <div className="flex space-x-4">
              <span>Lines: {output.split('\n').length}</span>
              <span>Characters: {output.length}</span>
              {searchTerm && (
                <span>Filtered: {filteredOutput.split('\n').length} lines</span>
              )}
            </div>

            <div className="flex items-center space-x-2">
              <span>Auto-scroll: {autoScroll ? 'ON' : 'OFF'}</span>
              {isPaused && <span className="text-yellow-500">• PAUSED</span>}
            </div>
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
};

export default RealTimeAgentOutput;