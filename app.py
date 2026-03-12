import os
import json
import time
import uvicorn

from pydantic import BaseModel
from dotenv import load_dotenv
from fastapi import FastAPI, Request, HTTPException, Header
from fastapi.responses import JSONResponse, StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from src.llms.groqllm import GroqLLM
from src.graphs.graph_builder import GraphBuilder
from src.utils.logger import get_logger

class BlogRequest(BaseModel):
    topic: str
    language: str = ""
    api_key: str # Required - user provides their Groq API Key

load_dotenv()
os.environ["LANGSMITH_API_KEY"] = os.getenv("LANGCHAIN_API_KEY")

# LLMs are created per-prequest with user's API key

app = FastAPI()

@app.get("/")
async def serve_frontend():
    return FileResponse("static/index.html")

# Server static frontend files
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"error": "Blog generation failed", "detail":str(exc)}
    )

logger = get_logger("app")

## API endpoints
@app.post("/blogs")
async def create_blogs(request:BlogRequest):
    logger.info("Blog request received: topic:'%s', language='%s'", request.topic, request.language)
    if not request.topic.strip():
        raise HTTPException(status_code=400, detail="Topic is required")
    
    if not request.api_key.strip():
        raise HTTPException(status_code=400, detail="API key is required")

    # Create LLMs with user's key
    groqllm=GroqLLM(api_key=request.api_key)
    fast_llm = groqllm.fast_llm()
    quality_llm = groqllm.quality_llm()

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

@app.post("/blogs/stream")
async def stream_blog(request: BlogRequest):
    logger.info("Stream request: topic='%s', language='%s'", request.topic, request.language)

    if not request.topic.strip():
        raise HTTPException(status_code=400, detail="Topic is required")
    
    if not request.api_key.strip():
        raise HTTPException(status_code=400, detail="API key is required")
    
    def generate():
        groqllm = GroqLLM(api_key=request.api_key)
        fast_llm = groqllm.fast_llm()
        quality_llm = groqllm.quality_llm()

        graph_builder = GraphBuilder(fast_llm, quality_llm)

        if request.language:
            graph = graph_builder.setup_graph(usecase="language")
            input_data = {"topic": request.topic, "current_language": request.language.lower()}
        else:
            graph = graph_builder.setup_graph(usecase="topic")
            input_data = {"topic": request.topic}
        
        # Stream node-by-node using LangGraph's stream()
        for event in graph.stream(input_data):
            # event is a dict like {"outline_generation":{"outline": ...}}
            node_name = list(event.keys())[0]
            node_output = event[node_name]

            # Send code completion event
            sse_data = {
                "node": node_name,
                "timestamp": time.time(),
            }

            # Include blog data if available
            if "blog" in node_output:
                blog = node_output["blog"]
                sse_data["blog"] = {
                    "title": blog.title,
                    "meta_description": blog.meta_description,
                    "introduction": blog.introduction,
                    "sections": [{"heading": s.heading, "content": s.content} for s in blog.sections],
                    "key_takeaways": blog.key_takeaways,
                    "call_to_action": blog.call_to_action,
                }
            
            # Include review data if available
            if "review_score" in node_output:
                sse_data["review_score"] = node_output["review_score"]
                sse_data["review_feedback"] = node_output["review_feedback"]
                sse_data["review_count"] = node_output.get("review_count", 0)
            
            # Include translation if available
            if "translated_content" in node_output:
                sse_data["translated_content"] = node_output["translated_content"]
            
            yield f"data: {json.dumps(sse_data)}\n\n"
        
        # Send completion event
        yield f"data: {json.dumps({'node': 'complete'})}\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
