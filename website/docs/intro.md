---
sidebar_position: 1
slug: /
title: Welcome to Hephaestus
---

# Welcome to Hephaestus

**Hephaestus** is a semi-structured agentic framework that enables AI agents to build workflows dynamically based on what they discover, rather than following rigid predetermined steps.

## What is Hephaestus?

Hephaestus enables you to:

- **Orchestrate Multiple AI Agents**: Coordinate dozens of AI agents working in parallel on complex workflows
- **Automated Task Management**: Intelligent task queuing, assignment, and lifecycle management
- **Self-Healing Monitoring**: Real-time trajectory analysis with Guardian agents that detect and fix stuck agents
- **Git Worktree Isolation**: Each agent works in its own isolated git workspace for conflict-free parallel execution
- **RAG-Powered Memory**: Semantic memory system that enables agents to learn from each other
- **Validation Framework**: Automated quality control with validator agents that verify task completion

## Key Features

### 🤖 Autonomous Agent Orchestration
- Create agents dynamically for each task
- Intelligent task assignment based on context
- Automatic agent lifecycle management

### 📊 Advanced Monitoring
- **Guardian Agents**: Monitor individual agent health and provide interventions
- **Conductor Agents**: System-wide coordination and duplicate detection
- **Trajectory Analysis**: Real-time behavior monitoring with LLM-powered insights

### 🔧 Workflow System
- Define multi-phase workflows in YAML or Python
- Task dependencies and blocking relationships
- Result validation and quality gates
- Ticket tracking for work management

### 💾 Intelligent Memory
- Vector-based semantic search with Qdrant
- Automatic knowledge sharing between agents
- Memory types: errors, discoveries, decisions, learnings
- Task deduplication to prevent duplicate work

### 🌳 Git Integration
- Worktree-based isolation for parallel development
- Automatic branch management
- Commit tracking and linking
- No merge conflicts between agents

## Quick Start Paths

### For New Users
Start with our [Quick Start Guide](getting-started/quick-start) to build your first workflow in 10 minutes.

### For Developers
Dive into the [Core Systems](core/monitoring-implementation) to understand the architecture, then check out the [SDK Guide](sdk/README) for programmatic control.

### For Workflow Designers
Read the [Workflow Design Best Practices](guides/best-practices) to learn design patterns for interconnected workflows, then explore [Python Phases](sdk/python-phases) for advanced configurations.

## Architecture Overview

Hephaestus is built on:

- **FastAPI Server**: REST API with MCP (Model Context Protocol) for Claude Code integration
- **SQLite Database**: Relational data for tasks, agents, and workflows
- **Qdrant Vector Store**: Semantic memory and RAG capabilities
- **tmux Sessions**: Agent isolation and output capture
- **Multi-Provider LLM**: Support for OpenAI and Anthropic models

## Documentation Structure

Our documentation is organized into several sections:

- **[Getting Started](getting-started/quick-start)**: Build your first workflow in 10 minutes
- **[Workflow Design Guides](guides/phases-system)**: Learn how to design effective multi-agent workflows
- **[Core Systems](core/monitoring-implementation)**: Architecture, system components, and advanced features
- **[Python SDK](sdk/README)**: Python SDK for programmatic workflow control

## Getting Started

Ready to dive in? Check out our [Quick Start Guide](getting-started/quick-start) or explore the documentation using the sidebar navigation.

---

**Need Help?** Check the [Best Practices](guides/best-practices) guide or explore the [Core Systems](core/monitoring-implementation) for architecture details.
