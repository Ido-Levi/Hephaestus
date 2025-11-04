"""
Phase 1: Issue Analysis and Reproduction

Entry point for the workflow. Analyzes the problem statement,
reproduces the issue, creates the main issue ticket, and spawns multiple Phase 2
exploration tasks with approach tickets.
"""

from src.sdk.models import Phase

PHASE_1_ISSUE_ANALYSIS_AND_REPRODUCTION = Phase(
    id=1,
    name="issue_analysis_and_reproduction",
    description="""[This is Phase 1 - Created by Phase 0 initialization]
FOCUS: Reproduce the issue, create main issue ticket, and create MULTIPLE Phase 2 exploration tasks with approach tickets.
Read PROBLEM_STATEMENT.md, reproduce the issue with clear steps, create reproduction
scripts, and spawn MULTIPLE Phase 2 tasks to explore different solution approaches.
DO NOT implement solutions - only reproduce and document the issue clearly.""",
    done_definitions=[
        "Problem statement from PROBLEM_STATEMENT.md has been thoroughly analyzed to understand ROOT CAUSE",
        "Codebase has been COMPREHENSIVELY searched for ALL instances of the problem pattern",
        "ALL files and functions related to the issue have been identified (not just the obvious ones)",
        "Issue has been successfully reproduced with clear, repeatable steps",
        "COMPREHENSIVE test cases created that would fail if ANY aspect of the fix is missing",
        "Main issue ticket created in 'exploring' status",
        "reproduction.md file created with exact commands and COMPREHENSIVE test cases",
        "Custom reproduction scripts created that test ALL edge cases (e.g., test_reproduction.py)",
        "Test commands documented and verified to show ALL aspects of the issue",
        "CRITICAL: At least 2-3 approach tickets created addressing ALL identified problem locations",
        "CRITICAL: At least 2-3 Phase 2 tasks created (one per approach ticket) with TICKET: ticket-xxx format",
        "Each approach ticket addresses the COMPLETE fix, not just one aspect",
        "Main issue ticket ID saved to memory for future reference",
    ],
    working_directory="/Users/idol/SWEBench_Hep_Problems/sphinx-doc__sphinx-7757/sphinx",
    additional_notes="""🚨 CRITICAL: YOUR MAIN GOAL IS REPRODUCTION + CREATING ISSUE TICKET + CREATING MULTIPLE APPROACH TICKETS & P2 TASKS! 🚨

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
PHASE 1 WORKFLOW WITH TICKET TRACKING
═══════════════════════════════════════════════════════════════════════

**STEP 1: UNDERSTAND THE ROOT CAUSE (NOT JUST THE SYMPTOM!)**

🎯 CRITICAL: Don't just reproduce what's in the problem statement - understand WHY it's broken!

1. Read PROBLEM_STATEMENT.md carefully and identify:
   - What is the UNDERLYING ROOT CAUSE? (not just the symptom)
   - What PATTERN or CONCEPT is broken?
   - What CATEGORY of problem is this? (parsing, validation, formatting, logic, etc.)

2. Ask yourself:
   - If this happens in one place, could it happen elsewhere?
   - What is the GENERAL PRINCIPLE that's violated?
   - Are there related operations that might have the same issue?

Extract from PROBLEM_STATEMENT.md:
1. What is broken or needs to be added
2. Expected behavior after the fix
3. Any specific test cases mentioned
4. Edge cases or special conditions
5. Related files or modules mentioned

**STEP 2: COMPREHENSIVE CODEBASE INVESTIGATION**

🔍 CRITICAL: Find ALL instances of the problem pattern, not just the obvious one!

1. **Search for the problem pattern across the ENTIRE relevant file(s):**
   - Use grep/search to find ALL occurrences of similar patterns
   - Check related functions and modules
   - Look for the same root cause in different locations

2. **Common search patterns:**
   ```bash
   # Search for specific keywords from the error
   grep -n "keyword" path/to/file.py

   # Search for function/class definitions related to the issue
   grep -n "def function_name" path/to/file.py
   grep -n "class ClassName" path/to/file.py

   # Search for string literals or patterns mentioned in the issue
   grep -n '"pattern"' path/to/file.py

   # Search for imports or dependencies
   grep -n "import module" path/to/file.py
   ```

3. **For EACH location found, ask:**
   - Could this be affected by the same root cause?
   - Would fixing ONLY the obvious location leave this broken?
   - Does this need to be included in the complete fix?

4. **Document ALL findings in your investigation**

**STEP 3: CREATE COMPREHENSIVE TEST CASES**

🧪 CRITICAL: Create tests that would FAIL if ANY aspect of the fix is missing!

1. **Test the example from the problem statement** (this is just the START!)

2. **Think beyond the given example:**
   - What are edge cases related to this issue?
   - What are variations of the problem scenario?
   - What related operations might also be affected?
   - What could break if only a partial fix is applied?

3. **Create test cases for:**
   - The specific example in the problem statement ✓
   - Variations of the input/scenario ✓
   - Edge cases you identified ✓
   - Related operations that use similar logic ✓
   - All locations you found in your codebase search ✓

4. **Write test_reproduction.py that tests ALL scenarios**

**STEP 4: REPRODUCE THE ISSUE**

1. Reproduce the issue with minimal test case from problem statement
2. Create reproduction.md with:
   - EXACT commands to reproduce
   - ALL test cases (not just the one from problem statement)
   - Expected vs actual behavior for each
   - Exact error messages or incorrect outputs
3. Write custom reproduction scripts (test_reproduction.py with COMPREHENSIVE tests)
4. Verify that your test cases would catch an incomplete fix

**STEP 5: CREATE MAIN ISSUE TICKET**

Create ONE main issue ticket that represents the problem:

```python
issue_ticket = mcp__hephaestus__create_ticket({
    "agent_id": "[YOUR ACTUAL AGENT ID]",  # Use your real agent ID!
    "title": "Issue: {brief_description}",
    "description": (
        "## Problem Statement\\n"
        "[Copy full problem statement from PROBLEM_STATEMENT.md]\\n\\n"
        "### Expected Behavior\\n"
        "[What should happen after fix]\\n\\n"
        "### Current Behavior\\n"
        "[What's happening now - the bug/missing feature]\\n\\n"
        "### Reproduction\\n"
        "See reproduction.md for detailed steps.\\n\\n"
        "### Test Commands\\n"
        "[Commands that demonstrate the issue]\\n"
    ),
    "ticket_type": "issue",
    "priority": "high",
    "tags": ["bug-fix"],
})
issue_ticket_id = issue_ticket["ticket_id"]
```

**STEP 6: MOVE ISSUE TICKET TO 'EXPLORING' STATUS**

```python
mcp__hephaestus__change_ticket_status({
    "ticket_id": issue_ticket_id,
    "agent_id": "[YOUR ACTUAL AGENT ID]",
    "new_status": "exploring",
    "comment": "Issue reproduced successfully. Comprehensive investigation complete. Creating multiple exploration approaches to find complete solution."
})
```

**STEP 7: IDENTIFY 2-3 DIFFERENT SOLUTION APPROACHES**

🔧 CRITICAL: Each approach should address the COMPLETE problem, not just one aspect!

Analyze the issue and identify different COMPREHENSIVE fix strategies:
- Different ways to solve ALL aspects of the problem
- Different implementation patterns that fix everything
- Different locations/architectures that address the complete issue

When creating approaches, ensure EACH approach:
- Addresses ALL problem locations you found in your investigation
- Would pass ALL test cases you created
- Represents a COMPLETE solution, not a partial one

Think about:
- Different design patterns to solve the ENTIRE problem
- Different files/modules where the COMPLETE fix could be applied
- Different algorithmic approaches that handle ALL edge cases

**STEP 8: CREATE APPROACH TICKETS (ONE PER STRATEGY)**

🎯 CRITICAL: Each approach ticket must describe a COMPLETE solution!

For EACH approach you identified, create an approach ticket:

```python
approach_1_ticket = mcp__hephaestus__create_ticket({
    "agent_id": "[YOUR ACTUAL AGENT ID]",
    "title": f"Approach 1: [COMPLETE solution description]",
    "description": (
        f"## Exploration Approach 1\\n\\n"
        "### Strategy\\n"
        "[Describe this COMPLETE approach that addresses ALL aspects]\\n\\n"
        "### Hypothesis\\n"
        "[Why you think this approach will completely solve the problem]\\n\\n"
        "### ALL Locations That Need Changes\\n"
        "- File: [file path] Line [X]: [what needs to change]\\n"
        "- File: [file path] Line [Y]: [what needs to change]\\n"
        "- [List ALL locations you found in your investigation]\\n\\n"
        "### Complete Fix Requirements\\n"
        "[List EVERY part that needs to be fixed for this approach]\\n\\n"
        "### Success Criteria\\n"
        "- All test cases pass (including edge cases)\\n"
        "- All problem locations are addressed\\n"
        "- [Specific verification steps]\\n\\n"
        "### Parent Issue\\n"
        f"This is an exploration approach for issue ticket {issue_ticket_id}"
    ),
    "ticket_type": "approach",
    "priority": "medium",
    "tags": ["exploration", "approach-1"],
    "parent_ticket_id": issue_ticket_id,  # Child of main issue
    "blocked_by_ticket_ids": [],  # Approaches can be explored in parallel
})
approach_1_id = approach_1_ticket["ticket_id"]

approach_2_ticket = mcp__hephaestus__create_ticket({
    "agent_id": "[YOUR ACTUAL AGENT ID]",
    "title": f"Approach 2: [Different COMPLETE solution]",
    "description": "[Detailed description of COMPLETE approach 2...]",
    "ticket_type": "approach",
    "priority": "medium",
    "tags": ["exploration", "approach-2"],
    "parent_ticket_id": issue_ticket_id,
    "blocked_by_ticket_ids": [],
})
approach_2_id = approach_2_ticket["ticket_id"]

# Create approach 3 ticket if you have a third COMPLETE approach...
```

**STEP 9: CREATE PHASE 2 TASKS (ONE PER APPROACH TICKET)**

For EACH approach ticket, create a Phase 2 task. P2 now does BOTH exploration AND implementation:

```python
# Task for Approach 1
mcp__hephaestus__create_task({
    "description": f"Phase 2: Explore and implement Approach 1 - TICKET: {approach_1_id}. Investigate this approach, implement it if valid, test with reproduction script. If fix works, create P3 task. If not, mark approach as failed and create new P2 task with different strategy. See reproduction.md for test cases.",
    "done_definition": f"Approach investigated and implemented, reproduction test run, ticket {approach_1_id} moved to 'testing' status OR 'approach-failed', P3 task created if fix works OR new P2 task created if failed.",
    "agent_id": "[YOUR ACTUAL AGENT ID]",
    "phase_id": 2,
    "priority": "medium",
    "cwd": ".",
    "ticket_id": approach_1_id  # Link to approach ticket!
})

# Task for Approach 2
mcp__hephaestus__create_task({
    "description": f"Phase 2: Explore and implement Approach 2 - TICKET: {approach_2_id}. Different strategy from Approach 1. Investigate, implement, test immediately. Move to P3 if works, or create new approach if fails.",
    "done_definition": f"Approach implemented and tested, ticket {approach_2_id} status updated to 'testing' OR 'approach-failed', P3 task created if successful OR new P2 task if failed.",
    "agent_id": "[YOUR ACTUAL AGENT ID]",
    "phase_id": 2,
    "priority": "medium",
    "cwd": ".",
    "ticket_id": approach_2_id
})

# Task for Approach 3 if you created a third COMPLETE approach ticket...
```

**STEP 10: SAVE MEMORIES**

Use save_memory to document:
- Main issue ticket ID
- Key requirements from the issue
- Reproduction steps and results
- Initial hypotheses about the cause
- Test commands and their current output
- List of approach tickets created

```python
mcp__hephaestus__save_memory({
    "agent_id": "[YOUR ACTUAL AGENT ID]",
    "content": f"Main issue ticket is {issue_ticket_id}. Created {num_approaches} approach tickets for exploration: {list_of_approach_ids}. Issue reproduced - see reproduction.md.",
    "memory_type": "codebase_knowledge"
})
```

**STEP 11: MARK PHASE 1 TASK AS DONE**

```python
mcp__hephaestus__update_task_status({
    "task_id": "[your Phase 1 task ID]",
    "agent_id": "[YOUR ACTUAL AGENT ID]",
    "status": "done",
    "summary": f"Comprehensive investigation complete. Issue reproduced with comprehensive test cases covering all aspects. Main issue ticket {issue_ticket_id} created in 'exploring' status. Created {num_approaches} COMPLETE approach tickets addressing all problem locations, with corresponding Phase 2 tasks. See reproduction.md for all test cases and findings."
})
```

═══════════════════════════════════════════════════════════════════════
MANDATORY REQUIREMENTS
═══════════════════════════════════════════════════════════════════════

✅ DO:
- Read PROBLEM_STATEMENT.md thoroughly and understand ROOT CAUSE
- Search codebase COMPREHENSIVELY for ALL instances of the problem pattern
- Create test cases for ALL aspects of the issue (not just the given example)
- Reproduce the issue with clear steps and comprehensive test coverage
- Create reproduction.md with exact commands AND all test cases
- Create ONE main issue ticket
- Move issue ticket to 'exploring' status
- Identify 2-3 COMPLETE solution approaches (each addresses ALL aspects)
- Create ONE approach ticket for EACH approach describing ALL required changes
- Create ONE Phase 2 task for EACH approach ticket
- Include "TICKET: ticket-xxx" in every task description
- Save issue ticket ID and investigation findings to memory
- Document EVERYTHING clearly (all locations, all test cases, all findings)

❌ DO NOT:
- Stop at the first obvious fix location (search for ALL related issues!)
- Create shallow test cases (only testing the given example)
- Create partial approaches (each must address the COMPLETE problem)
- Try to fix the issue (Phase 2 does that)
- Create only one approach (MUST be multiple!)
- Create tasks without approach tickets
- Forget to link tasks to tickets with ticket_id parameter
- Skip the "TICKET: xxx" format in task descriptions
- Resolve tickets (only Phase 3 can resolve)

═══════════════════════════════════════════════════════════════════════
TICKET LIFECYCLE IN PHASE 1
═══════════════════════════════════════════════════════════════════════

Main Issue Ticket:
  exploration-needed → exploring (Phase 1 moves it here)

Approach Tickets:
  exploration-needed (created in this status)

Phase 2 will move approach tickets to:
  - 'testing' if implementation works
  - 'approach-failed' if implementation doesn't work or approach is invalid

Phase 3 will move to:
  - 'solved' (if all tests pass)
  - 'approach-failed' (if tests fail)

═══════════════════════════════════════════════════════════════════════

Document everything in reproduction.md file that will guide the next phases.""",
    outputs=[
        "- Main issue ticket created in 'exploring' status",
        "- 2-3 approach tickets created (one per exploration strategy)",
        "- reproduction.md containing:",
        "  * Clear, step-by-step commands to reproduce the issue",
        "  * Expected vs actual behavior",
        "  * Exact error messages or incorrect outputs",
        "  * Test commands that demonstrate the problem",
        "- Custom reproduction scripts (e.g., test_reproduction.py) if needed",
        "- Multiple Phase 2 tasks (one per approach ticket) with TICKET: xxx format",
        "- Memories saved with issue ticket ID and approach ticket IDs",
    ],
    next_steps=[
        "Phase 2 agents will explore and implement each approach in parallel",
        "Each Phase 2 agent will:",
        "  - Investigate the approach",
        "  - Implement it if valid",
        "  - Test with reproduction script",
        "  - If works → create P3 task for full testing",
        "  - If fails → mark approach-failed + create new P2 task",
        "Main issue ticket stays in 'exploring' until an approach reaches P3",
        "Failed approaches remain visible for learning",
    ],
)
