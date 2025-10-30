# Open Source Bug Bounty Workflow

A systematic 5-phase workflow for hunting security vulnerabilities in open source projects using live environment testing and submitting them to HackerOne.

## Workflow Overview

This workflow implements a "bug factory" approach that systematically discovers, validates, and exploits security vulnerabilities using a live testing environment:

1. **Phase 1: Environment Research & Production Setup** - Set up realistic docker-compose environment for testing
2. **Phase 2: Code Recon & Strategic Targeting** - Map the project and spawn domain specialists using live environment
3. **Phase 3: Pattern Discovery & Vulnerability Identification** - Find and test vulnerabilities against live environment
4. **Phase 4: Vulnerability Investigation & Exploitation Planning** - Research and validate exploitability against running system
5. **Phase 5: Exploit Development & HackerOne Submission** - Build working exploits and submit with real evidence

## Key Features

### 🎯 Systematic Coverage
- **Domain-Based Exploration**: Security specialists analyze different code areas (auth, input validation, crypto, etc.)
- **CWE Classification**: Every finding gets proper CWE assignment
- **Quality Gates**: Go/no-go decisions prevent wasting time on non-exploitable findings

### 🔬 Professional Investigation
- **Multi-Method Discovery**: Static analysis tools + manual code review
- **Exploitation Research**: WebSearch for latest attack techniques and bypasses
- **Evidence Collection**: Comprehensive proof for HackerOne submissions

### 🏭 Factory Efficiency
- **Tree-Like Expansion**: 1 Phase 1 → 4-6 Phase 2 → 15-30 Phase 3 → 5-10 Phase 4 → 3-8 Phase 5
- **Environment-First Testing**: All phases validate against live docker-compose environment
- **Parallel Processing**: Multiple agents work simultaneously on different domains
- **Coordination**: Memory system shares findings between agents

## Usage

### Basic Usage

```python
from example_workflows.open_source_bug_bounty.phases import BUGBOUNTY_PHASES, BUGBOUNTY_WORKFLOW_CONFIG
from src.sdk import HephaestusSDK

sdk = HephaestusSDK(
    phases=BUGBOUNTY_PHASES,
    workflow_config=BUGBOUNTY_WORKFLOW_CONFIG,
    working_directory="/path/to/target_project",
    llm_provider="openai",
    llm_model="gpt-4",
)

sdk.start()

# Create initial task
task_id = sdk.create_task(
    description="Analyze FastAPI project for security vulnerabilities",
    phase_id=1,
    priority="high",
)

# Monitor progress
sdk.wait_for_completion()
```

### Example Project Setup

```bash
# Clone target project
git clone https://github.com/example/fastapi-project.git
cd fastapi-project

# Install dependencies
pip install -r requirements.txt

# Set up test environment
python setup_database.py

# Run Hephaestus
python -m example_workflows.open_source_bug_bounty.run_analysis
```

## Phase Details

### Phase 1: Environment Research & Production Setup

**Purpose**: Set up realistic testing environment for actual vulnerability validation

**Key Activities**:
- Analyze project type and architecture (web app, CLI tool, library, microservices)
- Research production deployment patterns and dependencies
- Create docker-compose.yml with multi-service environment
- Generate realistic sample data and test scenarios
- Document environment access and usage for other phases

**Environment Setup**:
- Docker-based local environment matching real-world deployments
- Sample applications with vulnerable functionality for testing
- Authentication flows and user management systems
- Database, cache, and external service integrations
- Comprehensive documentation for other agents

### Phase 2: Code Recon & Strategic Targeting

**Purpose**: Strategic analysis using live environment insights

**Key Activities**:
- Analyze running environment to understand actual functionality
- Verify project structure against live services
- Identify security-critical areas based on testable functionality
- Create 4-6 Phase 3 tasks for different domains with live testing objectives

**Domains Covered**:
- Authentication & Authorization (testable against live auth system)
- Input Validation & Data Parsing (validated with real endpoints)
- Cryptography & Secrets Management (tested in running environment)
- File System & External Interactions (verified with actual operations)
- Network Communications & APIs (analyzed against live services)
- Data Storage & Databases (tested with real data operations)

### Phase 3: Pattern Discovery & Vulnerability Identification

**Purpose**: Find and validate potential vulnerabilities using live environment

**Key Activities**:
- Run static analysis tools (bandit, semgrep)
- Manual code review for vulnerability patterns
- **LIVE TESTING**: Test potential vulnerabilities against running environment
- Data flow analysis validated with actual system behavior
- Create Phase 4 tasks ONLY for exploitable/testable vulnerabilities

**Tools Used**:
- **Static Analysis**: bandit, semgrep, pip-audit, npm audit
- **Live Testing**: curl, docker-compose exec, direct API calls
- **Environment Validation**: Testing against docker-compose services

### Phase 4: Vulnerability Investigation & Exploitation Planning

**Purpose**: Research and validate exploitability against live environment

**Key Activities**:
- WebSearch for specific CWE exploitation techniques
- Deep code analysis of vulnerable patterns
- **LIVE VALIDATION**: Test exploitation techniques against running system
- Exploitability assessment based on actual testing (Easy/Medium/Hard/Impossible)
- Go/no-go decision for Phase 5 based on real exploitability

**Exploitability Factors**:
- Live environment accessibility and attack surface
- Security controls validated in running system
- Actual execution context demonstrated in docker-compose
- Real-world security impact proven through testing

### Phase 5: Exploit Development & HackerOne Submission

**Purpose**: Build working exploits against live environment and submit

**Key Activities**:
- Develop reliable Proof of Concept tested against docker-compose
- Collect comprehensive evidence from actual exploitation
- Create professional HackerOne report with real evidence
- Submit via `submit_result` with validated exploitation proof

**Submission Package**:
```
submission_package/
├── hackerone_report.md          # Professional report
├── exploits/
│   └── exploit_[vuln_type].py   # Working exploit
├── evidence/
│   ├── screenshot_exploit.png   # Visual evidence
│   ├── application_logs.txt     # Server logs
│   └── output_dump.txt         # Exfiltrated data
└── README.md                   # Package overview
```

## Validation Criteria

The workflow includes strict validation for HackerOne submissions:

### Technical Validation
- ✅ Exploit successfully demonstrates vulnerability
- ✅ Security impact is clearly shown (not theoretical)
- ✅ Exploit is reliable and reproducible
- ✅ Evidence conclusively proves exploitation

### Professional Standards
- ✅ HackerOne report format compliance
- ✅ Clear reproduction instructions
- ✅ Comprehensive remediation guidance
- ✅ Professional documentation quality

### Project Context
- ✅ Vulnerability exists in actual project
- ✅ Exploitation validated against live environment
- ✅ Current/recent project versions affected
- ✅ No special conditions required for live testing

## Example Outputs

### Phase 1 Outputs
- `docker-compose.yml` - Complete multi-service environment setup
- `environment_setup.md` - Comprehensive configuration and access details
- `security_test_guide.md` - Testing instructions for other phases
- `attack_surface.md` - Documentation of all testable entry points
- Phase 2 code reconnaissance task

### Phase 2 Outputs
- `project_analysis.md` - Security assessment with environment insights
- `security_domains.md` - Mapping of high-risk areas with live testing objectives
- `environment_validation.md` - Testable vs theoretical vulnerabilities
- 4-6 Phase 3 tasks for different security domains

### Phase 3 Outputs
- `domain_[DOMAIN]_findings.md` - All exploitable vulnerabilities discovered and tested
- Static analysis tool outputs with live validation results
- Live environment test logs and validation evidence
- 2-6 Phase 4 tasks for exploitable findings only

### Phase 4 Outputs
- `vulnerability_[CWE_ID]_[LOCATION].md` - Complete investigation with live test results
- Exploitation research validated against running environment
- Live environment test logs showing exploitation attempts
- Phase 5 task (only for vulnerabilities proven exploitable)

### Phase 5 Outputs
- Complete HackerOne submission package with real evidence
- Working exploit tested against docker-compose environment
- Professional security report with actual exploitation proof

## Best Practices

### For Phase 1 Agents
- Research project type and determine appropriate environment setup
- Create realistic, production-like environments using suitable technologies
- Document environment access and usage clearly
- Ensure services are running and testable for security validation
- Provide comprehensive guides for other phases
- Focus on making vulnerabilities actually testable rather than theoretical

### For Phase 2 Agents
- Leverage the live environment for strategic insights
- Focus on testable vs theoretical vulnerabilities
- Create environment-aware domain analysis
- Provide clear testing objectives for Phase 3 agents
- Coordinate with environment documentation

### For Phase 3 Agents
- Validate findings against the running environment
- Prioritize exploitable over theoretical vulnerabilities
- Test potential vulnerabilities before creating tasks
- Document live test results and evidence
- Only create Phase 4 tasks for confirmed exploitable findings

### For Phase 4 Agents
- Validate exploitation techniques in live environment
- Base go/no-go decisions on actual testing results
- Test attack scenarios against docker-compose services
- Document live environment exploitation evidence
- Focus on what can be actually demonstrated

### For Phase 5 Agents
- Develop exploits that work against the live environment
- Collect real evidence from actual exploitation
- Test exploits multiple times for reliability
- Document live environment details in reproduction steps
- Ensure exploits work consistently against docker-compose

## Configuration

### Environment Setup
```python
sdk = HephaestusSDK(
    phases=BUGBOUNTY_PHASES,
    workflow_config=BUGBOUNTY_WORKFLOW_CONFIG,
    working_directory="/path/to/project",
    llm_provider="openai",  # or "anthropic"
    llm_model="gpt-4",
    max_concurrent_agents=3,
    monitoring_interval=60,
)
```

### Customization
You can adjust the workflow by:
- Modifying domain priorities in Phase 1
- Adding tool-specific configurations for Phase 2
- Adjusting exploitability thresholds in Phase 3
- Customizing report templates in Phase 4

## Troubleshooting

### Common Issues

**Phase 1 Creates Too Many Tasks**: Reduce the number of security domains or combine related areas.

**Phase 2 Finds No Vulnerabilities**: Ensure static analysis tools are properly configured and the project has security-relevant code.

**Phase 3 Rejects All Findings**: Check if exploitability assessment is too strict - consider Medium difficulty as acceptable.

**Phase 4 Exploits Fail**: Verify environment setup matches project requirements and all dependencies are installed.

### Debug Mode
Enable detailed logging:
```python
sdk = HephaestusSDK(
    log_level="DEBUG",
    monitoring_interval=30,  # More frequent checks
)
```

## Contributing

To extend this workflow:

1. **Add New Security Domains**: Update Phase 1 task creation logic
2. **Support New Languages**: Add tool configurations for Phase 2
3. **Improve CWE Coverage**: Expand vulnerability pattern recognition
4. **Enhance Validation**: Add new validation criteria for specific vulnerability types

## License

This workflow is part of the Hephaestus project and follows the same license terms.