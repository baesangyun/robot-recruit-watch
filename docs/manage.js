/* /**************************************************************
 * @name 로봇기업·채용포털 관리자
 * @file docs/manage.js
 * @version v01
 * @description 관리 대상 JSON 편집 및 인증된 GitHub API 단일 커밋 저장
 * @author OpenAI ChatGPT
 * @date 2026-11-03
 * @Revisions
 * - 현재 버전:
 *   1) 52개 기업·7개 포털 조회/추가/수정/패스/관리 제외/복원
 *   2) 토큰 일회성 사용, 파일 충돌 검사 및 원자적 Git 커밋
 * - 이전 버전:
 *   1) 최초 작성
 **************************************************************/ */
(() => {
  'use strict';
  const repo = "baesangyun/robot-recruit-watch";
  const branch = "main";
  const apiBase = "https://api.github.com/repos/" + repo;
  const filenames = {companies:"companies.json", portals:"job_portals.json"};
  const $ = id => document.getElementById(id);
  const state = {
    view:"companies", rows:{companies:[],portals:[]},
    original:{companies:[],portals:[]}, hashes:{companies:"",portals:""},
    ready:false, editKey:null
  };
  const clone = value => JSON.parse(JSON.stringify(value));
  const statusName = s => ({active:"정상",pass:"패스",deleted:"관리 제외"})[s] || "정상";
  const statusValue = o => o.monitor_status || "active";
  const node = (tag, text, className="") => {
    const e=document.createElement(tag);
    if(text!==undefined)e.textContent=String(text);
    if(className)e.className=className;
    return e;
  };
  const setMessage = (message, kind="") => {
    const e=$("status");
    e.textContent=message;
    e.className="save-status" +(kind?" "+kind:"");
  };
  const urlValid = (value, requireHttps=false) => {
    try {
      const u=new URL(value);
      return (requireHttps ? u.protocol==="https:" : ["https:","http:"].includes(u.protocol))
        && !!u.hostname && !u.username && !u.password;
    } catch {return false;}
  };

  async function request(path, token, method="GET", body=null) {
    const headers={"Accept":"application/vnd.github+json","X-GitHub-Api-Version":"2022-11-28"};
    if(token)headers.Authorization="Bearer "+token;
    if(body!==null)headers["Content-Type"]="application/json";
    const response=await fetch(apiBase+path,{
      method, headers, body:body===null?undefined:JSON.stringify(body),cache:"no-store"
    });
    let json={};
    try{json=await response.json();}catch{ /* GitHub may return no body */ }
    if(!response.ok){
      let message=typeof json.message==="string"?json.message:("HTTP "+response.status);
      if(response.status===401||response.status===403){
        message="GitHub 인증 또는 권한 오류("+response.status+"). 토큰의 저장소 Contents 읽기/쓰기 권한을 확인하세요.";
      }else if(response.status===409||response.status===422){
        message="저장 중 다른 Git 변경과 충돌했습니다. 페이지의 최신 목록을 다시 확인해야 합니다.";
      }
      throw new Error(message);
    }
    return json;
  }
  function decodeBase64(content) {
    const raw=atob((content||"").replace(/\s/g,""));
    const bytes=Uint8Array.from(raw, c=>c.charCodeAt(0));
    return new TextDecoder("utf-8").decode(bytes);
  }
  async function readConfig(key, token="") {
    const raw=await request("/contents/"+filenames[key]+"?ref="+branch,token);
    const entries=JSON.parse(decodeBase64(raw.content));
    if(!Array.isArray(entries))throw new Error(filenames[key]+"이 JSON 배열이 아닙니다.");
    return {entries,sha:raw.sha};
  }
  async function loadConfig() {
    $("commit-button").disabled=true;
    setMessage("현재 GitHub의 기업·채용포털 설정을 불러오는 중입니다.");
    try {
      const [a,b]=await Promise.all([readConfig("companies"),readConfig("portals")]);
      state.rows.companies=a.entries;state.rows.portals=b.entries;
      state.original.companies=clone(a.entries);state.original.portals=clone(b.entries);
      state.hashes={companies:a.sha,portals:b.sha};
      state.ready=true;
      $("commit-button").disabled=false;
      render();
      setMessage("기업 "+a.entries.length+"개, 채용포털 "+b.entries.length+"개를 불러왔습니다. 목록에서 수정한 뒤 GitHub에 저장하세요.","ok");
    }catch(e){
      state.ready=false;
      setMessage("데이터 불러오기 실패: "+e.message+" · 잠시 후 새로고침해 주세요.","err");
    }
  }
  function changedCount() {
    let count=0;
    for(const key of ["companies","portals"]){
      const before=new Map(state.original[key].map(x=>[x.id,JSON.stringify(x)]));
      for(const row of state.rows[key])if(before.get(row.id)!==JSON.stringify(row))count++;
      count+=state.original[key].filter(x=>!state.rows[key].some(y=>y.id===x.id)).length;
    }
    return count;
  }
  function render() {
    $("count-companies").textContent=state.rows.companies.filter(x=>statusValue(x)!=="deleted").length;
    $("count-portals").textContent=state.rows.portals.filter(x=>statusValue(x)==="active").length;
    $("count-pass").textContent=state.rows.companies.filter(x=>statusValue(x)==="pass").length;
    $("count-dirty").textContent=changedCount();
    $("company-tab-count").textContent=state.rows.companies.length;
    $("portal-tab-count").textContent=state.rows.portals.length;
    $("add-item").textContent=state.view==="companies"?"＋ 새 기업 추가":"＋ 새 포털 추가";
    $("tab-hint").textContent=state.view==="companies"
      ?"기업의 실제 채용목록 URL을 등록하세요. '패스'는 공식 URL 점검만 건너뛰고 전문 포털 검색은 유지합니다."
      :"채용 포털 이름과 HTTPS 주소를 관리합니다. 추가한 포털은 공개 검색색인 기반 탐색에 사용됩니다.";
    document.querySelectorAll("[data-view]").forEach(b=>{
      const active=b.dataset.view===state.view;
      b.classList.toggle("selected",active);
      b.setAttribute("aria-selected",String(active));
    });
    const head=$("thead");
    head.replaceChildren();
    const tr=node("tr");
    (state.view==="companies"?["기업명","분류","공식 채용 URL","상태","관리"]:["채용포털","URL / 검색 도메인","상태","관리"]).forEach(s=>tr.append(node("th",s)));
    head.append(tr);
    const q=$("query").value.trim().toLocaleLowerCase("ko");
    const showDeleted=$("show-deleted").checked;
    const entries=[...state.rows[state.view]].filter(x=>
      (showDeleted||statusValue(x)!=="deleted")&&
      (!q||(x.name+" "+(x.url||"")).toLocaleLowerCase("ko").includes(q))
    ).sort((a,b)=>a.name.localeCompare(b.name,"ko"));
    const body=$("list");body.replaceChildren();
    for(const item of entries){
      const tr=node("tr");if(statusValue(item)==="deleted")tr.className="deleted";
      const name=node("td",item.name,"name");tr.append(name);
      if(state.view==="companies")tr.append(node("td",item.group||"미분류"));
      const td=node("td",undefined,"url");
      if(item.url&&urlValid(item.url)){
        const a=node("a",item.url);
        a.href=item.url;a.target="_blank";a.rel="noopener noreferrer";
        td.append(a);
      }else td.append(node("span","미등록"));
      tr.append(td);
      const status=node("td");
      status.append(node("span",statusName(statusValue(item)),"state "+statusValue(item)));
      tr.append(status);
      const buttons=node("td");
      const makeButton=(label,action,clazz="")=>{
        const b=node("button",label,"smallbtn "+clazz);
        b.type="button";b.dataset.action=action;b.dataset.id=item.id;return b;
      };
      buttons.append(makeButton("수정","edit"));
      if(statusValue(item)==="deleted")buttons.append(makeButton("복원","restore"));
      else {
        if(state.view==="companies"){
          buttons.append(makeButton(statusValue(item)==="pass"?"패스 해제":"패스","pass"));
        }
        buttons.append(makeButton("삭제","delete","danger"));
      }
      tr.append(buttons);body.append(tr);
    }
    $("empty").hidden=entries.length!==0;
  }
  function showEditor(id=null) {
    if(!state.ready)return;
    const key=state.view, row=id?state.rows[key].find(x=>x.id===id):null;
    if(id&&!row)return;
    state.editKey=key;
    $("edit-id").value=row?row.id:"";
    $("edit-name").value=row?.name||"";
    $("edit-url").value=row?.url||"";
    $("edit-group").value=row?.group||"비상장기업";
    $("edit-status").value=statusValue(row||{});
    $("edit-alternative").value=row?.alternative_careers_url||"";
    $("edit-sector").value=row?.sector||"";
    $("edit-note").value=row?.official_url_note||"";
    $("editor-heading").textContent=(row?"정보 수정":"새 항목 추가")+" · "+(key==="companies"?"기업":"채용 전문포털");
    document.querySelectorAll(".company-only").forEach(e=>e.hidden=key!=="companies");
    $("edit-url").required=key==="portals";
    $("edit-advice").textContent=key==="companies"
      ?"공식 URL을 아직 못 찾았다면 비워두고 '패스'를 선택하세요. 직무 검색은 계속됩니다."
      :"포털 URL은 반드시 HTTPS 주소여야 합니다. 변경 즉시 다음 수집의 검색 도메인으로 사용됩니다.";
    $("editor").hidden=false;
    $("editor").scrollIntoView({behavior:"smooth",block:"start"});
    $("edit-name").focus({preventScroll:true});
  }
  const closeEditor=()=>{$("editor").hidden=true;state.editKey=null;};
  function suggestAdapter(url,existing) {
    if(!url)return "search";
    const host=new URL(url).hostname.toLowerCase();
    if(host.includes("greetinghr.com"))return "greeting";
    if(host.includes("ninehire.site"))return "ninehire";
    if(host.includes("breezy.hr"))return "breezy";
    if(existing?.url&&new URL(existing.url).hostname===host&&existing.adapter!=="search")
      return existing.adapter;
    return "landing";
  }
  function submitForm(event) {
    event.preventDefault();
    const key=state.editKey;if(!key)return;
    const id=$("edit-id").value;
    const name=$("edit-name").value.trim();
    const url=$("edit-url").value.trim();
    let status=$("edit-status").value;
    const isPortal=key==="portals";
    if(!name){alert("이름을 입력하세요.");return;}
    if(isPortal && !urlValid(url,true)){alert("채용 포털은 유효한 HTTPS URL이 필요합니다.");return;}
    if(url&&!urlValid(url,!isPortal?false:true)){alert("유효한 http/https URL을 입력하세요.");return;}
    if(!url&&!isPortal&&status==="active")status="pass";
    const duplicate=state.rows[key].some(x=>x.id!==id&&x.name.toLocaleLowerCase("ko")===name.toLocaleLowerCase("ko")&&statusValue(x)!=="deleted");
    if(duplicate){alert("같은 이름이 이미 있습니다. 기존 항목을 수정하세요.");return;}
    const current=id?state.rows[key].find(x=>x.id===id):null;
    const newId=id||("user-"+crypto.randomUUID().slice(0,16));
    const item=current?clone(current):{id:newId};
    item.name=name;item.url=url||null;item.monitor_status=status;
    if(!isPortal){
      item.group=$("edit-group").value;
      item.sector=$("edit-sector").value.trim()||item.sector||"로봇 관련";
      item.alternative_careers_url=$("edit-alternative").value.trim()||null;
      item.official_url_note=$("edit-note").value.trim();
      item.adapter=suggestAdapter(url,current);
    }
    if(current)state.rows[key][state.rows[key].findIndex(x=>x.id===id)]=item;
    else state.rows[key].push(item);
    closeEditor();render();
    setMessage(name+"을(를) 임시 목록에 반영했습니다. 아래 'GitHub에 변경사항 저장'을 누르면 실제 수집기에 적용됩니다.");
  }
  function changeStatus(id,action){
    const key=state.view,item=state.rows[key].find(x=>x.id===id);if(!item)return;
    if(action==="delete"&&!confirm("‘"+item.name+"’을 관리 대상에서 제외할까요?\n기존 공고 이력은 보존되며, 나중에 복원할 수 있습니다."))return;
    item.monitor_status=action==="delete"?"deleted":action==="restore"?"active":statusValue(item)==="pass"?"active":"pass";
    render();
    setMessage(item.name+" 상태를 '"+statusName(item.monitor_status)+"'으로 임시 변경했습니다. GitHub에 저장해야 적용됩니다.");
  }
  async function saveGitHub() {
    if(!state.ready)return;
    if(!changedCount()){setMessage("저장할 변경사항이 없습니다.","ok");return;}
    const token=$("github-token").value.trim();
    if(!token){setMessage("GitHub Fine-grained PAT을 입력하세요. 해당 저장소 Contents: Read and write 권한이 필요합니다.","err");return;}
    const button=$("commit-button");
    button.disabled=true;
    setMessage("기존 설정이 다른 곳에서 수정되지 않았는지 확인하는 중입니다.");
    try{
      const [a,b]=await Promise.all([readConfig("companies",token),readConfig("portals",token)]);
      if(a.sha!==state.hashes.companies||b.sha!==state.hashes.portals)
        throw new Error("저장 이후 외부에서 관리 설정을 수정했습니다. 중복 덮어쓰기를 막기 위해 중단했습니다. 현재 수정사항을 기록한 뒤 새로고침하세요.");
      const head=await request("/git/ref/heads/"+branch,token);
      const headSha=head.object.sha;
      const commit=await request("/git/commits/"+headSha,token);
      const files=[
        {path:filenames.companies,content:JSON.stringify(state.rows.companies,null,2)+"\n"},
        {path:filenames.portals,content:JSON.stringify(state.rows.portals,null,2)+"\n"}
      ];
      const blobs=await Promise.all(files.map(async file=>{
        const result=await request("/git/blobs",token,"POST",{content:file.content,encoding:"utf-8"});
        return {path:file.path,mode:"100644",type:"blob",sha:result.sha};
      }));
      const tree=await request("/git/trees",token,"POST",{base_tree:commit.tree.sha,tree:blobs});
      const next=await request("/git/commits",token,"POST",{
        message:"config: update employer and job portal monitoring sources via management page",
        tree:tree.sha,parents:[headSha]
      });
      await request("/git/refs/heads/"+branch,token,"PATCH",{sha:next.sha,force:false});
      state.original.companies=clone(state.rows.companies);
      state.original.portals=clone(state.rows.portals);
      const latest=await Promise.all([readConfig("companies",token),readConfig("portals",token)]);
      state.hashes.companies=latest[0].sha;state.hashes.portals=latest[1].sha;
      render();
      setMessage("GitHub 저장 성공 (커밋 "+next.sha.slice(0,10)+"). 기존 GitHub Actions가 자동 수집과 배포를 다시 시작합니다.","ok");
    }catch(e){
      setMessage("저장 실패: "+e.message+" · 수정 목록은 화면에 남아 있으니 원인을 확인한 뒤 다시 저장하세요.","err");
    }finally{
      $("github-token").value=""; // Never persist credentials in the browser or repository.
      button.disabled=false;
    }
  }
  document.addEventListener("DOMContentLoaded",()=>{
    document.querySelectorAll(".tab[data-view]").forEach(b=>b.addEventListener("click",()=>{
      state.view=b.dataset.view;closeEditor();$("query").value="";render();
    }));
    $("query").addEventListener("input",render);
    $("show-deleted").addEventListener("change",render);
    $("add-item").addEventListener("click",()=>showEditor());
    $("list").addEventListener("click",e=>{
      const btn=e.target.closest("button[data-action]");
      if(!btn)return;
      if(btn.dataset.action==="edit")showEditor(btn.dataset.id);
      else changeStatus(btn.dataset.id,btn.dataset.action);
    });
    $("edit-form").addEventListener("submit",submitForm);
    $("editor-cancel").addEventListener("click",closeEditor);
    $("editor-reset").addEventListener("click",closeEditor);
    $("edit-status").addEventListener("change",()=>{
      $("edit-url").required=state.editKey==="portals";
    });
    $("commit-button").addEventListener("click",saveGitHub);
    window.addEventListener("beforeunload",e=>{
      if(!changedCount())return;
      e.preventDefault();e.returnValue="";
    });
    loadConfig();
  });
})();
