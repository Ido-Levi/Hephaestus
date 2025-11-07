"""
Board Configuration for PRD to Software Workflow

Defines the Kanban board structure and workflow configuration.
"""

from src.sdk.models import WorkflowConfig

PRD_WORKFLOW_CONFIG = WorkflowConfig(
    has_result=True,
    enable_tickets=True,  # Enable Kanban board ticket tracking
    board_config={  # Kanban board configuration - 3-phase workflow (Phase 1: Analysis, Phase 2: Plan & Impl, Phase 3: Validate & Doc)
        "columns": [
            {"id": "backlog", "name": "📋 Backlog", "order": 1, "color": "#94a3b8"},
            {"id": "building", "name": "🔨 Building", "order": 2, "color": "#f59e0b"},
            {"id": "building-done", "name": "✅ Building Done", "order": 3, "color": "#fcd34d"},
            {"id": "validating", "name": "🧪 Validating", "order": 4, "color": "#8b5cf6"},
            {"id": "validating-done", "name": "✅ Validating Done", "order": 5, "color": "#c4b5fd"},
            {"id": "done", "name": "✅ Done", "order": 6, "color": "#22c55e"}
        ],
        "ticket_types": ["component", "bug", "design-revision", "documentation"],
        "default_ticket_type": "component",
        "initial_status": "backlog",
        "auto_assign": True,
        "require_comments_on_status_change": True,
        "allow_reopen": True,
        "track_time": True,

        # Human Approval Configuration
        "ticket_human_review": False,  # Disabled by default - set to True to enable human approval
        "approval_timeout_seconds": 1800,  # 30 minutes timeout (default)
    },
    result_criteria="""VALIDATION REQUIREMENTS FOR SOFTWARE BUILDER COMPLETION:

════════════════════════════════════════════════════════════════════
CRITICAL: PROJECT IS ONLY COMPLETE IF ALL REQUIREMENTS ARE MET
════════════════════════════════════════════════════════════════════

1. **REQUIREMENTS COVERAGE** (MANDATORY)
   ✓ Every requirement from PRD is addressed
   ✓ All functional requirements implemented
   ✓ All non-functional requirements met (performance, security, etc.)
   ✓ No missing features or capabilities

2. **CODE QUALITY** (MANDATORY)
   ✓ All components implemented and working
   ✓ Code follows language/framework best practices
   ✓ No linting errors or warnings
   ✓ No type checking errors (if applicable)
   ✓ Code is clean, readable, and maintainable

3. **TESTING** (MANDATORY)
   ✓ Comprehensive test suite exists
   ✓ ALL tests pass (100% pass rate)
   ✓ Test coverage >80% (provide coverage report)
   ✓ Unit tests for all components
   ✓ Integration tests for component interactions
   ✓ End-to-end tests for critical workflows

4. **DOCUMENTATION** (MANDATORY)
   ✓ README with overview and quick start
   ✓ API documentation complete
   ✓ Usage examples provided and tested
   ✓ Deployment guide exists and works
   ✓ Architecture documented

5. **DEPLOYABILITY** (MANDATORY)
   ✓ Application runs successfully
   ✓ Deployment instructions tested and work
   ✓ Configuration documented
   ✓ Dependencies listed and installable
   ✓ No critical security vulnerabilities

════════════════════════════════════════════════════════════════════
REQUIRED SUBMISSION FORMAT:
════════════════════════════════════════════════════════════════════

Submit SOLUTION.md with:

## 1. Project Overview
- What was built
- Key features implemented
- Architecture decisions

## 2. Requirements Coverage
- List each requirement from PRD
- Mark each as ✅ Implemented with evidence

## 3. Test Results
```
[FULL test suite output showing 100% pass rate]
[Coverage report showing >80% coverage]
```

## 4. Deployment Evidence
```
[Commands to deploy]
[Screenshot or log showing app running]
```

## 5. Documentation
- Link to README
- Link to API docs
- Link to deployment guide

## 6. Code Quality
```
[Linting results - clean]
[Type checking results - clean]
```

════════════════════════════════════════════════════════════════════
VALIDATION DECISION CRITERIA:
════════════════════════════════════════════════════════════════════

✅ APPROVE if and only if:
   - ALL requirements from PRD implemented
   - Test suite comprehensive and 100% passing
   - Documentation complete and accurate
   - Application deploys and runs successfully
   - Code quality meets standards

❌ REJECT if:
   - Any PRD requirement missing or incomplete
   - Tests failing or insufficient coverage
   - Documentation incomplete or inaccurate
   - Application doesn't run or deploy
   - Code quality issues present
   - Security vulnerabilities exist

When validating:
1. Check each PRD requirement has corresponding implementation
2. Verify test results (don't trust - verify the output)
3. Actually run deployment instructions
4. Review code quality reports
5. Confirm documentation is accurate

REMEMBER: The goal is production-ready software that fully satisfies
the PRD. Be thorough and strict in validation.""",
    on_result_found="stop_all",
)
