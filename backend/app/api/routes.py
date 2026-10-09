from fastapi import APIRouter, HTTPException

from backend.app.core.config import get_settings
from backend.app.core.guardrails import validate_input
from backend.app.models.schemas import TaskRequest, TaskResponse
from backend.app.services.llm import LLM
from backend.app.services.cache import Cache
from backend.app.workflow.orchestrator import Orchestrator

router = APIRouter(prefix="/api/v1")
settings = get_settings()

llm = LLM(
    api_key=settings.gemini_api_key,
    model=settings.gemini_model,
    use_web_search=settings.use_web_search,
    fallback_model=settings.gemini_fallback_model or None,
    max_retries=settings.gemini_max_retries,
)

cache = Cache(
    redis_url=settings.redis_url,
    ttl=settings.cache_ttl_seconds,
)

orchestrator = Orchestrator(
    llm=llm,
    cache=cache,
    max_iterations=settings.max_iterations,
    min_score=settings.min_accept_score,
)


@router.post("/tasks", response_model=TaskResponse)
async def create_task(request: TaskRequest):
    try:
        prompt = validate_input(request.prompt, settings.max_input_chars)
        return await orchestrator.run(prompt)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Task failed: {exc}") from exc