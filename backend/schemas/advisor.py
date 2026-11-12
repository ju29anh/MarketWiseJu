"""Bounded chat input and structured planning output."""
from typing import Annotated
from pydantic import BaseModel, ConfigDict, Field, model_validator, field_validator

Text = Annotated[str, Field(min_length=1, max_length=600)]


class ChatRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    question: str = Field(min_length=2, max_length=1600)
    analysis_id: str | None = Field(default=None, pattern=r'^mw_[a-f0-9]{10}$')
    research_id: str | None = Field(default=None, pattern=r'^[a-f0-9]{32}$')
    conversation_id: str | None = Field(default=None, pattern=r'^[a-f0-9]{32}$')

    @field_validator('question')
    @classmethod
    def clean_question(cls, value):
        value = value.strip()
        if len(value) < 2 or any(ord(c) < 32 and c not in '\n\r\t' for c in value):
            raise ValueError('Nhập câu hỏi từ 2 đến 1600 ký tự.')
        return value

    @model_validator(mode='after')
    def one_report(self):
        if bool(self.analysis_id) == bool(self.research_id):
            raise ValueError('Chọn đúng một báo cáo để trò chuyện.')
        return self


class StrictModel(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)


class PlanStep(StrictModel):
    title: Annotated[str, Field(min_length=2, max_length=100)]
    when: Annotated[str, Field(min_length=1, max_length=100)]
    action: Text
    deliverable: Text
    decision_rule: Text


class EvidenceSelection(StrictModel):
    quote_id: Annotated[str, Field(pattern=r'^S[1-9][0-9]*Q[1-9][0-9]*$')]


class AdvisorDraft(StrictModel):
    answer: Annotated[str, Field(min_length=10, max_length=1400)]
    assumptions: list[Text] = Field(max_length=4)
    steps: list[PlanStep] = Field(max_length=5)
    questions: list[Text] = Field(max_length=3)
    evidence: list[EvidenceSelection] = Field(max_length=4)
