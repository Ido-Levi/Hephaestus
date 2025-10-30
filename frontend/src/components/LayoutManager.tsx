import React, { useState, useEffect } from 'react';
import { Save, FolderOpen, Trash2, Star, Layout, Plus } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

export interface SavedLayout {
  id: string;
  name: string;
  cols: number;
  rows: number;
  panels: any[];
  visibleAgents: string[];
  createdAt: Date;
  isDefault?: boolean;
}

interface LayoutManagerProps {
  currentLayout: {
    cols: number;
    rows: number;
    panels: any[];
    visibleAgents: string[];
  };
  onLoadLayout: (layout: SavedLayout) => void;
  onSaveLayout?: (layout: SavedLayout) => void;
}

const LayoutManager: React.FC<LayoutManagerProps> = ({
  currentLayout,
  onLoadLayout,
  onSaveLayout,
}) => {
  const [savedLayouts, setSavedLayouts] = useState<SavedLayout[]>([]);
  const [showSaveDialog, setShowSaveDialog] = useState(false);
  const [showLoadDialog, setShowLoadDialog] = useState(false);
  const [layoutName, setLayoutName] = useState('');
  const [setAsDefault, setSetAsDefault] = useState(false);

  // Load saved layouts from localStorage
  useEffect(() => {
    const layouts = localStorage.getItem('observability_layouts');
    if (layouts) {
      setSavedLayouts(JSON.parse(layouts));
    }
  }, []);

  // Save layout
  const handleSave = () => {
    if (!layoutName.trim()) return;

    const newLayout: SavedLayout = {
      id: `layout_${Date.now()}`,
      name: layoutName,
      cols: currentLayout.cols,
      rows: currentLayout.rows,
      panels: currentLayout.panels,
      visibleAgents: currentLayout.visibleAgents,
      createdAt: new Date(),
      isDefault: setAsDefault,
    };

    const updatedLayouts = [...savedLayouts];

    // Remove default flag from others if setting this as default
    if (setAsDefault) {
      updatedLayouts.forEach(l => l.isDefault = false);
    }

    updatedLayouts.push(newLayout);

    setSavedLayouts(updatedLayouts);
    localStorage.setItem('observability_layouts', JSON.stringify(updatedLayouts));

    if (onSaveLayout) {
      onSaveLayout(newLayout);
    }

    setShowSaveDialog(false);
    setLayoutName('');
    setSetAsDefault(false);
  };

  // Delete layout
  const handleDelete = (layoutId: string) => {
    const updatedLayouts = savedLayouts.filter(l => l.id !== layoutId);
    setSavedLayouts(updatedLayouts);
    localStorage.setItem('observability_layouts', JSON.stringify(updatedLayouts));
  };

  // Set default layout
  const handleSetDefault = (layoutId: string) => {
    const updatedLayouts = savedLayouts.map(l => ({
      ...l,
      isDefault: l.id === layoutId,
    }));
    setSavedLayouts(updatedLayouts);
    localStorage.setItem('observability_layouts', JSON.stringify(updatedLayouts));
  };

  return (
    <>
      {/* Layout Management Bar */}
      <div className="flex items-center space-x-2 bg-white px-4 py-2 border-b">
        <Layout className="w-4 h-4 text-gray-600" />
        <span className="text-sm font-medium text-gray-700">Layouts:</span>

        {/* Quick Layout Buttons */}
        <div className="flex items-center space-x-1">
          {savedLayouts.slice(0, 3).map((layout) => (
            <button
              key={layout.id}
              onClick={() => onLoadLayout(layout)}
              className={`px-3 py-1 text-xs rounded transition-colors ${
                layout.isDefault
                  ? 'bg-blue-100 text-blue-700 hover:bg-blue-200'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
              title={`Load ${layout.name}${layout.isDefault ? ' (Default)' : ''}`}
            >
              {layout.isDefault && <Star className="w-3 h-3 inline mr-1" />}
              {layout.name}
            </button>
          ))}
        </div>

        {/* Action Buttons */}
        <div className="flex items-center space-x-2 ml-auto">
          <button
            onClick={() => setShowSaveDialog(true)}
            className="px-3 py-1 text-xs bg-green-100 text-green-700 hover:bg-green-200 rounded transition-colors flex items-center"
          >
            <Save className="w-3 h-3 mr-1" />
            Save Layout
          </button>

          <button
            onClick={() => setShowLoadDialog(true)}
            className="px-3 py-1 text-xs bg-blue-100 text-blue-700 hover:bg-blue-200 rounded transition-colors flex items-center"
            disabled={savedLayouts.length === 0}
          >
            <FolderOpen className="w-3 h-3 mr-1" />
            Load Layout ({savedLayouts.length})
          </button>
        </div>
      </div>

      {/* Save Layout Dialog */}
      <AnimatePresence>
        {showSaveDialog && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 bg-black bg-opacity-50 z-50"
              onClick={() => setShowSaveDialog(false)}
            />

            <motion.div
              initial={{ opacity: 0, scale: 0.9, y: -20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.9, y: -20 }}
              className="fixed left-1/2 top-1/2 transform -translate-x-1/2 -translate-y-1/2 bg-white rounded-lg shadow-xl z-50 w-96"
            >
              <div className="px-6 py-4 border-b">
                <h2 className="text-lg font-semibold text-gray-800 flex items-center">
                  <Save className="w-5 h-5 mr-2 text-green-600" />
                  Save Layout
                </h2>
              </div>

              <div className="px-6 py-4">
                <div className="space-y-4">
                  <div>
                    <label htmlFor="layout-name" className="block text-sm font-medium text-gray-700 mb-1">
                      Layout Name
                    </label>
                    <input
                      id="layout-name"
                      type="text"
                      value={layoutName}
                      onChange={(e) => setLayoutName(e.target.value)}
                      placeholder="e.g., Debug View, Production Monitor"
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      autoFocus
                    />
                  </div>

                  <div className="flex items-center">
                    <input
                      id="set-default"
                      type="checkbox"
                      checked={setAsDefault}
                      onChange={(e) => setSetAsDefault(e.target.checked)}
                      className="mr-2"
                    />
                    <label htmlFor="set-default" className="text-sm text-gray-700">
                      Set as default layout
                    </label>
                  </div>

                  <div className="bg-gray-50 rounded p-3 text-xs text-gray-600">
                    <p>This layout includes:</p>
                    <ul className="mt-1 space-y-0.5">
                      <li>• {currentLayout.cols}×{currentLayout.rows} grid configuration</li>
                      <li>• {currentLayout.visibleAgents.length} selected agents</li>
                      <li>• Current panel positions</li>
                    </ul>
                  </div>
                </div>
              </div>

              <div className="flex justify-end space-x-3 px-6 py-4 bg-gray-50 rounded-b-lg">
                <button
                  onClick={() => {
                    setShowSaveDialog(false);
                    setLayoutName('');
                    setSetAsDefault(false);
                  }}
                  className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={handleSave}
                  disabled={!layoutName.trim()}
                  className="px-4 py-2 text-sm font-medium text-white bg-green-600 rounded-lg hover:bg-green-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Save Layout
                </button>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>

      {/* Load Layout Dialog */}
      <AnimatePresence>
        {showLoadDialog && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 bg-black bg-opacity-50 z-50"
              onClick={() => setShowLoadDialog(false)}
            />

            <motion.div
              initial={{ opacity: 0, scale: 0.9, y: -20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.9, y: -20 }}
              className="fixed left-1/2 top-1/2 transform -translate-x-1/2 -translate-y-1/2 bg-white rounded-lg shadow-xl z-50 w-[500px] max-h-[600px]"
            >
              <div className="px-6 py-4 border-b">
                <h2 className="text-lg font-semibold text-gray-800 flex items-center">
                  <FolderOpen className="w-5 h-5 mr-2 text-blue-600" />
                  Load Layout
                </h2>
              </div>

              <div className="px-6 py-4 max-h-[400px] overflow-y-auto">
                {savedLayouts.length === 0 ? (
                  <p className="text-gray-500 text-center py-8">No saved layouts yet</p>
                ) : (
                  <div className="space-y-2">
                    {savedLayouts.map((layout) => (
                      <div
                        key={layout.id}
                        className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
                      >
                        <div className="flex-1">
                          <div className="flex items-center">
                            <h3 className="font-medium text-gray-800">
                              {layout.name}
                            </h3>
                            {layout.isDefault && (
                              <span className="ml-2 px-2 py-0.5 text-xs bg-blue-100 text-blue-700 rounded">
                                Default
                              </span>
                            )}
                          </div>
                          <div className="text-xs text-gray-500 mt-1">
                            {layout.cols}×{layout.rows} grid • {layout.visibleAgents.length} agents •
                            Created {new Date(layout.createdAt).toLocaleDateString()}
                          </div>
                        </div>

                        <div className="flex items-center space-x-2">
                          <button
                            onClick={() => {
                              onLoadLayout(layout);
                              setShowLoadDialog(false);
                            }}
                            className="px-3 py-1 text-xs bg-blue-100 text-blue-700 hover:bg-blue-200 rounded transition-colors"
                          >
                            Load
                          </button>

                          <button
                            onClick={() => handleSetDefault(layout.id)}
                            className={`p-1 rounded transition-colors ${
                              layout.isDefault
                                ? 'text-yellow-600 bg-yellow-100'
                                : 'text-gray-400 hover:text-yellow-600 hover:bg-yellow-100'
                            }`}
                            title={layout.isDefault ? 'Default layout' : 'Set as default'}
                          >
                            <Star className="w-4 h-4" />
                          </button>

                          <button
                            onClick={() => handleDelete(layout.id)}
                            className="p-1 text-red-400 hover:text-red-600 hover:bg-red-100 rounded transition-colors"
                            title="Delete layout"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              <div className="flex justify-end px-6 py-4 bg-gray-50 rounded-b-lg">
                <button
                  onClick={() => setShowLoadDialog(false)}
                  className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
                >
                  Close
                </button>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </>
  );
};

export default LayoutManager;