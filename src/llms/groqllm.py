from langchain_groq import ChatGroq
from dotenv import load_dotenv
import os


class GroqLLM:
    def __init__(self, api_key=None):
        load_dotenv()
        self.groq_api_key = api_key or os.getenv("GROQ_API_KEY")

    def get_llm(self, model_name: str):
        try:
            llm = ChatGroq(
                api_key=self.groq_api_key,
                model_name=model_name
            )
            return llm
        except Exception as e:
            raise ValueError(f"Error occured with exception: {e}")
    
    def fast_llm(self):
        return self.get_llm("llama-3.1-8b-instant")

    def quality_llm(self):
        return self.get_llm("llama-3.3-70b-versatile")