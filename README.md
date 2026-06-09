# 상권 입지 평가 매출예측 SaaS MVP

엑셀 계산 모델을 업종별 파이썬 모듈로 변환해 실행하는 Streamlit 배포용 MVP 앱입니다.

## 2026-06-09 PPT 화면 흐름 반영

업로드된 `01-UP-.pptx` 기준으로 기존 Streamlit 앱에 다음 화면 흐름을 반영했습니다.

- 서비스 홈: 업종선택 → 현장조사 입력 → 결제 및 보기 → 결과 다운로드 흐름 표시
- 입력 마법사: 기존 업종별 계산 마법사를 유지하면서 `간단 주소(구/동까지)` 입력 추가
- 회원가입: 개인/기업 회원 구분, 회사명, 연락처, 주소, 수신동의 항목 반영
- 마이페이지: 회원정보 수정 형태와 저장 기록/다운로드 이력 화면 구성
- 관리자: 회원관리, 결제내역, 팝업관리, SEO 설정 탭 구성
- 향후 업종 추가 안내: 준비 중 업종은 업종별 엑셀 로직 연결 후 활성화하는 구조 유지

이번 반영은 기존 계산/결제/저장 로직을 보존하면서 화면 흐름과 운영 메뉴를 추가한 버전입니다.

## 1단계 구조: 다중 업종 확장

사이드바의 업종 선택 박스에서 최대 42개 업종을 선택할 수 있습니다.
현재 계산 엔진이 연결된 업종은 아래 3개이며, 나머지는 업종별 엑셀 파일 분석 후 순차적으로 활성화합니다.

- 음식점 / 해장국
- 피자
- 치킨

업종별 계산 코드는 `industries/` 폴더 아래에 분리되어 있습니다.

- `industries/haejang_calc.py`: 음식점 / 해장국 계산 모듈
- `industries/haejang_excel_map.py`: 해장국 웹 입력값과 원본 엑셀 셀 매핑, 기본값 검증
- `industries/pizza_calc.py`: 피자 계산 모듈
- `industries/chicken_calc.py`: 치킨 계산 모듈
- `industries/chicken_excel_map.py`: 치킨 웹 입력값과 원본 엑셀 셀 매핑, 기본값 검증
- `industries/registry.py`: 업종 목록, 준비 중 업종, 계산 모듈 연결

## 2단계 구조: Supabase 인증 및 데이터 저장

현재 테스트 배포본은 회원가입 없이 `게스트로 시작`할 수 있습니다.
기존 계정 로그인과 분석 결과 저장은 Supabase를 사용합니다.
로컬 SQLite DB 대신 Supabase Auth와 Supabase Postgres 테이블에 연결됩니다.

`.streamlit/secrets.toml` 파일을 만들고 아래 값을 넣으세요.

```toml
SUPABASE_URL = "https://프로젝트ID.supabase.co"
SUPABASE_KEY = "Supabase anon public key"
ADMIN_EMAILS = "admin@example.com,owner@example.com"
PORTONE_IMP_CODE = "imp00000000"
PORTONE_PG = "html5_inicis"
PORTONE_PAY_METHOD = "card"
PORTONE_PAYMENT_AMOUNT = 1000
PORTONE_PRODUCT_NAME = "상권 매출 예측 분석 리포트"
```

Streamlit 공식 문서 기준으로 `.streamlit/secrets.toml`은 앱을 실행하는 프로젝트 폴더 안의 `.streamlit` 폴더에 둘 수 있습니다.
Supabase Python 클라이언트는 이메일/비밀번호 로그인에 `sign_in_with_password`를 사용합니다.

Supabase SQL Editor에서 아래 SQL을 먼저 실행하세요.

```sql
create table if not exists public.profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  email text not null,
  name text,
  role text not null default 'User',
  payment_status text not null default 'unpaid',
  created_at timestamptz not null default now()
);

create table if not exists public.analysis_results (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  industry_code text not null,
  industry_name text not null,
  store_name text not null,
  daily_sales_thousand numeric not null,
  monthly_sales_thousand numeric not null,
  contribution_profit_thousand numeric not null,
  input_json jsonb not null,
  result_json jsonb not null,
  created_at timestamptz not null default now()
);

create table if not exists public.payment_records (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  merchant_uid text,
  imp_uid text,
  amount numeric,
  status text not null default 'paid',
  raw_response jsonb,
  created_at timestamptz not null default now()
);

alter table public.profiles enable row level security;
alter table public.analysis_results enable row level security;
alter table public.payment_records enable row level security;

create policy "Users can read own profile"
on public.profiles for select
using (auth.uid() = id);

create policy "Users can insert own profile"
on public.profiles for insert
with check (auth.uid() = id);

create policy "Users can update own profile"
on public.profiles for update
using (auth.uid() = id)
with check (auth.uid() = id);

create policy "Users can read own analysis results"
on public.analysis_results for select
using (
  auth.uid() = user_id
  or exists (
    select 1 from public.profiles
    where profiles.id = auth.uid()
      and profiles.role = 'Admin'
  )
);

create policy "Users can insert own analysis results"
on public.analysis_results for insert
with check (auth.uid() = user_id);

create policy "Users can read own payment records"
on public.payment_records for select
using (
  auth.uid() = user_id
  or exists (
    select 1 from public.profiles
    where profiles.id = auth.uid()
      and profiles.role = 'Admin'
  )
);

create policy "Users can insert own payment records"
on public.payment_records for insert
with check (auth.uid() = user_id);
```

관리자 계정은 `ADMIN_EMAILS`에 들어 있는 이메일로 로그인하면 `Admin` 역할로 저장됩니다.

주의: 현재 결제 성공 처리는 포트원 결제창 콜백 신호를 Streamlit이 감지해 `profiles.payment_status`를 `paid`로 바꾸는 MVP 로직입니다.
상용 배포 전에는 포트원 REST API의 결제 단건조회/서버 검증 또는 웹훅 검증을 붙여서 결제금액과 주문번호를 반드시 서버에서 검증해야 합니다.

이전 MySQL/SQLite 설정은 더 이상 사용하지 않습니다.

## 3단계 구조: 게스트 시작, 로그인, Admin 권한

사이트에 접속하면 `회원가입 없이 시작` 버튼과 로그인 화면이 먼저 표시됩니다.
게스트 모드는 결과 확인용이며 분석 결과 저장은 제공하지 않습니다.
기존 회원 인증은 Supabase Auth가 처리하고, 서비스 권한/결제 상태는 `profiles` 테이블에 저장됩니다.

권한은 아래 두 가지입니다.

- `User`: 일반 회원. 본인이 저장한 분석 결과만 조회합니다.
- `Admin`: 관리자. 결제 여부와 관계없이 모든 회원의 분석 결과를 조회합니다.

상업용 배포에서는 Streamlit Secrets에 `ADMIN_EMAILS`를 등록해 관리자 이메일을 지정할 수 있습니다.

```toml
ADMIN_EMAILS = "admin@example.com,owner@example.com"
```

`ADMIN_EMAILS`에 포함된 이메일로 로그인하면 자동으로 `Admin` 권한이 부여됩니다.

## 4단계 구조: 결제 권한 로직

일반 `User` 계정은 입력을 마친 뒤 `분석 결과 보기` 버튼을 눌러도 바로 결과가 표시되지 않습니다.
결제 전에는 결과 화면 대신 `결제가 필요합니다` 안내와 포트원 카드 결제창 버튼이 표시됩니다.

포트원 결제가 완료되면 JavaScript 콜백이 `window.parent.postMessage`로 결제 결과를 부모 화면에 전달하고, 동시에 Streamlit이 감지할 수 있도록 URL query parameter를 갱신합니다.
Streamlit은 이 성공 신호를 감지하면 Supabase `profiles.payment_status` 값을 `paid`로 업데이트하고, `payment_records` 테이블에 결제 기록을 저장한 뒤 최종 매출 예측 결과를 표시합니다.

권한 조건은 아래처럼 동작합니다.

- `User` + `unpaid`: 결과 숨김, 결제 안내 표시
- `User` + `paid`: 결과 표시
- `Admin`: 결제 여부와 관계없이 결과 표시

현재 결제 버튼은 포트원 JavaScript SDK를 호출하는 프론트 연동 MVP입니다.
상용 배포 전에는 포트원 서버 검증 API와 웹훅 검증을 추가해야 합니다.

## 입력 화면 원칙

사용자가 처음 접속했을 때 분석 입력칸은 기존 엑셀 예시값으로 미리 채워지지 않습니다.
텍스트, 숫자, 선택 입력은 빈칸 또는 `선택 안 됨` 상태에서 시작합니다.

## UX/UI 개선

Streamlit 기본 스타일 위에 커스텀 CSS를 적용했습니다.

- 버튼 색상과 hover 효과
- 입력창 border-radius
- 데이터 표와 메트릭 영역의 정돈된 테두리
- 사이드바 배경과 경계선
- 폰트 스타일
- 4단계 입력 진행률 표시바

입력 화면은 `st.session_state`를 사용한 단계형 UI로 구성됩니다.
사용자는 `다음`과 `이전` 버튼을 누르며 카테고리별로 입력합니다.

- 1단계: 업종 선택 및 기본 정보
- 2단계: 배후 세대 및 통행량 입력
- 3단계: 주변 경쟁점 정보
- 4단계: 투자금 및 비용 입력
- 5단계: 결제 및 분석 결과
- 저장 기록

입력값은 세션 상태에 보존되므로 이전 단계로 돌아갔다가 다시 다음 단계로 이동해도 작성 중인 값이 유지됩니다.

결과는 아래 순서로만 계산됩니다.

1. 사용자가 직접 입력
2. 단계별 입력 완료
3. `분석 결과 보기` 버튼 클릭
4. 필수 입력값 검증
5. 결제 권한 확인
6. 계산 실행
7. 결과 표시

## 엑셀 100% 동일성 원칙

상업용 최종 MVP에서는 사용자가 웹에 원본 엑셀 테스트와 동일한 값을 입력했을 때, 최종 예측 매출액과 손익 결과가 엑셀과 소수점까지 동일해야 합니다.

이를 위해 업종별 계산 모듈은 단순 보정계수가 아니라 원본 엑셀의 아래 항목을 모두 이식해야 합니다.

- 입력 시트의 노란색 입력칸
- `가중치 기준표`
- `기초자료`
- `SIMULATION`
- 월별지수와 요일지수
- 경쟁점 점수표
- 투자손익 및 손익률 계산식

### 해장국 현재 상태

해장국은 이번 단계에서 아래 항목을 코드로 고정했습니다.

- 원본 파일: `01-pgm.xlsx`
- 최종 출력 셀: `표지!D9`
- 핵심 입력 셀: 조사월 `E8`, 요일 `L8`, 지역 `G13`, 행정 단위 `G14`, 배후세대/인구 `E25/I25/J25/L25/P25`, 통행량 `E65:P75`, 경쟁점 `E86:P106`, 투자비 `D113:G113`
- 검증 통과 항목: 최종 일매출, 1일 통행량, 주고객비율, 20대 비율, 통행인/세대/직장인 잠재수요, 후보점 경쟁점수, 총 경쟁점수, 월별지수, 요일지수

기본값 기준 원본 엑셀 `표지!D9`는 `1,799.028432천원`, 파이썬 계산값은 `1,799.0284318788188천원`입니다.

아직 남은 상업용 검증은 사용자가 입력값을 바꾸는 시나리오별 재계산 검증입니다. 예를 들어 월, 요일, 지역, 통행량 일부, 후보점 면적, 경쟁점 거리, 투자비를 변경했을 때 원본 엑셀과 파이썬 결과가 계속 일치하는지 테스트 케이스를 확장해야 합니다.

### 치킨 현재 상태

치킨은 이번 단계에서 아래 항목을 코드로 고정했습니다.

- 원본 파일: `01-chicken.xlsx`
- 최종 출력 셀: `표지!F11`
- 핵심 입력 셀: 조사월 `D6`, 요일 `K6`, 지역 선택 `B11/D11/F11/H11/J11/L11`, 배후세대/인구 `D22/F22/J22/L22`, 아파트 평형 `D28:H28`, 아파트 가격대 `D32:J32`, 통행량 `D39:O45`, 경쟁점 `D56:R76`, 투자비 `C83:E83`
- 치킨 전용 추가 입력: 홀판매여부 `P열`, 배달 여부 `Q열`, 테이크아웃 여부 `R열`
- 검증 통과 항목: 최종 일매출, 1일 통행량, 상권유형 결정비율, take-out 잠재수요, 배달 잠재수요, 내점 고객 잠재수요, 판매 방식별 후보점 배분액, 월/요일 보정 전 매출, 월별지수, 요일지수

기본값 기준 원본 엑셀 `표지!F11`은 `1,505.5666228034672천원`, 파이썬 계산값은 `1,505.5666228034672천원`입니다.

치킨은 더 이상 보정계수로 최종값만 맞춘 구조가 아닙니다. `take-out`, `배달`, `내점 고객` 3개 잠재수요와 판매 방식별 경쟁점수 배분 수식을 별도 파이썬 엔진으로 분리했습니다.

현재 피자는 기본값 중심의 보정 MVP 상태입니다.
해장국은 기본값 및 핵심 중간값 검증을 통과했습니다.
치킨은 기본값 중간 수식 12개 항목과 입력 변경 회귀 테스트 12개 케이스를 통과해 `exact_excel_match_regression_verified` 상태입니다.

치킨 입력 변경 회귀 테스트 통과 케이스:

- 기본 입력값
- 조사요일 수 -> 금
- 조사요일 수 -> 월
- 조사월 8 -> 3
- 19~20시 20대 남 통행량 22 -> 80
- 아파트 3,200 / 주택계 4,500
- 상주인구 863 -> 5,000
- 30평 이상 아파트 비율 상승
- 3억원 이상 아파트 가격대 비율 상승
- 후보점 배달 여부 1 -> 0
- 후보점 테이크아웃 여부 1 -> 0
- 후보점 면적 11평 -> 25평

## 상업용 Exact 전환 구조

업종별 입력 스키마를 `commercial_exact.py`에 분리했습니다.
현재 3개 업종은 아래 입력 구조를 단계별 UI에 반영합니다.

- 공통 기본 정보: 업종, 후보점명, 조사월, 요일, 지역, 행정단위, 운영형태
- 배후세대 입력: 아파트 세대수, 주택계, 주거인구, 직장인구, 소득
- 업종별 추가 입력: 아파트 평형별 세대수, 아파트 가격대별 세대수
- 통행량 입력: 시간대별 연령/성별 통행량
- 경쟁점 입력: 면적, 거리, 입지, 시계성, 접근성, 층, 면, 전면길이, 설비, 주차, 가격
- 피자/치킨 추가 경쟁점 입력: 홀판매여부, 배달 여부, 테이크아웃 여부
- 투자손익 입력: 보증금, 영업권, 임대료, 관리비, 로열티율, 영업일수, 원가율, 가입비, 교육비, 보증금, 개점홍보비

원본 엑셀 비교 검증용 개발 도구는 `excel_validation.py`에 있습니다.
LibreOffice가 설치된 검수 환경에서 원본 엑셀을 재계산하고 파이썬 결과와 비교하는 용도입니다.

상업용 공개 조건:

1. 업종별 입력 스키마가 원본 엑셀의 모든 사용자 입력칸을 포함해야 합니다.
2. 업종별 계산 모듈이 원본 엑셀의 `가중치 기준표`, `기초자료`, `SIMULATION`, `손익` 계산식을 모두 반영해야 합니다.
3. 기본값뿐 아니라 월/요일/세대수/통행량/경쟁점/임대료/원가율 변경 테스트를 통과해야 합니다.
4. 검증 통과 후에만 해당 업종의 `accuracy_status`를 `exact_excel_match`로 전환합니다.

Streamlit Cloud의 Secrets 전체 예시:

```toml
SUPABASE_URL = "https://프로젝트ID.supabase.co"
SUPABASE_KEY = "Supabase anon public key"
ADMIN_EMAILS = "admin@example.com,owner@example.com"
PORTONE_IMP_CODE = "imp00000000"
PORTONE_PG = "html5_inicis"
PORTONE_PAY_METHOD = "card"
PORTONE_PAYMENT_AMOUNT = 1000
PORTONE_PRODUCT_NAME = "상권 매출 예측 분석 리포트"
```

## Streamlit Cloud 배포 방법

1. GitHub에 새 저장소를 만듭니다.
2. 이 폴더 안의 파일을 저장소 루트에 업로드합니다.
3. Streamlit Cloud에서 `Create app`을 누릅니다.
4. 저장소, 브랜치, 앱 파일을 선택합니다.
5. 앱 파일 경로는 아래처럼 지정합니다.

```text
streamlit_app.py
```

배포가 끝나면 `https://...streamlit.app` 형태의 공유 링크가 생성됩니다.

## 파일 구성

- `streamlit_app.py`: 웹 화면
- `pure_model.py`: 엑셀 없이 동작하는 파이썬 계산 로직
- `supabase_backend.py`: Supabase Auth 및 분석 결과 저장/조회 모듈
- `industries/`: 업종별 독립 계산 모듈
- `mvp_industries.py`: 이전 코드와의 호환용 연결 파일
- `requirements.txt`: Streamlit Cloud 설치 패키지
- `.streamlit/config.toml`: 기본 화면 테마

## MVP 기준

피자는 현재 기본 결과값에 맞춰 보정계수를 적용한 MVP 계산기입니다.
치킨은 원본 엑셀의 주요 중간 수식을 `industries/chicken_exact.py`에 분해했습니다.
정식 버전에서는 각 업종이 입력값 변경 테스트까지 통과한 뒤 `exact_excel_match` 상태로 전환합니다.

## 로컬 테스트

```bash
python -m pip install -r requirements.txt
streamlit run streamlit_app.py
```
