import pytest


@pytest.fixture
def mock_cases_missing_auth():
    """Generated cases covering happy_path/negative/boundary but missing auth_permission."""
    return [
        {"id": "tc-1", "title": "User resets password with valid link", "category": "happy_path",
         "steps": ["Request reset"], "expected_result": "Login succeeds"},
        {"id": "tc-2", "title": "Reset link expired after one hour", "category": "boundary",
         "steps": ["Wait past expiry"], "expected_result": "Link rejected"},
        {"id": "tc-3", "title": "Reset requested for unregistered email", "category": "negative",
         "steps": ["Request reset with bad email"], "expected_result": "Generic confirmation, no email sent"},
    ]


@pytest.fixture
def mock_cases_with_dupe():
    """Two cases with near-identical titles that should be flagged as duplicates."""
    return [
        {"id": "tc-1", "title": "User resets password with valid link", "category": "happy_path",
         "steps": ["Request reset"], "expected_result": "Login succeeds"},
        {"id": "tc-2", "title": "User resets their password using a valid reset link", "category": "happy_path",
         "steps": ["Request reset"], "expected_result": "Login succeeds"},
    ]


@pytest.fixture
def mock_cases_off_topic():
    """One case with no keyword overlap with the requirement text - should be flagged."""
    return [
        {"id": "tc-1", "title": "User resets password with valid link", "category": "happy_path",
         "steps": ["Request reset"], "expected_result": "Login succeeds"},
        {"id": "tc-4", "title": "Unrelated dashboard widget loads correctly", "category": "negative",
         "steps": ["Log in", "View dashboard"], "expected_result": "Widget renders"},
    ]
