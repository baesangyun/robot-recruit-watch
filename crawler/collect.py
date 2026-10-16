# /**************************************************************
#  * @name 국내 로봇기업 채용 자동수집기
#  * @file crawler/collect.py
#  * @version v01
#  * @description 공식 채용페이지/공개 공고 피드 수집, 신규·진행·마감 판정, 기업별 검사 기록
#  * @author OpenAI ChatGPT
#  * @date 2026-10-16
#  * @Revisions
#  * - 현재 버전:
#  *   1) 30개 기업 모니터링 및 출처별 신뢰도/수집 상태 분리
#  *   2) 최초 스냅샷은 신규로 오판하지 않고 검증된 소스에만 종료 처리
#  * - 이전 버전:
#  *   1) 최초 작성
#  **************************************************************/
"""Conservative public career page monitor; no login, captcha bypass, or fictitious jobs."""
from __future__ import annotations

import argparse
import email.utils
import hashlib
import json
import logging
import re
import time
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = ROOT / "docs/data/jobs.json"
ROSTER_FILE = ROOT / "companies.json"
KST = timezone(timedelta(hours=9))
USER_AGENT = "RobotRecruitWatch/1.0 (public career pages; daily scheduled check; no authentication)"
LOG = logging.getLogger("robot_recruit")
VALID_SCHEMES = {"https", "http"}
MAX_JOBS_PER_SOURCE = 90
FIND_PATTERNS = {
    "ninehire": ["a[href*='/job_posting/']"],
    "greeting": ["a[href*='/ko/job/']", "a[href*='/job/']", "a[href*='/jobs/']"],
    "rainbow": ["a[href*='uid='][href*='mod=document']"],
    "angel": ["a[href*='/recruit/notice/']"],
    "yujin": ["a[href*='/company/recruit/']"],
}
ROLE_RULES = [
    ("유지보수·CS", r"유지보수|A/S|\bCS\b|C/S|서비스엔지니어|field engineer|field service|필드엔지니어|고객지원|기술지원|technical support|customer success|AS / CS|설치.?시운전|현장.?엔지니어"),
    ("SI·자동화", r"\bSI\b|시스템통합|자동화|인티그레이션|system integration|commissioning|application engineer|프로젝트.?PM|PLC|공정설계"),
    ("영업·사업", r"영업|business development|account manager|sales|마케팅|사업개발|해외사업"),
    ("SW·AI", r"소프트웨어|software|\bSW\b|\bAI\b|인공지능|알고리즘|ROS|SLAM|모션.?제어|백엔드|backend|frontend|프론트엔드|C\+\+|navigation|vision|ML engineer|machine learning"),
    ("HW·기구", r"하드웨어|hardware|\bHW\b|기구|전장|회로|전기|기계|firmware|펌웨어|mechanical|electronics|actuator|액추에이터"),
    ("생산·품질", r"생산|구매|SCM|품질|QA|QC|manufacturing|quality|supply|procurement|검사"),
    ("관리·기타", r"경영|재무|인사|회계|기획|지원|legal|법무|HR|총무|전략|IR|IT manager"),
]
REGIONS = [
    ("서울",r"서울|마곡|강서구|강남|구로|성수|seoul"),
    ("경기",r"경기|분당|판교|용인|성남|수원|광교|하남|화성|평택|안산|시흥|gyeonggi|pangyo"),
    ("인천",r"인천|송도|incheon"),
    ("대전",r"대전|유성|daejeon"),
    ("세종",r"세종|sejong"),
    ("대구",r"대구|현풍|달성|daegu"),
    ("부산",r"부산|busan"),
    ("경남",r"창원|경남|김해|changwon"),
    ("충청",r"충북|충남|천안|청주|아산|음성"),
    ("전라",r"전북|전남|광주|전주|광양|군산|gwangju"),
    ("경북",r"경북|구미|포항|경주"),
    ("해외",r"미국|일본|독일|싱가포르|usa|japan|global|singapore"),
]
HIRE_HINT = re.compile(r"채용|모집|인재|엔지니어|개발자|연구원|설계|manager|engineer|developer|직무|인턴|담당|specialist|intern|품질|영업|기술지원|연구|기획|서비스|로봇|\bCS\b", re.I)
NOT_JOB = re.compile(r"채용공고$|채용정보$|채용안내$|공지사항|채용절차|FAQ|privacy|career$|recruit$|지원방법|접수방법|기업문화|회원가입|로그인|목록|더보기|홈페이지|인재풀 등록$|전체 공고", re.I)
NO_OPENINGS = re.compile(r"(현재|진행.?중인|등록된).{0,12}(채용|공고).{0,15}(없|0건)|no (open|available|current) (positions|jobs|openings)", re.I)
DATE_RX = re.compile(r"(20\d\d)[.\-/년]\s*(\d{1,2})[.\-/월]\s*(\d{1,2})")
RSS_HOSTS = ("jobkorea.co.kr", "saramin.co.kr", "wanted.co.kr", "career.greetinghr.com", "ninehire.site", "breezy.hr", "recruit.hd.com", "career.doosan.com", "hanwhain.com", "rainbow-robotics.com", "yujinrobot.com", "angel-robotics.com")


def iso_now() -> str:
    return datetime.now(KST).isoformat(timespec="seconds")


def tidy(text: str) -> str:
    return re.sub(r"\s+", " ", str(text or "")).strip()


def safe_link(url: str) -> bool:
    try:
        u = urllib.parse.urlparse(url)
        return u.scheme.lower() in VALID_SCHEMES and bool(u.hostname) and not u.username and not u.password
    except Exception:
        return False


def host_allowed(url: str, allowed: tuple[str, ...]) -> bool:
    host = (urllib.parse.urlparse(url).hostname or "").lower()
    return any(host == domain or host.endswith("." + domain) for domain in allowed)


def classify_role(text: str) -> str:
    for name, rx in ROLE_RULES:
        if re.search(rx, text or "", re.I):
            return name
    return "기타"


def classify_region(text: str) -> str:
    for name, rx in REGIONS:
        if re.search(rx, text or "", re.I):
            return name
    return "미상"


def normalized_url(url: str) -> str:
    p = urllib.parse.urlsplit(url)
    q = urllib.parse.parse_qsl(p.query, keep_blank_values=False)
    relevant = [(k, v) for k, v in q if k.lower() not in ("utm_source","utm_campaign","utm_medium","fbclid","gclid","ref")]
    return urllib.parse.urlunsplit((p.scheme.lower(), p.netloc.lower(), p.path.rstrip("/") or "/", urllib.parse.urlencode(relevant), ""))


def job_key(company_id: str, link: str) -> str:
    return hashlib.sha256((company_id + "|" + normalized_url(link)).encode()).hexdigest()[:20]


def parse_deadline(text: str) -> str | None:
    # Only parse explicit end-date signals; dates without context are never deadlines.
    match = re.search(r"(?:마감일|접수마감|제출기한|접수기간|~|D-\d+).{0,100}", text or "", re.I)
    if not match:
        return None
    candidates = list(DATE_RX.finditer(match.group(0)))
    if not candidates:
        return None
    m = candidates[-1]
    try:
        return datetime(*map(int, m.groups())).date().isoformat()
    except ValueError:
        return None


def base_job(company: dict, title: str, url: str, *, location: str = "", detail: str = "", deadline: str | None = None, reliability: str = "official") -> dict:
    title = tidy(title)[:150]
    location = tidy(location)[:100]
    return {
        "id": job_key(company["id"], url), "company_id": company["id"], "company": company["name"],
        "title": title, "url": url, "location": location or "미상",
        "region": classify_region(location or detail), "role": classify_role(title),
        "career": "신입·경력" if re.search("신입.*경력|경력.*무관|무관", title+detail, re.I) else ("경력" if re.search("경력|senior|experienced",title+detail,re.I) else ("신입" if re.search("신입|intern|인턴",title+detail,re.I) else "미상")),
        "deadline": deadline or parse_deadline(detail), "verification": reliability,
        "first_seen": None, "last_seen": None, "status": "진행", "new": False, "missing_streak": 0,
    }


def fetch(session: requests.Session, url: str) -> requests.Response:
    if not safe_link(url):
        raise ValueError("접속 URL 형식 오류")
    r = session.get(url, timeout=(7, 22), allow_redirects=True)
    r.raise_for_status()
    if not safe_link(r.url):
        raise ValueError("응답 URL 형식 오류")
    return r


def collect_jsonld(soup: BeautifulSoup, company: dict, base_url: str) -> list[dict]:
    result = []
    for sc in soup.select('script[type="application/ld+json"]'):
        try:
            root = json.loads(sc.string or sc.get_text())
        except (ValueError, TypeError):
            continue
        stack = [root]
        while stack:
            item = stack.pop()
            if isinstance(item, list):
                stack.extend(item)
            elif isinstance(item, dict):
                stack.extend([v for k, v in item.items() if k == "@graph"])
                types = item.get("@type", [])
                if "JobPosting" not in ([types] if isinstance(types, str) else types):
                    continue
                org = item.get("hiringOrganization") or {}
                orgname = org.get("name", "") if isinstance(org, dict) else ""
                if orgname and company["name"].replace(" ", "").lower() not in str(orgname).replace(" ", "").lower():
                    # Group-company naming may differ, but avoid cross-company attribution.
                    continue
                url = urllib.parse.urljoin(base_url, item.get("url", ""))
                if not safe_link(url):
                    continue
                place = item.get("jobLocation") or ""
                if isinstance(place, list): place = place[0] if place else ""
                if isinstance(place, dict):
                    addr = place.get("address", {})
                    place = " ".join(str(addr.get(k,"")) for k in ("addressRegion","addressLocality")) if isinstance(addr, dict) else str(addr)
                valid_through = item.get("validThrough", "")
                deadline = str(valid_through)[:10] if re.match(r"^20\d\d-\d\d-\d\d",str(valid_through)) else None
                result.append(base_job(company, item.get("title", ""), url, location=str(place), deadline=deadline, detail=tidy(BeautifulSoup(item.get("description", ""), "html.parser").get_text(" "))))
    return [j for j in result if j["title"]]


def anchor_title(a) -> str:
    for sel in ("h1","h2","h3","h4",".title",".job-title","[class*='title']"):
        elem = a.select_one(sel)
        if elem:
            title = tidy(elem.get_text(" ",strip=True))
            if title: return title
    for attr in ("title","aria-label"):
        if a.get(attr): return tidy(a[attr])
    text = tidy(a.get_text(" ", strip=True))
    # For cards with metadata, prefer first meaningful line.
    lines = [tidy(x) for x in a.stripped_strings]
    lines = [x for x in lines if len(x) > 3 and x not in ("채용 시 마감","정규직","계약직","신입","경력")]
    return (lines[0] if lines else text)[:120]


def parse_listing(company: dict, html: str, base_url: str) -> tuple[list[dict], bool]:
    soup = BeautifulSoup(html, "html.parser")
    structured = collect_jsonld(soup, company, base_url)
    found = {j["id"]: j for j in structured}
    adapter = company["adapter"]
    base_hostname = (urllib.parse.urlparse(base_url).hostname or "").lower()
    for css in FIND_PATTERNS.get(adapter, []):
        for a in soup.select(css):
            href = urllib.parse.urljoin(base_url, a.get("href", ""))
            if not safe_link(href) or (urllib.parse.urlparse(href).hostname or "").lower() != base_hostname:
                continue
            if adapter == "angel" and not re.search(r"/notice/\d+(?:\?|$)",href):
                continue
            if adapter == "yujin" and any(x in href for x in ("/author/", "/page/", "/category/")):
                continue
            if adapter == "yujin" and urllib.parse.urlsplit(href).path.rstrip("/") == "/company/recruit":
                continue
            title = anchor_title(a)
            if adapter == "angel":
                fragments = [tidy(x) for x in a.stripped_strings]
                candidates = [x for x in fragments if len(x) > 8 and not re.search(r"채용 시 마감|플래닛|조회수|^.+Team$", x, re.I)]
                if candidates:
                    title = max(candidates, key=len)[:115]
            if (not HIRE_HINT.search(title) and not (adapter in ("angel","greeting") and len(title)>8)) or NOT_JOB.search(title):
                continue
            parent = a.find_parent(["article","li","section"]) or a.parent
            context = tidy(parent.get_text(" ",strip=True))[:400] if parent else title
            if len(title)>115 and context:
                # Avoid cards that collapse all metadata into a title.
                title = title[:115]
            job = base_job(company, title, href, detail=context)
            # Archive-style boards can retain old posts for years; do not call them active.
            if adapter == "yujin" or (adapter == "rainbow" and not re.search(r"채용중|상시채용", context)):
                job["verification"] = "official_unverified"
                job["status"] = "확인필요"
            found[job["id"]] = job
    return list(found.values())[:MAX_JOBS_PER_SOURCE], bool(NO_OPENINGS.search(soup.get_text(" ",strip=True)))


def parse_breezy(company: dict, payload) -> list[dict]:
    if not isinstance(payload, list):
        raise ValueError("Breezy 공개 피드의 데이터 형식이 변경되었습니다")
    out = []
    for p in payload[:MAX_JOBS_PER_SOURCE]:
        if not isinstance(p, dict): continue
        title = p.get("name") or p.get("title") or ""
        url = p.get("url") or p.get("link") or ""
        if not safe_link(str(url)):
            slug = p.get("friendly_id") or p.get("id")
            if slug: url = company["url"].rstrip("/") + "/p/" + str(slug)
        if not title or not safe_link(str(url)): continue
        loc = p.get("location") or {}
        if isinstance(loc, dict):
            loc = " ".join(str(loc.get(key) or "") for key in ("name", "city", "country"))
        j = base_job(company, title, url, location=str(loc), detail=str(p.get("department", "")))
        out.append(j)
    return out


def scrape_official(session: requests.Session, company: dict) -> tuple[list[dict], str, str, bool]:
    adapter, url = company.get("adapter", "search"), company.get("url")
    if not url:
        return [], "미설정", "확인된 공식 채용 링크 미설정", False
    try:
        if adapter == "breezy":
            api = company["url"].rstrip("/") + "/json"
            response = fetch(session, api)
            data = parse_breezy(company, response.json())
            return data, "성공", "공개 공고 JSON 확인", True
        response = fetch(session, url)
        if adapter in FIND_PATTERNS:
            jobs, definitive_empty = parse_listing(company, response.text, response.url)
            if jobs or definitive_empty:
                return jobs, "성공", "공식 목록 공고 판독" if jobs else "공식 목록 공고 0건 명시", True
            return [], "제한", "사이트 접속 성공 · 공고 자동 판독 불가", False
        # These URLs are valid sources but are not assumed to offer a machine-readable listing.
        jobs = collect_jsonld(BeautifulSoup(response.text, "html.parser"), company, response.url)
        if jobs:
            return jobs, "성공", "JobPosting 구조화 데이터 판독", True
        return [], "제한", "사이트 접속 성공 · 기업별 목록 수집 규칙 추가 필요", False
    except (requests.RequestException, ValueError, json.JSONDecodeError) as e:
        return [], "실패", (type(e).__name__+": "+str(e))[:170], False


def rss_candidates(session: requests.Session, company: dict) -> tuple[list[dict], str]:
    # Search results are leads, never proof that a job is still open.
    query = '"' + company["name"] + '" 채용 채용공고 2026'
    url = "https://www.bing.com/search?format=rss&q=" + urllib.parse.quote(query)
    try:
        r = fetch(session, url)
        root = ET.fromstring(r.content)
        seen = set()
        jobs = []
        for el in root.findall("./channel/item"):
            title = tidy(el.findtext("title") or "")
            link = tidy(el.findtext("link") or "")
            desc = tidy(BeautifulSoup(el.findtext("description") or "", "html.parser").get_text(" "))
            if not safe_link(link) or not host_allowed(link, RSS_HOSTS): continue
            if company["name"].replace(" ", "").lower() not in (title+" "+desc).replace(" ", "").lower(): continue
            if not HIRE_HINT.search(title) or NOT_JOB.search(title): continue
            if normalized_url(link) in seen: continue
            seen.add(normalized_url(link))
            j = base_job(company, title, link, detail=desc, reliability="search_unverified")
            j["status"] = "확인필요"
            jobs.append(j)
        return jobs[:12], "검색 완료" if jobs else "검색 결과 없음/확인 불가"
    except (requests.RequestException, ET.ParseError, ValueError) as e:
        return [], "검색 실패: " + str(e)[:95]


def load_previous() -> dict:
    if not DATA_FILE.exists(): return {}
    try:
        raw = json.loads(DATA_FILE.read_text(encoding="utf-8"))
        return raw if isinstance(raw, dict) else {}
    except (ValueError,OSError):
        return {}


def reconcile(old_data: dict, discovered: list[dict], statuses: dict[str, dict], at: str) -> list[dict]:
    old = {j["id"]: j for j in old_data.get("jobs", []) if isinstance(j, dict) and "id" in j}
    fresh_ids = set()
    baseline = not bool(old_data.get("last_run"))
    today = datetime.fromisoformat(at).date()
    for job in discovered:
        job_id = job["id"]
        if job_id in fresh_ids: continue
        fresh_ids.add(job_id)
        prev = old.get(job_id)
        job["first_seen"] = (prev or {}).get("first_seen") or at
        job["last_seen"] = at
        job["missing_streak"] = 0
        if job["verification"] != "official":
            # Never silently elevate an archived board or search result to an active posting.
            if prev and prev.get("verification") == "official" and job["verification"] == "search_unverified":
                job["verification"] = "official"
                job["status"] = "진행"
            else:
                job["status"] = "확인필요"
        else:
            job["status"] = "진행"
        if job.get("deadline"):
            try:
                if datetime.fromisoformat(job["deadline"]).date() < today:
                    job["status"] = "마감"
            except ValueError:
                job["deadline"] = None
        job["new"] = not baseline and prev is None and job["verification"] == "official"
        old[job_id] = job
    for job_id, job in old.items():
        if job_id in fresh_ids: continue
        src = statuses.get(job.get("company_id", ""), {})
        if job.get("status") == "마감": continue
        if job.get("deadline"):
            try:
                if datetime.fromisoformat(job["deadline"]).date() < today:
                    job["status"] = "마감"
                    job["new"] = False
                    continue
            except ValueError:
                pass
        # Absence from a verified complete list for two runs is a cautious signal, not proof.
        if src.get("complete") is True and job.get("verification") == "official":
            job["missing_streak"] = int(job.get("missing_streak") or 0) + 1
            if job["missing_streak"] >= 2:
                job["status"] = "확인필요"  # Never falsely claim closed from disappearance alone.
        job["new"] = False
    return sorted(old.values(), key=lambda j:(j["status"]!="진행",not j.get("new", False),j.get("first_seen", "")), reverse=False)


def run(*, with_search: bool = True, session: requests.Session | None = None) -> dict:
    roster = json.loads(ROSTER_FILE.read_text(encoding="utf-8"))
    prev = load_previous()
    now = iso_now()
    session = session or requests.Session()
    session.headers.update({"User-Agent": USER_AGENT, "Accept": "text/html,application/json,application/rss+xml;q=0.7,*/*;q=0.5", "Accept-Language":"ko-KR,ko;q=0.9,en;q=0.7"})
    discovered = []
    statuses = {}
    for company in roster:
        jobs, status, detail, complete = scrape_official(session, company)
        candidates = []
        search_note = "미실행"
        if with_search:
            candidates, search_note = rss_candidates(session, company)
        official_ids = {j["id"] for j in jobs}
        discovered.extend(jobs)
        discovered.extend(j for j in candidates if j["id"] not in official_ids)
        statuses[company["id"]] = {
            "id": company["id"], "name": company["name"], "group": company["group"],
            "sector": company["sector"], "url": company.get("url"),
            "adapter": company["adapter"], "status": status, "detail": detail,
            "checked_at": now, "official_count": len(jobs), "candidate_count": len(candidates),
            "search_status": search_note, "complete": complete,
        }
        LOG.info("%-14s %-4s official=%d search=%d %s", company["id"], status, len(jobs), len(candidates), detail)
        time.sleep(0.2)
    jobs = reconcile(prev, discovered, statuses, now)
    result = {"version": "v01", "last_run": now, "timezone": "Asia/Seoul", "companies": list(statuses.values()), "jobs": jobs,
              "history": ([{"time":now, "jobs_official":sum(1 for j in jobs if j.get("verification")=="official" and j.get("status")=="진행"),
                           "success":sum(s["status"]=="성공" for s in statuses.values()),
                           "limited":sum(s["status"] in ("제한","미설정") for s in statuses.values()),
                           "failed":sum(s["status"]=="실패" for s in statuses.values())}] + prev.get("history", []))[:30]}
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp = DATA_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(DATA_FILE)
    LOG.info("Wrote %s: %d jobs / %d companies", DATA_FILE, len(jobs), len(roster))
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-search",action="store_true",help="disable RSS discovery when testing")
    parser.add_argument("--verbose",action="store_true")
    args = parser.parse_args()
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO,format="%(asctime)s %(levelname)s %(message)s")
    run(with_search=not args.no_search)
