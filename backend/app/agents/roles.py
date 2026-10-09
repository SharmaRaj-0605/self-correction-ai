from backend.app.services.llm import LLM


class Planner:
    def __init__(self, llm: LLM):
        self.llm = llm

    def run(self, task: str) -> str:
        return self.llm.ask(
            "You are a practical planning agent. Break the user's task into a small "
            "number of useful subtasks. Do not answer the task yet.",
            f"User task:\n{task}",
        )


class Researcher:
    def __init__(self, llm: LLM):
        self.llm = llm

    def run(self, task: str, plan: str) -> str:
        return self.llm.ask(
            "You are the research agent. Collect useful facts, definitions, "
            "examples and caveats. Separate strong facts from uncertain claims. "
            "Do not invent sources.",
            f"Task:\n{task}\n\nPlan:\n{plan}",
            web_search=True,
        )


class Analyst:
    def __init__(self, llm: LLM):
        self.llm = llm

    def run(self, task: str, research: str) -> str:
        return self.llm.ask(
            "You are the analysis agent. Examine the research, identify the main "
            "points, relationships, tradeoffs and weaknesses. Be precise.",
            f"Task:\n{task}\n\nResearch:\n{research}",
        )


class Synthesizer:
    def __init__(self, llm: LLM):
        self.llm = llm

    def run(self, task: str, research: str, analysis: str) -> str:
        return self.llm.ask(
            "You are the synthesizer. Write a clear first draft for the user. "
            "Do not mention internal agents. Do not make claims that are not "
            "supported by the supplied material.",
            f"Task:\n{task}\n\nResearch:\n{research}\n\nAnalysis:\n{analysis}",
        )


class Critic:
    def __init__(self, llm: LLM):
        self.llm = llm

    def run(self, task: str, draft: str) -> dict:
        return self.llm.ask_json(
            "You are a strict but fair reviewer. Find factual, logical, relevance, "
            "clarity and completeness problems. Return JSON with: score (0-10), "
            "critical_errors (list), warnings (list), and recommendation "
            "(APPROVE or REVISE).",
            f"Task:\n{task}\n\nDraft:\n{draft}",
        )


class FactChecker:
    def __init__(self, llm: LLM):
        self.llm = llm

    def run(self, task: str, draft: str) -> dict:
        return self.llm.ask_json(
            "You are the fact-checking agent. Check important factual statements "
            "against your knowledge and, when web search is enabled, current "
            "sources. Return JSON with: verified_points, questionable_points, "
            "corrections, and confidence (0-1). Never pretend uncertainty is "
            "certainty.",
            f"Task:\n{task}\n\nDraft:\n{draft}",
            web_search=True,
        )


class Judge:
    def __init__(self, llm: LLM):
        self.llm = llm

    def run(self, draft: str, critique: dict, fact_check: dict, min_score: float) -> dict:
        return self.llm.ask_json(
            "You are the final quality judge. Decide whether the draft is ready. "
            "Return JSON with approved (boolean), score (0-10), reason, and "
            "required_changes (list). Be conservative when serious errors remain.",
            f"Draft:\n{draft}\n\nCritic:\n{critique}\n\nFact check:\n{fact_check}\n\n"
            f"Minimum acceptance score: {min_score}",
        )


class CorrectionAgent:
    def __init__(self, llm: LLM):
        self.llm = llm

    def run(self, task: str, draft: str, critique: dict, fact_check: dict, judge: dict) -> str:
        return self.llm.ask(
            "You are the correction agent. Rewrite the draft using the review "
            "feedback. Keep useful material, remove unsupported claims, fix "
            "logic and improve clarity. Return only the revised answer.",
            f"Task:\n{task}\n\nCurrent draft:\n{draft}\n\n"
            f"Critic:\n{critique}\n\nFact check:\n{fact_check}\n\nJudge:\n{judge}",
        )
