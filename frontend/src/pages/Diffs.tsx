import DiffResolutionPanel from '@/components/DiffResolutionPanel';
import ExecutionSelector from '@/components/ExecutionSelector';

export default function Diffs() {
  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <ExecutionSelector />
      </div>
      <DiffResolutionPanel />
    </div>
  );
}
