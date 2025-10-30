import React, { useCallback, useEffect, useMemo, useState } from 'react';
import ReactFlow, {
  Node,
  Edge,
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  MarkerType,
  Panel,
} from 'reactflow';
import dagre from 'dagre';
import { useQuery } from '@tanstack/react-query';
import { apiService } from '@/services/api';
import TicketGraphNode from './TicketGraphNode';
import TicketDetailModal from './TicketDetailModal';
import { CheckCircle, Lock, AlertCircle, Circle } from 'lucide-react';
import 'reactflow/dist/style.css';

const nodeTypes = {
  ticketNode: TicketGraphNode,
};

// Layout direction
type LayoutDirection = 'TB' | 'LR';

// Function to apply dagre layout
const getLayoutedElements = (
  nodes: Node[],
  edges: Edge[],
  direction: LayoutDirection = 'TB'
) => {
  const dagreGraph = new dagre.graphlib.Graph();
  dagreGraph.setDefaultEdgeLabel(() => ({}));

  const nodeWidth = 280;
  const nodeHeight = 140;

  dagreGraph.setGraph({
    rankdir: direction,
    nodesep: 80,
    ranksep: 100,
    marginx: 50,
    marginy: 50,
  });

  nodes.forEach((node) => {
    dagreGraph.setNode(node.id, { width: nodeWidth, height: nodeHeight });
  });

  edges.forEach((edge) => {
    dagreGraph.setEdge(edge.source, edge.target);
  });

  dagre.layout(dagreGraph);

  const layoutedNodes = nodes.map((node) => {
    const nodeWithPosition = dagreGraph.node(node.id);
    return {
      ...node,
      position: {
        x: nodeWithPosition.x - nodeWidth / 2,
        y: nodeWithPosition.y - nodeHeight / 2,
      },
    };
  });

  return { nodes: layoutedNodes, edges };
};

interface TicketGraphProps {
  workflowId: string;
  onNavigateToSearchTab?: (tag: string) => void;
}

const TicketGraph: React.FC<TicketGraphProps> = ({ workflowId, onNavigateToSearchTab }) => {
  const [selectedTicketId, setSelectedTicketId] = useState<string | null>(null);
  const [layoutDirection, setLayoutDirection] = useState<LayoutDirection>('TB');
  const [showResolved, setShowResolved] = useState(true);
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);

  // Fetch tickets
  const { data: tickets, isLoading } = useQuery({
    queryKey: ['tickets', workflowId],
    queryFn: () => apiService.getTickets({ workflow_id: workflowId }),
    refetchInterval: 5000,
  });

  // Build graph data
  useEffect(() => {
    if (!tickets || !tickets.length) {
      setNodes([]);
      setEdges([]);
      return;
    }

    // Filter tickets based on showResolved
    const filteredTickets = showResolved
      ? tickets
      : tickets.filter((t) => !t.is_resolved);

    // Create nodes
    const newNodes: Node[] = filteredTickets.map((ticket) => ({
      id: ticket.id,
      type: 'ticketNode',
      data: {
        ticket,
        onClick: setSelectedTicketId,
      },
      position: { x: 0, y: 0 }, // Will be set by layout
    }));

    // Create edges from blocking relationships
    const newEdges: Edge[] = [];
    filteredTickets.forEach((ticket) => {
      if (ticket.blocked_by_ticket_ids && ticket.blocked_by_ticket_ids.length > 0) {
        ticket.blocked_by_ticket_ids.forEach((blockerId: string) => {
          // Only create edge if blocker is in filtered tickets
          if (filteredTickets.find((t) => t.id === blockerId)) {
            newEdges.push({
              id: `${blockerId}-${ticket.id}`,
              source: blockerId,
              target: ticket.id,
              label: 'blocks',
              type: 'smoothstep',
              animated: false,
              markerEnd: {
                type: MarkerType.ArrowClosed,
                width: 20,
                height: 20,
              },
              style: {
                strokeWidth: 2,
                stroke: '#ef4444', // red
              },
              labelStyle: {
                fontSize: 10,
                fill: '#6b7280',
              },
            });
          }
        });
      }
    });

    // Apply layout
    const { nodes: layoutedNodes, edges: layoutedEdges } = getLayoutedElements(
      newNodes,
      newEdges,
      layoutDirection
    );

    setNodes(layoutedNodes);
    setEdges(layoutedEdges);
  }, [tickets, showResolved, layoutDirection, setNodes, setEdges]);

  const onLayout = useCallback(
    (direction: LayoutDirection) => {
      setLayoutDirection(direction);
    },
    []
  );

  // Stats for display
  const stats = useMemo(() => {
    if (!tickets) {
      return { blockedCount: 0, blockersCount: 0, resolvedCount: 0, normalCount: 0 };
    }
    const blockedCount = tickets.filter((t) => t.is_blocked).length;
    const blockersCount = tickets.filter((t) => t.blocks_ticket_ids && t.blocks_ticket_ids.length > 0).length;
    const resolvedCount = tickets.filter((t) => t.is_resolved).length;
    const normalCount = tickets.length - blockedCount - blockersCount - resolvedCount;

    return { blockedCount, blockersCount, resolvedCount, normalCount };
  }, [tickets]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-[600px]">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  if (!tickets || !tickets.length) {
    return (
      <div className="flex items-center justify-center h-[600px] bg-gray-50 rounded-lg border-2 border-dashed border-gray-300">
        <div className="text-center">
          <p className="text-gray-500 text-lg mb-2">No tickets found</p>
          <p className="text-gray-400 text-sm">Create some tickets to see the dependency graph</p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-[700px] bg-gray-50 rounded-lg border relative">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        nodeTypes={nodeTypes}
        fitView
        attributionPosition="bottom-left"
        minZoom={0.1}
        maxZoom={2}
      >
        <Background />
        <Controls />
        <MiniMap
          nodeColor={(node) => {
            const ticket = node.data?.ticket;
            if (!ticket) return '#3b82f6';
            if (ticket.is_resolved) return '#22c55e';
            if (ticket.is_blocked) return '#ef4444';
            if (ticket.blocks_ticket_ids && ticket.blocks_ticket_ids.length > 0) return '#f97316';
            return '#3b82f6';
          }}
          maskColor="rgba(0, 0, 0, 0.1)"
          className="bg-white border rounded"
        />

        {/* Control Panel */}
        <Panel position="top-right" className="bg-white p-4 rounded-lg shadow-lg space-y-3">
          <div className="font-semibold text-sm text-gray-900 mb-2">Layout</div>
          <div className="flex space-x-2">
            <button
              onClick={() => onLayout('TB')}
              className={`px-3 py-1 text-xs rounded ${
                layoutDirection === 'TB'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              }`}
            >
              Top-Down
            </button>
            <button
              onClick={() => onLayout('LR')}
              className={`px-3 py-1 text-xs rounded ${
                layoutDirection === 'LR'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              }`}
            >
              Left-Right
            </button>
          </div>

          <div className="border-t pt-3">
            <label className="flex items-center space-x-2 cursor-pointer">
              <input
                type="checkbox"
                checked={showResolved}
                onChange={(e) => setShowResolved(e.target.checked)}
                className="rounded"
              />
              <span className="text-xs text-gray-700">Show Resolved</span>
            </label>
          </div>
        </Panel>

        {/* Legend Panel */}
        <Panel position="bottom-right" className="bg-white p-4 rounded-lg shadow-lg">
          <div className="font-semibold text-sm text-gray-900 mb-3">Legend</div>
          <div className="space-y-2 text-xs">
            <div className="flex items-center space-x-2">
              <CheckCircle className="w-4 h-4 text-green-600" />
              <span className="text-gray-700">Resolved ({stats.resolvedCount})</span>
            </div>
            <div className="flex items-center space-x-2">
              <Lock className="w-4 h-4 text-red-600" />
              <span className="text-gray-700">Blocked ({stats.blockedCount})</span>
            </div>
            <div className="flex items-center space-x-2">
              <AlertCircle className="w-4 h-4 text-orange-600" />
              <span className="text-gray-700">Blocks Others ({stats.blockersCount})</span>
            </div>
            <div className="flex items-center space-x-2">
              <Circle className="w-4 h-4 text-blue-600" />
              <span className="text-gray-700">Normal ({stats.normalCount})</span>
            </div>
          </div>
          <div className="mt-3 pt-3 border-t text-xs text-gray-500">
            Click node to view details<br />
            Drag to pan • Scroll to zoom
          </div>
        </Panel>
      </ReactFlow>

      {/* Ticket Detail Modal */}
      {selectedTicketId && (
        <TicketDetailModal
          ticketId={selectedTicketId}
          onClose={() => setSelectedTicketId(null)}
          onNavigateToSearchTab={onNavigateToSearchTab}
        />
      )}
    </div>
  );
};

export default TicketGraph;
