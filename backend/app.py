import logging
import os
from contextlib import asynccontextmanager
from typing import Optional, List, Dict
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware

from scraper import scrape_website
from rag_engine import rag_engine
from scheduler import start_scheduler, update_knowledge_base

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Load local master context and perform initial scrape if empty
    rag_engine.load_local_context()
    start_scheduler()
    if rag_engine.is_empty():
        logger.info("Knowledge base is empty. Performing initial scrape...")
        update_knowledge_base()
    yield
    # Shutdown logic if needed

app = FastAPI(title="OrbitThink Chatbot API", lifespan=lifespan)

# CORS configuration - Restrict to your domain and local dev for security
ALLOWED_ORIGINS = [
    "https://syedmuhammadmehmam.site",
    "https://www.syedmuhammadmehmam.site",
    "http://localhost:3000",
    "http://localhost:3001",
    "http://localhost:8080",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:3001",
    "http://127.0.0.1:8080"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

def verify_admin_key(x_admin_key: Optional[str] = Header(None)):
    """Simple security check for administrative endpoints."""
    expected_key = os.getenv("ADMIN_SECRET_KEY")
    if not expected_key:
        # If no key is set in env, we allow it (development mode)
        return
    if x_admin_key != expected_key:
        raise HTTPException(status_code=403, detail="Forbidden: Invalid Admin Key")

class ChatRequest(BaseModel):
    message: str
    history: Optional[List[Dict[str, str]]] = []

@app.get("/")
def read_root():
    return {"status": "online", "service": "OrbitThink Chatbot Backend"}

@app.post("/api/scrape", dependencies=[Depends(verify_admin_key)])
def trigger_scrape():
    """
    Protected endpoint to trigger scraping and updating the knowledge base.
    Requires 'X-Admin-Key' header if ADMIN_SECRET_KEY is set in environment.
    """
    try:
        # 1. Refresh local master context
        rag_engine.load_local_context()
        
        # 2. Scrape website
        data = scrape_website()
        if not data:
            raise HTTPException(status_code=500, detail="Scraping returned no data")
        
        success = rag_engine.add_documents(data, source="website")
        if not success:
             raise HTTPException(status_code=500, detail="Failed to update Vector DB")
             
        return {"status": "success", "message": "Knowledge base updated successfully"}
    except Exception as e:
        logger.error(f"Scrape failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Administrative task failed")

@app.post("/api/chat")
def chat_endpoint(request: ChatRequest):
    """
    Chat endpoint for the widget with input validation.
    """
    # Security: Limit message length to prevent resource abuse
    if len(request.message) > 500:
        raise HTTPException(status_code=400, detail="Message too long (max 500 chars)")
    
    # Security: Limit history size
    if request.history and len(request.history) > 10:
        request.history = request.history[-10:]

    try:
        response_text = rag_engine.generate_response(request.message)
        return {"response": response_text}
    except Exception as e:
        logger.error(f"Chat failed: {str(e)}")
        raise HTTPException(status_code=500, detail="AI Assistant currently unavailable")
