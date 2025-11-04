"""
Phase 2: Exploration and Implementation

Explores ONE solution approach, implements it, and tests if it works.
This phase combines investigation and implementation for faster iteration.
"""

from src.sdk.models import Phase

PHASE_2_EXPLORATION_AND_IMPLEMENTATION = Phase(
    id=2,
    name="exploration_and_implementation",
    description="""Explore your assigned approach, implement it, and test if it works.
Your task description contains an approach ticket (TICKET: xxx) - investigate it,
implement the fix, test immediately, and either create P3 task or try a new approach.""",
    done_definitions=[
        "Approach ticket extracted from task description (TICKET: xxx)",
        "Ticket moved to 'exploring' status at start",
        "Code investigation completed - found exact locations to modify",
        "Changes implemented following project patterns",
        "Reproduction test run to verify fix",
        "Ticket status updated based on result:",
        "  - If fix works: moved to 'testing' + P3 task created",
        "  - If fix fails: moved to 'approach-failed' + new P2 task created",
        "All changes committed or reverted appropriately",
    ],
    working_directory="/Users/idol/SWEBench_Hep_Problems/sphinx-doc__sphinx-7757/sphinx",
    additional_notes="""🎯 MISSION: Investigate → Implement → Test → Decide

════════════════════════════════════════════════════════════════════
🎯 SWEBENCH BENCHMARK CONTEXT
════════════════════════════════════════════════════════════════════

You are solving a real-world bug from a popular open-source repository as part
of **SWEBench-Verified**, a rigorous AI benchmark for evaluating code generation
and bug-fixing capabilities.

**SWEBench Rules (MANDATORY):**
1. 🚨 **NO TEST FILE MODIFICATIONS** - You fix the SOURCE CODE to pass EXISTING tests
2. 🚨 **PATCH MUST APPLY CLEANLY** - Use `git apply` to validate before submitting
3. 🚨 **ALL TESTS MUST PASS** - No regression allowed
4. 🚨 **MINIMAL CHANGES ONLY** - Only fix what's broken, nothing more

**Success Criteria:**
- Patch applies to base commit without errors
- All existing tests pass (100% pass rate)
- Original issue is completely resolved
- No test files modified
- No unrelated changes included

**Your Mission:**
Solve this verified real-world bug with production-quality code that would
be acceptable in the actual open-source project. Be thorough, be precise,
and validate everything before submitting.

════════════════════════════════════════════════════════════════════

═══════════════════════════════════════════════════════════════════════
WORKFLOW: EXPLORE AND IMPLEMENT IN ONE GO
═══════════════════════════════════════════════════════════════════════

**STEP 1: EXTRACT APPROACH TICKET**

Your task description contains "TICKET: ticket-xxxxx" - this tells you WHAT to try.

```python
# Extract from task description
approach_ticket_id = "[extract TICKET: xxx]"

# Read the ticket to understand the approach
ticket = mcp__hephaestus__get_ticket(approach_ticket_id)
# The ticket describes what strategy to explore

# Move to 'exploring' status
mcp__hephaestus__change_ticket_status({
    "ticket_id": approach_ticket_id,
    "agent_id": "[YOUR AGENT ID]",
    "new_status": "exploring",
    "comment": "Starting exploration and implementation of this approach."
})
```

**STEP 2: INVESTIGATE CODE**

Find the exact locations where changes are needed:

Search strategies:
- Use grep/rg to find relevant functions, classes, error messages
- Read reproduction.md for test cases and failure patterns
- Trace code execution from the reproduction case
- Look for similar patterns in the codebase
- Check how related issues are handled elsewhere

**Early exit if approach is clearly invalid:**
If during investigation you realize this approach won't work (e.g., the code
structure doesn't support it, would require massive refactoring), jump to
STEP 5B (mark as failed) WITHOUT implementing.

**STEP 3: IMPLEMENT THE FIX**

Once you know WHAT to change and HOW:

🚨🚨🚨 CRITICAL: NEVER MODIFY TEST FILES! 🚨🚨🚨
═══════════════════════════════════════════════════════════════════════
**ABSOLUTE RULE: DO NOT MODIFY ANY FILES IN test/ OR tests/ DIRECTORIES!**

You must fix the SOURCE CODE to pass EXISTING tests.
You are NOT allowed to modify, update, or "fix" test files to make tests pass.

**FORBIDDEN ACTIONS:**
❌ Modifying test files (tests/, test/, *_test.py, test_*.py)
❌ Commenting out failing tests
❌ Changing test assertions
❌ Adding test fixtures that change test behavior
❌ Updating test data files used by tests

**WHY THIS RULE EXISTS:**
Your solution will be evaluated by running the ORIGINAL test suite.
If you modify tests, your solution will be INVALID and REJECTED.

**WHAT TO DO INSTEAD:**
✅ Fix the source code to make existing tests pass
✅ Understand what the test expects and fix the implementation
✅ If a test reveals a bug, fix the bug in the source code

**HOW TO IDENTIFY TEST FILES:**
- Any file in directories named: test/, tests/, testing/
- Any file matching: test_*.py, *_test.py, *_tests.py
- Any file in __pycache__ or .pytest_cache

**IF YOU ACCIDENTALLY MODIFY A TEST FILE:**
IMMEDIATELY revert the changes and fix the source code instead.
═══════════════════════════════════════════════════════════════════════

**Implementation principles:**
- Make MINIMAL changes - only what's needed to fix the issue
- NEVER modify test files (see warning above)
- Follow existing code style and patterns exactly
- Don't refactor unrelated code
- Handle edge cases mentioned in reproduction.md
- Test as you code - verify syntax is correct

```python
# Apply changes to files
# Keep track of what you modify
modified_files = ["file1.py", "file2.py"]
```

**STEP 4: TEST THE FIX**

Run the reproduction test from reproduction.md:

```bash
# Run reproduction commands from P1
# Example: python test_reproduction.py
# Example: pytest -xvs path/to/test_file.py
```

Document the test result:
```python
mcp__hephaestus__add_ticket_comment({
    "ticket_id": approach_ticket_id,
    "agent_id": "[YOUR AGENT ID]",
    "comment_text": (
        "Implementation complete. Test results:\\n"
        "\\n"
        "Test command: [command]\\n"
        "Result: [PASS/FAIL]\\n"
        "Output: [relevant output]"
    )
})
```

**STEP 5A: FIX WORKS ✅**

If reproduction test passes:

```python
# Move to 'testing' status
mcp__hephaestus__change_ticket_status({
    "ticket_id": approach_ticket_id,
    "agent_id": "[YOUR AGENT ID]",
    "new_status": "testing",
    "comment": (
        f"✅ Fix works! Reproduction test passes.\\n"
        f"\\n"
        f"Changes: {', '.join(modified_files)}\\n"
        f"\\n"
        f"Moving to comprehensive testing phase."
    )
})

# Create P3 task for full test suite
mcp__hephaestus__create_task({
    "description": f"Phase 3: Test and verify solution - TICKET: {approach_ticket_id}. Run full test suite, generate patch, and submit if all tests pass. If tests fail, mark approach as failed and create new P2 task.",
    "done_definition": f"Full test suite completed, ticket {approach_ticket_id} resolved OR marked failed, result submitted if successful OR new P2 task created if failed.",
    "agent_id": "[YOUR AGENT ID]",
    "phase_id": 3,
    "priority": "high",
    "ticket_id": approach_ticket_id
})

# Save success memory
mcp__hephaestus__save_memory({
    "agent_id": "[YOUR AGENT ID]",
    "content": f"Approach {approach_ticket_id} works! Modified {modified_files}. Reproduction test passes. Moving to P3 for full testing.",
    "memory_type": "discovery"
})
```

**STEP 5B: FIX DOESN'T WORK ❌**

🚨🚨🚨 CRITICAL: YOU MUST CREATE A NEW APPROACH TO CONTINUE! 🚨🚨🚨

If reproduction test still fails OR approach is clearly invalid, you MUST:
1. Mark this approach as failed
2. CREATE A NEW APPROACH TICKET with learnings from this failure
3. CREATE A NEW PHASE 2 TASK for the new approach

**DO NOT JUST MARK AS FAILED AND STOP! The workflow MUST continue!**

```python
# Move to 'approach-failed'
mcp__hephaestus__change_ticket_status({
    "ticket_id": approach_ticket_id,
    "agent_id": "[YOUR AGENT ID]",
    "new_status": "approach-failed",
    "comment": (
        "❌ Approach failed.\\n"
        "\\n"
        "What was tried: [brief description]\\n"
        "Why it failed: [reason - test still fails, wrong location, etc.]\\n"
        "Key learning: [what this revealed about the problem]\\n"
        "\\n"
        "Recommendation: [suggestion for next approach]"
    )
})

# Get main issue ticket
failed_ticket = mcp__hephaestus__get_ticket(approach_ticket_id)
main_issue_ticket_id = failed_ticket.get("parent_ticket_id")

# Create NEW approach based on learnings
new_approach = mcp__hephaestus__create_ticket({
    "agent_id": "[YOUR AGENT ID]",
    "title": f"Approach: [NEW strategy based on what you learned]",
    "description": (
        f"## New Approach (After {approach_ticket_id} Failed)\\n\\n"
        "### What We Learned\\n"
        "[Key insights from the failed attempt]\\n\\n"
        "### New Strategy\\n"
        "[Different approach addressing the learnings]\\n\\n"
        "### Why This Might Work\\n"
        "[Hypothesis]\\n\\n"
        "### Investigation Plan\\n"
        "- [What to investigate differently]\\n"
        "- [Different code locations or patterns to try]"
    ),
    "ticket_type": "approach",
    "priority": "medium",
    "tags": ["exploration", "retry"],
    "parent_ticket_id": main_issue_ticket_id
})

# Create NEW P2 task
mcp__hephaestus__create_task({
    "description": f"Phase 2: Explore and implement NEW approach - TICKET: {new_approach['ticket_id']}. Previous approach {approach_ticket_id} failed. Try this different strategy based on learnings.",
    "done_definition": f"Approach investigated and implemented, tested, ticket {new_approach['ticket_id']} moved to testing OR failed with new learnings and another new approach created.",
    "agent_id": "[YOUR AGENT ID]",
    "phase_id": 2,
    "priority": "medium",
    "ticket_id": new_approach["ticket_id"]
})

# Save failure learning
mcp__hephaestus__save_memory({
    "agent_id": "[YOUR AGENT ID]",
    "content": f"Approach {approach_ticket_id} failed: [reason]. Learned: [key insight]. Created new approach {new_approach['ticket_id']}.",
    "memory_type": "error_fix"
})

# Revert changes if needed
# git checkout -- [files] or git reset --hard if committed
```

**STEP 6: MARK P2 TASK DONE**

```python
mcp__hephaestus__update_task_status({
    "task_id": "[your P2 task ID]",
    "agent_id": "[YOUR AGENT ID]",
    "status": "done",
    "summary": (
        # If success:
        f"Approach {approach_ticket_id} works! Created P3 task for full testing."
        # If failure:
        # f"Approach {approach_ticket_id} failed. Created new approach {new_approach['ticket_id']} and P2 task."
    )
})
```

═══════════════════════════════════════════════════════════════════════
CRITICAL DECISION POINTS
═══════════════════════════════════════════════════════════════════════

**When to implement:**
✅ You found exact code locations
✅ You understand what needs to change
✅ The change is reasonable (not massive refactor)
✅ The approach seems feasible

**When to skip implementation:**
❌ Code structure doesn't support this approach
❌ Would require massive refactoring
❌ During investigation, realized bug is elsewhere
❌ Approach has fundamental flaws

**When fix "works":**
✅ Reproduction test from P1 passes
✅ The specific issue behavior is fixed
✅ No obvious new errors introduced

**When fix "fails":**
❌ Reproduction test still fails
❌ Fix causes new errors
❌ Only partially addresses the issue

═══════════════════════════════════════════════════════════════════════
REQUIREMENTS
═══════════════════════════════════════════════════════════════════════

✅ DO:
- Extract approach ticket from task description
- Move ticket to 'exploring' at start
- Investigate thoroughly before implementing
- Implement minimal, targeted changes to SOURCE CODE ONLY
- Test immediately after implementation
- Update ticket status based on test result
- Create P3 task if fix works
- Create new P2 task if fix fails
- Save learnings to memory
- Be honest about results

❌ DON'T:
- 🚨 MODIFY TEST FILES (tests/, test/, *_test.py, test_*.py) - ABSOLUTELY FORBIDDEN!
- Skip investigation and rush to implementation
- Make changes beyond what's needed
- Refactor unrelated code
- Skip testing the fix
- Mark as success if uncertain
- Create P3 task if fix doesn't work
- 🚨🚨🚨 JUST MARK AS FAILED AND STOP - YOU MUST CREATE NEW APPROACH! 🚨🚨🚨
- Give up when approach fails (create new one!)
- Leave failed changes uncommitted

═══════════════════════════════════════════════════════════════════════

**TICKET FLOW:**
exploration-needed → exploring → testing (if works) OR approach-failed (if not)

The key is FAST FEEDBACK: investigate, implement, test, decide. No handoffs,
no delays. One agent maintains full context from investigation to working code.""",
    outputs=[
        "- Approach ticket moved: exploration-needed → exploring → (testing OR approach-failed)",
        "- Modified source files with implementation (if fix works)",
        "- Test results from reproduction script",
        "- Ticket updated with detailed comments about result",
        "- EITHER P3 task (if works) OR new P2 task (if fails)",
        "- Memories saved with learnings",
    ],
    next_steps=[
        "If fix works:",
        "  - P3 will run full test suite",
        "  - If all pass → resolve tickets + submit",
        "  - If any fail → mark approach-failed + new P2",
        "",
        "If fix fails:",
        "  - New P2 task explores different approach",
        "  - Use learnings to try something different",
        "  - Workflow continues until solution found",
    ],
)
