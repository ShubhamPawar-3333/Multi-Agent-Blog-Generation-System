from typing import TypedDict, List
from pydantic import BaseModel, Field

class BlogSection(BaseModel):
    """Represents a single H2 section in the blog."""
    heading: str = Field(description="H2 heading of this section")
    content: str = Field(description="Detailed markdown content od this section") 

class BlogOutline(BaseModel):
    """Pre-writing plan generated before content creation."""
    sections: List[str] = Field(description="Planned section headings (3-5)")
    key_points: List[List[str]] = Field(description="Key points to cover per section")

class Blog(BaseModel):
    """Complete structured blog article."""
    title: str = Field(description="SEO friendly, engaging blog title")
    meta_description: str = Field(max_length=155, description="SEO meta description (max 155 chars)")
    introduction: str = Field(description="Hook paragraph - opens with pain point, stat, or bold claim")
    sections: List[BlogSection] = Field(description="3-5 detailed body section")
    key_takeaways: List[str] = Field(description="3-5 concise, actionable takeaways")
    call_to_action: str = Field(description="Closing CTA paragraph - tells reader wha to do next")

class BlogState(TypedDict):
    """LangGraph pipeline state - built incrementally across nodes."""
    topic: str
    outline: BlogOutline
    blog: Blog
    current_language: str
    review_count: int
    review_feedback:str
    

    