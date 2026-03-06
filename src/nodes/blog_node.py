from src.states.blogstate import BlogState
from langchain_core.messages import HumanMessage
from src.states.blogstate import Blog, BlogOutline, BlogSection, TitleMeta, TakeawayCTA

class BlogNode:
    """
    A class to represent the blog node in the graph.
    """
    def __init__(self, llm):
        self.llm = llm
    
    def outline_generation(self, state: BlogState):
        """Generate a structured outline from the topic."""
        structured_llm = self.llm.with_structured_output(BlogOutline)
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
        outline = structured_llm.invoke(system_message)
        return {"outline": outline}

    def title_creation(self, state: BlogState):
        """
        Generate SEO title and meta description from topic + outline.
        """
        structured_llm = self.llm.with_structured_output(TitleMeta)
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
            sections = state["outline"].sections
        )
        response = structured_llm.invoke(system_message)
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
            sections = state["outline"].sections
        )
        response = self.llm.invoke(system_message)
        blog.introduction = response.content.strip()

        return {"blog": blog}

    def section_generation(self, state: BlogState):
        """
        Generate each blog section independently using the outline.
        """
        blog = state["blog"]
        outline = state["outline"]
        sections = []

        for idx, heading in enumerate(outline.sections):
            key_points = outline.key_points[idx]
            prompt = """
                        You are an expert blog writer.

                        Blog Title: {title}
                        Section Heading: {heading}

                        Key Points to cover:
                        {key_points}

                        Write a detailed, high-quality markdown section.
                        Include examples were relevant.
                        DO NOT include the section heading in your response - just the content.
                     """
            system_message = prompt.format(
                title = blog.title,
                heading = heading,
                key_points = key_points
            )
            response = self.llm.invoke(system_message)
            section = BlogSection(
                heading = heading,
                content = response.content.strip()
            )
            sections.append(section)
        
        blog.sections = sections
        return {"blog": blog}

    def takeaways_cta(self, state: BlogState):
        """
            Generate Key takeaways and call-to-action from the full blog.
        """
        blog = state["blog"]
        structured_llm = self.llm.with_structured_output(TakeawayCTA)

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
        response = structured_llm.invoke(system_message)
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

        response = self.llm.invoke(
            [HumanMessage(content=translation_prompt)]
        )

        return {
            "translated_content": response.content,
            "blog": blog
        }