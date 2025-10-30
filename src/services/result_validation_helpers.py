"""Validation helpers for workflow result content."""

import re
from typing import Dict, Any, List, Optional
from pathlib import Path


class ValidationResult:
    """Result of content validation against criteria."""

    def __init__(self, passed: bool, feedback: str, evidence: List[Dict[str, Any]] = None):
        self.passed = passed
        self.feedback = feedback
        self.evidence = evidence or []

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "passed": self.passed,
            "feedback": self.feedback,
            "evidence": self.evidence,
        }


def validate_markdown_structure(content: str) -> List[str]:
    """
    Validate that markdown content has proper structure for results.

    Args:
        content: Markdown content to validate

    Returns:
        List of validation errors (empty if valid)
    """
    errors = []

    # Check for minimum length
    if len(content.strip()) < 100:
        errors.append("Result content is too short (minimum 100 characters)")

    # Check for basic markdown headers
    if not re.search(r'^#+\s+', content, re.MULTILINE):
        errors.append("No markdown headers found - results should have clear sections")

    # Check for code blocks or evidence
    has_code_block = '```' in content
    has_evidence_section = re.search(r'(evidence|proof|result|solution)', content, re.IGNORECASE)

    if not (has_code_block or has_evidence_section):
        errors.append("No code blocks or evidence sections found - results should include proof")

    return errors


def validate_result_criteria(content: str, criteria: str) -> ValidationResult:
    """
    Validate result content against specific criteria.

    Args:
        content: Markdown content of the result
        criteria: Criteria string to validate against

    Returns:
        ValidationResult with validation outcome
    """
    # Convert criteria to lowercase for case-insensitive matching
    criteria_lower = criteria.lower()
    content_lower = content.lower()

    evidence = []
    feedback_parts = []

    # Check for required keywords in criteria
    keywords = extract_keywords_from_criteria(criteria)
    missing_keywords = []
    found_keywords = []

    for keyword in keywords:
        if keyword.lower() in content_lower:
            found_keywords.append(keyword)
            evidence.append({
                "type": "keyword_match",
                "keyword": keyword,
                "found": True,
            })
        else:
            missing_keywords.append(keyword)
            evidence.append({
                "type": "keyword_match",
                "keyword": keyword,
                "found": False,
            })

    # Analyze structure
    structure_errors = validate_markdown_structure(content)
    if structure_errors:
        feedback_parts.extend(structure_errors)
        evidence.append({
            "type": "structure_validation",
            "errors": structure_errors,
        })

    # Check for specific evidence patterns
    evidence_patterns = [
        (r'```[\s\S]*?```', "code_block", "Code examples/outputs"),
        (r'!\[.*?\]\(.*?\)', "image", "Screenshots/images"),
        (r'https?://[^\s]+', "url", "External links"),
        (r'\$.*?\$|\$\$[\s\S]*?\$\$', "command", "Commands/execution"),
    ]

    for pattern, evidence_type, description in evidence_patterns:
        matches = re.findall(pattern, content)
        if matches:
            evidence.append({
                "type": evidence_type,
                "count": len(matches),
                "description": description,
            })

    # Generate feedback
    if found_keywords:
        feedback_parts.append(f"Found required keywords: {', '.join(found_keywords)}")

    if missing_keywords:
        feedback_parts.append(f"Missing keywords: {', '.join(missing_keywords)}")

    if not structure_errors:
        feedback_parts.append("Markdown structure is well-formatted")

    # Determine if validation passed
    # Simple heuristic: must have some keywords and good structure
    has_keywords = len(found_keywords) > 0
    has_good_structure = len(structure_errors) == 0
    has_evidence = any(e["type"] in ["code_block", "image", "command"] for e in evidence)

    passed = has_keywords and has_good_structure and has_evidence

    feedback = "; ".join(feedback_parts) if feedback_parts else "No specific feedback"

    if not passed:
        if not has_keywords:
            feedback = "Missing required keywords from criteria. " + feedback
        if not has_good_structure:
            feedback = "Poor markdown structure. " + feedback
        if not has_evidence:
            feedback = "Lacks concrete evidence (code, screenshots, etc.). " + feedback

    return ValidationResult(passed, feedback, evidence)


def extract_keywords_from_criteria(criteria: str) -> List[str]:
    """
    Extract important keywords from criteria string.

    Args:
        criteria: Criteria string

    Returns:
        List of important keywords
    """
    # Common important words to look for
    important_patterns = [
        r'\b(password|flag|key|solution|result|output|proof|evidence)\b',
        r'\b(working|successful|complete|implement|fix|solve)\b',
        r'\b(test|verify|demonstrate|show|provide)\b',
    ]

    keywords = set()
    for pattern in important_patterns:
        matches = re.findall(pattern, criteria, re.IGNORECASE)
        keywords.update(matches)

    # Also extract quoted strings as specific requirements
    quoted_strings = re.findall(r'"([^"]+)"', criteria)
    keywords.update(quoted_strings)

    return list(keywords)


def validate_file_contains_solution(file_path: str, criteria: str) -> ValidationResult:
    """
    Validate that a file contains a solution matching criteria.

    Args:
        file_path: Path to the result file
        criteria: Validation criteria

    Returns:
        ValidationResult with validation outcome
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        return validate_result_criteria(content, criteria)

    except FileNotFoundError:
        return ValidationResult(
            False,
            f"Result file not found: {file_path}",
            [{"type": "file_error", "error": "File not found"}]
        )
    except Exception as e:
        return ValidationResult(
            False,
            f"Error reading result file: {str(e)}",
            [{"type": "file_error", "error": str(e)}]
        )


def validate_evidence_sections(content: str) -> ValidationResult:
    """
    Validate that content has proper evidence sections.

    Args:
        content: Markdown content

    Returns:
        ValidationResult focusing on evidence quality
    """
    evidence = []
    feedback_parts = []

    # Look for common evidence section headers
    evidence_headers = [
        "solution", "result", "proof", "evidence", "demonstration",
        "output", "execution", "verification", "testing"
    ]

    found_sections = []
    for header in evidence_headers:
        pattern = rf'^#+\s*{re.escape(header)}'
        if re.search(pattern, content, re.IGNORECASE | re.MULTILINE):
            found_sections.append(header)

    evidence.append({
        "type": "evidence_sections",
        "found_sections": found_sections,
        "count": len(found_sections),
    })

    if found_sections:
        feedback_parts.append(f"Found evidence sections: {', '.join(found_sections)}")
    else:
        feedback_parts.append("No clear evidence sections found")

    # Check for step-by-step explanations
    numbered_steps = len(re.findall(r'^\d+\.', content, re.MULTILINE))
    bullet_points = len(re.findall(r'^\s*[-*+]', content, re.MULTILINE))

    evidence.append({
        "type": "structured_explanation",
        "numbered_steps": numbered_steps,
        "bullet_points": bullet_points,
    })

    if numbered_steps > 0:
        feedback_parts.append(f"Contains {numbered_steps} numbered steps")
    if bullet_points > 0:
        feedback_parts.append(f"Contains {bullet_points} bullet points")

    # Overall assessment
    has_sections = len(found_sections) > 0
    has_structure = numbered_steps > 0 or bullet_points > 0

    passed = has_sections and has_structure

    feedback = "; ".join(feedback_parts) if feedback_parts else "Basic evidence structure"

    return ValidationResult(passed, feedback, evidence)