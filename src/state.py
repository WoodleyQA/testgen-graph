from typing import TypedDict, Literal

Category = Literal["happy_path", "negative", "boundary", "auth_permission"]


class TestCase(TypedDict):
    id: str
    title: str
    category: Category
    steps: list[str]
    expected_result: str


class PlaywrightSkeleton(TypedDict):
    test_case_id: str
    code: str


class GraphState(TypedDict):
    requirement: str
    generated_cases: list[TestCase]
    skeletons: list[PlaywrightSkeleton]
