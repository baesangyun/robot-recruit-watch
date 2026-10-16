# /**************************************************************
#  * @name 국내 로봇 채용 모니터 단위테스트
#  * @file tests/test_collect.py
#  * @version v05
#  * @description 기업 수·HTML 공고 파싱·중복/신규/마감 오판 방지 테스트
#  * @author OpenAI ChatGPT
#  * @date 2026-10-16
#  * @Revisions
#  * - 현재 버전:
#  *   1) LinkedIn 검색 공고 링크·기업명·모집 여부 오판 방지
#  *   1) v03: 채용전문사이트 후보 및 승인 API 연동, 목록 가독성·정렬·수집 오류 확인
#  *   1) 신뢰 구분 및 첫 실행 신규 제외 확인
#  *   2) HTML 추출 및 종료 판정 테스트
#  * - 이전 버전:
#  *   1) 최초 작성
#  **************************************************************/
import json
from datetime import datetime,timedelta

from crawler.collect import (ROSTER_FILE, parse_breezy, parse_listing, reconcile, classify_region, classify_role, job_key, parse_deadline, host_allowed, base_job, classify_work_scope)

ROBOTIS = {"id":"robotis","name":"로보티즈","adapter":"ninehire","url":"https://robotisrecruiter.ninehire.site/jobs"}
BEAR = {"id":"bear","name":"베어로보틱스","adapter":"breezy","url":"https://bear-robotics.breezy.hr/"}


def test_company_roster():
    roster = json.loads(ROSTER_FILE.read_text())
    assert len(roster) == 30
    assert len({c['id'] for c in roster}) == 30
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
    assert "['잡코리아','사람인','인크루트']" in app


def test_angel_official_career_address():
    roster=json.loads(ROSTER_FILE.read_text())
    angel=next(c for c in roster if c['id']=='angel')
    assert angel['url']=='https://recruit.angel-robotics.com/ko/recruit/notice'

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
