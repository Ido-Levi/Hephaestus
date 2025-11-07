import React, { useState, useEffect } from 'react';
import { NavLink, Outlet } from 'react-router-dom';
import { Home, FileText, Bot, Database, GitBranch, Activity, Layers, Monitor, Compass, ListChecks, Menu, ChevronLeft, Ticket, Settings } from 'lucide-react';
import { useWebSocket } from '@/context/WebSocketContext';
import { format } from 'date-fns';
import { motion, AnimatePresence } from 'framer-motion';

const Layout: React.FC = () => {
  const { isConnected, lastUpdate } = useWebSocket();
  const [sidebarCollapsed, setSidebarCollapsed] = useState(() => {
    const saved = localStorage.getItem('sidebarCollapsed');
    return saved === 'true';
  });

  // Save sidebar state to localStorage
  useEffect(() => {
    localStorage.setItem('sidebarCollapsed', sidebarCollapsed.toString());
  }, [sidebarCollapsed]);

  // Keyboard shortcut for sidebar toggle (Cmd+B or Ctrl+B)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'b') {
        e.preventDefault();
        setSidebarCollapsed(prev => !prev);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

    const navItems = [
      { to: '/', icon: Home, label: 'Dashboard' },
      { to: '/overview', icon: Compass, label: 'Overview' },
      { to: '/tasks', icon: FileText, label: 'Tasks' },
      { to: '/tickets', icon: Ticket, label: 'Tickets' },
      { to: '/results', icon: ListChecks, label: 'Results' },
      { to: '/agents', icon: Bot, label: 'Agents' },
      { to: '/phases', icon: Layers, label: 'Phases' },
      { to: '/memories', icon: Database, label: 'Memories' },
      { to: '/graph', icon: GitBranch, label: 'Graph' },
      { to: '/observability', icon: Monitor, label: 'Observability' },
      // New config page
      { to: '/config', icon: Settings, label: 'Config' },
    ];

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar */}
      <AnimatePresence mode="wait">
        <motion.div
          initial={false}
          animate={{ width: sidebarCollapsed ? 64 : 256 }}
          transition={{ duration: 0.2, ease: 'easeInOut' }}
          className="bg-white shadow-lg flex flex-col relative"
        >
          {/* Toggle Button */}
          <button
            onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
            className="absolute -right-3 top-8 z-10 bg-white rounded-full p-1.5 shadow-md hover:shadow-lg transition-shadow border border-gray-200"
            title={`${sidebarCollapsed ? 'Expand' : 'Collapse'} sidebar (⌘B)`}
          >
            {sidebarCollapsed ? (
              <Menu className="w-4 h-4 text-gray-600" />
            ) : (
              <ChevronLeft className="w-4 h-4 text-gray-600" />
            )}
          </button>

          <div className={`${sidebarCollapsed ? 'p-4' : 'p-6'} transition-all`}>
            {sidebarCollapsed ? (
              <h1 className="text-xl font-bold text-gray-800 text-center">H</h1>
            ) : (
              <>
                <h1 className="text-2xl font-bold text-gray-800">Hephaestus</h1>
                <p className="text-sm text-gray-600 mt-1">AI Agent Orchestration</p>
              </>
            )}
          </div>

          <nav className="mt-8 flex-1">
            {navItems.map(({ to, icon: Icon, label }) => (
              <NavLink
                key={to}
                to={to}
                className={({ isActive }) =>
                  `flex items-center ${sidebarCollapsed ? 'px-4 justify-center' : 'px-6'} py-3 text-gray-700 hover:bg-gray-100 transition-colors ${
                    isActive ? 'bg-blue-50 border-r-4 border-blue-500 text-blue-600' : ''
                  }`
                }
                title={sidebarCollapsed ? label : undefined}
              >
                <Icon className={`w-5 h-5 ${sidebarCollapsed ? '' : 'mr-3'}`} />
                {!sidebarCollapsed && label}
              </NavLink>
            ))}
          </nav>

          {/* Connection Status */}
          <div className={`${sidebarCollapsed ? 'p-3' : 'p-6'} border-t mt-auto`}>
            <div className={`flex ${sidebarCollapsed ? 'justify-center' : 'items-center'}`}>
              <div
                className={`w-2 h-2 rounded-full ${sidebarCollapsed ? '' : 'mr-2'} ${isConnected ? 'bg-green-500' : 'bg-red-500'}`}
                title={sidebarCollapsed ? (isConnected ? 'Connected' : 'Disconnected') : undefined}
              />
              {!sidebarCollapsed && (
                <span className="text-sm text-gray-600">
                  {isConnected ? 'Connected' : 'Disconnected'}
                </span>
              )}
            </div>
            {isConnected && !sidebarCollapsed && (
              <p className="text-xs text-gray-500 mt-1">
                Last update: {format(lastUpdate, 'HH:mm:ss')}
              </p>
            )}
          </div>
        </motion.div>
      </AnimatePresence>

      {/* Main Content */}
      <div className="flex-1 overflow-auto">
          <header className="bg-white shadow-sm border-b">
            <div className="px-8 py-4 flex items-center justify-between">
              <div className="flex items-center">
                <Activity className="w-5 h-5 mr-2 text-gray-600" />
                <span className="text-gray-800 font-medium">System Overview</span>
              </div>
              <div className="flex items-center space-x-2">
                {isConnected && (
                  <span className="text-xs text-green-600 bg-green-50 px-2 py-1 rounded">
                    Live
                  </span>
                )}
                {/* Config page link */}
                <a href="/config" className="text-gray-600 hover:text-gray-800">
                  <Settings className="w-5 h-5" />
                </a>
              </div>
            </div>
          </header>

        <main className="p-8">
          <Outlet />
        </main>
      </div>
    </div>
  );
};

export default Layout;
