# 계산 엔진 표준화 및 서버 설계 패키지

43개 업종 확장을 위한 계산 엔진 표준 구조와 서버/DB 설계 초안입니다.

## 구성

```text
calculation_engine/
  schemas.py              공통 입력/출력 스키마
  base.py                 업종별 계산기 인터페이스
  common.py               공통 유틸
  registry.py             업종 계산기 등록
  industries/
    restaurant.py         음식점 계산기
    cafe.py               카페 계산기 골격
    retail.py             소매 계산기 골격
    beauty.py             뷰티/서비스 계산기 골격

backend_design/
  architecture.md         전체 아키텍처
  api_design.md           API 설계
  database_schema.md      DB 테이블 설계
  member_payment_flow.md  회원/결제/저장 흐름

api_server_example.py     FastAPI 계산 API 예시
example_usage.py          계산 엔진 직접 호출 예시
```

## 계산 엔진 테스트

```bash
python example_usage.py
```

기본 음식점 예시 기준으로 예상 일매출과 월매출이 출력됩니다.

## API 서버 예시 실행

```bash
python -m pip install -r requirements.txt
uvicorn api_server_example:app --reload
```

브라우저에서 API 문서를 확인합니다.

```text
http://localhost:8000/docs
```

## 다음 작업

1. 43개 업종 코드를 확정한다.
2. 각 업종의 엑셀 또는 기준표를 수집한다.
3. 업종별로 `calculation_engine/industries/{industry_code}.py`를 구현한다.
4. DB의 `industries`, `organization_industry_permissions`, `calculations` 테이블부터 만든다.
5. FastAPI 서버에 인증, 저장, 결제 webhook을 순서대로 붙인다.
