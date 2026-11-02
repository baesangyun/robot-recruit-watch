# /**************************************************************
#  * @name 국내 로봇 채용 모니터 단위테스트
#  * @file tests/test_collect.py
#  * @version v17
#  * @description 기업 수·HTML 공고 파싱·중복/신규/마감 오판 방지 테스트
#  * @author OpenAI ChatGPT
#  * @date 2026-10-31
#  * @Revisions
#  * - 현재 버전:
#  *   1) 사용자 관리 기업/포털 JSON과 패스·관리 제외 지원 검사
#  *   1) 트위니 GreetingHR 채용공고 / 사람인 보완 경로 유지 검증
#  *   1) 큐렉소 UUID 공고 판독/허위공고 방지, 엔젤 채용목록 페이지네이션·부분수집 체크
#  *   1) 기존 URL 정정 및 큐렉소·로보케어·삼익THK 등 모집 목록 경로 검증
#  *   1) 채용사이트 7곳 및 기업별 URL 유형·유진로봇 대체 채용 링크 검증
#  *   1) 신규 확인 필요 후보 발견 표시, 폐업/타사명 오판 방지 검사
#  *   1) 52개사 및 로봇 관련 신규 상장 기업 검증
#  *   1) 잡코리아 상세 마감 표시/종료일 파싱 및 기본 목록 숨김 검증
#  *   1) 폐업기업 제외/운영 중 엔닷라이트 교체 검증
#  *   1) 신규 기업과 중견/투자 자료 및 원래 30개 기업 보존 확인
#  *   1) 채용사이트 4곳에서 필드엔지니어 및 유지보수 12개 검색어 확장 검증
#  *   2) 역할 검색의 타 기업 혼입/다른 직무 혼입 및 기존 검색 보존 검증
#  *   1) 수집 예약 KST 10시·15시와 인증된 Actions 수동 실행 링크 회귀 검사
#  *   1) LinkedIn 검색 공고 링크·기업명·모집 여부 오판 방지
#  *   1) v03: 채용전문사이트 후보 및 승인 API 연동, 목록 가독성·정렬·수집 오류 확인
#  *   1) 신뢰 구분 및 첫 실행 신규 제외 확인
#  *   2) HTML 추출 및 종료 판정 테스트
#  * - 이전 버전:
#  *   1) 최초 작성
#  **************************************************************/
import json
import requests
from datetime import datetime,timedelta

from crawler.collect import (ROSTER_FILE, parse_breezy, parse_listing, reconcile, classify_region, classify_role, job_key, parse_deadline, host_allowed, base_job, classify_work_scope)

ROBOTIS = {"id":"robotis","name":"로보티즈","adapter":"ninehire","url":"https://robotisrecruiter.ninehire.site/jobs"}
BEAR = {"id":"bear","name":"베어로보틱스","adapter":"breezy","url":"https://bear-robotics.breezy.hr/"}


def test_company_roster():
    roster = json.loads(ROSTER_FILE.read_text())
    assert len(roster) >= 52
    assert len({c['id'] for c in roster}) == len(roster)
    assert all(c['name'] and c['adapter'] and c['group'] for c in roster)


def test_ninehire_card_parse():
    html = '''<main><a href="/job_posting/Ab123"><h3>협동로봇 CS 엔지니어 모집</h3><span>서울 · 경력</span></a><a href="/faq">FAQ</a></main>'''
    jobs, empty = parse_listing(ROBOTIS, html, ROBOTIS['url'])
    assert len(jobs) == 1
    assert jobs[0]['role']=='유지보수·CS'
    assert jobs[0]['region']=='서울'
    assert jobs[0]['url']=='https://robotisrecruiter.ninehire.site/job_posting/Ab123'
    assert not empty


def test_breezy_json():
    jobs=parse_breezy(BEAR,[{'id':'X1','name':'Robotics Field Engineer (AMR)','url':'https://bear-robotics.breezy.hr/p/abc1','location':{'city':'Seoul','country':'KR'}}])
    assert len(jobs)==1
    assert jobs[0]['role']=='유지보수·CS'
    assert jobs[0]['region']=='서울'


def test_no_false_new_on_baseline():
    j=base_job(ROBOTIS,'협동로봇 CS 엔지니어 모집','https://robotisrecruiter.ninehire.site/job_posting/AB')
    out=reconcile({},[j],{'robotis':{'complete':True}},'2026-10-16T07:10:00+09:00')
    assert len(out)==1 and not out[0]['new']
    prev={'last_run':'2026-10-15T07:10:00+09:00','jobs':[]}
    out=reconcile(prev,[j],{'robotis':{'complete':True}},'2026-10-16T07:10:00+09:00')
    assert out[0]['new']


def test_missing_from_full_page_is_not_auto_closed():
    j=base_job(ROBOTIS,'협동로봇 CS 엔지니어 모집','https://robotisrecruiter.ninehire.site/job_posting/AB')
    j['status']='진행'
    prev={'last_run':'2026-10-15T07:10:00+09:00','jobs':[j]}
    out=reconcile(prev,[],{'robotis':{'complete':True}},'2026-10-16T07:10:00+09:00')
    assert out[0]['status']=='진행'
    prev2={'last_run':'2026-10-16T07:10:00+09:00','jobs':out}
    out2=reconcile(prev2,[],{'robotis':{'complete':True}},'2026-10-17T07:10:00+09:00')
    assert out2[0]['status']=='확인필요'


def test_search_candidate_not_official():
    j=base_job(ROBOTIS,'로봇 현장 서비스 엔지니어','https://www.jobkorea.co.kr/Recruit/GI_Read/123',reliability='search_unverified')
    prev={'last_run':'2026-10-15T07:10:00+09:00','jobs':[]}
    out=reconcile(prev,[j],{'robotis':{'complete':False}},'2026-10-16T07:10:00+09:00')
    assert out[0]['status']=='확인필요' and not out[0]['new']


def test_deadline_only_with_signal():
    assert parse_deadline('마감일: 2026.10.15')=='2026-10-15'
    assert parse_deadline('작성일 2026.10.15') is None


def test_host_boundary():
    assert host_allowed('https://www.jobkorea.co.kr/recruit',('jobkorea.co.kr',))
    assert not host_allowed('https://www.jobkorea.co.kr.evil.com/',('jobkorea.co.kr',))


def test_classifications():
    assert classify_region('대전 유성구')=='대전'
    assert classify_role('로봇 A/S 엔지니어')=='유지보수·CS'
    assert job_key('a','https://site.com/p?q=1&utm_source=abc')==job_key('a','https://site.com/p?q=1')


def test_angel_nested_card_title():
    angel={"id":"angel","name":"엔젤로보틱스","adapter":"angel","url":"https://www.angel-robotics.com/ko/recruit/notice"}
    html='<a href="/ko/recruit/notice/60"><span>SCM Team</span><span>플래닛 하남</span><div>Junior Procurement &amp; Material Specialist</div><span>채용 시 마감</span></a>'
    jobs, _=parse_listing(angel,html,angel['url'])
    assert len(jobs)==1
    assert jobs[0]['title']=='Junior Procurement & Material Specialist'

def test_greeting_career_o_url():
    company={"id":"neuromeka","name":"뉴로메카","adapter":"greeting","url":"https://neuromeka1.career.greetinghr.com/ko/home"}
    html = '<main><a href="/ko/o/162718"><h3>IndyPD_자동화 장비 제어 프로그램 개발자</h3><span>포항</span></a><a href="/ko/help">안내</a></main>'
    jobs, empty=parse_listing(company,html,company['url'])
    assert len(jobs)==1 and not empty
    assert jobs[0]['url']=='https://neuromeka1.career.greetinghr.com/ko/o/162718'
    assert jobs[0]['role']=='SI·자동화'


def test_location_scope_domestic_overseas_unknown():
    assert classify_work_scope('Seoul, KR Seoul Korea')=='국내'
    assert classify_work_scope("Dublin, IE Dublin Ireland")=='해외'
    assert classify_work_scope('Hanoi, VN')=='해외'
    assert classify_work_scope('Xiamen, CN')=='해외'
    assert classify_work_scope('미상')=='미상'
    assert classify_work_scope('', '경기')=='국내'
    assert classify_work_scope('서울 성동구 해외영업 부서')=='국내'
    assert classify_work_scope('Tokyo, JP')=='해외'


def test_breezy_country_dict_and_country_scope():
    jobs=parse_breezy(BEAR,[{'id':'oversea','name':'Engineer',
        'url':'https://bear-robotics.breezy.hr/p/oversea',
        'location':{'name':'Dublin, IE','city':'Dublin','country':{'name':'Ireland','id':'IE'}}},
        {'id':'domestic','name':'Field Engineer','url':'https://bear-robotics.breezy.hr/p/domestic',
        'location':{'city':'Seoul','country':{'name':'Korea, Republic of','id':'KR'}}}])
    assert jobs[0]['work_scope']=='해외'
    assert jobs[1]['work_scope']=='국내'
    assert "{'name':" not in jobs[0]['location']


def test_old_jobs_keep_country_scope():
    job=base_job(BEAR,'Engineer','https://bear-robotics.breezy.hr/p/somejob',location='Tokyo, JP')
    job.pop('work_scope')
    prev={'last_run':'2026-10-15T07:10:00+09:00','jobs':[job]}
    out=reconcile(prev,[],{'bear':{'complete':False}},'2026-10-16T07:10:00+09:00')
    assert out[0]['work_scope']=='해외'


# v03: recruitment boards & safe fallback behaviors
from crawler.collect import (BOARD_SITES, board_search_url, portal_links, rss_board_candidates,
    saramin_api_candidates, deduplicate_sources, scrape_official)
import requests

class MockResp:
    def __init__(self, text='', json_data=None, url='https://www.bing.com/search?format=rss'):
        self.content=text.encode('utf-8'); self.text=text
        self._json=json_data
        self.url=url; self.status_code=200; self.headers={}
    def json(self):return self._json
    def raise_for_status(self):pass

class MockSession:
    def __init__(self, response):self.response=response
    def get(self, url, **kwargs):
        if isinstance(self.response, Exception):raise self.response
        return self.response


def test_portal_links_are_distinct_and_valid():
    links=portal_links('두산로보틱스')
    assert set(links)==set(BOARD_SITES)
    assert all(link.startswith('https://') for link in links.values())
    assert '두산' not in board_search_url('잡코리아','뉴로메카')


def test_rss_board_job_is_unverified_not_falsely_active():
    rss="""<rss><channel><item><title>두산로보틱스 로봇 유지보수 엔지니어 채용</title>
<link>https://www.jobkorea.co.kr/Recruit/GI_Read/99211</link><description>두산로보틱스</description></item>
<item><title>별개의 회사 채용</title><link>https://www.jobkorea.co.kr/Recruit/GI_Read/99212</link><description>두산로보틱스</description></item>
</channel></rss>"""
    company={'id':'doosan','name':'두산로보틱스','url':'https://career.doosan.com/'}
    jobs,note=rss_board_candidates(company,'잡코리아',MockSession(MockResp(rss)))
    assert len(jobs)==1
    assert jobs[0]['verification']=='search_unverified'
    assert jobs[0]['status']=='확인필요'
    assert jobs[0]['source'].startswith('잡코리아')


def test_saramin_api_strict_employer_and_active():
    response={'jobs':{'job':[
        {'active':1,'company':{'detail':{'name':'(주)로보스타'}},'position':{'title':'로봇 SI 엔지니어','location':{'name':'경기 > 안산'}},'url':'https://www.saramin.co.kr/zf_user/jobs/relay/view?rec_idx=333'},
        {'active':1,'company':{'detail':{'name':'로보스타파트너'}},'position':{'title':'로봇 SI 엔지니어'},'url':'https://www.saramin.co.kr/zf_user/jobs/relay/view?rec_idx=444'},
        {'active':0,'company':{'detail':{'name':'(주)로보스타'}},'position':{'title':'지난 공고'},'url':'https://www.saramin.co.kr/zf_user/jobs/relay/view?rec_idx=555'}]}}
    company={'id':'robostar','name':'로보스타'}
    jobs,note=saramin_api_candidates(MockSession(MockResp(json_data=response)),company,'TEST_KEY')
    assert len(jobs)==1
    assert jobs[0]['verification']=='platform_api'
    assert jobs[0]['work_scope']=='국내'


def test_dedup_keeps_official_and_alternative_links():
    company={'id':'test','name':'테스트로봇'}
    a=base_job(company,'로봇 서비스 엔지니어','https://example.com/post/1',location='서울')
    b=base_job(company,'로봇 서비스 엔지니어','https://www.jobkorea.co.kr/Recruit/GI_Read/11',location='서울',reliability='search_unverified')
    b['source']='잡코리아 검색후보'
    out=deduplicate_sources([b,a])
    assert len(out)==1 and out[0]['url']==a['url']
    assert out[0]['other_sources'][0]['url']==b['url']


def test_ssl_error_is_not_bypassed():
    company={'id':'robostar','name':'로보스타','url':'https://gw.robostar.com/','adapter':'landing'}
    jobs,status,message,complete=scrape_official(MockSession(requests.exceptions.SSLError('cert failed')),company)
    assert jobs==[] and status=='보안오류' and not complete
    assert '우회 금지' in message


def test_frontend_100_per_page_and_group_desc_sort():
    from pathlib import Path
    app=(Path(__file__).resolve().parents[1]/'docs/app.js').read_text()
    assert 'pageSize: 100' in app
    assert "(b.group||'').localeCompare(a.group||'','ko')" in app
    assert "Object.keys(c.portal_links||{})" in app


def test_angel_official_career_address():
    roster=json.loads(ROSTER_FILE.read_text())
    angel=next(c for c in roster if c['id']=='angel')
    assert angel['url']=='https://www.angel-robotics.com/ko/recruit/notice'

# v04: 공개 기업별 공고목록 검사
from crawler.portal_company import parse_public_company_listing,job_link,can_collect

def test_jobkorea_public_company_listing():
    html='<h2>진행중인 채용정보</h2><a href="/Recruit/GI_Read/50120827">[로보티즈] 로봇생산인원 모집의 건 신입·경력 서울 D-52</a><h2>동종업계 기업홈</h2><a href="/Recruit/GI_Read/11">지난 공고</a>'
    out=parse_public_company_listing(html,'잡코리아','https://www.jobkorea.co.kr/company/42816603/recruit')
    assert len(out)==1 and out[0]['title']=='[로보티즈] 로봇생산인원 모집의 건'

def test_saramin_public_company_listing():
    html='<h2>진행중 공고 12건</h2><a href="/zf_user/jobs/view?rec_idx=1122">[뉴로메카] 로봇 CS 엔지니어</a><h2>마감된 공고</h2><a href="/zf_user/jobs/view?rec_idx=44">지난 공고</a>'
    out=parse_public_company_listing(html,'사람인','https://www.saramin.co.kr/zf_user/company-info/view-inner-recruit?csn=a')
    assert len(out)==1 and '1122' in out[0]['url']

def test_portal_never_accepts_company_home_as_post():
    assert job_link('https://www.jobkorea.co.kr/Recruit/GI_Read/50120827','잡코리아')
    assert not job_link('https://www.jobkorea.co.kr/company/42816603/recruit','잡코리아')
    assert not job_link('https://jobkorea.co.kr.bad.test/Recruit/GI_Read/1','잡코리아')

def test_portal_obeys_robots_disallow():
    class Block:
        def get(self,*args,**kwargs):
            return MockResp(text='User-agent: *\\nDisallow: /')
    ok,reason=can_collect(Block(),'https://www.jobkorea.co.kr/company/42816603/recruit')
    assert not ok and 'robots' in reason


from crawler.collect import is_indexed_linkedin_job, LINKEDIN_NAMES
from urllib.parse import unquote

def test_linkedin_index_search_added():
    assert BOARD_SITES["LinkedIn"] == "linkedin.com"
    links = portal_links("두산로보틱스")
    assert "Doosan%20Robotics" in links["LinkedIn"]
    assert "site:linkedin.com/jobs/view/" in unquote(board_search_url("LinkedIn","두산로보틱스"))

def test_linkedin_link_rejects_unrelated_or_nonposting_url():
    company = {"name": "베어로보틱스"}
    url = "https://kr.linkedin.com/jobs/view/robotics-field-engineer-at-bear-robotics-4462189836"
    assert is_indexed_linkedin_job(company, "Bear Robotics Robotics Field Engineer", url)
    assert not is_indexed_linkedin_job(company, "Other Company Field Engineer", url.replace("bear-robotics","other-co"))
    assert not is_indexed_linkedin_job(company, "Bear Robotics Field Engineer","https://www.linkedin.com/jobs/search/?keywords=Bear")
    assert not is_indexed_linkedin_job(company, "Bear Robotics Field Engineer","https://linkedin.com.evil.com/jobs/view/post-4462189836")

def test_linkedin_results_are_unverified():
    company = {"id": "doosan", "name": "두산로보틱스"}
    xml = '<rss><channel><item><title>Doosan Robotics Field Engineer 채용 | LinkedIn</title><link>https://kr.linkedin.com/jobs/view/field-engineer-at-doosan-robotics-4397947416</link><description>Doosan Robotics Engineer</description></item><item><title>OtherCo Field Engineer</title><link>https://www.linkedin.com/jobs/view/engineer-at-otherco-4389057279</link></item></channel></rss>'
    jobs, note = rss_board_candidates(company, "LinkedIn", MockSession(MockResp(xml)))
    assert len(jobs) == 1 and jobs[0]["source"] == "LinkedIn 검색후보"
    assert jobs[0]["verification"] == "search_unverified" and jobs[0]["status"] == "확인필요"



def test_twice_daily_kst_schedule_and_manual_dispatch():
    from pathlib import Path
    root = Path(__file__).resolve().parents[1]
    wf = (root/'.github/workflows/daily-monitor.yml').read_text(encoding='utf-8')
    assert '  workflow_dispatch:' in wf
    assert "cron: '0 1 * * *'" in wf  # UTC 01:00 = KST 10:00
    assert "cron: '0 6 * * *'" in wf  # UTC 06:00 = KST 15:00
    assert "cron: '10 22 * * *'" not in wf
    html = (root/'docs/index.html').read_text(encoding='utf-8')
    assert '10:00 · 15:00' in html
    assert 'GitHub에서 <b>Run workflow → Run workflow</b>' in html
    assert 'https://github.com/baesangyun/robot-recruit-watch/actions/workflows/daily-monitor.yml' in html
    assert '수동 실행' in html
    # No GitHub personal token is exposed to the public static page.
    assert 'github_pat_' not in html and 'ghp_' not in html




# v06 maintenance / Field Engineer targeted index search
from crawler.collect import SERVICE_SEARCH_TERMS, SERVICE_ROLE_RX


def test_maintenance_search_term_coverage_all_portals():
    terms = (
        "필드엔지니어", "Field Engineer", "필드서비스엔지니어",
        "Field Service Engineer", "유지보수", "Maintenance",
        "서비스엔지니어", "Service Engineer", "기술지원",
        "Technical Support", "A/S", "CS Engineer",
    )
    assert SERVICE_SEARCH_TERMS == terms
    for platform in BOARD_SITES:
        ordinary = unquote(board_search_url(platform, "두산로보틱스"))
        extended = unquote(board_search_url(platform, "두산로보틱스", role_search=True))
        assert ordinary.startswith("https://www.bing.com/search?")
        assert ordinary != extended
        assert extended.startswith(ordinary.split("&q=")[0])
        assert all('"' + term + '"' in extended for term in terms)
        assert " OR " in extended
        assert "두산로보틱스" in extended or "Doosan Robotics" in extended
        assert all(term not in ordinary for term in terms)


def test_maintenance_role_matches_english_and_korean():
    for text in (
        "필드엔지니어 채용", "Field Engineer", "필드서비스엔지니어",
        "Field Service Engineer", "유지보수", "Maintenance",
        "서비스엔지니어", "Service Engineer", "기술지원",
        "Technical Support", "A/S", "CS Engineer",
    ):
        assert SERVICE_ROLE_RX.search(text), text
    assert SERVICE_ROLE_RX.search("Field   Service Engineer")
    assert not SERVICE_ROLE_RX.search("인사총무 담당")


def test_maintenance_search_results_validate_company_and_role():
    company={"id":"doosan","name":"두산로보틱스","url":"https://career.doosan.com"}
    xml="""<rss><channel>
      <item><title>두산로보틱스 필드엔지니어 채용</title>
      <link>https://www.jobkorea.co.kr/Recruit/GI_Read/90001</link></item>
      <item><title>두산로보틱스 인사총무 담당 채용</title>
      <link>https://www.jobkorea.co.kr/Recruit/GI_Read/90002</link></item>
      <item><title>다른로보틱스 Field Engineer 채용</title>
      <link>https://www.jobkorea.co.kr/Recruit/GI_Read/90003</link></item>
      <item><title>두산로보틱스 Field Engineer 채용</title>
      <link>https://jobkorea.co.kr.evil.example/Recruit/GI_Read/90004</link></item>
      </channel></rss>"""
    matches,note=rss_board_candidates(company,"잡코리아",MockSession(MockResp(xml)),role_search=True)
    assert len(matches)==1
    assert matches[0]["title"]=="두산로보틱스 필드엔지니어 채용"
    assert matches[0]["status"]=="확인필요"
    assert matches[0]["verification"]=="search_unverified"
    assert matches[0]["source"]=="잡코리아 유지보수 검색후보"


def test_maintenance_search_reuses_existing_dedup_logic():
    company={"id":"robotis","name":"로보티즈"}
    url="https://www.jobkorea.co.kr/Recruit/GI_Read/90005"
    a=base_job(company,"로보티즈 Field Engineer",url,reliability="search_unverified")
    b=base_job(company,"로보티즈 Field Engineer",url,reliability="search_unverified")
    assert len(deduplicate_sources([a,b]))==1


def test_maintenance_keyword_search_invoked_for_each_board():
    from pathlib import Path
    src=(Path(__file__).resolve().parents[1]/"crawler/collect.py").read_text(encoding="utf-8")
    assert "for board in BOARD_SITES:" in src
    assert "rss_board_candidates(company,board,local,role_search=True)" in src
    assert "found.extend(service_matches)" in src

def test_expansion_mid_and_corporate_investment_provenance():
    roster=json.loads(ROSTER_FILE.read_text(encoding="utf-8"))
    assert set(["hanwha","doosan","hd","samsung","lg","hyundai","rainbow","robotis","neuromeka","bear","angel","kohyoung","yujin","yuil","robostar","clobot","twinny","trobotics","everybot","roborobo","sbb","spg","higen","vd","neubility","robocare","curexo","raon","future","robot3"]).issubset({c["id"] for c in roster})
    assert len(roster)==len({c["id"] for c in roster})==len({c["name"] for c in roster}) and len(roster)>=52
    assert sum(c["group"]=="중견기업" for c in roster)==3
    assert sum(c["group"]=="대기업 투자기업" for c in roster)==5
    for c in roster:
        if c.get("investors"):
            assert c["investment_source_url"].startswith("https://")
        if c["group"]=="중견기업":
            assert c["size_evidence_url"].startswith("https://")


def test_investment_links_on_ui_and_seed_company_count():
    from pathlib import Path
    root=Path(__file__).resolve().parents[1]
    seed=(root/"docs/seed.js").read_text(encoding="utf-8").split("window.ROBOT_WATCH_SEED = ",1)[1].strip().rstrip(";")
    data=json.loads(seed)
    assert len(data["companies"])==52 and data["jobs"]==[]
    assert all(c["status"]=="미실행" for c in data["companies"])
    js=(root/"docs/app.js").read_text(encoding="utf-8")
    assert "투자 근거 ↗" in js and "중견기업 근거 ↗" in js
    html=(root/"docs/index.html").read_text(encoding="utf-8")
    assert 'id="hero-company-count">52<' in html
    assert 'id="companies-total">52<' in html

def test_exclude_closed_firm_and_include_active_corporate_investee():
    roster=json.loads(ROSTER_FILE.read_text(encoding="utf-8"))
    ids={c["id"] for c in roster}
    assert len(roster)>=52
    assert "floatic" not in ids
    assert "ndotlight" in ids
    c=next(c for c in roster if c["id"]=="ndotlight")
    assert c["group"]=="대기업 투자기업"
    assert c["investors"]=="네이버 D2SF"
    assert c["url"]=="https://ndotlight.careers.team/"


# v10 job deadline/closure verification
from crawler.job_status import (
    canonical_jobkorea_url, parse_jobkorea_details, update_jobkorea_statuses
)


def test_jobkorea_detail_parse_explicit_closed_and_recruiting_dates():
    html = """<html><body><h1>[로보티즈] 세미휴머노이드 필드엔지니어 모집의 건</h1>
    <div>마감</div><h2>지원정보</h2><p>마감되었습니다.</p>
    <div>기간 2026.08.31(월) ~ 2026.10.30(금)</div></body></html>"""
    result = parse_jobkorea_details(html)
    assert result == {"deadline":"2026-10-30","explicitly_closed":True}


def test_jobkorea_detail_parse_active_no_false_closed():
    html = """<h1>로봇 Field Engineer 채용</h1><p>마감일은 기업의 사정에 따라 조기 마감 또는 변경될 수 있습니다.</p>
    <p>접수기간/방법 기간 2026.10.31(토) ~ 2026.11.20(금)</p><button>지원하기</button>"""
    x = parse_jobkorea_details(html)
    assert x["deadline"] == "2026-11-20"
    assert not x["explicitly_closed"]


def test_jobkorea_detail_parse_pc_deadline_without_period():
    html = "<h1>엔지니어 채용</h1><section>접수기간 · 방법</section><div>마감일 2026.10.30(금)</div>"
    result = parse_jobkorea_details(html)
    assert result["deadline"] == "2026-10-30"


def test_jobkorea_url_validation_and_app_redirect_not_scraped():
    assert canonical_jobkorea_url(
      "https://www.jobkorea.co.kr/Recruit/GI_Read/49888960?Oem_Code=C1&sc=225"
    ) == "https://www.jobkorea.co.kr/Recruit/GI_Read/49888960"
    assert canonical_jobkorea_url("https://m.jobkorea.co.kr/Recruit/GI_Read/49888960")
    assert canonical_jobkorea_url("https://m.jobkorea.co.kr/info/app_down.asp?Gno=49888960") is None
    assert canonical_jobkorea_url("https://evil.jobkorea.co.kr.evil.net/Recruit/GI_Read/49888960") is None


def test_close_overdue_job_from_previous_evidence_without_network():
    class NoRequests:
        def get(self,*args,**kwargs):
            raise AssertionError("Remote request unnecessary for an already ended posting.")
    j=base_job(ROBOTIS,"[로보티즈] 세미휴머노이드 필드엔지니어 모집의 건",
      "https://www.jobkorea.co.kr/Recruit/GI_Read/49888960",
      reliability="search_unverified")
    j["deadline"]="2026-10-30"
    j["status"]="확인필요"
    stats=update_jobkorea_statuses(NoRequests(), [j], now=datetime.fromisoformat("2026-10-31T08:40:00+09:00"))
    assert j["status"]=="마감" and j["deadline"]=="2026-10-30" and stats["closed"]==1


def test_reconcile_retains_verified_deadline_after_rescan():
    company={"id":"robotis","name":"로보티즈"}
    url="https://www.jobkorea.co.kr/Recruit/GI_Read/49888960"
    old=base_job(company,"로보티즈 Field Engineer",url,reliability="search_unverified")
    old.update({"deadline":"2026-10-30","status":"마감","status_evidence":"사용자 제공 공고 마감 화면"})
    fresh=base_job(company,"로보티즈 Field Engineer",url,reliability="search_unverified")
    after=reconcile({"last_run":"2026-10-30T10:00:00+09:00","jobs":[old]},
         [fresh],{"robotis":{"complete":False}},"2026-10-31T10:00:00+09:00")
    assert after[0]["status"]=="마감" and after[0]["deadline"]=="2026-10-30"


def test_closed_posts_hidden_by_default_but_kept_in_archive():
    from pathlib import Path
    root=Path(__file__).resolve().parents[1]
    app=(root/"docs/app.js").read_text(encoding="utf-8")
    html=(root/"docs/index.html").read_text(encoding="utf-8")
    assert "state.status==='all'&&['마감','관리제외'].includes(status)" in app
    assert 'data-status="마감"' in html
    assert '모집·확인 필요' in html

def test_missing_robotics_firms_registered():
    cs=json.loads(ROSTER_FILE.read_text(encoding="utf-8"))
    by={c["id"]:c for c in cs}
    assert len(cs)==len(by) and len(cs)>=52
    assert all(by[k]["group"]=="상장기업" for k in ["bigwave","brils","zenixrobotics","pnnsrobotics","spsystems","vone","samickthk","cowin","samhyeon","knrsystem"])
    assert by["hlrobotics"]["group"]=="대기업계열"
    boards=json.loads((ROSTER_FILE.parent/"board_company_pages.json").read_text(encoding="utf-8"))
    assert boards["bigwave"]["사람인"] and boards["brils"]["사람인"] and boards["hlrobotics"]["잡코리아"]


from crawler.portal_company import company_prefix_matches


def test_new_company_name_aliases_are_strict():
    assert company_prefix_matches({"id":"brils","name":"브릴스"},"BRILS")
    assert company_prefix_matches({"id":"hlrobotics","name":"에이치엘로보틱스"},"HL로보틱스")
    assert not company_prefix_matches({"id":"brils","name":"브릴스"},"BRILS PARTNER")
    assert not company_prefix_matches({"id":"bigwave","name":"빅웨이브로보틱스"},"다른로보틱스")


def test_recent_new_search_candidate_is_shown_but_not_assumed_open():
    root=ROSTER_FILE.parent
    app=(root/"docs/app.js").read_text(encoding="utf-8")
    html=(root/"docs/index.html").read_text(encoding="utf-8")
    assert "const recentlyDiscovered = (j) =>" in app
    assert "48*60*60*1000" in app
    assert "state.status==='new'&&!recentlyDiscovered(j)" in app
    assert "NEW·미확인" in app
    assert "if (j.status === '마감') return '마감'" in app
    assert "신규 발견(48시간)" in html


# v17 search site / company URL audit regressions
from crawler.collect import indexed_job_url_valid, company_url_kind


def test_seven_professional_job_search_sources():
    expected={"잡코리아","사람인","인크루트","LinkedIn","리멤버","원티드","잡플래닛"}
    assert set(BOARD_SITES)=={v["name"] for v in load_portal_config()}
    for company in ["유진로봇","빅웨이브로보틱스","에이치엘로보틱스"]:
        links=portal_links(company)
        assert set(links)==expected
        assert all(links[site].startswith("https://www.google.com/search?q=")
                   for site in ("리멤버","원티드","잡플래닛"))
        for site in expected:
            assert site and board_search_url(site,company).startswith("https://www.bing.com/")


def test_job_search_index_only_matches_individual_job_links():
    assert indexed_job_url_valid("리멤버","https://career.rememberapp.co.kr/job/posting/350919")
    assert not indexed_job_url_valid("리멤버","https://career.rememberapp.co.kr/job/postings")
    assert indexed_job_url_valid("원티드","https://www.wanted.co.kr/wd/12345")
    assert not indexed_job_url_valid("원티드","https://www.wanted.co.kr/search?query=robot")
    assert indexed_job_url_valid("잡플래닛","https://www.jobplanet.co.kr/job/postings/12345")
    assert not indexed_job_url_valid("잡플래닛","https://www.jobplanet.co.kr/job")
    assert not indexed_job_url_valid("리멤버","https://career.rememberapp.co.kr.evil.io/job/posting/1234")


def test_official_url_types_are_not_claimed_as_verified_vacancies():
    assert company_url_kind({"url":"https://www.clobot.co.kr/"})=="기업 홈페이지(채용 전용 아님)"
    assert company_url_kind({"url":"https://career.kohyoung.com/recruit"})=="채용 전용 경로"
    assert company_url_kind({"url":"https://www.jobkorea.co.kr/company/45203970/Recruit"})=="외부 기업별 채용목록"
    assert company_url_kind({"url":None})=="공식 채용 URL 미등록"


def test_yujin_verified_alternate_listing_and_old_link_warning():
    roster=json.loads(ROSTER_FILE.read_text(encoding="utf-8"))
    co=next(c for c in roster if c["id"]=="yujin")
    assert co["alternative_careers_url"]=="https://www.jobkorea.co.kr/company/45203970/Recruit"
    assert "404" in co["official_url_note"]
    pages=json.loads((ROSTER_FILE.parent/"board_company_pages.json").read_text(encoding="utf-8"))
    assert "yujin" in pages and "잡코리아" in pages["yujin"]
    assert pages["yujin"]["잡코리아"][0]==co["alternative_careers_url"]


def test_legacy_sources_keep_linked_instead_of_removal():
    from pathlib import Path
    app=(Path(__file__).resolve().parents[1]/"docs/app.js").read_text(encoding="utf-8")
    assert "Object.keys(c.portal_links||{})" in app
    assert "회사 홈 ↗" in app


def test_career_url_audit_extra_verified_employer_pages():
    roster=json.loads(ROSTER_FILE.read_text(encoding="utf-8"))
    cs={c["id"]:c for c in roster}
    assert cs["spg"]["url"]=="https://spg.co.kr/aboutUs?tab=3"
    assert cs["curexo"]["url"]=="https://career.curexo.com/a049e805-13d8-4ccc-97d2-a3fab412be13"
    assert cs["sbb"]["url"]=="http://www.sbb.co.kr"
    for cid in ("yujin","curexo","robocare","higen","samhyeon","samickthk","vone","knrsystem"):
        assert cs[cid]["alternative_careers_url"].startswith("https://")
    boards=json.loads((ROSTER_FILE.parent/"board_company_pages.json").read_text(encoding="utf-8"))
    for cid in ("yujin","curexo","robocare","higen","samhyeon","samickthk","vone","knrsystem"):
        assert cid in boards
        assert all(url.startswith("https://") for group in boards[cid].values() for url in group)



def test_curexo_public_job_list_parses_not_about_pages():
    curexo={"id":"curexo","name":"큐렉소","adapter":"curexo",
            "url":"https://career.curexo.com/a049e805-13d8-4ccc-97d2-a3fab412be13"}
    html="""<main><h1>채용 공고</h1><h2>채용 중</h2>
       <a href="/321ed000-1d73-808d-b8e5-d1d13bbff9b3">의료로봇(관절) 기술지원 신입 경력</a>
       <a href="/34ced000-1d73-80ab-8770-e1878089dae0">의료로봇(재활·척추) 임상/기술지원 신입 경력</a>
       <a href="/034ad000-0000-0000-0000-000000000003">의료기기 마케팅 및 제품홍보</a>
       <a href="/b11abc00-0000-0000-0000-000000000000">큐렉소 소개</a>
       <a href="https://other-company.com/12345">기술지원 다른 회사 채용</a>
       <a href="/a049e805-13d8-4ccc-97d2-a3fab412be13">채용 공고</a>
       </main>"""
    jobs,empty=parse_listing(curexo,html,curexo["url"])
    assert len(jobs)==3 and not empty
    assert any("의료로봇(관절) 기술지원" in j["title"] for j in jobs)
    assert all(j["verification"]=="official" for j in jobs)
    assert all(j["url"].startswith("https://career.curexo.com/") for j in jobs)


def test_curexo_does_not_claim_hiring_without_open_label():
    c={"id":"curexo","name":"큐렉소","adapter":"curexo","url":"https://career.curexo.com/"}
    html='<a href="/321ed000-1d73-808d-b8e5-d1d13bbff9b3">의료로봇(관절) 기술지원</a>'
    jobs,_=parse_listing(c,html,c["url"])
    assert len(jobs)==1
    assert jobs[0]["verification"]=="official_unverified"
    assert jobs[0]["status"]=="확인필요"


def test_angel_public_two_pages_collects_full_count():
    from crawler.collect import scrape_official
    class Resp:
        def __init__(self,url,txt):
            self.url=url;self.text=txt;self.status_code=200;self.headers={}
        def raise_for_status(self):pass
    class Session:
        def __init__(self):self.urls=[]
        def get(self,url,**kw):
            self.urls.append(url)
            def cards(nums):
                return ''.join(f'<a href="/ko/recruit/notice/{i}"><div>필드 엔지니어 모집 {i}</div></a>' for i in nums)
            html='<p>총 3건의 공고가 진행중입니다.</p>'
            if "?page=2" in url:
                html+=cards([3])
            else:
                html+=cards([1,2])+'<a href="?page=2">2</a>'
            return Resp(url,html)
    co={"id":"angel","name":"엔젤로보틱스","adapter":"angel",
        "url":"https://www.angel-robotics.com/ko/recruit/notice"}
    ss=Session()
    jobs,status,note,complete=scrape_official(ss,co)
    assert status=="성공" and complete
    assert len(jobs)==3
    assert len(ss.urls)==2


def test_angel_partial_page_not_marked_complete():
    from crawler.collect import scrape_official
    class Resp:
        def __init__(self,url,txt):self.url=url;self.text=txt;self.status_code=200;self.headers={}
        def raise_for_status(self):pass
    class Broken:
        def get(self,url,**kw):
            if "?page=2" in url:raise requests.RequestException("site unavailable")
            return Resp(url,'<p>총 3건의 공고가 진행중입니다.</p>'
                            '<a href="/ko/recruit/notice/1">필드 엔지니어 모집</a>')
    co={"id":"angel","name":"엔젤로보틱스","adapter":"angel",
        "url":"https://www.angel-robotics.com/ko/recruit/notice"}
    jobs,status,note,complete=scrape_official(Broken(),co)
    assert len(jobs)==1 and status=="제한" and not complete
    assert "1/3" in note


def test_new_official_job_urls_in_registry():
    roster=json.loads(ROSTER_FILE.read_text(encoding="utf-8"))
    a={c["id"]:c for c in roster}
    assert len(roster)>=52
    assert a["angel"]["url"]=="https://www.angel-robotics.com/ko/recruit/notice"
    assert a["curexo"]["adapter"]=="curexo"
    assert "a049e805" in a["curexo"]["url"]
    assert a["doosan"]["url"].endswith("/dsp/sa/RecList.jsp")



def test_twinny_greetinghr_adapter_and_saramin_fallback():
    roster=json.loads(ROSTER_FILE.read_text(encoding="utf-8"))
    c=next(c for c in roster if c["id"]=="twinny")
    assert c["adapter"]=="greeting"
    assert c["url"]=="https://twinny.career.greetinghr.com/ko/home"
    assert c["alternative_careers_url"].startswith("https://www.saramin.co.kr/")
    boards=json.loads((ROSTER_FILE.parent/"board_company_pages.json").read_text(encoding="utf-8"))
    assert boards["twinny"]["사람인"]==[c["alternative_careers_url"]]


def test_twinny_field_engineer_posting_parses_with_existing_greeting_logic():
    company={"id":"twinny","name":"트위니","adapter":"greeting",
             "url":"https://twinny.career.greetinghr.com/ko/home"}
    html=('<div>채용 중인 공고</div>'
          '<a href="/ko/o/123456"><h3>[로봇사업본부] 자율주행로봇 CS팀 필드엔지니어 채용</h3>'
          '<span>현장기술지원 경력 무관 정규직 트위니</span></a>')
    jobs,empty=parse_listing(company,html,company["url"])
    assert not empty and len(jobs)==1
    assert jobs[0]["verification"]=="official"
    assert jobs[0]["role"]=="유지보수·CS"



from crawler.collect import load_portal_config


def test_manager_configurations_stay_integrated():
    entries=load_portal_config()
    assert len(entries)==len(BOARD_SITES)
    assert all(e["url"].startswith("https://") for e in entries)
    docroot=ROSTER_FILE.parent/"docs"
    html=(docroot/"manage.html").read_text(encoding="utf-8")
    script=(docroot/"manage.js").read_text(encoding="utf-8")
    assert "job_portals.json" in script and "companies.json" in script
    assert "관리 페이지" in html and "패스" in html
    assert "git/trees" in script and "git/commits" in script
    assert "localStorage" not in script and "sessionStorage" not in script
    assert "Authorization" in script
    assert "manage.html" in (docroot/"index.html").read_text(encoding="utf-8")


def test_portal_manager_skips_deleted_and_invalid_urls(tmp_path):
    source=[
        {"name":"예시","url":"https://jobs.example.com","monitor_status":"active"},
        {"name":"삭제","url":"https://deleted.example.com","monitor_status":"deleted"},
        {"name":"오류","url":"javascript:alert(1)","monitor_status":"active"},
    ]
    p=tmp_path/"portals.json"
    p.write_text(json.dumps(source,ensure_ascii=False),encoding="utf-8")
    active=load_portal_config(p)
    assert len(active)==1 and active[0]["name"]=="예시"


def test_soft_deleted_company_and_pass_semantics():
    s=(ROSTER_FILE.parent/"crawler/collect.py").read_text(encoding="utf-8")
    assert 'co.get("monitor_status")=="deleted"' in s
    assert 'company.get("monitor_status")=="pass"' in s
    assert 'job["status"]="관리제외"' in s
