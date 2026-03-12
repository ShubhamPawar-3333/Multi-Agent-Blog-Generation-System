from unittest.mock import patch, MagicMock
from src.graphs.graph_builder import GraphBuilder
from src.nodes.blog_node import BlogNode
from src.states.blogstate import (
    BlogOutline, OutlineSection, TitleMeta, TakeawayCTA,
    ReviewResult, BlogSection, Blog
)


class TestTopicPipeline:
    """Integration tests for the full topic pipeline."""

    def test_full_topic_pipeline_returns_blog(self):
        """Verify the graph wiring: outline → title → intro → sections → review → takeaways → END."""
        sample_outline = BlogOutline(sections=[
            OutlineSection(heading="S1", key_points=["p1"]),
            OutlineSection(heading="S2", key_points=["p2"]),
        ])
        sample_blog_empty = Blog(
            title="Test Blog", meta_description="Test meta",
            introduction="", sections=[],
            key_takeaways=[], call_to_action=""
        )
        sample_blog_with_intro = Blog(
            title="Test Blog", meta_description="Test meta",
            introduction="Great intro.", sections=[],
            key_takeaways=[], call_to_action=""
        )
        sample_blog_with_sections = Blog(
            title="Test Blog", meta_description="Test meta",
            introduction="Great intro.",
            sections=[
                BlogSection(heading="S1", content="Content 1"),
                BlogSection(heading="S2", content="Content 2"),
            ],
            key_takeaways=[], call_to_action=""
        )
        sample_blog_complete = Blog(
            title="Test Blog", meta_description="Test meta",
            introduction="Great intro.",
            sections=[
                BlogSection(heading="S1", content="Content 1"),
                BlogSection(heading="S2", content="Content 2"),
            ],
            key_takeaways=["T1", "T2", "T3"],
            call_to_action="Subscribe now!"
        )

        # Patch node methods on the class — affects instances created within the patch
        with patch.object(BlogNode, 'outline_generation', return_value={"outline": sample_outline}), \
             patch.object(BlogNode, 'title_creation', return_value={"blog": sample_blog_empty}), \
             patch.object(BlogNode, 'intro_generation', return_value={"blog": sample_blog_with_intro}), \
             patch.object(BlogNode, 'section_generation', return_value={"blog": sample_blog_with_sections}), \
             patch.object(BlogNode, 'review', return_value={
                 "review_feedback": "Good quality.", "review_count": 1, "review_score": 9
             }), \
             patch.object(BlogNode, 'takeaways_cta', return_value={"blog": sample_blog_complete}):

            gb = GraphBuilder(MagicMock(), MagicMock())
            graph = gb.setup_graph("topic")
            result = graph.invoke({"topic": "Test Topic"})

            # Verify pipeline produced a complete blog
            assert "blog" in result
            assert result["blog"].title == "Test Blog"
            assert len(result["blog"].sections) == 2
            assert len(result["blog"].key_takeaways) == 3
            assert result["blog"].call_to_action != ""
            assert result["review_count"] == 1

    def test_review_loop_triggers_rewrite(self):
        """Verify the review loop sends back to section_generation when score < 7."""
        sample_outline = BlogOutline(sections=[
            OutlineSection(heading="S1", key_points=["p1"]),
        ])
        blog_v1 = Blog(
            title="Test", meta_description="M", introduction="I",
            sections=[BlogSection(heading="S1", content="Draft")],
            key_takeaways=[], call_to_action=""
        )
        blog_v2 = Blog(
            title="Test", meta_description="M", introduction="I",
            sections=[BlogSection(heading="S1", content="Improved")],
            key_takeaways=[], call_to_action=""
        )
        blog_final = Blog(
            title="Test", meta_description="M", introduction="I",
            sections=[BlogSection(heading="S1", content="Improved")],
            key_takeaways=["T1", "T2", "T3"], call_to_action="Act now!"
        )

        # review_count tracks how many times review was called
        review_call = {"count": 0}

        def mock_review(state):
            review_call["count"] += 1
            if review_call["count"] == 1:
                return {"review_feedback": "Needs depth", "review_count": 1, "review_score": 5}
            return {"review_feedback": "Good now", "review_count": 2, "review_score": 8}

        section_call = {"count": 0}

        def mock_sections(state):
            section_call["count"] += 1
            if section_call["count"] == 1:
                return {"blog": blog_v1}
            return {"blog": blog_v2}

        with patch.object(BlogNode, 'outline_generation', return_value={"outline": sample_outline}), \
             patch.object(BlogNode, 'title_creation', return_value={"blog": Blog(
                 title="Test", meta_description="M", introduction="", sections=[],
                 key_takeaways=[], call_to_action=""
             )}), \
             patch.object(BlogNode, 'intro_generation', return_value={"blog": Blog(
                 title="Test", meta_description="M", introduction="I", sections=[],
                 key_takeaways=[], call_to_action=""
             )}), \
             patch.object(BlogNode, 'section_generation', side_effect=mock_sections), \
             patch.object(BlogNode, 'review', side_effect=mock_review), \
             patch.object(BlogNode, 'takeaways_cta', return_value={"blog": blog_final}):

            gb = GraphBuilder(MagicMock(), MagicMock())
            graph = gb.setup_graph("topic")
            result = graph.invoke({"topic": "Test Topic"})

            # The review loop should have triggered a rewrite
            assert review_call["count"] == 2
            assert section_call["count"] == 2
            assert result["review_count"] == 2