"""
HackerOne Bug Bounty Hunter - Python Phase Definitions

This file defines the phases for the bug bounty workflow as Python objects.
These can be loaded directly by the SDK without needing YAML files.

Usage:
 from example_workflows.hackerone_bug_bounty.phases import BUGBOUNTY_PHASES, BUGBOUNTY_WORKFLOW_CONFIG
 sdk = HephaestusSDK(
 phases=BUGBOUNTY_PHASES,
 workflow_config=BUGBOUNTY_WORKFLOW_CONFIG,
 working_directory="/path/to/bug_bounty_work",
 ...
 )
"""

from src.sdk.models import Phase, WorkflowConfig

# Phase definitions matching the YAML files
BUGBOUNTY_PHASES = [
 Phase(
 id=1,
 name="program_analysis",
 description="""[This is Phase 1 - Program Intelligence & Strategic Planning]

FOCUS: Parse the bug bounty program, understand all boundaries and compliance
requirements, then strategically spawn 3-6 Phase 2 exploration agents to
systematically map the target domain.

Read OVERVIEW.md and allowed_domain.txt, extract scope and rules, create testing
infrastructure, and spawn Phase 2 explorers to cover different areas of the site.""",
 done_definitions=[
 "OVERVIEW.md has been read and thoroughly analyzed",
 "allowed_domain.txt has been read to identify target domain",
 "All in-scope vulnerability types extracted and documented",
 "All out-of-scope items (assets + vulnerability types) documented",
 "Rules of engagement and compliance requirements documented",
 "Rate limits and testing constraints identified and documented",
 "Test accounts created using @wearehackerone.com email aliases",
 "STRATEGIC ANALYSIS: Identified 3-6 site areas to explore systematically",
 "CRITICAL: Created 3-6 Phase 2 exploration tasks for different site sections",
 "Each Phase 2 task assigned a specific area/section to explore thoroughly",
 "All scope information and compliance rules saved to memory",
 ],
 working_directory=".",
 additional_notes=""" YOUR MISSION: UNDERSTAND THE PROGRAM + SPAWN STRATEGIC EXPLORATION!


 PLAYWRIGHT & CURL: WHEN TO USE WHICH TOOL


 Working test account with username/password is in test_accounts.md - READY TO USE!
 To login: Read test_accounts.md for the email and password - they work and are verified!

**TOOL SELECTION STRATEGY:**

USE PLAYWRIGHT FOR (browser is visible, captchas will be solved):
- Initial login to get authenticated session cookies
- Pages with JavaScript/dynamic content that require rendering
- Actions that need UI interaction (clicks, form fills)
- When you need screenshots for documentation
- Creating test accounts via web interface

USE CURL FOR (faster, preferred when possible):
- API endpoint testing (use cookies from Playwright session)
- Simple GET/POST requests once you have auth cookies
- Repetitive testing where speed matters
- Enumerating endpoints without JS requirements
- Any request that doesn't need browser rendering

**WORKFLOW:** Login with Playwright Extract cookies Use curl with cookies for most testing

 CAPTCHA HANDLING:
If you encounter a captcha in Playwright:
1. WAIT 60 seconds - human will solve it
2. If still not solved, WAIT another 120 seconds
3. Then proceed once captcha is solved

 ACCOUNT BLOCKED TROUBLESHOOTING:
If you see: "Please try again on a different browser type or in an incognito window..."
This means the account is blocked. DO THIS:
1. Create NEW account with format: <random_name>@wearehackerone.com
 - Use password: ThisIsHephaestustest123
 - Register via Playwright
2. REPLACE the old account in test_accounts.md with the new account
3. Document: new email, password, any account details
4. Continue testing with the new account


STEP 1: READ AND PARSE CRITICAL FILES


Read OVERVIEW.md carefully and extract:

A. IN-SCOPE VULNERABILITY TYPES (Examples):
 - Broken Access Control
 - Remote Code Execution (RCE)
 - Injection (SQL, Command, LDAP, etc.)
 - Cross-Site Scripting (XSS)
 - Server-Side Request Forgery (SSRF)
 - Insecure Design
 - Security Misconfiguration
 - Account Takeover (ATO)
 - Authentication Failures
 - Cryptographic Failures
 - [Any others listed in OVERVIEW.md]

B. OUT-OF-SCOPE VULNERABILITY TYPES (Examples):
 - Denial of Service (DoS/DDoS)
 - Social Engineering
 - Clickjacking (unless specific impact)
 - Missing security headers
 - SSL/TLS best practices
 - Automated tool reports without PoC
 - Self-XSS without chaining
 - [Any others listed in OVERVIEW.md]

C. OUT-OF-SCOPE ASSETS:
 - Domains/subdomains explicitly listed as out-of-scope
 - Third-party services
 - [Any others listed in OVERVIEW.md]

D. RULES OF ENGAGEMENT (CRITICAL):
 - Rate limiting requirements (e.g., max 3 requests/second)
 - Forbidden actions (DoS, social engineering, etc.)
 - Data access restrictions
 - Account usage requirements
 - When to stop testing immediately

Read allowed_domain.txt:
- This contains the SINGLE domain to focus exploration on
- All testing MUST be confined to this domain
- Do not test other domains even if they are in-scope


STEP 2: CREATE TESTING INFRASTRUCTURE


Set up test accounts and session cookies:

 EXISTING ACCOUNT: test_accounts.md already has a working username/password!
 - This account is verified and ready to use
 - Login with Playwright, extract cookies, save for curl usage

1. LOGIN WORKFLOW (document this for Phase 2+ agents):
 - Use Playwright to login with test account credentials
 - Extract authenticated session cookies from browser
 - Save cookies to file (cookies.txt or similar)
 - Document cookie format and usage for curl commands
 - Example: curl -H "Cookie: session=xyz..." for authenticated requests

2. OPTIONAL: Create additional test accounts if needed:
 - Generate email aliases using @wearehackerone.com format
 - Example: yourhandle@wearehackerone.com (HackerOne-provided email alias)
 - USE PLAYWRIGHT to register via the web interface
 - Document in test_accounts.md with email, password, account ID

3. Document testing setup:
 - Playwright for: Login, JS pages, screenshots
 - curl for: Most testing (faster, with cookies from Playwright)
 - Rate limiting configuration
 - Compliance checklist

CRITICAL: All Phase 2+ agents MUST use ONLY test accounts from test_accounts.md.
Testing on real user accounts is STRICTLY FORBIDDEN.


STEP 3: CREATE COMPREHENSIVE DOCUMENTATION


Create scope_analysis.md and compliance_rules.md with all extracted information.
Document in-scope vulnerability types, out-of-scope items, rules of engagement,
rate limits, and compliance requirements.


STEP 4: SAVE TO MEMORY (CRITICAL FOR HIVE MIND)


Use save_memory extensively to document:
- Target domain
- Rate limits
- In-scope vulnerability types
- Out-of-scope items (as warnings)
- Critical compliance requirements

WHY: All Phase 2+ agents will fetch these memories to understand
boundaries and avoid violations. This is CRITICAL for compliance.


STEP 5: STRATEGIC AREA SELECTION & SPAWN PHASE 2 EXPLORERS (MANDATORY)


GOAL: Identify and spawn 3-6 Phase 2 EXPLORATION tasks to systematically map the site.

STRATEGIC ANALYSIS - Divide the site into explorable areas:

Consider these area divisions:
1. **Authentication & Account Management**
 - Login, signup, password reset, profile management, session handling

2. **User Content & Data Management**
 - File uploads, data entry forms, user-generated content, data export

3. **API Endpoints & Backend Services**
 - REST APIs, GraphQL, webhooks, integrations, background processes

4. **Administrative & Privileged Functions**
 - Admin panels, role management, permission controls, configuration

5. **E-commerce & Transactions** (if applicable)
 - Payment processing, cart, checkout, order management

6. **Public-Facing Content & Features**
 - Search, comments, social features, content rendering

CRITICAL: TASK CREATION REQUIREMENTS (MANDATORY - NON-NEGOTIABLE!)


WHEN CREATING TASKS, YOU MUST PROVIDE EXTENSIVE DETAIL:

1. DESCRIPTION REQUIREMENTS:
 - MINIMUM 4 lines of detailed description
 - Include WHAT to do, WHERE to do it, WHY it matters
 - Provide specific examples and context
 - Reference relevant files and previous findings

2. DONE_DEFINITION REQUIREMENTS:
 - MINIMUM 6 specific, measurable completion criteria
 - Each must be clear and verifiable
 - Include file outputs, memory saves, and next task creation
 - Be explicit about what "done" means

FAILURE TO MEET THESE REQUIREMENTS MEANS THE TASK WILL BE UNCLEAR AND FAIL!


TASK CREATION - Create 3-6 Phase 2 EXPLORATION tasks using MCP endpoint:

For EACH area, specify:
- description: MINIMUM 4 LINES with full context:
 "Phase 2: Explore [AREA] on [DOMAIN] to find exploitable surfaces.

 Focus on [specific features like login, registration, password reset for auth].
 Systematically navigate through all pages, forms, and APIs in this area using
 Playwright. Identify ALL input points (text fields, file uploads, parameters).
 Extract session cookies after login and save to surface_[AREA]_cookies.txt for
 Phase 3 agents. Create detailed Phase 3 tasks with cookies for each surface found.

 Reference: exploration_areas.md for area boundaries and priorities."

- done_definition: MINIMUM 6 SPECIFIC CRITERIA:
 "Logged in with Playwright and extracted session cookies to surface_[AREA]_cookies.txt"
 "Systematically explored all [AREA] pages and functionality"
 "Identified and documented ALL exploitable surfaces in exploration_[AREA]_surfaces.md"
 "Created Phase 3 reconnaissance task with cookies for EACH surface found"
 "Saved all discovered surfaces to memory with detailed descriptions"
 "No compliance violations occurred during exploration"

- phase_id: 2
- priority: "high"

QUALITY OVER QUANTITY: 6 thorough explorers > 15 scattered ones.


EXPECTED OUTCOMES


After this phase completes:
- Full understanding of program scope and rules
- 3-6 Phase 2 explorers spawned to map different site areas
- Each explorer will systematically find exploitable surfaces
- Testing infrastructure ready
- Compliance rules clearly documented
- Memory system populated with critical program info
- Systematic surface discovery begins!""",
 outputs=[
 "- scope_analysis.md with target domain, in-scope and out-of-scope items",
 "- compliance_rules.md with rate limits, forbidden actions, and requirements",
 "- test_accounts.md with created @wearehackerone.com test accounts",
 "- exploration_areas.md with analysis of site areas to explore",
 "- Memory entries with program scope and rules",
 "- 3-6 Phase 2 exploration tasks for different site sections",
 ],
 next_steps=[
 "Phase 2 explorers will launch in parallel, each systematically mapping",
 "a different area of the site. They will identify exploitable surfaces",
 "(file uploads, text inputs, forms, APIs) and create Phase 3 tasks for",
 "each surface found, enabling targeted vulnerability reconnaissance.",
 ],
 ),
 Phase(
 id=2,
 name="domain_exploration",
 description="""[This is Phase 2 - Systematic Domain Exploration & Surface Discovery]

FOCUS: Systematically explore your assigned site area using Playwright to identify
ALL exploitable surfaces. Map file uploads, text inputs, forms, APIs, and any
other potential vulnerability entry points.

Your task description specifies which AREA to explore (e.g., "authentication flows",
"file upload features", "API endpoints"). Explore thoroughly and create a Phase 3
reconnaissance task for EACH exploitable surface you find.""",
 done_definitions=[
 "OVERVIEW.md, allowed_domain.txt, and compliance_rules.md have been read",
 "Memories fetched to see what other explorers have discovered",
 "Playwright session established with authenticated test account",
 "CRITICAL: Session cookies extracted and saved to surface_[AREA]_cookies.txt",
 "Assigned site area systematically explored using Playwright",
 "ALL exploitable surfaces in the area identified and documented",
 "Each surface documented with: location, functionality, input points, potential vuln types",
 " Phase 3 reconnaissance task created for EACH surface with COOKIES IN TASK DESCRIPTION",
 "exploration_[AREA]_surfaces.md file created with all findings",
 "All discovered surfaces saved to memory for coordination",
 "No compliance violations occurred during exploration",
 ],
 working_directory=".",
 additional_notes=""" YOU ARE A SYSTEMATIC EXPLORER

Your task description tells you which AREA of the site to explore.
Examples: "Authentication flows", "File upload features", "API endpoints"

YOUR MISSION: Find ALL exploitable surfaces in your area, then create Phase 3
tasks so reconnaissance agents can hunt for vulnerabilities in those surfaces.


 TOOL USAGE: PLAYWRIGHT-FIRST EXPLORATION


 Working test account with username/password is in test_accounts.md - READY TO USE!
 To login: Read test_accounts.md for the email and password - they work and are verified!

**PRIMARY TOOL: PLAYWRIGHT (use for 90% of exploration)**

This phase is ALL about systematic Playwright exploration:
- Login and navigate through your assigned area
- Click through all features and workflows
- Fill out forms to understand input points
- Monitor network traffic to find API endpoints
- Take screenshots of interesting surfaces
- Interact with UI to discover hidden functionality

**SECONDARY TOOL: CURL (use sparingly)**
- Only if you need to quickly test an API endpoint
- Use cookies from Playwright session
- Don't spend time on curl - focus on Playwright exploration

**WORKFLOW:** Playwright exploration Document surfaces Create Phase 3 tasks

 CAPTCHA HANDLING:
If you encounter a captcha in Playwright:
1. WAIT 60 seconds - human will solve it
2. If still not solved, WAIT another 120 seconds
3. Then proceed once captcha is solved

 ACCOUNT BLOCKED TROUBLESHOOTING:
If you see: "Please try again on a different browser type or in an incognito window..."
This means the account is blocked. DO THIS:
1. Create NEW account with format: <random_name>@wearehackerone.com
 - Use password: ThisIsHephaestustest123
 - Register via Playwright
2. REPLACE the old account in test_accounts.md with the new account
3. Document: new email, password, any account details
4. Continue exploration with the new account


STEP 1: PREPARATION - READ FILES AND FETCH MEMORIES


MANDATORY READING:
1. OVERVIEW.md - Understand scope, rules, and what's in/out of bounds
2. allowed_domain.txt - Confirm your target domain
3. compliance_rules.md - Know rate limits and forbidden actions
4. exploration_areas.md - Understand your assigned area

FETCH MEMORIES:
- What surfaces have other explorers already found?
- What areas have been covered?
- Any compliance issues or patterns noted?

WHY: Avoid duplicating other explorers' work and learn from discoveries.


STEP 2: SYSTEMATIC PLAYWRIGHT EXPLORATION


GOAL: Navigate your assigned area and identify EVERY exploitable surface.

WHAT IS AN EXPLOITABLE SURFACE?
 File upload fields (images, documents, any file input)
 Text input fields (search, forms, comments, messages)
 URL parameters (query strings, path parameters)
 Forms (login, registration, settings, data submission)
 API endpoints (REST, GraphQL, webhooks discovered via network)
 Data export/import features
 Rich text editors or content rendering
 Any place user-controlled data enters the system

EXPLORATION CHECKLIST:
1. Login with Playwright using test account
2. Navigate to your assigned area (e.g., /profile for user content)
3. Click through EVERY link, button, and tab in the area
4. Fill out forms to see what inputs exist
5. Monitor browser network tab for API calls
6. Take screenshots of interesting surfaces
7. Document each surface you find

DETAILED DOCUMENTATION FOR EACH SURFACE:

For EACH surface, document:
- **Location**: Exact URL and page context
- **Functionality**: What does this feature do?
- **Input Points**: What can user control? (fields, params, files)
- **Potential Vulnerability Types**: What could go wrong here?
 Examples:
 - File upload Unrestricted file upload, XXE, malicious file execution
 - Text input XSS, SQL injection, command injection, LDAP injection
 - URL params SSRF, open redirect, parameter pollution
 - Form CSRF, auth bypass, business logic flaws
 - API IDOR, mass assignment, rate limit bypass


STEP 3: CREATE exploration_[AREA]_surfaces.md FILE


Create a markdown file documenting ALL surfaces found:

```markdown
# Exploitable Surfaces in [AREA]

## Surface 1: Profile Picture Upload
- **Location**: https://example.com/profile/settings
- **Functionality**: Users can upload profile pictures
- **Input Points**: File upload field (accepts images)
- **Potential Vulnerabilities**: Unrestricted file upload, XSS via SVG, ImageTragick
- **Notes**: No visible file type validation on client side

## Surface 2: Bio Text Field
- **Location**: https://example.com/profile/edit
- **Functionality**: Users can enter biography text
- **Input Points**: Textarea for bio (500 char limit)
- **Potential Vulnerabilities**: Stored XSS, HTML injection
- **Notes**: Rich text editor present, needs XSS testing
```


STEP 4: EXTRACT AUTHENTICATED SESSION COOKIES (CRITICAL!)


 After logging in with Playwright, you MUST extract session cookies.

WHY: Phase 3 agents will use these cookies instead of logging in themselves,
saving massive amounts of tokens (90% reduction per agent).

HOW TO EXTRACT COOKIES:

1. **While in Playwright session (after login):**
 - Use: `browser_evaluate` with function: `() => document.cookie`
 - This returns cookie string like: "session=abc123; user_id=456; token=xyz789"

2. **Save cookies to file:**
 - Create file: `surface_[AREA]_cookies.txt`
 - Format: One cookie per line OR the full cookie header string
 - Example content: `session=abc123; user_id=456; token=xyz789`

3. **Prepare cookie string for Phase 3 tasks:**
 - Format for curl: `Cookie: session=abc123; user_id=456; token=xyz789`
 - You'll embed this DIRECTLY in Phase 3 task descriptions

 DO THIS ONCE AFTER LOGIN, then use the same cookies for ALL Phase 3 tasks you create!


STEP 5: SAVE SURFACES TO MEMORY


For EACH surface discovered, save to memory:

Example memory:
"Found exploitable surface: Profile picture upload at https://example.com/profile/settings -
File upload field with no visible validation. Potential for unrestricted file upload,
XSS via SVG, or malicious file execution. Phase 3 recon task created."

WHY: Other agents can learn about discovered surfaces and coordinate hunting.


STEP 6: CREATE PHASE 3 RECONNAISSANCE TASKS (MANDATORY)


CRITICAL: TASK CREATION REQUIREMENTS (MANDATORY - NON-NEGOTIABLE!)


WHEN CREATING TASKS, YOU MUST PROVIDE EXTENSIVE DETAIL:

1. DESCRIPTION REQUIREMENTS:
 - MINIMUM 4 lines of detailed description
 - Include cookies, surface details, functionality, and context
 - Provide specific examples of what to test
 - Reference the exploration file for more context

2. DONE_DEFINITION REQUIREMENTS:
 - MINIMUM 6 specific, measurable completion criteria
 - Must include: reading files, WebSearching, navigating, creating analysis file
 - Must include: creating Phase 4 tasks with cookies for EACH promising CWE
 - Be explicit about what "done" means

FAILURE TO MEET THESE REQUIREMENTS MEANS THE TASK WILL BE UNCLEAR AND FAIL!


For EACH surface found, create a Phase 3 task using MCP endpoint:

TASK FORMAT:
- description: "Phase 3: Reconnaissance on [SURFACE] at [URL]

 AUTHENTICATED SESSION COOKIES (DO NOT LOGIN - USE THESE):
Cookie: [paste the actual cookie string here from Step 4]

Example: Cookie: session=abc123; user_id=456; token=xyz789

Surface Details:
- Functionality: [what the surface does]
- Input Points: [what user controls]
- Potential Vulnerabilities: [initial assessment]

Reference: exploration_[AREA]_surfaces.md"

- done_definition: "Read task description cookies, WebSearched relevant CWEs for [SURFACE], navigated to surface using provided cookies (NO LOGIN), assessed applicability, created Phase 4 tasks with cookies for exploitable CWEs, created cwe_analysis_[ID].md file"
- phase_id: 3
- priority: "high"

 CRITICAL FORMATTING - TASK DESCRIPTION MUST INCLUDE:

1. ** COOKIES SECTION AT THE TOP** (impossible to miss!)
 - Exact cookie string from Step 4
 - Clear label: "DO NOT LOGIN - USE THESE"

2. **Surface details:**
 - Exact URL
 - Functionality description
 - Input points
 - Initial vulnerability assessment

3. **Reference to exploration file**

EXAMPLE COMPLETE TASK DESCRIPTION:
```
Phase 3: Reconnaissance on profile picture upload at https://example.com/profile/settings

 AUTHENTICATED SESSION COOKIES (DO NOT LOGIN - USE THESE):
Cookie: session=abc123xyz; user_id=789; csrf_token=def456

Surface Details:
- Functionality: Users can upload profile pictures (images only claimed)
- Input Points: File upload field accepting images
- Potential Vulnerabilities: Unrestricted file upload, XSS via SVG, ImageTragick

Reference: exploration_authentication_surfaces.md
```

This gives Phase 3 agents EVERYTHING including ready-to-use cookies!""",
 outputs=[
 "- exploration_[AREA]_surfaces.md with ALL exploitable surfaces found",
 "- Memory entries for each discovered surface",
 "- Phase 3 reconnaissance tasks with cookies for EACH surface found",
 "- Screenshots of interesting surfaces for documentation",
 ],
 next_steps=[
 "Phase 3 reconnaissance agents will take each surface you discovered and",
 "WebSearch for relevant CWEs. They'll assess which vulnerabilities might",
 "apply to each surface, then create Phase 4 deep investigation tasks for",
 "promising CWE + surface combinations.",
 ],
 ),
 Phase(
 id=3,
 name="vulnerability_reconnaissance",
 description="""[This is Phase 3 - CWE-Based Vulnerability Reconnaissance]

FOCUS: Take ONE exploitable surface from Phase 2, WebSearch for relevant CWEs,
assess which vulnerabilities might apply, and create Phase 4 deep investigation
tasks for promising attack vectors.

Your task description specifies the exact surface to investigate (URL, feature,
input points). Research applicable CWEs, determine likelihood of exploitation,
and spawn Phase 4 tasks for each promising vulnerability.""",
 done_definitions=[
 "OVERVIEW.md and compliance_rules.md have been read",
 "exploration_[AREA]_surfaces.md has been read for surface details",
 " Cookies extracted from task description (NOT logged in - used provided cookies)",
 "Memories fetched to learn from similar reconnaissance work",
 "Navigated to the specific surface using provided cookies",
 "WebSearched for relevant CWEs based on surface type",
 "Assessed 5-10 CWEs for applicability to this surface",
 "Determined which CWEs are most likely exploitable",
 "Created cwe_analysis_[SURFACE_ID].md with findings",
 "All CWE research saved to memory",
 " Phase 4 investigation task created for EACH promising CWE with COOKIES IN DESCRIPTION",
 "Optional: New Phase 2/3 tasks created if new surfaces discovered",
 ],
 working_directory=".",
 additional_notes=""" YOU ARE A CWE RESEARCHER & RECONNAISSANCE SPECIALIST

Your task description tells you EXACTLY which surface to investigate.
Example: "Phase 3: Reconnaissance on profile picture upload at https://example.com/profile/settings"

YOUR MISSION: Research which CWEs apply to this surface, assess exploitability,
and create Phase 4 tasks for the most promising vulnerabilities.


 CRITICAL: USE COOKIES FROM YOUR TASK DESCRIPTION - DO NOT LOGIN!


 YOUR TASK DESCRIPTION CONTAINS AUTHENTICATED SESSION COOKIES

Look for the section in your task description that says:
" AUTHENTICATED SESSION COOKIES (DO NOT LOGIN - USE THESE):"

DO NOT LOGIN. DO NOT USE PLAYWRIGHT TO LOGIN. DO NOT READ test_accounts.md.

Instead, COPY the cookie string from your task description and use it:

**FOR CURL (90% of cases - use this!):**
```bash
curl -H "Cookie: [paste cookie from task description]" https://example.com/endpoint
```

**FOR PLAYWRIGHT (only if you need visual inspection):**
First set cookies, THEN navigate:
```javascript
# Extract cookie values from task description
# Then use browser_evaluate to set: document.cookie = "session=abc; user_id=123"
# THEN navigate to the URL
```

 CORRECT: Extract cookies from task description Use in requests
 WRONG: Login with Playwright Waste 40k tokens


 TOOL USAGE: CURL + WEBSEARCH (PLAYWRIGHT ONLY IF NEEDED)


**PRIMARY TOOLS FOR THIS PHASE:**

1. **CURL** (use this 90% of the time):
 - Quick navigation to surface using cookies from task description
 - Fast testing without browser overhead
 - Example: `curl -H "Cookie: session=xyz" https://example.com/api/upload`

2. **WEBSEARCH** (THIS IS CRITICAL - spend most time here!):
 - Search for CWEs relevant to this surface type
 - Research known vulnerabilities for similar features
 - Find exploitation techniques and PoCs
 - Learn from real bug bounty reports

3. **PLAYWRIGHT** (only if you need visual inspection - 10% of cases):
 - Set cookies from task description FIRST
 - Then navigate to inspect UI elements
 - Take screenshots for documentation
 - DO NOT LOGIN - just set cookies and navigate

**WORKFLOW:** Extract cookies from task WebSearch CWEs Quick curl test Create Phase 4 tasks with cookies


STEP 1: EXTRACT COOKIES & READ TASK CONTEXT


1. EXTRACT COOKIES FROM YOUR TASK DESCRIPTION:
 - Look for the " AUTHENTICATED SESSION COOKIES" section
 - Copy the entire cookie string
 - Example: "Cookie: session=abc123; user_id=456; token=xyz"
 - Save this - you'll use it for ALL requests AND pass it to Phase 4 tasks

2. READ YOUR TASK DESCRIPTION:
 - Extract the surface URL
 - Understand what feature/functionality this is
 - Note surface details (functionality, input points, potential vulns)

3. READ exploration_[AREA]_surfaces.md:
 - Find your specific surface in the document
 - Review all details for additional context

4. READ COMPLIANCE FILES:
 - OVERVIEW.md - Understand scope and rules
 - compliance_rules.md - Know the boundaries

5. QUICK SURFACE VERIFICATION (optional, use curl):
 - Test that cookies work: `curl -H "Cookie: [your cookies]" [surface URL]`
 - Confirm you get authenticated response
 - If cookies expired, note in memory (rare, but possible)


STEP 2: CWE RESEARCH (CRITICAL - SPEND TIME HERE!)


GOAL: Find 5-10 relevant CWEs that might apply to this surface.

WEBSEARCH STRATEGY:

1. **Search by surface type**:
 - "file upload vulnerability CWE OWASP"
 - "text input injection CWE list"
 - "API parameter vulnerability CWE"

2. **Search for specific CWEs**:
 - "CWE-434 unrestricted file upload exploitation"
 - "CWE-79 XSS attack techniques"
 - "CWE-89 SQL injection bypass methods"

3. **Search for bug bounty reports**:
 - "file upload bug bounty writeup"
 - "[feature type] vulnerability HackerOne report"
 - "CVE [year] [feature type]"

EXAMPLE CWEs BY SURFACE TYPE:

- **File Upload**: CWE-434 (unrestricted upload), CWE-611 (XXE), CWE-502 (deserialization)
- **Text Input**: CWE-79 (XSS), CWE-89 (SQLi), CWE-78 (command injection), CWE-90 (LDAP injection)
- **URL Parameters**: CWE-918 (SSRF), CWE-601 (open redirect), CWE-88 (argument injection)
- **API Endpoints**: CWE-639 (IDOR), CWE-285 (improper authz), CWE-770 (no rate limit)

DOCUMENT YOUR RESEARCH: For each CWE, note:
- CWE ID and name
- How it could apply to this surface
- Exploitation techniques
- Known bypasses
- PoC examples from research


STEP 3: ASSESS CWE APPLICABILITY


GOAL: Determine which CWEs are MOST LIKELY exploitable here.

For EACH CWE researched, ask:
1. **Does this surface have the vulnerable pattern?**
 Example: File upload with no validation CWE-434 applicable

2. **Is this CWE in-scope per OVERVIEW.md?**
 Example: XSS is in-scope, but DoS is not

3. **How likely is exploitation?**
 - High: Surface clearly vulnerable, common attack
 - Medium: Might be vulnerable, needs deep testing
 - Low: Unlikely but theoretically possible

4. **What's the potential impact?**
 - Use program's severity definitions
 - Consider realistic attack scenarios

PRIORITIZE: Focus on high-likelihood, high-impact CWEs first.


STEP 4: CREATE cwe_analysis_[SURFACE_ID].md


Document your CWE research in a structured file:

```markdown
# CWE Analysis: [Surface Name]

## Surface Details
- **URL**: https://example.com/profile/upload
- **Functionality**: Profile picture upload
- **Input Points**: File upload field

## Applicable CWEs

### CWE-434: Unrestricted File Upload (HIGH PRIORITY)
- **Likelihood**: High - No visible file type validation
- **Impact**: Critical - RCE possible if server executes uploaded files
- **Exploitation Approach**: Upload PHP/JSP web shell, access via direct URL
- **Research Sources**: [links to bug bounty reports, CVEs]
- **Scope Status**: In-scope (RCE is explicitly in-scope)

### CWE-79: XSS via SVG Upload (MEDIUM PRIORITY)
- **Likelihood**: Medium - If SVG files are accepted
- **Impact**: Medium - Stored XSS on profile page
- **Exploitation Approach**: Upload SVG with embedded JavaScript
- **Research Sources**: [links]
- **Scope Status**: In-scope (XSS is in-scope)

[Continue for all relevant CWEs...]
```


STEP 5: SAVE TO MEMORY & CREATE PHASE 4 TASKS


1. SAVE CWE RESEARCH TO MEMORY:
 - Each CWE with assessment
 - Links to useful resources
 - Why certain CWEs are applicable/not applicable

2. CREATE PHASE 4 DEEP INVESTIGATION TASKS:

CRITICAL: TASK CREATION REQUIREMENTS (MANDATORY - NON-NEGOTIABLE!)


WHEN CREATING TASKS, YOU MUST PROVIDE EXTENSIVE DETAIL:

1. DESCRIPTION REQUIREMENTS:
 - MINIMUM 4 lines of detailed description
 - Include cookies, CWE details, exploitation approach, and research sources
 - Provide specific guidance on what to attempt
 - Reference the CWE analysis file for full context

2. DONE_DEFINITION REQUIREMENTS:
 - MINIMUM 6 specific, measurable completion criteria
 - Must include: reading files, using cookies, attempting exploitation
 - Must include: testing multiple variations, creating PoC if successful
 - Must include: creating Phase 5 task if exploitable
 - Be explicit about what "done" means

FAILURE TO MEET THESE REQUIREMENTS MEANS THE TASK WILL BE UNCLEAR AND FAIL!


For EACH high/medium priority CWE, create a Phase 4 task:

TASK FORMAT:
- description: "Phase 4: Deep investigation of CWE-[ID] ([NAME]) on [SURFACE] at [URL]

 AUTHENTICATED SESSION COOKIES (DO NOT LOGIN - USE THESE):
Cookie: [paste the SAME cookie string from YOUR task description here]

CWE Details:
- Target CWE: CWE-[ID] ([NAME])
- Likelihood: [High/Medium from your analysis]
- Exploitation Approach: [from your CWE research]
- Research Sources: [links from WebSearch]

Reference: cwe_analysis_[SURFACE_ID].md"

- done_definition: "Read cwe_analysis_[ID].md, used cookies from task description (NO LOGIN), attempted exploitation of CWE-[ID] using cookies for auth, tested 5+ variations, created PoC if successful, created Phase 5 task with cookies if exploitable"
- phase_id: 4
- priority: "high" (for high-likelihood CWEs) or "medium"

 CRITICAL TASK DESCRIPTION FORMATTING:

1. ** COOKIES AT TOP** - Copy the EXACT cookie string from YOUR task description
2. **CWE Details** - Include key info from your research
3. **Reference to analysis file**

EXAMPLE COMPLETE PHASE 4 TASK DESCRIPTION:
```
Phase 4: Deep investigation of CWE-434 (Unrestricted File Upload) on profile picture upload at https://example.com/profile/settings

 AUTHENTICATED SESSION COOKIES (DO NOT LOGIN - USE THESE):
Cookie: session=abc123xyz; user_id=789; csrf_token=def456

CWE Details:
- Target CWE: CWE-434 (Unrestricted File Upload)
- Likelihood: High - No visible file type validation observed
- Exploitation Approach: Upload web shell (PHP/JSP), access via direct URL
- Research Sources: https://hackerone.com/reports/xxxxx, CVE-2024-xxxxx

Reference: cwe_analysis_profile_upload.md
```

CREATE ONE PHASE 4 TASK FOR EACH PROMISING CWE YOU IDENTIFIED.
EACH task MUST include the cookie string so Phase 4 agents don't login!""",
 outputs=[
 "- cwe_analysis_[SURFACE_ID].md with CWE research and assessment",
 "- Screenshots of the surface for documentation",
 "- Memory entries with CWE applicability findings",
 "- Phase 4 deep investigation tasks for EACH promising CWE (2-5 tasks)",
 "- Optional: Additional Phase 2/3 tasks if new surfaces discovered",
 ],
 next_steps=[
 "Phase 4 deep investigation agents will take each CWE you identified and",
 "attempt exploitation using the research and techniques you documented.",
 "They'll try multiple attack variations to develop a working PoC, then",
 "create Phase 5 validation tasks for successful exploits.",
 ],
 ),
 Phase(
 id=4,
 name="deep_investigation",
 description="""[This is Phase 4 - CWE-Specific Deep Investigation & Exploitation]

FOCUS: Take ONE CWE from Phase 3 and attempt exploitation on the specific surface.
Use the CWE research from Phase 3, try multiple attack techniques, develop a working
PoC, and create a Phase 5 validation task if successful.

Your task description specifies the exact CWE to investigate and the surface URL.
Read the CWE analysis, attempt exploitation, and create Phase 5 task if exploitable.""",
 done_definitions=[
 "OVERVIEW.md and compliance_rules.md have been read",
 "cwe_analysis_[SURFACE_ID].md has been read for CWE details",
 " Cookies extracted from task description (NOT logged in - used provided cookies)",
 "Memories fetched for similar exploitation attempts and techniques",
 "Attempted exploitation using cookies for authentication (NO LOGIN PERFORMED)",
 "Tested 5+ different attack variations using curl/Playwright with cookies",
 "Tested bypasses and edge cases based on CWE knowledge",
 "Documented all exploitation attempts and results",
 "If SUCCESSFUL: Working PoC developed and documented",
 "If SUCCESSFUL: Created exploitation_[CWE_ID]_[SURFACE].md with PoC",
 "If SUCCESSFUL: Phase 5 validation task created with PoC reference",
 "If UNSUCCESSFUL: Documented why exploitation failed",
 "All findings saved to memory",
 "Optional: New Phase 2/3/4 tasks created for related discoveries",
 ],
 working_directory=".",
 additional_notes=""" YOU ARE A FOCUSED EXPLOITATION SPECIALIST

Your task description tells you EXACTLY which CWE to exploit and where.
Example: "Phase 4: Deep investigation of CWE-434 (Unrestricted File Upload) on profile picture upload at https://example.com/profile/settings"

YOUR MISSION: Attempt exploitation of this SPECIFIC CWE using techniques from
Phase 3 research. Try multiple variations, develop a working PoC, and create
Phase 5 task if successful.


 CRITICAL: USE COOKIES FROM YOUR TASK DESCRIPTION - DO NOT LOGIN!


 YOUR TASK DESCRIPTION CONTAINS AUTHENTICATED SESSION COOKIES

Look for the section in your task description that says:
" AUTHENTICATED SESSION COOKIES (DO NOT LOGIN - USE THESE):"

DO NOT LOGIN. DO NOT USE PLAYWRIGHT TO LOGIN. DO NOT READ test_accounts.md.

Instead, COPY the cookie string from your task description and use it:

**FOR CURL (USE THIS 90% OF THE TIME - FASTEST!):**
```bash
curl -X POST -H "Cookie: session=abc123; user_id=456" \
 -F "file=@malicious.php" https://example.com/upload
```

**FOR PLAYWRIGHT (only for UI exploits needing visual proof):**
Set cookies FIRST, then navigate and exploit:
```javascript
# Use browser_evaluate to set cookies BEFORE navigation:
# document.cookie = "session=abc123; user_id=456; token=xyz"
# Then navigate to URL and perform exploitation
```

 CORRECT: Extract cookies from task Use in exploitation Fast!
 WRONG: Login with Playwright Waste 40k tokens!


 TOOL USAGE: CURL-FIRST (PLAYWRIGHT ONLY WHEN NECESSARY)


**PRIMARY TOOL: CURL (90% of exploits)**
- SQLi: `curl -H "Cookie: [cookies]" "https://site.com/api?id=1' OR '1'='1"`
- SSRF: `curl -H "Cookie: [cookies]" -d "url=http://169.254.169.254" /api/fetch`
- Command injection: `curl -H "Cookie: [cookies]" -d "cmd=; cat /etc/passwd" /exec`
- File upload: `curl -H "Cookie: [cookies]" -F "file=@shell.php" /upload`
- IDOR: `curl -H "Cookie: [cookies]" https://site.com/api/users/1234/private`
- Any backend CWE exploitation

**SECONDARY TOOL: PLAYWRIGHT (10% of exploits - only when needed)**
- XSS visual confirmation (need to see alert/DOM manipulation)
- File upload + XSS (upload SVG with <script>, view rendered page)
- Complex multi-step UI exploits
- When you need screenshot proof for HackerOne

**WORKFLOW:** Extract cookies curl exploitation Develop PoC Screenshots only if needed


STEP 1: EXTRACT COOKIES & READ CWE ANALYSIS


1. EXTRACT COOKIES FROM YOUR TASK DESCRIPTION:
 - Look for " AUTHENTICATED SESSION COOKIES" section
 - Copy the entire cookie string
 - Example: "Cookie: session=abc123; user_id=456; token=xyz"
 - Save this - you'll use it for ALL exploitation attempts

2. READ YOUR TASK DESCRIPTION:
 - Extract the CWE ID and name (e.g., CWE-434 Unrestricted File Upload)
 - Note the surface URL
 - Review the CWE details provided
 - Note exploitation approach hints

3. READ cwe_analysis_[SURFACE_ID].md:
 - Find the section for YOUR specific CWE
 - Review the exploitation approach documented by Phase 3
 - Note the research sources and PoC examples
 - Understand why Phase 3 assessed this as exploitable

4. FETCH MEMORIES:
 - Has anyone exploited this CWE before?
 - What techniques worked on similar surfaces?
 - Any known bypasses or tricks?


STEP 2: QUICK SURFACE VERIFICATION WITH COOKIES


1. Test cookies work with curl:
 `curl -H "Cookie: [your cookies]" [surface URL]`

2. Confirm the surface exists and functions as documented

3. Identify the exact attack point (input field, parameter, endpoint)

4. You're ready to exploit - NO LOGIN NEEDED!


STEP 3: SYSTEMATIC EXPLOITATION ATTEMPTS


GOAL: Try 5+ exploitation variations based on CWE knowledge.

EXPLOITATION STRATEGY:

1. **Start with Phase 3's recommended approach**:
 - Use the exact technique from cwe_analysis file
 - Follow any PoC examples found in research

2. **Try standard CWE exploitation techniques**:
 - Use known payloads for this CWE
 - Test common bypasses
 - Try encoding variations (URL, HTML, unicode, etc.)

3. **Test edge cases and bypasses**:
 - Capitalization changes (if filters are case-sensitive)
 - Double encoding
 - Null byte injection
 - Content-Type manipulation
 - Parameter pollution
 - Race conditions (if applicable)

4. **Observe responses carefully**:
 - Error messages revealing info?
 - Behavior changes indicating success?
 - Reflection or execution of payload?

DOCUMENT EVERYTHING:
- What payload was tried
- What response was received
- Why it succeeded or failed
- Next variation to try


STEP 4: DEVELOP WORKING POC (IF SUCCESSFUL)


If you achieve successful exploitation:

1. CREATE exploitation_[CWE_ID]_[SURFACE].md with:
 - Working payload(s)
 - Step-by-step reproduction instructions
 - Screenshots showing successful exploitation
 - Explanation of why this works
 - Potential security impact

2. MAKE IT REPRODUCIBLE:
 - Test the PoC 3 times to ensure consistency
 - Document all prerequisites
 - Provide exact curl commands or Playwright steps
 - Note any timing/race condition considerations


STEP 5: CREATE PHASE 5 VALIDATION TASK (IF SUCCESSFUL)


If exploitation was successful, create Phase 5 validation task:

TASK FORMAT:
- description: "Phase 5: Validate and submit CWE-[ID] ([NAME]) on [SURFACE] at [URL]"
 Example: "Phase 5: Validate and submit CWE-434 (Unrestricted File Upload) on profile picture upload at https://example.com/profile/settings"
- done_definition: "Read exploitation_[CWE_ID]_[SURFACE].md, reproduced vulnerability 3+ times, performed 5-point validation, created HackerOne report, called submit_result if all validation passes"
- phase_id: 5
- priority: "critical"

INCLUDE IN TASK:
- CWE ID and name
- Surface URL
- Reference to exploitation_[CWE_ID]_[SURFACE].md file
- Key details for validator

IF UNSUCCESSFUL:
- Document why exploitation failed in memory
- Note what was tried and why it didn't work
- This prevents duplicate effort by other agents
- Do NOT create Phase 5 task""",
 outputs=[
 "- IF SUCCESSFUL: exploitation_[CWE_ID]_[SURFACE].md with working PoC",
 "- IF SUCCESSFUL: Screenshots showing successful exploitation",
 "- IF SUCCESSFUL: Phase 5 validation task created",
 "- IF UNSUCCESSFUL: Memory entry documenting failed attempts",
 "- Memory entries with exploitation findings",
 ],
 next_steps=[
 "If exploitation successful: Phase 5 validation agent will reproduce the",
 "vulnerability, perform rigorous validation checks, create a professional",
 "HackerOne report, and submit if all criteria are met.",
 "",
 "If exploitation unsuccessful: Findings documented in memory to prevent",
 "duplicate work. Other Phase 4 agents continue testing other CWEs.",
 ],
 ),
 Phase(
 id=5,
 name="validation_and_submission",
 description="""[This is Phase 5 - Independent Skeptical Validation & Submission]

FOCUS: You are a SKEPTICAL VALIDATOR. Your job is to INDEPENDENTLY prove the
vulnerability exists WITHOUT trusting Phase 4's claim. Develop your own exploit
proof from scratch, validate it works 3+ times, then submit ONLY if perfect.

CRITICAL: DO NOT blindly trust Phase 4. They might be hallucinating or wrong.
You must INDEPENDENTLY discover and prove the vulnerability yourself.

Your task description specifies the CWE and surface to validate. Read the surface
details and CWE analysis, then INDEPENDENTLY exploit it. Only if YOU can prove it
exists should you submit.

This is the final quality gate. Better to reject a borderline finding than
risk program ban for submitting out-of-scope or low-quality reports.""",
 done_definitions=[
 "OVERVIEW.md and compliance_rules.md have been read",
 "exploitation_[CWE_ID]_[SURFACE].md read to understand WHAT is claimed (not HOW)",
 "cwe_analysis_[SURFACE_ID].md has been read for exploitation techniques",
 "Task description analyzed to understand CWE, surface URL, and functionality",
 "CRITICAL: Approached with skepticism - did NOT blindly follow Phase 4's steps",
 "INDEPENDENTLY developed exploit from scratch using own techniques",
 "Attempted own exploitation methods (did NOT copy Phase 4's exact steps)",
 "INDEPENDENTLY proved vulnerability exists 3+ times with own PoC",
 "RIGOROUS 5-POINT VALIDATION COMPLETED:",
 " 1. Reproducibility: MY exploit works 3+ times consistently",
 " 2. Asset Scope: Asset confirmed in-scope per allowed_domain.txt and OVERVIEW.md",
 " 3. Vulnerability Scope: CWE type confirmed in-scope per OVERVIEW.md",
 " 4. NOT Out-of-Scope: Confirmed NOT in out-of-scope list",
 " 5. Real Impact: Real security impact demonstrated with MY PoC (not theoretical)",
 "Professional HackerOne report created with MY independent findings (if validated)",
 "CRITICAL: submit_result called FIRST with complete evidence (if all validations pass)",
 " MANDATORY IF SUBMITTED: Phase 6 vulnerability chaining task created AFTER submit_result",
 "CRITICAL: update_task_status to 'done' called LAST after Phase 6 task created (if submitted)",
 "If UNABLE to independently prove vulnerability: REJECTED with detailed reasoning",
 "Validation results saved to memory",
 ],
 working_directory=".",
 additional_notes=""" YOU ARE A SKEPTICAL INDEPENDENT VALIDATOR

CRITICAL MINDSET: You are NOT here to confirm Phase 4's findings. You are here
to INDEPENDENTLY PROVE the vulnerability exists. Phase 4 might be wrong,
hallucinating, or exaggerating. Your job is to discover the truth.

APPROACH: Pretend Phase 4 doesn't exist. Read the CWE analysis and surface details,
then exploit it YOURSELF using YOUR OWN techniques. Only if YOU can prove it
independently should you submit.

Your task tells you which CWE and surface to validate.
Example: "Phase 5: Validate and submit CWE-434 (Unrestricted File Upload) on profile picture upload at https://example.com/profile/settings"


 PLAYWRIGHT & CURL: WHEN TO USE WHICH TOOL


 Working test account with username/password is in test_accounts.md - READY TO USE!
 To login: Read test_accounts.md for the email and password - they work and are verified!

**TOOL SELECTION FOR VALIDATION:**

USE PLAYWRIGHT FOR (browser is visible, captchas will be solved):
- Final visual validation and PoC demonstration
- Capturing high-quality screenshots for HackerOne report
- Reproducing UI-based vulnerabilities 3+ times
- Creating professional visual evidence
- Validating exploits that require browser rendering

USE CURL FOR (faster, preferred when possible):
- Validating API/backend vulnerabilities repeatedly
- Quick reproduction testing (3+ times) with session cookies
- Testing edge cases and variations efficiently
- Backend exploit validation
- Any validation that doesn't need visual proof

**WORKFLOW:** Use curl for quick validation, Playwright for visual evidence

 CAPTCHA HANDLING:
If you encounter a captcha in Playwright:
1. WAIT 60 seconds - human will solve it
2. If still not solved, WAIT another 120 seconds
3. Then proceed once captcha is solved

 ACCOUNT BLOCKED TROUBLESHOOTING:
If you see: "Please try again on a different browser type or in an incognito window..."
This means the account is blocked. DO THIS:
1. Create NEW account with format: <random_name>@wearehackerone.com
 - Use password: ThisIsHephaestustest123
 - Register via Playwright
2. REPLACE the old account in test_accounts.md with the new account
3. Document: new email, password, any account details
4. Continue validation with the new account


STEP 1: UNDERSTAND WHAT TO VALIDATE (READ REPORT FOR CONTEXT ONLY)


1. READ YOUR TASK DESCRIPTION:
 - Extract the CWE ID and name
 - Note the exact surface URL
 - Understand what vulnerability type to test for

2. READ exploitation_[CWE_ID]_[SURFACE].md:
 - Understand WHAT vulnerability Phase 4 is claiming exists
 - Note WHERE the vulnerability is located (URL, endpoint, parameter)
 - Note WHAT the expected impact is
 - DO NOT copy their exploitation steps - just understand the claim

3. READ cwe_analysis_[SURFACE_ID].md:
 - Understand the surface functionality
 - Review the CWE research (exploitation techniques, known bypasses)
 - Note the theoretical exploitation approaches

4. READ COMPLIANCE FILES:
 - OVERVIEW.md - Verify scope
 - compliance_rules.md - Know boundaries

5. FETCH MEMORIES:
 - Has anyone independently validated similar CWEs?
 - What exploitation techniques worked?
 - Any false positives to watch for?


STEP 2: INDEPENDENTLY DEVELOP YOUR OWN EXPLOIT


CRITICAL: DO NOT copy Phase 4's approach. Develop YOUR OWN proof.

1. Navigate to the surface (with cookies or fresh login)
2. Based on the CWE type, attempt YOUR OWN exploitation:
 - Use techniques from cwe_analysis research
 - Try multiple payloads and approaches
 - Test bypasses and edge cases
 - Document what works and what doesn't

3. If you CANNOT make it work after 5-10 attempts:
 - The vulnerability might NOT exist
 - Phase 4 might be wrong or hallucinating
 - REJECT the finding with detailed explanation

4. If you CAN make it work:
 - Test 3+ times to confirm consistency
 - Document YOUR exploitation steps
 - Take screenshots of YOUR proof
 - Continue to validation


STEP 3: COMPARE WITH PHASE 4 (OPTIONAL, AFTER YOU HAVE PROOF)


Only AFTER you have independently proven the vulnerability:

1. NOW you can read exploitation_[CWE_ID]_[SURFACE].md
2. Compare Phase 4's approach to yours:
 - Did they find the same vulnerability you found?
 - Are the exploitation techniques similar?
 - Did you both get the same results?

3. If Phase 4's PoC is DIFFERENT from yours:
 - Both might be valid (multiple exploitation paths)
 - Use YOUR PoC for the HackerOne report
 - Note the difference in your validation docs

4. If Phase 4 claimed something you CANNOT reproduce:
 - REJECT the finding
 - Document why Phase 4's claim is unproven


STEP 4: RIGOROUS 5-POINT VALIDATION


You MUST validate ALL 5 points. If ANY fails, DO NOT SUBMIT.

VALIDATION POINT 1: REPRODUCIBILITY /
- Did you reproduce 3+ times successfully?
- Works consistently every time?
- Not intermittent or timing-dependent?

VALIDATION POINT 2: ASSET SCOPE COMPLIANCE /
- Is the asset in allowed_domain.txt?
- Is it in-scope in OVERVIEW.md?
- Is it NOT in out-of-scope assets list?

VALIDATION POINT 3: VULNERABILITY TYPE SCOPE COMPLIANCE /
- Is the CWE/vulnerability type in-scope in OVERVIEW.md?
- Is it NOT in out-of-scope vulnerability types?
- No specific exclusions apply?

VALIDATION POINT 4: NOT IN OUT-OF-SCOPE LIST /
- Re-read ENTIRE out-of-scope section in OVERVIEW.md
- Check for subtle exclusions
- Verify no "except when" clauses apply

VALIDATION POINT 5: REAL SECURITY IMPACT /
- Does this have real, exploitable impact?
- Not just theoretical?
- Realistic attack scenario?
- Demonstrates actual security boundary violation?


STEP 5: CREATE HACKERONE REPORT WITH YOUR INDEPENDENT FINDINGS


IF ALL 5 VALIDATION POINTS ARE :

Create validated_bug_[CWE_ID]_[SURFACE].md with HackerOne format using YOUR
independent exploitation proof (NOT Phase 4's):

```markdown
## Summary:
[2-3 sentences describing the vulnerability YOU discovered]

## Steps To Reproduce:
[Use YOUR exploitation steps, not Phase 4's!]

 1. [First step from YOUR PoC]
 2. [Second step from YOUR PoC]
 3. [Third step from YOUR PoC]
 4. [Result from YOUR testing]

## Impact:
[Detailed explanation of security impact based on YOUR proof]

## Supporting Material/References:
[YOUR screenshots, YOUR PoC, YOUR evidence]

 * Screenshot 1: [from YOUR exploitation]
 * Screenshot 2: [from YOUR testing]
 * PoC script: [YOUR exploit code]
```

CRITICAL:
- Use YOUR exploitation steps, not Phase 4's
- Include YOUR screenshots and proof
- Document YOUR independent findings
- Follow HackerOne format EXACTLY


STEP 6: SUBMISSION DECISION & TASK CREATION (CRITICAL ORDERING!)


IF ALL 5 ARE PASS:
 STEP 1: Call submit_result FIRST with complete evidence
 STEP 2: MANDATORY - Create Phase 6 vulnerability chaining task (see STEP 6 below)
 STEP 3: Call update_task_status to 'done' LAST

IF ANY ARE FAIL:
 Document rejection in rejection_[CWE_ID]_[SURFACE].md
 Save to memory explaining why rejected
 DO NOT SUBMIT
 DO NOT create Phase 6 task
 Call update_task_status to 'done' with rejection summary

 ORDERING IS MANDATORY:
 1. submit_result (if validation passes)
 2. Create Phase 6 task (if validation passes) - MANDATORY!
 3. update_task_status to 'done'

When in doubt DO NOT SUBMIT
Better to reject 10 borderline bugs than submit 1 out-of-scope issue.


STEP 7: CREATE PHASE 6 VULNERABILITY CHAINING TASK (MANDATORY IF SUBMITTED)


 IF YOU SUBMITTED THE BUG (all validations passed), you MUST create a Phase 6 task.

WHY: One vulnerability often enables discovery of additional vulnerabilities.
A validated CWE is a STEPPING STONE to find more severe chained attacks.

TASK FORMAT:
- description: "Phase 6: Research vulnerability chains for CWE-[ID] ([NAME]) validated at [URL]"
 Example: "Phase 6: Research vulnerability chains for CWE-79 (XSS) validated at https://example.com/profile/bio"
- done_definition: "Read validated_bug_[CWE_ID]_[SURFACE].md, explored area using validated CWE access, WebSearched 5+ chaining techniques, assessed 3-5 chain opportunities, created Phase 4 tasks for each promising chain, created chain_analysis_[CWE_ID].md"
- phase_id: 6
- priority: "high"

INCLUDE IN TASK DESCRIPTION:
- The validated CWE ID and name
- The exact URL/surface where it was found
- Reference to validated_bug_[CWE_ID]_[SURFACE].md
- What access/capabilities this CWE provides to an attacker

Example description:
"Phase 6: Research vulnerability chains for CWE-79 (Stored XSS) validated at https://example.com/profile/bio.
This XSS executes in the context of any user viewing the profile. The validated bug gives us:
JavaScript execution in victim browsers, access to victim cookies/localStorage, ability to make
requests as the victim. Reference: validated_bug_79_profile_bio.md"

 YOU MUST CREATE THIS TASK BEFORE calling update_task_status!""",
 outputs=[
 "- validation_results_[CWE_ID]_[SURFACE].md with all 5 validation checks",
 "- IF SUBMITTED: validated_bug_[CWE_ID]_[SURFACE].md with HackerOne report",
 "- IF SUBMITTED: Phase 6 vulnerability chaining task created",
 "- IF REJECTED: rejection_[CWE_ID]_[SURFACE].md explaining why",
 "- Memory entries with validation results",
 "- submit_result call (only if all validations pass)",
 ],
 next_steps=[
 "If submitted: Two things happen in parallel:",
 " 1. The workflow result validator reviews and attempts to reproduce the bug",
 " 2. Phase 6 chaining agent researches how to chain this validated CWE with",
 " additional vulnerabilities to escalate severity and impact",
 "",
 "If rejected: The finding is documented and saved to memory to prevent",
 "duplicate investigation. No Phase 6 task is created.",
 "",
 "The workflow continues - other agents keep hunting for more vulnerabilities.",
 ],
 ),
 Phase(
 id=6,
 name="vulnerability_chaining",
 description="""[This is Phase 6 - Vulnerability Chaining & Escalation Research]

FOCUS: Take ONE validated vulnerability from Phase 5 and research how it can be
CHAINED with additional vulnerabilities to escalate impact and severity.

Your task description specifies the validated CWE. Use the access/capabilities it
provides to explore the surrounding area, WebSearch extensively for chaining
techniques, and create Phase 4 tasks for each promising chain you discover.

CRITICAL: This phase is about finding vulnerabilities that BUILD ON TOP of the
validated one. Low severity bugs become CRITICAL when chained properly.""",
 done_definitions=[
 "OVERVIEW.md and compliance_rules.md have been read",
 "validated_bug_[CWE_ID]_[SURFACE].md has been read to understand the validated CWE",
 "Memories fetched for similar chaining discoveries and techniques",
 "Analyzed what access/capabilities the validated CWE provides to an attacker",
 "EXTENSIVE WEBSEARCH COMPLETED (5+ searches for chaining techniques):",
 " - Searched for chains involving this specific CWE type",
 " - Researched bug bounty reports showing REAL dependency chains",
 " - Found exploitation techniques that build on this CWE",
 " - Studied examples of FAKE chains to avoid",
 " - Discovered real-world chain examples with clear causality",
 "Explored the area around the validated vulnerability using Playwright/curl",
 "Identified new attack surfaces accessible ONLY via the validated CWE",
 "CRITICAL: Applied DEPENDENCY TEST to each potential chain:",
 " - Asked: Can I exploit the second CWE WITHOUT the first?",
 " - Rejected chains where second CWE works independently",
 " - Only accepted chains with DIRECT causality (A enables B)",
 "Created chain_analysis_[CWE_ID].md with dependency analysis for each chain",
 "All chaining opportunities (and rejections) saved to memory with reasoning",
 "Phase 4 task created ONLY for chains that pass dependency test",
 "If no REAL chains found after dependency test: Documented why and created NO tasks",
 ],
 working_directory=".",
 additional_notes=""" YOU ARE A VULNERABILITY CHAIN ARCHITECT

Your task tells you which validated CWE to build upon.
Example: "Phase 6: Research vulnerability chains for CWE-79 (XSS) validated at https://example.com/profile/bio"

YOUR MISSION: Research how this validated CWE can be LEVERAGED to discover
additional vulnerabilities. Turn a medium-severity bug into a CRITICAL chain!


 UNDERSTANDING VULNERABILITY CHAINING


CRITICAL DEFINITION: WHAT IS A REAL CHAIN VS FAKE CHAIN?

A vulnerability chain is when the validated CWE is a MANDATORY PREREQUISITE that
DIRECTLY ENABLES the next vulnerability. Without the first CWE, the second is
IMPOSSIBLE or SIGNIFICANTLY HARDER to exploit.

KEY TEST: "Can I exploit the second CWE WITHOUT the first one?"
- If YES: NOT a chain (just multiple bugs)
- If NO: REAL chain (first enables second)

EXAMPLES OF REAL CHAINS (THESE ARE VALID):

1. **XSS Session Hijacking Account Takeover** (REAL CHAIN)
 - Validated CWE: Stored XSS at /profile/bio
 - Chain: XSS steals admin session cookie when admin views profile
 - Next step: Use stolen cookie to login as admin
 - WHY IT'S A CHAIN: Without XSS, you CANNOT get the admin's session cookie
 - Result: Account takeover (CRITICAL)

2. **SSRF Cloud Metadata AWS Key Theft** (REAL CHAIN)
 - Validated CWE: SSRF at /api/fetch
 - Chain: Use SSRF to reach http://169.254.169.254/latest/meta-data/iam/
 - Next step: Extract AWS credentials from metadata endpoint
 - WHY IT'S A CHAIN: Without SSRF, you CANNOT reach internal metadata endpoint
 - Result: Cloud infrastructure takeover (CRITICAL)

3. **IDOR Email Leak Password Reset Poisoning** (REAL CHAIN)
 - Validated CWE: IDOR exposing user emails at /api/users/{id}
 - Chain: Extract admin email via IDOR
 - Next step: Exploit password reset with known admin email
 - WHY IT'S A CHAIN: Without IDOR, you DON'T KNOW the admin email to target
 - Result: Account takeover (CRITICAL)

4. **File Upload Stored XSS** (REAL CHAIN)
 - Validated CWE: Unrestricted file upload at /upload
 - Chain: Upload malicious SVG file with embedded JavaScript
 - Next step: SVG is rendered on victim's browser, executing JavaScript
 - WHY IT'S A CHAIN: Without file upload, you CANNOT inject the SVG
 - Result: Stored XSS (HIGH)

EXAMPLES OF FAKE CHAINS (THESE ARE NOT VALID - REJECT THESE!):

1. **NoSQL Injection + Account Enumeration + CSRF** (NOT A CHAIN!)
 - Validated CWE: NoSQL injection changes page title
 - Other bugs: Account enumeration API, CSRF on profile update
 - WHY IT'S NOT A CHAIN: Each bug works INDEPENDENTLY
 - You can do CSRF WITHOUT NoSQL injection
 - You can enumerate accounts WITHOUT NoSQL injection
 - These are just 3 separate bugs, not a chain!

2. **XSS + SQLi + IDOR** (NOT A CHAIN!)
 - Validated CWE: XSS on comments page
 - Other bugs: SQLi on search, IDOR on profile API
 - WHY IT'S NOT A CHAIN: XSS doesn't enable SQLi or IDOR
 - Each can be exploited completely independently
 - Just finding multiple bugs is NOT chaining!

3. **SSRF + CSRF** (NOT A CHAIN!)
 - Validated CWE: SSRF to internal services
 - Other bug: CSRF on password change
 - WHY IT'S NOT A CHAIN: SSRF doesn't help you do CSRF
 - CSRF works the same with or without SSRF
 - These are unrelated bugs!

CRITICAL RULES FOR VALID CHAINS:

1. The validated CWE MUST be step 1 in a DIRECT exploit path
2. Step 2 MUST be IMPOSSIBLE (or much harder) without step 1
3. The chain should have CLEAR causality: A enables B, B enables C
4. If you can exploit B WITHOUT exploiting A first, it's NOT a chain
5. "Using them together in an attack scenario" is NOT enough - they must DEPEND on each other


 PLAYWRIGHT & CURL: WHEN TO USE WHICH TOOL


 Working test account with username/password is in test_accounts.md - READY TO USE!
 To login: Read test_accounts.md for the email and password - they work and are verified!

**PRIMARY TOOL: WEBSEARCH (THIS IS THE MOST CRITICAL TOOL FOR THIS PHASE!)**

You MUST perform extensive WebSearches to discover chaining techniques:
- Search for your specific CWE + "chain" or "escalation"
- Look for bug bounty writeups showing chains
- Research common vulnerabilities that follow this CWE type
- Find CVE reports demonstrating chains
- Discover PoCs that combine multiple vulnerabilities

**SECONDARY TOOLS: PLAYWRIGHT & CURL (for exploration)**

USE PLAYWRIGHT FOR:
- Exploring the area around the validated vulnerability
- Testing what the validated CWE gives you access to
- Discovering new surfaces accessible via the exploit
- Taking screenshots of chain opportunities

USE CURL FOR:
- Quick API endpoint enumeration with authenticated session
- Testing access to internal resources (if SSRF/SSRF-like validated)
- Rapidly probing new attack surfaces discovered

**WORKFLOW:** WebSearch extensively Explore with Playwright Document chains Create Phase 4 tasks

 CAPTCHA HANDLING:
If you encounter a captcha in Playwright:
1. WAIT 60 seconds - human will solve it
2. If still not solved, WAIT another 120 seconds
3. Then proceed once captcha is solved

 ACCOUNT BLOCKED TROUBLESHOOTING:
If you see: "Please try again on a different browser type or in an incognito window..."
This means the account is blocked. DO THIS:
1. Create NEW account with format: <random_name>@wearehackerone.com
 - Use password: ThisIsHephaestustest123
 - Register via Playwright
2. REPLACE the old account in test_accounts.md with the new account
3. Document: new email, password, any account details
4. Continue chaining research with the new account


STEP 1: UNDERSTAND THE VALIDATED CWE & ITS CAPABILITIES


1. READ validated_bug_[CWE_ID]_[SURFACE].md:
 - What vulnerability was validated?
 - Where is it located (exact URL/endpoint)?
 - How does the exploit work?
 - What does it give an attacker?

2. ANALYZE ATTACKER CAPABILITIES:

Ask yourself: "What can an attacker DO with this validated CWE?"

Examples by CWE type:

**If CWE-79 (XSS):**
- Execute JavaScript in victim's browser context
- Steal cookies, tokens, localStorage data
- Make authenticated requests as the victim
- Redirect users to malicious sites
- Modify page content in real-time
 Chains: Session hijacking, CSRF, credential theft, clickjacking

**If CWE-639 (IDOR):**
- Access other users' data/resources
- Enumerate user IDs, emails, or sensitive info
- Modify other users' data if write access
- Map internal ID structure
 Chains: Privilege escalation, mass data exfiltration, targeted attacks

**If CWE-918 (SSRF):**
- Make requests to internal services
- Access cloud metadata endpoints
- Scan internal network
- Bypass IP-based access controls
 Chains: Cloud credential theft, internal service exploitation, port scanning

**If CWE-434 (File Upload):**
- Upload arbitrary files to server
- Host content on trusted domain
- Potentially execute code (if upload location accessible)
- Serve malicious payloads from legitimate domain
 Chains: RCE, phishing, malware distribution, stored XSS

**If CWE-89 (SQL Injection):**
- Read/write database data
- Potentially execute OS commands (if DB has xp_cmdshell etc.)
- Extract sensitive data
- Modify authentication/authorization data
 Chains: Credential theft, privilege escalation, RCE, mass data breach

3. FETCH MEMORIES:
 - What chains have other agents discovered?
 - Are there known chaining patterns for this CWE type?
 - Has anyone found similar chains on this domain?


STEP 2: EXTENSIVE WEBSEARCH FOR CHAINING TECHNIQUES (CRITICAL!)


 THIS IS THE MOST IMPORTANT STEP - SPEND TIME HERE!

You MUST perform at least 5 WebSearches to discover chaining techniques.

SEARCH STRATEGY:

1. **CWE-Specific Chaining Searches:**
 - "CWE-[ID] vulnerability chaining techniques"
 - "CWE-[ID] escalation to account takeover"
 - "[CWE name] chain attack bug bounty"
 - "[CWE name] to RCE exploitation chain"

 Examples:
 - "CWE-79 XSS chaining account takeover"
 - "stored XSS to admin compromise chain"
 - "CWE-918 SSRF to AWS credential theft"

2. **Bug Bounty Report Searches:**
 - "[CWE name] chain HackerOne writeup"
 - "[CWE name] to critical severity escalation"
 - "bug bounty [CWE name] chain report 2024"
 - "[technology stack] [CWE name] chain vulnerability"

 Examples:
 - "XSS to ATO HackerOne report"
 - "SSRF chain AWS metadata bug bounty"
 - "IDOR privilege escalation chain writeup"

3. **Follow-Up Vulnerability Searches:**
 - "vulnerabilities that follow [CWE name]"
 - "[CWE name] common next steps exploitation"
 - "what to do after finding [CWE name]"
 - "[CWE name] post-exploitation techniques"

4. **Technology-Specific Searches (if applicable):**
 - "[framework/platform] [CWE name] chain vulnerability"
 - "[technology] security chain attacks"

 Examples (if you know the tech stack):
 - "Django XSS to CSRF chain"
 - "React stored XSS escalation"
 - "AWS SSRF metadata exploitation"

5. **CVE and Real-World Chain Searches:**
 - "CVE [CWE name] vulnerability chain"
 - "[CWE name] real world attack chain"
 - "[CWE name] APT chain techniques"

DOCUMENT YOUR RESEARCH:

For EACH WebSearch, document:
- Search query used
- Relevant chains discovered
- Exploitation techniques found
- Bug bounty reports showing similar chains
- PoC examples or writeups
- Estimated feasibility for this target


STEP 3: EXPLORE THE AREA USING THE VALIDATED CWE


GOAL: Use the validated vulnerability to discover NEW attack surfaces.

1. **Navigate to the validated vulnerability location**:
 - Login with test account
 - Go to the exact URL/surface where the CWE exists
 - Reproduce the validated exploit to confirm access

2. **Explore what the CWE gives you access to**:

 If XSS:
 - What cookies/tokens can you steal?
 - What authenticated requests can you make?
 - What admin functions are accessible with stolen sessions?
 - Are there anti-CSRF tokens you can bypass?

 If IDOR:
 - What data can you access?
 - Can you enumerate other users?
 - What sensitive info is exposed (emails, tokens, IDs)?
 - Can you modify data or just read it?

 If SSRF:
 - What internal URLs can you reach?
 - Can you access cloud metadata (169.254.169.254)?
 - What services are running internally?
 - Are there admin panels on localhost?

 If File Upload:
 - Where are uploaded files stored?
 - Can you access them directly via URL?
 - What file types are allowed/rendered?
 - Can you upload HTML/SVG for stored XSS?

3. **Document new surfaces discovered**:
 - New endpoints accessible via the validated CWE
 - Additional functionality you can reach
 - Privileged features accessible through the chain
 - Sensitive data exposed by the validated vulnerability


STEP 4: IDENTIFY & ASSESS VULNERABILITY CHAINS


GOAL: Combine your WebSearch research with your exploration to identify 1-3
REAL vulnerability chains to investigate.

CRITICAL: QUALITY OVER QUANTITY. One real chain is infinitely better than
five fake chains. If you can't find a real chain where the validated CWE is
a MANDATORY PREREQUISITE, document why and create NO Phase 4 tasks.

For EACH potential chain, assess with THE DEPENDENCY TEST FIRST:

0. **DEPENDENCY TEST** (MOST CRITICAL - IF THIS FAILS, REJECT THE CHAIN!):
 - Ask: "Can I exploit the second CWE WITHOUT exploiting the first?"
 - If YES → NOT A CHAIN, REJECT IT
 - If NO → Might be a chain, continue assessment
 - Example: Can I do CSRF without the validated XSS? YES → Not a chain!
 - Example: Can I steal session cookie without the validated XSS? NO → Real chain!

1. **DIRECT CAUSALITY**: Does the first CWE DIRECTLY enable the second?
 - Is there a CLEAR exploit path: A → B → C?
 - Does A give you something you NEED for B?
 - Would B be IMPOSSIBLE or significantly harder without A?
 - Example: XSS gives you victim's cookie → Cookie enables session hijacking (DIRECT!)
 - Counter-example: XSS exists AND CSRF exists, but XSS doesn't help CSRF (NOT DIRECT!)

2. **IMPACT ESCALATION**: How much does the chain increase severity?
 - Current validated CWE severity: Low/Medium/High
 - Chained result severity: High/Critical
 - Potential payout increase: 3x+

3. **FEASIBILITY**: Can this chain realistically be executed here?
 - Do the necessary conditions exist?
 - Is the follow-up vulnerability likely present?
 - Does the validated CWE actually provide the required access?

4. **SCOPE COMPLIANCE**: Is the chained vulnerability in-scope?
 - Check OVERVIEW.md for chained CWE type
 - Verify not in out-of-scope list
 - Confirm the chain doesn't violate rules of engagement

5. **RESEARCH SUPPORT**: Did you find real-world examples?
 - Bug bounty reports showing this EXACT chain pattern?
 - CVEs demonstrating this dependency?
 - PoCs available for reference?

PRIORITIZE CHAINS:
- ACCEPT: Passes dependency test + Direct causality + Feasible + In-Scope
- REJECT: Fails dependency test OR No direct causality OR Out-of-scope

REMEMBER: If the second CWE works fine WITHOUT the first, it's NOT a chain!


STEP 5: CREATE chain_analysis_[CWE_ID].md


Document all your chaining research in a structured file:

```markdown
# Vulnerability Chain Analysis: CWE-[ID] at [URL]

## Validated Vulnerability Summary
- **CWE**: CWE-[ID] ([Name])
- **Location**: [URL]
- **Capabilities Provided**: [What attacker can do with this]
- **Current Severity**: [Low/Medium/High]

## WebSearch Research Summary
[5+ searches performed - summarize key findings]

### Search 1: "[query]"
- Found: [key chaining techniques discovered]
- Sources: [links to bug bounty reports, CVEs, writeups]

### Search 2: "[query]"
- Found: [chaining patterns identified]
- Sources: [relevant references]

[Continue for all searches...]

## Identified Vulnerability Chains

### Chain 1: [Validated CWE] [CWE-XXX] [Final Impact] (HIGH PRIORITY)
- **Follow-Up CWE**: CWE-XXX ([Name])
- **Chain Logic**:
 1. Use validated CWE-[ID] to [action]
 2. Exploit new surface to achieve [CWE-XXX]
 3. Result in [critical impact]
- **Impact Escalation**: [Current Severity] CRITICAL
- **Feasibility**: High - [why this is likely to work]
- **Research Support**: [links to similar chains in bug bounty reports]
- **Scope Status**: In-scope per OVERVIEW.md
- **Attack Surface**: [exact endpoint/feature to target]

### Chain 2: [Validated CWE] [CWE-YYY] [Final Impact] (MEDIUM PRIORITY)
[Same structure as above...]

### Chain 3: [Validated CWE] [CWE-ZZZ] [Final Impact] (HIGH PRIORITY)
[Same structure as above...]

## Chains Considered But Rejected
- **Chain**: [CWE-ID] [other CWE]
- **Reason for Rejection**: [Out of scope / Low feasibility / etc.]
```


STEP 6: SAVE TO MEMORY & CREATE PHASE 4 TASKS FOR CHAINS


1. SAVE CHAINING RESEARCH TO MEMORY:
 - Each identified chain with feasibility assessment
 - Links to valuable research sources
 - Why certain chains were prioritized or rejected
 - What new surfaces were discovered

2. CREATE PHASE 4 TASKS FOR EACH PROMISING CHAIN:

CRITICAL: TASK CREATION REQUIREMENTS (MANDATORY - NON-NEGOTIABLE!)


WHEN CREATING TASKS, YOU MUST PROVIDE EXTENSIVE DETAIL:

1. DESCRIPTION REQUIREMENTS:
 - MINIMUM 4 lines of detailed description
 - Include the FULL chain (Validated CWE → New CWE → Final Impact)
 - Explain HOW to use the validated CWE as starting point
 - Provide exploitation approach based on your WebSearch research
 - Reference both chain_analysis and validated_bug files

2. DONE_DEFINITION REQUIREMENTS:
 - MINIMUM 6 specific, measurable completion criteria
 - Must include: reading both analysis files, attempting chained exploitation
 - Must include: testing multiple chain variations, creating PoC if successful
 - Must include: creating Phase 5 task if chain exploit works
 - Be explicit about what "done" means

FAILURE TO MEET THESE REQUIREMENTS MEANS THE TASK WILL BE UNCLEAR AND FAIL!


For EACH high/medium priority chain, create a Phase 4 task:

TASK FORMAT:
- description: "Phase 4: Investigate chain: CWE-[VALIDATED] CWE-[NEW] ([NAME]) at [URL]"

 Example: "Phase 4: Investigate chain: CWE-79 (XSS) CWE-352 (Session Hijacking) Account Takeover at https://example.com/profile/bio.

 Start by exploiting the validated stored XSS to steal admin session cookies when admin views profile.
 Research shows XSS session hijacking ATO is a common high-impact chain. The XSS executes in viewer
 context, giving access to their cookies/localStorage. Target admin accounts by crafting profiles that
 admins are likely to review. Reference: chain_analysis_79.md and validated_bug_79_profile_bio.md"

- done_definition: "Read chain_analysis_[CWE_ID].md and validated_bug_[CWE_ID]_[SURFACE].md, attempted chained exploitation using validated CWE as starting point, tested 5+ chain attack variations, created PoC if successful, created Phase 5 task if chain exploit works"

- phase_id: 4

- priority: "critical" (for high-priority chains) or "high" (for medium-priority chains)

CRITICAL: Include in task description:
- The FULL chain: [Validated CWE] [New CWE] [Final Impact]
- How to use the validated CWE as the starting point
- What new vulnerability to look for in the chain
- Reference to both chain_analysis_[CWE_ID].md and validated_bug_[CWE_ID]_[SURFACE].md
- Key insights from your WebSearch research
- The attack surface to target for the chain

CREATE ONE PHASE 4 TASK FOR EACH HIGH/MEDIUM PRIORITY CHAIN YOU IDENTIFIED.

IF NO VIABLE CHAINS FOUND:
- Document in chain_analysis_[CWE_ID].md why no chains are feasible
- Save to memory explaining the research performed
- Do NOT create Phase 4 tasks
- This is acceptable - not all vulnerabilities have exploitable chains""",
 outputs=[
 "- chain_analysis_[CWE_ID].md with comprehensive chaining research",
 "- Memory entries documenting all identified chains and research",
 "- Phase 4 investigation tasks for EACH promising chain identified",
 "- Documentation of WebSearch findings and chaining techniques",
 "- If no chains found: Explanation of why chains aren't viable",
 ],
 next_steps=[
 "Phase 4 deep investigation agents will take each chain you identified and",
 "attempt to exploit it. They'll use the validated CWE as a stepping stone",
 "to achieve the chained vulnerability, develop a working multi-stage PoC,",
 "and create Phase 5 validation tasks for successful chains.",
 "",
 "Successful chains can increase bug bounty payouts by 3x-50x depending on",
 "the severity escalation. A medium XSS becomes critical when chained to ATO.",
 ],
 ),
]

# Workflow configuration for result handling
BUGBOUNTY_WORKFLOW_CONFIG = WorkflowConfig(
 has_result=True,
 result_criteria="""VALIDATION REQUIREMENTS FOR BUG BOUNTY SUBMISSION ACCEPTANCE:


CRITICAL: A SUBMISSION IS ONLY VALID IF ALL REQUIREMENTS ARE MET


1. **SCOPE COMPLIANCE** (MANDATORY - VIOLATIONS CAN RESULT IN BAN)
 Asset is in the allowed domain from allowed_domain.txt
 Asset is listed as in-scope in OVERVIEW.md
 Vulnerability type is in the in-scope list from OVERVIEW.md
 Vulnerability type is NOT in the out-of-scope list
 No rules of engagement were violated during discovery
 Testing was performed only on self-created test accounts

2. **REPRODUCIBILITY** (MANDATORY)
 Bug reproduces consistently (tested 3+ times)
 Clear, step-by-step reproduction instructions provided
 Working proof of concept included
 All prerequisites documented (accounts, permissions, etc.)
 Expected vs actual behavior clearly demonstrated

3. **SECURITY IMPACT** (MANDATORY)
 Real security impact demonstrated (not theoretical)
 Impact aligns with program's severity definitions
 Confidentiality, integrity, or availability affected
 Business risk clearly articulated
 Attack scenario is realistic and plausible

4. **SUBMISSION QUALITY** (MANDATORY)
 Follows exact HackerOne markdown format
 Professional, clear, and concise language
 Summary section: Brief, accurate vulnerability description
 Steps to Reproduce: Numbered, detailed, complete steps
 Supporting Material: Screenshots, logs, PoC code included
 No sensitive data exposed in submission

5. **TESTING COMPLIANCE** (MANDATORY)
 Rate limits respected during discovery
 No denial of service attacks performed
 No social engineering attempted
 No access to real user data
 No aggressive automated scanning
 Testing stopped immediately if sensitive data accessed
 Only @wearehackerone.com email accounts used


VALIDATION DECISION CRITERIA:


 APPROVE if and only if:
 - ALL scope compliance checks pass
 - Bug reproduces reliably with provided steps
 - Real security impact is demonstrated
 - Submission is professional and complete
 - No testing violations occurred

 REJECT if:
 - Asset or vulnerability type out of scope
 - Cannot reproduce the bug
 - Only theoretical impact (no real exploit)
 - Missing steps, PoC, or evidence
 - Rules of engagement violated
 - Submission quality is poor

CRITICAL VALIDATION APPROACH - YOU ARE A SKEPTICAL VALIDATOR:

YOU ARE NOT HERE TO CONFIRM THE SUBMISSION. YOU ARE HERE TO INDEPENDENTLY
PROVE THE VULNERABILITY EXISTS. The submitter might be wrong, hallucinating,
or exaggerating.

When validating:
1. Read the submission to understand WHAT vulnerability is being claimed
2. Note WHERE it's located (URL, endpoint, parameter)
3. Note WHAT the expected impact is
4. First verify asset and vulnerability type are in-scope
5. Check OVERVIEW.md out-of-scope list carefully
6. DO NOT blindly follow the submission's steps - develop YOUR OWN exploitation
7. Based on the CWE and surface, INDEPENDENTLY attempt exploitation
8. Try YOUR OWN payloads and techniques (not the submission's payloads)
9. If YOU cannot make it work after 5-10 attempts, REJECT IT
10. Only if YOU can independently prove it exists with YOUR OWN PoC, then APPROVE
11. Verify real security impact with YOUR proof (not their claims)
12. Ensure submission format is professional
13. Confirm no testing violations occurred

KEY PRINCIPLE: If you cannot INDEPENDENTLY reproduce the vulnerability using
your own techniques, REJECT IT. Do not approve based on trust.

EXAMPLES:
- Submission claims: XSS at /profile with payload <script>alert(1)</script>
- You try: Multiple XSS payloads at /profile
- If NONE work: REJECT - "Could not independently reproduce XSS after 10 attempts"
- If ONE works: APPROVE - "Independently confirmed XSS with payload: [your payload]"

REMEMBER: Better to reject a borderline submission than risk program ban.
Only approve vulnerabilities YOU personally proved exist.
Do not trust claims - verify independently.""",
 on_result_found="do_nothing", # Don't stop - keep finding more bugs!
)
