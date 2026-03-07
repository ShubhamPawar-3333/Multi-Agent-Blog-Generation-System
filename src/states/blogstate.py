from typing import TypedDict, List
from pydantic import BaseModel, Field

class BlogSection(BaseModel):
    """Represents a single H2 section in the blog."""
    heading: str = Field(description="H2 heading of this section")
    content: str = Field(description="Detailed markdown content of this section") 

class OutlineSection(BaseModel):
    """A single section in the blog outline."""
    heading: str = Field(description="H2 section heading")
    key_points: List[str] = Field(description="3-4 key points to cover in this section")

class BlogOutline(BaseModel):
    """Pre-writing plan generated before content creation."""
    sections: List[OutlineSection] = Field(description="3-5 planned blog sections with key points")

class TitleMeta(BaseModel):
    """Structured output model for the title generation node."""
    title: str = Field(description="SEO friendly, engaging blog title")
    meta_description: str = Field(max_length=155, description="SEO meta description (max 155 chars)")

class ReviewResult(BaseModel):
    review_score: int = Field(description="Quality score 1-10")
    feedback: str = Field(description="Specific improvement suggestions")

class TakeawayCTA(BaseModel):
    """Structured output model for takeaways and CTA generation node."""
    key_takeaways: List[str] = Field(description="3-5 concise, actionable takeaways")
    call_to_action: str = Field(description="Closing CTA paragraph - tells reader wha to do next")

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
    review_score: int
    review_count: int
    review_feedback:str
    translated_content: str
    

    