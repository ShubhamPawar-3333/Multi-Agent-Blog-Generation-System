from src.states.blogstate import BlogState
from langchain_core.messages import HumanMessage,SystemMessage
from src.states.blogstate import Blog

class BlogNode:
    """
    A class to represent the blog node in the graph.
    """
    def __init__(self, llm):
        self.llm = llm

    def title_creation(self, state: BlogState):
        """
        Generate a title for the blog.
        """
        
        if "topic" in state and state["topic"]:
            prompt = """
                    You are a professional blog content writer. Use Markdown for formatting.
                    Generate a catchy and engaging title for a blog post based on the following topic:
                    Topic: {topic}
                    
                    This title should be creative and SEO friendly.
                    """
            system_message = prompt.format(
                topic=state["topic"]
            )
            response = self.llm.invoke(system_message)
            return {"blog": {"title": response.content}}
            
            

    def content_generation(self, state: BlogState):
        """
        Generate content for the blog.
        """
        if "topic" in state and state["topic"]:
            prompt = """
                    You are a professional blog content writer. Use Markdown for formatting.
                    Generate a detailed blog content with detailed breakdown for the folowing topic:
                    Topic: {topic}
                    """
            system_message = prompt.format(
                topic=state["topic"]
            )
            response = self.llm.invoke(system_message)
            return {"blog": {"title": state["blog"]["title"], "content": response.content}}
    
    def translation(self,state:BlogState):
        """
        Translate the content to the specified language.
        """
        translation_prompt="""
        Translate the following content into {current_language}.
        - Maintain the original tone, style, and formatting.
        - Adapt cultural references and idioms to be appropriate for {current_language}.

        ORIGINAL CONTENT:
        {blog_content}

        """
        print(state["current_language"])
        blog_content=state["blog"]["content"]
        messages=[
            HumanMessage(translation_prompt.format(current_language=state["current_language"], blog_content=blog_content))

        ]
        translation_response = self.llm.invoke(messages)
        return {"blog": {"title": state["blog"]["title"], "content": translation_response.content}}


    def route(self, state: BlogState):
        """
        Route the blog to the appropriate language node.
        """
        return {"current_language": state["current_language"]}

    def route_decision(self, state: BlogState):
        """
        Decide the route for the blog.
        """
        if state["current_language"] == "hindi":
            return "hindi"
        elif state["current_language"] == "french":
            return "french"
        else:
            return state["current_language"]