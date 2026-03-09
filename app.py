import os
import uvicorn

from pydantic import BaseModel
from dotenv import load_dotenv
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from src.llms.groqllm import GroqLLM
from src.graphs.graph_builder import GraphBuilder

class BlogRequest(BaseModel):
    topic: str
    language: str = ""

load_dotenv()
os.environ["LANGSMITH_API_KEY"] = os.getenv("LANGCHAIN_API_KEY")

## Module - level LLM init (Once, not per request)
groqllm=GroqLLM()
fast_llm = groqllm.fast_llm()
quality_llm = groqllm.quality_llm()


app = FastAPI()

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"error": "Blog generation failed", "detail":str(exc)}
    )

## API endpoints
@app.post("/blogs")
async def create_blogs(request:BlogRequest):
    if not request.topic.strip():
        raise HTTPException(status_code=400, detail="Topic is required")
    
    ## get the graph
    graph_builder=GraphBuilder(fast_llm, quality_llm)
    
    if request.language:
        graph=graph_builder.setup_graph(usecase="language")
        state=graph.invoke({
            "topic":request.topic,
            "current_language":request.language.lower()
        })
    else:
        graph=graph_builder.setup_graph(usecase="topic")
        state=graph.invoke({"topic":request.topic})

    return {"data":state}

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
