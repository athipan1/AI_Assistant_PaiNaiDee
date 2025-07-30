"""
Background scheduler for periodic RAG knowledge base updates.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import threading
from concurrent.futures import ThreadPoolExecutor

from .core import RAGSystem

logger = logging.getLogger(__name__)

class RAGScheduler:
    """Background scheduler for periodic knowledge base updates."""
    
    def __init__(self, rag_system: RAGSystem, update_interval_hours: int = 6):
        self.rag_system = rag_system
        self.update_interval_hours = update_interval_hours
        self.is_running = False
        self.last_update = None
        self.executor = ThreadPoolExecutor(max_workers=1)
        self.update_task = None
        
    def start(self) -> None:
        """Start the background scheduler."""
        if self.is_running:
            logger.warning("Scheduler is already running")
            return
        
        self.is_running = True
        self.update_task = asyncio.create_task(self._run_scheduler())
        logger.info(f"RAG scheduler started with {self.update_interval_hours}h update interval")
    
    def stop(self) -> None:
        """Stop the background scheduler."""
        if not self.is_running:
            return
        
        self.is_running = False
        if self.update_task:
            self.update_task.cancel()
        
        self.executor.shutdown(wait=False)
        logger.info("RAG scheduler stopped")
    
    async def _run_scheduler(self) -> None:
        """Main scheduler loop."""
        while self.is_running:
            try:
                # Calculate time until next update
                now = datetime.now()
                if self.last_update is None:
                    # First update after 1 minute of startup
                    next_update = now + timedelta(minutes=1)
                else:
                    next_update = self.last_update + timedelta(hours=self.update_interval_hours)
                
                # Wait until next update time
                if now < next_update:
                    wait_seconds = (next_update - now).total_seconds()
                    logger.info(f"Next RAG update in {wait_seconds/3600:.1f} hours")
                    await asyncio.sleep(min(wait_seconds, 3600))  # Check every hour at most
                    continue
                
                # Perform update
                logger.info("Starting scheduled RAG knowledge base update...")
                result = await self.rag_system.update_knowledge_base()
                
                self.last_update = datetime.now()
                
                if result["status"] == "success":
                    logger.info(f"Scheduled update completed: {result['documents_added']} new documents")
                else:
                    logger.warning(f"Scheduled update failed: {result.get('error', 'Unknown error')}")
                
            except asyncio.CancelledError:
                logger.info("Scheduler cancelled")
                break
            except Exception as e:
                logger.error(f"Error in scheduler: {e}")
                # Wait 30 minutes before retrying on error
                await asyncio.sleep(1800)
    
    async def trigger_manual_update(self) -> Dict[str, Any]:
        """Trigger a manual update outside the schedule."""
        logger.info("Manual RAG update triggered")
        result = await self.rag_system.update_knowledge_base()
        self.last_update = datetime.now()
        return result
    
    def get_status(self) -> Dict[str, Any]:
        """Get scheduler status."""
        now = datetime.now()
        
        if self.last_update:
            time_since_last = (now - self.last_update).total_seconds() / 3600
            next_update = self.last_update + timedelta(hours=self.update_interval_hours)
            time_to_next = (next_update - now).total_seconds() / 3600
        else:
            time_since_last = None
            time_to_next = 1/60  # 1 minute for first update
        
        return {
            "is_running": self.is_running,
            "update_interval_hours": self.update_interval_hours,
            "last_update": self.last_update.isoformat() if self.last_update else None,
            "time_since_last_update_hours": time_since_last,
            "time_to_next_update_hours": max(0, time_to_next) if time_to_next else None,
            "status": "running" if self.is_running else "stopped"
        }

# Global scheduler instance
_global_scheduler: Optional[RAGScheduler] = None

def get_scheduler(rag_system: Optional[RAGSystem] = None) -> RAGScheduler:
    """Get or create the global scheduler instance."""
    global _global_scheduler
    
    if _global_scheduler is None and rag_system is not None:
        _global_scheduler = RAGScheduler(rag_system)
    
    return _global_scheduler

def start_background_updates(rag_system: RAGSystem, interval_hours: int = 6) -> RAGScheduler:
    """Start background updates for the RAG system."""
    global _global_scheduler
    
    if _global_scheduler is not None:
        _global_scheduler.stop()
    
    _global_scheduler = RAGScheduler(rag_system, interval_hours)
    _global_scheduler.start()
    
    return _global_scheduler

def stop_background_updates() -> None:
    """Stop background updates."""
    global _global_scheduler
    
    if _global_scheduler is not None:
        _global_scheduler.stop()
        _global_scheduler = None