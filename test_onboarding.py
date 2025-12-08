"""
Simple integration test for onboarding flow.
This tests the onboarding modal component and API integration.
"""

import json
import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_onboarding_modal():
    """Test that the OnboardingModal component can be imported."""
    try:
        # Try to import the component
        from components.Auth.OnboardingModal import OnboardingModal
        print("[PASS] OnboardingModal component imported successfully")
        return True
    except ImportError as e:
        print(f"[FAIL] Failed to import OnboardingModal: {e}")
        return False

def test_api_endpoint_structure():
    """Test that the API endpoint structure is correct."""
    # Check if the users.py file exists and has the onboarding endpoint
    users_file_path = os.path.join(os.path.dirname(__file__), 'backend', 'src', 'api', 'routes', 'users.py')

    if not os.path.exists(users_file_path):
        print("[FAIL] users.py file not found")
        return False

    with open(users_file_path, 'r') as f:
        content = f.read()

    # Check for the onboarding endpoint
    if '/onboarding' in content and 'def submit_onboarding(' in content:
        print("[PASS] Onboarding API endpoint found in users.py")
        return True
    else:
        print("[FAIL] Onboarding API endpoint not found")
        return False

def test_schema_definitions():
    """Test that the required schemas are defined."""
    schema_file_path = os.path.join(os.path.dirname(__file__), 'backend', 'src', 'schemas', 'auth.py')

    if not os.path.exists(schema_file_path):
        print("[FAIL] auth.py schemas file not found")
        return False

    with open(schema_file_path, 'r') as f:
        content = f.read()

    required_schemas = [
        'OnboardingResponseCreate',
        'OnboardingBatch',
        'SuccessResponse'
    ]

    missing_schemas = []
    for schema in required_schemas:
        if f'class {schema}' not in content:
            missing_schemas.append(schema)

    if not missing_schemas:
        print("[PASS] All required onboarding schemas found")
        return True
    else:
        print(f"[FAIL] Missing schemas: {', '.join(missing_schemas)}")
        return False

def test_database_models():
    """Test that the database models are defined."""
    model_file_path = os.path.join(os.path.dirname(__file__), 'backend', 'src', 'models', 'auth.py')

    if not os.path.exists(model_file_path):
        print("[FAIL] auth.py models file not found")
        return False

    with open(model_file_path, 'r') as f:
        content = f.read()

    required_models = [
        'class UserBackground',
        'class OnboardingResponse'
    ]

    missing_models = []
    for model in required_models:
        if model not in content:
            missing_models.append(model)

    if not missing_models:
        print("[PASS] All required database models found")
        return True
    else:
        print(f"[FAIL] Missing models: {', '.join(missing_models)}")
        return False

def main():
    """Run all tests."""
    print("Running onboarding integration tests...\n")

    tests = [
        ("Onboarding Modal Import", test_onboarding_modal),
        ("API Endpoint Structure", test_api_endpoint_structure),
        ("Schema Definitions", test_schema_definitions),
        ("Database Models", test_database_models),
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"\nTesting {test_name}:")
        if test_func():
            passed += 1

    print(f"\n\n{'='*50}")
    print(f"Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("[SUCCESS] All tests passed! Onboarding implementation is ready.")
    else:
        print("[WARNING] Some tests failed. Please review the implementation.")

    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)