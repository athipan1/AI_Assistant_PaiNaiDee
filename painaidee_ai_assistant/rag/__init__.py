"""
RAG (Retrieval-Augmented Generation) Module for PaiNaiDee AI Assistant

This module provides retrieval-augmented generation capabilities for the Thai tourism assistant,
allowing it to answer questions based on up-to-date information from external sources.
"""

from .core import RAGSystem
from .retriever import DocumentRetriever
from .crawler import TourismCrawler
from .vector_store import SimpleVectorStore
from .scheduler import RAGScheduler, start_background_updates, stop_background_updates

__all__ = ['RAGSystem', 'DocumentRetriever', 'TourismCrawler', 'SimpleVectorStore', 'RAGScheduler', 'start_background_updates', 'stop_background_updates']