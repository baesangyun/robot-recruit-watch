# /**************************************************************
#  * @name 채용전문사이트 기업별 공고 수집
#  * @file crawler/portal_company.py
#  * @version v04
#  * @description 공개 기업별 목록에서 개별 공고 링크만 수집
#  * @author OpenAI ChatGPT
#  * @date 2026-10-16
#  * @Revisions
#  * - 현재 버전:
#  *   1) 기업별 공개 목록의 개별 공고 링크 추출
#  *   2) robots 및 HTTPS 검증 준수, 실패 시 오류 기록
#  * - 이전 버전:
#  *   1) 새 파일
#  **************************************************************/
from __future__ import annotations
import re
import urllib.parse
import urllib.robotparser
import requests
from bs4 import BeautifulSoup

SITES={'잡코리아':'jobkorea.co.kr','사람인':'saramin.co.kr','인크루트':'incruit.com'}
USER_AGENT='RobotRecruitWatch/1.0 (public career pages; daily scheduled check; no authentication)'
URL_PATTERNS={
 '잡코리아':re.compile(r'/Recruit/GI_Read/\d+',re.I),
 '사람인':re.compile(r'/zf_user/jobs/(?:relay/)?view',re.I),
 '인크루트':re.compile(r'/jobdb_info/(?:jobpost|joblist)',re.I),
}

def valid_site(url,platform):
    p=urllib.parse.urlsplit(url)
    host=(p.hostname or '').lower()
    dom=SITES.get(platform,'')
    return bool(dom and p.scheme=='https' and (host==dom or host.endswith('.'+dom))
                and not p.username and not p.password)

def job_link(url,platform):
    if not valid_site(url,platform):return False
    p=urllib.parse.urlsplit(url)
    if not URL_PATTERNS[platform].search(p.path):return False
    if platform=='사람인' and not re.search(r'(?:^|&)rec_idx=\d+',p.query):return False
    return True

def tidy(text):
    return re.sub(r'\s+',' ',str(text or '')).strip()

def can_collect(session,url):
    parts=urllib.parse.urlsplit(url)
    robots=f'{parts.scheme}://{parts.netloc}/robots.txt'
    try:
        r=session.get(robots,timeout=(4,8),allow_redirects=True)
        if r.status_code in (401,403):return False,'robots 접근 제한'
        if r.status_code in (404,410):return True,'robots 파일 없음'
        r.raise_for_status()
        if urllib.parse.urlsplit(r.url).hostname != parts.hostname:
            return False,'robots 리다이렉션 확인 불가'
        parser=urllib.robotparser.RobotFileParser()
        parser.parse(r.text.splitlines())
        if not parser.can_fetch(USER_AGENT,url):return False,'robots 자동 접근 제한'
        return True,'robots 허용'
    except (requests.RequestException,ValueError) as e:
        return False,'robots 확인 실패: '+type(e).__name__

def parse_public_company_listing(html,platform,page_url):
    soup=BeautifulSoup(html,'html.parser')
    headings=soup.find_all(['h1','h2','h3','h4','h5','h6'])
    start=next((h for h in headings if re.search(
        r'진행중인 채용정보|진행중 공고|진행 중 공고|진행중인 채용',
        h.get_text(' ',strip=True))),None)
    if start is None:return []
    out=[];urls=set()
    for item in start.next_elements:
        if getattr(item,'name',None) in ('h1','h2','h3','h4','h5','h6') and item is not start:
            if re.search(r'마감된 공고|지난 공고|동종업계|최근 본|고객센터|마감된 채용',
                         item.get_text(' ',strip=True)):break
        if getattr(item,'name',None)!='a' or not item.get('href'):continue
        url=urllib.parse.urljoin(page_url,item['href'])
        if not job_link(url,platform):continue
        link_text=tidy(item.get_text(' ',strip=True))
        if not link_text or re.search(r'마감\s*\(|접수마감|마감되었습니다',link_text):continue
        title=re.split(r'\s+(?:신입·경력|경력무관|경력|신입|인턴|서울|경기|부산|인천|대전|대구|충남|충북|경북|경남|D-\d+)',link_text,maxsplit=1)[0]
        title=re.sub(r'\s*(?:스크랩|입사지원)','',title).strip()
        if len(title)<5:continue
        if url in urls:continue
        urls.add(url)
        context=tidy(item.parent.get_text(' ',strip=True)) if item.parent else link_text
        loc=re.search(r'서울|경기|인천|부산|대전|대구|세종|광주|울산|충북|충남|전북|전남|경북|경남|제주|강원',context)
        out.append({'title':title,'url':url,'location':loc.group(0) if loc else '',
                    'context':context[:300]})
        if len(out)>=45:break
    return out

def portal_company_page_candidates(session,company,platform,page_url):
    if not valid_site(page_url,platform):return [],'기업별 링크 오류'
    allowed,policy=can_collect(session,page_url)
    if not allowed:return [],policy
    try:
        response=session.get(page_url,timeout=(7,22),allow_redirects=True)
        response.raise_for_status()
        if not valid_site(response.url,platform):return [],'리다이렉션 확인 불가'
        posts=parse_public_company_listing(response.text,platform,response.url)
        ident=re.sub(r'[^가-힣a-z0-9]','',company['name'].lower())
        checked=[]
        for post in posts:
            # Guard against an unrelated company embedded in a listing.
            first=re.match(r'^\[([^\]]+)\]',post['title'])
            if first:
                v=re.sub(r'[^가-힣a-z0-9]','',first.group(1).lower())
                if ident not in v and v not in ident:continue
            checked.append(post)
        return checked,('기업별 목록 후보 '+str(len(checked))+'건') if checked else '공고 링크 판독 0건'
    except (requests.RequestException,ValueError) as e:
        return [],'기업별 목록 접근 실패: '+type(e).__name__
