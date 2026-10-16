# /**************************************************************
#  * @name 국내 로봇 채용 모니터 단위테스트
#  * @file tests/test_collect.py
#  * @version v02
#  * @description 기업 수·HTML 공고 파싱·중복/신규/마감 오판 방지 테스트
#  * @author OpenAI ChatGPT
#  * @date 2026-10-16
#  * @Revisions
#  * - 현재 버전:
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
