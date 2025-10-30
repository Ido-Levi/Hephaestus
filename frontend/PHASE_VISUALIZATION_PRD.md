# Phase Visualization - Product Requirements Document

## Executive Summary

This PRD outlines the frontend changes required to make workflow phases a first-class concept in the Hephaestus UI. The goal is to provide users with clear visibility into workflow progression, phase-based task organization, and cross-phase relationships.

## Goals & Objectives

### Primary Goals
1. **Visibility**: Users should instantly understand which phase tasks belong to and overall workflow progress
2. **Navigation**: Users should be able to filter and navigate tasks by phase
3. **Context**: Users should understand phase relationships and dependencies
4. **Monitoring**: Users should track phase progression and identify bottlenecks

### Success Metrics
- Users can identify task phases within 1 second
- Phase progression is clear without explanation
- Cross-phase task relationships are visually apparent

## Design System Updates

### Dynamic Phase Color System
Phases use a gradient system that works for any number of phases (2-10+):

```typescript
// Dynamic color generation based on phase order
function getPhaseColor(phaseOrder: number, totalPhases: number): string {
  const hue = (phaseOrder - 1) * (240 / Math.max(totalPhases - 1, 1)); // Spread across blue→purple→red spectrum
  const saturation = 70;
  const lightness = 50;
  return `hsl(${hue}, ${saturation}%, ${lightness}%)`;
}

// Alternative: Single color with opacity gradient
function getPhaseIntensity(phaseOrder: number, totalPhases: number): string {
  const opacity = 0.3 + (0.7 * ((phaseOrder - 1) / Math.max(totalPhases - 1, 1)));
  return `rgba(59, 130, 246, ${opacity})`; // Blue with varying intensity
}
```

**Design Decision**: Use subtle intensity gradient rather than different colors to maintain visual consistency and avoid rainbow effect.

### New Components

#### PhaseBadge Component
```
[P1: {name}] - Gradient intensity based on phase order
[P2: {name}] - Same base color, different intensity
```
- Compact design (height: 20px)
- Rounded corners (4px)
- Shows phase number and dynamic name
- Tooltip on hover with phase description
- Adjusts to any phase name length

#### PhaseActivity Component
```
Phase 1 ━━━━━━ Phase 2 ━━━━━━ Phase 3 ━━━━━━
 🤖 2 agents    🤖 5 agents    🤖 0 agents
 📋 15 tasks    📋 23 tasks    📋 3 tasks
```
- Horizontal timeline showing ACTIVITY not completion
- Real-time agent counts per phase
- No "complete" state (phases never fully complete)
- Click to view phase details

---

## Page Specifications

## 1. NEW PAGE: Phases Overview

### URL
`/phases`

### Purpose
Central hub for understanding workflow structure and phase progression

### Layout

```
┌─────────────────────────────────────────────────────────┐
│ Workflow: {Dynamic Workflow Name}           [Refresh] 🔄 │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Active Phase Distribution                             │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━        │
│  Phase 1     Phase 2     Phase 3     Phase N...        │
│  🤖 2/15    🤖 5/23     🤖 0/3      🤖 1/7            │
│  agents/tasks                                          │
│                                                         │
├─────────────────────────────────────────────────────────┤
│  Phase Cards (Horizontally scrollable for many phases) │
│  ←────────────────────────────────────────────────→   │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐     │
│  │  Phase 1    │ │  Phase 2    │ │  Phase N    │     │
│  │  {Name}     │ │  {Name}     │ │  {Name}     │     │
│  │             │ │             │ │             │     │
│  │ 🤖 Active:  │ │ 🤖 Active:  │ │ 🤖 Active:  │     │
│  │    2 agents │ │    5 agents │ │    0 agents │     │
│  │             │ │             │ │             │     │
│  │ 📋 Tasks:   │ │ 📋 Tasks:   │ │ 📋 Tasks:   │     │
│  │  Total: 15  │ │  Total: 23  │ │  Total: 3   │     │
│  │  Done: 10   │ │  Done: 18   │ │  Done: 0    │     │
│  │  Active: 5  │ │  Active: 5  │ │  Active: 3  │     │
│  │             │ │             │ │             │     │
│  │ [View Tasks]│ │ [View Tasks]│ │ [View Tasks]│     │
│  └─────────────┘ └─────────────┘ └─────────────┘     │
│                                                         │
│  Live Activity Feed (Auto-scrolling)                   │
│  ┌──────────────────────────────────────────────┐     │
│  │ ▼ Newest activities (real-time from Hephaestus)│     │
│  │ • [12:34:56] Agent-abc (P2) → task in P1      │     │
│  │ • [12:34:45] Agent-def (P1) → task in P3      │     │
│  │ • [12:34:30] Task completed in P2             │     │
│  │ • [12:34:15] Agent-ghi started in P4         │     │
│  │ • [12:34:00] Cross-phase: P3 → P1 task       │     │
│  │ ▲ [Load more...]                              │     │
│  └──────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────┘
```

### Features
1. **Workflow Header**: Dynamic workflow name (supports any workflow)
2. **Active Distribution Bar**: Visual representation of where activity is happening
3. **Phase Cards**: Real-time metrics per phase
   - **Active agent count** (primary metric)
   - Task counts (total, done, active)
   - No "completion" percentage (phases never complete)
   - Horizontally scrollable for 10+ phases
4. **Live Activity Feed**:
   - Real-time updates from Hephaestus WebSocket
   - Auto-scrolls with new activities
   - Shows cross-phase task creation
   - Timestamps for each activity
   - Load more for history

### User Interactions
- Click phase card → Navigate to Tasks page filtered by that phase
- Scroll horizontally → View additional phases (for workflows with many phases)
- Activity feed auto-updates → No manual refresh needed
- Click "Load more" → View older activities

### API Requirements
```typescript
GET /api/workflow
Response: {
  id: string;
  name: string;
  status: 'active' | 'completed' | 'paused';
  total_phases: number;
  phases: Phase[];
}

GET /api/phases
Response: Phase[]

interface Phase {
  id: string;
  order: number;
  name: string;
  description: string;
  // No "status" field - phases are always active
  active_agents: number;  // Currently working agents
  total_tasks: number;
  completed_tasks: number;
  active_tasks: number;
  pending_tasks: number;
}

// WebSocket events for activity feed
interface PhaseActivity {
  type: 'cross_phase_task' | 'task_completed' | 'agent_started' | 'agent_stopped';
  timestamp: string;
  from_phase?: number;
  to_phase?: number;
  agent_id?: string;
  task_id?: string;
  description: string;
}
```

### Done Definition
- [ ] Page loads and displays current workflow
- [ ] Phase timeline shows correct progression
- [ ] Phase cards show accurate task counts
- [ ] Clicking phase card navigates to filtered Tasks view
- [ ] Real-time updates when phase status changes
- [ ] Activity feed shows last 5 cross-phase activities

---

## 2. UPDATED PAGE: Tasks

### Current State
Shows list of tasks with status, priority, and basic metadata

### Proposed Changes

#### Visual Updates
```
Before:
[Task Description] [Status Badge] [Priority]

After:
[Task Description] [Phase 1: Planning] [Status Badge] [Priority]
                   ^^^^^^^^^^^^^^^^^ New phase badge
```

#### New Filtering Options
```
┌────────────────────────────────────────────┐
│ Filter by:                                 │
│ [All Phases ▼] [All Status ▼] [All Priority ▼] │
│  └─ Phase 1: Planning                      │
│  └─ Phase 2: Implementation                │
│  └─ Phase 3: Validation                    │
└────────────────────────────────────────────┘
```

#### Grouping Option
```
[✓] Group by Phase

Phase 1: Planning (12 tasks)
├── Design database schema [done] [high]
├── Create API specification [in_progress] [high]
└── ...

Phase 2: Implementation (8 tasks)
├── Implement auth endpoints [assigned] [medium]
└── ...
```

### Implementation Details

1. **Add to Task interface**:
```typescript
interface Task {
  // ... existing fields
  phase_id: string | null;
  phase_name: string | null;
  phase_order: number | null;
  workflow_id: string | null;
}
```

2. **PhaseBadge placement**: Between task title and status badge
3. **Filter persistence**: Save filter state in URL params
4. **Sorting**: Allow sort by phase_order

### Done Definition
- [ ] Phase badge appears on all tasks with phase assignment
- [ ] Phase filter dropdown works correctly
- [ ] Group by phase toggle functions
- [ ] URL updates when filters change
- [ ] Tasks without phases show "No Phase" badge
- [ ] Phase badges use correct color coding

---

## 3. UPDATED PAGE: Graph

### Current State
Shows nodes for agents and tasks with basic relationships

### Proposed Changes

#### Phase Swimlanes Layout
```
┌─────────────────────────────────────────────────────┐
│ Phase 1: Planning          │ ← Blue background tint │
│  ┌──────┐    ┌──────┐     │                       │
│  │Task 1│───►│Task 2│      │                       │
│  └──────┘    └──────┘      │                       │
├─────────────────────────────────────────────────────┤
│ Phase 2: Implementation    │ ← Green background    │
│     ┌──────┐               │                       │
│     │Task 3│◄──────────────│ Cross-phase edge     │
│     └──────┘               │ (dashed line)        │
├─────────────────────────────────────────────────────┤
│ Phase 3: Validation        │ ← Purple background   │
│     (empty)                │                       │
└─────────────────────────────────────────────────────┘
```

#### Node Enhancements
- Border color matches phase color
- Phase number shown in node (small badge)
- Tooltip includes phase information

#### Legend Component
```
┌──────────────────┐
│ Legend           │
│ ● Phase 1 (Blue) │
│ ● Phase 2 (Green)│
│ ● Phase 3 (Purple)│
│ --- Cross-phase  │
│ ─── Same-phase   │
└──────────────────┘
```

### Implementation Details

1. **Update GraphNode interface**:
```typescript
interface GraphNode {
  // ... existing fields
  phase_id?: string;
  phase_name?: string;
  phase_order?: number;
  phase_color?: string;
}
```

2. **Layout Algorithm**:
   - Organize nodes vertically by phase
   - Maintain phase order top-to-bottom
   - Highlight cross-phase edges differently

3. **Interactive Features**:
   - Click legend item to highlight/dim that phase
   - Zoom to phase on double-click
   - Show phase statistics on hover

### Done Definition
- [ ] Graph shows horizontal swimlanes for each phase
- [ ] Nodes are colored by their phase
- [ ] Cross-phase edges use dashed lines
- [ ] Legend shows all phases with correct colors
- [ ] Clicking legend filters visible nodes
- [ ] Empty phases show placeholder text
- [ ] Phase boundaries are clearly visible

---

## 4. UPDATED PAGE: Dashboard

### Current State
Shows overall system statistics and recent activity

### Proposed Changes

#### New Phase Progress Widget
```
┌─────────────────────────────────────────┐
│ Workflow Progress                       │
│                                         │
│ Simple Project                          │
│ ════════════════════░░░░░░░  66%       │
│                                         │
│ ✓ Phase 1: Planning      (Complete)    │
│ ◉ Phase 2: Implementation (Active)     │
│ ○ Phase 3: Validation    (Pending)     │
│                                         │
│ 20 total tasks | 15 complete | 5 active│
│                                         │
│ [View Phases →]                         │
└─────────────────────────────────────────┘
```

Position: Top-right of dashboard, below connection status

### Implementation Details

1. **Add to DashboardStats interface**:
```typescript
interface DashboardStats {
  // ... existing fields
  workflow?: {
    id: string;
    name: string;
    completion_percentage: number;
    phases: PhaseStatus[];
  };
}

interface PhaseStatus {
  order: number;
  name: string;
  status: 'pending' | 'active' | 'completed';
  task_count: number;
  completed_count: number;
}
```

### Done Definition
- [ ] Widget shows current workflow name
- [ ] Overall progress bar is accurate
- [ ] Phase list shows correct status icons
- [ ] Task counts are accurate and real-time
- [ ] Click "View Phases" navigates to /phases
- [ ] Widget handles no-workflow state gracefully

---

## 5. UPDATED PAGE: Agents

### Current State
Shows agent cards with status and current task

### Proposed Changes

#### Agent Card Enhancement
Add phase context to agent cards:
```
┌─────────────────────────┐
│ Agent abc123            │
│ Status: Working         │
│ Current Task: xyz789    │
│ Working in: Phase 2 🟢  │ ← New
└─────────────────────────┘
```

### Done Definition
- [ ] Agent cards show current task's phase
- [ ] Phase indicator uses correct color
- [ ] Agents without tasks show "No phase"

---

## Navigation Updates

### Menu Structure
```
Dashboard
Tasks
Agents
Phases      ← New menu item (with phase icon)
Memories
Graph
```

### Icon Selection
Use `Layers` icon from lucide-react for Phases menu item

---

## WebSocket Events

### New Event Types
```typescript
interface PhaseTransitionEvent {
  type: 'phase_transition';
  phase_id: string;
  from_status: string;
  to_status: string;
  workflow_id: string;
}

interface CrossPhaseTaskEvent {
  type: 'cross_phase_task';
  from_phase: number;
  to_phase: number;
  task_id: string;
  agent_id: string;
}
```

---

## Performance Considerations

1. **Phase data caching**: Cache phase structure (changes rarely)
2. **Lazy loading**: Load phase details only when Phases tab is visited
3. **Batch updates**: Group multiple phase-related WebSocket events
4. **Virtualization**: Use virtualization for large task lists grouped by phase

---

## Accessibility

1. **Color coding**: Don't rely solely on color - include text labels
2. **ARIA labels**: Add descriptive labels for phase indicators
3. **Keyboard navigation**: Support tab navigation through phase timeline
4. **Screen readers**: Announce phase transitions and progress

---

## Mobile Responsiveness

1. **Phase badges**: Collapse to just number on mobile (P1, P2, P3)
2. **Timeline**: Convert to vertical on narrow screens
3. **Graph**: Provide pan/zoom controls for phase swimlanes
4. **Cards**: Stack phase cards vertically on mobile

---

## Testing Requirements

### Unit Tests
- [ ] PhaseBadge component renders correctly
- [ ] Phase filtering logic works
- [ ] Phase color mapping is correct

### Integration Tests
- [ ] Phase data loads from API
- [ ] Cross-phase navigation works
- [ ] WebSocket updates trigger re-renders

### E2E Tests
- [ ] User can navigate through phase workflow
- [ ] Filtering by phase persists across navigation
- [ ] Real-time updates appear without refresh

---

## Rollout Plan

### Phase 1: Foundation (Week 1)
- [ ] Create type definitions
- [ ] Build PhaseBadge component
- [ ] Add API endpoints
- [ ] Update existing types

### Phase 2: Core Pages (Week 2)
- [ ] Implement Phases page
- [ ] Update Tasks page with badges
- [ ] Add phase filtering

### Phase 3: Enhancements (Week 3)
- [ ] Update Graph with swimlanes
- [ ] Add Dashboard widget
- [ ] Enhance Agent cards
- [ ] WebSocket integration

### Phase 4: Polish (Week 4)
- [ ] Performance optimization
- [ ] Mobile responsiveness
- [ ] Accessibility improvements
- [ ] Documentation

---

## Success Criteria

The implementation is considered successful when:

1. **Clarity**: Users can identify task phases at a glance
2. **Navigation**: Users can filter and find tasks by phase efficiently
3. **Understanding**: Users comprehend workflow progression without training
4. **Performance**: Phase features don't degrade app performance
5. **Consistency**: Phase visualization is consistent across all pages

---

## Future Enhancements

1. **Phase Templates**: Save and reuse phase structures
2. **Phase Analytics**: Time spent per phase, bottleneck identification
3. **Phase Automation**: Auto-transition rules based on completion
4. **Phase Dependencies**: Visual dependency mapping between phases
5. **Multi-workflow Support**: Compare phases across workflows
6. **Phase History**: Track phase transitions over time
7. **Custom Phase Icons**: Allow custom icons per phase type

---

## Appendix: Design Mockups

### Color Reference
```css
/* Phase Colors */
--phase-1-blue: #3B82F6;
--phase-1-bg: #EFF6FF;
--phase-2-green: #10B981;
--phase-2-bg: #F0FDF4;
--phase-3-purple: #8B5CF6;
--phase-3-bg: #F3E8FF;
--phase-4-orange: #F97316;
--phase-4-bg: #FFF7ED;
```

### Component Library
- React Flow for graph visualization
- Framer Motion for phase transitions
- Tailwind CSS for styling
- Lucide React for icons
- React Query for data fetching

---

This PRD serves as the definitive guide for implementing phase visualization in Hephaestus frontend.