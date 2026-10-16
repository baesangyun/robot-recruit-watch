# /**************************************************************
#  * @name 국내 로봇기업 채용 자동수집기
#  * @file crawler/collect.py
#  * @version v03
#  * @description 공식 채용페이지/공개 공고 피드 수집, 신규·진행·마감 판정, 기업별 검사 기록
#  * @author OpenAI ChatGPT
#  * @date 2026-10-16
#  * @Revisions
#  * - 현재 버전:
#  *   1) v03: 채용전문사이트 후보 및 승인 API 연동, 목록 가독성·정렬·수집 오류 확인
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
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
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
    "ninehire": ["a[href*='/job_posting/']", "a[href*='/jobs/']"],
    "greeting": ["a[href*='/ko/o/']", "a[href*='/o/']", "a[href*='/ko/job/']", "a[href*='/job/']", "a[href*='/jobs/']"],
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
    ("제주",r"제주|jeju"),
    ("강원",r"강원|춘천|원주|강릉|gangwon"),
    ("울산",r"울산|ulsan"),
    ("해외",r"미국|일본|독일|싱가포르|아일랜드|베트남|중국|인도|대만|영국|캐나다|프랑스|호주|usa|japan|singapore|ireland|vietnam|china|taiwan|india|germany|canada|australia|tokyo|dublin|hanoi|xiamen"),
]
HIRE_HINT = re.compile(r"채용|모집|인재|엔지니어|개발자|연구원|설계|manager|engineer|developer|직무|인턴|담당|specialist|intern|품질|영업|기술지원|연구|기획|서비스|로봇|\bCS\b", re.I)
NOT_JOB = re.compile(r"채용공고$|채용정보$|채용안내$|공지사항|채용절차|FAQ|privacy|career$|recruit$|지원방법|접수방법|기업문화|회원가입|로그인|목록|더보기|홈페이지|인재풀 등록$|전체 공고", re.I)
NO_OPENINGS = re.compile(r"(현재|진행.?중인|등록된).{0,12}(채용|공고).{0,15}(없|0건)|no (open|available|current) (positions|jobs|openings)", re.I)
DATE_RX = re.compile(r"(20\d\d)[.\-/년]\s*(\d{1,2})[.\-/월]\s*(\d{1,2})")
BOARD_SITES = {"잡코리아": "jobkorea.co.kr", "사람인": "saramin.co.kr", "인크루트": "incruit.com"}
VERIFIED_SOURCES = {"official", "platform_api"}
RSS_HOSTS = ("jobkorea.co.kr", "saramin.co.kr", "incruit.com", "wanted.co.kr", "career.greetinghr.com", "ninehire.site", "breezy.hr", "recruit.hd.com", "career.doosan.com", "hanwhain.com", "rainbow-robotics.com", "yujinrobot.com", "angel-robotics.com")


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


# Worksite country, not company headquarters or job-title keywords. Uncertain locations remain unknown.
DOMESTIC_COUNTRY = re.compile(r"(?:\b(?:KR|KOR|Korea|South Korea|Republic of Korea)\b|대한민국|한국|서울|경기|인천|대전|세종|대구|부산|울산|광주|제주|강원|충북|충남|전북|전남|경북|경남|수원|용인|성남|판교|화성|포항|창원|청주|천안|안산|하남|마곡|송도|seoul|incheon|suwon|daejeon|busan|daegu|gyeonggi|pangyo|jeju)", re.I)
OVERSEAS_COUNTRY = re.compile(r"(?:\b(?:US|USA|IE|JP|CN|VN|TW|SG|IN|GB|UK|DE|FR|CA|AU|JPN|CHN|SGP|Vietnam|Ireland|Japan|China|Taiwan|Singapore|Germany|France|Canada|Australia|India)\b|미국|일본|중국|베트남|아일랜드|대만|싱가포르|독일|프랑스|캐나다|호주|영국|tokyo|dublin|hanoi|xiamen|san francisco|sunnyvale|boston|new york|london)", re.I)


def classify_work_scope(location: str, region: str = "미상") -> str:
    """국내 / 해외 / 미상. 직무 제목(예: 해외영업)으로 해외 근무를 추정하지 않음."""
    location = tidy(location)
    if location in ("", "미상", "원격", "Remote", "remote"):
        return "국내" if region not in ("미상", "해외") else "미상"
    if OVERSEAS_COUNTRY.search(location):
        return "해외"
    if DOMESTIC_COUNTRY.search(location):
        return "국내"
    return "국내" if region not in ("미상", "해외") else ("해외" if region == "해외" else "미상")


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
        "region": classify_region(location or detail), "work_scope": classify_work_scope(location, classify_region(location)), "role": classify_role(title),
        "career": "신입·경력" if re.search("신입.*경력|경력.*무관|무관", title+detail, re.I) else ("경력" if re.search("경력|senior|experienced",title+detail,re.I) else ("신입" if re.search("신입|intern|인턴",title+detail,re.I) else "미상")),
        "deadline": deadline or parse_deadline(detail), "verification": reliability,
        "source": "공식 채용페이지" if reliability == "official" else "검색 후보", "other_sources": [],
        "first_seen": None, "last_seen": None, "status": "진행", "new": False, "missing_streak": 0,
    }


def fetch(session: requests.Session, url: str) -> requests.Response:
    if not safe_link(url):
        raise ValueError("접속 URL 형식 오류")
    r = session.get(url, timeout=(7, 22), allow_redirects=True)
    if r.status_code in (429, 503):
        # Respect a short server Retry-After; do not bypass long rate limits.
        retry_header = tidy(r.headers.get("Retry-After", ""))
        delay = min(7, max(2, int(retry_header))) if retry_header.isdecimal() and int(retry_header) <= 7 else 0
        if delay:
            time.sleep(delay)
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
            parts = []
            for key in ("name", "city", "country"):
                val = loc.get(key) or ""
                if isinstance(val, dict): val = val.get("name") or val.get("id") or ""
                val = tidy(val)
                if val and not any(val.lower() in x.lower() for x in parts): parts.append(val)
            loc = " / ".join(parts)
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
    except requests.exceptions.SSLError as e:
        # Certificate warnings must NOT be bypassed using verify=False.
        return [], "보안오류", "HTTPS 인증서 확인 실패 · 보안 경고 우회 금지 · 대체 채용 링크 확인", False
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


def board_search_url(platform: str, company_name: str) -> str:
    """Public search index query only; not a portal content scraper or authorized API."""
    domain = BOARD_SITES[platform]
    query = 'site:' + domain + ' "' + company_name + '" 채용'
    return "https://www.bing.com/search?format=rss&q=" + urllib.parse.quote(query)


def portal_links(company_name: str) -> dict[str,str]:
    # Deep-link into each site's public search screen; never assume results are currently open.
    q=urllib.parse.quote(company_name)
    return {
        "잡코리아": "https://www.jobkorea.co.kr/Search/?stext=" + q,
        "사람인": "https://www.saramin.co.kr/zf_user/search/recruit?searchword=" + q,
        "인크루트": "https://search.incruit.com/list/search.asp?col=job&kw=" + q,
    }


def company_identity(text: str) -> str:
    """Normalize common legal entity wrappers but DO NOT equate affiliates."""
    value=tidy(text).lower().replace('㈜','').replace('(주)','').replace('주식회사','')
    return re.sub(r'[^가-힣a-z0-9]+','',value)


def rss_board_candidates(company: dict, platform: str, session: requests.Session) -> tuple[list[dict],str]:
    # Search engine index is not proof of an active advertisement. Never scrape portal HTML.
    try:
        url=board_search_url(platform,company['name'])
        r=session.get(url,timeout=(3,8),allow_redirects=True)
        r.raise_for_status()
        if not safe_link(r.url): raise ValueError('RSS redirect URL invalid')
        tree=ET.fromstring(r.content)
        out=[]; seen=set()
        for el in tree.findall('./channel/item'):
            title=tidy(el.findtext('title') or '')
            link=tidy(el.findtext('link') or '')
            desc=tidy(BeautifulSoup(el.findtext('description') or '', 'html.parser').get_text(' '))
            if not safe_link(link) or not host_allowed(link,(BOARD_SITES[platform],)):
                continue
            # Avoid cross-company attribution: exact company name in title or snippet is mandatory.
            normalized_title=company_identity(title)
            if company_identity(company['name']) not in normalized_title:
                continue
            if not HIRE_HINT.search(title) or NOT_JOB.search(title):
                continue
            canonical=normalized_url(link)
            if canonical in seen: continue
            seen.add(canonical)
            j=base_job(company,title,link,detail=desc,reliability='search_unverified')
            j['source']=platform+' 검색후보'
            j['status']='확인필요'
            out.append(j)
        return out[:12],('검색 후보 '+str(len(out))+'건' if out else '색인 결과 없음/검증 불가')
    except (requests.RequestException,ValueError,ET.ParseError) as e:
        return [],'검색 확인 불가: '+type(e).__name__


def saramin_api_candidates(session: requests.Session, company: dict, access_key: str) -> tuple[list[dict],str]:
    """Official Saramin search API requires approved key. Strict company matching."""
    if not access_key: return [],'API 키 미설정(검색 링크 이용)'
    try:
        r=fetch(session,'https://oapi.saramin.co.kr/job-search?'+urllib.parse.urlencode({
            'access-key':access_key,'keywords':company['name'],'count':75,'sort':'pd'}))
        data=r.json()
        if 'result' in data:
            return [],'API 오류: '+tidy(data['result'].get('message',''))[:90]
        records=(data.get('jobs') or {}).get('job') or []
        if isinstance(records,dict):records=[records]
        out=[]
        for item in records:
            employer=((item.get('company') or {}).get('detail') or {}).get('name','')
            if company_identity(employer)!=company_identity(company['name']):continue
            if str(item.get('active',0))!='1':continue
            position=item.get('position') or {}
            title=tidy(position.get('title',''))
            url=item.get('url','')
            if not title or not safe_link(url) or not host_allowed(url,('saramin.co.kr',)):continue
            area=(position.get('location') or {}).get('name','')
            deadline=None
            end=item.get('expiration-timestamp')
            if end and str(end).isdigit():
                deadline=datetime.fromtimestamp(int(end),KST).date().isoformat()
            job=base_job(company,title,url,location=area,deadline=deadline,reliability='platform_api')
            job['source']='사람인 API (진행 확인)'
            out.append(job)
        return out,'API '+str(len(out))+'건 검증(해당기업 일치)'
    except (requests.RequestException,ValueError,TypeError,OverflowError,KeyError) as e:
        return [],'API 확인 실패: '+type(e).__name__


def duplicate_signature(job: dict) -> tuple:
    """Cross-provider conservative matching; leave ambiguous unknown work locations unmerged."""
    title=tidy(job.get('title','')).lower()
    title=re.sub(r'^\[[^]]{1,35}\]\s*','',title)
    title=re.sub(r'\b(?:모집|채용|공고)\b','',title)
    title=re.sub(r'[^가-힣a-z0-9]+','',title)
    loc=tidy(job.get('location',''))
    # Avoid merging different sites' ambiguous postings merely because title matches.
    return job['company_id'],title,job.get('region','미상') if loc!='미상' else job.get('id')


def deduplicate_sources(discovered: list[dict]) -> list[dict]:
    # Keep one job per stable ID, preserve alternate source URLs and prefer verified official.
    priorities={'official':0,'platform_api':1,'search_unverified':2,'official_unverified':3}
    ordered=sorted(discovered,key=lambda j:priorities.get(j.get('verification'),9))
    out={}; signatures={}
    for j in ordered:
        ident=duplicate_signature(j)
        if ident in signatures:
            prev=out[signatures[ident]]
            if prev['url']!=j['url'] and not any(x.get('url')==j['url'] for x in prev['other_sources']):
                prev['other_sources'].append({'source':j.get('source','대체 출처'),'url':j['url']})
            continue
        if j['id'] in out: continue
        signatures[ident]=j['id']
        out[j['id']]=j
    return list(out.values())


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
        if job["verification"] not in VERIFIED_SOURCES:
            # Never silently elevate an archived board or search result to an active posting.
            if prev and prev.get("verification") in VERIFIED_SOURCES and job["verification"] == "search_unverified":
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
        job["new"] = not baseline and prev is None and job["verification"] in VERIFIED_SOURCES
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
    for j in old.values():
        # Backfill worksite classification for v01 history without dropping old jobs.
        j["work_scope"] = classify_work_scope(j.get("location", ""), j.get("region", "미상"))
    return sorted(old.values(), key=lambda j:(j["status"]!="진행",not j.get("new", False),j.get("first_seen", "")), reverse=False)


def run(*, with_search: bool = True, session: requests.Session | None = None) -> dict:
    roster = json.loads(ROSTER_FILE.read_text(encoding="utf-8"))
    prev = load_previous()
    now = iso_now()
    session = session or requests.Session()
    session.headers.update({"User-Agent": USER_AGENT, "Accept": "text/html,application/json,application/rss+xml;q=0.7,*/*;q=0.5", "Accept-Language":"ko-KR,ko;q=0.9,en;q=0.7"})
    discovered = []
    statuses = {}
    saramin_key=os.environ.get('SARAMIN_ACCESS_KEY','').strip()
    # Search indexes provide candidates only. No passwords, cookie replay, or blocked-site bypass.
    def fetch_boards(company):
        local=requests.Session()
        local.headers.update(session.headers)
        found=[]; notes={}
        for board in BOARD_SITES:
            matches,note=rss_board_candidates(company,board,local)
            found.extend(matches)
            notes[board]=note
        if saramin_key:
            verified,note=saramin_api_candidates(local,company,saramin_key)
            found.extend(verified)
            notes['사람인 API']=note
        else:
            notes['사람인 API']='API 키 미설정(검색후보만 표시)'
        local.close()
        return company['id'],found,notes

    for company in roster:
        official,status,detail,complete=scrape_official(session,company)
        discovered.extend(official)
        statuses[company['id']]={
            'id':company['id'],'name':company['name'],'group':company['group'],
            'sector':company['sector'],'url':company.get('url'),
            'adapter':company['adapter'],'status':status,'detail':detail,
            'checked_at':now,'official_count':len(official),'candidate_count':0,
            'search_status':'검색 미실행','complete':complete,
            'portal_links':portal_links(company['name']),'portal_results':{},
            'alternative_careers_url':company.get('alternative_careers_url'),
            'official_access':'보안 경고' if status=='보안오류' else ('접속 성공' if status in ('성공','제한') else '확인 불가'),
        }
        LOG.info('%-14s %-4s official=%d %s',company['id'],status,len(official),detail)
        time.sleep(0.15)
    if with_search:
        # Bounded parallelism prevents 90 sequential RSS requests from making workflow appear frozen.
        with ThreadPoolExecutor(max_workers=6) as executor:
            futures={executor.submit(fetch_boards,c):c['id'] for c in roster}
            for fut in as_completed(futures):
                company_id=futures[fut]
                try:
                    _,found,notes=fut.result()
                except Exception as exc:
                    found,notes=[],{'오류':type(exc).__name__}
                discovered.extend(found)
                statuses[company_id]['candidate_count']=sum(j['verification']=='search_unverified' for j in found)
                statuses[company_id]['portal_results']=notes
                statuses[company_id]['search_status']='전문 채용사이트 3곳 검색 시도' if notes else '검색 미실행'
    jobs = reconcile(prev, deduplicate_sources(discovered), statuses, now)
    result = {"version": "v03", "last_run": now, "timezone": "Asia/Seoul", "companies": list(statuses.values()), "jobs": jobs,
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
