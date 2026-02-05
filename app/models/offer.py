"""Unified offer data model across all affiliate networks."""
from typing import Optional, List
from pydantic import BaseModel, Field


class Offer(BaseModel):
    """Standardized offer model."""

    # Basic Info
    id: str
    name: str
    description: Optional[str] = None
    network: str  # "impact", "cj", "awin", etc.

    # Advertiser Info
    advertiser_name: str
    advertiser_id: str

    # Commission Info
    commission_type: Optional[str] = None  # "CPA", "CPS", "Hybrid", etc.
    commission_value: Optional[float] = None  # Dollar amount or percentage
    commission_currency: str = "USD"

    # Performance Metrics
    epc: Optional[float] = Field(None, description="Earnings Per Click")
    conversion_rate: Optional[float] = Field(None, description="Conversion rate %")
    avg_sale_value: Optional[float] = Field(None, description="Average order value")

    # Popularity/Quality Indicators
    popularity_score: Optional[float] = None  # Network-specific popularity metric

    # Categories
    category: Optional[str] = None
    subcategory: Optional[str] = None

    # Links
    tracking_url: Optional[str] = None
    landing_page_url: Optional[str] = None

    # YouTube Suitability (calculated)
    youtube_score: Optional[float] = Field(None, description="Calculated YT suitability score")

    # Search Volume & Potential Analysis
    search_interest: Optional[int] = Field(None, description="Google Trends interest (0-100)")
    search_trend: Optional[str] = Field(None, description="Trend: rising, stable, declining")
    potential_score: Optional[int] = Field(None, description="Overall potential score (0-100)")
    potential_rating: Optional[str] = Field(None, description="Rating: Excellent, Good, Fair, Poor")
    potential_analysis: Optional[str] = Field(None, description="Text analysis of potential")
    related_keywords: Optional[List[str]] = Field(None, description="Related search keywords for SEO")

    # Scalability Metrics
    scalability_score: Optional[int] = Field(None, description="Overall scalability score (0-100)")
    cookie_duration: Optional[int] = Field(None, description="Cookie duration in days")
    traffic_monthly: Optional[str] = Field(None, description="Monthly traffic estimate (e.g. '45K/mo')")
    growth_percentage: Optional[str] = Field(None, description="Growth percentage (e.g. '+62%')")
    competition_level: Optional[str] = Field(None, description="Competition level: Low, Medium, High")
    domain_authority: Optional[int] = Field(None, description="Domain authority score (0-100)")
    instagram_followers: Optional[str] = Field(None, description="Instagram followers (e.g. '12K')")

    def calculate_youtube_score(self) -> float:
        """
        Calculate a YouTube suitability score (0-100).

        Factors:
        - High EPC (visual products sell better on video)
        - High commission value (worth promoting)
        - Popularity (proven to convert)
        """
        score = 0.0

        # EPC component (0-40 points)
        if self.epc:
            # $1+ EPC = excellent for YT
            score += min(self.epc * 20, 40)

        # Commission component (0-30 points)
        if self.commission_value:
            # $50+ commission = high score
            if self.commission_type == "CPA":
                score += min(self.commission_value / 2, 30)
            elif self.commission_type == "CPS":
                # % commission: 10% or more is good
                score += min(self.commission_value * 2, 30)

        # Popularity component (0-30 points)
        if self.popularity_score:
            score += min(self.popularity_score / 3, 30)

        self.youtube_score = round(min(score, 100), 2)
        return self.youtube_score

    class Config:
        """Pydantic config."""
        json_schema_extra = {
            "example": {
                "id": "12345",
                "name": "Premium VPN Service",
                "description": "Top-rated VPN with 30-day money-back guarantee",
                "network": "impact",
                "advertiser_name": "VPN Company",
                "advertiser_id": "1000",
                "commission_type": "CPA",
                "commission_value": 75.0,
                "epc": 2.50,
                "conversion_rate": 3.5,
                "category": "Software",
                "youtube_score": 85.5
            }
        }
