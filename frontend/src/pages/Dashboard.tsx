import React, { useEffect, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import { Bot, FileText, Database, AlertCircle, TrendingUp, Clock, Ban } from 'lucide-react';
import { apiService } from '@/services/api';
import { DashboardStats } from '@/types';
import { useWebSocket } from '@/context/WebSocketContext';
import { formatDistanceToNow } from 'date-fns';
import QueueStatusWidget from '@/components/QueueStatusWidget';
import BlockedTasksView from '@/components/BlockedTasksView';

const StatCard: React.FC<{
  title: string;
  value: number;
  icon: React.ElementType;
  color: string;
  trend?: number;
}> = ({ title, value, icon: Icon, color, trend }) => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-white rounded-lg shadow-md p-6"
    >
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-gray-600">{title}</p>
          <motion.p
            key={value}
            initial={{ scale: 0.8 }}
            animate={{ scale: 1 }}
            className="text-3xl font-bold text-gray-800 mt-2"
          >
            {value}
          </motion.p>
          {trend !== undefined && (
            <div className="flex items-center mt-2">
              <TrendingUp className={`w-4 h-4 ${trend > 0 ? 'text-green-500' : 'text-red-500'}`} />
              <span className={`text-sm ml-1 ${trend > 0 ? 'text-green-500' : 'text-red-500'}`}>
                {trend > 0 ? '+' : ''}{trend}
              </span>
            </div>
          )}
        </div>
        <div className={`p-3 rounded-full ${color}`}>
          <Icon className="w-6 h-6 text-white" />
        </div>
      </div>
    </motion.div>
  );
};

const ActivityItem: React.FC<{ activity: any; isNew?: boolean }> = ({ activity, isNew }) => {
  return (
    <motion.div
      initial={isNew ? { opacity: 0, x: -20 } : false}
      animate={{ opacity: 1, x: 0 }}
      className={`flex items-center p-3 ${isNew ? 'bg-blue-50' : ''} hover:bg-gray-50 transition-colors`}
    >
      <div className="flex-1">
        <p className="text-sm text-gray-800">{activity.message}</p>
        <p className="text-xs text-gray-500 mt-1">
          {formatDistanceToNow(new Date(activity.timestamp), { addSuffix: true })}
        </p>
      </div>
    </motion.div>
  );
};

const Dashboard: React.FC = () => {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [recentActivities, setRecentActivities] = useState<any[]>([]);
  const { subscribe } = useWebSocket();

  const { data, isLoading, error } = useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: apiService.getDashboardStats,
    refetchInterval: 5000, // Refresh every 5 seconds
  });

  const { data: blockedTasks } = useQuery({
    queryKey: ['blocked-tasks'],
    queryFn: apiService.getBlockedTasks,
    refetchInterval: 5000, // Refresh every 5 seconds
  });

  useEffect(() => {
    if (data) {
      setStats(data);
      setRecentActivities(data.recent_activity);
    }
  }, [data]);

  // Subscribe to WebSocket updates
  useEffect(() => {
    const unsubscribe = subscribe('stats_update', (message) => {
      if (stats) {
        setStats({
          ...stats,
          active_agents: message.active_agents ?? stats.active_agents,
          running_tasks: message.running_tasks ?? stats.running_tasks,
          total_memories: message.total_memories ?? stats.total_memories,
        });
      }
    });

    return unsubscribe;
  }, [subscribe, stats]);

  useEffect(() => {
    const unsubscribeTask = subscribe('task_created', (message) => {
      const newActivity = {
        id: Date.now(),
        type: 'task_created',
        message: `New task created: ${message.description?.substring(0, 50)}...`,
        timestamp: new Date().toISOString(),
        agent_id: message.agent_id,
      };
      setRecentActivities(prev => [newActivity, ...prev.slice(0, 9)]);
    });

    const unsubscribeAgent = subscribe('agent_created', (message) => {
      const newActivity = {
        id: Date.now(),
        type: 'agent_created',
        message: `Agent ${message.agent_id?.substring(0, 8)} spawned`,
        timestamp: new Date().toISOString(),
        agent_id: message.agent_id,
      };
      setRecentActivities(prev => [newActivity, ...prev.slice(0, 9)]);
    });

    return () => {
      unsubscribeTask();
      unsubscribeAgent();
    };
  }, [subscribe]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6">
        <p className="text-red-600">Failed to load dashboard stats</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-800">Dashboard</h1>
        <p className="text-gray-600 mt-1">Real-time system overview</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-6 gap-6">
        <StatCard
          title="Active Agents"
          value={stats?.active_agents || 0}
          icon={Bot}
          color="bg-blue-500"
        />
        <StatCard
          title="Running Tasks"
          value={stats?.running_tasks || 0}
          icon={FileText}
          color="bg-green-500"
        />
        <StatCard
          title="Queued Tasks"
          value={stats?.queued_tasks || 0}
          icon={Clock}
          color="bg-orange-500"
        />
        <StatCard
          title="Blocked Tasks"
          value={blockedTasks?.length || 0}
          icon={Ban}
          color="bg-red-500"
        />
        <StatCard
          title="Total Memories"
          value={stats?.total_memories || 0}
          icon={Database}
          color="bg-purple-500"
        />
        <StatCard
          title="Stuck Agents"
          value={stats?.stuck_agents || 0}
          icon={AlertCircle}
          color="bg-yellow-500"
        />
      </div>

      {/* Queue Status */}
      <QueueStatusWidget />

      {/* Blocked Tasks */}
      {blockedTasks && blockedTasks.length > 0 && (
        <div>
          <BlockedTasksView />
        </div>
      )}

      {/* Recent Activity */}
      <div className="bg-white rounded-lg shadow-md">
        <div className="px-6 py-4 border-b flex items-center justify-between">
          <h2 className="text-lg font-semibold text-gray-800">Recent Activity</h2>
          <div className="flex items-center text-sm text-gray-500">
            <Clock className="w-4 h-4 mr-1" />
            Live Updates
          </div>
        </div>
        <div className="divide-y">
          {recentActivities.length > 0 ? (
            recentActivities.map((activity, index) => (
              <ActivityItem
                key={activity.id}
                activity={activity}
                isNew={index === 0}
              />
            ))
          ) : (
            <div className="p-6 text-center text-gray-500">
              No recent activity
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Dashboard;