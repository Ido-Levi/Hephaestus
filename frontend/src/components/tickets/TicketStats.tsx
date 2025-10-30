import React from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import { Loader2, AlertCircle, TrendingUp, CheckCircle, Lock, Ticket } from 'lucide-react';
import { apiService } from '@/services/api';
import { cn } from '@/lib/utils';

interface TicketStatsProps {
  workflowId: string;
}

const COLORS = {
  status: ['#9ca3af', '#6b7280', '#3b82f6', '#f59e0b', '#10b981'],
  type: ['#ef4444', '#f59e0b', '#3b82f6', '#10b981', '#8b5cf6', '#6b7280'],
  priority: ['#dc2626', '#ea580c', '#eab308', '#6b7280'],
};

const TicketStats: React.FC<TicketStatsProps> = ({ workflowId }) => {
  const { data: stats, isLoading, error } = useQuery({
    queryKey: ['ticketStats', workflowId],
    queryFn: () => apiService.getTicketStats(workflowId),
    enabled: !!workflowId,
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 text-blue-600 animate-spin" />
      </div>
    );
  }

  if (error || !stats) {
    return (
      <div className="flex flex-col items-center justify-center h-64 text-gray-500">
        <AlertCircle className="w-12 h-12 mb-4 text-red-500" />
        <p>Failed to load statistics</p>
      </div>
    );
  }

  // Prepare data for charts
  const statusData = Object.entries(stats.by_status).map(([name, value]) => ({
    name: name.replace('_', ' '),
    value,
  }));

  const typeData = Object.entries(stats.by_type).map(([name, value]) => ({
    name,
    value,
  }));

  const priorityData = Object.entries(stats.by_priority).map(([name, value]) => ({
    name,
    value,
  }));

  const agentData = Object.entries(stats.by_agent)
    .map(([name, value]) => ({
      name: name.split('-')[0] || name,
      value,
    }))
    .slice(0, 10); // Top 10 agents

  return (
    <div className="space-y-6">
      {/* Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white rounded-lg border shadow-sm p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 mb-1">Total Tickets</p>
              <p className="text-3xl font-bold text-gray-900">{stats.total_tickets}</p>
            </div>
            <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
              <Ticket className="w-6 h-6 text-blue-600" />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg border shadow-sm p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 mb-1">Resolved</p>
              <p className="text-3xl font-bold text-green-600">{stats.resolved_count}</p>
            </div>
            <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
              <CheckCircle className="w-6 h-6 text-green-600" />
            </div>
          </div>
        </div>

        <div className={cn(
          "bg-white rounded-lg border shadow-sm p-6",
          stats.blocked_count > 0 && "border-red-200 bg-red-50"
        )}>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 mb-1">Blocked</p>
              <p className={cn(
                "text-3xl font-bold",
                stats.blocked_count > 0 ? "text-red-600" : "text-gray-900"
              )}>
                {stats.blocked_count}
              </p>
            </div>
            <div className={cn(
              "w-12 h-12 rounded-lg flex items-center justify-center",
              stats.blocked_count > 0 ? "bg-red-200" : "bg-gray-100"
            )}>
              <Lock className={cn(
                "w-6 h-6",
                stats.blocked_count > 0 ? "text-red-600" : "text-gray-400"
              )} />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg border shadow-sm p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 mb-1">7-Day Velocity</p>
              <p className="text-3xl font-bold text-purple-600">{stats.velocity_last_7_days}</p>
              <p className="text-xs text-gray-500 mt-1">tickets completed</p>
            </div>
            <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center">
              <TrendingUp className="w-6 h-6 text-purple-600" />
            </div>
          </div>
        </div>
      </div>

      {/* Today's Activity */}
      <div className="bg-white rounded-lg border shadow-sm p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Today's Activity</h3>
        <div className="grid grid-cols-2 gap-4">
          <div className="p-4 bg-green-50 rounded-lg border border-green-200">
            <p className="text-sm text-green-700 mb-1">Created Today</p>
            <p className="text-2xl font-bold text-green-600">{stats.created_today}</p>
          </div>
          <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
            <p className="text-sm text-blue-700 mb-1">Completed Today</p>
            <p className="text-2xl font-bold text-blue-600">{stats.completed_today}</p>
          </div>
        </div>
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Tickets by Status */}
        <div className="bg-white rounded-lg border shadow-sm p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Tickets by Status</h3>
          {statusData.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={statusData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" tick={{ fontSize: 12 }} />
                <YAxis />
                <Tooltip />
                <Bar dataKey="value" fill="#3b82f6">
                  {statusData.map((_entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS.status[index % COLORS.status.length]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-64 flex items-center justify-center text-gray-400">
              No data
            </div>
          )}
        </div>

        {/* Tickets by Type */}
        <div className="bg-white rounded-lg border shadow-sm p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Tickets by Type</h3>
          {typeData.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={typeData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }: any) => `${name} ${(percent * 100).toFixed(0)}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {typeData.map((_entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS.type[index % COLORS.type.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-64 flex items-center justify-center text-gray-400">
              No data
            </div>
          )}
        </div>

        {/* Tickets by Priority */}
        <div className="bg-white rounded-lg border shadow-sm p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Tickets by Priority</h3>
          {priorityData.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={priorityData} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis type="number" />
                <YAxis dataKey="name" type="category" tick={{ fontSize: 12 }} />
                <Tooltip />
                <Bar dataKey="value" fill="#8b5cf6">
                  {priorityData.map((_entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS.priority[index % COLORS.priority.length]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-64 flex items-center justify-center text-gray-400">
              No data
            </div>
          )}
        </div>

        {/* Agent Workload */}
        <div className="bg-white rounded-lg border shadow-sm p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Agent Workload (Top 10)</h3>
          {agentData.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={agentData} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis type="number" />
                <YAxis dataKey="name" type="category" width={80} tick={{ fontSize: 10 }} />
                <Tooltip />
                <Bar dataKey="value" fill="#10b981" />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-64 flex items-center justify-center text-gray-400">
              No data
            </div>
          )}
        </div>
      </div>

      {/* Board Configuration */}
      <div className="bg-white rounded-lg border shadow-sm p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Board Configuration</h3>
        <div className="space-y-3">
          <div>
            <span className="text-sm text-gray-600">Board Name:</span>
            <span className="ml-2 font-medium">{stats.board_config.name}</span>
          </div>
          <div>
            <span className="text-sm text-gray-600">Columns:</span>
            <div className="flex flex-wrap gap-2 mt-2">
              {stats.board_config.columns
                .sort((a, b) => a.order - b.order)
                .map((column) => (
                  <span
                    key={column.id}
                    className="px-3 py-1 rounded-full text-sm font-medium"
                    style={{
                      backgroundColor: `${column.color}20`,
                      color: column.color,
                      border: `1px solid ${column.color}`,
                    }}
                  >
                    {column.name}
                  </span>
                ))}
            </div>
          </div>
          <div>
            <span className="text-sm text-gray-600">Settings:</span>
            <div className="flex flex-wrap gap-4 mt-2 text-sm">
              <span className="flex items-center">
                Auto-assign: {stats.board_config.auto_assign ? '✓' : '✗'}
              </span>
              <span className="flex items-center">
                Allow reopen: {stats.board_config.allow_reopen ? '✓' : '✗'}
              </span>
              <span className="flex items-center">
                Track time: {stats.board_config.track_time ? '✓' : '✗'}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TicketStats;
