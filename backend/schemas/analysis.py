from typing import Any, Literal
from pydantic import BaseModel, Field, field_validator


class DatasetRequest(BaseModel):
    dataset_name: str = Field(min_length=1, max_length=200)

    @field_validator('dataset_name')
    @classmethod
    def filename_only(cls, value):
        if any(c in value for c in ('/', '\\', ':', '\x00')) or value in ('.', '..'):
            raise ValueError('Tên dataset không hợp lệ')
        return value


class AnalyzeRequest(DatasetRequest):
    product_name: str = Field(min_length=2, max_length=200)
    category: str = Field(min_length=1, max_length=120)
    description: str | None = Field(default='', max_length=4000)
    custom_roles: dict[str, str | None] | None = None

    @field_validator('product_name', 'category')
    @classmethod
    def clean_label(cls, value, info):
        value = ' '.join(value.split())
        if len(value) < (2 if info.field_name == 'product_name' else 1) or any(ord(c) < 32 for c in value):
            raise ValueError('Tên đối tượng hoặc ngành không hợp lệ')
        return value


class AnalysisResponse(BaseModel):
    # ML outputs retain their existing fields for backwards compatibility.
    model_config = {'extra': 'allow'}
    session_id: str
    product_name: str
    category: str
    dataset_name: str
    quality_score: float
    potential_score: float
    regression: dict[str, Any]
    classification: dict[str, Any]
    clustering: dict[str, Any]
    strategy_recommendation: dict[str, Any]


class JobResponse(BaseModel):
    job_id: str
    status: Literal['queued', 'running', 'complete', 'failed']
    step: int
    message: str
    session_id: str | None = None


class PreviewResponse(BaseModel):
    columns: list[str]
    rows: list[dict[str, Any]]
    total_rows: int


class UploadResponse(BaseModel):
    message: str
    filename: str
    validation: dict[str, Any]
    preview: PreviewResponse
