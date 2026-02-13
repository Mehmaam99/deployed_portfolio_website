from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import logging
from scraper import scrape_website
from rag_engine import rag_engine

logger = logging.getLogger(__name__)

def update_knowledge_base():
    """
    Job to scrape the website and update the vector store.
    """
    logger.info("Scheduler: Starting daily scrape job...")
    text_content = scrape_website()
    if text_content:
        success = rag_engine.add_documents(text_content)
        if success:
            logger.info("Scheduler: Knowledge base updated successfully.")
        else:
            logger.error("Scheduler: Failed to update knowledge base.")
    else:
        logger.warning("Scheduler: Scrape returned empty content.")

def start_scheduler():
    scheduler = BackgroundScheduler()
    # Run every 30 days
    scheduler.add_job(
        update_knowledge_base,
        trigger=IntervalTrigger(days=30),
        id='monthly_scrape_job',
        name='Monthly Portfolio Scrape',
        replace_existing=True
    )
    scheduler.start()
    logger.info("Scheduler started. Job scheduled for every 30 days.")
