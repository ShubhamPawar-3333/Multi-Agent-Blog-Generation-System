from langgraph.graph import StateGraph, START, END
from src.llms.groqllm import GroqLLM
from src.states.blogstate import BlogState
from src.nodes.blog_node import BlogNode

class GraphBuilder:
    def __init__(self, llm):
        self.llm = llm
        self.graph=StateGraph(BlogState)

    def build_topic_graph(self):
        """
        Build a graph to generate blogs based on topic
        """
        self.blog_node_obj = BlogNode(self.llm)

        # Nodes
        self.graph.add_node("outline_generation", self.blog_node_obj.outline_generation)
        self.graph.add_node("title_creation",self.blog_node_obj.title_creation)
        self.graph.add_node("intro_generation",self.blog_node_obj.intro_generation)
        self.graph.add_node("section_generation", self.blog_node_obj.section_generation)
        self.graph.add_node("takeaways_cta", self.blog_node_obj.takeaways_cta)

        # Edges
        self.graph.add_edge(START, "outline_generation")
        self.graph.add_edge("outline_generation", "title_creation")
        self.graph.add_edge("title_creation", "intro_generation")
        self.graph.add_edge("intro_generation", "section_generation")
        self.graph.add_edge("section_generation", "takeaways_cta")
        self.graph.add_edge("takeaways_cta", END)

        return self.graph

    def build_language_graph(self):
        """
        Build a graph to generate blogs based on language
        """
        self.blog_node_obj = BlogNode(self.llm)

        # Nodes
        self.graph.add_node("outline_generation", self.blog_node_obj.outline_generation)
        self.graph.add_node("title_creation",self.blog_node_obj.title_creation)
        self.graph.add_node("intro_generation",self.blog_node_obj.intro_generation)
        self.graph.add_node("section_generation", self.blog_node_obj.section_generation)
        self.graph.add_node("takeaways_cta", self.blog_node_obj.takeaways_cta)
        self.graph.add_node("translation", self.blog_node_obj.translation)

        # Edges
        self.graph.add_edge(START, "outline_generation")
        self.graph.add_edge("outline_generation", "title_creation")
        self.graph.add_edge("title_creation", "intro_generation")
        self.graph.add_edge("intro_generation", "section_generation")
        self.graph.add_edge("section_generation", "takeaways_cta")
        self.graph.add_edge("takeaways_cta", "translation")
        self.graph.add_edge("translation", END)

        return self.graph

    def setup_graph(self, usecase):
        """
        Setup graph based on usecase
        """
        if usecase == "topic":
            graph = self.build_topic_graph()
        elif usecase == "language":
            graph = self.build_language_graph()
        return graph.compile()
    
## Below code is for the langsmith langgraph studio
llm = GroqLLM().get_llm()

# Get the graph
graph_builder = GraphBuilder(llm)
graph = graph_builder.build_language_graph().compile()