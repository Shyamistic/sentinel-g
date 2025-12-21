"""
Unit tests for EcommerceRecommendationAgent
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from src.llm.ecommerce_agent import EcommerceRecommendationAgent
from src.core.models import RecommendationRequest, BrowsingEvent


def test_agent_initialization():
    """Test agent can be initialized."""
    agent = EcommerceRecommendationAgent()
    assert agent is not None
    print("✓ Agent initialized successfully")


def test_basic_recommendation():
    """Test basic recommendation generation."""
    agent = EcommerceRecommendationAgent()
    
    request = RecommendationRequest(
        user_id="test_user_123",
        current_cart_value=150.0,
        user_segment="premium",
        browsing_history=[
            BrowsingEvent(
                product_id="SKU001",
                category="Electronics",
                dwell_time_ms=5000
            ),
            BrowsingEvent(
                product_id="SKU002",
                category="Accessories",
                dwell_time_ms=3000
            ),
        ]
    )
    
    result = agent.recommend(request)
    
    # Verify response structure
    assert result is not None
    assert len(result.recommendations) == 5, f"Expected 5 recommendations, got {len(result.recommendations)}"
    assert 0 <= result.recommendation_diversity <= 1.0, "Diversity should be between 0 and 1"
    assert 0 <= result.confidence_score <= 1.0, "Confidence should be between 0 and 1"
    
    print(f"✓ Got {len(result.recommendations)} recommendations")
    print(f"✓ Diversity: {result.recommendation_diversity:.2f}")
    print(f"✓ Confidence: {result.confidence_score:.2f}")


def test_empty_browsing_history():
    """Test recommendation with empty browsing history."""
    agent = EcommerceRecommendationAgent()
    
    request = RecommendationRequest(
        user_id="new_user",
        current_cart_value=0.0,
        user_segment="new",
        browsing_history=[]
    )
    
    result = agent.recommend(request)
    
    assert result is not None
    assert len(result.recommendations) == 5
    print("✓ Handles empty browsing history correctly")


def test_high_value_customer():
    """Test recommendations for high-value customer."""
    agent = EcommerceRecommendationAgent()
    
    request = RecommendationRequest(
        user_id="vip_customer",
        current_cart_value=1000.0,
        user_segment="high_value",
        browsing_history=[
            BrowsingEvent(product_id=f"SKU{i:03d}", category="Premium", dwell_time_ms=4000)
            for i in range(5)
        ]
    )
    
    result = agent.recommend(request)
    
    assert result is not None
    assert result.confidence_score > 0.7, "High-value customer should have high confidence"
    print(f"✓ High-value customer recommendation confidence: {result.confidence_score:.2f}")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("TESTING: EcommerceRecommendationAgent")
    print("="*60)
    
    try:
        test_agent_initialization()
        test_basic_recommendation()
        test_empty_browsing_history()
        test_high_value_customer()
        
        print("\n" + "="*60)
        print("✓ ALL TESTS PASSED")
        print("="*60)
    except Exception as e:
        print(f"\n❌ TEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)