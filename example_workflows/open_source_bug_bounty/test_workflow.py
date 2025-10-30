#!/usr/bin/env python3
"""
Test script for the Open Source Bug Bounty workflow.

This script demonstrates how to use the workflow and validates that all phases
are properly configured and importable.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from example_workflows.open_source_bug_bounty.phases import BUGBOUNTY_PHASES, BUGBOUNTY_WORKFLOW_CONFIG

def test_workflow_import():
    """Test that the workflow imports correctly."""
    print("✅ Workflow imports successfully!")
    print(f"📊 Loaded {len(BUGBOUNTY_PHASES)} phases")

    for phase in BUGBOUNTY_PHASES:
        print(f"  - Phase {phase.id}: {phase.name}")

    print(f"🔧 Workflow config: has_result={BUGBOUNTY_WORKFLOW_CONFIG.has_result}")
    return True

def test_phase_structure():
    """Test that all phases have required fields."""
    print("\n🔍 Validating phase structure...")

    required_fields = ['id', 'name', 'description', 'done_definitions', 'working_directory']

    for i, phase in enumerate(BUGBOUNTY_PHASES, 1):
        print(f"  Phase {phase.id} ({phase.name}):")

        for field in required_fields:
            if hasattr(phase, field) and getattr(phase, field):
                print(f"    ✅ {field}")
            else:
                print(f"    ❌ {field} - MISSING!")
                return False

        # Check done_definitions
        if phase.done_definitions:
            print(f"    📋 {len(phase.done_definitions)} done definitions")
        else:
            print(f"    ⚠️  No done definitions")

        # Check outputs
        if phase.outputs:
            print(f"    📦 {len(phase.outputs)} expected outputs")
        else:
            print(f"    ⚠️  No expected outputs")

    print("✅ All phases have required fields!")
    return True

def test_workflow_sequence():
    """Test that phases are properly sequenced."""
    print("\n🔢 Validating phase sequence...")

    expected_ids = [1, 2, 3, 4, 5]
    actual_ids = [phase.id for phase in BUGBOUNTY_PHASES]

    if actual_ids == expected_ids:
        print("✅ Phases are correctly sequenced!")
        return True
    else:
        print(f"❌ Phase sequence mismatch!")
        print(f"   Expected: {expected_ids}")
        print(f"   Actual: {actual_ids}")
        return False

def demonstrate_usage():
    """Show how to use the workflow."""
    print("\n🚀 Usage Example:")
    print("""
from example_workflows.open_source_bug_bounty.phases import BUGBOUNTY_PHASES, BUGBOUNTY_WORKFLOW_CONFIG
from src.sdk import HephaestusSDK

# Initialize the SDK with the bug bounty workflow
sdk = HephaestusSDK(
    phases=BUGBOUNTY_PHASES,
    workflow_config=BUGBOUNTY_WORKFLOW_CONFIG,
    working_directory="/path/to/target_project",
    llm_provider="openai",
    llm_model="gpt-4",
)

# Start the workflow
sdk.start()

# Create initial task to begin bug hunting
task_id = sdk.create_task(
    description="Analyze FastAPI project for security vulnerabilities",
    phase_id=1,
    priority="high",
)

print(f"🎯 Created initial task: {task_id}")
print("🔍 Bug hunting has begun!")

# Monitor progress
sdk.wait_for_completion()
""")

def main():
    """Run all tests and demonstrations."""
    print("🧪 Testing Open Source Bug Bounty Workflow")
    print("=" * 50)

    success = True

    # Test import
    try:
        success &= test_workflow_import()
    except Exception as e:
        print(f"❌ Import test failed: {e}")
        success = False

    # Test phase structure
    try:
        success &= test_phase_structure()
    except Exception as e:
        print(f"❌ Structure test failed: {e}")
        success = False

    # Test phase sequence
    try:
        success &= test_workflow_sequence()
    except Exception as e:
        print(f"❌ Sequence test failed: {e}")
        success = False

    # Show usage
    try:
        demonstrate_usage()
    except Exception as e:
        print(f"❌ Usage demo failed: {e}")
        success = False

    print("\n" + "=" * 50)
    if success:
        print("🎉 All tests passed! The workflow is ready to use.")
        print("\n🎯 Next steps:")
        print("1. Choose an open source project to analyze")
        print("2. Clone it to a local directory")
        print("3. Run the workflow with the project path")
        print("4. Monitor the bug hunting progress!")
    else:
        print("❌ Some tests failed. Please check the configuration.")

    return success

if __name__ == "__main__":
    main()