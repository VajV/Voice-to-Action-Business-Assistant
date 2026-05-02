from pydantic import BaseModel, Field


class ActionItem(BaseModel):
    title: str
    owner: str | None = None
    due_date: str | None = None
    priority: str = Field(pattern="^(low|medium|high)$")
    context: str
    confidence: float = Field(ge=0, le=1)


class MeetingAnalysisPayload(BaseModel):
    summary: str
    decisions: list[str] = Field(default_factory=list)
    action_items: list[ActionItem] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    follow_up_questions: list[str] = Field(default_factory=list)
