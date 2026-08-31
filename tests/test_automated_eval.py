"""
Formal test suite for eval/automated_eval.py.

Same checks as the original dry_run_test.py, split into isolated tests: a failure
in one doesn't hide the results of the others, and this is discoverable/runnable
by pytest (and therefore CI) instead of a script you have to remember to execute.
"""

import sys
sys.path.insert(0, ".")

from eval.automated_eval import evaluate


def test_coverage_detects_missing_category(mock_cases_missing_auth):
    result = evaluate("password_reset", mock_cases_missing_auth)
    assert result.coverage["auth_permission"] is False
    assert result.coverage["happy_path"] is True
    assert result.coverage["boundary"] is True
    assert result.coverage["negative"] is True


def test_coverage_score_reflects_missing_category(mock_cases_missing_auth):
    result = evaluate("password_reset", mock_cases_missing_auth)
    # 3 of 4 applicable categories hit
    assert result.coverage_score == 0.75


def test_full_coverage_scores_100_percent():
    all_categories = [
        {"id": "tc-1", "title": "Valid reset flow", "category": "happy_path", "steps": [], "expected_result": ""},
        {"id": "tc-2", "title": "Invalid email rejected", "category": "negative", "steps": [], "expected_result": ""},
        {"id": "tc-3", "title": "Link expiry boundary", "category": "boundary", "steps": [], "expected_result": ""},
        {"id": "tc-4", "title": "Token reuse rejected", "category": "auth_permission", "steps": [], "expected_result": ""},
    ]
    result = evaluate("password_reset", all_categories)
    assert result.coverage_score == 1.0


def test_duplicate_detection_flags_near_identical_titles(mock_cases_with_dupe):
    result = evaluate("password_reset", mock_cases_with_dupe)
    assert len(result.duplicates) == 1
    ids_flagged = {result.duplicates[0][0], result.duplicates[0][1]}
    assert ids_flagged == {"tc-1", "tc-2"}


def test_no_duplicates_when_titles_are_distinct():
    distinct_cases = [
        {"id": "tc-1", "title": "Valid reset flow", "category": "happy_path", "steps": [], "expected_result": ""},
        {"id": "tc-2", "title": "Token reuse rejected", "category": "auth_permission", "steps": [], "expected_result": ""},
    ]
    result = evaluate("password_reset", distinct_cases)
    assert result.duplicates == []


def test_traceability_flags_off_topic_case(mock_cases_off_topic):
    result = evaluate("password_reset", mock_cases_off_topic)
    assert "tc-4" in result.traceability_flags
    assert "tc-1" not in result.traceability_flags


def test_traceability_passes_when_all_cases_reference_requirement():
    on_topic_cases = [
        {"id": "tc-1", "title": "Password reset link expires", "category": "boundary",
         "steps": ["Request password reset"], "expected_result": "Reset link expires"},
    ]
    result = evaluate("password_reset", on_topic_cases)
    assert result.traceability_flags == []
