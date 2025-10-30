# Hephaestus Monitoring Architecture - Implementation Deep Dive

> **📚 Looking for the user guide?** This is a technical deep-dive for contributors and advanced users. If you want to understand how Guardian works from a user perspective, see [Guardian Monitoring Guide](../guides/guardian-monitoring.md).

## System Architecture Overview

```mermaid
graph TB
    subgraph "External Systems"
        MCP[MCP Client<br/>Claude Code]
        UI[Frontend<br/>React Dashboard]
    end

    subgraph "Monitoring Service"
        ML[Monitoring Loop<br/>run_monitor.py]
        TC[Trajectory Context<br/>Builder]
        PL[Prompt Loader<br/>Templates]
    end

    subgraph "Analysis Layer"
        direction LR
        G[Guardian<br/>Agent Analysis]
        C[Conductor<br/>System Analysis]
    end

    subgraph "Intelligence Layer"
        GPT[GPT-5 API<br/>OpenAI/Anthropic]
    end

    subgraph "Agent Layer"
        AM[Agent Manager]
        A1[Agent 1<br/>tmux session]
        A2[Agent 2<br/>tmux session]
        A3[Agent N<br/>tmux session]
    end

    subgraph "Data Layer"
        DB[(SQLite Database)]
        VDB[(Qdrant<br/>Vector Store)]
    end

    MCP --> ML
    UI --> DB
    ML --> G & C
    TC --> G
    PL --> G & C
    G --> GPT
    C --> GPT
    G --> AM
    C --> AM
    AM --> A1 & A2 & A3
    G & C --> DB
    TC --> DB
    G --> VDB

    style ML fill:#f9f,stroke:#333,stroke-width:4px
    style G fill:#9f9,stroke:#333,stroke-width:2px
    style C fill:#99f,stroke:#333,stroke-width:2px
    style GPT fill:#ff9,stroke:#333,stroke-width:2px
    style DB fill:#f99,stroke:#333,stroke-width:2px
```

## Component Details

### Monitoring Loop
- **Location**: `run_monitor.py`, `src/monitoring/monitor.py`
- **Responsibility**: Orchestrates the monitoring cycle every 60 seconds
- **Key Methods**:
  - `_monitoring_cycle()`: Main cycle execution
  - `_guardian_analysis_for_agent()`: Individual agent analysis
  - `_save_conductor_analysis()`: System analysis persistence

### Guardian System
- **Location**: `src/monitoring/guardian.py`
- **Responsibility**: Individual agent trajectory monitoring
- **Key Features**:
  - Grace period for new agents (default: 60 seconds) before monitoring begins
  - Builds accumulated context from entire conversation
  - Retrieves and uses past summaries for continuity
  - Calls GPT-5 for intelligent trajectory analysis
  - Provides targeted steering interventions

### Conductor System
- **Location**: `src/monitoring/conductor.py`
- **Responsibility**: System-wide coherence and orchestration
- **Key Features**:
  - Analyzes all Guardian summaries collectively
  - Detects duplicate work across agents
  - Makes termination and coordination decisions
  - Maintains system coherence score

### Trajectory Context Builder
- **Location**: `src/monitoring/trajectory_context.py`
- **Responsibility**: Extracts meaningful context from agent history
- **Key Extractions**:
  - Overall goals and their evolution
  - Persistent and lifted constraints
  - Standing instructions
  - Current focus and blockers

### Prompt Loader
- **Location**: `src/monitoring/prompt_loader.py`, `src/prompts/`
- **Responsibility**: Manages GPT-5 prompt templates
- **Templates**:
  - `guardian_trajectory_analysis.md` - Guardian agent analysis prompts
  - `conductor_system_analysis.md` - Conductor system analysis prompts
- **Key Features**:
  - Dynamic template loading from markdown files
  - Context injection using Python `.format()`
  - Structured JSON response formatting

## Data Flow

```mermaid
sequenceDiagram
    participant Timer
    participant Monitor
    participant DB
    participant Guardian
    participant GPT5
    participant Agent
    participant Conductor

    Timer->>Monitor: Every 60 seconds
    Monitor->>DB: Get active agents

    loop For each agent
        Monitor->>Guardian: Analyze agent
        Guardian->>DB: Get past summaries
        Guardian->>DB: Get agent logs
        Guardian->>Guardian: Build accumulated context
        Guardian->>GPT5: Send context + prompt
        GPT5-->>Guardian: Trajectory analysis
        Guardian->>DB: Save to guardian_analyses

        alt Needs steering
            Guardian->>Agent: Send intervention
            Guardian->>DB: Save to steering_interventions
        end

        Guardian-->>Monitor: Return summary
    end

    Monitor->>Conductor: All Guardian summaries
    Conductor->>GPT5: System coherence check
    GPT5-->>Conductor: System analysis
    Conductor->>DB: Save to conductor_analyses

    alt Duplicates detected
        Conductor->>DB: Save to detected_duplicates
        Conductor->>Agent: Terminate duplicate
    end

    alt Low coherence
        Conductor->>Monitor: Escalate issue
    end
```

## Database Schema

```mermaid
erDiagram
    agents ||--o{ agent_logs : generates
    agents ||--o{ guardian_analyses : monitored_by
    agents ||--o{ steering_interventions : receives
    tasks ||--o{ agents : assigned_to
    guardian_analyses ||--o| steering_interventions : triggers
    conductor_analyses ||--o{ detected_duplicates : identifies

    agents {
        string id PK
        string status
        string tmux_session_name
        string current_task_id FK
        datetime last_activity
        int health_check_failures
    }

    guardian_analyses {
        int id PK
        string agent_id FK
        datetime timestamp
        string current_phase
        boolean trajectory_aligned
        float alignment_score "0.0-1.0"
        boolean needs_steering
        string steering_type
        text trajectory_summary
        json details
    }

    conductor_analyses {
        int id PK
        datetime timestamp
        float coherence_score "0.0-1.0"
        int num_agents
        text system_status
        int duplicate_count
        json details
    }

    detected_duplicates {
        int id PK
        int conductor_analysis_id FK
        string agent1_id FK
        string agent2_id FK
        float similarity_score "0.0-1.0"
        text work_description
    }

    steering_interventions {
        int id PK
        string agent_id FK
        int guardian_analysis_id FK
        string steering_type
        text message
        boolean was_successful
    }
```

## Monitoring Cycle Phases

```mermaid
stateDiagram-v2
    [*] --> Initialize
    Initialize --> BuildContext: For each agent

    state "Guardian Phase" as guardian {
        BuildContext --> RetrieveSummaries
        RetrieveSummaries --> CallGPT5
        CallGPT5 --> AnalyzeTrajectory
        AnalyzeTrajectory --> CheckAlignment

        CheckAlignment --> SteerAgent: Needs steering
        CheckAlignment --> SaveAnalysis: Aligned
        SteerAgent --> SaveAnalysis
    }

    SaveAnalysis --> CollectSummaries: All agents done

    state "Conductor Phase" as conductor {
        CollectSummaries --> SystemAnalysis
        SystemAnalysis --> CallGPT5System
        CallGPT5System --> CheckCoherence
        CheckCoherence --> DetectDuplicates

        DetectDuplicates --> MakeDecisions: Issues found
        DetectDuplicates --> SaveSystemAnalysis: No issues
        MakeDecisions --> ExecuteDecisions
        ExecuteDecisions --> SaveSystemAnalysis
    }

    SaveSystemAnalysis --> CleanupSessions
    CleanupSessions --> Wait60s
    Wait60s --> BuildContext
```

## Key Algorithms

### Accumulated Context Building

```python
def build_accumulated_context(agent_id: str) -> Dict[str, Any]:
    """
    Builds complete context from agent's entire session.

    1. Get all agent logs ordered by time
    2. Extract overall goal from task and conversation
    3. Track goal evolution through conversation
    4. Extract persistent constraints ("must", "cannot")
    5. Identify lifted constraints
    6. Extract standing instructions ("always", "remember")
    7. Identify current focus (most recent activity)
    8. Discover blockers from errors and stuck patterns
    9. Calculate session duration and conversation length

    Returns structured context for GPT-5 analysis.
    """
```

### Trajectory Alignment Scoring

```python
def calculate_alignment_score(
    trajectory: Dict[str, Any],
    goal: str,
    constraints: List[str]
) -> float:
    """
    GPT-5 calculates alignment score (0.0-1.0) based on:

    - Goal progress (0-40%):
      * How much of the goal is completed
      * Whether work contributes to goal

    - Constraint adherence (0-30%):
      * Following active constraints
      * Not violating any constraints

    - Efficiency (0-20%):
      * Not stuck or repeating
      * Making forward progress

    - Focus (0-10%):
      * Staying on current task
      * Not context switching

    The score is determined by GPT-5's analysis of the agent's
    trajectory_summary against the accumulated_goal and constraints.
    """
```

### Duplicate Detection

```python
def detect_duplicates(
    summaries: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    GPT-5 detects duplicates by analyzing:

    1. Work descriptions similarity
    2. File/component overlap
    3. Goal similarity
    4. Approach similarity

    Returns list of duplicate pairs with similarity scores.
    """
```

## Performance Metrics

```mermaid
graph LR
    subgraph "Monitoring Metrics"
        M1[Cycle Time<br/>Target: <5s]
        M2[GPT-5 Latency<br/>Target: <3s]
        M3[DB Operations<br/>Target: <500ms]
    end

    subgraph "System Metrics"
        S1[Coherence Score<br/>Target: >0.7]
        S2[Duplicate Rate<br/>Target: <5%]
        S3[Intervention Success<br/>Target: >80%]
    end

    subgraph "Agent Metrics"
        A1[Alignment Score<br/>Target: >0.8]
        A2[Steering Rate<br/>Target: <20%]
        A3[Completion Rate<br/>Target: >90%]
    end
```

## Configuration Parameters

```yaml
# Monitoring Settings
monitoring:
  interval_seconds: 60                 # How often to run monitoring cycle
  parallel_analysis: true              # Analyze agents in parallel
  max_concurrent: 10                   # Max concurrent Guardian analyses
  guardian_min_agent_age_seconds: 60   # Grace period before Guardian monitors new agents

# Guardian Settings
guardian:
  past_summaries_limit: 10    # Number of past summaries to include
  context_history_lines: 200  # Lines of conversation to include
  tmux_output_lines: 100      # Lines from tmux to analyze
  cache_duration_minutes: 5   # How long to cache summaries

# Conductor Settings
conductor:
  min_agents_for_analysis: 2  # Minimum agents for system analysis
  duplicate_threshold: 0.8    # Similarity score for duplicates
  coherence_thresholds:
    critical: 0.3             # Below this triggers escalation
    warning: 0.5              # Below this increases monitoring
    healthy: 0.7              # Above this is normal

# Intervention Settings
interventions:
  max_nudges_before_restart: 3
  restart_cooldown_minutes: 10
  steering_types:
    - general
    - stuck
    - confused
    - wrong_direction
    - violating_constraints
```

## Integration Points

### MCP Server Endpoints

```python
# Get agent trajectories
GET /api/agent_trajectories
Response: {
    "agents": [
        {
            "agent_id": "uuid",
            "current_phase": "implementation",
            "alignment_score": 0.85,
            "trajectory_summary": "Building auth..."
        }
    ]
}

# Get system coherence
GET /api/system_coherence
Response: {
    "coherence_score": 0.75,
    "active_agents": 5,
    "duplicates": 1,
    "system_status": "Healthy with minor duplicates"
}

# Manual steering
POST /api/steer_agent
Body: {
    "agent_id": "uuid",
    "steering_type": "stuck",
    "message": "Try using X approach"
}
```

### Frontend Dashboard Integration

```typescript
// Real-time monitoring data
interface MonitoringData {
    agents: AgentTrajectory[];
    systemCoherence: number;
    duplicates: Duplicate[];
    interventions: Intervention[];
}

// WebSocket updates
ws.on('monitoring_update', (data: MonitoringData) => {
    updateAgentGrid(data.agents);
    updateCoherenceChart(data.systemCoherence);
    highlightDuplicates(data.duplicates);
});
```

## Troubleshooting Guide

### Common Issues

```mermaid
flowchart TD
    Issue[Monitoring Issue] --> Type{Issue Type}

    Type -->|No analyses| NoData[No Data Saved]
    Type -->|Wrong steering| BadSteer[Incorrect Steering]
    Type -->|Duplicates missed| MissDup[Missed Duplicates]
    Type -->|Low coherence| LowCoh[Low Coherence]

    NoData --> CheckGPT[Check GPT-5 API]
    NoData --> CheckDB[Check DB Connection]

    BadSteer --> CheckContext[Check Context Building]
    BadSteer --> CheckPrompt[Check Prompt Template]

    MissDup --> CheckSummaries[Check Guardian Summaries]
    MissDup --> CheckThreshold[Check Similarity Threshold]

    LowCoh --> CheckAgents[Check Agent Count]
    LowCoh --> CheckGoals[Check System Goals]
```

### Debug Commands

```bash
# Check monitoring logs
tail -f logs/monitor.log | grep -E "Guardian|Conductor"

# Check database state
sqlite3 hephaestus.db "
    SELECT COUNT(*) as analyses,
           AVG(alignment_score) as avg_score
    FROM guardian_analyses
    WHERE timestamp > datetime('now', '-1 hour');
"

# Check system coherence
sqlite3 hephaestus.db "
    SELECT timestamp, coherence_score, system_status
    FROM conductor_analyses
    ORDER BY timestamp DESC LIMIT 5;
"

# Check for stuck agents
sqlite3 hephaestus.db "
    SELECT agent_id, COUNT(*) as stuck_count
    FROM guardian_analyses
    WHERE needs_steering = 1
    GROUP BY agent_id
    HAVING stuck_count > 3;
"
```

## Future Enhancements

### Planned Features

1. **Machine Learning Integration**
   - Learn from successful interventions
   - Predict trajectory deviations
   - Optimize steering messages

2. **Advanced Duplicate Detection**
   - Semantic code analysis
   - Git diff integration
   - Automatic work redistribution

3. **Multi-Model Support**
   - Claude for trajectory analysis
   - GPT-4 for code understanding
   - Specialized models for different phases

4. **Enhanced Visualizations**
   - Real-time trajectory graphs
   - System coherence heatmaps
   - Intervention effectiveness charts

### Scalability Roadmap

```mermaid
gantt
    title Monitoring System Roadmap
    dateFormat YYYY-MM
    section Phase 1
    Current Implementation    :done, 2024-09, 2024-09
    section Phase 2
    ML Integration           :active, 2024-10, 2024-12
    Advanced Duplicates      :2024-11, 2025-01
    section Phase 3
    Multi-Model Support      :2024-12, 2025-02
    Distributed Monitoring   :2025-01, 2025-03
    section Phase 4
    Auto-Optimization        :2025-02, 2025-04
    Predictive Steering      :2025-03, 2025-05
```