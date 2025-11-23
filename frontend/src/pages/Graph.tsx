import React, { useEffect, useState, useCallback, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import ReactFlow, {
  Node,
  Edge,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  Position,
  ConnectionMode,
  Handle,
  MiniMap,
} from 'react-flow-renderer';
import { motion, AnimatePresence } from 'framer-motion';
import { GitBranch, Bot, FileText, X, RefreshCw, Layers, ArrowRight, Play, Pause, Settings } from 'lucide-react';
import { apiService } from '@/services/api';
import { GraphNode, GraphEdge, PhaseInfo } from '@/types';
import { useWebSocket } from '@/context/WebSocketContext';
import { useWorkflow } from '@/context/WorkflowContext';
import ExecutionSelector from '@/components/ExecutionSelector';
import StatusBadge from '@/components/StatusBadge';
import TaskDetailModal from '@/components/TaskDetailModal';
import RealTimeAgentOutput from '@/components/RealTimeAgentOutput';

// Custom node component for agents
const AgentNode: React.FC<{ data: any }> = ({ data }) => {
  const isExternal = data.status === 'external';
  const isHighlighted = data.isHighlighted;
  const isDimmed = data.isDimmed;

  const formatTime = (timestamp: string) => {
    if (!timestamp) return '';
    const date = new Date(timestamp);
    return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
  };

  const baseClasses = isExternal ? 'bg-purple-50 border-purple-400' : 'bg-blue-50 border-blue-400';
  const highlightClasses = isHighlighted ? 'ring-4 ring-red-400 ring-opacity-75 shadow-2xl scale-105' : '';
  const dimClasses = isDimmed ? 'opacity-30' : '';

  return (
    <div className={`${baseClasses} ${highlightClasses} ${dimClasses} border-2 rounded-lg p-2 min-w-[140px] shadow-md relative transition-all duration-300`}>
      <Handle
        type="target"
        position={Position.Left}
        style={{ background: isExternal ? '#9333EA' : '#3B82F6', width: 8, height: 8 }}
      />
      <Handle
        type="source"
        position={Position.Right}
        style={{ background: isExternal ? '#9333EA' : '#3B82F6', width: 8, height: 8 }}
      />
      <div className="flex items-center gap-1 mb-1">
        <Bot className={`w-4 h-4 ${isExternal ? 'text-purple-600' : 'text-blue-600'}`} />
        <span className="text-xs font-semibold text-gray-800">{isExternal ? 'MCP' : 'Agent'}</span>
      </div>
      <p className="text-xs font-mono text-gray-700">{data.id.substring(0, 8)}...</p>
      {data.created_at && (
        <p className="text-xs text-gray-500">🕐 {formatTime(data.created_at)}</p>
      )}
      {!isExternal && <StatusBadge status={data.status} size="sm" />}
    </div>
  );
};

// Custom node component for tasks
const TaskNode: React.FC<{ data: any }> = ({ data }) => {
  const isHighlighted = data.isHighlighted;
  const isDimmed = data.isDimmed;

  const formatTime = (timestamp: string) => {
    if (!timestamp) return '';
    const date = new Date(timestamp);
    return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
  };

  const phaseColors: Record<number, string> = {
    1: 'bg-green-50 border-green-400',
    2: 'bg-blue-50 border-blue-400',
    3: 'bg-yellow-50 border-yellow-400',
    4: 'bg-pink-50 border-pink-400',
    5: 'bg-indigo-50 border-indigo-400',
  };

  const bgClass = phaseColors[data.phase_order] || 'bg-gray-50 border-gray-400';
  const highlightClasses = isHighlighted ? 'ring-4 ring-red-400 ring-opacity-75 shadow-2xl scale-105' : '';
  const dimClasses = isDimmed ? 'opacity-30' : '';

  return (
    <div className={`${bgClass} ${highlightClasses} ${dimClasses} border-2 rounded-lg p-2 min-w-[160px] max-w-[200px] shadow-md relative transition-all duration-300`}>
      <Handle
        type="target"
        position={Position.Left}
        style={{ background: '#10B981', width: 8, height: 8 }}
      />
      <Handle
        type="source"
        position={Position.Right}
        style={{ background: '#10B981', width: 8, height: 8 }}
      />
      <div className="flex items-center gap-1 mb-1">
        <FileText className="w-4 h-4 text-gray-600" />
        <span className="text-xs font-semibold text-gray-800">Task</span>
        {data.phase_name && (
          <span className="text-xs px-1.5 py-0.5 bg-white bg-opacity-70 text-gray-700 rounded ml-auto font-bold">
            P{data.phase_order}
          </span>
        )}
      </div>
      <p className="text-xs text-gray-700 line-clamp-2">
        {data.description?.substring(0, 50)}...
      </p>
      {data.created_at && (
        <p className="text-xs text-gray-500">🕐 {formatTime(data.created_at)}</p>
      )}
      <StatusBadge status={data.status} size="sm" />
    </div>
  );
};

const nodeTypes = {
  agent: AgentNode,
  task: TaskNode,
};

// Node preview modal
const NodePreview: React.FC<{ node: any; onClose: () => void }> = ({ node, onClose }) => {
  if (!node) return null;

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
          initial={{ scale: 0.9 }}
          animate={{ scale: 1 }}
          className="bg-white rounded-lg shadow-xl max-w-lg w-full"
          onClick={(e) => e.stopPropagation()}
        >
          <div className="px-6 py-4 border-b flex items-center justify-between">
            <div className="flex items-center">
              {node.type === 'agent' ? (
                <Bot className="w-5 h-5 mr-2 text-blue-600" />
              ) : (
                <FileText className="w-5 h-5 mr-2 text-green-600" />
              )}
              <h3 className="text-lg font-semibold text-gray-800">
                {node.type === 'agent' ? 'Agent' : 'Task'} Details
              </h3>
            </div>
            <button
              onClick={onClose}
              className="text-gray-500 hover:text-gray-700"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          <div className="p-6 space-y-3">
            <div>
              <p className="text-sm text-gray-600">ID</p>
              <p className="font-mono text-xs text-gray-800">{node.data.id}</p>
            </div>

            {node.type === 'agent' ? (
              <>
                <div>
                  <p className="text-sm text-gray-600">Status</p>
                  <StatusBadge status={node.data.status} />
                </div>
                <div>
                  <p className="text-sm text-gray-600">CLI Type</p>
                  <p className="text-gray-800">{node.data.cli_type}</p>
                </div>
                {node.data.current_task_id && (
                  <div>
                    <p className="text-sm text-gray-600">Current Task</p>
                    <p className="font-mono text-xs text-gray-800">
                      {node.data.current_task_id}
                    </p>
                  </div>
                )}
              </>
            ) : (
              <>
                <div>
                  <p className="text-sm text-gray-600">Description</p>
                  <p className="text-gray-800">{node.data.description}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">Status</p>
                  <StatusBadge status={node.data.status} />
                </div>
                {node.data.phase_name && (
                  <div>
                    <p className="text-sm text-gray-600">Phase</p>
                    <p className="text-gray-800">
                      Phase {node.data.phase_order}: {node.data.phase_name}
                    </p>
                  </div>
                )}
                <div>
                  <p className="text-sm text-gray-600">Priority</p>
                  <span
                    className={`text-xs px-2 py-1 rounded ${
                      node.data.priority === 'high'
                        ? 'bg-red-100 text-red-700'
                        : node.data.priority === 'medium'
                        ? 'bg-yellow-100 text-yellow-700'
                        : 'bg-gray-100 text-gray-700'
                    }`}
                  >
                    {node.data.priority}
                  </span>
                </div>
              </>
            )}
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
};

const Graph: React.FC = () => {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [selectedNode, setSelectedNode] = useState<any>(null);
  const [selectedTaskId, setSelectedTaskId] = useState<string | null>(null);
  const [selectedAgent, setSelectedAgent] = useState<any>(null);
  const [hoveredNode, setHoveredNode] = useState<string | null>(null);
  const [highlightedNodes, setHighlightedNodes] = useState<Set<string>>(new Set());
  const [highlightedEdges, setHighlightedEdges] = useState<Set<string>>(new Set());
  const [columnHeaders, setColumnHeaders] = useState<{ label: string; x: number; width: number; type: 'agents' | 'tasks' }[]>([]);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [refreshInterval, setRefreshInterval] = useState(15);
  const { subscribe } = useWebSocket();
  const { selectedExecution } = useWorkflow();

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['graph'],
    queryFn: apiService.getGraphData,
    refetchInterval: autoRefresh ? refreshInterval * 1000 : false,
  });

  // Create proper alternating columns
  const layoutNodes = useCallback((graphNodes: GraphNode[], graphEdges: GraphEdge[], phases: Record<string, PhaseInfo>): Node[] => {
    const nodeMap = new Map<string, Node>();

    // Add phase info to task nodes
    graphNodes.forEach(node => {
      if (node.type === 'task' && node.data.phase_id && phases[node.data.phase_id]) {
        const phase = phases[node.data.phase_id];
        node.data.phase_name = phase.name;
        node.data.phase_order = phase.order;
      }
    });

    // Sort phases and deduplicate
    const sortedPhases = Object.values(phases)
      .sort((a, b) => a.order - b.order)
      .filter((phase, index, array) =>
        index === 0 || phase.order !== array[index - 1].order
      );


    // Create alternating column structure: Agents → Tasks → Agents → Tasks
    const columns: { id: string; type: 'agents' | 'tasks'; nodes: GraphNode[]; label: string }[] = [];

    // Column 0: External agents
    columns.push({
      id: 'external_agents',
      type: 'agents',
      nodes: [],
      label: 'External Agents'
    });

    // For each phase: Tasks column, then Agents column (if not last phase)
    sortedPhases.forEach((phase, index) => {
      // Tasks column for this phase
      columns.push({
        id: `tasks_p${phase.order}`,
        type: 'tasks',
        nodes: [],
        label: `Phase ${phase.order}: ${phase.name}`
      });

      // Agents column for agents that work on NEXT phase (if there is a next phase)
      if (index < sortedPhases.length - 1) {
        const nextPhase = sortedPhases[index + 1];
        columns.push({
          id: `agents_for_p${nextPhase.order}`,
          type: 'agents',
          nodes: [],
          label: `Agents→P${nextPhase.order}`
        });
      }
    });


    // First pass: Place all tasks in their phase columns
    graphNodes.forEach(node => {
      if (node.type === 'task' && node.data.phase_order) {
        const column = columns.find(col => col.id === `tasks_p${node.data.phase_order}`);
        if (column) {
          column.nodes.push(node);
        }
      }
    });


    // Second pass: Place agents to create the alternating flow
    // Separate external and internal agents
    const externalAgents = graphNodes.filter(n => n.type === 'agent' && n.data.status === 'external');
    const internalAgents = graphNodes.filter(n => n.type === 'agent' && n.data.status !== 'external');

    // Place external agents in column 0
    externalAgents.forEach(agent => {
      columns[0].nodes.push(agent);
    });

    // Find the agent columns (agents_for_pX)
    const agentColumns = columns.filter(col => col.type === 'agents' && col.id !== 'external_agents');

    if (agentColumns.length > 0 && internalAgents.length > 0) {
      // Strategy: Distribute internal agents proportionally based on task counts in subsequent phases
      const p2TaskCount = graphNodes.filter(n => n.type === 'task' && n.data.phase_order === 2).length;
      const p3TaskCount = graphNodes.filter(n => n.type === 'task' && n.data.phase_order === 3).length;

      // Calculate proportional distribution
      const totalTasks = p2TaskCount + p3TaskCount;
      let agentsForP2 = 0;
      let agentsForP3 = 0;

      if (totalTasks > 0) {
        agentsForP2 = Math.round((p2TaskCount / totalTasks) * internalAgents.length);
        agentsForP3 = internalAgents.length - agentsForP2;
      } else {
        // Even split if no tasks
        agentsForP2 = Math.floor(internalAgents.length / 2);
        agentsForP3 = internalAgents.length - agentsForP2;
      }

      // Place agents in columns
      internalAgents.forEach((agent, index) => {
        if (index < agentsForP2) {
          // Place in agents_for_p2 column
          const p2Column = columns.find(col => col.id === 'agents_for_p2');
          if (p2Column) {
            p2Column.nodes.push(agent);
          } else {
            columns[0].nodes.push(agent); // fallback
          }
        } else {
          // Place in agents_for_p3 column
          const p3Column = columns.find(col => col.id === 'agents_for_p3');
          if (p3Column) {
            p3Column.nodes.push(agent);
          } else {
            columns[0].nodes.push(agent); // fallback
          }
        }
      });
    } else {
      // Fallback: put all internal agents in external column
      internalAgents.forEach(agent => {
        columns[0].nodes.push(agent);
      });
    }

    // Layout configuration
    const columnWidth = 250;
    const nodeHeight = 70;
    const nodeSpacing = 15;
    const startX = 100;
    const startY = 120;

    // Track headers
    const headers: { label: string; x: number; width: number; type: 'agents' | 'tasks' }[] = [];

    // Position nodes in each column
    let currentX = startX;

    columns.forEach((column) => {
      if (column.nodes.length === 0 && column.id !== 'external_agents') {
        // Skip empty columns except external agents (always show it)
        return;
      }

      // Sort nodes to minimize edge crossings
      column.nodes.sort((a, b) => {
        // Sort by ID for consistency
        return a.id.localeCompare(b.id);
      });

      // Calculate vertical positions
      const totalHeight = column.nodes.length * (nodeHeight + nodeSpacing);
      const columnStartY = startY + Math.max(0, (600 - totalHeight) / 2);

      column.nodes.forEach((node, index) => {
        const y = columnStartY + index * (nodeHeight + nodeSpacing);

        const isHighlighted = highlightedNodes.has(node.id);
        const isDimmed = hoveredNode && !isHighlighted;

        const reactFlowNode: Node = {
          id: node.id,
          type: node.type,
          position: { x: currentX, y },
          data: {
            ...node.data,
            isHighlighted,
            isDimmed,
          },
          sourcePosition: Position.Right,
          targetPosition: Position.Left,
        };

        nodeMap.set(node.id, reactFlowNode);
      });

      // Add header for this column
      headers.push({
        label: column.label,
        x: currentX - 50,
        width: columnWidth,
        type: column.type
      });

      currentX += columnWidth;
    });

    // Update column headers state
    setColumnHeaders(headers);

    return Array.from(nodeMap.values());
  }, [highlightedNodes, hoveredNode]);

  // Function to find all connected nodes in the chain (excluding external agents)
  const findConnectedChain = useCallback((nodeId: string, graphEdges: GraphEdge[]): { nodes: Set<string>, edges: Set<string> } => {
    const visitedNodes = new Set<string>();
    const connectedEdges = new Set<string>();
    const queue = [nodeId];

    // Get all external agent IDs to exclude them from traversal
    const externalAgentIds = new Set(
      data?.nodes
        .filter(n => n.type === 'agent' && n.data.status === 'external')
        .map(n => n.id) || []
    );

    while (queue.length > 0) {
      const currentNode = queue.shift()!;
      if (visitedNodes.has(currentNode)) continue;
      visitedNodes.add(currentNode);

      // Find all edges connected to this node (both incoming and outgoing)
      graphEdges.forEach(edge => {
        if (edge.source === currentNode || edge.target === currentNode) {
          connectedEdges.add(edge.id);

          // Add the other node to the queue if not visited and not an external agent
          const otherNode = edge.source === currentNode ? edge.target : edge.source;
          if (!visitedNodes.has(otherNode) && !externalAgentIds.has(otherNode)) {
            queue.push(otherNode);
          }
        }
      });
    }

    return { nodes: visitedNodes, edges: connectedEdges };
  }, [data]);

  // Convert edges with better styling and highlighting
  const convertEdges = useCallback((graphEdges: GraphEdge[]): Edge[] => {
    return graphEdges.map(edge => {
      const isHighlighted = highlightedEdges.has(edge.id);

      return {
        id: edge.id,
        source: edge.source,
        target: edge.target,
        type: 'smoothstep',
        animated: isHighlighted,
        style: {
          stroke: isHighlighted ? '#FF6B6B' :
                  edge.type === 'created' ? '#8B5CF6' :
                  edge.type === 'assigned' ? '#10B981' :
                  edge.type === 'subtask' ? '#F59E0B' :
                  '#6B7280',
          strokeWidth: isHighlighted ? 4 : 2,
          opacity: hoveredNode && !isHighlighted ? 0.3 : 1,
        },
        labelStyle: {
          fill: '#4B5563',
          fontSize: 9,
        },
        labelBgStyle: {
          fill: '#ffffff',
          fillOpacity: 0.8,
        },
      };
    });
  }, [highlightedEdges, hoveredNode]);

  useEffect(() => {
    if (data) {
      const layoutedNodes = layoutNodes(data.nodes, data.edges, data.phases || {});
      const convertedEdges = convertEdges(data.edges);
      setNodes(layoutedNodes);
      setEdges(convertedEdges);
    }
  }, [data, layoutNodes, convertEdges, setNodes, setEdges]);

  // Subscribe to WebSocket updates
  useEffect(() => {
    const unsubscribeTask = subscribe('task_created', () => {
      refetch();
    });

    const unsubscribeAgent = subscribe('agent_created', () => {
      refetch();
    });

    return () => {
      unsubscribeTask();
      unsubscribeAgent();
    };
  }, [subscribe, refetch]);

  const onNodeClick = useCallback((event: React.MouseEvent, node: Node) => {
    if (node.type === 'task') {
      // Open TaskDetailModal for task nodes
      setSelectedTaskId(node.data.id);
      setSelectedNode(null); // Close the preview
    } else if (node.type === 'agent') {
      // Open RealTimeAgentOutput for agent nodes
      const agentData = {
        id: node.data.id,
        status: node.data.status,
        cli_type: node.data.cli_type || 'unknown',
        current_task_id: node.data.current_task_id || null,
        tmux_session_name: null,
        health_check_failures: 0,
        created_at: node.data.created_at || '',
        last_activity: null,
      };
      setSelectedAgent(agentData);
      setSelectedNode(null); // Close the preview
    } else {
      // Fallback to original preview behavior for other node types
      setSelectedNode(node);
    }
  }, []);

  const onNodeMouseEnter = useCallback((event: React.MouseEvent, node: Node) => {
    if (!data) return;

    setHoveredNode(node.id);
    const chain = findConnectedChain(node.id, data.edges);
    setHighlightedNodes(chain.nodes);
    setHighlightedEdges(chain.edges);
  }, [data, findConnectedChain]);

  const onNodeMouseLeave = useCallback(() => {
    setHoveredNode(null);
    setHighlightedNodes(new Set());
    setHighlightedEdges(new Set());
  }, []);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6">
        <p className="text-red-600">Failed to load graph data</p>
      </div>
    );
  }

  // Column headers component
  const ColumnHeaders = () => (
    <div className="absolute top-0 left-0 right-0 h-16 pointer-events-none z-10">
      <div className="relative h-full">
        {columnHeaders.map((header, index) => (
          <div
            key={index}
            className="absolute flex items-center justify-center h-full"
            style={{
              left: header.x,
              width: header.width,
            }}
          >
            <div
              className={`w-full h-full flex items-center justify-center border-b-2 ${
                header.type === 'agents'
                  ? (header.label.includes('External') ? 'bg-purple-100 border-purple-400' : 'bg-gray-100 border-gray-400')
                  : header.label.includes('Phase 1') ? 'bg-green-100 border-green-400' :
                    header.label.includes('Phase 2') ? 'bg-blue-100 border-blue-400' :
                    header.label.includes('Phase 3') ? 'bg-yellow-100 border-yellow-400' :
                    header.label.includes('Phase 4') ? 'bg-pink-100 border-pink-400' :
                    'bg-indigo-100 border-indigo-400'
              }`}
            >
              <div className="text-center px-2">
                <p className="text-xs font-bold text-gray-700">
                  {header.label.split(':')[0]}
                </p>
                {header.label.includes(':') && (
                  <p className="text-xs text-gray-600">
                    {header.label.split(':')[1]}
                  </p>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );

  return (
    <div className="h-full flex flex-col">
      <div className="mb-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-800">Graph Visualization</h1>
            <p className="text-gray-600 mt-1">
              {selectedExecution ? (
                <>Graph for: {selectedExecution.description || selectedExecution.definition_name}</>
              ) : (
                'Agent and task flow through phases'
              )}
            </p>
          </div>

          {/* Refresh Controls */}
          <div className="flex items-center gap-3">
            <ExecutionSelector />
            <div className="flex items-center gap-2 text-sm">
              <span className="text-gray-600">Auto-refresh:</span>
              <select
                value={refreshInterval}
                onChange={(e) => setRefreshInterval(Number(e.target.value))}
                className="px-2 py-1 border border-gray-300 rounded text-sm"
                disabled={!autoRefresh}
              >
                <option value={5}>5s</option>
                <option value={10}>10s</option>
                <option value={15}>15s</option>
                <option value={30}>30s</option>
                <option value={60}>60s</option>
              </select>

              <button
                onClick={() => setAutoRefresh(!autoRefresh)}
                className={`p-2 rounded-lg transition-colors flex items-center ${
                  autoRefresh
                    ? 'bg-green-100 text-green-700 hover:bg-green-200'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
                title={autoRefresh ? 'Pause auto-refresh' : 'Resume auto-refresh'}
              >
                {autoRefresh ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
              </button>
            </div>

            <button
              onClick={() => refetch()}
              className="px-4 py-2 bg-primary text-white rounded-lg hover:bg-blue-600 transition-colors flex items-center"
            >
              <RefreshCw className="w-4 h-4 mr-2" />
              Refresh
            </button>
          </div>
        </div>
      </div>

      {/* Legend */}
      <div className="bg-white rounded-lg shadow-md p-4 mb-4">
        <div className="flex items-center space-x-6 flex-wrap gap-2">
          <div className="flex items-center">
            <ArrowRight className="w-4 h-4 mr-2 text-indigo-600" />
            <span className="text-sm font-semibold text-gray-700">Flow: Agents → Tasks → Agents</span>
          </div>
          <div className="w-px h-4 bg-gray-300"></div>
          <div className="flex items-center">
            <div className="w-4 h-4 bg-purple-500 rounded mr-2"></div>
            <span className="text-sm text-gray-600">External/MCP Agent</span>
          </div>
          <div className="flex items-center">
            <div className="w-4 h-4 bg-blue-500 rounded mr-2"></div>
            <span className="text-sm text-gray-600">Internal Agent</span>
          </div>
          <div className="flex items-center">
            <div className="w-4 h-4 bg-green-500 rounded mr-2"></div>
            <span className="text-sm text-gray-600">Phase 1 Task</span>
          </div>
          <div className="flex items-center">
            <div className="w-4 h-4 bg-blue-500 rounded mr-2"></div>
            <span className="text-sm text-gray-600">Phase 2 Task</span>
          </div>
          <div className="flex items-center">
            <div className="w-4 h-4 bg-yellow-500 rounded mr-2"></div>
            <span className="text-sm text-gray-600">Phase 3 Task</span>
          </div>
          <div className="w-px h-4 bg-gray-300"></div>
          <div className="flex items-center">
            <div className="w-8 h-1 bg-purple-500 mr-2"></div>
            <span className="text-sm text-gray-600">Creates</span>
          </div>
          <div className="flex items-center">
            <div className="w-8 h-1 bg-green-500 mr-2"></div>
            <span className="text-sm text-gray-600">Assigned</span>
          </div>
          <div className="w-px h-4 bg-gray-300"></div>
          <div className="flex items-center">
            <div className="w-8 h-1 bg-red-500 mr-2"></div>
            <span className="text-sm text-gray-600">Hover to highlight chain</span>
          </div>
          <div className="w-px h-4 bg-gray-300"></div>
          <div className="flex items-center">
            <GitBranch className="w-4 h-4 mr-2 text-gray-500" />
            <span className="text-sm text-gray-600 font-medium">
              {nodes.length} nodes, {edges.length} edges
            </span>
          </div>
        </div>
      </div>

      {/* Graph with Column Headers */}
      <div className="bg-white rounded-lg shadow-md relative" style={{ height: '800px', width: '100%' }}>
        <ColumnHeaders />

        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onNodeClick={onNodeClick}
          onNodeMouseEnter={onNodeMouseEnter}
          onNodeMouseLeave={onNodeMouseLeave}
          nodeTypes={nodeTypes}
          connectionMode={ConnectionMode.Loose}
          fitView
          fitViewOptions={{ padding: 0.1, maxZoom: 0.8 }}
          style={{ width: '100%', height: '100%', paddingTop: '60px' }}
        >
          <Background variant="dots" gap={20} size={1} />
          <Controls />
          <MiniMap
            nodeColor={(node) => {
              if (node.type === 'agent') {
                return node.data.status === 'external' ? '#9333EA' : '#3B82F6';
              }
              // Color tasks by phase
              const phaseOrder = node.data.phase_order;
              if (phaseOrder === 1) return '#10B981';
              if (phaseOrder === 2) return '#3B82F6';
              if (phaseOrder === 3) return '#EAB308';
              if (phaseOrder === 4) return '#EC4899';
              return '#6366F1';
            }}
            nodeStrokeWidth={3}
            pannable
            zoomable
          />
        </ReactFlow>
      </div>

      {/* Node Preview Modal */}
      {selectedNode && (
        <NodePreview node={selectedNode} onClose={() => setSelectedNode(null)} />
      )}

      {/* Task Detail Modal */}
      <TaskDetailModal
        taskId={selectedTaskId}
        onClose={() => setSelectedTaskId(null)}
        onNavigateToTask={(taskId) => setSelectedTaskId(taskId)}
        onNavigateToGraph={(taskId) => {
          setSelectedTaskId(null);
          // Could implement highlighting the task in the graph here
        }}
      />

      {/* Real-time Agent Output Modal */}
      <RealTimeAgentOutput
        agent={selectedAgent}
        onClose={() => setSelectedAgent(null)}
      />
    </div>
  );
};

export default Graph;