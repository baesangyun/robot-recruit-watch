/**************************************************************
 * @name 국내 로봇기업 채용 대시보드
 * @file docs/app.js
 * @version v03
 * @description 채용/수집현황/이력 단일페이지, 신규/마감/직무/지역/기업 검색, CSV
 * @author OpenAI ChatGPT
 * @date 2026-10-16
 * @Revisions
 * - 현재 버전:
 *   1) v03: 채용전문사이트 후보 및 승인 API 연동, 목록 가독성·정렬·수집 오류 확인
 *   1) 동적 JSON 로드, 공식공고와 확인필요 검색결과 엄격 구분
 *   2) 30개사 상태판, 필터, 페이지 이동 및 CSV 다운로드
 * - 이전 버전:
 *   1) 최초 작성
 **************************************************************/
'use strict';
(() => {
  const $ = (id) => document.getElementById(id);
  const state = { data: null, view: 'jobs', status: 'all', term: '', role: '', region: '', scope: '', company: '', page: 1, pageSize: 100, sort: 'recent', companyTerm: '' };
  const clean = (v) => String(v ?? '').trim();
  const jobStatus = (j) => {
    if (j.status === '마감') return '마감';
    if (!['official','platform_api'].includes(j.verification)) return '확인필요';
    return j.status === '확인필요' ? '확인필요' : '진행';
  };
  const scopeOf = (j) => {
    if (['국내','해외','미상'].includes(j.work_scope)) return j.work_scope;
    const location=clean(j.location);
    if (/\b(?:US|USA|IE|JP|CN|VN|TW|SG|IN|GB|UK|DE|FR|CA|AU|Ireland|Vietnam|Japan|China|Taiwan|Singapore)\b|미국|일본|아일랜드|베트남|중국|대만|싱가포르|tokyo|dublin|hanoi|xiamen/i.test(location)) return '해외';
    if (/\b(?:KR|Korea|Seoul|Busan|Incheon)\b|서울|경기|인천|부산|대전|대구|성남|수원|용인|포항|창원|제주|판교/i.test(location)) return '국내';
    return j.region && !['해외','미상'].includes(j.region) ? '국내' : '미상';
  };
  const safelyOpen = (url) => {
    if (!url) return '';
    try { const u = new URL(url); return /^https?:$/.test(u.protocol) ? u.href : ''; } catch { return ''; }
  };
  const formatDate = (iso, time = false) => {
    if (!iso) return '—';
    const d = new Date(iso);
    if (Number.isNaN(d.getTime())) return '—';
    return new Intl.DateTimeFormat('ko-KR',{timeZone:'Asia/Seoul',year:'numeric',month:'2-digit',day:'2-digit',...(time?{hour:'2-digit',minute:'2-digit',hour12:false}:{})}).format(d);
  };
  const el = (tag, attrs={}, children=[]) => {
    const node = document.createElement(tag);
    for (const [k,v] of Object.entries(attrs)) {
      if (k === 'class') node.className=v;
      else if (k === 'text') node.textContent=clean(v);
      else if (k === 'title') node.title=clean(v);
      else if (k === 'target' || k === 'rel' || k === 'href') node.setAttribute(k,v);
      else node.setAttribute(k,clean(v));
    }
    for (const child of children) node.append(child);
    return node;
  };
  const td = (...children) => el('td',{},children);
  const statuses = {'성공':'good','제한':'partial','실패':'failed','보안오류':'failed','미설정':'idle','미실행':'idle'};
  const chip = (text,kind) => el('span',{class:'status-chip '+kind,text});
  const roleKind = (role) => role.includes('SI')?'r-si':role.includes('영업')?'r-sales':role.includes('SW')?'r-sw':role.includes('HW')?'r-hw':'r-etc';
  const setText = (id,value) => {const e=$(id); if(e) e.textContent=clean(value);};
  const companyById = () => new Map((state.data?.companies||[]).map(c=>[c.id,c]));

  function displayView(v) {
    state.view = v;
    for (const name of ['jobs','companies','history']) {
      $(name+'-view').hidden = name !== v;
      document.querySelectorAll(`[data-view="${name}"]`).forEach(b=>b.classList.toggle('active',name===v));
    }
    if (v === 'companies') renderCompanies();
    if (v === 'history') renderHistory();
    if (v === 'jobs') renderJobs();
  }
  function initOptions() {
    const jobs=state.data.jobs||[];
    const roles=['유지보수·CS','SI·자동화','영업·사업','SW·AI','HW·기구','생산·품질','관리·기타','기타'];
    const regions=['서울','경기','인천','대전','세종','대구','부산','경남','충청','전라','경북','제주','강원','울산','해외','미상'];
    const fill=(id,values)=>{const target=$(id);for(const v of values) target.append(el('option',{value:v,text:v}));};
    fill('filter-role',roles); fill('filter-region',regions);
    const cs=[...state.data.companies].sort((a,b)=>a.name.localeCompare(b.name,'ko'));
    for (const c of cs) $('filter-company').append(el('option',{value:c.id,text:c.name}));
  }
  function updateSummary(){
    const jobs=state.data.jobs||[];
    const official=jobs.filter(j=>['official','platform_api'].includes(j.verification));
    const active=official.filter(j=>jobStatus(j)==='진행');
    const closed=official.filter(j=>jobStatus(j)==='마감');
    const fresh=active.filter(j=>j.new);
    const companies=state.data.companies||[];
    const success=companies.filter(c=>c.status==='성공').length;
    setText('hero-company-count',companies.length); setText('nav-company-count',companies.length); setText('last-sync',state.data.last_run?formatDate(state.data.last_run,true):'아직 실행 전');
    setText('stat-new',fresh.length); setText('stat-active',active.length); setText('stat-closed',closed.length);
    setText('stat-success',success); setText('stat-success-total','/ '+companies.length);
    setText('nav-job-count',jobs.length); setText('num-all',jobs.length); setText('num-new',fresh.length);
    setText('num-active',active.length); setText('num-closed',closed.length);
    setText('num-pending',jobs.filter(j=>jobStatus(j)==='확인필요').length);
    setText('companies-total',companies.length);
    setText('scope-counts', ['국내','해외','미상'].map(t=>t+' '+jobs.filter(j=>scopeOf(j)===t).length+'건').join(' · '));
    const notChecked=companies.filter(c=>c.status==='미실행').length;
    const limited=companies.filter(c=>c.status==='제한'||c.status==='미설정'||c.status==='실패'||c.status==='보안오류').length;
    const notice=$('notice');
    notice.classList.toggle('warning',Boolean(state.data.last_run&&limited>0));
    if (!state.data.last_run) setText('notice-text','아직 자동 수집을 실행하지 않았습니다. 이 화면의 0건은 실제 채용 0건이 아니라 데이터 미수집을 뜻합니다.');
    else setText('notice-text', `공식 공고 판독 ${success}개사 · 제한/실패/미설정 ${limited}개사. 수집 불가 기업은 채용 0건으로 간주하지 않습니다. 검색 후보는 반드시 원문 확인이 필요합니다.`);
  }
  function filteredJobs(){
    const term=state.term.toLocaleLowerCase('ko');
    let jobs=(state.data.jobs||[]).filter(j=>{
      const status=jobStatus(j);
      if(state.status==='new'&&!j.new) return false;
      if(state.status!=='new'&&state.status!=='all'&&status!==state.status) return false;
      if(state.scope && scopeOf(j)!==state.scope) return false;
      if(state.role&&j.role!==state.role)return false;
      if(state.region&&j.region!==state.region)return false;
      if(state.company&&j.company_id!==state.company)return false;
      if(term&&!((j.company+' '+j.title+' '+j.location+' '+j.role).toLocaleLowerCase('ko').includes(term)))return false;
      return true;
    });
    jobs.sort((a,b)=>{
      if(state.sort==='company')return a.company.localeCompare(b.company,'ko')||a.title.localeCompare(b.title,'ko');
      if(state.sort==='deadline')return (a.deadline||'9999').localeCompare(b.deadline||'9999')||a.company.localeCompare(b.company,'ko');
      return (b.first_seen||'').localeCompare(a.first_seen||'')||a.company.localeCompare(b.company,'ko');
    });
    return jobs;
  }
  function makeJobRow(job,coMap){
    const tr=el('tr'); const co=coMap.get(job.company_id)||{};
    const left=el('div',{class:'company-cell'},[
      el('span',{class:'company-avatar',text:job.company.slice(0,1)}),
      el('div',{},[el('div',{class:'company-name',text:job.company}),el('div',{class:'company-class',text:co.group||'로봇기업'})])
    ]);
    tr.append(td(left));
    const content=el('div',{class:'job-title'});
    const u=safelyOpen(job.url);
    content.append(u?el('a',{href:u,target:'_blank',rel:'noopener noreferrer',text:job.title}):el('span',{text:job.title}));
    if(job.new && jobStatus(job)==='진행')content.append(el('span',{class:'title-new',text:'NEW'}));
    content.append(el('div',{class:'source-hint',text:job.verification==='official'?'기업 공개 채용목록':job.verification==='platform_api'?'사람인 API · 활성 공고 확인':job.verification==='official_unverified'?'기업 과거·현행 목록 · 진행 여부 확인 필요':(job.source||'검색 발견')+' · 모집 여부 확인 필요'}));
    if (Array.isArray(job.other_sources)&&job.other_sources.length) {
      const links=el('div',{class:'alt-job-sources'});
      job.other_sources.forEach(s=>{const link=safelyOpen(s.url);if(link)links.append(el('a',{href:link,target:'_blank',rel:'noopener noreferrer',text:s.source+' ↗'}));});
      content.append(links);
    }
    tr.append(td(content));
    tr.append(td(el('span',{class:'job-badge '+roleKind(job.role||''),text:job.role||'기타'})));
    tr.append(td(el('span',{text:(job.location&&job.location!=='미상'?job.location:(job.region==='미상'?'지역 미상':job.region))+' · '+scopeOf(job)})));
    tr.append(td(el('span',{text:job.deadline?formatDate(job.deadline):'미정·상시'})));
    const st=jobStatus(job);
    tr.append(td(chip(st,st==='진행'?'good':st==='마감'?'closed':'verify')));
    tr.append(td(u?el('a',{href:u,target:'_blank',rel:'noopener noreferrer',class:'open-arrow',title:'원문 채용공고 열기',text:'↗'}):el('span',{text:'—'})));
    return tr;
  }
  function renderJobs(){
    const all=filteredJobs(); const total=all.length;
    const totalPages=Math.max(1,Math.ceil(total/state.pageSize));
    state.page=Math.min(state.page,totalPages);
    const start=(state.page-1)*state.pageSize;
    $('jobs-body').replaceChildren(...all.slice(start,start+state.pageSize).map(j=>makeJobRow(j,companyById())));
    $('empty-jobs').hidden=total!==0;
    if (total===0) setText('empty-reason',state.data.last_run ? '현재 조건에 일치하는 공고가 없습니다. 수집 제한 기업의 공고는 별도로 확인해 주세요.' : '최초 GitHub Actions 수집 실행 후 자동으로 표시됩니다. 기업별 상태 화면도 확인해 보세요.');
    setText('result-count',total);
    setText('page-info',total?`${start+1}–${Math.min(start+state.pageSize,total)} / ${total}개 · ${state.page}/${totalPages} 페이지`:'0개 표시');
    $('prev-page').disabled=state.page===1; $('next-page').disabled=state.page===totalPages;
  }
  function renderCompanies(){
    const list=[...(state.data.companies||[])].filter(c=>c.name.toLocaleLowerCase('ko').includes(state.companyTerm.toLocaleLowerCase('ko')));
    // 기본: 분류(기업 유형) 내림차순 → 동일 분류 기업명 내림차순
    list.sort((a,b)=>(b.group||'').localeCompare(a.group||'','ko')||b.name.localeCompare(a.name,'ko'));
    const rows=list.map(c=>{
      const tr=el('tr');
      tr.append(td(el('div',{class:'source-name',text:c.name})));
      tr.append(td(el('span',{text:c.group||'—'})));
      tr.append(td(chip(c.status||'미실행',statuses[c.status]||'idle')));
      tr.append(td(el('span',{text:c.status==='성공'?String(c.official_count??0)+'건': '—'})));
      const boardData=c.portal_results||{};
      const detail=Object.entries(boardData).filter(([k])=>k!=='사람인 API').map(([k,v])=>k+': '+v).join(' / ');
      tr.append(td(el('span',{text:String(c.candidate_count??0)+'건',title:detail})));
      const msg=el('div',{class:'source-msg',text:c.detail||'—'});
      if(c.status==='제한')msg.append(el('div',{class:'source-sub',text:'※ 웹 접속 성공과 채용 목록 판독 성공은 다릅니다.'}));
      if(c.status==='실패'||c.status==='보안오류')msg.append(el('div',{class:'source-sub',text:'※ 자동 수집환경에서 확인 실패. 브라우저 접속 가능 여부와 별개'}));
      const date=el('div',{class:'source-hint',text:formatDate(c.checked_at,true)});
      tr.append(td(msg,date));
      const links=el('div',{class:'company-source-links'});
      const u=safelyOpen(c.url);
      if(u)links.append(el('a',{class:'source-link',href:u,target:'_blank',rel:'noopener noreferrer',text:'공식 ↗'}));
      if(c.alternative_careers_url){const alt=safelyOpen(c.alternative_careers_url);if(alt)links.append(el('a',{class:'source-link',href:alt,target:'_blank',rel:'noopener noreferrer',text:'대체 채용목록 ↗'}));}
      for(const site of ['잡코리아','사람인','인크루트']){
        const target=safelyOpen((c.portal_links||{})[site]);
        if(target)links.append(el('a',{class:'board-link',href:target,target:'_blank',rel:'noopener noreferrer',text:site+' ↗'}));
      }
      tr.append(td(links));
      return tr;
    });
    $('companies-body').replaceChildren(...rows);
  }
  function renderHistory(){
    const list=state.data.history||[];
    $('empty-history').hidden=list.length>0;
    $('history-body').replaceChildren(...list.map(h=>{
      const tr=el('tr');
      for (const value of [formatDate(h.time,true),h.jobs_official,h.success,h.limited,h.failed]) tr.append(td(el('span',{text:value})));
      return tr;
    }));
  }
  function resetFilters(){
    state.term='';state.scope=''; state.role=''; state.region=''; state.company=''; state.status='all';state.page=1;state.sort='recent';
    $('search').value=''; $('filter-role').value=''; $('filter-region').value='';$('filter-scope').value=''; $('filter-company').value=''; $('sort').value='recent';
    document.querySelectorAll('.quick-role').forEach(b=>b.classList.remove('active'));
    document.querySelectorAll('.tab').forEach(b=>b.classList.toggle('active',b.dataset.status==='all'));
    renderJobs();
  }
  function downloadCsv(){
    const items=filteredJobs();
    const cols=['기업명','채용 직무','직무 분야','근무지역','국내해외','경력','마감일','상태','신규 여부','검증 수준','출처 URL'];
    const rows=items.map(j=>[j.company,j.title,j.role,j.location,scopeOf(j),j.career,j.deadline||'',jobStatus(j),j.new?'신규':'',j.verification==='official'?'공식 목록':j.verification==='platform_api'?'사람인 API':'검색 후보',j.url]);
    const csv='\ufeff'+[cols,...rows].map(row=>row.map(value=>'"'+clean(value).replace(/^[=+@-]/,'\'$&').replace(/"/g,'""')+'"').join(',')).join('\r\n');
    const blob=new Blob([csv],{type:'text/csv;charset=utf-8'});
    const url=URL.createObjectURL(blob);
    const a=document.createElement('a');a.href=url;a.download='국내_로봇기업_채용현황_v03_'+new Date().toISOString().slice(0,10)+'.csv';document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);
  }
  function bind(){
    document.querySelectorAll('.side-nav-item').forEach(b=>b.addEventListener('click',()=>{displayView(b.dataset.view);window.scrollTo({top:0,behavior:'smooth'});}));
    document.querySelectorAll('.tab').forEach(b=>b.addEventListener('click',()=>{state.status=b.dataset.status;state.page=1;document.querySelectorAll('.tab').forEach(x=>x.classList.toggle('active',x===b));renderJobs();}));
    document.querySelectorAll('.quick-role').forEach(b=>b.addEventListener('click',()=>{state.role=state.role===b.dataset.role?'':b.dataset.role;state.page=1;$('filter-role').value=state.role;document.querySelectorAll('.quick-role').forEach(x=>x.classList.toggle('active',x.dataset.role===state.role));displayView('jobs');renderJobs();}));
    $('search').addEventListener('input',e=>{state.term=e.target.value;state.page=1;renderJobs()});
    $('filter-role').addEventListener('change',e=>{state.role=e.target.value;state.page=1;document.querySelectorAll('.quick-role').forEach(x=>x.classList.toggle('active',x.dataset.role===state.role));renderJobs()});
    $('filter-scope').addEventListener('change',e=>{state.scope=e.target.value;state.page=1;renderJobs()});
    $('filter-region').addEventListener('change',e=>{state.region=e.target.value;state.page=1;renderJobs()});
    $('filter-company').addEventListener('change',e=>{state.company=e.target.value;state.page=1;renderJobs()});
    $('sort').addEventListener('change',e=>{state.sort=e.target.value;state.page=1;renderJobs()});
    $('reset').addEventListener('click',resetFilters);
    $('prev-page').addEventListener('click',()=>{state.page--;renderJobs()});
    $('next-page').addEventListener('click',()=>{state.page++;renderJobs()});
    $('download-csv').addEventListener('click',downloadCsv);
    $('company-search').addEventListener('input',e=>{state.companyTerm=e.target.value;renderCompanies()});
    $('empty-go-companies').addEventListener('click',()=>displayView('companies'));
    $('notice-link').addEventListener('click',e=>{e.preventDefault();displayView('companies')});
  }
  async function start(){
    setText('date-now',formatDate(new Date().toISOString())+' · KST');
    let data;
    try {
      const res=await fetch('./data/jobs.json?v='+Date.now(),{cache:'no-store'});
      if(!res.ok) throw new Error(`HTTP ${res.status}`);
      data=await res.json();
      if(!Array.isArray(data.jobs)||!Array.isArray(data.companies))throw new Error('수집 결과 데이터 형식 오류');
    } catch(err) {
      data=window.ROBOT_WATCH_SEED||{companies:[],jobs:[],history:[],last_run:null};
      console.warn('ROBOT WATCH: Data fetch unavailable; showing initial configuration only.',err);
      setText('notice-text','실시간 데이터 파일 연결에 실패했습니다. 현재 초기 기업 목록만 표시 중이며, 자동 수집 결과가 아닙니다. 배포 상태를 확인하세요.');
    }
    state.data=data;
    initOptions();bind();updateSummary();renderJobs();renderCompanies();renderHistory();
  }
  document.addEventListener('DOMContentLoaded',start);
})();
