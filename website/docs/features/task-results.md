# Results Reporting System Documentation

## Table of Contents
1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Prerequisites](#prerequisites)
4. [API Reference](#api-reference)
5. [Markdown Template and Guidelines](#markdown-template-and-guidelines)
6. [Agent Integration Guide](#agent-integration-guide)
7. [Verification System](#verification-system)
8. [Frontend Integration Guide](#frontend-integration-guide)
9. [Testing Procedures](#testing-procedures)
10. [Troubleshooting Guide](#troubleshooting-guide)
11. [End-to-End Examples](#end-to-end-examples)
12. [Configuration Options](#configuration-options)

## Overview

The Results Reporting System is the third and final component in the Hephaestus trilogy (following Git Worktree Isolation and Validation Agent System). It provides a formal mechanism for agents to document their achievements, creating a permanent record of work completed with verification tracking.

### Purpose
- **Accountability**: Creates an audit trail of agent work
- **Quality Assurance**: Enables verification of claimed achievements
- **Knowledge Preservation**: Documents solutions for future reference
- **Trust Building**: Provides evidence-based validation of results

### Key Features
- Markdown-based result reporting
- Two result types: **Task-level** (`AgentResult`) and **Workflow-level** (`WorkflowResult`)
- Multiple results per task support
- Immutable result storage
- Verification status tracking
- Integration with validation system
- File size and format validation
- Path traversal protection

### Result Types

Hephaestus supports two types of results:

1. **Task-Level Results** (`AgentResult`):
   - Created via `POST /report_results` endpoint
   - Associated with a specific task
   - Verification status: `unverified`, `verified`, or `disputed`
   - Multiple results can be submitted for the same task

2. **Workflow-Level Results** (`WorkflowResult`):
   - Created via `POST /submit_result` endpoint
   - Associated with an entire workflow
   - Status: `pending_validation`, `validated`, or `rejected`
   - Automatically triggers result validator agent when configured
   - Marks workflow completion when validated

## Architecture

### System Components

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│                 │     │                  │     │                 │
│  Agent Process  │────▶│   MCP Server     │────▶│    Database     │
│                 │     │                  │     │                 │
└─────────────────┘     └──────────────────┘     └─────────────────┘
        │                       │                         │
        │                       │                         │
        ▼                       ▼                         ▼
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Markdown File  │     │ Result Service   │     │ agent_results   │
│   (results.md)  │     │   Validation     │     │     table       │
└─────────────────┘     └──────────────────┘     └─────────────────┘
```

### Database Schema

```sql
CREATE TABLE agent_results (
    id VARCHAR PRIMARY KEY,
    agent_id VARCHAR NOT NULL,
    task_id VARCHAR NOT NULL,
    markdown_content TEXT NOT NULL,
    markdown_file_path TEXT NOT NULL,
    result_type VARCHAR NOT NULL CHECK (
        result_type IN ('implementation', 'analysis', 'fix',
                       'design', 'test', 'documentation')
    ),
    summary TEXT NOT NULL,
    verification_status VARCHAR NOT NULL DEFAULT 'unverified' CHECK (
        verification_status IN ('unverified', 'verified', 'disputed')
    ),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    verified_at TIMESTAMP,
    verified_by_validation_id VARCHAR,
    FOREIGN KEY (agent_id) REFERENCES agents(id),
    FOREIGN KEY (task_id) REFERENCES tasks(id),
    FOREIGN KEY (verified_by_validation_id) REFERENCES validation_reviews(id)
);
```

### Data Flow

1. **Agent Completes Work**: Agent finishes task implementation
2. **Create Markdown Report**: Agent writes results to markdown file
3. **Submit via MCP**: Agent calls `report_results` endpoint
4. **Validation**: System validates file and ownership
5. **Storage**: Result stored in database
6. **Task Update**: Task marked as having results
7. **Verification**: Validator agent can verify results
8. **Status Update**: Verification status updated

## Prerequisites

### Required Systems
- Git Worktree Isolation System (must be implemented)
- Validation Agent System (must be implemented)
- SQLite database with proper schema
- Python 3.8+ with required dependencies
- MCP server running on port 8000

### Dependencies
```python
# Required Python packages
sqlalchemy>=1.4.0
fastapi>=0.68.0
pydantic>=1.8.0
httpx>=0.19.0
pytest>=6.2.0
pytest-asyncio>=0.15.0
```

## API Reference

### POST /report_results

Submit formal results for a completed task.

#### Request Headers
```http
X-Agent-ID: <agent-id>
Content-Type: application/json
```

#### Request Body
```json
{
    "task_id": "task-uuid",
    "markdown_file_path": "/path/to/results.md",
    "result_type": "implementation",
    "summary": "Brief summary of results"
}
```

#### Result Types
- `implementation`: Code or feature implementation
- `analysis`: Research or analysis results
- `fix`: Bug fix or issue resolution
- `design`: Design documents or architecture
- `test`: Test implementation or results
- `documentation`: Documentation creation or updates

#### Response (200 OK)
```json
{
    "status": "stored",
    "result_id": "result-uuid",
    "task_id": "task-uuid",
    "agent_id": "agent-uuid",
    "verification_status": "unverified",
    "created_at": "2024-01-01T12:00:00Z"
}
```

#### Error Responses

##### 400 Bad Request
```json
{
    "detail": "File too large: 150.00KB exceeds maximum of 100KB"
}
```

##### 404 Not Found
```json
{
    "detail": "Markdown file not found: /path/to/missing.md"
}
```

##### 403 Forbidden
```json
{
    "detail": "Task task-123 is not assigned to agent agent-456"
}
```

### Validation Rules

1. **File Existence**: File must exist and be readable
2. **File Format**: Must be markdown (.md extension)
3. **File Size**: Maximum 100KB
4. **Path Security**: No directory traversal allowed
5. **Task Ownership**: Agent must own the task
6. **Multiple Results**: Agents can submit multiple results per task
7. **Immutability**: Results cannot be modified after submission

### POST /submit_result

Submit a workflow-level result (different from task-level results).

#### Request Headers
```http
X-Agent-ID: <agent-id>
Content-Type: application/json
```

#### Request Body
```json
{
    "markdown_file_path": "/path/to/result.md",
    "explanation": "Brief explanation of what was accomplished",
    "evidence": ["Evidence item 1", "Evidence item 2"]
}
```

#### Response (200 OK)
```json
{
    "status": "submitted",
    "result_id": "result-uuid",
    "workflow_id": "workflow-uuid",
    "agent_id": "agent-uuid",
    "validation_triggered": true,
    "message": "Result submitted successfully and validation triggered",
    "created_at": "2024-01-01T12:00:00Z"
}
```

**Note**: This endpoint is for workflow-level results that mark completion of an entire workflow. It automatically derives the workflow_id from the agent's current task and may trigger result validation.

## Markdown Template and Guidelines

### Template Location
`templates/result_report_template.md`

### Required Sections

1. **Task Results Header**
   - Clear title describing the task

2. **Summary**
   - 2-3 sentence overview of achievements

3. **Detailed Achievements**
   - Bullet list of completed items
   - Technical implementation details

4. **Artifacts Created**
   - Table of files created/modified
   - Code metrics if applicable

5. **Validation Evidence**
   - Test results
   - Manual verification steps
   - Performance metrics

6. **Known Limitations**
   - Current limitations
   - Workarounds available

7. **Recommended Next Steps**
   - Immediate actions needed
   - Future enhancements

### Best Practices

```markdown
# Good Example
## Summary
Successfully implemented JWT authentication with refresh tokens,
achieving 100% test coverage and sub-100ms response times.

# Bad Example
## Summary
Done with auth stuff.
```

## Agent Integration Guide

### Step 1: Complete Your Task
```python
# Perform the actual work
result = implement_feature()
run_tests()
verify_output()
```

### Step 2: Create Markdown Report
```python
report_content = f"""# Task Results: {task_description}

## Summary
{summary_of_work}

## Detailed Achievements
{list_of_achievements}

## Artifacts Created
{table_of_files}

## Validation Evidence
{test_results}
"""

# Write to file
report_path = f"/tmp/results_{task_id}.md"
with open(report_path, 'w') as f:
    f.write(report_content)
```

### Step 3: Submit Results via MCP
```python
import httpx

async def report_results(task_id, report_path, agent_id):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/report_results",
            json={
                "task_id": task_id,
                "markdown_file_path": report_path,
                "result_type": "implementation",
                "summary": "Implemented feature successfully"
            },
            headers={"X-Agent-ID": agent_id}
        )

        if response.status_code == 200:
            result_data = response.json()
            print(f"Results stored: {result_data['result_id']}")
        else:
            print(f"Error: {response.text}")
```

### Step 4: Update Task Status
```python
# After reporting results, mark task as complete
await update_task_status(task_id, "done", summary, learnings)
```

## Verification System

### How Verification Works

1. **Initial State**: Results start as `unverified`
2. **Validation Trigger**: When task enters validation
3. **Validator Review**: Validator agent examines results
4. **Evidence Check**: Validator verifies claims against evidence
5. **Status Update**: Results marked as `verified` or `disputed`

### Verification States

| Status | Description | When Applied |
|--------|-------------|--------------|
| `unverified` | Default state | On creation |
| `verified` | Claims validated | Validation passed |
| `disputed` | Claims questioned | Validation failed |

### Integration with Validation System

```python
# In validation review handler
if validation_passed:
    # Update all results for the task to verified
    for result in task.results:
        ResultService.verify_result(
            result_id=result.id,
            validation_review_id=review.id,
            verified=True
        )
```

## Frontend Integration Guide

### Fetching Results

```javascript
// Get results for a specific task
async function getTaskResults(taskId) {
    const response = await fetch(`/api/results?task_id=${taskId}`);
    const results = await response.json();
    return results;
}
```

### Displaying Results

```jsx
function ResultCard({ result }) {
    return (
        <div className="result-card">
            <div className="result-header">
                <h3>{result.summary}</h3>
                <VerificationBadge status={result.verification_status} />
            </div>
            <div className="result-content">
                <MarkdownRenderer content={result.markdown_content} />
            </div>
            <div className="result-metadata">
                <span>Type: {result.result_type}</span>
                <span>Created: {result.created_at}</span>
                {result.verified_at && (
                    <span>Verified: {result.verified_at}</span>
                )}
            </div>
        </div>
    );
}
```

### Verification Badge Component

```jsx
function VerificationBadge({ status }) {
    const badges = {
        unverified: { icon: '⏳', color: 'gray', text: 'Unverified' },
        verified: { icon: '✅', color: 'green', text: 'Verified' },
        disputed: { icon: '⚠️', color: 'red', text: 'Disputed' }
    };

    const badge = badges[status];

    return (
        <span className={`badge badge-${badge.color}`}>
            {badge.icon} {badge.text}
        </span>
    );
}
```

## Testing Procedures

### Unit Tests

Run unit tests for the result service:
```bash
pytest tests/test_result_service.py -v
```

Run unit tests for the MCP endpoint:
```bash
pytest tests/test_mcp_results_endpoint.py -v
```

### Integration Tests

Run the full integration test:
```bash
python tests/mcp_integration/test_mcp_flow.py
```

Expected output:
```
✓ Server Health Check
✓ Create Task via MCP
✓ Get Tasks List
✓ Save Memory
✓ Update Task (Wrong Agent)
✓ Report Results
✓ Report Multiple Results
✓ Update Task (Correct Agent)
✓ Update Task (Missing Fields)
✓ Get Agent Status

All 10 tests passed!
```

### Manual Testing

1. Start the MCP server:
```bash
python run_server.py
```

2. Create a test markdown file:
```bash
echo "# Test Results\n\nTest content" > /tmp/test_results.md
```

3. Submit results via curl:
```bash
curl -X POST http://localhost:8000/report_results \
  -H "Content-Type: application/json" \
  -H "X-Agent-ID: test-agent-001" \
  -d '{
    "task_id": "task-123",
    "markdown_file_path": "/tmp/test_results.md",
    "result_type": "implementation",
    "summary": "Test implementation"
  }'
```

## Troubleshooting Guide

### Common Issues and Solutions

#### Issue: "File not found" error
**Cause**: Markdown file doesn't exist at specified path
**Solution**:
- Verify file exists: `ls -la /path/to/file.md`
- Check file permissions: `chmod 644 /path/to/file.md`
- Use absolute paths instead of relative

#### Issue: "File too large" error
**Cause**: Markdown file exceeds 100KB limit
**Solution**:
- Check file size: `du -h /path/to/file.md`
- Split into multiple results if needed
- Compress images or move to external storage

#### Issue: "Not assigned to agent" error
**Cause**: Agent trying to report results for wrong task
**Solution**:
- Verify task assignment in database
- Check agent ID in request header
- Ensure task wasn't reassigned

#### Issue: Results not being verified
**Cause**: Validation system not running or misconfigured
**Solution**:
- Check validation agent is spawned
- Verify validation_reviews table has entries
- Check worktree manager is initialized

### Debug Logging

Enable debug logging for troubleshooting:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("src.services.result_service")
```

### Database Queries for Debugging

```sql
-- Check results for a task
SELECT * FROM agent_results WHERE task_id = 'task-123';

-- Check verification status
SELECT ar.*, vr.feedback
FROM agent_results ar
LEFT JOIN validation_reviews vr ON ar.verified_by_validation_id = vr.id
WHERE ar.task_id = 'task-123';

-- Count results by status
SELECT verification_status, COUNT(*)
FROM agent_results
GROUP BY verification_status;
```

## End-to-End Examples

### Example 1: Simple Implementation Task

```python
# Agent completes implementation
async def complete_implementation_task(task_id, agent_id):
    # 1. Do the work
    implement_feature()
    run_tests()

    # 2. Create report
    report = """# Task Results: Implement User Authentication

## Summary
Implemented JWT-based authentication with refresh tokens.

## Detailed Achievements
- [x] JWT token generation
- [x] Token validation middleware
- [x] Refresh token mechanism
- [x] 15 unit tests passing

## Artifacts Created
| File Path | Type | Description |
|-----------|------|-------------|
| src/auth.py | Python | Authentication logic |
| tests/test_auth.py | Python | Unit tests |

## Validation Evidence
```
Ran 15 tests in 0.5s
OK
```
"""

    # 3. Write to file
    report_path = f"/tmp/results_{task_id}.md"
    with open(report_path, 'w') as f:
        f.write(report)

    # 4. Submit results
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/report_results",
            json={
                "task_id": task_id,
                "markdown_file_path": report_path,
                "result_type": "implementation",
                "summary": "Implemented JWT authentication"
            },
            headers={"X-Agent-ID": agent_id}
        )

        result_id = response.json()["result_id"]
        print(f"Results reported: {result_id}")

    # 5. Mark task complete
    await update_task_status(task_id, "done")
```

### Example 2: Multiple Results for Analysis Task

```python
async def report_analysis_results(task_id, agent_id):
    # First result: Initial analysis
    analysis_report = """# Task Results: Performance Analysis

## Summary
Analyzed application performance and identified bottlenecks.

## Detailed Achievements
- Profiled application under load
- Identified N+1 query problems
- Found memory leaks in cache layer
"""

    with open("/tmp/analysis.md", 'w') as f:
        f.write(analysis_report)

    await submit_result(task_id, "/tmp/analysis.md",
                       "analysis", "Performance analysis complete")

    # Second result: Optimization recommendations
    recommendations = """# Additional Results: Optimization Plan

## Summary
Detailed plan for addressing performance issues.

## Recommendations
1. Implement query batching
2. Add Redis caching layer
3. Optimize database indices
"""

    with open("/tmp/recommendations.md", 'w') as f:
        f.write(recommendations)

    await submit_result(task_id, "/tmp/recommendations.md",
                       "design", "Optimization plan created")
```

### Example 3: Fix with Validation

```python
async def fix_bug_with_validation(task_id, agent_id):
    # 1. Fix the bug
    apply_fix()

    # 2. Create detailed report with evidence
    report = """# Task Results: Fix Memory Leak in Cache Manager

## Summary
Fixed memory leak by implementing proper cleanup in cache eviction.

## Detailed Achievements
- Identified leak using memory profiler
- Implemented cleanup callbacks
- Added unit tests for cleanup
- Verified fix under load

## Validation Evidence
### Before Fix
```
Memory usage: 2.5GB after 1 hour
Growth rate: 50MB/minute
```

### After Fix
```
Memory usage: 500MB after 1 hour
Growth rate: 0MB/minute (stable)
```

## Test Results
```
pytest tests/test_cache.py::test_cleanup
===== 5 passed in 0.3s =====
```
"""

    # 3. Save and submit
    with open("/tmp/fix_results.md", 'w') as f:
        f.write(report)

    result = await submit_result(task_id, "/tmp/fix_results.md",
                                "fix", "Memory leak fixed")

    # 4. Mark task done (triggers validation if enabled)
    await update_task_status(task_id, "done")

    # 5. Result will be verified during validation
    print(f"Result {result['result_id']} awaiting verification")
```

## Configuration Options

### Current Implementation

The Results Reporting System uses hard-coded configuration values implemented in the validation layer:

**File Size Limit**:
- Maximum file size: **100 KB** (hard-coded in `src/services/validation_helpers.py`)
- Enforced by `validate_file_size()` function

**File Format**:
- Allowed format: **Markdown (.md)** only (hard-coded in `src/services/validation_helpers.py`)
- Enforced by `validate_markdown_format()` function

**Security Validation**:
- Path traversal protection enabled (checks for ".." in paths)
- Task ownership verification required
- Results are immutable after creation

### Database Indexing

Database indices are automatically managed by SQLAlchemy through foreign key relationships defined in the `AgentResult` model:

```python
# src/core/database.py - AgentResult model
class AgentResult(Base):
    __tablename__ = "agent_results"

    id = Column(String, primary_key=True)
    agent_id = Column(String, ForeignKey("agents.id"), nullable=False)
    task_id = Column(String, ForeignKey("tasks.id"), nullable=False)
    # ... other fields
```

SQLAlchemy automatically creates indices for:
- Primary key (`id`)
- Foreign keys (`agent_id`, `task_id`, `verified_by_validation_id`)

### Future Configuration Enhancements (Planned)

The following configuration options are planned for future releases:

```bash
# Planned environment variables (not yet implemented)
HEPHAESTUS_MAX_RESULT_SIZE_KB=100
HEPHAESTUS_RESULTS_DIR=/var/hephaestus/results
HEPHAESTUS_ARCHIVE_RESULTS=true
HEPHAESTUS_ARCHIVE_RETENTION_DAYS=30
```

```python
# Planned configuration class (not yet implemented)
class ResultsConfig:
    max_file_size_kb: int = 100
    allowed_file_extensions: List[str] = [".md"]
    results_directory: str = "/tmp"
    enable_archival: bool = False
    archive_retention_days: int = 30
    enable_duplicate_detection: bool = True
    duplicate_threshold: float = 0.95
```

## Performance Considerations

### Optimization Tips

1. **Batch Result Queries**: Fetch all results for a task in one query
2. **Cache Markdown Content**: Store rendered HTML to avoid re-parsing
3. **Index Frequently Queried Fields**: Add database indices as needed
4. **Compress Old Results**: Archive and compress results after 30 days
5. **Limit Result Size**: Enforce 100KB limit to prevent storage issues

### Monitoring Metrics

```python
# Key metrics to track
metrics = {
    "results_per_task": "Average number of results per task",
    "result_size_avg": "Average result file size",
    "verification_rate": "Percentage of verified results",
    "submission_latency": "Time to store result",
    "retrieval_latency": "Time to fetch results",
}
```

## Security Considerations

### Path Traversal Protection
```python
def validate_file_path(file_path: str) -> None:
    """Prevent directory traversal attacks."""
    if ".." in file_path:
        raise ValueError("Directory traversal detected")

    # Resolve to absolute path
    abs_path = os.path.abspath(file_path)

    # Ensure within allowed directories
    if not abs_path.startswith(ALLOWED_DIRS):
        raise ValueError("File outside allowed directories")
```

### Input Sanitization
- Validate all file paths
- Check file extensions
- Limit file sizes
- Sanitize markdown content
- Validate task ownership

### Access Control
- Agents can only report results for their tasks
- Results are immutable after creation
- Verification limited to validator agents
- Read access controlled by task visibility

## Support and Resources

### Documentation
- [Git Worktree Isolation System](../core/worktree-isolation.md)
- [Validation Agent System](../core/validation-system.md)
- MCP Server Documentation (see main codebase)

### Code Examples
- [Integration Tests](../tests/mcp_integration/test_mcp_flow.py)
- [Unit Tests](../tests/test_result_service.py)
- [Template](../templates/result_report_template.md)

### Troubleshooting
- Check logs in the console output or agent tmux sessions
- Enable debug mode with `LOG_LEVEL=DEBUG`
- Query database directly to inspect results:
  ```sql
  SELECT * FROM agent_results WHERE task_id = 'your-task-id';
  ```
- Use the frontend dashboard to view results and validation status

---

**Document Version**: 1.0.0
**Last Updated**: January 2024
**System Version**: Hephaestus Results Reporting System v1.0.0