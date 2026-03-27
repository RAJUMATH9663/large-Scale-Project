import time
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional
from app.database import get_db
from app.models.models import User, QueryHistory, Dataset
from app.utils.auth import get_current_user
from app.config import get_settings
import httpx

router = APIRouter(prefix="/api/ai", tags=["AI (LangGraph + OpenRouter)"])
settings = get_settings()

AVAILABLE_MODELS = [
    "openai/gpt-4o-mini",
    "openai/gpt-4o",
    "anthropic/claude-3-5-sonnet",
    "google/gemini-flash-1.5",
    "meta-llama/llama-3-8b-instruct",
    "mistralai/mixtral-8x7b-instruct",
]


class AIQueryRequest(BaseModel):
    query: str
    dataset_id: Optional[int] = None
    model: Optional[str] = None
    include_explanation: bool = True
    include_story: bool = True


class ChatMessage(BaseModel):
    role: str
    content: str


async def call_openrouter(messages: list, model: str) -> tuple[str, int]:
    """Call OpenRouter API and return (text, tokens_used)."""
    if not settings.OPENROUTER_API_KEY:
        # Demo mode — return mock response
        return (
            "**Demo Mode** — Add your `OPENROUTER_API_KEY` to `.env` to enable live AI responses.\n\n"
            "This is where the AI would analyze your data and return insights, explanations, and stories.",
            0,
        )

    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            f"{settings.OPENROUTER_BASE_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
                "HTTP-Referer": "https://dataai.saas",
                "X-Title": "DataAI SaaS",
            },
            json={"model": model, "messages": messages},
        )
        if resp.status_code != 200:
            raise HTTPException(500, f"LLM error: {resp.text}")
        data = resp.json()
        text = data["choices"][0]["message"]["content"]
        tokens = data.get("usage", {}).get("total_tokens", 0)
        return text, tokens


def detect_intent(query: str) -> str:
    """Simple intent detection — in production use a classifier."""
    q = query.lower()
    if any(w in q for w in ["predict", "forecast", "future"]):
        return "prediction"
    if any(w in q for w in ["anomaly", "spike", "outlier", "unusual"]):
        return "anomaly"
    if any(w in q for w in ["compare", "difference", "vs"]):
        return "comparison"
    if any(w in q for w in ["why", "explain", "reason"]):
        return "explanation"
    if any(w in q for w in ["story", "narrative", "summary"]):
        return "storytelling"
    return "general_analysis"


def build_system_prompt(intent: str, dataset_context: str) -> str:
    base = (
        "You are DataAI, an expert data analyst AI. You analyze datasets and provide clear, "
        "actionable insights. Always structure your response with:\n"
        "1. **Key Finding** - The main insight\n"
        "2. **Analysis** - Detailed explanation\n"
        "3. **Recommendation** - What to do\n"
    )
    if intent == "storytelling":
        base += "\n4. **Story** - A business narrative that non-technical stakeholders can understand\n"
    if intent == "explanation":
        base += "\nProvide step-by-step reasoning. Be transparent about your logic.\n"
    if dataset_context:
        base += f"\n\nDataset context:\n{dataset_context}"
    return base


@router.post("/query")
async def ai_query(
    payload: AIQueryRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    model = payload.model or settings.DEFAULT_MODEL
    start_time = time.time()

    # Build dataset context
    dataset_context = ""
    if payload.dataset_id:
        result = await db.execute(
            select(Dataset).where(Dataset.id == payload.dataset_id, Dataset.owner_id == current_user.id)
        )
        dataset = result.scalar_one_or_none()
        if dataset and dataset.meta:
            cols = dataset.meta.get("columns", [])
            dataset_context = (
                f"Dataset: {dataset.name}\n"
                f"Rows: {dataset.rows}, Columns: {dataset.columns}\n"
                f"Column names: {', '.join(cols[:20])}\n"
            )

    # Detect intent (LangGraph node 1)
    intent = detect_intent(payload.query)
    system_prompt = build_system_prompt(intent, dataset_context)

    # Build messages (LangGraph node 2)
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": payload.query},
    ]

    # Call LLM (LangGraph node 3)
    ai_response, tokens = await call_openrouter(messages, model)

    latency_ms = (time.time() - start_time) * 1000

    # Save to history
    history = QueryHistory(
        user_id=current_user.id,
        dataset_id=payload.dataset_id,
        query=payload.query,
        response=ai_response,
        model_used=model,
        tokens_used=tokens,
        latency_ms=latency_ms,
    )
    db.add(history)
    await db.commit()
    await db.refresh(history)

    return {
        "query_id": history.id,
        "intent": intent,
        "model": model,
        "response": ai_response,
        "tokens_used": tokens,
        "latency_ms": round(latency_ms, 2),
    }


@router.get("/models")
async def list_models(current_user: User = Depends(get_current_user)):
    return {"models": AVAILABLE_MODELS, "default": settings.DEFAULT_MODEL}
