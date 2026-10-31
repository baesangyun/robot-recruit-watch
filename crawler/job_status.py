# /**************************************************************
#  * @name 채용공고 마감일·모집상태 확인
#  * @file crawler/job_status.py
#  * @version v01
#  * @description 공개 잡코리아 공고의 접수 종료일과 명시적 마감 안내를 확인하고 기존 공고 상태를 갱신
#  * @author OpenAI ChatGPT
#  * @date 2026-10-31
#  * @Revisions
#  * - 현재 버전:
#  *   1) 공개 상세페이지에서 '마감되었습니다'와 접수기간 종료일을 보수적으로 검출
#  *   2) robots 정책 준수 및 403/429 발생 시 중단, 기존 이력과 미확인 공고 보존
#  * - 이전 버전:
#  *   1) 신규 모듈
#  **************************************************************/
"""JobKorea public detail status checker; no authentication, proxy rotation or access bypass."""
from __future__ import annotations

import logging
import re
import time
import urllib.parse
from datetime import date, datetime, timezone, timedelta

import requests
from bs4 import BeautifulSoup

from crawler.portal_company import can_collect

LOG = logging.getLogger("robot_recruit")
KST = timezone(timedelta(hours=9))
DATE_PART = r"20\d{2}[./-]\d{1,2}[./-]\d{1,2}"
DATE_RANGE = re.compile(
    rf"({DATE_PART})\s*(?:\([^)]{{1,6}}\))?\s*[~～]\s*({DATE_PART})"
)
CLOSED_BADGE = re.compile(
    r"마감되었습니다\.?|접수\s*마감되었습니다\.?|모집이\s*마감되었습니다\.?"
)
DETAIL_PATH = re.compile(r"^/Recruit/GI_Read/(\d+)$", re.I)


def canonical_jobkorea_url(url: str) -> str | None:
    """Only a specific HTTPS JobKorea job detail, not generic search or redirect URLs."""
    try:
        p = urllib.parse.urlsplit(url)
        host = (p.hostname or "").lower()
        if p.scheme != "https" or host not in ("www.jobkorea.co.kr", "m.jobkorea.co.kr", "jobkorea.co.kr"):
            return None
        match = DETAIL_PATH.fullmatch(p.path)
        if not match or p.username or p.password:
            return None
        return "https://www.jobkorea.co.kr/Recruit/GI_Read/" + match.group(1)
    except ValueError:
        return None


def _date(value: str) -> str | None:
    try:
        dt = datetime.strptime(re.sub(r"[./]", "-", value), "%Y-%m-%d").date()
        return dt.isoformat()
    except ValueError:
        return None


def parse_jobkorea_details(html: str) -> dict:
    """Return independent explicit deadline and closed signal.

    Do not confuse '마감일', '조기 마감될 수 있습니다' or 'D-10' with actual closure.
    """
    soup = BeautifulSoup(html or "", "html.parser")
    for tag in soup(["script", "style", "noscript", "template"]):
        tag.decompose()
    text = " ".join(soup.stripped_strings)
    text = re.sub(r"\s+", " ", text)
    deadline = None

    # "기간 2026.08.31(월) ~ 2026.10.30(금)" in JobKorea detail.
    for hint in re.finditer(r"접수기간(?:\s*[/·-]\s*방법)?|지원정보|\b기간\b", text):
        fragment = text[hint.end(): hint.end() + 300]
        period = DATE_RANGE.search(fragment)
        if period:
            deadline = _date(period.group(2))
            if deadline:
                break

    # PC detail may show "마감일 2026.10.30" without a date range.
    if not deadline:
        m = re.search(rf"마감일\s*[:：]?\s*({DATE_PART})", text)
        if m:
            deadline = _date(m.group(1))

    closed = bool(CLOSED_BADGE.search(text))
    return {"deadline": deadline, "explicitly_closed": closed}


def update_jobkorea_statuses(
    session: requests.Session,
    jobs: list[dict],
    *,
    now: datetime | None = None,
    max_checks: int = 40,
) -> dict:
    """Check unverified JobKorea candidates once per URL; never block a full collection.

    Closure requires a passed explicit end date or a positive closed signal.
    Inability to access the page is NOT evidence of closure.
    """
    now = now or datetime.now(KST)
    today = now.astimezone(KST).date()
    candidates = [
        j for j in jobs
        if j.get("status") != "마감" and canonical_jobkorea_url(str(j.get("url", "")))
    ]
    stats = {"checked": 0, "closed": 0, "restricted": False}

    # Known past deadlines already imply closure, no remote request needed.
    for job in candidates:
        due = job.get("deadline")
        if due:
            try:
                if date.fromisoformat(due) < today:
                    job["status"] = "마감"
                    job["new"] = False
                    job["status_evidence"] = "지원 종료일 경과"
                    stats["closed"] += 1
            except ValueError:
                pass
    candidates = [j for j in candidates if j.get("status") != "마감"][:max_checks]
    if not candidates:
        return stats

    allowed, reason = can_collect(session, canonical_jobkorea_url(candidates[0]["url"]))
    if not allowed:
        stats["restricted"] = True
        LOG.info("JobKorea detail checks skipped: %s", reason)
        return stats

    seen = {}
    for job in candidates:
        url = canonical_jobkorea_url(job["url"])
        if url in seen:
            details = seen[url]
        else:
            try:
                resp = session.get(url, timeout=(4, 11), allow_redirects=True)
                if resp.status_code in (401, 403, 429, 503):
                    stats["restricted"] = True
                    LOG.info("JobKorea details restricted: HTTP %d", resp.status_code)
                    break
                resp.raise_for_status()
                # Redirects to login, other job IDs, or non-JobKorea sites are not evidence.
                if canonical_jobkorea_url(resp.url) != url:
                    continue
                details = parse_jobkorea_details(resp.text)
                seen[url] = details
                stats["checked"] += 1
                time.sleep(0.15)
            except (requests.RequestException, ValueError) as exc:
                LOG.info("JobKorea detail unavailable: %s", type(exc).__name__)
                continue

        deadline = details["deadline"]
        if deadline:
            job["deadline"] = deadline
        expired = bool(deadline and date.fromisoformat(deadline) < today)
        if details["explicitly_closed"] or expired:
            job["status"] = "마감"
            job["new"] = False
            job["status_evidence"] = "잡코리아 상세페이지 마감 문구" if details["explicitly_closed"] else "잡코리아 접수기간 종료"
            stats["closed"] += 1
        if deadline or details["explicitly_closed"]:
            job["status_checked_at"] = now.isoformat(timespec="seconds")
    return stats
