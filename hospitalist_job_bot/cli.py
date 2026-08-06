"""Command-line entrypoint.

    python -m hospitalist_job_bot search    # fetch + score + draft cover letters
    python -m hospitalist_job_bot review     # write data/review.md
    python -m hospitalist_job_bot list [--status new]
    python -m hospitalist_job_bot approve <job_id>
    python -m hospitalist_job_bot reject <job_id>
    python -m hospitalist_job_bot apply <job_id>     # only for approved jobs
"""

from __future__ import annotations

import argparse
import logging
import sys

from .config import Config, load_resume
from .coverletter import draft_cover_letter
from .matcher import filter_and_score
from .models import (
    STATUS_APPLIED,
    STATUS_APPROVED,
    STATUS_MANUAL_NEEDED,
    STATUS_REJECTED,
)
from .review import build_review_report
from .sources import AdzunaSource, WorkdaySource
from .store import JobStore
from .util import extract_email

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)


def cmd_search(args: argparse.Namespace) -> None:
    config = Config.load()
    resume = load_resume()
    store = JobStore()

    all_postings = []
    for source_cls in (AdzunaSource, WorkdaySource):
        source = source_cls(config)
        found = source.search()
        logger.info("%s: %d raw result(s)", source.name, len(found))
        all_postings.extend(found)

    matched = filter_and_score(all_postings, config)
    logger.info("%d posting(s) matched criteria (score >= %d)", len(matched), config.min_score)

    new_count = 0
    for posting in matched:
        if not posting.apply_email:
            posting.apply_email = extract_email(posting.description)

        is_new = store.upsert(posting)
        if is_new:
            new_count += 1
            cover_letter = draft_cover_letter(posting, resume)
            store.set_cover_letter(posting.job_id, cover_letter)
            if posting.apply_email:
                store.set_apply_email(posting.job_id, posting.apply_email)

    logger.info("%d new posting(s) added to the review queue", new_count)


def cmd_review(args: argparse.Namespace) -> None:
    store = JobStore()
    path = build_review_report(store)
    print(f"Review report written to {path}")


def cmd_list(args: argparse.Namespace) -> None:
    store = JobStore()
    jobs = store.list_by_status(args.status)
    if not jobs:
        print("No jobs found.")
        return
    for job in jobs:
        print(f"[{job['status']:14}] {job['score']:3}  {job['job_id']}  {job['title']} -- {job['employer']} ({job['location']})")


def cmd_approve(args: argparse.Namespace) -> None:
    store = JobStore()
    job = store.get(args.job_id)
    if not job:
        print(f"No job found with id {args.job_id}", file=sys.stderr)
        sys.exit(1)
    store.set_status(args.job_id, STATUS_APPROVED)
    print(f"Approved: {job['title']} -- {job['employer']}")


def cmd_reject(args: argparse.Namespace) -> None:
    store = JobStore()
    job = store.get(args.job_id)
    if not job:
        print(f"No job found with id {args.job_id}", file=sys.stderr)
        sys.exit(1)
    store.set_status(args.job_id, STATUS_REJECTED)
    print(f"Rejected: {job['title']} -- {job['employer']}")


def cmd_apply(args: argparse.Namespace) -> None:
    from pathlib import Path

    from .apply import send_application_email
    from .apply.email_apply import EmailApplyError

    config = Config.load()
    resume = load_resume()
    store = JobStore()

    job = store.get(args.job_id)
    if not job:
        print(f"No job found with id {args.job_id}", file=sys.stderr)
        sys.exit(1)

    if job["status"] != STATUS_APPROVED:
        print(
            f"Job {args.job_id} has status '{job['status']}', not 'approved'. "
            f"Run `approve {args.job_id}` first.",
            file=sys.stderr,
        )
        sys.exit(1)

    if not job["apply_email"]:
        store.set_status(args.job_id, STATUS_MANUAL_NEEDED)
        print(
            f"No application email found for this posting. Marked as needing manual "
            f"submission -- use the link in data/review.md: {job['url']}"
        )
        return

    try:
        send_application_email(
            to_email=job["apply_email"],
            subject=f"Application: {job['title']} -- {resume.get('name', '')}",
            body=job["cover_letter"] or "",
            resume_path=Path(resume.get("resume_file", "")),
            config=config,
        )
    except EmailApplyError as exc:
        print(f"Could not send application: {exc}", file=sys.stderr)
        sys.exit(1)

    store.set_status(args.job_id, STATUS_APPLIED)
    print(f"Application sent to {job['apply_email']} for {job['title']} -- {job['employer']}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="hospitalist_job_bot")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("search", help="Fetch, score, and stage new matches").set_defaults(
        func=cmd_search
    )
    subparsers.add_parser("review", help="Write data/review.md").set_defaults(func=cmd_review)

    list_parser = subparsers.add_parser("list", help="List stored jobs")
    list_parser.add_argument("--status", default=None)
    list_parser.set_defaults(func=cmd_list)

    approve_parser = subparsers.add_parser("approve", help="Approve a job for submission")
    approve_parser.add_argument("job_id")
    approve_parser.set_defaults(func=cmd_approve)

    reject_parser = subparsers.add_parser("reject", help="Reject a job")
    reject_parser.add_argument("job_id")
    reject_parser.set_defaults(func=cmd_reject)

    apply_parser = subparsers.add_parser("apply", help="Submit an approved job's application")
    apply_parser.add_argument("job_id")
    apply_parser.set_defaults(func=cmd_apply)

    return parser


def main(argv: list | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
