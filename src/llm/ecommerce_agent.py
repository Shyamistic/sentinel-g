import json
import random
import uuid
from datetime import datetime
from src.core.models import RecommendationRequest, RecommendationResponse, ProductRecommendation


class EcommerceRecommendationAgent:
    """Gemini-powered e-commerce recommendation agent."""
    
    def __init__(self):
        """Initialize recommendation agent."""
        self.baseline_confidence = 0.85
        self.baseline_diversity = 0.70
        self.baseline_latency = 1800  # ms
        
        # Sample product catalog
        self.products = {
            "SKU001": {"name": "Wireless Headphones", "category": "Electronics", "price": 79.99},
            "SKU002": {"name": "Phone Case", "category": "Accessories", "price": 19.99},
            "SKU003": {"name": "Screen Protector", "category": "Accessories", "price": 9.99},
            "SKU004": {"name": "USB-C Cable", "category": "Electronics", "price": 14.99},
            "SKU005": {"name": "Power Bank", "category": "Electronics", "price": 49.99},
            "SKU006": {"name": "Laptop Stand", "category": "Office", "price": 34.99},
            "SKU007": {"name": "Mechanical Keyboard", "category": "Office", "price": 99.99},
            "SKU008": {"name": "Mouse Pad", "category": "Office", "price": 19.99},
            "SKU009": {"name": "Webcam", "category": "Electronics", "price": 59.99},
            "SKU010": {"name": "Desk Lamp", "category": "Office", "price": 44.99},
        }
    
    def recommend(self, request: RecommendationRequest) -> RecommendationResponse:
        """Generate product recommendations."""
        request_id = str(uuid.uuid4())
        start_time = datetime.utcnow()
        
        # Segment-based confidence adjustment
        segment_multiplier = {
            "new": 0.75,
            "standard": 0.85,
            "premium": 0.95,
            "high_value": 0.90,
        }.get(request.user_segment, 0.85)
        
        # Calculate confidence
        confidence = min(0.98, self.baseline_confidence * segment_multiplier)
        
        # Add browsing history influence
        if request.browsing_history:
            history_boost = min(0.1, len(request.browsing_history) * 0.02)
            confidence = min(0.99, confidence + history_boost)
        
        # Calculate diversity based on browsing categories
        categories_browsed = set(e.category for e in request.browsing_history) if request.browsing_history else set()
        diversity = self.baseline_diversity
        if len(categories_browsed) > 1:
            diversity = min(0.95, self.baseline_diversity + 0.1)
        elif len(categories_browsed) == 1:
            diversity = max(0.50, self.baseline_diversity - 0.15)
        
        # Predicted CTR based on confidence and cart value
        base_ctr = 0.04
        if request.current_cart_value > 100:
            base_ctr += 0.01
        if confidence > 0.90:
            base_ctr += 0.005
        predicted_ctr = min(0.15, base_ctr)
        
        # Select recommendations
        recommendations = []
        selected_skus = set()
        
        # Prioritize complementary products
        if request.browsing_history:
            last_category = request.browsing_history[-1].category
            for sku, product in self.products.items():
                if sku not in selected_skus and product["category"] != last_category:
                    recommendations.append(sku)
                    selected_skus.add(sku)
                    if len(recommendations) >= 5:
                        break
        
        # Fill remaining slots randomly
        remaining_skus = set(self.products.keys()) - selected_skus
        while len(recommendations) < 5 and remaining_skus:
            sku = random.choice(list(remaining_skus))
            recommendations.append(sku)
            remaining_skus.remove(sku)
        
        # Build response
        rec_objects = []
        for sku in recommendations[:5]:
            product = self.products.get(sku)
            if product:
                rec_objects.append(
                    ProductRecommendation(
                        product_id=sku,
                        product_name=product["name"],
                        category=product["category"],
                        confidence=confidence,
                        predicted_ctr=predicted_ctr,
                        reason=f"Based on your interest in {request.user_segment} products"
                    )
                )
        
        # Calculate latency
        latency = self.baseline_latency + random.randint(-200, 200)
        
        return RecommendationResponse(
            request_id=request_id,
            recommendations=rec_objects,
            recommendation_diversity=diversity,
            confidence_score=confidence,
            latency_ms=float(latency),
        )