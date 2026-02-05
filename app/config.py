"""Configuration management for API credentials."""
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Application configuration."""

    # Impact API
    IMPACT_ACCOUNT_SID = os.getenv("IMPACT_ACCOUNT_SID", "")
    IMPACT_AUTH_TOKEN = os.getenv("IMPACT_AUTH_TOKEN", "")

    # CJ API
    CJ_API_KEY = os.getenv("CJ_API_KEY", "")

    # Awin API
    AWIN_API_KEY = os.getenv("AWIN_API_KEY", "")
    AWIN_PUBLISHER_ID = os.getenv("AWIN_PUBLISHER_ID", "")

    # Partnerstack API
    PARTNERSTACK_API_KEY = os.getenv("PARTNERSTACK_API_KEY", "")

    # SerpAPI
    SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY", "")

    @classmethod
    def is_impact_configured(cls) -> bool:
        """Check if Impact credentials are set."""
        return bool(cls.IMPACT_ACCOUNT_SID and cls.IMPACT_AUTH_TOKEN)

    @classmethod
    def is_cj_configured(cls) -> bool:
        """Check if CJ credentials are set."""
        return bool(cls.CJ_API_KEY)

    @classmethod
    def is_awin_configured(cls) -> bool:
        """Check if Awin credentials are set."""
        return bool(cls.AWIN_API_KEY and cls.AWIN_PUBLISHER_ID)

    @classmethod
    def is_partnerstack_configured(cls) -> bool:
        """Check if Partnerstack credentials are set."""
        return bool(cls.PARTNERSTACK_API_KEY)

    @classmethod
    def is_serpapi_configured(cls) -> bool:
        """Check if SerpAPI credentials are set."""
        return bool(cls.SERPAPI_API_KEY)
