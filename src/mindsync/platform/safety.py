"""Conservative English phrase routing, not a clinically validated classifier."""
import re

URGENT_REPLY = (
    "I'm sorry you're going through this. Please seek human support now. "
    "If you or someone else is in immediate danger, has taken an overdose, or has serious "
    "physical symptoms, call your local emergency number or go to the nearest emergency department. "
    "If you can, contact someone you trust to stay with you. For urgent emotional support, "
    "contact a local crisis service or a healthcare professional. "
    "This prototype cannot assess your safety; simulated readings cannot establish that you are safe."
)
PATTERNS = (
    r"\b(suicid\w*|overdos\w*)\b",
    r"\b(kill|hurt|harm|cut) (myself|yourself|himself|herself|someone|another person)\b",
    r"\b(end my life|want to die|wish i (?:was|were) dead|cannot stay safe|can't stay safe)\b",
    r"\b(chest pain|chest pressure|severe bleeding|coughing blood|unconscious)\b",
    r"\b(can't breathe|cannot breathe|struggling to breathe|difficulty breathing)\b",
    r"\b(took|taken|swallowed) (?:too many|a lot of|all (?:my|the)) (?:pills|tablets)\b",
)

def is_urgent(message):
    normalized = " ".join(message.lower().replace("’", "'").split())
    return any(re.search(pattern, normalized) for pattern in PATTERNS)
