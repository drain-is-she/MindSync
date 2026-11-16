"""Curated paraphrases, checked against the linked NHS pages on 2026-11-16.

No page scraping, embeddings service, credentials, or network access at runtime.
"""
from dataclasses import dataclass
import re
from mindsync.contracts import SourceRef

@dataclass(frozen=True)
class Guide:
    topic: str
    terms: frozenset[str]
    source: SourceRef
    advice: str
    steps: tuple[str, ...]

GUIDES = (
    Guide("sleep", frozenset("sleep sleeping asleep insomnia bedtime tired rest awake exhausted".split()),
          SourceRef(source_id="nhs-sleep", chunk_id="routine-1", publisher="NHS",
                    title="How to fall asleep faster and sleep better", section="Sleep routine and relaxation",
                    url="https://www.nhs.uk/every-mind-matters/mental-wellbeing-tips/how-to-fall-asleep-faster-and-sleep-better/"),
          "A consistent sleep schedule and a quiet wind-down period can support sleep.",
          ("Choose a regular time to get up, including on days off.",
           "Before bed, try a quiet activity such as reading or calming music.",
           "If worries keep returning, write down what you want to address tomorrow.")),
    Guide("worry", frozenset("worry worries worrying anxious anxiety exam exams study studying overwhelmed deadline deadlines work stress stressed".split()),
          SourceRef(source_id="nhs-worry", chunk_id="worry-time-1", publisher="NHS",
                    title="Tackling your worries", section="Worry time and making a plan",
                    url="https://www.nhs.uk/every-mind-matters/mental-wellbeing-tips/self-help-cbt-techniques/tackling-your-worries/"),
          "Writing worries down and separating actionable problems from things outside your control can help you plan.",
          ("Set aside 10 to 15 minutes to write down your concerns.",
           "Choose one concern you can influence and write one specific action and when to do it.",
           "For concerns you cannot act on now, acknowledge them and return attention to the present.")),
    Guide("breathing", frozenset("breath breathe breathing calm calming relax relaxation panic tense tension".split()),
          SourceRef(source_id="nhs-breathing", chunk_id="gentle-1", publisher="NHS",
                    title="Breathing exercises for stress", section="Gentle breathing exercise",
                    url="https://www.nhs.uk/mental-health/self-help/guides-tools-and-activities/breathing-exercises-for-stress/"),
          "Gentle, unforced breathing is one option for a calming exercise.",
          ("Sit or stand comfortably, with your feet supported.",
           "Let air enter gently through your nose and leave through your mouth; do not force a deep breath.",
           "If comfortable, count up to five on each inward and outward breath, repeating for about five minutes.")),
)

def retrieve(message: str, topic: str | None = None) -> list[Guide]:
    """Rank by whole-word overlap. Abstain when no supported topic matches."""
    words = set(re.findall(r"[a-z]+", message.lower()))
    ranked = sorted(((len(words & g.terms), i, g) for i, g in enumerate(GUIDES)),
                    key=lambda item: (-item[0], item[1]))
    if ranked[0][0]:
        return [g for score, _, g in ranked if score][:1]
    if topic and words & {"more", "continue", "again", "exercise", "yes", "next"}:
        return [g for g in GUIDES if g.topic == topic]
    return []
