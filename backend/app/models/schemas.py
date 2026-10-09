from typing import List
from pydantic import BaseModel, Field


class TaskRequest(BaseModel):
    prompt: str = Field(min_length=3, max_length=8000)


class AgentLog(BaseModel):
    agent: str
    status: str
    summary: str


class TaskResponse(BaseModel):
    task_id: str
    cached: bool = False
    answer: str
    score: float
    iterations: int
    logs: List[AgentLog]
