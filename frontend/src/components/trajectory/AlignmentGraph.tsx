import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceDot } from 'recharts';
import { Star } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';

interface TrajectoryPoint {
  timestamp: string;
  alignment_score: number;
  current_phase?: string;
  phase_changed?: boolean;
}

interface AlignmentGraphProps {
  trajectoryHistory: TrajectoryPoint[];
}

export default function AlignmentGraph({ trajectoryHistory }: AlignmentGraphProps) {
  if (!trajectoryHistory || trajectoryHistory.length === 0) {
    return (
      <div className="text-gray-500 text-center py-4">
        No trajectory data available
      </div>
    );
  }

  // Prepare data for chart
  const chartData = trajectoryHistory.map((point, index) => ({
    ...point,
    time: new Date(point.timestamp).getTime(),
    displayTime: formatDistanceToNow(new Date(point.timestamp), { addSuffix: true }),
    alignmentPercent: Math.round((point.alignment_score || 0) * 100),
    index
  }));

  // Custom dot for phase transitions
  const CustomDot = (props: any) => {
    const { cx, cy, payload } = props;
    if (!payload.phase_changed) return null;

    return (
      <g>
        <Star
          x={cx - 8}
          y={cy - 8}
          width={16}
          height={16}
          className="fill-yellow-400 stroke-yellow-600"
        />
      </g>
    );
  };

  // Custom tooltip
  const CustomTooltip = ({ active, payload }: any) => {
    if (!active || !payload || !payload[0]) return null;

    const data = payload[0].payload;

    return (
      <div className="bg-white border border-gray-200 rounded-lg shadow-lg p-3">
        <div className="text-sm font-medium text-gray-900">
          {data.displayTime}
        </div>
        <div className="text-sm text-gray-600 mt-1">
          Alignment: <span className="font-semibold">{data.alignmentPercent}%</span>
        </div>
        {data.phase_changed && data.current_phase && (
          <div className="text-sm text-yellow-600 mt-1 flex items-center">
            <Star className="w-3 h-3 mr-1" />
            Phase: {data.current_phase}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="w-full h-64">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart
          data={chartData}
          margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis
            dataKey="index"
            tick={false}
            axisLine={{ stroke: '#9ca3af' }}
          />
          <YAxis
            domain={[0, 100]}
            ticks={[0, 25, 50, 75, 100]}
            axisLine={{ stroke: '#9ca3af' }}
            tick={{ fontSize: 12 }}
            label={{ value: 'Alignment %', angle: -90, position: 'insideLeft', style: { fontSize: 12 } }}
          />
          <Tooltip content={<CustomTooltip />} />
          <Line
            type="monotone"
            dataKey="alignmentPercent"
            stroke="#3b82f6"
            strokeWidth={2}
            dot={<CustomDot />}
            activeDot={{ r: 6 }}
          />
          {/* Reference lines for alignment zones */}
          <line y1={80} y2={80} stroke="#10b981" strokeDasharray="3 3" opacity={0.3} />
          <line y1={40} y2={40} stroke="#f59e0b" strokeDasharray="3 3" opacity={0.3} />
        </LineChart>
      </ResponsiveContainer>

      {/* Legend */}
      <div className="flex items-center justify-center space-x-6 mt-2 text-xs">
        <div className="flex items-center">
          <div className="w-3 h-0.5 bg-blue-500 mr-1"></div>
          <span className="text-gray-600">Alignment Score</span>
        </div>
        <div className="flex items-center">
          <Star className="w-3 h-3 fill-yellow-400 stroke-yellow-600 mr-1" />
          <span className="text-gray-600">Phase Change</span>
        </div>
        <div className="flex items-center">
          <div className="w-3 h-0.5 bg-green-500 mr-1" style={{ borderStyle: 'dashed', borderWidth: '1px 0 0 0' }}></div>
          <span className="text-gray-600">Good (&gt;80%)</span>
        </div>
        <div className="flex items-center">
          <div className="w-3 h-0.5 bg-yellow-500 mr-1" style={{ borderStyle: 'dashed', borderWidth: '1px 0 0 0' }}></div>
          <span className="text-gray-600">Partial (&gt;40%)</span>
        </div>
      </div>
    </div>
  );
}