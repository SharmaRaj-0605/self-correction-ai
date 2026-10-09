import asyncio
import uuid

from backend.app.agents.roles import (
    Planner, Researcher, Analyst, Synthesizer,
    Critic, FactChecker, Judge, CorrectionAgent,
)
from backend.app.models.schemas import AgentLog, TaskResponse
from backend.app.services.cache import Cache
from backend.app.services.llm import LLM


class Orchestrator:
    def __init__(self, llm: LLM, cache: Cache, max_iterations: int, min_score: float):
        self.llm = llm
        self.cache = cache
        self.max_iterations = max_iterations
        self.min_score = min_score

        self.planner = Planner(llm)
        self.researcher = Researcher(llm)
        self.analyst = Analyst(llm)
        self.synthesizer = Synthesizer(llm)
        self.critic = Critic(llm)
        self.fact_checker = FactChecker(llm)
        self.judge = Judge(llm)
        self.corrector = CorrectionAgent(llm)

    async def run(self, task: str) -> TaskResponse:
        cached = await self.cache.get(task)
        if cached:
            cached["cached"] = True
            return TaskResponse(**cached)

        task_id = str(uuid.uuid4())
        logs = []

        plan = await asyncio.to_thread(self.planner.run, task)
        logs.append(AgentLog(agent="Planner", status="completed", summary="Created task plan."))

        research = await asyncio.to_thread(self.researcher.run, task, plan)
        logs.append(AgentLog(agent="Researcher", status="completed", summary="Collected research."))

        analysis = await asyncio.to_thread(self.analyst.run, task, research)
        logs.append(AgentLog(agent="Analyst", status="completed", summary="Analyzed the research."))

        draft = await asyncio.to_thread(self.synthesizer.run, task, research, analysis)
        logs.append(AgentLog(agent="Synthesizer", status="completed", summary="Created the first draft."))

        final_score = 0.0
        completed_iterations = 0

        for iteration in range(1, self.max_iterations + 1):
            critique = await asyncio.to_thread(self.critic.run, task, draft)
            logs.append(
                AgentLog(
                    agent="Critic",
                    status="completed",
                    summary=f"Review round {iteration}: {critique.get('recommendation', 'REVISE')}.",
                )
            )

            fact_check = await asyncio.to_thread(self.fact_checker.run, task, draft)
            logs.append(
                AgentLog(
                    agent="Fact Checker",
                    status="completed",
                    summary=f"Fact check confidence: {fact_check.get('confidence', 'unknown')}.",
                )
            )

            judge = await asyncio.to_thread(
                self.judge.run, draft, critique, fact_check, self.min_score
            )
            final_score = float(judge.get("score", critique.get("score", 0)))
            completed_iterations = iteration

            approved = bool(judge.get("approved", False)) and final_score >= self.min_score
            if approved:
                logs.append(
                    AgentLog(
                        agent="Judge",
                        status="approved",
                        summary=f"Accepted the answer with score {final_score:.1f}/10.",
                    )
                )
                break

            logs.append(
                AgentLog(
                    agent="Judge",
                    status="revision_needed",
                    summary=f"Requested another revision. Score: {final_score:.1f}/10.",
                )
            )

            if iteration < self.max_iterations:
                draft = await asyncio.to_thread(
                    self.corrector.run, task, draft, critique, fact_check, judge
                )
                logs.append(
                    AgentLog(
                        agent="Correction Agent",
                        status="completed",
                        summary=f"Revised the draft after round {iteration}.",
                    )
                )

        result = TaskResponse(
            task_id=task_id,
            cached=False,
            answer=draft,
            score=final_score,
            iterations=completed_iterations,
            logs=logs,
        )

        await self.cache.set(task, result.model_dump())
        return result
