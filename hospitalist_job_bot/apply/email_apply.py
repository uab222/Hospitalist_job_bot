"""Sends an application email with the drafted cover letter and CV attached.

Only ever called for a job you've explicitly marked 'approved' -- see
cli.py's `apply` command. Requires SMTP_HOST/PORT/USER/PASSWORD env vars
(see README setup step 4). Uses an app password, not your real account
password, if your provider is Gmail/Outlook/etc.
"""

from __future__ import annotations

import mimetypes
import smtplib
from email.message import EmailMessage
from pathlib import Path

from ..config import Config


class EmailApplyError(Exception):
    pass


def send_application_email(
    to_email: str,
    subject: str,
    body: str,
    resume_path: Path,
    config: Config,
) -> None:
    secrets = config.secrets
    if not (secrets.smtp_host and secrets.smtp_user and secrets.smtp_password):
        raise EmailApplyError(
            "SMTP not configured. Set SMTP_HOST, SMTP_USER, SMTP_PASSWORD (and "
            "optionally SMTP_PORT) to enable emailed applications."
        )

    msg = EmailMessage()
    msg["From"] = secrets.smtp_user
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content(body)

    resume_path = Path(resume_path)
    if resume_path.exists():
        mime_type, _ = mimetypes.guess_type(str(resume_path))
        maintype, subtype = (mime_type or "application/octet-stream").split("/", 1)
        msg.add_attachment(
            resume_path.read_bytes(),
            maintype=maintype,
            subtype=subtype,
            filename=resume_path.name,
        )
    else:
        raise EmailApplyError(
            f"Resume file not found at {resume_path}. Add your CV (see resume/README.md) "
            "and set resume_file in resume.yaml before applying."
        )

    with smtplib.SMTP(secrets.smtp_host, secrets.smtp_port) as server:
        server.starttls()
        server.login(secrets.smtp_user, secrets.smtp_password)
        server.send_message(msg)
