"""Base class for affiliate network integrations."""
from abc import ABC, abstractmethod
from typing import List, Optional
from models.offer import Offer


class BaseNetwork(ABC):
    """Abstract base class for affiliate network APIs."""

    def __init__(self):
        """Initialize the network client."""
        self.network_name = self.__class__.__name__.replace("Network", "").lower()

    @abstractmethod
    def search_offers(
        self,
        keyword: Optional[str] = None,
        category: Optional[str] = None,
        min_epc: Optional[float] = None,
        limit: int = 50
    ) -> List[Offer]:
        """
        Search for offers based on criteria.

        Args:
            keyword: Search term for offer name/description
            category: Filter by category
            min_epc: Minimum earnings per click
            limit: Max results to return

        Returns:
            List of standardized Offer objects
        """
        pass

    @abstractmethod
    def get_offer_details(self, offer_id: str) -> Optional[Offer]:
        """
        Get detailed information about a specific offer.

        Args:
            offer_id: The network-specific offer ID

        Returns:
            Offer object or None if not found
        """
        pass

    @abstractmethod
    def test_connection(self) -> bool:
        """
        Test if API credentials are valid.

        Returns:
            True if connection successful, False otherwise
        """
        pass
