"""Drafts a tailored cover letter for a posting from resume.yaml facts.

This is a template, not an LLM call -- deterministic and free to run, and
easy for you to tweak the wording of in one place (TEMPLATE below). Every
draft is meant to be read and edited by you before anything is sent.
"""

from __future__ import annotations

from jinja2 import Template

from .models import JobPosting

TEMPLATE = Template(
    """\
Dear Hiring Team at {{ employer }},

I am writing to express my interest in the {{ title }} position in {{ location }}. \
I am a board-eligible/certified hospitalist with {{ years_experience }} years of \
hospital medicine experience, currently practicing at {{ current_employer }}, where \
I am also a partner in our group.

{% for h in highlights -%}
- {{ h }}
{% endfor %}
I am relocating to the {{ target_area }} area {{ relocation_reason }}, and this \
opportunity caught my attention{% if schedule_note %} ({{ schedule_note }}){% endif %}. \
I am open to full-time, part-time, or per-diem arrangements.

I would welcome the chance to discuss how my experience could contribute to your \
hospital medicine program. My CV is attached for your review.

Sincerely,
{{ name }}
{{ email }}{% if phone %} | {{ phone }}{% endif %}
"""
)


def draft_cover_letter(posting: JobPosting, resume: dict) -> str:
    schedule_note = None
    for pref in ("7 on 7 off", "7 on/7 off", "7on7off", "day shift"):
        if pref.lower() in f"{posting.title} {posting.description}".lower():
            schedule_note = f"I saw the posting mentions {pref}, which matches my preference"
            break

    return TEMPLATE.render(
        employer=posting.employer,
        title=posting.title,
        location=posting.location or "the Orange County area",
        years_experience=resume.get("years_experience", ""),
        current_employer=resume.get("current_employer", ""),
        highlights=resume.get("highlights", []),
        target_area="Orange County",
        relocation_reason=resume.get("relocation_reason", "for family reasons"),
        schedule_note=schedule_note,
        name=resume.get("name", ""),
        email=resume.get("email", ""),
        phone=resume.get("phone", ""),
    )
