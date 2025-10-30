# Hephaestus Documentation

Welcome to Hephaestus - an autonomous AI agent orchestration system that manages multiple AI agents working together on complex tasks.

## 🚀 Quick Navigation

### New to Hephaestus?

Start here to get up and running in minutes:

- **[Quick Start Guide](getting-started/quick-start.md)** - Build your first workflow in 10 minutes

### Designing Workflows

Learn how to design effective multi-agent workflows:

- **[Phases System](guides/phases-system.md)** - Understanding how workflows build themselves
- **[Best Practices](guides/best-practices.md)** - Patterns for interconnected problem-solving
- **[Guardian Monitoring](guides/guardian-monitoring.md)** - How Guardian keeps agents on track
- **[Ticket Tracking](guides/ticket-tracking.md)** - Kanban boards for agent coordination

### Core Systems

Deep dive into the architecture and core systems:

- **[Agent Communication](core/agent-communication.md)** - Inter-agent messaging and coordination
- **[Memory System](core/memory-system.md)** - RAG-based knowledge sharing
- **[Monitoring Implementation](core/monitoring-implementation.md)** - Technical deep-dive into Guardian & Conductor
- **[Queue & Task Management](core/queue-and-task-management.md)** - Task lifecycle and queue system
- **[Validation System](core/validation-system.md)** - Automated quality control
- **[Worktree Isolation](core/worktree-isolation.md)** - Git worktrees for parallel agent execution

### Advanced Features

Specialized features for power users:

- **[Diagnostic Agents](features/diagnostic-agents.md)** - Self-healing workflow detection
- **[Task Deduplication](features/task-deduplication.md)** - Prevent duplicate work with embeddings
- **[Task Results](features/task-results.md)** - Task-level result reporting
- **[Workflow Results](features/workflow-results.md)** - Workflow-level solution submission

### Python SDK

Programmatic workflow control with Python:

- **[SDK Overview](sdk/overview.md)** - What the SDK does and when to use it
- **[Defining Phases](sdk/phases.md)** - Complete guide to Phase objects
- **[SDK Examples](sdk/examples.md)** - Breakdown of run_prd_workflow.py

### API Reference

For advanced integration and power users:

- **[Tickets API](api/tickets.md)** - Complete API reference for ticket tracking system

---

## 📖 Recommended Learning Paths

### Path 1: Workflow Designer (Recommended for Most Users)

1. Start with [Quick Start](getting-started/quick-start.md) to understand the basics
2. Read [Phases System](guides/phases-system.md) to learn how workflows work
3. Study [Best Practices](guides/best-practices.md) for design patterns
4. Learn about [Guardian Monitoring](guides/guardian-monitoring.md) and [Ticket Tracking](guides/ticket-tracking.md)
5. Explore [SDK Overview](sdk/overview.md) for Python integration

### Path 2: Contributor / Advanced User

1. Start with [Quick Start](getting-started/quick-start.md) for context
2. Read all [Workflow Design Guides](#designing-workflows)
3. Deep dive into [Core Systems](#core-systems) to understand architecture
4. Review [Advanced Features](#advanced-features)
5. Check [API Reference](#api-reference) for integration

### Path 3: Python Developer

1. [Quick Start](getting-started/quick-start.md) for overview
2. [SDK Overview](sdk/overview.md) for programmatic usage
3. [Defining Phases](sdk/phases.md) for defining workflows in code
4. [SDK Examples](sdk/examples.md) for real-world patterns
5. Reference [Workflow Design Guides](#designing-workflows) as needed

---

## 🎯 Key Concepts

### Phases
Logical stages of problem-solving (reconnaissance → implementation → validation) that communicate and branch dynamically based on discoveries.

### Guardian
AI-powered monitoring system that analyzes agent trajectories every 60 seconds, ensuring agents stay aligned with their goals and providing steering when needed.

### Tickets
Persistent work items with memory - agents create tickets, move them through Kanban columns, add comments, and resolve them when complete. Perfect for coordinating multi-agent workflows.

### Semi-Structured Workflows
Combine structure (phases, tickets, done definitions) with flexibility (dynamic task spawning, cross-phase branching, adaptive problem-solving).

---

## 🔗 External Resources

- **[Main README](../README.md)** - Project overview and installation
- **[CLAUDE.md](../CLAUDE.md)** - Instructions for Claude Code when working with this codebase
- **[Example Workflows](../example_workflows/)** - Real-world workflow implementations

---

## 📝 Documentation Structure

```
docs/
├── getting-started/     # First steps and tutorials
├── guides/              # Workflow design and usage
├── core/                # Architecture and core systems
├── features/            # Advanced features
├── sdk/                 # Python SDK reference
└── api/                 # API references
```

---

**Last Updated:** 2025-10-29
**Documentation Version:** 3.0 (Reorganized for Docusaurus)
