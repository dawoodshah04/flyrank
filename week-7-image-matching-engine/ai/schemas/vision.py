"""Pydantic schemas for vision model responses."""

from pydantic import BaseModel, Field


class ImageAnalysis(BaseModel):
    """Structured output from the vision model for a single image."""

    subject: str = Field(..., description="Primary subject of the image (e.g. 'red fox')")
    category: str = Field(..., description="Broad category (e.g. 'fox', 'wolf', 'mountain')")
    caption: str = Field(..., description="One-sentence description of the image")
    attributes: list[str] = Field(
        default_factory=list,
        description="3-7 keyword attributes describing the image",
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Model's confidence in its analysis (0.0 to 1.0)",
    )
