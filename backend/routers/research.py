from concurrent.futures import ThreadPoolExecutor
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, field_validator
from services.research import discover, compare_profiles, normalize, slots, provider_configuration
from services.ai_engine import generate_tts_briefing, ask_market_ai
from fastapi.responses import FileResponse
from schemas.advisor import ChatRequest
from core.presentation import public_payload

router = APIRouter(prefix='/api/research', tags=['Nghiên cứu'])


class ResearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=200)

    @field_validator('query')
    @classmethod
    def clean(cls, value):
        value = ' '.join(value.split())
        if not value or any(ord(c) < 32 for c in value):
            raise ValueError('Nhập từ khóa từ 1 đến 200 ký tự.')
        return value


class CompareRequest(BaseModel):
    left: ResearchRequest
    right: ResearchRequest


class TTSRequest(BaseModel):
    text: str = Field(min_length=2, max_length=2500)
    voice: str = Field(default='Kore', max_length=40)


class AdvisorContext(BaseModel):
    category: str | None = Field(default=None, max_length=120)
    potential_score: int | None = Field(default=None, ge=0, le=100)
    growth_pct: float | None = Field(default=None, allow_inf_nan=False)


class AskAIRequest(BaseModel):
    query: str | None = Field(default=None, max_length=200)
    product_name: str | None = Field(default=None, max_length=200)
    category: str = Field(default='General Market', max_length=120)
    question: str = Field(min_length=2, max_length=600)
    potential_score: int | None = Field(default=None, ge=0, le=100)
    growth_pct: float | None = Field(default=None, allow_inf_nan=False)
    context: AdvisorContext | None = None


@router.get('/providers')
def providers():
    # Configuration only: no credentials and no billable provider requests.
    return provider_configuration()


@router.get('/datasets/{dataset_id}/csv')
def download_research_dataset(dataset_id: str):
    import re
    from services.market_report import storage
    if not re.fullmatch(r'[a-f0-9]{32}', dataset_id):
        raise HTTPException(404, 'Không tìm thấy bộ dữ liệu nghiên cứu.')
    path = storage() / f'{dataset_id}.csv'
    if not path.is_file():
        raise HTTPException(404, 'Bộ dữ liệu chưa có hoặc đã được lưu ở lần chạy khác.')
    return FileResponse(path, media_type='text/csv; charset=utf-8', filename=f'du-lieu-phan-tich-{dataset_id[:8]}.csv')


@router.post('/search')
def search(payload: ResearchRequest):
    if not slots.acquire(blocking=False):
        raise HTTPException(429, 'Nhiều yêu cầu nghiên cứu đang chạy. Vui lòng thử lại.')
    try:
        return public_payload(discover(payload.query))
    finally:
        slots.release()


@router.post('/compare')
def compare(payload: CompareRequest):
    if normalize(payload.left.query) == normalize(payload.right.query):
        raise HTTPException(400, 'Hãy chọn hai đối tượng khác nhau.')
    if not slots.acquire(blocking=False):
        raise HTTPException(429, 'Nhiều yêu cầu nghiên cứu đang chạy. Vui lòng thử lại.')
    try:
        with ThreadPoolExecutor(max_workers=2) as executor:
            left = executor.submit(discover, payload.left.query)
            right = executor.submit(discover, payload.right.query)
            return public_payload(compare_profiles(left.result(), right.result()))
    finally:
        slots.release()


@router.post('/context')
def reference_context(payload: ResearchRequest):
    if not slots.acquire(blocking=False):
        raise HTTPException(429, 'Nhiều yêu cầu nghiên cứu đang chạy. Vui lòng thử lại.')
    try:
        from services.market_report import build_report
        # Explicitly requested macro context, never merged into subject findings.
        return public_payload(build_report(payload.query, [], {}))
    finally:
        slots.release()


@router.post('/tts')
def synthesize_tts(payload: TTSRequest):
    return public_payload(generate_tts_briefing(payload.text, payload.voice))


@router.post('/ask')
def ask_ai_advisor(payload: AskAIRequest):
    ctx = payload.context or AdvisorContext()
    target_name = (payload.product_name or payload.query or 'Thị trường mục tiêu').strip()
    cat = ctx.category or payload.category
    pot = ctx.potential_score if ctx.potential_score is not None else payload.potential_score
    gr = ctx.growth_pct if ctx.growth_pct is not None else payload.growth_pct
    return public_payload(ask_market_ai(
        product_name=target_name,
        category=cat,
        question=payload.question,
        potential_score=pot,
        growth_pct=gr,
    ))


@router.post('/chat')
def chat_with_report(payload: ChatRequest):
    from services.advisor import chat
    return public_payload(chat(payload))
