"""
External plugins package for third-party service integrations
"""

from .tripadvisor_plugin import TripAdvisorPlugin
from .thai_news_plugin import ThaiNewsPlugin
from .cultural_sites_plugin import CulturalSitesPlugin

__all__ = [
    'TripAdvisorPlugin',
    'ThaiNewsPlugin', 
    'CulturalSitesPlugin'
]