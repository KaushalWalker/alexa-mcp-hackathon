
import re


def detect_intent(message: str) -> str:
    """Classify a user command without making an LLM API call."""
    text = re.sub(r"\s+", " ", message.lower()).strip()

    if re.search(
        r"\b(i (?:have )?(?:finished|completed)|mark .+ (?:complete|completed))\b",
        text,
    ):
        return "complete_task"

    if re.search(r"\b(add|create|remind me to)\b", text):
        return "create_task"

    if re.search(
        r"\b(show|list|what are)\b.*\b(tasks|to-dos|todos)\b",
        text,
    ):
        return "list_tasks"

    if re.search(
        r"\b(change|set|update)\b.*\b(focus|break|preferences|working hours)\b",
        text,
    ):
        return "update_preferences"

    if re.search(r"\b(plan|replan|schedule|organize)\b", text):
        return "generate_plan"

    return "general_chat"
