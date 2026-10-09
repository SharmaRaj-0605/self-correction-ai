import re


BLOCKED_PATTERNS = [
    r"ignore\s+(all\s+)?previous\s+instructions",
    r"reveal\s+(your|the)\s+(system|developer)\s+prompt",
    r"show\s+me\s+your\s+hidden\s+instructions",
]


class GuardrailError(ValueError):
    pass


def validate_input(prompt: str, max_chars: int) -> str:
    cleaned = prompt.strip()

    if len(cleaned) < 3:
        raise GuardrailError("Please provide a more useful task.")

    if len(cleaned) > max_chars:
        raise GuardrailError(f"Task is too long. Maximum is {max_chars} characters.")

    for pattern in BLOCKED_PATTERNS:
        if re.search(pattern, cleaned, flags=re.IGNORECASE):
            raise GuardrailError("The request contains a blocked instruction pattern.")

    return cleaned
