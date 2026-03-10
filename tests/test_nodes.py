from src.nodes.blog_node import BlogNode
from unittest.mock import MagicMock
from src.states.blogstate import BlogOutline, OutlineSection, TitleMeta, Blog, BlogSection, TakeawayCTA, ReviewResult

class TestReviewDecision:
    """Tests for review_decision routing logic."""

    def setup_method(self):
        # review_decision doesn't use LLM, so None is fine
        self.node = BlogNode(None, None)

    def test_passes_when_score_high(self):
        state = {"review_count": 0, "review_score": 8}
        assert self.node.review_decision(state) == "pass"

    def test_rewrites_when_score_low(self):
        state = {"review_count": 0, "review_score": 5}
        assert self.node.review_decision(state) == "rewrite"

    def test_passes_when_loop_cap_reached(self):
        state = {"review_count": 2, "review_score": 3}
        assert self.node.review_decision(state) == "pass"

    def test_passes_at_boundary_score_7(self):
        state = {"review_count": 0, "review_score": 7}
        assert self.node.review_decision(state) == "pass"

    def test_rewrites_at_score_6(self):
        state = {"review_count": 0, "review_score": 6}
        assert self.node.review_decision(state) == "rewrite"

    def test_defaults_to_pass_when_no_score(self):
        state = {}
        assert self.node.review_decision(state) == "pass"
    
class TestOutlineGeneration:
    """Tests for outline_generation node."""

    def setup_method(self):
        self.mock_fast = MagicMock()
        self.mock_quality = MagicMock()
        self.node = BlogNode(self.mock_fast, self.mock_quality)

    def test_returns_blog_outline(self):
        # Mock: llm.with_structured_output(BlogOutline).invoke() → returns fake outline
        mock_outline = BlogOutline(sections=[
            OutlineSection(heading="Section 1", key_points=["point1", "point2"]),
            OutlineSection(heading="Section 2", key_points=["point3", "point4"]),
            OutlineSection(heading="Section 3", key_points=["point5", "point6"]),
        ])
        self.mock_fast.with_structured_output.return_value.invoke.return_value = mock_outline
        state = {"topic": "Benefits of AI"}
        result = self.node.outline_generation(state)
        assert "outline" in result
        assert isinstance(result["outline"], BlogOutline)

    def test_outline_has_3_to_5_sections(self):
        mock_outline = BlogOutline(sections=[
            OutlineSection(heading="S1", key_points=["p1"]),
            OutlineSection(heading="S2", key_points=["p2"]),
            OutlineSection(heading="S3", key_points=["p3"]),
        ])
        self.mock_fast.with_structured_output.return_value.invoke.return_value = mock_outline
        state = {"topic": "Test topic"}
        result = self.node.outline_generation(state)
        assert 3 <= len(result["outline"].sections) <= 5

    def test_each_section_has_key_points(self):
        mock_outline = BlogOutline(sections=[
            OutlineSection(heading="S1", key_points=["p1", "p2"]),
            OutlineSection(heading="S2", key_points=["p3", "p4"]),
            OutlineSection(heading="S3", key_points=["p5", "p6"]),
        ])
        self.mock_fast.with_structured_output.return_value.invoke.return_value = mock_outline
        state = {"topic": "Test topic"}
        result = self.node.outline_generation(state)
        for section in result["outline"].sections:
            assert len(section.key_points) > 0
    
class TestTitleCreation:
    """Tests for title_creation node."""
    def setup_method(self):
        self.mock_fast = MagicMock()
        self.mock_quality = MagicMock()
        self.node = BlogNode(self.mock_fast, self.mock_quality)
    def test_returns_blog_with_title(self):
        mock_title = TitleMeta(
            title="10 Benefits of Morning Walks",
            meta_description="Discover the benefits of morning walks."
        )
        self.mock_fast.with_structured_output.return_value.invoke.return_value = mock_title
        state = {
            "topic": "Morning walks",
            "outline": BlogOutline(sections=[
                OutlineSection(heading="S1", key_points=["p1"]),
            ])
        }
        result = self.node.title_creation(state)
        assert "blog" in result
        assert result["blog"].title == "10 Benefits of Morning Walks"
        assert result["blog"].meta_description != ""
    def test_blog_starts_with_empty_sections(self):
        mock_title = TitleMeta(
            title="Test Title",
            meta_description="Test meta"
        )
        self.mock_fast.with_structured_output.return_value.invoke.return_value = mock_title
        state = {
            "topic": "Test",
            "outline": BlogOutline(sections=[
                OutlineSection(heading="S1", key_points=["p1"]),
            ])
        }
        result = self.node.title_creation(state)
        assert result["blog"].sections == []
        assert result["blog"].introduction == ""
class TestIntroGeneration:
    """Tests for intro_generation node."""
    def setup_method(self):
        self.mock_fast = MagicMock()
        self.mock_quality = MagicMock()
        self.node = BlogNode(self.mock_fast, self.mock_quality)
    def test_returns_blog_with_introduction(self):
        # Mock the quality LLM (intro uses quality model)
        mock_response = MagicMock()
        mock_response.content = "AI is transforming healthcare at an unprecedented pace."
        self.mock_quality.invoke.return_value = mock_response
        state = {
            "blog": Blog(
                title="AI in Healthcare",
                meta_description="Test",
                introduction="",
                sections=[],
                key_takeaways=[],
                call_to_action=""
            ),
            "outline": BlogOutline(sections=[
                OutlineSection(heading="S1", key_points=["p1"]),
            ])
        }
        result = self.node.intro_generation(state)
        assert result["blog"].introduction != ""
        assert "AI" in result["blog"].introduction

class TestSectionGeneration:
    """Tests for section_generation node."""

    def setup_method(self):
        self.mock_fast = MagicMock()
        self.mock_quality = MagicMock()
        self.node = BlogNode(self.mock_fast, self.mock_quality)

    def test_generates_correct_number_of_sections(self):
        # Mock: quality_llm.invoke() returns content for each section
        mock_response = MagicMock()
        mock_response.content = "This is detailed section content about the topic."
        self.mock_quality.invoke.return_value = mock_response

        outline = BlogOutline(sections=[
            OutlineSection(heading="Section A", key_points=["p1", "p2"]),
            OutlineSection(heading="Section B", key_points=["p3", "p4"]),
            OutlineSection(heading="Section C", key_points=["p5", "p6"]),
        ])
        state = {
            "blog": Blog(
                title="Test", meta_description="Test",
                introduction="Intro", sections=[],
                key_takeaways=[], call_to_action=""
            ),
            "outline": outline
        }
        result = self.node.section_generation(state)

        assert len(result["blog"].sections) == 3

    def test_each_section_has_heading_and_content(self):
        mock_response = MagicMock()
        mock_response.content = "Detailed content here."
        self.mock_quality.invoke.return_value = mock_response

        outline = BlogOutline(sections=[
            OutlineSection(heading="My Heading", key_points=["p1"]),
        ])
        state = {
            "blog": Blog(
                title="Test", meta_description="Test",
                introduction="Intro", sections=[],
                key_takeaways=[], call_to_action=""
            ),
            "outline": outline
        }
        result = self.node.section_generation(state)

        section = result["blog"].sections[0]
        assert section.heading == "My Heading"
        assert section.content != ""

    def test_uses_review_feedback_on_rewrite(self):
        mock_response = MagicMock()
        mock_response.content = "Rewritten content addressing feedback."
        self.mock_quality.invoke.return_value = mock_response

        outline = BlogOutline(sections=[
            OutlineSection(heading="S1", key_points=["p1"]),
        ])
        state = {
            "blog": Blog(
                title="Test", meta_description="Test",
                introduction="Intro", sections=[],
                key_takeaways=[], call_to_action=""
            ),
            "outline": outline,
            "review_feedback": "Sections lack depth and examples"
        }
        result = self.node.section_generation(state)

        # Verify the LLM was called (meaning the rewrite path worked)
        assert self.mock_quality.invoke.called
        assert len(result["blog"].sections) == 1


class TestTakeawaysCta:
    """Tests for takeaways_cta node."""

    def setup_method(self):
        self.mock_fast = MagicMock()
        self.mock_quality = MagicMock()
        self.node = BlogNode(self.mock_fast, self.mock_quality)

    def test_returns_takeaways_and_cta(self):
        mock_result = TakeawayCTA(
            key_takeaways=["Takeaway 1", "Takeaway 2", "Takeaway 3"],
            call_to_action="Start your journey today!"
        )
        self.mock_quality.with_structured_output.return_value.invoke.return_value = mock_result

        state = {
            "blog": Blog(
                title="Test", meta_description="Test",
                introduction="Intro paragraph.",
                sections=[BlogSection(heading="S1", content="Content")],
                key_takeaways=[], call_to_action=""
            )
        }
        result = self.node.takeaways_cta(state)

        assert len(result["blog"].key_takeaways) == 3
        assert result["blog"].call_to_action != ""

    def test_takeaways_count_between_3_and_5(self):
        mock_result = TakeawayCTA(
            key_takeaways=["T1", "T2", "T3", "T4"],
            call_to_action="Act now!"
        )
        self.mock_quality.with_structured_output.return_value.invoke.return_value = mock_result

        state = {
            "blog": Blog(
                title="Test", meta_description="Test",
                introduction="Intro.",
                sections=[BlogSection(heading="S1", content="C1")],
                key_takeaways=[], call_to_action=""
            )
        }
        result = self.node.takeaways_cta(state)

        assert 3 <= len(result["blog"].key_takeaways) <= 5

class TestReview:
    """Tests for review node."""

    def setup_method(self):
        self.mock_fast = MagicMock()
        self.mock_quality = MagicMock()
        self.node = BlogNode(self.mock_fast, self.mock_quality)

    def test_returns_score_and_feedback(self):
        mock_result = ReviewResult(
            review_score=8,
            feedback="Well structured blog with good depth."
        )
        self.mock_quality.with_structured_output.return_value.invoke.return_value = mock_result

        state = {
            "blog": Blog(
                title="Test", meta_description="Test",
                introduction="Great intro.",
                sections=[BlogSection(heading="S1", content="Content here")],
                key_takeaways=["T1"], call_to_action="Act now"
            ),
            "review_count": 0
        }
        result = self.node.review(state)

        assert result["review_score"] == 8
        assert result["review_feedback"] != ""
        assert result["review_count"] == 1

    def test_increments_review_count(self):
        mock_result = ReviewResult(review_score=5, feedback="Needs work.")
        self.mock_quality.with_structured_output.return_value.invoke.return_value = mock_result

        state = {
            "blog": Blog(
                title="T", meta_description="T", introduction="I",
                sections=[BlogSection(heading="S", content="C")],
                key_takeaways=["T"], call_to_action="A"
            ),
            "review_count": 1
        }
        result = self.node.review(state)

        assert result["review_count"] == 2


class TestTranslation:
    """Tests for translation node."""

    def setup_method(self):
        self.mock_fast = MagicMock()
        self.mock_quality = MagicMock()
        self.node = BlogNode(self.mock_fast, self.mock_quality)

    def test_translates_blog_content(self):
        mock_response = MagicMock()
        mock_response.content = "# Translated title\n\nTranslated content in Hindi"
        self.mock_quality.invoke.return_value = mock_response

        state = {
            "blog": Blog(
                title="Test Title", meta_description="Meta",
                introduction="English intro.",
                sections=[BlogSection(heading="S1", content="English content")],
                key_takeaways=["Takeaway 1"], call_to_action="Subscribe!"
            ),
            "current_language": "hindi"
        }
        result = self.node.translation(state)

        assert "translated_content" in result
        assert result["translated_content"] != ""

    def test_skips_translation_when_no_language(self):
        state = {
            "blog": Blog(
                title="Test", meta_description="M",
                introduction="Intro.", sections=[],
                key_takeaways=[], call_to_action=""
            ),
            "current_language": ""
        }
        result = self.node.translation(state)

        # Should return blog unchanged, no translated_content
        assert "blog" in result
        assert "translated_content" not in result