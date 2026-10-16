> **ROBOT WATCH v05 (수집기) / v05 (웹) · 통합 업데이트 v10 · 2026-10-17**
>
> LinkedIn을 네 번째 채용 검색 경로로 추가했습니다. 매일 Bing 공개 색인에서 기업별 LinkedIn 공고 URL 후보를 확인하고, 웹페이지에는 기업별 LinkedIn 검색 바로가기를 표시합니다. LinkedIn 사이트 자체를 크롤링하거나 접근 제한을 우회하지 않습니다. 확인되지 않은 공고는 `확인 필요`이며 0건은 실제 채용 0건을 의미하지 않습니다.

# ROBOT WATCH — 국내 로봇기업 채용 자동 모니터링

### v10 추가 — 매일 두 번 자동 수집 및 웹페이지 수동 실행 버튼

- **정기 수집:** 매일 한국시간 **10:00 / 15:00** 두 차례 예약 실행. 이전 오전 7:10 예약은 제거했습니다. GitHub Actions 예약 시작 시각은 서버 부하에 따라 늦어질 수 있습니다.
- **수동 실행:** 웹페이지 상단의 **\`↻ 수동 실행 ↗\`** 버튼은 GitHub의 **\`Robot Watch Daily Monitor\`** 워크플로 페이지로 연결됩니다.
- GitHub 계정 **\`baesangyun\`**으로 로그인한 다음 우측 **\`Run workflow\` → 브랜치 \`main\` → \`Run workflow\`**를 누르면 실행됩니다. GitHub 실행이 완료되고 Pages 배포가 성공한 후 웹페이지를 새로고침하세요.
- **보안:** 정적 GitHub Pages 자체에서 서버 작업을 시작하는 기능은 없습니다. 계정 토큰이나 비밀번호를 웹페이지에 노출시키지 않도록 수동 버튼은 **인증된 GitHub Actions 화면으로 이동**합니다. 버튼을 누르는 것만으로 실행이 시작되는 것은 아닙니다.
- 기존 **\`push\`** 트리거는 코드 업데이트 후 자동 배포를 위해 유지되므로 업데이트 시 추가 실행이 발생할 수 있습니다.
- 기업 수, 공고 이력, 검색사이트 및 화면 필터는 변경하지 않았습니다.


**프로그램 v03 · 설치/운영 안내서 v07 · 2026-10-16**

한화로보틱스, 두산로보틱스 등 **국내 로봇 관련 기업 30개사**의 공개 채용정보를 매일 확인하고, PC와 휴대폰에서 **하나의 웹페이지**로 열람하는 프로그램입니다.

> **이 문서는 GitHub를 처음 사용하는 분을 위한 처음부터 끝까지의 설치 설명서입니다.** GitHub 화면에 표시되는 **영문 버튼·메뉴 이름 그대로** 적었습니다. PC에 GitHub 앱이나 Python을 설치하지 않아도 됩니다.
>
> 이 안내서는 `국내_로봇기업_채용모니터_v07_전문사이트통합.zip`을 기준으로 합니다. v07에는 기존 설치·삭제·폴더 경로 수정 안내를 보존하고, **프로그램 v03 개선**을 반영했습니다.
>
> **이미 저장소에 README.md가 있는 경우**: 저장소를 새로 만들 필요 없이 바로 **3단계 B**로 이동합니다. 이때는 ZIP 내부의 `README.md`를 제외한 프로그램 파일만 업로드하세요.

---


### 프로그램 v03 변경 내용 및 채용 전문사이트 연동 (2026-10-16)

- **잡코리아·사람인·인크루트 추가:** 회사별로 3개 전문 채용사이트 검색 링크 제공. 공개 검색엔진 RSS에 노출된 개별 공고 주소만 **확인 필요** 후보로 수집하며, 공개 검색엔진 색인에 없으면 나타나지 않습니다. **전체 공고 누락 방지 보장 불가**.
- **사람인 정식 API 선택 지원:** 사이트에서 이용 승인을 받고 발급된 키를 GitHub Actions Secret에 등록하면 진행 중 공고를 확인할 수 있습니다. 승인받지 않은 상태에서는 API로 수집하지 않습니다. 잡코리아 API도 사전 승인 절차가 별도로 필요하므로 승인 없이 내부 API를 호출하지 않습니다. 인크루트는 공식 기업별 채용 링크를 우선 활용합니다.
- **공고 리스트 글씨 소폭 확대**, 기본 **100건/페이지** (101번째부터 다음 페이지), 기존 디자인 유지.
- **기업 수집 현황:** 회사 분류 내림차순 → 같은 분류 내 기업명 내림차순. 회사별 공식·잡코리아·사람인·인크루트 출처 링크를 제공합니다.
- **오류 재점검:** 웹페이지 접속 성공과 실제 채용공고 자동 판독 성공을 별개로 표시합니다. 접근 실패·429는 강제 우회하지 않습니다.
- **로보스타 보안:** `gw.robostar.com` HTTPS 인증서 경고는 우회하지 않습니다. 검증된 잡코리아 기업 채용목록 주소를 별도 제공합니다.
- **엔젤로보틱스:** 실제 채용 중 공고 주소인 `https://recruit.angel-robotics.com/ko/recruit/notice`로 교체합니다.
- **검증:** 로컬 단위 테스트 21개를 통과했으며, 실제 사이트별 성공 여부는 GitHub Actions 실행 후 검증합니다.

#### 사람인 API 연동 (선택 사항)

1. [사람인 API 공식 신청/안내](https://oapi.saramin.co.kr/guide/info)에서 **API 이용을 신청**하고 승인받습니다.
2. 승인 이후 **본인의 access-key**를 발급받습니다. 이 키는 공개 GitHub 파일이나 이 채팅에 붙여넣지 마세요.
3. GitHub 저장소에서 **`Settings → Secrets and variables → Actions → New repository secret`**을 클릭합니다.
4. **`Name`**에 `SARAMIN_ACCESS_KEY`를 입력합니다.
5. **`Secret`**에 발급받은 키를 붙여넣고 **`Add secret`**을 클릭합니다.
6. **`Actions → Robot Watch Daily Monitor → Run workflow → Run workflow`**로 다시 실행합니다.
7. 기업 수집 현황의 검색 후보 기록과 공고 원문을 비교해 중복 및 마감 여부를 검증합니다.

> 보안상 API 키는 저장소 파일에 넣지 않습니다. 승인 없이 자동으로 가져오는 공고는 검색 후보로 표시되며 **모집 진행 보증이 아닙니다**. 사람인 공식 API는 1일 호출한도가 있습니다.

---

### 프로그램 v02 개선 내역 (2026-10-16)

- **근무국가 구분:** 기존 전체 공고 화면을 유지하면서 `국내 근무 / 해외 근무 / 근무지 미상 / 국내·해외 전체` 선택. 저장된 v01 이력도 재실행 시 국가 구분 반영.
- **채용공고 CSV:** 현재 검색·필터에 맞춰 내보내고 `국내해외` 열 추가.
- **베어로보틱스:** 공개 Breezy JSON의 중첩된 `country` 객체를 정상 문자열로 변환. 도시/국가를 함께 보고 국가 분류.
- **뉴로메카:** 그리팅 채용 플랫폼의 `/ko/o/공고번호` 링크 인식 규칙 추가. **실제 수집률 향상은 다음 GitHub Actions 실행에서 확인**해야 합니다.
- **로보티즈:** Ninehire `/jobs/` 링크 패턴 추가. HTTP 429·503에서는 `Retry-After`가 짧고 숫자일 때만 1회 재시도하며 무리한 접근 회피. **429가 계속되면 실패/제한으로 표시합니다.**
- **수집 상태:** 30개사 중 아직 자동 판독이 어려운 기업은 `제한/실패/미설정`으로 계속 정확히 표시하고, 채용 0건으로 오인하지 않음.
- **검증:** 기본 10개에 국가 구분·그리팅 링크 인식·Breezy 객체·기존 데이터 보존 테스트를 추가해 총 **14개 단위 테스트** 통과.

**중요:** 이번 버전은 검증되지 않은 기업 공고를 임의로 채우지 않습니다. `한화인·두산·HD현대`의 자바스크립트 기반 채용 목록은 사이트별 공식 데이터 제공 방식이 확인될 때까지 `제한`으로 남을 수 있습니다.

---
## 시작 전에 — 3가지만 알아두세요

1. **Repository(저장소)**: 소스코드와 데이터가 올라가는 GitHub의 폴더 같은 공간입니다.
2. **GitHub Actions**: GitHub 서버가 프로그램을 매일 자동 실행하는 기능입니다. **내 PC를 켜둘 필요가 없습니다.**
3. **GitHub Pages**: 결과를 웹사이트 주소로 보여 주는 기능입니다.

**우리가 만들 저장소 이름:** `robot-recruit-watch`  
**GitHub 계정:** `baesangyun`  
**배포 성공 후 예상 웹주소:** <https://baesangyun.github.io/robot-recruit-watch/>  
**수집 예정 시각:** 한국시간 매일 **오전 10:00 / 오후 3:00** 두 차례(지연 가능)

진행 상황은 아래 항목을 하나씩 체크하면 됩니다.

- [ ] 1. GitHub에 새 Repository 만들기 (이미 만들었다면 건너뛰기)
- [ ] 2. ZIP 압축 풀기
- [ ] 3. GitHub Repository에 프로그램 파일 전체 업로드
- [ ] 4. Actions 쓰기 권한 설정
- [ ] 5. Pages 배포 방식 설정
- [ ] 6. `Robot Watch Daily Monitor` 최초 수동 실행
- [ ] 7. 웹주소에서 채용 대시보드 확인
- [ ] 8. 다음날 자동 실행 확인

---

## 1단계. GitHub에서 새 저장소 만들기

### 1-1. 새 저장소 생성 화면 열기

1. 웹브라우저에서 <https://github.com> 열기 → GitHub 로그인
2. 화면 오른쪽 위의 **`+`** 클릭
3. 메뉴에서 **`New repository`** 클릭

또는 아래 주소로 바로 이동할 수 있습니다.

**바로가기: <https://github.com/new>**

### 1-2. `Create a new repository` 화면에 다음과 같이 입력

| GitHub 화면의 영문 항목 | 선택/입력할 값 | 설명 |
| --- | --- | --- |
| `Owner` | `baesangyun` | 본인 계정 선택 |
| `Repository name *` | `robot-recruit-watch` | 이름을 정확히 입력 |
| `Description` | `국내 로봇기업 채용 자동 모니터링` | 선택 입력 |
| `Choose visibility *` | **`Public`** | 무료 GitHub Pages 배포 목적 |
| `Add README` | **`Off`** | 프로그램 ZIP에 `README.md`가 이미 있으므로 중복 생성 방지 |
| `Add .gitignore` | `No .gitignore` (또는 추가하지 않음) | 프로그램에 필요 없음 |
| `Choose a license` | `No license` (또는 추가하지 않음) | 우선 추가하지 않음 |

**맨 아래 `Create repository`** 클릭.

> **왜 Public인가요?** GitHub Free 계정으로 GitHub Pages 사이트를 만들 때는 Public Repository가 필요합니다. **소스코드와 공개 채용 데이터도 누구나 볼 수 있습니다.** 비밀번호·토큰·개인정보는 절대 넣지 마세요. 나중에 `Settings → General → Danger Zone → Change repository visibility`에서 공개 범위를 바꿀 수 있지만, 비공개로 바꾸면 무료 플랜에서는 Pages 사용에 제한이 생깁니다.

### 1-3. 새 저장소 확인

생성 후 주소는 다음과 같습니다.

<https://github.com/baesangyun/robot-recruit-watch>

**저장소를 만들 때 `Add README: Off`였다면** 파일이 없는 화면에 `Quick setup — if you've done this kind of thing before` 영역이 보일 수 있습니다.

**저장소를 만들 때 `Add README: On`이었다면** 처음부터 `README.md` 파일이 보입니다. 이 경우 `Quick setup`은 표시되지 않습니다. **3단계 B**로 진행하세요.

**2026-10-16 확인된 실제 계정 상태:** `baesangyun/robot-recruit-watch`는 `Public` / `main`이며, 기본 `README.md` 파일 1개가 있습니다. 저장소를 또 만들 필요가 없습니다.

---

## 2단계. 프로그램 ZIP 파일 압축 풀기

1. 전달받은 **`국내_로봇기업_채용모니터_v05_폴더경로수정안내.zip`** 파일을 PC에 저장합니다.
2. Windows 파일 탐색기에서 해당 ZIP 파일을 마우스 오른쪽 버튼으로 클릭합니다.
3. **`모두 압축 풀기`** 또는 **`Extract All...`**을 선택합니다.
4. 압축을 푼 폴더를 엽니다. 안에 **`README.md`, `companies.json`, `crawler`, `docs`, `.github`** 등이 보여야 합니다.

### 정상적인 파일 구성

```text
robot-recruit-watch/              ← GitHub 저장소의 최상위 위치(Repository root)
├─ README.md                     ← 지금 읽는 설치 안내서
├─ companies.json                ← 30개 기업 목록
├─ requirements.txt              ← 자동 수집 의존성
├─ crawler/
│  └─ collect.py                 ← 채용공고 자동 수집 프로그램
├─ docs/
│  ├─ index.html                 ← 실제 웹사이트 시작 파일
│  ├─ styles.css
│  ├─ app.js
│  ├─ seed.js
│  └─ data/
│     └─ jobs.json              ← 채용 데이터 (최초에는 비어 있음)
├─ tests/
│  └─ test_collect.py
└─ .github/
   └─ workflows/
      └─ daily-monitor.yml      ← 매일 자동 실행 + Pages 배포 설정
```

**절대 하지 말아야 할 것**

- ZIP 압축파일 **하나만** GitHub에 올리지 마세요.
- `robot_recruit_monitor_v02`라는 **바깥 폴더만 추가된 중첩 구조**로 올리지 마세요.
- `.github/workflows/daily-monitor.yml`을 빼먹지 마세요. 빠지면 자동 실행 메뉴가 나타나지 않습니다.
- `docs/index.html`을 저장소 최상위로 옮기지 마세요. 이 프로그램은 `docs/` 구조를 사용합니다.

---

## 3단계. 압축 해제한 프로그램 파일을 GitHub에 업로드

**저장소:** <https://github.com/baesangyun/robot-recruit-watch>

GitHub의 `Quick setup` 화면은 **빈 저장소에서만** 표시됩니다. 저장소에 `README.md`가 하나라도 있으면 `Quick setup`을 찾을 필요가 없습니다.

### B. 저장소에 `README.md`가 이미 있는 경우 (**현재 사용자 화면: 이 방법으로 진행**)

현재 `Code` 화면에는 `README.md` 한 개가 보이고, 파일 목록 위에 **`Add file`** 버튼이 있습니다.

1. 저장소의 상단 메뉴에서 **`Code`**를 클릭합니다.
2. 파일 목록 바로 위에서 **`Go to file` 오른쪽, 초록색 `Code` 버튼 왼쪽의 `Add file`**을 클릭합니다.
3. 드롭다운에서 **`Upload files`**를 클릭합니다.
4. PC에서 ZIP 압축을 해제한 **안쪽 폴더를 열고**, `companies.json`, `requirements.txt`, `.github`, `crawler`, `docs`, `tests`를 선택합니다. **`README.md`는 제외**합니다. (이미 저장소에 있기 때문입니다.)
5. 선택한 파일과 폴더를 GitHub의 **`Drag files here to add them to your repository`** 영역으로 끌어놓습니다. ZIP 자체는 올리지 마세요.
6. 업로드 목록에서 `.github/workflows/daily-monitor.yml` 및 `docs/index.html` 등이 **원래 폴더 구조 그대로** 등록되었는지 확인합니다.
7. 화면 아래 **`Commit changes...`** 또는 **`Commit changes`**를 클릭하고, 메시지에는 `Upload Robot Watch v01 application`을 입력합니다.
8. 최종 **`Commit changes`**를 클릭하면 저장소에 반영됩니다.

> **현재 GitHub 저장소의 기본 README.md는 삭제할 필요가 없습니다.** 상세한 설치 안내 README는 별도로 제공한 파일을 쓰거나, 이후 GitHub의 README를 수정해 교체할 수 있습니다.

### A. `README.md`조차 없는 완전한 빈 저장소인 경우

1. `Code` 화면 중앙 **`Quick setup — if you've done this kind of thing before`** 영역을 찾습니다.
2. **`uploading an existing file`** 링크를 클릭합니다.
3. 압축 해제한 폴더의 **안쪽 내용 전체**(`README.md` 포함)를 끌어놓습니다.
4. 아래쪽 **`Commit changes`**를 눌러 등록합니다.

### 업로드 후 확인 (매우 중요)

`Code` 화면 최상위에 다음 항목이 모두 있어야 합니다.

- `.github`
- `crawler`
- `docs`
- `tests`
- `README.md`
- `companies.json`
- `requirements.txt`

그리고 `.github → workflows → daily-monitor.yml`을 클릭하여 파일이 열리는지 확인합니다.
`docs → index.html`도 클릭하여 파일이 열리는지 확인합니다.

**잘못된 예:** 최상위에 `robot_recruit_monitor_v02` 또는 `robot_recruit_monitor_v03`라는 폴더 **하나만** 보이고, 위 항목이 그 안에 들어 있으면 잘못 업로드한 것입니다. 이 경우 자동 실행 경로를 찾지 못할 수 있습니다.

> 업로드 시 `push`로 Actions가 자동 실행될 수 있습니다. 아직 4~5단계 권한이나 Pages를 설정하지 않았다면 최초 실행이 실패할 수 있으며, 이때는 설정 후 **6단계의 수동 재실행**을 진행하세요.

---

### C. `.github` 폴더가 업로드되지 않아 `github`라는 임시 이름으로 올린 경우

> **적용 상황:** Windows에서 `.github`를 `github`로 바꾸고 업로드한 결과, GitHub의 `Code` 화면에
> `github / workflows / daily-monitor.yml`이 표시되는 경우입니다.
>
> `.github/workflows`는 GitHub Actions에서 **정확히 요구하는 경로**입니다.
> `github/workflows`로 남아 있으면 **`Actions → Robot Watch Daily Monitor`가 표시되지 않습니다.**
> **2중 폴더 구조는 오류가 아닙니다.** 드래그 업로드가 실패한 정확한 원인은 당시 오류 메시지 없이는 확정할 수 없습니다.

#### ① 먼저 현재 파일을 엽니다

1. GitHub 저장소에서 상단 **`Code`**를 클릭합니다.
2. 왼쪽 폴더 목록 또는 파일 목록에서 **`github → workflows → daily-monitor.yml`**을 클릭합니다.
3. 오른쪽 위 연필 모양 **`Edit this file`**을 클릭합니다.
4. 편집 화면 상단에 다음 경로가 표시되는지 확인합니다.

   ```text
   robot-recruit-watch / github / workflows / [daily-monitor.yml]
   ```

   **중요:** 파란 글씨로 표시된 `github` 폴더 이름은 **직접 수정하는 칸이 아닙니다.**
   수정할 곳은 **오른쪽 `daily-monitor.yml`이 들어 있는 파일명 입력란**입니다.

#### ② 파일명 입력란에서 상위 폴더로 이동합니다

1. **`daily-monitor.yml` 입력란**을 클릭합니다.
2. 키보드 **`Home`**을 눌러 파일명 **맨 앞**으로 이동합니다.
3. 파일명을 지우지 않은 채 **`../`**를 입력합니다.
   - GitHub 편집 화면에서 경로가 한 단계 위인 `github` 쪽으로 이동합니다.
   - **`daily-monitor.yml` 글자는 그대로 남아 있어야 합니다.**
4. 다시 파일명 맨 앞에 **`../`**를 입력합니다.
   - 이제 저장소 최상위인 `robot-recruit-watch` 위치로 이동합니다.
5. 이어 파일명 맨 앞에 **`.github/workflows/`**를 입력합니다.
   - 입력 도중 GitHub가 `/`에 따라 폴더 경로를 분리해 표시할 수 있습니다.

**파일명 맨 앞에 입력하는 전체 경로 문자열은 다음과 같습니다.**

```text
../../.github/workflows/
```

위 문자열은 **순서 설명용**입니다. GitHub가 `../` 입력 직후 경로를 이동시킬 수 있으므로,
한 번에 붙여넣기보다는 **`../` → `../` → `.github/workflows/` 순으로 입력하며 상단 표시를 확인**하는 편이 안전합니다.

#### ③ 저장하기 전에 최종 경로를 확인합니다

**수정 전**

```text
robot-recruit-watch / github / workflows / daily-monitor.yml
```

**수정 후 (반드시 이렇게 보여야 함)**

```text
robot-recruit-watch / .github / workflows / daily-monitor.yml
```

1. 코드 본문은 수정하지 않습니다.
2. 오른쪽 위 **`Commit changes...`**를 클릭합니다.
3. 커밋 메시지에 예를 들어 `Move workflow to .github directory`를 입력합니다.
4. **`Commit changes`**를 눌러 확정합니다.
5. `Code` 탭에서 **`.github → workflows → daily-monitor.yml`** 파일이 보이는지 확인합니다.
6. 상단 **`Actions`**에서 **`Robot Watch Daily Monitor`**가 나타나는지 확인합니다. 표시가 늦으면 새로고침합니다.

**참고:** 임시 `github` 폴더에 해당 파일만 있었다면, 이동 후 비어 있는 폴더는 Git 기록에 남지 않으므로 화면에서도 사라집니다. 다른 파일이 있으면 그 폴더는 계속 남습니다.

**주의:** 이 방법은 **이미 업로드된 파일의 경로를 바꾸는 방법**입니다. 기존 `.github/workflows/daily-monitor.yml`이 이미 있다면 같은 경로로 다시 이동하지 마세요. 파일이 중복되거나 충돌할 수 있습니다. **저장소 전체를 삭제하거나 새로 만들 필요는 없습니다.**

---

## 4단계. GitHub Actions 권한 설정

수집된 데이터를 `docs/data/jobs.json`에 매일 저장하려면 쓰기 권한이 필요합니다.

1. 저장소 상단 **`Settings`** 클릭
2. 왼쪽 메뉴 **`Actions` → `General`** 클릭
3. 화면 아래로 내려 **`Workflow permissions`** 찾기
4. **`Read and write permissions`** 선택
5. **`Save`** 클릭

`Read and write permissions`가 보이지 않거나 선택할 수 없으면 현재 계정/조직 정책의 제한일 수 있습니다. 우선 5단계로 넘어가지 말고 저장소 권한을 확인하세요.

**설정 바로가기:** <https://github.com/baesangyun/robot-recruit-watch/settings/actions>

---

## 5단계. 웹페이지 게시 설정 (GitHub Pages)

1. 저장소 상단 **`Settings`** 클릭
2. 왼쪽 메뉴 **`Pages`** 클릭
3. **`Build and deployment`** 섹션 찾기
4. **`Source`** 항목의 드롭다운에서 **`GitHub Actions`** 선택
5. **추가로 표시되는 `Jekyll` 또는 `Static HTML` 템플릿의 `Configure` 버튼은 누르지 마세요.** 이미 `daily-monitor.yml`에 배포 절차가 포함돼 있습니다.

**설정 바로가기:** <https://github.com/baesangyun/robot-recruit-watch/settings/pages>

> Pages 설정에서 `Deploy from a branch`를 선택하지 마세요. 이 프로젝트는 **`GitHub Actions`**를 사용하는 구성입니다. GitHub Free 계정이라면 Public Repository인지 확인하세요.

---

## 6단계. 최초로 자동 수집 프로그램 실행하기

1. 저장소 상단 **`Actions`** 클릭
2. 왼쪽 **`All workflows`** 아래에서 **`Robot Watch Daily Monitor`** 클릭
3. 오른쪽의 **`Run workflow`** 클릭
4. **`Branch: main`** 또는 `Use workflow from: Branch: main`인지 확인
5. 펼쳐진 메뉴에서 다시 **`Run workflow`** 클릭
6. 잠시 기다린 뒤 실행 목록에 새로운 실행 건이 나타나면 해당 실행 건을 클릭
7. **`collect-and-deploy`** 작업을 열고 단계별 결과 확인

아래 주요 단계들이 성공했는지 확인합니다.

| 로그의 단계명 | 성공 시 의미 |
| --- | --- |
| `Checkout repository` | 파일을 불러옴 |
| `Setup Python 3.12` | 수집 환경 구성 |
| `Install scraper dependencies` | 필요한 패키지 설치 |
| `Collect public recruitment posts` | 기업별 공개 채용정보 확인 |
| `Commit current data and history` | 수집 결과 JSON 저장 |
| `Configure GitHub Pages` | Pages 설정 |
| `Upload website artifact` | 웹페이지 파일 올림 |
| `Deploy GitHub Pages` | 웹페이지 배포 완료 |

**초록색 체크(✓)**가 나타나면 실행 성공입니다. **빨간색 X**는 실패입니다. 실행 건을 클릭한 뒤 실패한 단계의 로그를 확인하세요.

**Actions 바로가기:** <https://github.com/baesangyun/robot-recruit-watch/actions>

**중요:** `workflow_dispatch` 수동 실행 버튼이 보이려면 `.github/workflows/daily-monitor.yml` 파일이 `main` 브랜치에 있어야 합니다. GitHub에서는 워크플로가 등록된 직후 목록 표시가 잠시 지연될 수 있습니다.

---

## 7단계. 웹사이트 열기

1. 저장소 상단 **`Settings` → `Pages`**로 이동
2. `GitHub Pages` 섹션에서 **`Visit site`** 버튼 클릭
3. 처음 배포한 직후라면 잠시 기다린 후 새로고침

정상 배포 시 예상 주소:

**<https://baesangyun.github.io/robot-recruit-watch/>**

이 주소는 **배포 완료 후에만 작동**합니다. 배포 후 표시까지 수 분, 경우에 따라 약 10분 걸릴 수 있습니다.

### 정상 작동 확인 항목

- [ ] `ROBOT WATCH` 화면이 열림
- [ ] 30개 기업 목록이 표시됨
- [ ] 상단에 **최종 수집 시각**이 표시됨
- [ ] 기업별 **성공 / 제한 / 실패 / 미설정** 상태를 볼 수 있음
- [ ] 채용공고 검색과 **직무 / 지역 / 기업 / 상태** 필터가 작동함
- [ ] 채용공고 링크 클릭 시 원문으로 이동함
- [ ] CSV 다운로드 버튼이 작동함

> **공고가 0건이어도 정상 화면일 수 있습니다.** 실제 공고가 없거나 대상 회사 사이트의 접근/판독이 제한되었을 수 있습니다. 반드시 **기업별 수집 상태와 최종 수집 시각**을 함께 확인하세요.

---

## 8단계. 매일 자동 수집 확인

`daily-monitor.yml`에는 다음 일정이 이미 포함돼 있습니다.

```yaml
schedule:
  - cron: '10 22 * * *'
```

- **UTC 01:00** = **한국시간 오전 10:00**\n- **UTC 06:00** = **한국시간 오후 3:00**
- 프로그램이 **GitHub 서버에서 실행**됩니다. PC를 끄거나 브라우저를 닫아도 됩니다.
- GitHub Actions 예약 작업은 **정각 실행 보장이 없고 지연 또는 드물게 누락될 수 있습니다.**
- 공고를 보는 것만으로 수집이 실행되는 것이 아니라, 예약 실행/수동 실행으로 데이터가 갱신됩니다.
- GitHub의 정책에 따라 오랫동안 활동이 없는 공개 저장소는 예약 워크플로가 비활성화될 수 있습니다. 그때는 `Actions`에서 다시 활성화해야 합니다.

**다음날 확인:** `Actions → Robot Watch Daily Monitor`에서 오전 10시 및 오후 3시 예약 실행이 기록되었는지, 그리고 대시보드의 **최종 수집 시각**이 바뀌었는지 확인하세요.

---

## 9단계. 채용 데이터가 어떻게 표시되나요?

| 구분 | 기준 |
| --- | --- |
| **신규 (NEW)** | 기존 데이터와 비교해 새로 확인된 공식 채용공고. **첫 실행의 기존 공고는 전부 신규로 표시하지 않음** |
| **진행** | 공식 공개 채용 목록에서 확인된 공고 |
| **마감** | 확인된 공고 마감일이 지난 경우 |
| **확인필요** | 검색엔진에서만 찾았거나 실제 모집 중인지 확인되지 않은 공고, 공식 목록에서 사라졌지만 마감 여부가 불명확한 공고 |
| **기업별 성공** | 수집기가 정해진 기준에 따라 공고를 추출한 상태. 모든 공고의 완전성을 보장하지 않음 |
| **기업별 제한/실패/미설정** | 사이트 접근·판독 제한, 통신 오류 또는 공식 URL 미등록. **채용 0건이라는 뜻이 아님** |

**주의:** 30개사를 등록했지만, 전 기업 채용공고를 빠짐없이 자동 수집할 수 있는 것은 아닙니다. 일부 기업은 별도 수집기 수정이 필요합니다. 기업의 공고 지원 전에는 **반드시 채용 원문**으로 실제 공고 상태를 재확인하세요.

---

## 10단계. 문제가 생겼을 때 (GitHub 영문 메뉴 기준)

| 증상 | 어디서 무엇을 확인하나요? |
| --- | --- |
| `Actions`에 `Robot Watch Daily Monitor`가 없음 | `Code → .github → workflows → daily-monitor.yml`이 있는지, 브랜치가 `main`인지 확인. `github/workflows`로 올라갔다면 **3단계 C**대로 경로 변경 |
| `Run workflow`가 안 보임 | `Actions → Robot Watch Daily Monitor` 화면인지 확인. 워크플로가 기본 브랜치 `main`에 있어야 함 |
| `Permission denied` / `403` / 데이터 커밋 실패 | `Settings → Actions → General → Workflow permissions → Read and write permissions → Save` |
| `Configure GitHub Pages` 또는 `Deploy GitHub Pages` 실패 | `Settings → Pages → Build and deployment → Source: GitHub Actions` 확인. Public 저장소인지 확인 |
| `Visit site`가 안 보임 | `Actions`의 `Deploy GitHub Pages` 성공 여부를 확인한 뒤 `Settings → Pages` 새로고침 |
| 웹사이트 `404` 오류 | 배포 완료 후 최대 약 10분 기다림. 저장소명과 주소 철자 확인 |
| 채용공고 0건 | `Actions → Robot Watch Daily Monitor → 최근 실행 → Collect public recruitment posts` 로그, 화면의 수집 상태 확인 |
| 웹 화면은 열리는데 예전 데이터가 보임 | Actions 실행 날짜와 `docs/data/jobs.json` 갱신 여부 확인. 브라우저 새로고침 |
| 일부 기업이 실패 또는 제한 | 해당 기업의 채용페이지 구조·접근 제한 문제일 수 있음. 원문 확인 및 전용 수집기 보완 필요 |
| 업로드한 파일을 찾을 수 없음 | `Code`에서 바깥 폴더가 추가로 생기지 않았는지, `.github`가 누락되지 않았는지 확인 |

### 문제 해결을 요청할 때 알려줄 정보

`Actions → Robot Watch Daily Monitor → 가장 최근 실행`으로 들어가 **빨간 X가 난 작업 이름과 오류 메시지**를 보내 주세요. 비밀번호와 개인 토큰은 보내지 마세요.

---

## 11단계. 이후 프로그램 수정 방법

- **기업 추가·수정:** `Code → companies.json`에서 해당 파일을 열고 오른쪽 연필(`Edit this file`) 버튼 → 수정 → `Commit changes...`
- **프로그램 수정:** 수정할 파일을 GitHub에 올리고 `Commit changes...`
- **수집 시간 변경:** `.github/workflows/daily-monitor.yml`의 `schedule` 아래 `cron` 값을 **UTC 시간** 기준으로 수정
- **수동 재실행:** `Actions → Robot Watch Daily Monitor → Run workflow`
- **실행 이력 확인:** 대시보드의 실행 이력 화면 또는 `Actions` 실행 목록

기존 코드를 함부로 삭제하거나 폴더 구조를 변경하지 마세요.

---

## 12단계. 저장소(Repository) 전체 삭제하는 방법

> ⚠️ **삭제 대상: 저장소 전체** — `README.md`, `companies.json`, `crawler/`, `docs/`, `tests/`, `.github/` 등 저장소 안에 있는 모든 파일과 GitHub Actions·Pages 설정에 영향을 줍니다. 이 작업은 **파일 1개 삭제**와 완전히 다릅니다. 삭제 전 필요한 코드를 별도로 백업하세요. 본인의 GitHub 계정 자체가 삭제되는 것은 아닙니다.

**GitHub 화면 영문 메뉴 그대로 진행**

1. 저장소 <https://github.com/baesangyun/robot-recruit-watch>에 들어갑니다.
2. 상단 **`Settings`** 클릭.
3. 왼쪽 메뉴 **`General`** 선택(보통 기본으로 선택됨).
4. 화면을 맨 아래로 내려 **`Danger Zone`**을 찾습니다.
5. **`Delete this repository`** 클릭.
6. 확인창에서 **`I want to delete this repository`** 클릭.
7. 경고를 읽고 **`I have read and understand these effects`** 클릭.
8. 요청하는 입력란에 아래 저장소 전체 이름을 정확히 입력합니다.

   ```text
   baesangyun/robot-recruit-watch
   ```

9. 마지막 **`Delete this repository`** 버튼을 눌러 삭제를 확정합니다. GitHub가 로그인이나 추가 인증을 요구하면 화면 지시에 따르세요.
10. 저장소 목록에서 해당 저장소가 더 이상 보이지 않는지 확인합니다.

**삭제 설정 화면 바로가기:** <https://github.com/baesangyun/robot-recruit-watch/settings>

**주의사항**

- **`Delete this repository` 버튼은 저장소 관리자(Admin) 권한이 있어야 표시·실행**할 수 있습니다.
- 이 저장소가 삭제되면 **이 프로젝트의 웹주소와 예약 수집도 정상적으로 유지되지 않습니다.** 다시 운영하려면 저장소 생성부터 다시 설정해야 합니다.
- GitHub는 **일부 삭제된 저장소에 한해 90일 이내 복구를 지원**할 수 있지만, 복구가 보장되는 것은 아닙니다. 안전한 백업을 먼저 만드세요.
- Public 저장소에서 타인이 만든 Fork(복제 저장소)가 있다면 원본 삭제가 그 Fork를 삭제하지는 않습니다.

---

## 13단계. 저장소 안에서 파일 1개씩 삭제하는 방법

> ⚠️ **삭제 대상: 선택한 파일 1개** — 저장소 자체는 유지됩니다. 원하는 파일만 반복해서 삭제할 때 사용하는 방법입니다.

**예: `README.md` 파일 1개 삭제**

1. 저장소 상단 **`Code`** 클릭.
2. 파일 목록에서 삭제할 파일(예: **`README.md`**) 클릭. 하위 폴더 안 파일이라면 해당 폴더를 차례대로 열어 파일을 클릭합니다.
3. 파일 내용을 보여 주는 화면의 **오른쪽 위 `...`(점 3개 / More file actions)** 메뉴 클릭.
4. 메뉴에서 **`Delete file`** 클릭.
5. 삭제 내용을 확인하고, **`Commit message`**에 삭제 사유 입력(예: `Remove old README`).
6. **`Commit changes...`** 또는 **`Commit changes`** 클릭. 브랜치를 선택하라는 화면이 나타나면 작업 목적에 맞게 직접 커밋하거나 새 브랜치를 선택합니다.
7. 기본 브랜치에 반영되면 **`Code`** 파일 목록으로 돌아가서 해당 파일이 사라졌는지 확인합니다.

**하위 폴더 파일 삭제 예시**: `Code` → `.github` → `workflows` → `daily-monitor.yml` → `...` → `Delete file` → `Commit changes`.

**주의사항**

- **`docs/index.html`을 삭제하면 웹페이지가 열리지 않을 수 있습니다.**
- **`.github/workflows/daily-monitor.yml`을 삭제하면 이 프로그램의 자동 수집·배포 워크플로가 사라집니다.**
- GitHub에서 파일을 삭제하고 커밋해도 **기존 Git 커밋 이력에는 그 파일이 남아 있을 수 있습니다.** 비밀번호·토큰을 올린 경우 파일 삭제만으로 정보가 완전히 제거되지는 않습니다.
- 여러 파일을 삭제하려면 위 절차를 **파일마다 1회씩 반복**합니다. 저장소 전체를 지울 필요는 없습니다.
- GitHub 화면에서 메뉴가 달라 보인다면 **GitHub 공식 안내**의 파일 삭제 화면과 비교하세요.

**공식 문서**: [Deleting files in a repository](https://docs.github.com/en/repositories/working-with-files/managing-files/deleting-files-in-a-repository)

---

## 개발자용 (일반 사용자는 생략 가능)

로컬 Python 환경에서 수집기 테스트:

```bash
python -m pip install -r requirements.txt pytest
python -m pytest -q
python crawler/collect.py --no-search
```

위 명령은 **개발자 테스트 용도**이며 GitHub 사용자는 PC에서 실행할 필요가 없습니다.

## 버전 이력

| 구분 | 버전 | 내용 |
| --- | --- | --- |
| 프로그램 | v01 | 30개사 목록·채용 수집기·대시보드·GitHub Actions 구현 |
| 프로그램 | v02 | 근무국가 분리·뉴로메카 수집 개선 |
| 프로그램 | v03 | 채용 전문사이트 후보·승인 API 연동·100건/페이지·가독성·분류 내림차순·안전한 대체 출처 |
| 설치 안내서 | v07 | v01~v06 전체 절차 유지 + 전문사이트 승인 및 연결 방법 |
| 설치 안내서 | v02 | 최초 GitHub 설치·운영 설명서 |
| 설치 안내서 | v03 | 기본 README가 이미 있는 GitHub 화면에 맞춰 `Add file → Upload files` 경로 수정, 중복 파일 제외 설명 추가 |
| 설치 안내서 | v04 | GitHub 저장소 전체 삭제와 파일 1개씩 삭제하는 실제 영문 메뉴·경고·확인 순서 추가 |
| 설치 안내서 | v05 | `github/workflows`를 `.github/workflows`로 직접 옮기는 GitHub 편집 화면 조작법 추가 |

### 공식 GitHub 도움말

- [Creating a new repository](https://docs.github.com/en/repositories/creating-and-managing-repositories/creating-a-new-repository)
- [Adding a file to a repository](https://docs.github.com/en/repositories/working-with-files/managing-files/adding-a-file-to-a-repository)
- [Configuring a publishing source for your GitHub Pages site](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site)
- [Creating a GitHub Pages site](https://docs.github.com/en/pages/getting-started-with-github-pages/creating-a-github-pages-site)
- [Manually running a workflow](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/manually-run-a-workflow)
- [Deleting a repository](https://docs.github.com/en/repositories/creating-and-managing-repositories/deleting-a-repository)
- [Deleting files in a repository](https://docs.github.com/en/repositories/working-with-files/managing-files/deleting-files-in-a-repository)

---

**ROBOT WATCH / 국내 로봇기업 채용 자동 모니터링**  
프로그램 v03 / README v07 / 작성 2026-10-16

> v02 개발 이력: 원본 v01 코드와 배포 구조 유지, `crawler/collect.py`, `docs/app.js`, `docs/index.html`, 테스트만 기능 변경.
## v04 — 전문 채용사이트 개별 공고 URL 실수집 개선

- `board_company_pages.json`에 검증된 기업별 공개 채용목록 주소만 추가합니다.
- 잡코리아·사람인·인크루트에서 검색 결과 외에 기업별 채용목록을 제한적으로 점검합니다.
- robots.txt 정책을 먼저 확인하고, 허용되지 않으면 해당 목록 수집을 중단합니다.
- 개인 로그인·자동 인증·TLS 보안경고 우회는 사용하지 않습니다.
- 목록에서 발견한 공고는 별도 API 확인 전까지 **확인 필요**로 표시합니다.
- 누락 없는 완전 수집을 보장하지 않습니다. 수집 불가 사유는 기업별 현황에 남깁니다.
