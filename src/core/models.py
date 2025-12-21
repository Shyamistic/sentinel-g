from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class BrowsingEvent(BaseModel):
    """User browsing history event."""
    product_id: str
    category: str
    dwell_time_ms: int


class RecommendationRequest(BaseModel):
    """Request for product recommendations."""
    user_id: str
    current_cart_value: float
    user_segment: str = "standard"
    browsing_history: List[BrowsingEvent] = []


class ProductRecommendation(BaseModel):
    """Individual product recommendation."""
    product_id: str
    product_name: str
    category: str
    confidence: float
    predicted_ctr: float
    reason: str


class RecommendationResponse(BaseModel):
    """Response with recommendations and telemetry."""
    request_id: str
    recommendations: List[ProductRecommendation]
    recommendation_diversity: float
    confidence_score: float
    failure_class: Optional[str] = None
    failure_score: Optional[float] = None
    latency_ms: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    service: str
    version: str
    uptime_seconds: float = 0.0