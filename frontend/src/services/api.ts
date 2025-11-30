import axios from 'axios';
import {
  Agent,
  Task,
  Memory,
  DashboardStats,
  GraphData,
  ResultSummary,
  ResultContentResponse,
  ResultValidationDetail,
  ExtraFileContentResponse,
  TicketDetail,
  TicketComment,
  TicketHistory,
  TicketCommit,
  TicketStats,
  CommitDiff,
  TicketSearchResult,
  BlockedTask,
  WorkflowDefinition,
  WorkflowExecution,
} from '@/types';

interface ResultQueryParams {
  scope?: 'all' | 'workflow' | 'task';
  status?: string;
  workflow_id?: string;
  agent_id?: string;
  search?: string;
  date_from?: string;
  date_to?: string;
  limit?: number;
  offset?: number;
}

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

export const apiService = {
  // Workflow Definitions and Executions
  listWorkflowDefinitions: async (): Promise<WorkflowDefinition[]> => {
    const { data } = await api.get('/workflow-definitions');
    return data.definitions || [];
  },

  listWorkflowExecutions: async (status: string = 'all'): Promise<WorkflowExecution[]> => {
    const { data } = await api.get(`/workflow-executions?status=${status}`);
    return data.executions || [];
  },

  startWorkflowExecution: async (
    definitionId: string,
    description: string,
    workingDirectory?: string,
    launchParams?: Record<string, any>
  ): Promise<{ workflow_id: string }> => {
    const { data } = await api.post('/workflow-executions', {
      definition_id: definitionId,
      description,
      working_directory: workingDirectory,
      launch_params: launchParams,
    });
    return data;
  },

  getWorkflowExecution: async (workflowId: string): Promise<WorkflowExecution & { phases: any[] }> => {
    const { data } = await api.get(`/workflow-executions/${workflowId}`);
    return data;
  },

  // Dashboard
  getDashboardStats: async (workflowId?: string): Promise<DashboardStats> => {
    const params = workflowId ? `?workflow_id=${workflowId}` : '';
    const { data } = await api.get(`/dashboard/stats${params}`);
    return data;
  },

  // Tasks
  getTasks: async (skip = 0, limit = 50, status?: string, workflowId?: string): Promise<Task[]> => {
    const params = new URLSearchParams();
    params.append('skip', skip.toString());
    params.append('limit', limit.toString());
    if (status) params.append('status', status);
    if (workflowId) params.append('workflow_id', workflowId);

    const { data } = await api.get(`/tasks?${params}`);
    return data;
  },

  // Agents
  getAgents: async (): Promise<Agent[]> => {
    const { data } = await api.get('/agents');
    return data;
  },

  getAgentOutput: async (agentId: string, lines = 2000): Promise<{ output: string; timestamp: string }> => {
    const { data } = await api.get(`/agents/${agentId}/output?lines=${lines}`);
    return data;
  },

  // Memories
  getMemories: async (skip = 0, limit = 50, memoryType?: string, search?: string): Promise<{ memories: Memory[]; total: number; type_counts: Record<string, number> }> => {
    const params = new URLSearchParams();
    params.append('skip', skip.toString());
    params.append('limit', limit.toString());
    if (memoryType) params.append('memory_type', memoryType);
    if (search) params.append('search', search);

    const { data } = await api.get(`/memories?${params}`);
    return data;
  },

  // Graph
  getGraphData: async (workflowId?: string): Promise<GraphData> => {
    const params = workflowId ? `?workflow_id=${workflowId}` : '';
    const { data } = await api.get(`/graph${params}`);
    return data;
  },

  // Task Full Details
  getTaskFullDetails: async (taskId: string): Promise<any> => {
    const { data } = await api.get(`/tasks/${taskId}/full-details`);
    return data;
  },

  // Get single task by ID
  getTaskById: async (taskId: string): Promise<Task> => {
    const { data } = await api.get(`/tasks/${taskId}`);
    return data;
  },

  // Guardian Analyses
  getGuardianAnalyses: async (agentId: string, limit = 50): Promise<any[]> => {
    const { data } = await api.get(`/guardian-analyses/${agentId}?limit=${limit}`);
    return data;
  },

  // Conductor Analyses
  getConductorAnalyses: async (limit = 20): Promise<any[]> => {
    const { data } = await api.get(`/conductor-analyses?limit=${limit}`);
    return data;
  },

  getLatestConductorAnalysis: async (): Promise<any | null> => {
    const { data } = await api.get('/conductor-analyses/latest');
    return data;
  },

  // Steering Interventions
  getSteeringInterventions: async (agentId?: string, limit = 50): Promise<any[]> => {
    const params = new URLSearchParams();
    params.append('limit', limit.toString());
    if (agentId) params.append('agent_id', agentId);

    const { data } = await api.get(`/steering-interventions?${params}`);
    return data;
  },

  // System Overview
  getSystemOverview: async (): Promise<any> => {
    const { data } = await api.get('/system-overview');
    return data;
  },

  // Results
  getResults: async (params: ResultQueryParams = {}): Promise<ResultSummary[]> => {
    try {
      const searchParams = new URLSearchParams();
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null && value !== '') {
          searchParams.append(key, String(value));
        }
      });
      const query = searchParams.toString();
      const { data } = await api.get(`/results${query ? `?${query}` : ''}`);
      return data;
    } catch (error) {
      if (axios.isAxiosError(error) && error.response?.status === 404) {
        return [];
      }
      throw error;
    }
  },

  getResultContent: async (resultId: string): Promise<ResultContentResponse | null> => {
    try {
      const { data } = await api.get(`/results/${resultId}/content`);
      return data;
    } catch (error) {
      if (axios.isAxiosError(error) && error.response?.status === 404) {
        return null;
      }
      throw error;
    }
  },

  getResultValidation: async (resultId: string): Promise<ResultValidationDetail | null> => {
    try {
      const { data } = await api.get(`/results/${resultId}/validation`);
      return data;
    } catch (error) {
      if (axios.isAxiosError(error) && error.response?.status === 404) {
        return null;
      }
      throw error;
    }
  },

  getExtraFileContent: async (resultId: string, fileIndex: number): Promise<ExtraFileContentResponse | null> => {
    try {
      const { data } = await api.get(`/results/${resultId}/extra-files/${fileIndex}`);
      return data;
    } catch (error) {
      if (axios.isAxiosError(error) && error.response?.status === 404) {
        return null;
      }
      throw error;
    }
  },

  // Agent Communication
  broadcastMessage: async (message: string, senderAgentId: string = 'ui-user'): Promise<{ success: boolean; recipient_count: number; message: string }> => {
    const { data } = await api.post(
      '/broadcast_message',
      { message },
      {
        headers: {
          'X-Agent-ID': senderAgentId,
        },
      }
    );
    return data;
  },

  sendMessage: async (
    message: string,
    recipientAgentId: string,
    senderAgentId: string = 'ui-user'
  ): Promise<{ success: boolean; message: string }> => {
    const { data } = await api.post(
      '/send_message',
      {
        recipient_agent_id: recipientAgentId,
        message,
      },
      {
        headers: {
          'X-Agent-ID': senderAgentId,
        },
      }
    );
    return data;
  },

  // Queue management endpoints
  getQueueStatus: async (workflowId?: string): Promise<{
    active_agents: number;
    max_concurrent_agents: number;
    queued_tasks_count: number;
    queued_tasks: Array<{
      task_id: string;
      description: string;
      priority: string;
      priority_boosted: boolean;
      queue_position: number;
      queued_at: string | null;
      phase_id: string | null;
    }>;
    slots_available: number;
    at_capacity: boolean;
  }> => {
    const params = workflowId ? `?workflow_id=${workflowId}` : '';
    const { data } = await api.get(`/queue_status${params}`);
    return data;
  },

  terminateAgent: async (
    agentId: string,
    reason: string = 'Manual termination from UI'
  ): Promise<{ success: boolean; message: string }> => {
    const { data } = await api.post('/terminate_agent', {
      agent_id: agentId,
      reason,
    });
    return data;
  },

  bumpTaskPriority: async (
    taskId: string
  ): Promise<{ success: boolean; message: string; agent_id: string }> => {
    const { data } = await api.post('/bump_task_priority', {
      task_id: taskId,
    });
    return data;
  },

  cancelQueuedTask: async (
    taskId: string
  ): Promise<{ success: boolean; message: string }> => {
    const { data } = await api.post('/cancel_queued_task', {
      task_id: taskId,
    });
    return data;
  },

  restartTask: async (
    taskId: string
  ): Promise<{ success: boolean; message: string; agent_id?: string; status: string }> => {
    const { data } = await api.post('/restart_task', {
      task_id: taskId,
    });
    return data;
  },

  // Ticket Tracking System Endpoints

  createTicket: async (
    ticketData: {
      workflow_id: string;
      title: string;
      description: string;
      ticket_type?: string;
      priority?: string;
      assigned_agent_id?: string;
      parent_ticket_id?: string;
      tags?: string[];
    },
    agentId: string = 'ui-user'
  ): Promise<{ ticket_id: string; status: string }> => {
    const { data } = await api.post('/tickets/create', ticketData, {
      headers: { 'X-Agent-ID': agentId },
    });
    return data;
  },

  updateTicket: async (
    ticketId: string,
    updates: {
      title?: string;
      description?: string;
      priority?: string;
      assigned_agent_id?: string;
      tags?: string[];
    },
    agentId: string = 'ui-user'
  ): Promise<{ success: boolean; message: string }> => {
    const { data } = await api.post('/tickets/update', { ticket_id: ticketId, ...updates }, {
      headers: { 'X-Agent-ID': agentId },
    });
    return data;
  },

  changeTicketStatus: async (
    ticketId: string,
    newStatus: string,
    comment?: string,
    agentId: string = 'ui-user'
  ): Promise<{ success: boolean; message: string }> => {
    const { data } = await api.post('/tickets/change-status', {
      ticket_id: ticketId,
      new_status: newStatus,
      comment,
    }, {
      headers: { 'X-Agent-ID': agentId },
    });
    return data;
  },

  addTicketComment: async (
    ticketId: string,
    commentText: string,
    commentType: string = 'general',
    agentId: string = 'ui-user'
  ): Promise<{ comment_id: string }> => {
    const { data } = await api.post('/tickets/comment', {
      ticket_id: ticketId,
      comment_text: commentText,
      comment_type: commentType,
    }, {
      headers: { 'X-Agent-ID': agentId },
    });
    return data;
  },

  getTicket: async (ticketId: string): Promise<{
    ticket: TicketDetail;
    comments: TicketComment[];
    history: TicketHistory[];
    commits: TicketCommit[];
  }> => {
    const { data } = await api.get(`/tickets/${ticketId}`, {
      headers: { 'X-Agent-ID': 'ui-user' },
    });
    return data;
  },

  getTickets: async (params?: {
    workflow_id?: string;
    status?: string;
    assigned_agent_id?: string;
    is_blocked?: boolean;
    limit?: number;
    offset?: number;
  }): Promise<TicketDetail[]> => {
    const searchParams = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          searchParams.append(key, String(value));
        }
      });
    }
    const query = searchParams.toString();
    const { data } = await api.get(`/tickets${query ? `?${query}` : ''}`, {
      headers: { 'X-Agent-ID': 'ui-user' },
    });
    return data.tickets || [];
  },

  searchTickets: async (params: {
    workflow_id?: string;
    query: string;
    search_type?: 'semantic' | 'keyword' | 'hybrid';
    filters?: {
      status?: string[];
      ticket_type?: string[];
      priority?: string[];
      assigned_agent_id?: string[];
      is_blocked?: boolean;
      is_resolved?: boolean;
      tags?: string[];
    };
    limit?: number;
  }): Promise<TicketSearchResult[]> => {
    const { data } = await api.post('/tickets/search', params, {
      headers: { 'X-Agent-ID': 'ui-user' },
    });
    // Backend returns {success, query, results, total_found, search_time_ms}
    // Frontend expects just the results array
    return data.results || [];
  },

  getTicketStats: async (workflowId: string): Promise<TicketStats> => {
    const { data } = await api.get(`/tickets/stats/${workflowId}`, {
      headers: { 'X-Agent-ID': 'ui-user' },
    });
    // Backend returns {success, workflow_id, stats, board_config}
    // Frontend expects stats merged with board_config
    return {
      ...data.stats,
      board_config: data.board_config,
    };
  },

  resolveTicket: async (
    ticketId: string,
    resolution: string,
    agentId: string = 'ui-user'
  ): Promise<{ success: boolean; message: string }> => {
    const { data } = await api.post('/tickets/resolve', {
      ticket_id: ticketId,
      resolution,
    }, {
      headers: { 'X-Agent-ID': agentId },
    });
    return data;
  },

  approveTicket: async (
    ticketId: string,
    agentId: string = 'ui-user'
  ): Promise<{ success: boolean; ticket_id: string; message: string }> => {
    const { data } = await api.post('/tickets/approve',
      { ticket_id: ticketId },
      { headers: { 'X-Agent-ID': agentId } }
    );
    return data;
  },

  rejectTicket: async (
    ticketId: string,
    rejectionReason: string,
    agentId: string = 'ui-user'
  ): Promise<{ success: boolean; ticket_id: string; message: string }> => {
    const { data } = await api.post('/tickets/reject',
      { ticket_id: ticketId, rejection_reason: rejectionReason },
      { headers: { 'X-Agent-ID': agentId } }
    );
    return data;
  },

  getPendingReviewCount: async (): Promise<{ count: number; ticket_ids: string[] }> => {
    const { data } = await api.get('/tickets/pending-review-count');
    return data;
  },

  getCommitDiff: async (commitSha: string): Promise<CommitDiff> => {
    const { data } = await api.get(`/tickets/commit-diff/${commitSha}`, {
      headers: { 'X-Agent-ID': 'ui-user' },
    });
    return data;
  },

  // Blocked Tasks
  getBlockedTasks: async (workflowId?: string): Promise<BlockedTask[]> => {
    const params = workflowId ? `?workflow_id=${workflowId}` : '';
    const { data } = await api.get(`/blocked-tasks${params}`);
    return data;
  },

  getTaskBlockerDetails: async (taskId: string): Promise<{
    task_id: string;
    is_blocked: boolean;
    blocker_count: number;
    blockers: Array<{
      ticket_id: string;
      title: string;
      status: string;
      priority: string;
      is_resolved: boolean;
    }>;
  }> => {
    const { data } = await api.get(`/blocked-tasks/${taskId}/blockers`);
    return data;
  },

  syncBlockingStatus: async (): Promise<{
    success: boolean;
    tasks_blocked: number;
    tasks_unblocked: number;
    total_checked: number;
    errors: Array<{ task_id: string; error: string }>;
  }> => {
    const { data } = await api.post('/sync-blocking-status');
    return data;
  },
};
