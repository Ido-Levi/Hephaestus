import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { motion, AnimatePresence } from 'framer-motion';
import { X, ChevronDown, ChevronRight, FileCode, FilePlus, FileX, FileEdit, Loader2 } from 'lucide-react';
import { format } from 'date-fns';
import { apiService } from '@/services/api';
import { cn } from '@/lib/utils';
import 'highlight.js/styles/github.css';

interface GitDiffModalProps {
  commitSha: string;
  onClose: () => void;
}

const GitDiffModal: React.FC<GitDiffModalProps> = ({ commitSha, onClose }) => {
  const [expandedFiles, setExpandedFiles] = useState<Set<string>>(new Set());

  const { data: commitDiff, isLoading } = useQuery({
    queryKey: ['commitDiff', commitSha],
    queryFn: () => apiService.getCommitDiff(commitSha),
    enabled: !!commitSha,
  });

  const toggleFile = (filePath: string) => {
    setExpandedFiles((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(filePath)) {
        newSet.delete(filePath);
      } else {
        newSet.add(filePath);
      }
      return newSet;
    });
  };

  const getFileIcon = (status: string) => {
    switch (status) {
      case 'added':
        return <FilePlus className="w-4 h-4 text-green-600" />;
      case 'deleted':
        return <FileX className="w-4 h-4 text-red-600" />;
      case 'modified':
        return <FileEdit className="w-4 h-4 text-blue-600" />;
      case 'renamed':
        return <FileCode className="w-4 h-4 text-purple-600" />;
      default:
        return <FileCode className="w-4 h-4 text-gray-600" />;
    }
  };

  const renderDiffLine = (line: string, index: number) => {
    const trimmedLine = line;
    let bgColor = '';
    let textColor = 'text-gray-900';
    let linePrefix = ' ';

    if (trimmedLine.startsWith('+')) {
      bgColor = 'bg-green-50';
      textColor = 'text-green-900';
      linePrefix = '+';
    } else if (trimmedLine.startsWith('-')) {
      bgColor = 'bg-red-50';
      textColor = 'text-red-900';
      linePrefix = '-';
    } else if (trimmedLine.startsWith('@@')) {
      bgColor = 'bg-blue-50';
      textColor = 'text-blue-900';
      linePrefix = '@';
    }

    return (
      <div key={index} className={cn('flex font-mono text-xs', bgColor)}>
        <span className={cn('w-8 flex-shrink-0 text-center select-none', textColor)}>
          {linePrefix}
        </span>
        <pre className={cn('flex-1 px-2 overflow-x-auto', textColor)}>
          <code>{trimmedLine}</code>
        </pre>
      </div>
    );
  };

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50"
        onClick={onClose}
      >
        <motion.div
          initial={{ scale: 0.95, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          exit={{ scale: 0.95, opacity: 0 }}
          className="bg-white rounded-lg shadow-2xl w-full max-w-6xl max-h-[90vh] overflow-hidden flex flex-col"
          onClick={(e) => e.stopPropagation()}
        >
          {/* Header */}
          <div className="px-6 py-4 border-b bg-gray-50">
            <div className="flex items-start justify-between">
              <div>
                <h2 className="text-xl font-bold text-gray-900 mb-1">Commit Diff</h2>
                {commitDiff && (
                  <div className="space-y-1">
                    <p className="text-sm font-mono text-gray-600">{commitSha}</p>
                    <p className="text-sm text-gray-700">{commitDiff.commit_message}</p>
                    <div className="flex items-center space-x-4 text-xs text-gray-500">
                      <span>{commitDiff.author}</span>
                      <span>{format(new Date(commitDiff.commit_timestamp), 'MMM d, yyyy HH:mm')}</span>
                      <span className="text-green-600">+{commitDiff.total_insertions}</span>
                      <span className="text-red-600">-{commitDiff.total_deletions}</span>
                      <span>{commitDiff.total_files} files</span>
                    </div>
                  </div>
                )}
              </div>
              <button
                onClick={onClose}
                className="p-2 hover:bg-gray-200 rounded-lg transition-colors"
              >
                <X className="w-5 h-5 text-gray-500" />
              </button>
            </div>
          </div>

          {/* Content */}
          <div className="flex-1 overflow-y-auto p-6">
            {isLoading ? (
              <div className="flex items-center justify-center h-64">
                <Loader2 className="w-8 h-8 text-blue-600 animate-spin" />
              </div>
            ) : commitDiff ? (
              <div className="space-y-4">
                {commitDiff.files.map((file, fileIndex) => {
                  const isExpanded = expandedFiles.has(file.path);

                  return (
                    <div key={fileIndex} className="border rounded-lg overflow-hidden">
                      {/* File Header */}
                      <button
                        onClick={() => toggleFile(file.path)}
                        className="w-full flex items-center justify-between px-4 py-3 bg-gray-50 hover:bg-gray-100 transition-colors"
                      >
                        <div className="flex items-center space-x-3">
                          {isExpanded ? (
                            <ChevronDown className="w-4 h-4 text-gray-600" />
                          ) : (
                            <ChevronRight className="w-4 h-4 text-gray-600" />
                          )}
                          {getFileIcon(file.status)}
                          <span className="font-mono text-sm text-gray-900">{file.path}</span>
                        </div>
                        <div className="flex items-center space-x-4 text-xs">
                          <span className={cn(
                            'px-2 py-1 rounded',
                            file.status === 'added' && 'bg-green-100 text-green-700',
                            file.status === 'deleted' && 'bg-red-100 text-red-700',
                            file.status === 'modified' && 'bg-blue-100 text-blue-700',
                            file.status === 'renamed' && 'bg-purple-100 text-purple-700'
                          )}>
                            {file.status}
                          </span>
                          <span className="text-green-600">+{file.insertions}</span>
                          <span className="text-red-600">-{file.deletions}</span>
                        </div>
                      </button>

                      {/* File Diff Content */}
                      {isExpanded && (
                        <div className="border-t bg-white">
                          <div className="overflow-x-auto">
                            {file.diff.split('\n').map((line, lineIndex) =>
                              renderDiffLine(line, lineIndex)
                            )}
                          </div>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            ) : (
              <div className="flex items-center justify-center h-64 text-gray-500">
                <p>No diff data available</p>
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="px-6 py-4 border-t bg-gray-50 flex justify-end">
            <button
              onClick={onClose}
              className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors"
            >
              Close
            </button>
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
};

export default GitDiffModal;
