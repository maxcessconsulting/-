# 상권 입지 평가 매출예측 SaaS MVP

엑셀 계산 모델을 업종별 파이썬 모듈로 변환해 실행하는 Streamlit 배포용 MVP 앱입니다.

## 1단계 구조: 다중 업종 확장

사이드바의 업종 선택 박스에서 최대 42개 업종을 선택할 수 있습니다.
현재 계산 엔진이 연결된 업종은 아래 3개이며, 나머지는 업종별 엑셀 파일 분석 후 순차적으로 활성화합니다.

- 음식점 / 해장국
- 피자
- 치킨

업종별 계산 코드는 `industries/` 폴더 아래에 분리되어 있습니다.

- `industries/haejang_calc.py`: 음식점 / 해장국 계산 모듈
- `industries/pizza_calc.py`: 피자 계산 모듈
- `industries/chicken_calc.py`: 치킨 계산 모듈
- `industries/registry.py`: 업종 목록, 준비 중 업종, 계산 모듈 연결

## 2단계 구조: Supabase 인증 및 데이터 저장

회원가입/로그인과 분석 결과 저장은 Supabase를 사용합니다.
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

관리자 계정은 `ADMIN_EMAILS`에 들어 있는 이메일로 회원가입/로그인하면 `Admin` 역할로 저장됩니다.

주의: 현재 결제 성공 처리는 포트원 결제창 콜백 신호를 Streamlit이 감지해 `profiles.payment_status`를 `paid`로 바꾸는 MVP 로직입니다.
상용 배포 전에는 포트원 REST API의 결제 단건조회/서버 검증 또는 웹훅 검증을 붙여서 결제금액과 주문번호를 반드시 서버에서 검증해야 합니다.

이전 MySQL/SQLite 설정은 더 이상 사용하지 않습니다.

## 3단계 구조: 회원가입, 로그인, Admin 권한

사이트에 접속하면 분석 화면보다 로그인/회원가입 화면이 먼저 표시됩니다.
회원 인증은 Supabase Auth가 처리하고, 서비스 권한/결제 상태는 `profiles` 테이블에 저장됩니다.

권한은 아래 두 가지입니다.

- `User`: 일반 회원. 본인이 저장한 분석 결과만 조회합니다.
- `Admin`: 관리자. 결제 여부와 관계없이 모든 회원의 분석 결과를 조회합니다.

상업용 배포에서는 Streamlit Secrets에 `ADMIN_EMAILS`를 등록해 관리자 이메일을 지정할 수 있습니다.

```toml
ADMIN_EMAILS = "admin@example.com,owner@example.com"
```

`ADMIN_EMAILS`에 포함된 이메일로 회원가입하면 자동으로 `Admin` 권한이 부여됩니다.

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

현재 피자와 치킨은 기본값 중심의 보정 MVP 상태입니다.
최종 공개 전에는 업종별 엑셀 파일을 다시 역추적해 `exact_excel_match` 검증을 통과한 모듈만 결과 공개 대상으로 전환해야 합니다.

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

피자와 치킨은 각 엑셀 파일의 기본 결과값에 맞춰 보정계수를 적용한 MVP 계산기입니다.
치킨 업종은 원본 엑셀의 월/요일 가중치를 별도로 반영했으며, 기본값과 요일 변경값은 원본 엑셀 재계산 결과와 일치하도록 검증했습니다.
정식 버전에서는 각 업종의 세부 기준표와 수식을 `pizza_calc.py`, `chicken_calc.py` 안에 완전 분해하고, 원본 엑셀과 비교 테스트를 통과한 뒤 `exact_excel_match` 상태로 전환합니다.

## 로컬 테스트

```bash
python -m pip install -r requirements.txt
streamlit run streamlit_app.py
```
