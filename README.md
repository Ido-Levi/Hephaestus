# 🔥 Hephaestus: A Semi-Structured Agentic Framework

<div align="center">

![Python](https://img.shields.io/badge/python-3.8%2B-blue)
![License](https://img.shields.io/badge/license-AGPL--3.0-green)
![Status](https://img.shields.io/badge/status-alpha-orange)
![Docs](https://img.shields.io/badge/docs-online-brightgreen)

**What if AI workflows could write their own instructions as agents discover what needs to be done?**

[Quick Start](https://ido-levi.github.io/Hephaestus/docs/getting-started/quick-start) • [Documentation](https://ido-levi.github.io/Hephaestus/) • [Examples](example_workflows/)

</div>

---

## 🎥 See Hephaestus in Action

<div align="center">

https://github.com/user-attachments/assets/7b021611-2c09-494b-9da1-2ce05176dc51

*Watch how Hephaestus coordinates multiple AI agents, monitors their trajectories, and builds workflows dynamically*

</div>

---

## The Problem I Kept Running Into

I was trying to build a system where AI agents could handle complex software projects. You know the kind: "Build me an authentication system with OAuth, JWT, rate limiting, and comprehensive tests."

Traditional agentic frameworks can branch and loop, but they have a limitation: **every branch needs predefined instructions.** You must write the task descriptions upfront for every scenario you anticipate.

But what about discoveries you didn't anticipate? When a testing agent finds an optimization opportunity, a security issue, or a better architectural pattern?

Here's what I tried instead: **Define logical phase types that are needed to solve problems - like "Plan → Implement → Test" - and let agents create tasks in ANY phase based on what they discover.**

## What Actually Happened: A Branching Tree That Builds Itself

Instead of a rigid sequence, I set up phase types:
- **Phase 1 (Analysis)**: Understanding, planning, investigation
- **Phase 2 (Implementation)**: Building, fixing, optimizing
- **Phase 3 (Validation)**: Testing, verification, quality checks

The key insight: **Agents can spawn tasks in any phase they want.**

A validation agent testing your auth system might discover an elegant caching pattern. Instead of being stuck (or following predefined branching logic you wrote), the agent:

1. **Creates a Phase 1 investigation task**: "Analyze auth caching pattern - could apply to 12 other API routes for 40% speedup"
2. **Keeps working** on their validation task
3. Another agent picks up the investigation task and explores it

The workflow just branched itself. Not because you predicted "if optimization found, spawn investigation task" - but because the agent discovered something worth exploring and had the freedom to create work for it.

This creates a **branching tree of tasks** that grows based on actual discoveries, not anticipated scenarios.

Let me show you what this looks like in practice:

### Example 1: Security Testing - Finding What You Didn't Predict

You're pentesting a web application. You define three phase types:
- **Phase 1 (Reconnaissance)**: Map attack surface, enumerate endpoints
- **Phase 2 (Investigation)**: Test vulnerabilities, analyze findings
- **Phase 3 (Validation)**: Verify exploitability, assess impact

That's it. No predefined attack chains. No "if SQL injection found, then do X" logic. Just guidelines for how to recon, investigate, and validate.

**Phase 1 agent** maps the application and spawns **3 Phase 2 investigation tasks** for interesting endpoints it found.

**Phase 2 agent** investigating the `/api/users` endpoint discovers an IDOR vulnerability. It saves this to memory and spawns a **Phase 3 validation task**.

**Phase 3 agent** validates the IDOR works. While testing, it notices the exposed user data includes internal API keys. That's interesting - what can those keys access?

The agent **spawns a Phase 1 recon task**: "Enumerate internal API endpoints using discovered keys from IDOR vulnerability."

A new **Phase 1 agent** picks this up, searches memories for "IDOR" and "API keys", finds the relevant context, and discovers several internal endpoints. It spawns **Phase 2 investigation tasks** for each.

One of those **Phase 2 agents** finds an internal `/admin/export` endpoint with weak authorization. It saves this discovery to memory.

Another **Phase 2 agent**, investigating a different endpoint, searches memories for "admin" discoveries and finds the export endpoint. It chains these together: IDOR → API keys → admin access → data export. It spawns a **Phase 3 validation task** to verify the full chain.

**The complex vulnerability discovered itself** - agents chained multiple smaller findings by sharing discoveries through memory and spawning new tasks as they explored.

```mermaid
graph TB
    P1[Phase 1: Map Application<br/>Finds 3 interesting endpoints] --> P2A[Phase 2: Test /api/users]
    P1 --> P2B[Phase 2: Test /api/auth]
    P1 --> P2C[Phase 2: Test /api/docs]

    P2A -->|IDOR found| P3A[Phase 3: Validate IDOR]
    P3A -->|discovers API keys| P1B[Phase 1: Recon with Keys<br/>NEW BRANCH]

    P1B -->|finds internal APIs| P2D[Phase 2: Test /admin/export]
    P1B --> P2E[Phase 2: Test /internal/logs]

    P2D -->|saves to memory| MEM[(Memory: admin export found)]
    P2E -->|searches memory| MEM
    P2E -->|chains findings| P3B[Phase 3: Validate Full Chain<br/>IDOR + Keys + Admin = Critical]

    style P3A fill:#fff3e0
    style P1B fill:#e1f5fe
    style P2E fill:#ffebee
    style P3B fill:#c8e6c9
```

You never told agents to chain IDOR with admin access. You never wrote "if API keys found, enumerate internal endpoints."

You just defined **how to do reconnaissance, investigation, and validation** - and agents figured out the complex attack chain by discovering, sharing, and building on each other's findings.

### Example 2: Building from a PRD

I give Hephaestus a product requirements document: "Build a web application with authentication, REST API, and a React frontend."

**Phase 1 agent** reads the PRD and identifies 5 major components:
1. Authentication system
2. REST API layer
3. React frontend
4. Database schema
5. Background workers

It spawns **5 Phase 2 tasks** — one for each component. Now I have 5 agents building in parallel, each focused on one piece.

One of the **Phase 2 agents** finishes the REST API and spawns a **Phase 3 validation task**: "Test the REST API endpoints."

The **Phase 3 agent** starts testing. Everything passes. But then it notices something:

> "The auth endpoints use a caching pattern that reduces database queries by 60%. This could speed up all API routes significantly."

**Here's where it gets interesting.**

The Phase 3 agent doesn't just log this observation and move on. It doesn't get stuck because there's no "investigate optimizations" in the workflow plan.

Instead, it **spawns a new Phase 1 investigation task**: "Analyze auth caching pattern — could apply to other API routes for major performance gain."

<div align="center">
<img src="assets/hephaestus_overview.png" alt="Hephaestus System Overview" width="100%">
<p><em>Real-time view: 2 agents working across 3 phases, Guardian monitoring at 90% coherence</em></p>
</div>

A new Phase 1 agent spawns, investigates the caching pattern, confirms it's viable, and spawns a **Phase 2 implementation task**: "Apply caching pattern to all API routes."

Another agent implements it. Another agent validates it.

**The workflow just branched itself.** No one planned for this optimization. An agent discovered it during testing and created new work to explore it.

Meanwhile, a different Phase 3 agent is testing the authentication component. Tests fail. So it spawns a **Phase 2 bug fix task**: "Fix auth token expiry validation — current implementation allows expired tokens."

The fix agent implements the solution and spawns **Phase 3 retest**: "Validate auth fixes."

### What Just Happened?

Look at what emerged:

```mermaid
graph TB
    P1[Phase 1: Analyze PRD<br/>Creates 5 tickets] --> P2A[Phase 2: Build Auth]
    P1 --> P2B[Phase 2: Build API]
    P1 --> P2C[Phase 2: Build Frontend]

    P2B --> P3B[Phase 3: Test API]
    P3B -->|discovers optimization| P1New[Phase 1: Investigate Caching<br/>NEW BRANCH]
    P3B -->|testing continues| P3Done[API Validated]

    P1New --> P2New[Phase 2: Implement Caching]
    P2New --> P3New[Phase 3: Validate Optimization]

    P2A --> P3A[Phase 3: Test Auth]
    P3A -->|tests fail| P2Fix[Phase 2: Fix Auth Bug]
    P2Fix --> P3Retest[Phase 3: Retest Auth]

    style P3B fill:#fff3e0
    style P1New fill:#e1f5fe
    style P2Fix fill:#ffebee
```

**This workflow built itself:**
- Started with 1 analysis task
- Branched into 5 parallel implementation tasks
- One testing phase discovered optimization → spawned 3-phase investigation branch
- Another testing phase found bugs → spawned fix → retest loop
- All coordinated through Kanban tickets with blocking relationships

<div align="center">
<img src="assets/kanban_board.png" alt="Kanban Board Created in Real-Time" width="100%">
<p><em>Kanban board automatically built by agents: Backlog → Building → Testing → Done</em></p>
</div>

<div align="center">
<img src="assets/tickets_interaction.png" alt="Workflow Dependencies" width="100%">
<p><em>Dependency graph showing which tickets block others - the workflow structure Hephaestus discovered</em></p>
</div>

## Why This Changes Everything

**Traditional workflows:** Predict every scenario upfront → rigid plan → breaks when reality diverges

**Hephaestus approach:** Define work types → agents discover → workflow adapts in real-time

Here's another example that shows the power: **Security testing**

A Phase 1 reconnaissance agent maps a web application's attack surface. It finds 12 potential vulnerabilities and spawns **12 Phase 2 exploitation tasks** — one per vulnerability.

Twelve agents start testing exploits in parallel.

**Phase 2 Agent #5** successfully bypasses authentication. But now it can see the admin panel that wasn't visible before. The admin panel has its own vulnerabilities.

What does it do? **Spawns 3 new Phase 1 reconnaissance tasks:**
- "Investigate admin panel endpoints"
- "Map privileged API routes"
- "Analyze session management for privilege escalation"

Each of these spawns their own exploitation attempts. Each successful exploit might reveal more attack surface.

**The attack tree builds itself** based on what agents actually find, not what we predicted upfront.

## The Semi-Structured Sweet Spot

Here's why this is "semi-structured" and why that matters:

**Fully structured workflows** (traditional frameworks):
- ❌ Require predefined prompts for every scenario
- ❌ Can branch/loop, but need fixed instructions for each path
- ❌ Must anticipate all discoveries upfront

**Fully unstructured agents** (chaos):
- ❌ No coordination
- ❌ Duplicate work
- ❌ Contradictory changes
- ❌ No clear success criteria

**Semi-structured (Hephaestus)**:
- ✅ **Phase definitions** provide work type structure and guidelines
- ✅ **Agents write task descriptions** dynamically based on discoveries
- ✅ **Kanban tickets** coordinate work with blocking relationships
- ✅ **Guardian monitoring** ensures agents stay aligned with phase goals
- ✅ Workflow adapts to what agents actually find, not what you predicted

You get **structure where it matters**:
- Phase types define what kind of work is happening
- Done definitions set clear completion criteria
- Guardian validates alignment with phase instructions
- Tickets track dependencies and prevent chaos

And **flexibility where you need it**:
- Agents create detailed task descriptions on the fly
- No need to predefine every possible branch
- Discoveries drive workflow expansion in real-time
- New work types emerge as agents explore

## 🚀 Quick Start

### Prerequisites

- **Python 3.10+**
- **tmux** - Terminal multiplexer for agent isolation
- **Git** - Your project must be a git repository
- **Docker** - For running Qdrant vector store
- **Node.js & npm** - For the frontend UI
- **Claude Code** - AI coding assistant that agents run inside
- **API Keys**: OpenAI, OpenRouter, or Anthropic

### Get Started in 10 Minutes

Build your first self-adapting workflow:

**👉 [Quick Start Guide](https://ido-levi.github.io/Hephaestus/docs/getting-started/quick-start)**

The guide walks you through:
- Setting up API keys and LLM configuration
- Configuring MCP servers (Hephaestus + Qdrant)
- Setting your working directory
- Defining phases with dynamic task generation
- Running a workflow that adapts in real-time
- Watching agents coordinate and discover new work automatically

<div align="center">
<img src="assets/hephaestus_observability.png" alt="Agent Observability" width="100%">
<p><em>Real-time observability: Watch agents work in isolated Claude Code sessions as they discover and build the workflow</em></p>
</div>

---

**Want to learn more?** Check out the [full documentation](https://ido-levi.github.io/Hephaestus/) for:
- Complete architecture and technical details
- API reference and SDK guides
- Example workflows and templates
- Best practices and advanced features

---

## 🤝 Getting Help

- 📖 **[Documentation](https://ido-levi.github.io/Hephaestus/)** - Complete guides, API reference, and tutorials
- 💬 **[GitHub Discussions](https://github.com/Ido-Levi/Hephaestus/discussions)** - Ask questions and share ideas
- 🐛 **[Issue Tracker](https://github.com/Ido-Levi/Hephaestus/issues)** - Report bugs and request features
- 📧 **Email** - Reach out for support or collaboration

---

<div align="center">

**Hephaestus: Where workflows forge themselves**

*Named after the Greek god of the forge, Hephaestus creates a system where agents craft the workflow as they work*

[Quick Start](https://ido-levi.github.io/Hephaestus/docs/getting-started/quick-start) • [Documentation](https://ido-levi.github.io/Hephaestus/)

**License:** AGPL-3.0 • **Status:** Alpha - Active Development

</div>
