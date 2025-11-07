export interface Agent {
  id: string;
  status: 'idle' | 'working' | 'stuck' | 'terminated';
  cli_type: string;
  current_task_id: string | null;
  tmux_session_name: string | null;
  health_check_failures: number;
  created_at: string;
  last_activity: string | null;
  current_task?: {
    id: string;
    description: string;
    status: string;
    priority: string;
    started_at: string | null;
    runtime_seconds: number;
    phase_info?: {
      id: string;
      name: string;
      order: number;
    };
  } | null;
}

export interface Task {
  id: string;
  description: string;
  done_definition: string;
  status: 'pending' | 'queued' | 'blocked' | 'assigned' | 'in_progress' | 'done' | 'failed' | 'duplicated';
  priority: 'low' | 'medium' | 'high';
  assigned_agent_id: string | null;
  created_by_agent_id: string | null;
  parent_task_id: string | null;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
  estimated_complexity: number | null;
  phase_id?: string | null;
  phase_name?: string | null;
  phase_order?: number | null;
  workflow_id?: string | null;
  ticket_id?: string | null;
  // Task deduplication fields
  duplicate_of_task_id?: string | null;
  similarity_score?: number | null;
  related_task_ids?: string[] | null;
}

export interface Memory {
  id: string;
  content: string;
  memory_type: 'error_fix' | 'discovery' | 'decision' | 'learning' | 'warning' | 'codebase_knowledge';
  agent_id: string;
  related_task_id: string | null;
  tags: string[] | null;
  related_files: string[] | null;
  created_at: string;
}

export interface DashboardStats {
  active_agents: number;
  running_tasks: number;
  queued_tasks: number;
  total_memories: number;
  recent_activity: ActivityLog[];
  stuck_agents: number;
  failed_tasks_today: number;
  timestamp: string;
}

export interface ActivityLog {
  id: number;
  type: string;
  message: string;
  agent_id: string;
  timestamp: string;
}

export interface GraphNode {
  id: string;
  type: 'agent' | 'task';
  label: string;
  data: any;
  position?: { x: number; y: number };
}

export interface GraphEdge {
  id: string;
  source: string;
  target: string;
  label: string;
  type: 'created' | 'assigned' | 'subtask';
}

export interface PhaseInfo {
  id: string;
  name: string;
  order: number;
  description: string;
}

export interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
  phases: Record<string, PhaseInfo>;
  timestamp: string;
}

export type ResultScope = 'workflow' | 'task';

export type WorkflowResultStatus = 'pending_validation' | 'validated' | 'rejected';

export type TaskResultStatus = 'unverified' | 'verified' | 'disputed';

export type ResultStatus = WorkflowResultStatus | TaskResultStatus;

export interface ResultEvidenceItem {
  criterion: string;
  passed: boolean;
  notes?: string | null;
  artifact_path?: string | null;
}

export interface ResultSummary {
  result_id: string;
  scope: ResultScope;
  workflow_id: string | null;
  workflow_name?: string | null;
  task_id: string | null;
  task_description?: string | null;
  agent_id: string;
  agent_label?: string | null;
  status: ResultStatus;
  validation_feedback?: string | null;
  validation_evidence?: ResultEvidenceItem[];
  result_type?: string | null;
  summary: string;
  created_at: string;
  validated_at?: string | null;
  result_file_path?: string | null;
  validation_report_path?: string | null;
  extra_files?: string[];
}

export interface ResultValidationDetail {
  result_id: string;
  status: ResultStatus;
  validator_agent_id?: string | null;
  feedback?: string | null;
  evidence: ResultEvidenceItem[];
  started_at?: string | null;
  completed_at?: string | null;
  report_path?: string | null;
}

export interface ResultContentResponse {
  result_id: string;
  content: string;
  content_type?: 'markdown' | 'text';
}

export interface ExtraFileContentResponse {
  result_id: string;
  file_index: number;
  file_path: string;
  filename: string;
  content: string;
  content_type: 'text' | 'binary';
  encoding: 'utf-8' | 'base64';
}

export interface WebSocketMessage {
  type:
    | 'task_created'
    | 'task_completed'
    | 'agent_created'
    | 'agent_status_changed'
    | 'memory_added'
    | 'stats_update'
    | 'guardian_analysis'
    | 'conductor_analysis'
    | 'steering_intervention'
    | 'duplicate_detected'
    | 'results_reported'
    | 'result_validation_completed'
    | 'ticket_created'
    | 'ticket_updated'
    | 'status_changed'
    | 'comment_added'
    | 'commit_linked'
    | 'ticket_resolved';
  [key: string]: any;
}

export interface TaskFullDetails {
  id: string;
  raw_description: string;
  enriched_description: string | null;
  done_definition: string;
  status: 'pending' | 'queued' | 'assigned' | 'in_progress' | 'under_review' | 'validation_in_progress' | 'needs_work' | 'done' | 'failed' | 'duplicated';
  priority: 'low' | 'medium' | 'high';
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
  completion_notes: string | null;
  failure_reason: string | null;
  estimated_complexity: number | null;
  runtime_seconds: number;
  system_prompt: string | null;
  user_prompt: string;
  // Task deduplication fields
  duplicate_of_task_id?: string | null;
  similarity_score?: number | null;
  related_task_ids?: string[] | null;
  duplicated_tasks?: Array<{
    id: string;
    description: string;
    similarity_score: number;
    created_at: string;
    created_by_agent_id: string | null;
  }>;
  phase_info: {
    id: string;
    name: string;
    order: number;
    description: string;
    done_definitions: string[];
    additional_notes: string | null;
  } | null;
  agent_info: {
    id: string;
    status: string;
    cli_type: string;
    created_at: string | null;
    last_activity: string | null;
  } | null;
  parent_task: {
    id: string;
    description: string;
    status: string;
    created_at: string | null;
  } | null;
  child_tasks: Array<{
    id: string;
    description: string;
    status: string;
    priority: string;
    created_at: string | null;
  }>;
  has_results: boolean;
  validation_enabled: boolean;
  // Ticket tracking integration
  ticket_id?: string | null;
  related_ticket_ids?: string[];
  related_tasks_details?: Array<{
    id: string;
    description: string;
    status: string;
    similarity_score: number;
    created_at: string | null;
  }>;
}

// Ticket Tracking System Types

export type TicketPriority = 'low' | 'medium' | 'high' | 'critical';

export type TicketType = 'bug' | 'feature' | 'improvement' | 'task' | 'spike' | 'documentation' | 'research';

export interface BoardColumn {
  id: string;
  name: string;
  order: number;
  color: string;
}

export interface BoardConfig {
  id: string;
  workflow_id: string;
  name: string;
  columns: BoardColumn[];
  ticket_types: TicketType[];
  default_ticket_type: TicketType;
  initial_status: string;
  auto_assign: boolean;
  require_comments_on_status_change: boolean;
  allow_reopen: boolean;
  track_time: boolean;
  created_at: string;
  updated_at: string;
}

export interface Ticket {
  id: string;
  workflow_id: string;
  created_by_agent_id: string;
  assigned_agent_id: string | null;
  title: string;
  description: string;
  ticket_type: TicketType;
  priority: TicketPriority;
  status: string;
  created_at: string;
  updated_at: string;
  started_at: string | null;
  completed_at: string | null;
  parent_ticket_id: string | null;
  related_task_ids: string[] | null;
  related_ticket_ids: string[] | null;
  tags: string[] | null;
  blocked_by_ticket_ids: string[] | null;
  blocks_ticket_ids?: string[] | null;
  is_blocked: boolean;
  is_resolved: boolean;
  resolved_at: string | null;
  // Human approval fields
  approval_status: 'auto_approved' | 'pending_review' | 'approved' | 'rejected';
  approval_requested_at: string | null;
  approval_decided_at: string | null;
  approval_decided_by: string | null;
  rejection_reason: string | null;
}

export interface TicketComment {
  id: string;
  ticket_id: string;
  agent_id: string;
  comment_text: string;
  comment_type: 'general' | 'status_change' | 'assignment' | 'blocker' | 'resolution';
  created_at: string;
  updated_at: string | null;
  is_edited: boolean;
  mentions: string[] | null;
  attachments: string[] | null;
}

export interface TicketHistory {
  id: number;
  ticket_id: string;
  agent_id: string;
  change_type: 'created' | 'status_changed' | 'assigned' | 'commented' | 'field_updated' | 'commit_linked' | 'reopened' | 'blocked' | 'unblocked';
  field_name: string | null;
  old_value: string | null;
  new_value: string | null;
  change_description: string;
  metadata: any;
  changed_at: string;
}

export interface TicketCommit {
  id: string;
  ticket_id: string;
  agent_id: string;
  commit_sha: string;
  commit_message: string;
  commit_timestamp: string;
  files_changed: number;
  insertions: number;
  deletions: number;
  files_list: string[] | null;
  linked_at: string;
  link_method: 'manual' | 'auto_detected' | 'worktree';
}

export interface TicketDetail extends Ticket {
  comment_count: number;
  commit_count: number;
  blocks_ticket_ids: string[] | null;
}

export interface TicketStats {
  total_tickets: number;
  by_status: Record<string, number>;
  by_type: Record<string, number>;
  by_priority: Record<string, number>;
  by_agent: Record<string, number>;
  blocked_count: number;
  resolved_count: number;
  created_today: number;
  completed_today: number;
  velocity_last_7_days: number;
  board_config: BoardConfig;
}

export interface CommitDiff {
  commit_sha: string;
  commit_message: string;
  commit_timestamp: string;
  author: string;
  files: Array<{
    path: string;
    status: 'added' | 'modified' | 'deleted' | 'renamed';
    language: string;
    insertions: number;
    deletions: number;
    diff: string;
  }>;
  total_insertions: number;
  total_deletions: number;
  total_files: number;
}

export interface TicketSearchResult {
  ticket_id: string;
  title: string;
  description: string;
  status: string;
  priority: string;
  ticket_type: string;
  relevance_score: number;
  matched_in: string[];
  preview: string;
  created_at: string;
  assigned_agent_id?: string | null;
  tags?: string[] | null;
}

export interface BlockerTicket {
  ticket_id: string;
  title: string;
  status: string;
  priority: string;
  is_resolved: boolean;
}

export interface BlockedTask {
  task_id: string;
  description: string;
  priority: string;
  created_at: string;
  ticket_id: string | null;
  is_blocked: boolean;
  blocking_ticket_ids: string[];
  blocking_tickets: BlockerTicket[];
  phase_id?: string | null;
  workflow_id?: string | null;
}
