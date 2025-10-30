import React, { useState, useEffect, useCallback, useRef } from 'react';
import { Search, X, ChevronUp, ChevronDown } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

interface PanelSearchProps {
  content: string;
  isOpen: boolean;
  onClose: () => void;
}

const PanelSearch: React.FC<PanelSearchProps> = ({
  content,
  isOpen,
  onClose,
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [currentMatch, setCurrentMatch] = useState(0);
  const [matches, setMatches] = useState<number[]>([]);
  const searchInputRef = useRef<HTMLInputElement>(null);

  // Focus input when opened
  useEffect(() => {
    if (isOpen && searchInputRef.current) {
      searchInputRef.current.focus();
    }
  }, [isOpen]);

  // Find matches
  useEffect(() => {
    if (!searchTerm || !content) {
      setMatches([]);
      setCurrentMatch(0);
      return;
    }

    const regex = new RegExp(searchTerm, 'gi');
    const foundMatches: number[] = [];
    let match;

    while ((match = regex.exec(content)) !== null) {
      foundMatches.push(match.index);
    }

    setMatches(foundMatches);
    setCurrentMatch(foundMatches.length > 0 ? 0 : -1);
  }, [searchTerm, content]);

  // Navigate matches
  const goToNext = useCallback(() => {
    if (matches.length === 0) return;
    setCurrentMatch((prev) => (prev + 1) % matches.length);
  }, [matches]);

  const goToPrevious = useCallback(() => {
    if (matches.length === 0) return;
    setCurrentMatch((prev) => (prev - 1 + matches.length) % matches.length);
  }, [matches]);

  // Handle keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!isOpen) return;

      if (e.key === 'Escape') {
        onClose();
      } else if (e.key === 'Enter') {
        if (e.shiftKey) {
          goToPrevious();
        } else {
          goToNext();
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose, goToNext, goToPrevious]);

  if (!isOpen) return null;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ y: -20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        exit={{ y: -20, opacity: 0 }}
        className="absolute top-2 right-2 z-20 bg-white rounded-lg shadow-lg border border-gray-200 p-2"
      >
        <div className="flex items-center space-x-2">
          <Search className="w-4 h-4 text-gray-400" />
          <input
            ref={searchInputRef}
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search in output..."
            className="w-48 px-2 py-1 text-sm border-0 focus:outline-none"
          />

          {/* Match Counter */}
          {searchTerm && (
            <span className="text-xs text-gray-500">
              {matches.length > 0 ? (
                <>
                  {currentMatch + 1}/{matches.length}
                </>
              ) : (
                'No matches'
              )}
            </span>
          )}

          {/* Navigation Buttons */}
          <div className="flex items-center space-x-1">
            <button
              onClick={goToPrevious}
              disabled={matches.length === 0}
              className="p-1 rounded hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed"
              title="Previous match (Shift+Enter)"
            >
              <ChevronUp className="w-3 h-3" />
            </button>
            <button
              onClick={goToNext}
              disabled={matches.length === 0}
              className="p-1 rounded hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed"
              title="Next match (Enter)"
            >
              <ChevronDown className="w-3 h-3" />
            </button>
          </div>

          {/* Close Button */}
          <button
            onClick={onClose}
            className="p-1 rounded hover:bg-gray-100"
            title="Close (Esc)"
          >
            <X className="w-3 h-3" />
          </button>
        </div>
      </motion.div>
    </AnimatePresence>
  );
};

export const HighlightedContent: React.FC<{
  content: string;
  searchTerm: string;
  currentMatch: number;
}> = ({ content, searchTerm, currentMatch }) => {
  if (!searchTerm) return <>{content}</>;

  const parts: JSX.Element[] = [];
  const regex = new RegExp(`(${searchTerm})`, 'gi');
  const matches = content.split(regex);
  let matchIndex = 0;

  matches.forEach((part, index) => {
    if (regex.test(part)) {
      const isCurrent = matchIndex === currentMatch;
      parts.push(
        <span
          key={index}
          className={`${
            isCurrent
              ? 'bg-yellow-300 text-black font-bold'
              : 'bg-yellow-100'
          }`}
        >
          {part}
        </span>
      );
      matchIndex++;
    } else {
      parts.push(<span key={index}>{part}</span>);
    }
  });

  return <>{parts}</>;
};

export default PanelSearch;