from pathlib import Path
import asyncio
from uuid import uuid4
import traceback
from fastapi import HTTPException
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from fastapi.templating import Jinja2Templates

from app.config.settings import get_settings
from app.database.session import async_session_factory
from app.schemas.digest import DigestRequest
from app.services.digest_service import build_digest
from app.services.digest_task_manager import (
    create_task,
    get_task,
    update_task,
)
settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug,
)

templates = Jinja2Templates(
    directory=str(Path(__file__).parent / "templates")
)


@app.get("/")
async def index(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
    )


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}

async def _run_digest_task(
    task_id: str,
    credentials: str,
    interests: list[str],
    sources: list[str],
) -> None:
    try:
        async with async_session_factory() as session:
            result = await build_digest(
                session,
                credentials=credentials,
                interests=interests,
                sources=sources,
                task_id=task_id,
            )

        update_task(
            task_id,
            result={
                "total_articles": result.total_articles,
                "analyzed": result.analyzed,
                "relevant": result.relevant,
                "not_relevant": result.not_relevant,
                "markdown": "/api/digest/download/markdown",
                "docx": "/api/digest/download/docx",
                "preview": result.preview,
            },
        )

    except Exception as exc:
        print(
            f"\n[ERROR] Digest task {task_id} failed:",
            flush=True,
        )
        traceback.print_exc()

        update_task(
            task_id,
            status="failed",
            message="Ошибка формирования дайджеста.",
            error=str(exc),
        )

@app.post("/api/digest")
async def create_digest(request: DigestRequest):
    task_id = str(uuid4())

    create_task(task_id)

    asyncio.create_task(
        _run_digest_task(
            task_id,
            request.credentials,
            request.interests,
            request.sources,
        )
    )

    return {
        "task_id": task_id,
    }

@app.get("/api/digest/status/{task_id}")
async def digest_status(task_id: str):
    task = get_task(task_id)

    if task is None:
        raise HTTPException(
            status_code=404,
            detail="Task not found.",
        )

    return {
        "status": task.status,
        "current": task.current,
        "total": task.total,
        "percent": task.percent,
        "message": task.message,
        "error": task.error,
        "result": task.result,
    }


@app.get("/api/digest/download/markdown")
async def download_markdown():
    path = Path("output/digest.md")

    if not path.exists():
        return {"error": "Digest has not been generated yet."}

    return FileResponse(
        path,
        media_type="text/markdown",
        filename="digest.md",
    )


@app.get("/api/digest/download/docx")
async def download_docx():
    path = Path("output/digest.docx")

    if not path.exists():
        return {"error": "Digest has not been generated yet."}

    return FileResponse(
        path,
        media_type=(
            "application/vnd.openxmlformats-officedocument."
            "wordprocessingml.document"
        ),
        filename="digest.docx",
    )