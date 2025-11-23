"""
Phase 2: Documentation Generation

Generates documentation for ONE component/area based on the ticket created in Phase 1.
Multiple Phase 2 agents run in parallel, each handling one documentation ticket.
"""

from src.sdk.models import Phase

PHASE_2_DOCUMENTATION_GENERATION = Phase(
    id=2,
    name="documentation_generation",
    description="""Generate documentation for ONE component/area based on the ticket.

This phase creates or updates documentation for a single component/area:
1. Reads the ticket to understand what to document
2. Checks if documentation already exists (UPDATE if so!)
3. Analyzes the relevant code
4. Generates comprehensive markdown documentation
5. Updates docs/README.md index if needed
6. Resolves the ticket when documentation is complete

Multiple Phase 2 agents run in parallel, each handling one ticket.""",
    done_definitions=[
        "Ticket read and documentation scope understood",
        "Existing documentation checked (update if exists)",
        "Relevant code analyzed thoroughly",
        "Documentation written in markdown format",
        "Documentation saved to docs/ folder",
        "docs/README.md index updated (if applicable)",
        "Documentation quality verified",
        "Ticket resolved with resolution comment",
        "Task marked as done with summary",
    ],
    working_directory=".",
    additional_notes="""═══════════════════════════════════════════════════════════════════════
YOU ARE A DOCUMENTATION WRITER - GENERATE DOCS FOR ONE COMPONENT
═══════════════════════════════════════════════════════════════════════

🎯 YOUR MISSION: Generate documentation for ONE ticket's component/area

═══════════════════════════════════════════════════════════════════════
⚠️ CRITICAL WORKFLOW RULES
═══════════════════════════════════════════════════════════════════════

0. **🚨 ALWAYS USE YOUR ACTUAL AGENT ID! 🚨**
   DO NOT use "agent-mcp" - use your real agent ID from task context.

1. **ONE TICKET = ONE DOCUMENTATION FILE**
   You are documenting ONE component/area from ONE ticket.
   Do NOT try to document everything!

2. **CHECK EXISTING DOCS FIRST**
   If documentation already exists, UPDATE it - don't overwrite blindly!
   Preserve existing good content while adding/updating.

3. **ALL DOCS GO IN docs/ FOLDER**
   Create docs/ folder if it doesn't exist.
   Use consistent naming: `docs/component-name.md`

4. **RESOLVE YOUR TICKET WHEN DONE**
   Unlike other workflows, Phase 2 resolves tickets directly.
   No Phase 3 validation - documentation is self-validating.

═══════════════════════════════════════════════════════════════════════

STEP 1: READ YOUR TICKET

Your task description contains TICKET: [ticket_id]

```python
# Get full ticket details
ticket = get_ticket("[YOUR TICKET ID]")
```

The ticket description tells you:
- What component/area to document
- Target file path (e.g., `docs/api-reference.md`)
- What content to include
- Existing documentation to check
- Style guidelines

═══════════════════════════════════════════════════════════════════════

STEP 2: CHECK EXISTING DOCUMENTATION

**CRITICAL: Look before you write!**

```bash
# Check if docs folder exists
ls -la docs/

# Check if target file already exists
ls -la docs/[target-file].md
```

**If docs file exists:**
- READ the existing content
- PRESERVE good existing content
- UPDATE outdated sections
- ADD missing sections
- DO NOT overwrite blindly!

**If docs file doesn't exist:**
- Create new file
- Follow ticket's content guidelines

```python
save_memory(
    content="Documentation: [file] - Existing: [yes/no]. Action: [create/update].",
    agent_id="[YOUR AGENT ID]",
    memory_type="discovery"
)
```

═══════════════════════════════════════════════════════════════════════

STEP 3: ANALYZE THE CODE

**Use existing memories from index_repo if available!**

If no memories, analyze the relevant code:

1. Find the relevant files for your component
2. Understand what the code does
3. Identify public APIs, interfaces, usage patterns
4. Note any configuration options
5. Find usage examples in tests or examples/

```python
save_memory(
    content="[Component] analysis: Purpose=[X], Key functions=[list], Public API=[describe].",
    agent_id="[YOUR AGENT ID]",
    memory_type="codebase_knowledge"
)
```

═══════════════════════════════════════════════════════════════════════

STEP 4: WRITE THE DOCUMENTATION

**Follow markdown best practices:**

```markdown
# Component Name

Brief one-paragraph description of what this component does.

## Overview

More detailed explanation:
- What problem it solves
- When to use it
- Key concepts

## Getting Started

Quick start guide with minimal code:

```python
# Minimal example to get started
from myproject import Component

component = Component()
component.do_something()
```

## Usage

### Basic Usage

Detailed usage with examples:

```python
# Example with comments explaining each part
```

### Advanced Usage

More complex scenarios:

```python
# Advanced example
```

## API Reference

### `function_name(param1, param2)`

Description of the function.

**Parameters:**
- `param1` (type): Description
- `param2` (type, optional): Description. Default: `value`

**Returns:**
- `type`: Description

**Raises:**
- `ExceptionType`: When this happens

**Example:**
```python
result = function_name("value", param2=True)
```

### `ClassName`

Description of the class.

#### Methods

- `method_name()`: Brief description

## Configuration

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `option1` | string | `"default"` | What it does |
| `option2` | boolean | `false` | What it does |

## Examples

### Example: Common Use Case

```python
# Full working example
```

### Example: Another Use Case

```python
# Another example
```

## Troubleshooting

### Common Issue 1

**Problem:** Description of the problem.

**Solution:** How to fix it.

### Common Issue 2

**Problem:** Description.

**Solution:** How to fix.

## See Also

- [Related Doc 1](./related.md)
- [Related Doc 2](./other.md)
```

═══════════════════════════════════════════════════════════════════════

STEP 5: WRITE THE FILE

**Create/Update the documentation file:**

```python
# Ensure docs/ folder exists
import os
os.makedirs("docs", exist_ok=True)

# Write the documentation
with open("docs/[component].md", "w") as f:
    f.write(documentation_content)
```

Or use the available file writing tools.

═══════════════════════════════════════════════════════════════════════

STEP 6: UPDATE docs/README.md INDEX

**If this is a new documentation file, add it to the index:**

```markdown
# Documentation

Welcome to the project documentation.

## Contents

- [Overview](./overview.md) - Project overview and quick start
- [Getting Started](./getting-started.md) - Installation and setup
- [Architecture](./architecture.md) - System design and components
- [API Reference](./api-reference.md) - Complete API documentation
- [Configuration](./configuration.md) - Configuration options
- [Contributing](./contributing.md) - How to contribute

## Quick Links

- [Installation](./getting-started.md#installation)
- [Quick Start](./overview.md#quick-start)
- [API](./api-reference.md)
```

**Only update if:**
- docs/README.md exists AND your file is new
- OR you're creating docs/README.md as part of Overview ticket

═══════════════════════════════════════════════════════════════════════

STEP 7: VERIFY DOCUMENTATION QUALITY

**Check your documentation:**

✅ **Content Checklist:**
- [ ] Accurate - reflects actual code behavior
- [ ] Complete - covers all public APIs/features
- [ ] Clear - understandable by target audience
- [ ] Organized - logical structure with headings
- [ ] Examples - working code examples included
- [ ] Links - references to related docs

✅ **Formatting Checklist:**
- [ ] Valid markdown syntax
- [ ] Code blocks have language hints
- [ ] Tables are properly formatted
- [ ] Links work (relative paths)
- [ ] Consistent heading levels

═══════════════════════════════════════════════════════════════════════

STEP 8: RESOLVE YOUR TICKET

**Documentation is self-validating - resolve directly:**

```python
resolve_ticket(
    ticket_id="[YOUR TICKET ID]",
    agent_id="[YOUR AGENT ID]",
    resolution_comment="Documentation created/updated at docs/[filename].md. Includes: [summary of content]. docs/README.md index updated: [yes/no]."
)
```

═══════════════════════════════════════════════════════════════════════

STEP 9: MARK YOUR TASK AS DONE

```python
update_task_status(
    task_id="[YOUR TASK ID]",
    agent_id="[YOUR AGENT ID]",
    status="done",
    summary="Documentation for [component] created/updated at docs/[filename].md. Content includes: [brief summary]. Action: [created new/updated existing]. Ticket resolved."
)
```

═══════════════════════════════════════════════════════════════════════
DOCUMENTATION TEMPLATES BY TYPE
═══════════════════════════════════════════════════════════════════════

**Overview/README:**
- Project name and description
- Key features (bullet list)
- Quick start (3-5 steps)
- Links to other docs

**Getting Started:**
- Prerequisites
- Installation steps
- First run
- Basic configuration
- Troubleshooting setup

**Architecture:**
- System overview diagram (mermaid or ASCII)
- Component descriptions
- Data flow
- Design decisions
- External dependencies

**API Reference:**
- Grouped by resource/domain
- Each endpoint: method, path, params, responses
- Authentication requirements
- Error responses
- Code examples (curl/SDK)

**Configuration:**
- All options with descriptions
- Environment variables
- Config file format
- Default values
- Examples for common setups

**Contributing:**
- Development setup
- Code style guide
- Testing requirements
- PR process
- Issue reporting

═══════════════════════════════════════════════════════════════════════
CRITICAL RULES
═══════════════════════════════════════════════════════════════════════

✅ DO:
- Check existing docs BEFORE writing
- Update existing content (don't overwrite blindly)
- Use consistent naming: `docs/component-name.md`
- Include working code examples
- Use proper markdown formatting
- Update docs/README.md index for new files
- Resolve ticket when documentation complete

❌ DO NOT:
- Document everything (you have ONE ticket)
- Overwrite existing docs without reading them
- Create docs outside docs/ folder
- Skip code examples
- Leave broken links or placeholders
- Create multiple files for one ticket
- Forget to resolve your ticket

═══════════════════════════════════════════════════════════════════════
""",
    outputs=[
        "Ticket scope understood",
        "Existing documentation checked",
        "Relevant code analyzed",
        "Documentation written in markdown",
        "Documentation saved to docs/ folder",
        "docs/README.md index updated (if applicable)",
        "Ticket resolved with resolution comment",
    ],
    next_steps=[
        "Other Phase 2 agents continue their documentation tasks",
        "When all tickets resolved, documentation is complete",
        "User can review generated docs in docs/ folder",
    ],
)
