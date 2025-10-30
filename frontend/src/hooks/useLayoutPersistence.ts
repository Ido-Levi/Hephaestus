import { useCallback } from 'react';
import type { GridLayout, LayoutPreset } from '@/pages/Observability';

const STORAGE_KEY = 'hephaestus_observability_layout';
const MAX_SAVED_LAYOUTS = 10;

export interface SavedLayout {
  id: string;
  name?: string;
  selectedLayout: LayoutPreset;
  gridLayout: GridLayout;
  visibleAgents: string[];
  timestamp: number;
}

export interface LayoutHistory {
  current?: SavedLayout;
  saved: SavedLayout[];
}

export const useLayoutPersistence = () => {
  // Load layout from localStorage
  const loadLayout = useCallback((): SavedLayout | null => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) {
        const history: LayoutHistory = JSON.parse(stored);
        return history.current || null;
      }
    } catch (error) {
      console.error('Failed to load layout from localStorage:', error);
    }
    return null;
  }, []);

  // Save layout to localStorage
  const saveLayout = useCallback((layout: Omit<SavedLayout, 'id' | 'timestamp'>) => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      const history: LayoutHistory = stored ? JSON.parse(stored) : { saved: [] };

      const newLayout: SavedLayout = {
        ...layout,
        id: Date.now().toString(),
        timestamp: Date.now(),
      };

      history.current = newLayout;
      localStorage.setItem(STORAGE_KEY, JSON.stringify(history));

      return newLayout.id;
    } catch (error) {
      console.error('Failed to save layout to localStorage:', error);
      return null;
    }
  }, []);

  // Save a named layout
  const saveNamedLayout = useCallback((
    layout: Omit<SavedLayout, 'id' | 'timestamp'>,
    name: string
  ) => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      const history: LayoutHistory = stored ? JSON.parse(stored) : { saved: [] };

      const newLayout: SavedLayout = {
        ...layout,
        id: Date.now().toString(),
        name,
        timestamp: Date.now(),
      };

      // Add to saved layouts (limit to MAX_SAVED_LAYOUTS)
      history.saved = [newLayout, ...history.saved.slice(0, MAX_SAVED_LAYOUTS - 1)];
      localStorage.setItem(STORAGE_KEY, JSON.stringify(history));

      return newLayout.id;
    } catch (error) {
      console.error('Failed to save named layout to localStorage:', error);
      return null;
    }
  }, []);

  // Load a specific saved layout
  const loadSavedLayout = useCallback((layoutId: string): SavedLayout | null => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) {
        const history: LayoutHistory = JSON.parse(stored);
        const layout = history.saved.find(l => l.id === layoutId);
        if (layout) {
          // Set as current
          history.current = layout;
          localStorage.setItem(STORAGE_KEY, JSON.stringify(history));
          return layout;
        }
      }
    } catch (error) {
      console.error('Failed to load saved layout from localStorage:', error);
    }
    return null;
  }, []);

  // Get all saved layouts
  const getSavedLayouts = useCallback((): SavedLayout[] => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) {
        const history: LayoutHistory = JSON.parse(stored);
        return history.saved || [];
      }
    } catch (error) {
      console.error('Failed to get saved layouts from localStorage:', error);
    }
    return [];
  }, []);

  // Delete a saved layout
  const deleteSavedLayout = useCallback((layoutId: string): boolean => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) {
        const history: LayoutHistory = JSON.parse(stored);
        history.saved = history.saved.filter(l => l.id !== layoutId);
        localStorage.setItem(STORAGE_KEY, JSON.stringify(history));
        return true;
      }
    } catch (error) {
      console.error('Failed to delete saved layout from localStorage:', error);
    }
    return false;
  }, []);

  // Clear all layouts
  const clearLayout = useCallback(() => {
    try {
      localStorage.removeItem(STORAGE_KEY);
      return true;
    } catch (error) {
      console.error('Failed to clear layouts from localStorage:', error);
      return false;
    }
  }, []);

  // Export layouts to JSON
  const exportLayouts = useCallback(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) {
        const history: LayoutHistory = JSON.parse(stored);
        const blob = new Blob([JSON.stringify(history, null, 2)], {
          type: 'application/json',
        });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `observability-layouts-${Date.now()}.json`;
        a.click();
        URL.revokeObjectURL(url);
        return true;
      }
    } catch (error) {
      console.error('Failed to export layouts:', error);
    }
    return false;
  }, []);

  // Import layouts from JSON
  const importLayouts = useCallback((file: File): Promise<boolean> => {
    return new Promise((resolve) => {
      const reader = new FileReader();
      reader.onload = (e) => {
        try {
          const content = e.target?.result as string;
          const history: LayoutHistory = JSON.parse(content);

          // Validate structure
          if (!history.saved || !Array.isArray(history.saved)) {
            throw new Error('Invalid layout file format');
          }

          localStorage.setItem(STORAGE_KEY, content);
          resolve(true);
        } catch (error) {
          console.error('Failed to import layouts:', error);
          resolve(false);
        }
      };
      reader.onerror = () => resolve(false);
      reader.readAsText(file);
    });
  }, []);

  return {
    loadLayout,
    saveLayout,
    saveNamedLayout,
    loadSavedLayout,
    getSavedLayouts,
    deleteSavedLayout,
    clearLayout,
    exportLayouts,
    importLayouts,
  };
};