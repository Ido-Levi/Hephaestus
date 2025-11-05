"""
Board Configuration for Bug Fixing Workflow

Defines the Kanban board structure for tracking issue resolution
through exploration, validation, implementation, and testing phases.
"""

from src.sdk.models import WorkflowConfig

SWEBENCH_WORKFLOW_CONFIG = WorkflowConfig(
    has_result=True,
    enable_tickets=True,  # Enable Kanban board ticket tracking
    board_config={  # Kanban board configuration - streamlined exploration workflow
        "columns": [
            {"id": "exploration-needed", "name": "🔍 Exploration Needed", "order": 1, "color": "#94a3b8"},
            {"id": "exploring", "name": "🧪 Exploring & Implementing", "order": 2, "color": "#f59e0b"},
            {"id": "testing", "name": "✅ Testing Solution", "order": 3, "color": "#8b5cf6"},
            {"id": "solved", "name": "✅ Solved", "order": 4, "color": "#10b981"},
            {"id": "approach-failed", "name": "❌ Failed Approach", "order": 5, "color": "#ef4444"}
        ],
        "ticket_types": ["issue", "approach", "investigation"],
        "default_ticket_type": "issue",
        "initial_status": "exploration-needed",
        "auto_assign": True,
        "require_comments_on_status_change": True,
        "allow_reopen": True,  # Can reopen failed approaches if new insight found
        "track_time": True
    },
    result_criteria="""VALIDATION REQUIREMENTS FOR SOLUTION ACCEPTANCE:

════════════════════════════════════════════════════════════════════
🎯 SWEBENCH BENCHMARK CONTEXT
════════════════════════════════════════════════════════════════════

You are validating a real-world bug fix from a popular open-source repository
submitted as part of **SWEBench-Verified**, a rigorous AI benchmark for
evaluating code generation and bug-fixing capabilities.

**SWEBench Rules (MANDATORY):**
1. 🚨 **NO TEST FILE MODIFICATIONS** - Solutions fix SOURCE CODE to pass EXISTING tests
2. 🚨 **PATCH MUST APPLY CLEANLY** - Use `git apply` to validate
3. 🚨 **ALL TESTS MUST PASS** - No regression allowed
4. 🚨 **MINIMAL CHANGES ONLY** - Only fix what's broken, nothing more

**Success Criteria:**
- Patch applies to base commit without errors
- All existing tests pass (100% pass rate)
- Original issue is completely resolved
- No test files modified
- No unrelated changes included

**Your Mission:**
Validate this bug fix with the same rigor as reviewing a pull request for
the actual open-source project. Be thorough, be strict, and reject anything
that doesn't meet production quality standards.

════════════════════════════════════════════════════════════════════
CRITICAL: INDEPENDENT VALIDATION - YOU MUST VERIFY FROM SCRATCH!
════════════════════════════════════════════════════════════════════

**YOUR VALIDATION PROCESS:**

You are validating a bug fix solution. You MUST independently verify the fix by:
1. Cloning the repository from scratch (DO NOT use existing worktrees)
2. Reproducing the original issue to confirm it exists
3. Applying the submitted patch
4. Verifying the fix works with all test cases

**REPOSITORY DETAILS:**

Repository: {REPO_URL}
Commit SHA: {COMMIT_SHA}

**Problem Statement:**
{PROBLEM_STATEMENT}

**STEP-BY-STEP VALIDATION INSTRUCTIONS:**

STEP 1: Clone Fresh Repository
```bash
# Clone to a new temporary location
git clone {REPO_URL} /tmp/validation_repo_<random_suffix>
cd /tmp/validation_repo_<random_suffix>

# Checkout the exact commit
git checkout {COMMIT_SHA}
```

STEP 2: Reproduce Original Issue (BEFORE applying patch)
- Read the submitted reproduction_instructions.md (in extra_files)
- Follow the reproduction steps exactly
- Verify the bug/issue exists
- Document the buggy behavior
- **CRITICAL:** If you cannot reproduce the issue, validation FAILS

🚨🚨🚨 STEP 3: APPLY THE SUBMITTED PATCH (CRITICAL!) 🚨🚨🚨

**THIS IS THE MOST IMPORTANT VALIDATION STEP - DO NOT SKIP!**

Many submissions have patches that LOOK valid but DO NOT APPLY or DO NOT WORK!
You MUST verify the patch applies cleanly and solves the issue!

```bash
# Copy the solution.patch from extra_files
cp /path/to/extra_files/solution.patch /tmp/validation_repo_<random_suffix>

# Attempt to apply the patch
echo "🧪 CRITICAL: Applying patch to verify it works..."
if ! git apply solution.patch; then
    echo "🚨 VALIDATION FAILED: Patch does NOT apply cleanly!"
    echo "This is an INVALID submission - REJECT immediately!"
    # Document the exact error message
    git apply solution.patch 2>&1 | tee patch_error.log
    exit 1
fi

echo "✅ Patch applied successfully"

# VERIFY git status shows changes
git status
git diff --stat

# If no changes after applying patch, something is wrong!
if [ -z "$(git status --porcelain)" ]; then
    echo "🚨 ERROR: Patch applied but made NO changes!"
    echo "This is an INVALID patch - REJECT!"
    exit 1
fi
```

**IF PATCH FAILS TO APPLY:**
- REJECT the submission immediately
- Document the exact error: "Patch failed to apply: [error message]"
- Common issues: wrong paths, line number mismatches, whitespace problems
- This is an AUTOMATIC REJECTION - do not try to "fix" the patch

🚨🚨🚨 STEP 4: VERIFY FIX ACTUALLY WORKS (MANDATORY!) 🚨🚨🚨

**After applying patch, you MUST verify it solves the issue!**

🚨🚨🚨 CRITICAL: RUN THE FULL TEST SUITE AFTER APPLYING THE PATCH! 🚨🚨🚨

Many validators skip this step - DON'T! You MUST run ALL tests AFTER applying the patch!

```bash
# STEP 4A: Run the reproduction test from reproduction_instructions.md
echo "🧪 CRITICAL: Running reproduction test to verify fix works..."
[FOLLOW THE EXACT STEPS FROM reproduction_instructions.md]

# The issue should now be FIXED
# Document the output - it should show the fix working

# STEP 4B: Run ALL test cases mentioned in reproduction_instructions.md
echo "🧪 Running all specific test cases..."
[RUN EACH TEST CASE FROM reproduction_instructions.md]

# EVERY test case must pass!
# If ANY test case fails, validation FAILS!

# STEP 4C: 🚨🚨🚨 RUN THE FULL TEST SUITE TO CHECK FOR REGRESSIONS 🚨🚨🚨
echo "🧪 CRITICAL: Running FULL test suite to check for regressions..."
echo "This is MANDATORY - do not skip this step!"

# Find the test command from reproduction_instructions.md
# Examples: pytest, python -m pytest, npm test, make test, tox, etc.
[RUN THE FULL TEST SUITE COMMAND FROM reproduction_instructions.md]

# 🚨 DOCUMENT THE COMPLETE OUTPUT!
# - Total number of tests run
# - Number passed
# - Number failed (MUST be 0)
# - Any warnings or errors

echo "📊 Test Results:"
echo "Total: [X] tests"
echo "Passed: [X] tests"
echo "Failed: [Y] tests"

# 🚨 IF ANY TEST FAILS -> REJECT IMMEDIATELY!
if [ "$FAILED_COUNT" -gt 0 ]; then
    echo "🚨 VALIDATION FAILED: $FAILED_COUNT tests failed after applying patch!"
    echo "This indicates either:"
    echo "  1. The patch causes regressions"
    echo "  2. The patch doesn't fully fix the issue"
    echo "  3. The patch is incomplete"
    echo ""
    echo "REJECT THIS SUBMISSION!"
    exit 1
fi

echo "✅ ALL TESTS PASS - No regressions detected!"
```

**YOU MUST:**
- ✅ Verify reproduction test NOW PASSES (issue is fixed)
- ✅ Run EVERY test case from reproduction_instructions.md
- ✅ Confirm ALL edge cases work correctly
- ✅ 🚨🚨🚨 RUN THE FULL TEST SUITE TO CHECK FOR REGRESSIONS (MANDATORY!) 🚨🚨🚨
- ✅ Document COMPLETE output from full test suite showing everything works
- ✅ Verify test count is reasonable (not 0 or suspiciously low)

**IF ANY TEST FAILS AFTER APPLYING PATCH:**
- REJECT the submission immediately
- Document which tests failed and why
- Document the full test output showing failures
- The patch does NOT solve the issue correctly - REJECT!

════════════════════════════════════════════════════════════════════
VALIDATION REQUIREMENTS (ALL MUST BE MET):
════════════════════════════════════════════════════════════════════

1. **ISSUE REQUIREMENTS VERIFICATION** (MANDATORY)
   ✓ Every requirement from the problem statement is addressed
   ✓ Expected behavior exactly matches issue description
   ✓ All edge cases mentioned in the issue are handled correctly
   ✓ No unintended side effects introduced

2. **TEST SUITE VALIDATION** (MANDATORY)
   ✓ Full test suite runs successfully (provide complete output)
   ✓ ALL existing tests pass - NO REGRESSION allowed
   ✓ Tests specific to the issue pass (if they exist)
   ✓ Any new tests added for the fix also pass
   ✓ Include the exact test commands and their full output

3. **REPRODUCTION EVIDENCE** (MANDATORY)
   ✓ Original failing case now works correctly
   ✓ Before/after behavior clearly demonstrated
   ✓ Console output, error messages, or results showing the fix
   ✓ Step-by-step reproduction instructions included

4. **CODE QUALITY VERIFICATION** (MANDATORY)
   ✓ Changes follow project's coding conventions
   ✓ No linting errors or warnings introduced
   ✓ No type checking errors (if applicable)
   ✓ Code is clean, readable, and maintainable
   ✓ Only necessary changes included (no extra modifications)

5. **PATCH VALIDATION** (MANDATORY)
   ✓ Complete git patch included in submission
   ✓ 🚨 CRITICAL: Patch contains NO test file modifications (tests/, test/, *_test.py, *_tests.py)
   ✓ Patch applies cleanly to the base commit
   ✓ Patch contains ONLY source code changes (no test modifications!)
   ✓ Patch format is correct and can be applied with git apply

════════════════════════════════════════════════════════════════════
REQUIRED SUBMISSION FORMAT:
════════════════════════════════════════════════════════════════════

The submission markdown file MUST include these sections:

## 1. Problem Summary
- Brief description of the issue
- Key requirements addressed

## 2. Solution Overview
- What was changed and why
- Files modified with brief explanations

## 3. Test Results
```
[FULL test suite output showing all tests passing]
```

## 4. Reproduction Evidence
- Before: [Show the failing case]
- After: [Show the working case]
- Include exact commands and outputs

## 5. Code Quality Checks
- Linting results (if applicable)
- Type checking results (if applicable)

## 6. Git Patch
```patch
[COMPLETE git diff patch that can be applied with git apply]
```

════════════════════════════════════════════════════════════════════
VALIDATION DECISION CRITERIA:
════════════════════════════════════════════════════════════════════

✅ APPROVE if and only if:
   - ALL mandatory requirements are met
   - Patch contains ZERO test file modifications
   - Test suite fully passes with no regression
   - Patch is clean and minimal
   - Evidence clearly demonstrates the fix works

❌ REJECT IMMEDIATELY if:
   - `solution.patch` is missing!!!
   - 🚨 Patch modifies ANY test files (tests/, test/, *_test.py) - AUTOMATIC REJECTION!
   - Any test fails or shows regression
   - Requirements not fully addressed
   - Patch includes unnecessary changes
   - Missing evidence of fix working
   - Code quality issues present

When validating:
1. 🚨 FIRST: Check patch for test file modifications - if found, REJECT immediately
2. 🚨 SECOND: Apply patch with `git apply` - if fails, REJECT immediately
3. 🚨 THIRD: Run reproduction test after applying - if fails, REJECT immediately
4. Check that all tests pass (no "trust" - verify the output)
5. Confirm the specific issue is fixed
6. Ensure no extra changes snuck in
7. Validate code quality and style

════════════════════════════════════════════════════════════════════
🚨🚨🚨 CRITICAL VALIDATION CHECKLIST - FOLLOW THIS EXACTLY! 🚨🚨🚨
════════════════════════════════════════════════════════════════════

Before approving ANY submission, you MUST complete this checklist:

☐ 1. Cloned fresh repository to /tmp/validation_repo_<random_suffix>
☐ 2. Checked out exact commit SHA
☐ 3. Reproduced original issue (confirmed bug exists)
☐ 4. Read solution.patch from extra_files
☐ 5. **ATTEMPTED TO APPLY PATCH WITH `git apply solution.patch`**
☐ 6. **VERIFIED PATCH APPLIED WITHOUT ERRORS**
☐ 7. **VERIFIED `git status` shows changes after applying patch**
☐ 8. **RAN REPRODUCTION TEST AFTER APPLYING PATCH**
☐ 9. **VERIFIED ISSUE IS NOW FIXED**
☐ 10. **RAN ALL TEST CASES from reproduction_instructions.md**
☐ 11. 🚨🚨🚨 **RAN THE FULL TEST SUITE AFTER APPLYING PATCH** 🚨🚨🚨
☐ 12. 🚨🚨🚨 **VERIFIED ALL TESTS IN FULL SUITE PASS (NO REGRESSIONS)** 🚨🚨🚨
☐ 13. **DOCUMENTED COMPLETE TEST OUTPUT (test counts, pass/fail numbers)**
☐ 14. Checked patch contains NO test file modifications
☐ 15. Verified no regression in existing functionality
☐ 16. Confirmed code quality is acceptable

**IF ANY CHECKBOX IS UNCHECKED OR FAILED:**
- ❌ VALIDATION FAILS
- ❌ REJECT THE SUBMISSION
- ❌ Document which step failed and why

**NEVER APPROVE A SUBMISSION WHERE:**
- Patch doesn't apply cleanly
- Tests fail after applying patch
- Issue is not actually fixed
- Patch modifies test files

════════════════════════════════════════════════════════════════════

REMEMBER: The goal is a production-ready patch that:
1. **APPLIES CLEANLY** (test with `git apply`)
2. **SOLVES THE ISSUE** (verify by running reproduction test)
3. **PASSES ALL TESTS** (🚨 YOU MUST RUN THE FULL TEST SUITE - no shortcuts!)
4. **NO REGRESSIONS** (all existing tests still pass after patch applied)
5. **CONTAINS NO TEST MODIFICATIONS** (only source code changes)

**BE THOROUGH AND STRICT - INVALID PATCHES WASTE EVERYONE'S TIME!**
**MISSING solution.patch FILE = AUTOMATIC REJECTION!**
**MISSING solution.patch FILE = AUTOMATIC REJECTION!**
**MISSING solution.patch FILE = AUTOMATIC REJECTION!**

🚨🚨🚨 COMMON MISTAKE TO AVOID 🚨🚨🚨
Many validators only run the reproduction test and skip the full test suite!
This is WRONG! You MUST run the complete test suite to check for regressions!
If you don't run all tests, you might approve a patch that breaks other functionality!""",
    on_result_found="stop_all",
)
