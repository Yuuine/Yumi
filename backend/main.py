"""
Yumi Backend - FastAPI 服务
"""
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .core import settings, setup_exception_handlers
from .core.logging import YumiLogger, get_logger
from .core.middleware import RequestTracingMiddleware, SlowRequestMiddleware
from .database import init_db
from .routers import chat, memory, user
from .routers import settings as settings_router
from .routers import models
from .services.emotion import EmotionEngine
from .services.llm import LLMService
from .services.memory import MemoryEngine
from .services.prompt_builder import PromptBuilder

PROJECT_ROOT = Path(__file__).resolve().parent.parent
log_dir = PROJECT_ROOT / settings.logging.dir
YumiLogger.setup(
    level=settings.logging.level,
    log_dir=log_dir,
    app_name=settings.app.name.lower(),
    app_version=settings.app.version,
    environment="development" if settings.app.debug else "production",
    max_file_size=settings.logging.max_file_size_mb * 1024 * 1024,
    backup_count=settings.logging.backup_count,
    enable_file_log=settings.logging.enable_file,
    enable_json_format=settings.logging.enable_json,
)
logger = get_logger(__name__)

memory_engine: MemoryEngine | None = None
emotion_engine: EmotionEngine | None = None
llm_service: LLMService | None = None
prompt_builder: PromptBuilder | None = None


async def lifespan(app: FastAPI):
    global memory_engine, emotion_engine, llm_service, prompt_builder

    logger.info("Initializing Yumi backend services...")

    await init_db()

    memory_engine = MemoryEngine()
    await memory_engine.initialize()

    emotion_engine = EmotionEngine()
    await emotion_engine.initialize()

    llm_service = LLMService()

    prompt_builder = PromptBuilder(memory_engine, emotion_engine)

    app.state.memory_engine = memory_engine
    app.state.emotion_engine = emotion_engine
    app.state.llm_service = llm_service
    app.state.prompt_builder = prompt_builder

    logger.info("Yumi backend services initialized successfully")

    yield

    logger.info("Shutting down Yumi backend services...")
    if memory_engine:
        await memory_engine.close()
    if emotion_engine:
        await emotion_engine.close()
    if llm_service:
        await llm_service.close()
    logger.info("Yumi backend services shut down complete")


app = FastAPI(
    title="Yumi API",
    description="Yumi AI虚拟人物伴侣后端服务",
    version=settings.app.version,
    lifespan=lifespan,
)

setup_exception_handlers(app)

app.add_middleware(SlowRequestMiddleware, threshold_ms=1000)
app.add_middleware(RequestTracingMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.server.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router, prefix="/api", tags=["chat"])
app.include_router(memory.router, prefix="/api", tags=["memory"])
app.include_router(user.router, prefix="/api", tags=["user"])
app.include_router(settings_router.router, prefix="/api", tags=["settings"])
app.include_router(models.router, prefix="/api", tags=["models"])


@app.get("/")
async def root():
    return {
        "message": f"{settings.app.name} API v{settings.app.version}",
        "status": "running",
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    import sys
    from pathlib import Path

    project_root = Path(__file__).resolve().parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    import uvicorn

    uvicorn.run(
        "backend.main:app",
        host=settings.server.host,
        port=settings.server.port,
        reload=settings.app.debug,
    )
