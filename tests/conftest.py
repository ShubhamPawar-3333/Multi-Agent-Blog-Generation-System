import pytest
from unittest.mock import MagicMock
from src.states.blogstate import BlogOutline, OutlineSection, Blog, BlogSection

@pytest.fixture
def mock_fast_llm():
    return MagicMock()

@pytest.fixture
def mock_quality_llm():
    return MagicMock()

@pytest.fixture
def simple_outline():
    return BlogOutline(
        sections = [
            OutlineSection(
                heading = "Introduction to AI",
                key_points = [
                    "What is AI",
                    "History"
                ]
            ),
            OutlineSection(
                heading = "AI applications",
                key_points = [
                    "Healthcare",
                    "Education"
                ]
            ),
            OutlineSection(
                heading = "Future of AI",
                key_points = [
                    "Trends",
                    "Challenges"
                ]
            )
        ]
    )

@pytest.fixture
def sample_blog():
    return Blog(
        title = "Test Blog Title",
        meta_description = "Test meta",
        introduction = "Test intro pragraph.",
        sections = [
            BlogSection(
                heading = "Section 1",
                content = "Content 1"
            ),
            BlogSection(
                heading = "Section 2",
                content = "Content 2"
            )
        ],
        key_takeaways = [
            "Takeaway 1",
            "Takeaway 2"
        ],
        call_to_action = "Subscribe now!"
    )