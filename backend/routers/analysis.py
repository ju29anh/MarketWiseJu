from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from database import get_analysis_session_by_id
from schemas.analysis import AnalyzeRequest, AnalysisResponse, JobResponse
from services.analysis import analyze
from services.datasets import resolve_dataset
from services.jobs import analysis_slots
from core.presentation import public_payload

router = APIRouter(prefix='/api', tags=['Analysis'])


@router.post('/analyze', response_model=AnalysisResponse)
def run_market_analysis(req: AnalyzeRequest):
    if not analysis_slots.acquire(blocking=False):
        raise HTTPException(429, 'Một phân tích đang chạy. Vui lòng thử lại sau.')
    try:
        return JSONResponse(content=public_payload(analyze(req)))
    finally:
        analysis_slots.release()


@router.post('/analysis/jobs', response_model=JobResponse, status_code=202)
def start_job(payload: AnalyzeRequest, request: Request):
    resolve_dataset(payload.dataset_name)
    return request.app.state.jobs.submit(payload)


@router.get('/analysis/jobs/{job_id}', response_model=JobResponse)
def job_status(job_id: str, request: Request):
    return request.app.state.jobs.get(job_id)


@router.get('/analysis/{session_id}', response_model=AnalysisResponse)
def get_analysis_by_id(session_id: str):
    session = get_analysis_session_by_id(session_id)
    if not session:
        raise HTTPException(404, 'Không tìm thấy phiên phân tích này.')
    return public_payload(session)
