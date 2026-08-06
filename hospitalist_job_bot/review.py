"""Builds a human-readable review queue (data/review.md) from the store."""

from __future__ import annotations

import json
from pathlib import Path

from .config import DEFAULT_REVIEW_PATH
from .models import STATUS_APPLIED, STATUS_APPROVED, STATUS_MANUAL_NEEDED, STATUS_NEW, STATUS_REVIEWED
from .store import JobStore

PENDING_STATUSES = (STATUS_NEW, STATUS_REVIEWED)


def build_review_report(store: JobStore, output_path: Path = DEFAULT_REVIEW_PATH) -> Path:
    pending = [j for j in store.list_by_status() if j["status"] in PENDING_STATUSES]
    approved = [j for j in store.list_by_status(STATUS_APPROVED)]
    manual = [j for j in store.list_by_status(STATUS_MANUAL_NEEDED)]
    applied = [j for j in store.list_by_status(STATUS_APPLIED)]

    lines = ["# Hospitalist Job Search -- Review Queue", ""]

    lines.append(f"**{len(pending)} new match(es) awaiting your review.**")
    lines.append("")
    lines.append(
        "For each job you like, run `python -m hospitalist_job_bot approve <job_id>`, "
        "then `python -m hospitalist_job_bot apply <job_id>`."
    )
    lines.append("")

    def render_job(job: dict, show_cover_letter: bool = True) -> list:
        reasons = json.loads(job["match_reasons"] or "[]")
        out = [
            f"## {job['title']} -- {job['employer']}",
            f"- **job_id:** `{job['job_id']}`",
            f"- **score:** {job['score']}/100",
            f"- **location:** {job['location']}",
            f"- **employment type:** {job['employment_type'] or 'unspecified'}",
            f"- **source:** {job['source']}",
            f"- **link:** {job['url']}",
            f"- **why it matched:** {'; '.join(reasons)}",
        ]
        if job.get("apply_email"):
            out.append(f"- **apply email:** {job['apply_email']}")
        if show_cover_letter and job.get("cover_letter"):
            out.append("")
            out.append("<details><summary>Drafted cover letter</summary>")
            out.append("")
            out.append("```")
            out.append(job["cover_letter"])
            out.append("```")
            out.append("</details>")
        out.append("")
        return out

    for job in pending:
        lines.extend(render_job(job))

    if approved:
        lines.append("---")
        lines.append("## Approved, not yet applied")
        lines.append("")
        for job in approved:
            lines.extend(render_job(job, show_cover_letter=False))

    if manual:
        lines.append("---")
        lines.append(
            "## Needs manual submission (no application email found -- use the link above)"
        )
        lines.append("")
        for job in manual:
            lines.extend(render_job(job, show_cover_letter=True))

    if applied:
        lines.append("---")
        lines.append("## Already applied")
        lines.append("")
        for job in applied:
            lines.append(f"- {job['title']} -- {job['employer']} (`{job['job_id']}`)")

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines), encoding="utf-8")
    return output_path
