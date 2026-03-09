from src.states.blogstate import BlogState
from langchain_core.messages import HumanMessage
from src.states.blogstate import Blog, BlogOutline, BlogSection, TitleMeta, TakeawayCTA, ReviewResult
from src.utils.retry import retry_llm_call

class BlogNode:
    """
    A class to represent the blog node in the graph.
    """
    def __init__(self, fast_llm, quality_llm):
        self.fast_llm = fast_llm
        self.quality_llm = quality_llm
    
    def outline_generation(self, state: BlogState):
        """Generate a structured outline from the topic."""
        structured_llm = self.fast_llm.with_structured_output(BlogOutline)
        prompt = """
                    You are a senior content strategist.
                    Topic: {topic}
                    Generate:
                    - 3-5 strong H2 section headings
                    - 3-4 key bullet points per section
                    Make it logical and reader-focused.
                """
        system_message = prompt.format(
            topic=state["topic"]
        )
        outline = retry_llm_call(lambda: structured_llm.invoke(system_message))
        return {"outline": outline}

    def title_creation(self, state: BlogState):
        """
        Generate SEO title and meta description from topic + outline.
        """
        structured_llm = self.fast_llm.with_structured_output(TitleMeta)
        prompt = """
                    You are an SEO specialist.
                    Topic: {topic}
                    Sections: {sections}
                    Generate:
                    - SEO optimized title
                    - Meta description under 155 characters
                 """
        system_message = prompt.format(
            topic = state["topic"],
            sections = [s.heading for s in state["outline"].sections]
        )
        response = retry_llm_call(lambda: structured_llm.invoke(system_message))
        blog = Blog(
            title = response.title,
            meta_description = response.meta_description,
            introduction = "",
            sections = [],
            key_takeaways = [],
            call_to_action = ""
        )

        return {"blog": blog}
            
    def intro_generation(self, state: BlogState):
        """
        Write and engaging introduction with a hook
        """
        blog = state["blog"]
        prompt = """
                    You are a professional copywriter.
                    Title: {title}
                    Sections: {sections}
                    Write an engaging introduction.
                    Open with a strong hook (pain point, stat, bold claim).
                 """
        system_message = prompt.format(
            title = blog.title,
            sections = [s.heading for s in state["outline"].sections]
        )
        response = retry_llm_call(lambda: self.quality_llm.invoke(system_message))
        blog.introduction = response.content.strip()

        return {"blog": blog}

    def section_generation(self, state: BlogState):
        """
        Generate each blog section independently using the outline.
        """
        blog = state["blog"]
        outline = state["outline"]
        review_feedback = state.get("review_feedback", "")
        sections = []

        feedback_context = ""
        if review_feedback:
            feedback_context = f"Previous review feedback: {review_feedback}. Address these issues in your writing."

        for section_data in outline.sections:
            heading = section_data.heading
            key_points = section_data.key_points

            if review_feedback:
                # REWRITE prompt - focused on addressing specific feedback.
                prompt = """
                            You are an expert blog writer revising a section.

                            Blog Title: {title}
                            Section Heading: {heading}
                            Key Points: {key_points}

                            Previous reviewer feedback:
                            {review_feedback}

                            Rewrite this section addressing the feedback above.
                            Maintain depth and quality. DO NOT include the heading.
                         """
                system_message = prompt.format(
                    title = blog.title,
                    heading = heading,
                    key_points = key_points,
                    review_feedback = review_feedback
                )
            else:
                # First-GENERATION prompt - focused on creating great content
                prompt = """
                            You are an expert blog writer.

                            Blog Title: {title}
                            Section Heading: {heading}
                            Key Points: {key_points}

                            Write a detailed, high-quality markdown section.
                            Include examples were relevant.
                            DO NOT include the section heading.
                        """
                system_message = prompt.format(
                    title = blog.title,
                    heading = heading,
                    key_points = key_points
                )
            response = retry_llm_call(lambda: self.quality_llm.invoke(system_message))
            section = BlogSection(
                heading = heading,
                content = response.content.strip()
            )
            sections.append(section)
        
        blog.sections = sections
        return {"blog": blog}
    
    def review(self, state: BlogState):
        blog = state["blog"]
        review_count = state.get("review_count", 0)

        structured_llm = self.quality_llm.with_structured_output(ReviewResult)

        full_content = "\n\n".join(
            [blog.introduction] +
            [f"## {section.heading}\n{section.content}" for section in blog.sections]
        )

        prompt = """
                    You are a blog editor.
                    Score this blog from 1-10 on coherence, depth, engagement, structure, completeness.

                    Blog content:
                    {full_content}
                 """
        system_message = prompt.format(
            full_content = full_content
        )
        result = retry_llm_call(lambda: structured_llm.invoke(system_message))
        return  {
            "review_feedback": result.feedback,
            "review_count": review_count + 1,
            "review_score": result.review_score
        }
    
    def review_decision(self, state):
        if state.get("review_count", 0) >= 2:
            return "pass"
        if state.get("review_score", 10) >= 7:
            return "pass"
        return "rewrite"

    def takeaways_cta(self, state: BlogState):
        """
            Generate Key takeaways and call-to-action from the full blog.
        """
        blog = state["blog"]
        structured_llm = self.quality_llm.with_structured_output(TakeawayCTA)

        full_content = "\n\n".join(
            [blog.introduction] +
            [f"## {section.heading}\n{section.content}" for section in blog.sections]
        )

        prompt = """
                    You are a senior editor.

                    Based on the blog content below:

                    {full_content}

                    Generate:
                    - 3-5 concise key takeaways (actionable bullet points)
                    - A strong closing call-to-action paragraph
                """
        system_message = prompt.format(
            full_content = full_content
        )
        response = retry_llm_call(lambda: structured_llm.invoke(system_message))
        blog.key_takeaways = response.key_takeaways
        blog.call_to_action = response.call_to_action
        return {"blog": blog}
    
    def translation(self,state:BlogState):
        """Translate the full blog content section-by-section."""
        blog = state["blog"]
        target_lang = state.get("current_language", "")

        if not target_lang:
            return {"blog": blog}

        full_blog_markdown = f"# {blog.title}\n\n"
        full_blog_markdown += f"{blog.introduction}\n\n"
        for section in blog.sections:
            full_blog_markdown += f"## {section.heading}\n{section.content}\n\n"
        full_blog_markdown += "## Key Takeaways\n"
        full_blog_markdown += "\n".join(f"- {t}" for t in blog.key_takeaways)
        full_blog_markdown += f"\n\n{blog.call_to_action}"

        translation_prompt = f"""
                                Translate the following content into {target_lang}.
                                Maintain tone, structure, and markdown formatting.

                                {full_blog_markdown}
                            """

        response = retry_llm_call(lambda: self.quality_llm.invoke(
                [HumanMessage(content=translation_prompt)]
            )
        )
        return {
            "translated_content": response.content,
            "blog": blog
        }