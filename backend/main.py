from fastapi import FastAPI, HTTPException, BackgroundTasks, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from contextlib import asynccontextmanager
import logging
import structlog
from typing import Dict, Any, Optional
import asyncio
import os
import time
import json
import aiohttp
import base64
from datetime import datetime
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

from rag.ingestion import DocumentIngestor
from rag.chat import ChatHandler
from rag.qdrant_client import QdrantManager
from rag.tasks import TaskManager
from api.exceptions import ContentNotFoundError, RAGException

# Import security middleware
from middleware.csrf import CSRFMiddleware
from middleware.auth import AuthMiddleware

# Import auth routes
from routes import auth

# Import ChatKit server
# from chatkit_server import get_chatkit_server

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Load environment variables
load_dotenv()


class Settings(BaseSettings):
    """Application settings from environment variables."""

    # OpenAI Configuration
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4.1-nano")
    openai_embedding_model: str = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")

    # Qdrant Configuration
    qdrant_url: str = os.getenv("QDRANT_URL", "http://localhost:6333")
    qdrant_api_key: Optional[str] = os.getenv("QDRANT_API_KEY")

    # Content Configuration
    book_content_path: str = os.getenv("BOOK_CONTENT_PATH", "./book_content")
    chunk_size: int = int(os.getenv("CHUNK_SIZE", "1000"))
    chunk_overlap: int = int(os.getenv("CHUNK_OVERLAP", "200"))

    # API Configuration
    api_host: str = os.getenv("API_HOST", "0.0.0.0")
    api_port: int = int(os.getenv("API_PORT", "7860"))
    log_level: str = os.getenv("LOG_LEVEL", "INFO")

    # Rate Limiting
    rate_limit_requests: int = int(os.getenv("RATE_LIMIT_REQUESTS", "60"))
    rate_limit_window: int = int(os.getenv("RATE_LIMIT_WINDOW", "60"))

    # CORS Configuration
    allowed_origins: str = os.getenv(
        "ALLOWED_ORIGINS",
        "http://localhost:3000,http://localhost:8080,https://mrowaisabdullah.github.io,https://huggingface.co"
    )

    # JWT Configuration
    jwt_secret_key: str = os.getenv("JWT_SECRET_KEY", "your-super-secret-jwt-key")

    # Conversation Context
    max_context_messages: int = int(os.getenv("MAX_CONTEXT_MESSAGES", "3"))
    context_window_size: int = int(os.getenv("CONTEXT_WINDOW_SIZE", "4000"))

    # Ingestion Configuration
    batch_size: int = int(os.getenv("BATCH_SIZE", "100"))
    max_concurrent_requests: int = int(os.getenv("MAX_CONCURRENT_REQUESTS", "10"))

    # Health Monitoring
    health_check_interval: int = int(os.getenv("HEALTH_CHECK_INTERVAL", "30"))

    class Config:
        case_sensitive = False


# Initialize settings
settings = Settings()

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

# Global variables for services
chat_handler: Optional[ChatHandler] = None
qdrant_manager: Optional[QdrantManager] = None
document_ingestor: Optional[DocumentIngestor] = None
task_manager: Optional[TaskManager] = None
app_start_time: datetime = datetime.utcnow()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan manager for FastAPI application."""
    global chat_handler, qdrant_manager, document_ingestor, task_manager

    # Create database tables on startup
    from database.config import create_tables
    create_tables()

    logger.info("Starting up RAG backend...",
                openai_configured=bool(settings.openai_api_key),
                qdrant_url=settings.qdrant_url)

    try:
        # Initialize Qdrant manager
        qdrant_manager = QdrantManager(
            url=settings.qdrant_url,
            api_key=settings.qdrant_api_key
        )
        await qdrant_manager.initialize()

        # Initialize document ingestor
        document_ingestor = DocumentIngestor(
            qdrant_manager,
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
            batch_size=settings.batch_size
        )

        # Initialize chat handler
        chat_handler = ChatHandler(
            qdrant_manager,
            openai_api_key=settings.openai_api_key,
            model=settings.openai_model,
            embedding_model=settings.openai_embedding_model,
            max_context_messages=settings.max_context_messages,
            context_window_size=settings.context_window_size
        )

        # Initialize task manager
        task_manager = TaskManager(
            max_concurrent_tasks=settings.max_concurrent_requests
        )
        await task_manager.start()

        logger.info("RAG backend initialized successfully")

        yield

    except Exception as e:
        logger.error("Failed to initialize RAG backend", error=str(e))
        raise
    finally:
        logger.info("Shutting down RAG backend...")
        if task_manager:
            await task_manager.stop()
        if qdrant_manager:
            await qdrant_manager.close()


# Create FastAPI app with lifespan
app = FastAPI(
    title="Physical AI & Humanoid Robotics RAG API",
    description="RAG backend for querying Physical AI & Humanoid Robotics book content",
    version="1.0.0",
    lifespan=lifespan
)

# Rate limit exceeded handler
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add session middleware for OAuth
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.jwt_secret_key,
    session_cookie="session_id",
    max_age=3600,  # 1 hour
    same_site="lax",
    https_only=False,  # Set to True in production with HTTPS
)

# Add security middleware (order matters: CSRF before Auth)
app.add_middleware(
    CSRFMiddleware,
    cookie_name="csrf_token",
    header_name="X-CSRF-Token",
    secure=False,  # Set to True in production with HTTPS
    httponly=False,
    samesite="lax",
    max_age=3600,
    exempt_paths=["/health", "/docs", "/openapi.json", "/ingest/status", "/collections"],
)

app.add_middleware(
    AuthMiddleware,
    anonymous_limit=3,
    exempt_paths=["/health", "/docs", "/openapi.json", "/ingest/status", "/collections", "/auth"],
    anonymous_header="X-Anonymous-Session-ID",
)

# Include auth routes
app.include_router(auth.router)


# Optional API key security for higher rate limits
security = HTTPBearer(auto_error=False)


async def get_api_key(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)):
    """Optional API key authentication."""
    if credentials:
        return credentials.credentials
    return None


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add request processing time header."""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled errors."""
    logger.error(
        "Unhandled exception",
        path=request.url.path,
        method=request.method,
        error=str(exc),
        exc_info=True
    )
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred",
            "request_id": str(id(request))
        }
    )


@app.get("/health")
@limiter.limit("100/minute")
async def health_check(request: Request):
    """Comprehensive health check endpoint."""
    health_status = {
        "status": "healthy",
        "version": "1.0.0",
        "uptime_seconds": (datetime.utcnow() - app_start_time).total_seconds(),
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "qdrant": {"status": "unknown", "details": {}},
            "openai": {"status": "unknown", "details": {}},
            "task_manager": {"status": "unknown", "details": {}}
        },
        "metrics": {
            "documents_count": 0,
            "chunks_count": 0,
            "active_tasks": 0
        }
    }

    # Check Qdrant
    if qdrant_manager:
        try:
            collections = await qdrant_manager.list_collections()
            collection_stats = await qdrant_manager.get_collection_stats()

            health_status["services"]["qdrant"] = {
                "status": "healthy",
                "details": {
                    "collections": collections,
                    "collection_stats": collection_stats
                }
            }

            # Update metrics
            if collection_stats:
                health_status["metrics"]["chunks_count"] = collection_stats.get("vector_count", 0)

        except Exception as e:
            health_status["services"]["qdrant"] = {
                "status": "unhealthy",
                "details": {"error": str(e)}
            }
            health_status["status"] = "degraded"
    else:
        health_status["services"]["qdrant"] = {
            "status": "not_initialized",
            "details": {}
        }
        health_status["status"] = "unhealthy"

    # Check OpenAI API key
    health_status["services"]["openai"] = {
        "status": "configured" if settings.openai_api_key else "not_configured",
        "details": {
            "api_key_configured": bool(settings.openai_api_key),
            "model": settings.openai_model,
            "embedding_model": settings.openai_embedding_model
        }
    }

    # Check task manager
    if task_manager:
        try:
            task_stats = task_manager.get_task_stats()
            health_status["services"]["task_manager"] = {
                "status": "healthy",
                "details": task_stats
            }

            # Update metrics
            health_status["metrics"]["active_tasks"] = task_stats.get("running_tasks", 0)

        except Exception as e:
            health_status["services"]["task_manager"] = {
                "status": "unhealthy",
                "details": {"error": str(e)}
            }
            health_status["status"] = "degraded"
    else:
        health_status["services"]["task_manager"] = {
            "status": "not_initialized",
            "details": {}
        }

    # Determine overall status
    service_statuses = [s["status"] for s in health_status["services"].values()]
    if "unhealthy" in service_statuses:
        health_status["status"] = "unhealthy"
    elif "not_initialized" in service_statuses:
        health_status["status"] = "initializing"

    return health_status


@app.post("/api/chat")
@limiter.limit(f"{settings.rate_limit_requests}/{settings.rate_limit_window}minute")
async def chat_endpoint(
    request: Request,
    chat_request: Dict[str, Any],
    api_key: Optional[str] = Depends(get_api_key)
):
    """Chat endpoint with Server-Sent Events streaming."""
    if not chat_handler:
        raise HTTPException(status_code=503, detail="Chat service not initialized")

    query = chat_request.get("question")
    if not query:
        raise HTTPException(status_code=400, detail="Question is required")

    session_id = chat_request.get("session_id")
    context_window = chat_request.get("context_window", settings.context_window_size)
    k = chat_request.get("k", 5)
    stream = chat_request.get("stream", True)

    # Log the request
    logger.info(
        "Chat request received",
        session_id=session_id,
        query_length=len(query),
        stream=stream,
        has_api_key=bool(api_key)
    )

    try:
        if stream:
            # Return SSE response
            return StreamingResponse(
                chat_handler.stream_chat(
                    query=query,
                    session_id=session_id,
                    k=k,
                    context_window=context_window
                ),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no"  # Disable nginx buffering
                }
            )
        else:
            # Return complete response (non-streaming)
            response = await chat_handler.chat(
                query=query,
                session_id=session_id,
                k=k,
                context_window=context_window
            )
            return response
    except ContentNotFoundError as e:
        # Specific error for when no relevant content is found
        logger.warning(f"No content found for query: {query[:100]}...")

        if stream:
            # Return a helpful streaming message
            async def helpful_response():
                import json
                message = {
                    "type": "error",
                    "error": "CONTENT_NOT_FOUND",
                    "message": "I couldn't find specific information about your question.",
                    "suggestion": "Try asking about specific topics like 'physical AI', 'humanoid robots', or 'robot sensing systems'. Your query might be too general.",
                    "help": {
                        "example_queries": [
                            "What is Physical AI?",
                            "How do humanoid robots work?",
                            "What are robot sensing systems?",
                            "Explain the key components of robotics"
                        ]
                    }
                }
                yield f"data: {json.dumps(message)}\n\n"
                yield "data: [DONE]\n\n"

            return StreamingResponse(
                helpful_response(),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no"
                }
            )
        else:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "CONTENT_NOT_FOUND",
                    "message": str(e),
                    "suggestion": "Try rephrasing your question or check if the content has been ingested."
                }
            )
    except RAGException as e:
        # General RAG system errors
        logger.error(f"RAG system error: {str(e)}", extra={"code": e.code})
        raise HTTPException(
            status_code=500,
            detail={
                "error": e.code,
                "message": str(e)
            }
        )
    except Exception as e:
        # Unexpected errors
        logger.error(f"Unexpected error in chat endpoint: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "INTERNAL_ERROR",
                "message": "An unexpected error occurred. Please try again later."
            }
        )


@app.post("/ingest")
@limiter.limit("10/minute")
async def ingest_documents(
    request: Request,
    background_tasks: BackgroundTasks,
    ingest_request: Optional[Dict[str, Any]] = None,
    api_key: Optional[str] = Depends(get_api_key)
):
    """Trigger document ingestion in the background."""
    if not task_manager or not document_ingestor:
        raise HTTPException(status_code=503, detail="Ingestion service not initialized")

    # Parse request or use defaults
    content_path = ingest_request.get("content_path") if ingest_request else None
    force_reindex = ingest_request.get("force_reindex", False) if ingest_request else False
    batch_size = ingest_request.get("batch_size", settings.batch_size) if ingest_request else settings.batch_size

    book_path = content_path or settings.book_content_path

    if not os.path.exists(book_path):
        raise HTTPException(status_code=404, detail=f"Content path not found: {book_path}")

    # Create task
    task_id = await task_manager.create_ingestion_task(
        content_path=book_path,
        force_reindex=force_reindex,
        batch_size=batch_size
    )

    # Execute task in background
    background_tasks.add_task(
        execute_ingestion_task,
        task_id
    )

    logger.info(
        "Document ingestion started",
        task_id=task_id,
        book_path=book_path,
        force_reindex=force_reindex,
        batch_size=batch_size
    )

    return {
        "message": "Document ingestion started",
        "task_id": task_id,
        "content_path": book_path,
        "force_reindex": force_reindex,
        "batch_size": batch_size,
        "status": "processing"
    }


async def execute_ingestion_task(task_id: str):
    """Execute ingestion task using task manager."""
    try:
        if not task_manager or not document_ingestor:
            logger.error("Task manager or ingestor not initialized")
            return

        await task_manager.execute_ingestion_task(
            task_id=task_id,
            ingestor=document_ingestor
        )

    except Exception as e:
        logger.error(
            "Task execution failed",
            task_id=task_id,
            error=str(e),
            exc_info=True
        )


@app.get("/ingest/status")
@limiter.limit("30/minute")
async def get_ingestion_status(
    request: Request,
    task_id: Optional[str] = None
):
    """Get ingestion status for a specific task or all tasks."""
    if not task_manager:
        raise HTTPException(status_code=503, detail="Task manager not initialized")

    if task_id:
        # Get specific task
        task = task_manager.get_task(task_id)
        if not task:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

        return task.model_dump()
    else:
        # Get all tasks
        limit = request.query_params.get("limit", 20)
        try:
            limit = int(limit)
        except ValueError:
            limit = 20

        tasks = task_manager.get_tasks(limit=limit)
        return {
            "tasks": [task.model_dump() for task in tasks],
            "total": len(tasks)
        }


@app.post("/ingest/{task_id}/cancel")
@limiter.limit("10/minute")
async def cancel_ingestion_task(
    request: Request,
    task_id: str
):
    """Cancel an ingestion task."""
    if not task_manager:
        raise HTTPException(status_code=503, detail="Task manager not initialized")

    success = await task_manager.cancel_task(task_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found or cannot be cancelled")

    return {"message": f"Task {task_id} cancelled successfully"}


@app.get("/ingest/stats")
@limiter.limit("30/minute")
async def get_ingestion_stats(request: Request):
    """Get ingestion task statistics."""
    if not task_manager:
        raise HTTPException(status_code=503, detail="Task manager not initialized")

    stats = task_manager.get_task_stats()
    return stats


@app.get("/collections")
@limiter.limit("30/minute")
async def list_collections(request: Request):
    """List all Qdrant collections."""
    if not qdrant_manager:
        raise HTTPException(status_code=503, detail="Service not initialized")

    try:
        collections = await qdrant_manager.list_collections()
        return {"collections": collections}
    except Exception as e:
        logger.error("Failed to list collections", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to list collections: {str(e)}")


@app.delete("/collections/{collection_name}")
@limiter.limit("10/minute")
async def delete_collection(request: Request, collection_name: str):
    """Delete a Qdrant collection."""
    if not qdrant_manager:
        raise HTTPException(status_code=503, detail="Service not initialized")

    try:
        await qdrant_manager.delete_collection(collection_name)
        logger.info("Collection deleted", collection_name=collection_name)
        return {"message": f"Collection '{collection_name}' deleted successfully"}
    except Exception as e:
        logger.error("Failed to delete collection", collection_name=collection_name, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to delete collection: {str(e)}")


@app.post("/api/chatkit/session")
@limiter.limit("60/minute")
async def create_chatkit_session(request: Request):
    """Create a ChatKit session by generating a client secret."""
    if not settings.openai_api_key:
        raise HTTPException(
            status_code=500,
            detail="OpenAI API key not configured"
        )

    try:
        # Get or generate a user ID for session persistence
        user_id = request.headers.get("X-User-ID")
        if not user_id:
            import uuid
            user_id = str(uuid.uuid4())

        # For development/demo, we'll use a mock workflow
        # In production, you'd get this from OpenAI Agent Builder
        workflow_id = os.getenv("CHATKIT_WORKFLOW_ID", "wf_demo_workflow")

        # If we have a custom workflow ID that points to our own system
        if workflow_id.startswith("custom_"):
            # Return a mock session for custom workflow
            # The frontend will handle connecting to our /chat endpoint directly
            return {
                "client_secret": None,  # Not used for custom integration
                "expires_after": 3600,
                "custom_endpoint": "http://localhost:7860/chat",
                "demo_mode": False,
                "custom_mode": True
            }

        # Create session with OpenAI ChatKit API
        async with aiohttp.ClientSession() as session:
            async with session.post(
                'https://api.openai.com/v1/chatkit/sessions',
                headers={
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {settings.openai_api_key}',
                    'OpenAI-Beta': 'chatkit_beta=v1',
                },
                json={
                    'workflow': {'id': workflow_id},
                    'user': user_id,
                    'chatkit_configuration': {
                        'file_upload': {'enabled': False},
                    },
                }
            ) as upstream_response:

                if upstream_response.status != 200:
                    error_text = await upstream_response.text()
                    logger.error(
                        "ChatKit session creation failed",
                        status=upstream_response.status,
                        error=error_text
                    )

                    # For development without a real workflow, return a mock session
                    # This allows the UI to load but won't have AI responses
                    if workflow_id == "wf_demo_workflow":
                        logger.warning(
                            "Using demo workflow - ChatKit UI will load but responses are disabled"
                        )
                        # For demo mode, return null to make ChatKit use its built-in demo mode
                        # This avoids the "Unsupported token version" error
                        return {
                            "client_secret": None,
                            "expires_after": 3600,
                            "demo_mode": True
                        }

                    raise HTTPException(
                        status_code=upstream_response.status,
                        detail=f"Failed to create ChatKit session: {error_text}"
                    )

                upstream_data = await upstream_response.json()

                return {
                    "client_secret": upstream_data.get("client_secret"),
                    "expires_after": upstream_data.get("expires_after", 3600)
                }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to create ChatKit session",
            error=str(e),
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create ChatKit session: {str(e)}"
        )


# Custom ChatKit Endpoint (disabled for now)
# @app.post("/chatkit")
# @limiter.limit("60/minute")
# async def chatkit_endpoint(request: Request):
#     """Custom ChatKit server endpoint that integrates with RAG system."""
#     try:
#         # Get the ChatKit server instance
#         server = get_chatkit_server()
#
#         # Get request body
#         body = await request.body()
#
#         # Get user context from headers
#         context = {
#             "user_id": request.headers.get("X-User-ID", "anonymous"),
#             "user_agent": request.headers.get("User-Agent", ""),
#             "ip": request.client.host if request.client else "unknown"
#         }
#
#         # Process the ChatKit request
#         result = await server.process(body, context)

        # Return streaming response if needed
        # if hasattr(result, '__aiter__'):
        #     return StreamingResponse(
        #         result,
        #         media_type="text/event-stream",
        #         headers={
        #             "Cache-Control": "no-cache",
        #             "Connection": "keep-alive",
        #             "X-Accel-Buffering": "no"  # Disable nginx buffering
        #         }
        #     )
        # else:
        #     # Return JSON response
        #     return JSONResponse(content=result.json if hasattr(result, 'json') else result)

    # except Exception as e:
    #     logger.error("ChatKit endpoint error", error=str(e), exc_info=True)
    #     raise HTTPException(status_code=500, detail=f"ChatKit processing error: {str(e)}")


if __name__ == "__main__":
    import uvicorn

    # Configure logging level
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Run with uvicorn for Hugging Face Spaces compatibility
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True,
        access_log=True
    )