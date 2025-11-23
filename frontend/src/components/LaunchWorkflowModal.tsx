import React, { useState, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Rocket,
  ChevronRight,
  ChevronLeft,
  AlertCircle,
  CheckCircle,
  Play,
  FileText,
} from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { apiService } from '@/services/api';
import {
  WorkflowDefinition,
  LaunchTemplate,
  LaunchParameter,
} from '@/types';

interface LaunchWorkflowModalProps {
  open: boolean;
  onClose: () => void;
  onLaunch: (workflowId: string) => void;
}

type Step = 'select' | 'form' | 'preview';

const LaunchWorkflowModal: React.FC<LaunchWorkflowModalProps> = ({
  open,
  onClose,
  onLaunch,
}) => {
  const [step, setStep] = useState<Step>('select');
  const [selectedDefinition, setSelectedDefinition] = useState<WorkflowDefinition | null>(null);
  const [executionName, setExecutionName] = useState('');
  const [formValues, setFormValues] = useState<Record<string, any>>({});
  const [isLaunching, setIsLaunching] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Fetch workflow definitions
  const { data: definitions = [], isLoading } = useQuery<WorkflowDefinition[]>({
    queryKey: ['workflow-definitions'],
    queryFn: apiService.listWorkflowDefinitions,
    enabled: open,
  });

  // Initialize form values when a definition is selected
  const initializeFormValues = (template: LaunchTemplate | null | undefined) => {
    if (!template) {
      setFormValues({});
      return;
    }
    const initial: Record<string, any> = {};
    template.parameters.forEach((param) => {
      initial[param.name] = param.default ?? (param.type === 'boolean' ? false : '');
    });
    setFormValues(initial);
  };

  const handleSelectDefinition = (def: WorkflowDefinition) => {
    setSelectedDefinition(def);
    setExecutionName('');
    initializeFormValues(def.launch_template);
    setError(null);

    // If no launch template, go directly to preview with just execution name
    if (!def.launch_template || def.launch_template.parameters.length === 0) {
      setStep('form'); // Still need form for execution name
    } else {
      setStep('form');
    }
  };

  const handleFormValueChange = (name: string, value: any) => {
    setFormValues((prev) => ({ ...prev, [name]: value }));
  };

  const validateForm = (): boolean => {
    if (!executionName.trim()) {
      setError('Execution name is required');
      return false;
    }

    if (selectedDefinition?.launch_template) {
      for (const param of selectedDefinition.launch_template.parameters) {
        if (param.required && !formValues[param.name] && formValues[param.name] !== false) {
          setError(`${param.label} is required`);
          return false;
        }
      }
    }

    setError(null);
    return true;
  };

  const handleProceedToPreview = () => {
    if (validateForm()) {
      setStep('preview');
    }
  };

  // Substitute parameters in a template string
  const substituteParams = (template: string, params: Record<string, any>): string => {
    let result = template;
    for (const [key, value] of Object.entries(params)) {
      result = result.replace(new RegExp(`\\{${key}\\}`, 'g'), String(value ?? ''));
    }
    return result;
  };

  const previewTaskPrompt = useMemo(() => {
    if (!selectedDefinition?.launch_template?.phase_1_task_prompt) {
      return null;
    }
    return substituteParams(selectedDefinition.launch_template.phase_1_task_prompt, formValues);
  }, [selectedDefinition, formValues]);

  const handleLaunch = async () => {
    if (!selectedDefinition) return;

    setIsLaunching(true);
    setError(null);

    try {
      const result = await apiService.startWorkflowExecution(
        selectedDefinition.id,
        executionName,
        undefined, // working_directory - using default
        Object.keys(formValues).length > 0 ? formValues : undefined
      );

      onLaunch(result.workflow_id);
      handleClose();
    } catch (err: any) {
      setError(err.message || 'Failed to launch workflow');
    } finally {
      setIsLaunching(false);
    }
  };

  const handleClose = () => {
    setStep('select');
    setSelectedDefinition(null);
    setExecutionName('');
    setFormValues({});
    setError(null);
    setIsLaunching(false);
    onClose();
  };

  const renderParameterInput = (param: LaunchParameter) => {
    const value = formValues[param.name];

    switch (param.type) {
      case 'text':
        return (
          <input
            type="text"
            value={value || ''}
            onChange={(e) => handleFormValueChange(param.name, e.target.value)}
            className="w-full px-3 py-2 border rounded-md bg-white dark:bg-gray-800 border-gray-300 dark:border-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder={param.description || `Enter ${param.label.toLowerCase()}`}
          />
        );

      case 'textarea':
        return (
          <textarea
            value={value || ''}
            onChange={(e) => handleFormValueChange(param.name, e.target.value)}
            rows={4}
            className="w-full px-3 py-2 border rounded-md bg-white dark:bg-gray-800 border-gray-300 dark:border-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500 resize-y"
            placeholder={param.description || `Enter ${param.label.toLowerCase()}`}
          />
        );

      case 'number':
        return (
          <input
            type="number"
            value={value || ''}
            onChange={(e) => handleFormValueChange(param.name, e.target.valueAsNumber || '')}
            className="w-full px-3 py-2 border rounded-md bg-white dark:bg-gray-800 border-gray-300 dark:border-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder={param.description || `Enter ${param.label.toLowerCase()}`}
          />
        );

      case 'boolean':
        return (
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={value || false}
              onChange={(e) => handleFormValueChange(param.name, e.target.checked)}
              className="w-4 h-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
            <span className="text-sm text-gray-600 dark:text-gray-400">
              {param.description || 'Enable'}
            </span>
          </label>
        );

      case 'select':
      case 'dropdown':
        return (
          <select
            value={value || ''}
            onChange={(e) => handleFormValueChange(param.name, e.target.value)}
            className="w-full px-3 py-2 border rounded-md bg-white dark:bg-gray-800 border-gray-300 dark:border-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">Select {param.label.toLowerCase()}</option>
            {param.options?.map((option) => (
              <option key={option} value={option}>
                {option}
              </option>
            ))}
          </select>
        );

      default:
        return null;
    }
  };

  const renderStepContent = () => {
    switch (step) {
      case 'select':
        return (
          <div className="space-y-4">
            <DialogDescription>
              Select a workflow definition to start a new execution.
            </DialogDescription>

            {isLoading ? (
              <div className="flex items-center justify-center py-8">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500" />
              </div>
            ) : definitions.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                No workflow definitions available.
              </div>
            ) : (
              <ScrollArea className="h-[400px] pr-4">
                <div className="space-y-2">
                  {definitions.map((def) => (
                    <button
                      key={def.id}
                      onClick={() => handleSelectDefinition(def)}
                      className="w-full p-4 text-left border rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <h3 className="font-medium text-gray-900 dark:text-white">
                            {def.name}
                          </h3>
                          {def.description && (
                            <p className="text-sm text-gray-500 mt-1">{def.description}</p>
                          )}
                          <div className="flex items-center gap-2 mt-2">
                            <Badge variant="outline">{def.phases_count} phases</Badge>
                            {def.launch_template && (
                              <Badge variant="secondary">
                                {def.launch_template.parameters.length} inputs
                              </Badge>
                            )}
                            {def.has_result && (
                              <Badge className="bg-green-100 text-green-800">
                                Produces result
                              </Badge>
                            )}
                          </div>
                        </div>
                        <ChevronRight className="w-5 h-5 text-gray-400" />
                      </div>
                    </button>
                  ))}
                </div>
              </ScrollArea>
            )}
          </div>
        );

      case 'form':
        return (
          <div className="space-y-4">
            <DialogDescription>
              Configure your workflow execution for <strong>{selectedDefinition?.name}</strong>.
            </DialogDescription>

            <ScrollArea className="h-[450px] pr-4">
              <div className="space-y-4">
                {/* Execution Name - Always Required */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Execution Name <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    value={executionName}
                    onChange={(e) => setExecutionName(e.target.value)}
                    className="w-full px-3 py-2 border rounded-md bg-white dark:bg-gray-800 border-gray-300 dark:border-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="e.g., My URL Shortener Project"
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    A unique name to identify this workflow execution
                  </p>
                </div>

                {/* Dynamic Parameters from Launch Template */}
                {selectedDefinition?.launch_template?.parameters.map((param) => (
                  <div key={param.name}>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      {param.label}
                      {param.required && <span className="text-red-500"> *</span>}
                    </label>
                    {renderParameterInput(param)}
                    {param.description && param.type !== 'boolean' && (
                      <p className="text-xs text-gray-500 mt-1">{param.description}</p>
                    )}
                  </div>
                ))}
              </div>
            </ScrollArea>

            {error && (
              <div className="flex items-center gap-2 text-red-500 text-sm">
                <AlertCircle className="w-4 h-4" />
                {error}
              </div>
            )}
          </div>
        );

      case 'preview':
        return (
          <div className="space-y-4">
            <DialogDescription>
              Review your configuration before launching.
            </DialogDescription>

            <ScrollArea className="h-[450px] pr-4">
              <div className="space-y-4">
                {/* Summary */}
                <div className="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
                  <h4 className="font-medium text-gray-900 dark:text-white mb-2">
                    Execution Summary
                  </h4>
                  <dl className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <dt className="text-gray-500">Workflow:</dt>
                      <dd className="font-medium">{selectedDefinition?.name}</dd>
                    </div>
                    <div className="flex justify-between">
                      <dt className="text-gray-500">Execution Name:</dt>
                      <dd className="font-medium">{executionName}</dd>
                    </div>
                    <div className="flex justify-between">
                      <dt className="text-gray-500">Phases:</dt>
                      <dd className="font-medium">{selectedDefinition?.phases_count}</dd>
                    </div>
                  </dl>
                </div>

                {/* Parameter Values */}
                {selectedDefinition?.launch_template && Object.keys(formValues).length > 0 && (
                  <div className="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
                    <h4 className="font-medium text-gray-900 dark:text-white mb-2">
                      Input Parameters
                    </h4>
                    <dl className="space-y-2 text-sm">
                      {selectedDefinition.launch_template.parameters.map((param) => (
                        <div key={param.name}>
                          <dt className="text-gray-500">{param.label}:</dt>
                          <dd className="font-medium mt-1 pl-2 border-l-2 border-blue-300">
                            {param.type === 'boolean'
                              ? (formValues[param.name] ? 'Yes' : 'No')
                              : (formValues[param.name] || <span className="text-gray-400 italic">Not provided</span>)
                            }
                          </dd>
                        </div>
                      ))}
                    </dl>
                  </div>
                )}

                {/* Phase 1 Task Preview */}
                {previewTaskPrompt && (
                  <div className="p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                    <h4 className="font-medium text-blue-900 dark:text-blue-100 mb-2 flex items-center gap-2">
                      <FileText className="w-4 h-4" />
                      Phase 1 Initial Task
                    </h4>
                    <p className="text-sm text-blue-800 dark:text-blue-200 whitespace-pre-wrap">
                      {previewTaskPrompt}
                    </p>
                  </div>
                )}
              </div>
            </ScrollArea>

            {error && (
              <div className="flex items-center gap-2 text-red-500 text-sm">
                <AlertCircle className="w-4 h-4" />
                {error}
              </div>
            )}
          </div>
        );
    }
  };

  const renderFooter = () => {
    switch (step) {
      case 'select':
        return (
          <Button variant="outline" onClick={handleClose}>
            Cancel
          </Button>
        );

      case 'form':
        return (
          <div className="flex justify-between w-full">
            <Button variant="outline" onClick={() => setStep('select')}>
              <ChevronLeft className="w-4 h-4 mr-1" />
              Back
            </Button>
            <Button onClick={handleProceedToPreview}>
              Preview
              <ChevronRight className="w-4 h-4 ml-1" />
            </Button>
          </div>
        );

      case 'preview':
        return (
          <div className="flex justify-between w-full">
            <Button variant="outline" onClick={() => setStep('form')}>
              <ChevronLeft className="w-4 h-4 mr-1" />
              Back
            </Button>
            <Button
              onClick={handleLaunch}
              disabled={isLaunching}
              className="bg-green-600 hover:bg-green-700"
            >
              {isLaunching ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2" />
                  Launching...
                </>
              ) : (
                <>
                  <Play className="w-4 h-4 mr-1" />
                  Launch Workflow
                </>
              )}
            </Button>
          </div>
        );
    }
  };

  return (
    <Dialog open={open} onOpenChange={(open) => !open && handleClose()}>
      <DialogContent className="max-w-3xl">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Rocket className="w-5 h-5 text-blue-500" />
            {step === 'select' && 'Launch New Workflow'}
            {step === 'form' && 'Configure Workflow'}
            {step === 'preview' && 'Review & Launch'}
          </DialogTitle>
        </DialogHeader>

        {renderStepContent()}

        <DialogFooter>{renderFooter()}</DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

export default LaunchWorkflowModal;
