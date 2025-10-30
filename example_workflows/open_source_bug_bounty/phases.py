"""
Open Source Bug Bounty Hunter - Python Phase Definitions

This file defines the phases for hunting security vulnerabilities in open source projects.
These phases systematically discover, investigate, and exploit security bugs for HackerOne submission.

Usage:
    from example_workflows.open_source_bug_bounty.phases import BUGBOUNTY_PHASES, BUGBOUNTY_WORKFLOW_CONFIG
    sdk = HephaestusSDK(
        phases=BUGBOUNTY_PHASES,
        workflow_config=BUGBOUNTY_WORKFLOW_CONFIG,
        working_directory="/path/to/target_project",
        ...
    )
"""

from src.sdk.models import Phase, WorkflowConfig

# Phase definitions for open source bug bounty hunting
BUGBOUNTY_PHASES = [
    Phase(
        id=1,
        name="environment_research_and_setup",
        description="""[This is Phase 1 - Environment Research & Production Setup]

FOCUS: Analyze the open source project to understand its type and architecture, then set up
a local production-like environment where security vulnerabilities can be actually tested
and exploited. Create comprehensive documentation for other agents on how to interact
with this environment.

This phase transforms static code analysis into real security testing by providing
a live, realistic target environment that matches the project's actual deployment patterns.""",
        done_definitions=[
            "Project type and architecture thoroughly analyzed (web app, CLI, library, etc.)",
            "Production deployment patterns researched and understood",
            "CRITICAL: Ports 8000, 3000, and 6333 AVOIDED - no conflicts with Hephaestus services",
            "Docker-based local environment created matching real-world setup with alternative ports",
            "All necessary services configured (databases, redis, external APIs, etc.)",
            "Realistic sample data and test scenarios implemented",
            "environment_setup.md created with comprehensive setup documentation",
            "security_test_guide.md created for other phases with testing instructions",
            "TEST SCRIPTS CREATED: test_environment.sh, validate_services.py, sample_data_test.py, reset_environment.py",
            "MANDATORY VALIDATION: All test scripts executed and verified to PASS 100%",
            "validation_results.md created with complete test execution logs and status",
            "Docker containers up and running in healthy state (docker ps shows all services healthy)",
            "ALL services tested and fully functional - NO failures or errors",
            "CRITICAL: Phase 2 task created ONLY after all validation tests pass",
            "Memory entries saved with environment details for other agents",
        ],
        working_directory=".",
        additional_notes="""YOUR MISSION: CREATE A TESTING ENVIRONMENT FOR THE TARGET PROJECT!

UNDERSTAND THE TARGET vs ENVIRONMENT DISTINCTION:
- TARGET PROJECT: The original open source code you're analyzing for vulnerabilities
- TESTING ENVIRONMENT: A demo app you create ONLY to validate exploitation techniques

CRITICAL CONCEPT: You are NOT finding vulnerabilities in your demo app!
Your demo app is a "shooting range" - it exists to help other agents test whether
vulnerabilities they find in the TARGET PROJECT are actually exploitable.

YOUR PRIMARY GOAL:
1. Analyze the TARGET PROJECT (original codebase)
2. Create a demo app that mimics the TARGET PROJECT's technology and patterns
3. Set up environment so agents can test exploits against something realistic

WHAT YOUR DEMO APP SHOULD DO:
- Use the same frameworks/libraries as the TARGET PROJECT
- Have similar functionality patterns (auth, file handling, etc.)
- Include intentional vulnerabilities that match patterns found in TARGET PROJECT
- Serve as a testbed for validating exploits discovered in TARGET PROJECT

WHAT YOUR DEMO APP SHOULD NOT DO:
- Be the primary target for vulnerability discovery
- Replace analysis of the original TARGET PROJECT
- Become the focus of security testing (it's just a tool!)

CRITICAL PORT CONFLICT WARNING:
NEVER use ports 8000, 3000, or 6333 for your testing environment!
- Port 8000: Reserved for Hephaestus MCP server
- Port 3000: Common development port (avoid conflicts)
- Port 6333: Reserved for Qdrant vector database

If the target project normally uses these ports, you MUST reconfigure it to use
alternative ports. Document the port mappings clearly in your environment setup.

CRITICAL WORKFLOW REQUIREMENT:
You MUST create the Phase 2 task BEFORE marking your task as done! The workflow
cannot continue without Phase 2 being created. This is the most important requirement
- without it, the entire bug bounty process stops.

ENVIRONMENT TESTING IMPERATIVE:
Your environment must be ACTUALLY WORKING, not just theoretically configured.
You must personally test every service, every endpoint, every functionality.
If services are failing, you must fix them before completing your task.

PHASE 1 FOCUS: SETUP ONLY!
Your job is environment setup and validation, NOT security analysis:
- ✅ Set up working environment
- ✅ Test everything thoroughly
- ✅ Create documentation for others
- ✅ Create Phase 2 task
- ❌ NO attack surface analysis (that's Phase 2's job)
- ❌ NO vulnerability hunting (that's Phase 3's job)
- ❌ NO security testing (that's for later phases)

STEP 1: PROJECT ANALYSIS & RESEARCH

MANDATORY READING - Start with these files:
1. README.md - Understand what this project does and how it works
2. CONTRIBUTING.md - Learn development setup and deployment patterns
3. Container files (Dockerfile, docker-compose.yml, etc.) - Check for existing containerization
4. Dependency files (requirements.txt, package.json, Cargo.toml, etc.) - Identify dependencies and tech stack
5. docs/ directory - Look for deployment and architecture documentation

CRITICAL PORT CONFLICT AVOIDANCE:
NEVER use these ports for your testing environment:
- PORT 8000 - Reserved for Hephaestus MCP server
- PORT 3000 - Common development port, avoid conflicts
- PORT 6333 - Reserved for Qdrant vector database

Always choose different ports for your services. If the project normally uses these ports,
you MUST reconfigure it to use alternative ports to avoid conflicts with Hephaestus services.

STEP 1A: ANALYZE THE TARGET PROJECT
BEFORE creating any demo app, you must thoroughly analyze the TARGET PROJECT:

MANDATORY TARGET PROJECT ANALYSIS:
1. Read and understand what the TARGET PROJECT actually does
2. Identify the main functionality and purpose of the TARGET PROJECT
3. Map the technology stack used by the TARGET PROJECT
4. Understand how users interact with the TARGET PROJECT
5. Identify the security-relevant components in the TARGET PROJECT

TARGET PROJECT FOCUS AREAS:
- What is this library/app supposed to do?
- How do developers integrate and use this TARGET PROJECT?
- What are the main entry points and interfaces?
- What kind of data does it handle/process?
- What external systems does it interact with?

DOCUMENT THE TARGET PROJECT:
Create target_project_analysis.md with:
- Project purpose and functionality
- Technology stack and dependencies
- Usage patterns and integration methods
- Potential security areas to investigate later
- Integration points where vulnerabilities might exist

PROJECT CLASSIFICATION - Determine what type of TARGET PROJECT this is:

WEB APPLICATION:
- Needs HTTP server, database, possibly cache/queue services
- Create sample API endpoints with vulnerable functionality
- Set up authentication flows and user management
- Configure realistic routing and middleware

CLI TOOL:
- Create interactive test harness with command inputs
- Set up file system scenarios for testing
- Mock external dependencies and system interactions
- Create test datasets and configurations

LIBRARY/SDK:
- Build demo application that uses the library
- Create test scenarios covering main functionality
- Set up integration testing environment
- Document library usage patterns and attack surfaces

MICROSERVICES:
- Identify service boundaries and communication patterns
- Set up multiple containers representing different services
- Configure service discovery and load balancing
- Create realistic inter-service communication scenarios

STEP 2: ENVIRONMENT SETUP STRATEGY

ENVIRONMENT SETUP STRATEGY:

Based on your project analysis, determine the appropriate environment setup:

For each project type, research and implement:
- Container configuration appropriate to the TARGET PROJECT's tech stack
- Service dependencies (databases, caches, external APIs)
- Network configuration and service discovery
- Data initialization and sample content
- Security configurations that mimic real TARGET PROJECT deployments

STEP 1B: DESIGN DEMO APP BASED ON TARGET PROJECT
Your demo app MUST reflect the TARGET PROJECT's characteristics:

DEMO APP DESIGN PRINCIPLES:
- Same technology stack as TARGET PROJECT
- Similar functionality patterns as TARGET PROJECT
- Same data types and processing as TARGET PROJECT
- Same integration points as TARGET PROJECT
- Same security boundaries as TARGET PROJECT

EXAMPLE: If TARGET PROJECT is a Python authentication library:
- Demo app: Python web app that USES the authentication library
- Focus: Test vulnerabilities in how the library handles auth
- NOT: Find vulnerabilities in the demo app itself

EXAMPLE: If TARGET PROJECT is a file processing library:
- Demo app: Application that processes files using the library
- Focus: Test vulnerabilities in the library's file handling
- NOT: Find vulnerabilities in the demo app's file upload

SAMPLE DATA CREATION:
- Create realistic test data similar to what TARGET PROJECT handles
- Generate sample scenarios that mirror TARGET PROJECT use cases
- Set up configurations that mimic real TARGET PROJECT deployments
- Create test scenarios that help validate TARGET PROJECT vulnerabilities

THE GOAL:
Your demo app helps other agents answer: "If we find vulnerability X in TARGET PROJECT,
can we actually exploit it in a realistic scenario?"

STEP 3: COMPREHENSIVE ENVIRONMENT VALIDATION
THIS STEP IS MANDATORY AND CANNOT BE SKIPPED!

COMPREHENSIVE ENVIRONMENT TESTING - MANDATORY:
YOU MUST PERSONALLY TEST EVERYTHING! No assumptions allowed:

BASIC SERVICE TESTING:
- Start all services and verify they're running without errors
- Check container logs for any startup failures or issues
- Test main application functionality with real requests
- Verify all services are accessible on their designated ports

CONNECTIVITY TESTING:
- Test database connections and actually run queries
- Verify cache/queue services respond to commands
- Test inter-service communication works properly
- Validate external service integrations (if any)

FUNCTIONALITY TESTING:
- Test authentication flows with actual login/logout
- Create/read/update/delete operations to verify data persistence
- Test file operations with actual file uploads/downloads
- Verify API endpoints return proper responses

CREATE SANITY TEST SCRIPTS:
You must create test scripts that other agents can run:
- test_environment.sh - Basic connectivity and functionality test
- validate_services.py - Programmatic testing of all services
- sample_data_test.py - Verify sample data is accessible
- reset_environment.py - Reset environment to clean state

RUN FULL SANITY CHECKS:
Execute your test scripts and ensure they pass completely.
Document any issues and fix them before proceeding.
Only when ALL tests pass is your environment truly ready.

FAILURE IS NOT AN OPTION:
If any service fails to start or any test fails, you MUST:
1. Identify the root cause
2. Fix the issue completely
3. Re-test until everything works
4. Document the fix for future reference

DO NOT proceed to Phase 2 task creation until environment is fully functional!

STEP 4: FINAL VALIDATION & SCRIPT EXECUTION
CRITICAL: This step must be completed BEFORE creating Phase 2 task!

MANDATORY VALIDATION EXECUTION:
You MUST run all test scripts you created and ensure they pass completely:

EXECUTE ALL TEST SCRIPTS IN ORDER:
1. Run test_environment.sh - Basic connectivity and functionality
2. Run validate_services.py - Programmatic testing of all services
3. Run sample_data_test.py - Verify sample data accessibility
4. Run reset_environment.py - Reset to clean state and verify

DOCUMENT VALIDATION RESULTS:
Create validation_results.md with:
```
# Environment Validation Results

## Test Script Execution Results

### test_environment.sh
- Status: [PASSED/FAILED]
- Output: [Full script output]
- Issues Found: [Any issues and how they were resolved]

### validate_services.py
- Status: [PASSED/FAILED]
- Output: [Full script output]
- Services Tested: [List of services tested]
- Issues Found: [Any issues and how they were resolved]

### sample_data_test.py
- Status: [PASSED/FAILED]
- Output: [Full script output]
- Data Verified: [Types of data tested]
- Issues Found: [Any issues and how they were resolved]

### reset_environment.py
- Status: [PASSED/FAILED]
- Output: [Full script output]
- Reset Verified: [What was reset]
- Issues Found: [Any issues and how they were resolved]

## Final Validation Status
OVERALL STATUS: [PASSED/FAILED]
ALL SCRIPTS MUST PASS BEFORE PROCEEDING!

## Issues Resolution Log
[Document any issues found and how they were fixed]
```

MANDATORY VALIDATION CRITERIA:
- ALL test scripts must execute without errors
- ALL containers must be running in healthy state
- ALL services must be accessible and functional
- ALL sample data must be accessible and verifiable
- NO errors or warnings in container logs
- Full connectivity between all services verified

IF ANY TEST FAILS:
1. STOP - Do NOT proceed to task creation
2. IDENTIFY the root cause of failure
3. FIX the issue completely
4. RE-RUN all validation tests
5. ONLY proceed when ALL tests pass 100%

STEP 5: DOCUMENTATION CREATION

CREATE environment_setup.md:
```markdown
# Security Testing Environment Setup

## Target Project Analysis
## TARGET PROJECT: [Original project name and purpose]
- What this project does: [brief description]
- How it's used: [integration/usage patterns]
- Main functionality: [key features]
- Technology stack: [frameworks, languages]
- Security relevance: [why this project matters for security]

## Demo Application Purpose
DEMO APP IS FOR TESTING ONLY - NOT THE TARGET!
This demo application helps validate exploits discovered in the TARGET PROJECT.
It mimics the TARGET PROJECT's technology and usage patterns.

## Services Configuration
### Demo Application (Testing Tool)
- Service: [service name]
- Access: [how to access the demo app]
- Purpose: Validates exploits for TARGET PROJECT
- Health Check: [how to verify it's running]

### Supporting Services
- Database: [type, access method, connection details]
- Cache/Queue: [type, access method, connection details]
- Other Services: [description and access details]

## How to Use This Environment
1. Analyze TARGET PROJECT code for vulnerabilities
2. Use demo app to test if those vulnerabilities are exploitable
3. Demo app proves exploitability, TARGET PROJECT has the actual vulnerability

## Access Credentials
- Demo app credentials: [for testing exploits]
- Service access: [database, cache credentials]

## Testing Data
- Sample data: [mirrors TARGET PROJECT data types]
- Test scenarios: [based on TARGET PROJECT use cases]

## Common Operations
- Service management: [start/stop/restart commands]
- Log viewing: [how to view different service logs]
- Debug access: [how to access services for debugging]

REMINDER: Focus on TARGET PROJECT vulnerabilities, not demo app issues!
```

CREATE security_test_guide.md:
```markdown
# Security Testing Guide for Agents

## TARGET PROJECT FOCUS
ALWAYS REMEMBER: TARGET PROJECT is the focus, demo app is the tool!

## Primary Analysis: TARGET PROJECT
- Analyze TARGET PROJECT code for vulnerabilities
- Look for security issues in the original codebase
- Identify vulnerable patterns in TARGET PROJECT
- Map attack surfaces in TARGET PROJECT

## Secondary Tool: Demo Application
- Use demo app ONLY to validate TARGET PROJECT vulnerabilities
- Test whether vulnerabilities found in TARGET PROJECT are exploitable
- Demo app provides realistic testing environment
- Demo app proves exploitability, doesn't contain the vulnerabilities

## Testing Strategy
1. TARGET PROJECT Analysis: Find vulnerabilities in original code
2. Demo App Validation: Test if those vulnerabilities can be exploited
3. Exploit Development: Build exploits that work in realistic scenarios
4. Impact Verification: Demonstrate security consequences

## Environment Interaction Rules
- PRIMARY: Analyze TARGET PROJECT code
- SECONDARY: Use demo app for exploit validation
- Document TARGET PROJECT vulnerabilities, not demo app issues
- Test exploits against demo app, but discoveries come from TARGET PROJECT
- Focus on security impact in real TARGET PROJECT usage

## Success Criteria
A vulnerability from TARGET PROJECT is "confirmed" when:
1. Vulnerability exists in TARGET PROJECT code
2. Exploit works against demo app (proves exploitability)
3. Security impact demonstrated in realistic scenario
4. Exploit is reproducible and reliable
5. Evidence shows real-world security consequences for TARGET PROJECT users

## CRITICAL: Don't Hunt Demo App Vulnerabilities!
- Demo app vulnerabilities = NOT your focus
- TARGET PROJECT vulnerabilities = YOUR focus
- Demo app = Testing tool only
- TARGET PROJECT = Actual target
```

STEP 5: MEMORY INTEGRATION

SAVE CRITICAL ENVIRONMENT INFO:
"TARGET PROJECT Analysis Complete: [Project Name] is [type] with [Key Technologies].
Purpose: [what TARGET PROJECT does]. Integration: [how it's used].
Security relevance: [why TARGET PROJECT matters for security]."

"Demo Environment Ready: [Tech stack matching TARGET PROJECT].
Services: [list of services and access for exploit validation].
Auth: [test credentials for demo app].
Purpose: Demo app validates TARGET PROJECT vulnerability exploitability."

"Testing Strategy: PRIMARY focus on TARGET PROJECT code analysis.
SECONDARY use of demo app for exploit validation.
All agents: Analyze TARGET PROJECT, validate with demo app."

CRITICAL FINAL STEP - CREATE PHASE 2 TASK:
Use the mcp__hephaestus__create_task endpoint to create the next phase task:
```
Task Description: "Phase 2: Perform code reconnaissance and strategic targeting for security vulnerability assessment using the live environment"
Done Definition: "Project architecture analyzed with live environment insights, security domains identified with testing objectives, 4-6 Phase 3 pattern discovery tasks created for different code areas"
Phase ID: 2
Priority: high
```

MANDATORY EXECUTION SEQUENCE:
You MUST complete these steps in this exact order:

STEP A: ENVIRONMENT VALIDATION
1. Start all Docker containers: docker-compose up -d
2. Verify all containers are healthy: docker ps
3. Run test_environment.sh and verify it PASSES
4. Run validate_services.py and verify it PASSES
5. Run sample_data_test.py and verify it PASSES
6. Run reset_environment.py and verify it PASSES
7. Create validation_results.md with all test results

STEP B: TASK CREATION
8. ONLY AFTER all tests pass: Create Phase 2 task using MCP endpoint
9. VERIFY the Phase 2 task was created successfully

STEP C: TASK COMPLETION
10. ONLY AFTER Phase 2 task is created and verified: Mark your task as done

ABSOLUTELY CRITICAL - TASK CREATION ORDER:
- ALL validation tests must PASS 100% before task creation
- Phase 2 task must be created BEFORE marking task as done
- If any validation test fails, STOP and fix issues
- Do NOT skip any validation step

FAILURE CONSEQUENCES:
- Skip validation = Environment may not work for other phases
- Skip task creation = Entire workflow stops
- Both issues = Complete workflow failure

This is the #1 reason Phase 1 tasks fail - follow the sequence exactly!

SUCCESS METRICS:
✅ Environment matches real-world deployment patterns
✅ All services running and accessible (verified by your tests)
✅ Sample data and scenarios are realistic
✅ Documentation enables other agents to test effectively
✅ Sanity test scripts created and all tests pass
✅ Environment validated for security testing
✅ PHASE 2 TASK CREATED AND VERIFIED BEFORE COMPLETION

Remember: You're creating the foundation for real security testing. The quality and
realism of this environment determines whether subsequent phases find theoretical
vulnerabilities or demonstrable security issues with real impact!

PHASE 1 IS ABOUT SETUP, NOT SECURITY ANALYSIS!
Your success is measured by environment quality, not vulnerabilities found!

FINAL CRITICAL REMINDER:
- TARGET PROJECT = Where to find vulnerabilities
- Demo App = How to test those vulnerabilities
- NEVER hunt demo app vulnerabilities!
- ALWAYS hunt TARGET PROJECT vulnerabilities!
- Demo app validates, TARGET PROJECT contains the vulnerabilities!

You're setting up a shooting range, NOT becoming the target!""",
        outputs=[
            "- target_project_analysis.md with comprehensive TARGET PROJECT analysis",
            "- Container configuration with complete multi-service environment setup",
            "- environment_setup.md with comprehensive configuration and access details",
            "- security_test_guide.md with TARGET PROJECT focus and testing instructions",
            "- test_environment.sh, validate_services.py, sample_data_test.py, reset_environment.py",
            "- validation_results.md with complete test execution logs and PASS/FAIL status",
            "- Sample data and test scenarios mirroring TARGET PROJECT use cases",
            "- Docker containers running and verified healthy (docker ps output)",
            "- All test scripts executed and verified PASSING 100%",
            "- Memory entries with TARGET PROJECT details for other agents",
            "- Phase 2 code reconnaissance task created ONLY after all validation tests pass",
        ],
        next_steps=[
            "Phase 2 code reconnaissance agents will analyze the running environment to",
            "understand the real attack surface and create targeted pattern discovery tasks.",
            "The live environment enables actual exploitation testing rather than theoretical",
            "vulnerability assessment, transforming this into real security validation.",
        ],
    ),
    Phase(
        id=2,
        name="code_recon_and_targeting",
        description="""[This is Phase 2 - Code Reconnaissance & Strategic Targeting]

CRITICAL FOCUS: Analyze the TARGET PROJECT codebase to identify security-critical areas,
then strategically spawn 4-6 Phase 3 pattern discovery agents to systematically hunt for
vulnerabilities in the TARGET PROJECT across different code domains.

PRIMARY MISSION: Map the TARGET PROJECT structure, identify high-risk components in the
TARGET PROJECT, understand the TARGET PROJECT's tech stack, and create targeted exploration
tasks that focus on TARGET PROJECT vulnerabilities.

SECONDARY MISSION: Use the demo environment to understand how TARGET PROJECT can be tested
and exploited. Demo app is for validation, NOT discovery!""",
        done_definitions=[
            "target_project_analysis.md thoroughly analyzed to understand TARGET PROJECT",
            "environment_setup.md and security_test_guide.md thoroughly analyzed",
            "Demo environment explored ONLY to understand TARGET PROJECT testing capabilities",
            "TARGET PROJECT README, CONTRIBUTING.md, and SECURITY.md thoroughly analyzed",
            "TARGET PROJECT architecture and tech stack documented with real-world insights",
            "High-risk TARGET PROJECT code areas identified and prioritized",
            "TARGET PROJECT dependencies and third-party integrations mapped",
            "TARGET PROJECT security-relevant entry points identified and mapped",
            "STRATEGIC ANALYSIS: Identified 4-6 distinct TARGET PROJECT code domains for systematic exploration",
            "CRITICAL: Created 4-6 Phase 3 pattern discovery tasks for TARGET PROJECT areas",
            "Each Phase 3 task assigned specific TARGET PROJECT domain with validation objectives",
            "project_analysis.md and security_domains.md created with TARGET PROJECT focus",
            "All TARGET PROJECT intelligence saved to memory for coordination between Phase 3+ agents",
        ],
        working_directory=".",
        additional_notes="""YOUR MISSION: MAP THE TARGET PROJECT + SPAWN TARGETED EXPLORATION!

CRITICAL DISTINCTION:
- TARGET PROJECT = Where you find vulnerabilities (PRIMARY FOCUS)
- Demo Environment = How you test those vulnerabilities (SECONDARY TOOL)

Your PRIMARY job is to be the strategic reconnaissance specialist who maps the
TARGET PROJECT and sends specialized teams (Phase 3 agents) to investigate specific
areas of the TARGET PROJECT code.

YOUR SECONDARY job is to understand how the demo environment can help validate
vulnerabilities found in the TARGET PROJECT.

ABSOLUTELY CRITICAL: DO NOT hunt demo app vulnerabilities!
- Demo app = Testing tool, NOT discovery target
- TARGET PROJECT = Discovery target, NOT testing tool
- Find vulnerabilities in TARGET PROJECT
- Use demo app to validate TARGET PROJECT vulnerabilities

MANDATORY READING - Start with these files:
1. target_project_analysis.md - Understand the TARGET PROJECT (YOUR PRIMARY FOCUS)
2. environment_setup.md - Understand the testing environment (VALIDATION TOOL)
3. security_test_guide.md - Learn TARGET PROJECT focus and validation approach
4. TARGET PROJECT README.md - Understand what TARGET PROJECT does and how it works
5. TARGET PROJECT CONTRIBUTING.md - Learn TARGET PROJECT development practices
6. TARGET PROJECT SECURITY.md - Check TARGET PROJECT security policies
7. TARGET PROJECT dependency files - Identify TARGET PROJECT dependencies and tech stack

PRIMARY ANALYSIS: TARGET PROJECT FOCUS
- Analyze TARGET PROJECT code structure and architecture
- Understand TARGET PROJECT functionality and usage patterns
- Identify TARGET PROJECT security-relevant components
- Map TARGET PROJECT attack surfaces and entry points
- Document TARGET PROJECT integration points and dependencies

SECONDARY ANALYSIS: DEMO ENVIRONMENT FOR VALIDATION
- Verify the demo environment is running and accessible (FOR TESTING ONLY)
- Test demo app functionality to understand TARGET PROJECT validation capabilities
- Confirm how demo app can help validate TARGET PROJECT vulnerabilities
- Document validation approaches for different TARGET PROJECT vulnerability types

CRITICAL ANALYSIS SEQUENCE:
1. PRIMARY: Analyze TARGET PROJECT for vulnerabilities
2. SECONDARY: Understand how to validate those vulnerabilities with demo app
3. NEVER: Find vulnerabilities in demo app instead of TARGET PROJECT

KEY QUESTIONS TO ANSWER ABOUT TARGET PROJECT:
- What type of TARGET PROJECT is this? (web app, CLI tool, library, etc.)
- What programming languages and frameworks does TARGET PROJECT use?
- How do developers integrate and use TARGET PROJECT?
- What are the main TARGET PROJECT entry points and interfaces?
- What kind of data does TARGET PROJECT handle/process?
- What external systems does TARGET PROJECT interact with?
- What are the TARGET PROJECT's security-relevant components?

VALIDATION QUESTIONS (SECONDARY):
- How can demo app help validate TARGET PROJECT vulnerabilities?
- What TARGET PROJECT functionality can be tested in demo environment?
- How does demo environment support TARGET PROJECT exploit validation?

HIGH-RISK TARGET PROJECT DOMAINS (prioritize these):
1. Authentication & Authorization - TARGET PROJECT auth functions, session management, access control
2. Input Validation & Data Parsing - TARGET PROJECT input processing, validation, parsing logic
3. Cryptography & Secrets Management - TARGET PROJECT encryption, secrets, random generation
4. File System & External Interactions - TARGET PROJECT file operations, external calls, system commands
5. Network Communications & APIs - TARGET PROJECT network code, HTTP handling, API implementation
6. Data Storage & Databases - TARGET PROJECT data storage, database queries, data validation

FOCUS ON TARGET PROJECT:
Each domain should be analyzed in the TARGET PROJECT codebase, NOT the demo app!
Demo app only helps validate whether TARGET PROJECT vulnerabilities are exploitable.

CREATE THESE ESSENTIAL FILES:

project_analysis.md:
```markdown
# Project Security Analysis

## Project Overview
- Name, type, purpose
- Tech stack and languages
- Main features and user interactions
- Security-relevant architecture notes

## High-Risk Components
- List most critical security domains
- Risk assessment and priorities
- Complexity analysis
- Known security considerations
```

security_domains.md:
```markdown
# Security Domain Mapping

## Domain 1: Authentication & Authorization
- Location: src/auth/, lib/security.py
- Risk Level: High
- Components: Authentication, session management
- Notes: Uses custom authentication implementation
```

USE SAVE_MEMORY EXTENSIVELY:
- "Project type: Web application with authentication system"
- "High-risk area: src/auth/login.py contains custom authentication validation"
- "Dependencies: Uses ORM, template engine"
- "Security concern: Manual password hashing without secure hash function"
- "Entry points: HTTP endpoints in /api/, file upload in /upload"

CREATE 4-6 PHASE 3 TASKS USING MCP ENDPOINT:
```python
create_task(
    description="Phase 3: Investigate authentication and authorization code for security vulnerabilities using the live environment",
    done_definition="Systematically analyzed auth modules, tested against running environment, identified all potential auth bypass, privilege escalation, and session management vulnerabilities, created Phase 4 tasks for each exploitable finding",
    phase_id=3,
    priority="high",
    agent_id="your-agent-id"
)
```

ENVIRONMENT-AWARE TASK CREATION:
- Each task must leverage the running container environment
- Include testing objectives that can be validated against live services
- Reference specific endpoints, ports, or functionality from environment setup
- Prioritize domains where vulnerabilities can be actually exploited and tested

QUALITY OVER QUANTITY: 4-6 thorough domain explorers > 15 scattered tasks.

TASK DISTRIBUTION STRATEGY:
- High-risk domains → Priority "high"
- Medium-risk domains → Priority "medium"
- Each task gets clearly defined code area + live testing objectives
- Ensure complete coverage of testable attack surface
- Avoid overlap between tasks, coordinate via environment documentation""",
        outputs=[
            "- project_analysis.md with comprehensive project overview and security assessment",
            "- security_domains.md with detailed mapping of security-critical code areas",
            "- Memory entries with project architecture and high-risk component analysis",
            "- environment_validation.md documenting testable vs theoretical vulnerabilities",
            "- 4-6 Phase 3 pattern discovery tasks covering all security domains with live testing objectives",
        ],
        next_steps=[
            "Phase 3 pattern discovery agents will systematically analyze their assigned",
            "security domains using the live environment to find potential vulnerabilities.",
            "Each agent will test findings against the running system and create Phase 4",
            "investigation tasks for exploitable vulnerabilities that can be validated.",
        ],
    ),
    Phase(
        id=3,
        name="pattern_discovery_and_vulnerability_identification",
        description="""[This is Phase 3 - Pattern Discovery & Vulnerability Identification]

FOCUS: Systematically analyze your assigned security domain using the live environment
to identify and validate potential vulnerabilities. Use pattern recognition, code analysis
tools, security knowledge, and actual testing against the running system to find
exploitable security issues.

Your task specifies the exact code domain to investigate (e.g., "authentication code",
"input validation", "file operations"). Find all potential vulnerabilities in this
domain, TEST THEM against the running environment, and create Phase 4 investigation
tasks for each exploitable finding.""",
        done_definitions=[
            "environment_setup.md and security_test_guide.md thoroughly analyzed",
            "Running environment tested to understand live attack surface",
            "project_analysis.md and security_domains.md read to understand project context",
            "Memories fetched to see what other domain explorers have discovered",
            "Assigned security domain systematically analyzed using multiple detection methods",
            "Static analysis tools (bandit/semgrep/sonarqube) run on assigned code area",
            "Manual code review performed on high-risk functions and patterns",
            "LIVE TESTING: Potential vulnerabilities tested against running environment",
            "ALL exploitable vulnerabilities in the domain identified and documented",
            "Each vulnerability assigned appropriate CWE classification",
            "Each vulnerability documented with: location, vulnerable pattern, tested impact",
            "Phase 4 investigation task created ONLY for exploitable/testable vulnerabilities",
            "domain_[DOMAIN]_findings.md file created with tested discoveries",
            "All vulnerability findings and test results saved to memory for coordination",
            "No duplicate work performed with other domain explorers",
        ],
        working_directory=".",
        additional_notes="""YOU ARE A SECURITY DOMAIN SPECIALIST WITH LIVE TESTING CAPABILITIES

Your task description tells you EXACTLY which security domain to investigate.
Examples: "authentication and authorization code", "input validation and data parsing",
"file system operations", "cryptographic implementations"

YOUR MISSION: Be the expert for your domain - find ALL exploitable vulnerabilities
in your assigned code area by TESTING against the live environment, then create Phase 4
tasks for vulnerabilities that can be actually exploited and validated.

MANDATORY READING:
1. environment_setup.md - Understand the testing environment and services
2. security_test_guide.md - Learn how to test against the running system
3. project_analysis.md - Understand overall project architecture
4. security_domains.md - Find your assigned domain details
5. FETCH MEMORIES - Learn what other domains have discovered

ENVIRONMENT TESTING APPROACH:
- Verify environment is running before starting analysis
- Test actual endpoints/functionality mentioned in your domain
- Use provided credentials to test authenticated scenarios
- Validate findings against live services, not just code analysis
- Document which vulnerabilities are theoretical vs exploitable

USE COMPREHENSIVE DETECTION METHODS:

METHOD 1: STATIC ANALYSIS TOOLS
```bash
# Python projects
bandit -r your_domain_directory/ -f json -o bandit_findings.json
semgrep --config=security your_domain_directory/

# JavaScript/Node.js
npm audit --audit-level=moderate
semgrep --config=security your_domain_directory/

# General use
grep -r "eval|exec|subprocess|os.system" your_domain_directory/
grep -r "pickle|marshal|yaml.load" your_domain_directory/
```

METHOD 2: MANUAL CODE REVIEW PATTERNS

Authentication Domain Patterns:
- Hardcoded credentials or API keys
- Weak password hashing (MD5, SHA1 instead of bcrypt/argon2)
- Custom crypto implementations instead of battle-tested libraries
- Authentication tokens with weak secrets or algorithm confusion
- Session management issues (predictable IDs, no timeout)

Input Validation Patterns:
- Direct use of user input in dangerous functions
- Missing input sanitization before database operations
- Regex that doesn't account for malicious input
- Type confusion between strings and integers
- Unrestricted file upload or file path traversal

Cryptography Patterns:
- Usage of deprecated or weak cryptographic algorithms
- Predictable random number generation
- Hardcoded encryption keys or IVs
- Improper certificate validation
- Missing integrity checks on encrypted data

File Operations Patterns:
- Path traversal vulnerabilities (../../../etc/passwd)
- Unrestricted file uploads
- Race conditions in file operations
- Temporary file creation with predictable names
- Permission issues on sensitive files

Network/API Patterns:
- SQL injection in database queries
- Command injection in system calls
- XXE in XML parsing
- SSRF in HTTP requests
- Insecure direct object references (IDOR)

METHOD 3: DATA FLOW ANALYSIS
1. Identify Entry Points: Where does user input enter your domain?
2. Track Transformations: How is the data processed/modified?
3. Find Sensitive Operations: Where does the data interact with security-critical functions?
4. Look for Validation Gaps: Are there missing checks between steps?

METHOD 4: DEPENDENCY ANALYSIS
```bash
# Python
pip-audit

# JavaScript
npm audit

# Look for specific vulnerable versions
grep -r "requests==2.20.0" your_domain_directory/  # Known vulnerable version
```

FOR EACH VULNERABILITY FOUND, DOCUMENT:

LOCATION INFORMATION:
- File: Exact file path and line number
- Function: Function name and context
- Code Snippet: The vulnerable code (2-3 lines before/after)

VULNERABILITY CLASSIFICATION:
- CWE Number: Specific CWE identifier (e.g., CWE-89 for SQLi)
- Vulnerability Type: Brief description (e.g., "SQL Injection")
- Severity: Critical/High/Medium/Low based on potential impact

POTENTIAL IMPACT:
- Attack Vector: How an attacker would exploit this
- Security Impact: What could happen (data theft, RCE, etc.)
- Real-world Scenario: Practical exploitation scenario

EXPLOITABILITY ASSESSMENT:
- Complexity: Easy/Medium/Hard to exploit
- Prerequisites: What conditions needed for exploitation?
- Detection Likelihood: Would this be noticed in logs/monitoring?

CREATE domain_[DOMAIN]_findings.md WITH ALL YOUR DISCOVERIES:

```markdown
# [DOMAIN] Security Vulnerability Findings

## Domain Overview
- Assigned Area: Your specific domain and files
- Analysis Methods: Tools and techniques used
- Coverage: % of domain thoroughly analyzed

## Vulnerabilities Found

### Vulnerability 1: [Name]
- CWE: CWE-XXX (Vulnerability Name)
- Location: file.py:line
- Severity: High
- Description: Brief explanation
- Code: Vulnerable code snippet
- Impact: Security consequences
- Exploitation: How to exploit
- Prerequisites: Conditions needed

## Analysis Summary
- Total Vulnerabilities: X
- Critical: Y, High: Z, Medium: A, Low: B
- Most Critical: Brief summary of worst finding
- Recommendations: General security improvements
```

SAVE FINDINGS TO MEMORY:
For each vulnerability: "Found potential [VULNERABILITY TYPE] in [LOCATION] (CWE-XXX):
[brief description]. Pattern: [vulnerable pattern]. Impact: [potential impact].
Phase 3 investigation task created."

CREATE PHASE 4 INVESTIGATION TASKS:
For EACH EXPLOITABLE vulnerability found, create a Phase 4 task:
```python
create_task(
    description="Phase 4: Investigate [VULNERABILITY TYPE] in [FUNCTION] at [LOCATION] using live environment",
    done_definition="Researched [VULNERABILITY TYPE] exploitation techniques, analyzed vulnerable code at [LOCATION], tested against running environment, assessed exploitability and impact, determined if Phase 5 task warranted",
    phase_id=4,
    priority="high",
    agent_id="your-agent-id"
)
```

CRITICAL FILTERING:
- ONLY create Phase 4 tasks for vulnerabilities that can be tested in the live environment
- Prioritize vulnerabilities where security impact can be demonstrated
- Skip theoretical vulnerabilities that cannot be validated
- Focus on findings where the running environment provides real attack surface

REMEMBER: You're the specialist for your security domain with live testing capabilities.
Your thorough analysis and testing sets up the investigation phase for success.
Find exploitable vulnerabilities, validate them against the running environment,
and give the Phase 4 agents clear targets that can be actually exploited!""",
        outputs=[
            "- domain_[DOMAIN]_findings.md with all exploitable vulnerabilities discovered and tested",
            "- Static analysis tool outputs (bandit, semgrep, etc.)",
            "- Live environment test results and validation logs",
            "- Memory entries for each vulnerability with test results and CWE classification",
            "- Phase 4 investigation tasks ONLY for exploitable/testable vulnerabilities (typically 2-6 tasks)",
        ],
        next_steps=[
            "Phase 4 investigation agents will take each exploitable vulnerability you discovered",
            "and validated against the live environment. They'll perform deep analysis to determine",
            "exact exploitation methods, research specific attack techniques, and decide which",
            "findings warrant full exploit development in Phase 5.",
        ],
    ),
    Phase(
        id=4,
        name="vulnerability_investigation_and_exploitation_planning",
        description="""[This is Phase 4 - Vulnerability Investigation & Exploitation Planning]

FOCUS: Take ONE validated vulnerability from Phase 3, research specific exploitation
techniques, test against the live environment, analyze the vulnerable code patterns,
and determine if this is actually exploitable. Create a Phase 5 exploitation task
if the vulnerability can be reliably exploited.

Your task specifies the exact vulnerability to investigate (location, CWE, function).
Research attack techniques, test exploitation against the running environment, analyze
exploitability conditions, and make the go/no-go decision for exploit development.""",
        done_definitions=[
            "domain_[DOMAIN]_findings.md read for vulnerability details and test results",
            "Running environment verified and accessible for exploit testing",
            "Vulnerability location thoroughly analyzed through manual code inspection",
            "Specific CWE exploitation techniques researched through WebSearch and security resources",
            "Attack surface and exploitation prerequisites clearly identified",
            "LIVE TESTING: Exploitation techniques tested against running environment",
            "Exploitation feasibility assessed (Easy/Medium/Hard/Impossible) based on actual testing",
            "Security impact analysis performed with realistic attack scenarios on live system",
            "Vulnerability_[CWE_ID]_[LOCATION].md investigation file created with findings",
            "All research, analysis, and test results saved to memory",
            "Phase 5 exploitation task created IF vulnerability is reliably exploitable",
            "Go/No-Go decision documented with clear reasoning and test evidence",
        ],
        working_directory=".",
        additional_notes="""YOU ARE A VULNERABILITY EXPERT INVESTIGATOR WITH LIVE TESTING

Your task description tells you EXACTLY which vulnerability to investigate.
Example: "Phase 4: Investigate SQL injection vulnerability in search_users() function at src/api/users.py:47 using live environment"

YOUR MISSION: Be the expert investigator who validates and determines if this vulnerability
is actually exploitable against the running environment. Research techniques, test against
the live system, analyze the code, and make the critical go/no-go decision for exploitation development.

READ YOUR TASK DESCRIPTION CAREFULLY:
- Extract the vulnerability type (e.g., SQL injection, auth bypass)
- Note the exact location (file.py:line, function name)
- Understand the CWE classification and initial assessment

READ THE SOURCE FINDINGS:
- Find your vulnerability in domain_*_findings.md
- Review the initial assessment and code snippet
- Understand the context and potential impact

FETCH RELEVANT MEMORIES:
- Has anyone investigated similar vulnerabilities?
- What techniques worked for related findings?
- Any context about the project's security posture?

DEEP CODE ANALYSIS:
1. Locate and examine the vulnerable code
2. Read the surrounding context (entire function, related functions)
3. Understand the data flow - how does attacker-controlled input reach this point?
4. Identify security controls - are there any validations or protections in place?

KEY QUESTIONS TO ANSWER:
- Input Source: Where does the user input come from?
- Validation: Is there any input validation or sanitization?
- Context: How is the vulnerable data used?
- Output: Where does the result go?
- Access Control: Who can access this function?

EXPLOITATION TECHNIQUE RESEARCH (CRITICAL):

Use WebSearch to research specific exploitation techniques:

RESEARCH STRATEGY:
1. CWE-Specific Research:
   - "CWE-89 SQL injection exploitation techniques"
   - "CWE-79 cross-site scripting attack methods"
   - "CWE-22 path traversal exploitation examples"

2. Technology-Specific Research:
   - "FastAPI SQL injection vulnerabilities"
   - "Python pickle deserialization attacks"
   - "Node.js command injection bypasses"

3. Real-World Examples:
   - "[Vulnerability type] bug bounty writeups"
   - "[CWE number] real world exploitation"
   - "[Framework] security vulnerabilities"

4. Advanced Techniques:
   - "[Vulnerability type] bypass techniques"
   - "[CWE number] exploitation methods"
   - "WAF bypass for [vulnerability type]"

DOCUMENT YOUR RESEARCH:
For each technique found, document:
- Technique Name: What is this attack method called?
- Prerequisites: What conditions are needed?
- Payload Examples: Specific strings or inputs to use
- Bypass Methods: How to circumvent common protections
- Detection Indicators: Would this be logged or monitored?

EXPLOITABILITY ASSESSMENT:

Analyze if this specific vulnerability is actually exploitable:

EXPLOITABILITY FACTORS:
1. Input Control:
   - Can an attacker provide malicious input?
   - Is the input field accessible (web form, API parameter, CLI arg)?
   - Are there input length restrictions or character filters?

2. Validation Gaps:
   - Are there security controls that would block exploitation?
   - Input validation, output encoding, framework protections?
   - Can these be bypassed using techniques from your research?

3. Execution Context:
   - Does the vulnerable code actually execute with user input?
   - Are there conditions that prevent execution?
   - Error handling that might stop the attack?

4. Impact Realization:
   - Would successful exploitation actually cause security impact?
   - Can sensitive data be accessed or modified?
   - Can system control be achieved?

EXPLOITABILITY SCORING:

EASY TO EXPLOIT (Proceed to Phase 4):
- Direct user input reaches vulnerable operation
- Minimal or no security controls
- Clear security impact achievable
- Simple payload requirements

MEDIUM DIFFICULTY (Consider Phase 4):
- User input accessible but has some restrictions
- Basic security controls that might be bypassable
- Security impact possible but requires specific conditions
- Multiple steps or complex payload needed

HARD TO EXPLOIT (Usually skip Phase 4):
- Indirect input sources or chained vulnerabilities needed
- Strong security controls requiring advanced bypasses
- Limited impact or difficult to achieve meaningful outcome
- Very specific timing or conditions required

IMPOSSIBLE TO EXPLOIT (Do NOT create Phase 4 task):
- Vulnerability exists but no realistic attack path
- Input sources not controllable by attacker
- Security controls prevent any practical exploitation
- Theoretical vulnerability with no real-world impact

CREATE INVESTIGATION REPORT:
Create vulnerability_[CWE_ID]_[LOCATION].md with your findings:

```markdown
# Vulnerability Investigation: [Vulnerability Name]

## Vulnerability Details
- CWE: CWE-XXX (Vulnerability Name)
- Location: src/file.py:line, function_name()
- Initial Finding: Brief description from Phase 2

## Code Analysis
### Vulnerable Code
[code snippet]

### Data Flow Analysis
1. Input Source: HTTP GET parameter 'search' from /api/search
2. Processing: Directly passed to query construction without validation
3. Vulnerable Operation: String concatenation creates SQL query
4. Impact: Arbitrary SQL execution on database

### Security Controls Assessment
- Input Validation: None present
- Framework Protections: FastAPI provides no SQLi protection
- Access Control: Any authenticated user can access
- Logging: Queries logged but not reviewed

## Exploitation Research

### Attack Techniques Researched
1. Union-Based SQLi: Extract data from other tables
2. Boolean-Blind SQLi: Extract data via true/false responses
3. Time-Based Blind SQLi: Extract via response delays

### Bypass Opportunities
- No input sanitization to bypass
- No WAF or protection mechanisms
- Direct database connection without ORM protection

## Exploitability Assessment

### Exploitation Difficulty: EASY
Reasoning:
- Direct user input to SQL query
- No security controls present
- Clear data extraction possible

### Prerequisites for Exploitation
- Valid user session (any role works)
- Network access to API endpoint
- Basic SQL knowledge

### Potential Impact
- Confidentiality: Complete database exfiltration
- Integrity: Data modification via UPDATE/INSERT
- Availability: Potential DoS via heavy queries

## Go/No-Go Decision: GO
Justification: Easy exploitation, high impact, no security controls,
clear attack path, valuable target data. Proceed to Phase 4 exploitation.
```

SAVE RESEARCH TO MEMORY:
"SQL injection investigation at src/api/users.py:47 (CWE-89):
Vulnerable due to direct string concatenation in SQL query. Exploitation
difficulty: EASY. No security controls present. Impact: database
exfiltration possible. Go decision for Phase 4 exploitation."

CREATE PHASE 5 EXPLOITATION TASK (IF GO DECISION):
If exploitation difficulty is EASY or MEDIUM based on live testing, create Phase 5 task:
```python
create_task(
    description="Phase 5: Develop exploit for [VULNERABILITY TYPE] in [FUNCTION] at [LOCATION] using live environment",
    done_definition="Created working exploit for [VULNERABILITY TYPE] at [LOCATION], tested against running environment, validated exploitation techniques, developed reliable PoC, created HackerOne report with evidence",
    phase_id=5,
    priority="high",
    agent_id="your-agent-id"
)
```

LIVE ENVIRONMENT VALIDATION REQUIREMENT:
- Only create Phase 5 tasks if exploitation was validated against the running environment
- The exploit must work consistently against the container services
- Security impact must be demonstrable in the live system
- Evidence must show actual exploitation, not theoretical scenarios

DECISION FRAMEWORK:

CREATE PHASE 5 TASK IF:
- Exploitation difficulty is EASY or MEDIUM based on live testing
- Clear security impact demonstrated against running environment
- Realistic attack scenario validated in container environment
- High chance of developing reliable exploit that works consistently

DO NOT CREATE PHASE 5 TASK IF:
- Exploitation difficulty is HARD or IMPOSSIBLE in live environment
- Theoretical vulnerability that cannot be validated in practice
- Extensive chaining or unlikely conditions required for exploitation
- Better to focus investigation resources on testable vulnerabilities
- Live environment testing shows exploit is not feasible

Remember: You're the gatekeeper for exploitation development with the advantage of
live testing. Your thorough investigation and validation ensures that Phase 5 agents
only work on vulnerabilities that have been proven exploitable in the running environment.
Quality over quantity - focus on what can be actually demonstrated!""",
        outputs=[
            "- vulnerability_[CWE_ID]_[LOCATION].md with complete investigation and live test results",
            "- Exploitation research documentation with validated attack techniques and bypass methods",
            "- Live environment test logs showing exploitation attempts and results",
            "- Memory entries with exploitability assessment based on actual testing",
            "- Phase 5 exploitation task (ONLY for vulnerabilities proven exploitable in live environment)",
        ],
        next_steps=[
            "If exploitation is validated: Phase 5 agent will develop a working exploit",
            "against the live environment and create a HackerOne-ready submission with",
            "comprehensive evidence and demonstrated security impact. If not exploitable:",
            "the investigation ends here and resources are allocated to more promising vulnerabilities.",
        ],
    ),
    Phase(
        id=5,
        name="exploit_development_and_submission",
        description="""[This is Phase 5 - Exploit Development & HackerOne Submission]

FOCUS: Take ONE validated vulnerability from Phase 4 and develop a working exploit
against the live environment with comprehensive evidence. Create a professional
HackerOne report demonstrating the actual security impact and submit via submit_result
if exploitation succeeds against the running system.

Your task specifies the exact vulnerability to exploit, the validated research from
Phase 4, and the tested exploitation plan. Build a reliable Proof of Concept that works
against the container environment, document everything thoroughly, and create a
complete HackerOne submission package with real evidence.""",
        done_definitions=[
            "vulnerability_[CWE_ID]_[LOCATION].md investigation report with live test results analyzed",
            "Live environment verified and accessible for exploit development",
            "Validated exploitation plan from Phase 4 research reviewed and understood",
            "Working exploit developed against live environment and tested successfully",
            "Exploit reproduced 3+ times against container environment to ensure reliability",
            "Professional HackerOne report created with clear vulnerability description",
            "Step-by-step reproduction instructions documented with live environment details",
            "Security impact demonstrated with concrete evidence from actual exploitation",
            "All exploit code, live environment evidence, and documentation packaged for submission",
            "CRITICAL: submit_result called with complete submission package",
            "All findings and exploits saved to memory for learning",
        ],
        working_directory=".",
        additional_notes="""YOU ARE AN EXPLOIT DEVELOPMENT EXPERT WITH LIVE ENVIRONMENT ACCESS

Your task description tells you EXACTLY which vulnerability to exploit.
Example: "Phase 5: Develop exploit for SQL injection in search_users() function at src/api/users.py:47 against live environment"

YOUR MISSION: Build a working, reliable exploit that demonstrates the actual security
impact against the running container environment and create a professional HackerOne
submission. This is where the rubber meets the road - turn the Phase 4 validated research
into a concrete, proven exploit that works against real services.

READ YOUR INVESTIGATION BRIEFING:
- Study the vulnerability_[CWE_ID]_[LOCATION].md file thoroughly
- Understand the exploitation plan and expected difficulty
- Review the attack techniques and bypass methods researched
- Note the prerequisites and expected impact

SET UP YOUR EXPLOITATION ENVIRONMENT:
1. Project Setup: Clone/download the target project if needed
2. Dependencies: Install required dependencies for testing
3. Database Setup: Initialize database with test data if applicable
4. Test Accounts: Create accounts for testing (if authentication needed)
5. Tools Preparation: Have exploitation tools ready

VERIFY EXPLOITATION PREREQUISITES:
- Can you access the vulnerable functionality?
- Do you have the required permissions or authentication?
- Are all the conditions from Phase 3 investigation met?
- Is the target environment properly configured?

PROOF OF CONCEPT DEVELOPMENT:

Start with a basic exploit and iterate toward reliability:

BASIC EXPLOIT DEVELOPMENT:

1. Manual Testing First:
   - Test the vulnerability manually using simple payloads
   - Confirm the vulnerability exists as described
   - Understand the exact behavior and responses

2. Simple Script Development:
```python
# Example: Basic SQL Injection Exploit
import requests

def test_sqli(target_url, session_cookie):
    payload = "' UNION SELECT username,password FROM users -- "
    response = requests.get(
        f"{target_url}/api/search",
        params={"search": payload},
        cookies={"session": session_cookie}
    )
    return response.text
```

3. Iterative Improvement:
   - Handle errors and edge cases
   - Add automation for repeated tasks
   - Improve reliability and consistency

EXPLOIT RELIABILITY TESTING:
Test your exploit at least 3 times and document results:
```python
# Test Results Log
Test Run 1: SUCCESS - Extracted 15 user credentials
Test Run 2: SUCCESS - Consistent results, 0 errors
Test Run 3: SUCCESS - Reproducible across different sessions
```

EXPLOITATION VARIATIONS:
Test multiple exploitation approaches if applicable:
- Different payload variants
- Alternative injection techniques
- Bypass methods for security controls
- Various impact demonstrations

EVIDENCE COLLECTION AND DOCUMENTATION:

Collect comprehensive evidence to prove the vulnerability:

SCREENSHOT EVIDENCE:
- Before Exploitation: Normal application behavior
- During Exploitation: Exploit being executed
- After Exploitation: Results/impact demonstrated
- Configuration: Setup and environment details

LOG EVIDENCE:
- Application Logs: Show exploit execution in logs
- Network Traffic: Request/response capture if relevant
- Database Logs: SQL queries or data changes
- System Logs: File system changes or system calls

FILE EVIDENCE:
- Exploit Script: Clean, commented exploit code
- Output Files: Results of data exfiltration
- Configuration Files: Before/after comparisons
- Database Dumps: Sensitive data extracted

PROFESSIONAL HACKERONE REPORT CREATION:

Create a professional, comprehensive HackerOne report:

```markdown
# SQL Injection in User Search Function

## Summary
A SQL injection vulnerability exists in the search_users() function at
src/api/users.py:47. The vulnerability allows authenticated attackers to
execute arbitrary SQL queries, leading to complete database exfiltration.

## Vulnerability Details
- CWE: CWE-89 (SQL Injection)
- Location: src/api/users.py, line 47, function search_users()
- Severity: Critical
- Impact: Complete database compromise

## Steps To Reproduce

### Prerequisites
1. Valid user account (any role)
2. Network access to the application

### Reproduction Steps

1. Authenticate to the application
   POST /api/login
   {"username": "testuser", "password": "password123"}

2. Execute SQL Injection via search parameter
   GET /api/search?search=test' UNION SELECT username,password FROM users --

3. Observe leaked credentials in search results

### Expected Results
Search results contain admin credentials
[{"username": "admin", "password": "admin123_hash", ...}]

## Impact

### Confidentiality Impact
- Complete exfiltration of all user data
- Exposure of administrative credentials
- Access to sensitive application data

### Business Impact
- Complete compromise of user accounts
- Regulatory compliance violations
- Reputational damage and loss of customer trust

## Supporting Material

### Evidence Files
1. exploit_sqlmi.py: Automated exploitation script
2. screenshot_exploit.png: Visual evidence of exploitation
3. database_dump.txt: Sample of exfiltrated data
4. application_logs.txt: Server logs showing exploit execution

### Proof of Concept Code
```python
#!/usr/bin/env python3
import requests
import json

class SQLInjectionExploit:
    def __init__(self, base_url, session_cookie):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.cookies.set('session', session_cookie)

    def dump_user_credentials(self):
        payload = "' UNION SELECT username,password,email FROM users -- "
        response = self.session.get(
            f"{self.base_url}/api/search",
            params={"search": payload}
        )
        return response.json()

if __name__ == "__main__":
    exploit = SQLInjectionExploit("http://localhost:8000", "abc123")
    credentials = exploit.dump_user_credentials()
    print(json.dumps(credentials, indent=2))
```

## Remediation

### Immediate Fix
Use parameterized queries instead of string concatenation:

```python
# Vulnerable code:
query = f"SELECT * FROM users WHERE name LIKE '%{search_term}%'"

# Secure code:
query = "SELECT * FROM users WHERE name LIKE ?"
cursor.execute(query, (f"%{search_term}%",))
```
```

SUBMISSION PACKAGE PREPARATION:

Organize all materials for HackerOne submission:

```
submission_package/
├── hackerone_report.md          # Professional report
├── exploits/
│   └── exploit_[vuln_type].py   # Clean, working exploit
├── evidence/
│   ├── screenshot_before.png    # Normal state
│   ├── screenshot_exploit.png   # Exploit execution
│   ├── screenshot_results.png   # Impact demonstrated
│   ├── application_logs.txt     # Server logs
│   └── output_dump.txt         # Exfiltrated data
└── README.md                   # Package overview
```

PACKAGE VALIDATION CHECKLIST:
- [ ] Exploit script runs without errors
- [ ] Evidence clearly shows vulnerability impact
- [ ] Report follows HackerOne format exactly
- [ ] All files are properly named and organized
- [ ] No sensitive information in package (API keys, etc.)
- [ ] Exploit is reproducible on fresh environment

SAVE FINDINGS TO MEMORY:
"Successfully developed working exploit for [VULNERABILITY TYPE] at [LOCATION].
Exploitation method: [brief technique]. Impact achieved: [what was demonstrated].
HackerOne submission package created and submitted via submit_result."

SUBMIT VIA SUBMIT_RESULT (CRITICAL):
```python
submit_result(
    markdown_file_path="submission_package/hackerone_report.md",
    agent_id="your-agent-id",
    explanation="Developed working exploit for SQL injection vulnerability in search_users() function. Exploit demonstrates complete database exfiltration through union-based SQL injection attack. Professional HackerOne report includes comprehensive evidence, PoC code, and remediation guidance.",
    evidence=[
        "exploit_sqlmi.py - Automated SQL injection exploit script",
        "evidence/screenshot_exploit.png - Visual evidence of successful exploitation",
        "evidence/database_dump.txt - Sample of exfiltrated user credentials",
        "evidence/application_logs.txt - Server logs confirming exploit execution"
    ]
)
```

SUCCESS CRITERIA:
YOUR WORK IS SUCCESSFUL IF:
- Working exploit demonstrates clear security impact
- Exploit is reliable and reproducible
- HackerOne report is professional and complete
- Evidence clearly proves the vulnerability
- submit_result called with comprehensive package
- All materials organized for review

REMEMBER:
- Quality over quantity - one solid exploit is better than many flaky ones
- Professional presentation matters for HackerOne acceptance
- Clear evidence and reproducibility are essential
- Your work represents the entire Hephaestus system - make it count!

You're the final step in the bug factory pipeline - turn the Phase 4 validated investigation
into a concrete, proven vulnerability that demonstrates real security impact against the live environment!""",
        outputs=[
            "- submission_package/ with complete HackerOne submission materials from live testing",
            "- exploits/exploit_[vuln_type].py with working, reliable exploit code tested against container environment",
            "- evidence/ with screenshots, logs, and proof of actual vulnerability impact in live environment",
            "- hackerone_report.md following professional HackerOne format with real exploitation evidence",
            "- Memory entries documenting live exploit development techniques and success",
            "- submit_result call with complete submission package validated against running environment",
        ],
        next_steps=[
            "The workflow result validator will review your submission package, attempt",
            "to reproduce the vulnerability against the live environment, and validate the",
            "demonstrated security impact. If validated, the report will be finalized for",
            "HackerOne submission. The bug factory continues with other vulnerability",
            "investigations and exploitations using the same testing environment.",
        ],
    ),
]

# Workflow configuration for result validation
BUGBOUNTY_WORKFLOW_CONFIG = WorkflowConfig(
    has_result=True,
    result_criteria="""VALIDATION REQUIREMENTS FOR OPEN SOURCE BUG BOUNTY SUBMISSIONS:

CRITICAL: A SUBMISSION IS ONLY VALID IF ALL REQUIREMENTS ARE MET

1. VULNERABILITY VALIDATION (MANDATORY)
   ✓ Exploit successfully demonstrates the vulnerability
   ✓ Security impact is clearly shown, not theoretical
   ✓ Vulnerability occurs in real-world usage scenarios
   ✓ CWE classification is accurate and appropriate
   ✓ Exploit is reliable and reproducible

2. TECHNICAL QUALITY (MANDATORY)
   ✓ Exploit code is clean, well-documented, and functional
   ✓ Step-by-step reproduction instructions are clear and complete
   ✓ Evidence conclusively proves vulnerability exploitation
   ✓ No false positives or exploitation errors
   ✓ Exploit works consistently across multiple test runs

3. REPORT STANDARDS (MANDATORY)
   ✓ Follows exact HackerOne report format requirements
   ✓ Summary clearly explains vulnerability and impact
   ✓ Steps to Reproduce are detailed and actionable
   ✓ Impact assessment demonstrates real-world security consequences
   ✓ Remediation guidance is practical and technically sound

4. EVIDENCE REQUIREMENTS (MANDATORY)
   ✓ Screenshots show before/during/after exploitation states
   ✓ Logs or network traffic demonstrate the exploit execution
   ✓ Proof of concept code works as documented
   ✓ Evidence clearly shows security boundary violation
   ✓ All supporting materials are organized and readable

5. PROJECT CONTEXT (MANDATORY)
   ✓ Vulnerability exists in the actual open source project
   ✓ Exploitation path is realistic and achievable
   ✓ Project version and configuration clearly documented
   ✓ No modified or special conditions required for exploitation
   ✓ Vulnerability affects current or recent project versions

VALIDATION DECISION CRITERIA:

APPROVE if and only if:
   - Exploit successfully demonstrates the vulnerability
   - Security impact is real and clearly proven
   - Report is professional and HackerOne-ready
   - Evidence is comprehensive and convincing
   - Technical quality meets production standards

REJECT if:
   - Exploit doesn't work or fails to demonstrate vulnerability
   - Security impact is theoretical or unproven
   - Missing clear reproduction steps or evidence
   - Report quality is poor or incomplete
   - Technical inaccuracies or false claims

When validating:
1. Attempt to reproduce the exploit exactly as documented
2. Verify all evidence shows genuine vulnerability exploitation
3. Confirm report accurately describes the vulnerability and impact
4. Ensure submission meets professional HackerOne standards
5. Validate that the vulnerability affects the actual project

REMEMBER: This represents the Hephaestus system's work quality.
Only approve submissions that demonstrate real security vulnerabilities
with working exploits and professional documentation. """,
    on_result_found="do_nothing",  # Don't stop - keep finding more bugs!
)