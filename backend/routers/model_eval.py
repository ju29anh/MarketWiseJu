from fastapi import APIRouter
from pydantic import BaseModel
from typing import Any
from routers.analysis import get_analysis_by_id

router = APIRouter(prefix='/api', tags=['Model evaluation'])


class ModelEvaluation(BaseModel):
    session_id: str
    regression: dict[str, Any]
    classification: list[dict[str, Any]]
    silhouette_score: float | None


@router.get('/analysis/{session_id}/model-eval', response_model=ModelEvaluation)
def get_model_evaluation(session_id: str):
    data = get_analysis_by_id(session_id)
    return {'session_id': session_id, 'regression': data['regression_metrics'],
            'classification': data['classification_metrics'],
            'silhouette_score': data['clustering'].get('silhouette_score')}
