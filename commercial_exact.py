from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EditorSpec:
    key: str
    title: str
    columns: list[str]
    help_text: str = ""


@dataclass(frozen=True)
class IndustryInputSchema:
    industry_code: str
    market_editors: list[EditorSpec]
    competitor_extra_columns: list[str]
    exact_status: str
    exact_note: str


APARTMENT_SIZE_COLUMNS = ["0~20평", "20~29평", "30~39평", "40~49평", "50평 이상"]
APARTMENT_PRICE_COLUMNS = ["1억 미만", "1억원대", "2억원대", "3억원대", "4억원대", "5억원대", "6억원 이상"]
SERVICE_COLUMNS = ["홀판매여부", "배달 여부", "테이크아웃 여부"]


SCHEMAS = {
    "haejang": IndustryInputSchema(
        industry_code="haejang",
        market_editors=[
            EditorSpec(
                key="apartment_size_mix",
                title="배후세대 아파트 평형별 세대수",
                columns=APARTMENT_SIZE_COLUMNS,
                help_text="원본 엑셀의 배후세대 아파트 평형별 입력칸입니다.",
            ),
            EditorSpec(
                key="apartment_price_mix",
                title="배후세대 아파트 가격대별 세대수",
                columns=APARTMENT_PRICE_COLUMNS,
                help_text="원본 엑셀의 아파트 가격대별 입력칸입니다.",
            ),
        ],
        competitor_extra_columns=[],
        exact_status="default_excel_match_input_mapped",
        exact_note=(
            "해장국은 원본 엑셀 기본값의 최종 일매출과 핵심 중간값 검증을 통과했고, "
            "웹 입력값과 원본 엑셀 입력 셀 매핑을 코드로 고정했습니다. "
            "상업용 최종 공개 전에는 입력값 변경 시나리오별 재계산 검증을 추가로 통과해야 합니다."
        ),
    ),
    "pizza": IndustryInputSchema(
        industry_code="pizza",
        market_editors=[
            EditorSpec(
                key="apartment_size_mix",
                title="배후세대 아파트 평형별 세대수",
                columns=APARTMENT_SIZE_COLUMNS,
                help_text="피자 원본 엑셀의 30평 이상, 대형 평형 반영 기준에 사용됩니다.",
            ),
            EditorSpec(
                key="apartment_price_mix",
                title="배후세대 아파트 가격대별 세대수",
                columns=APARTMENT_PRICE_COLUMNS,
                help_text="피자 원본 엑셀의 3억 이상 아파트 비율 기준에 사용됩니다.",
            ),
        ],
        competitor_extra_columns=SERVICE_COLUMNS,
        exact_status="exact_excel_match_regression_verified",
        exact_note=(
            "피자는 원본 엑셀의 50대 이상 상권 유형, 업종 전용 시간대 구성비, "
            "평형/가격/상주인구/통행인 가중치, take-out/배달/내점 고객 잠재수요, "
            "경쟁점 점수와 후보점 배분식을 파이썬으로 이식했습니다. "
            "기본값 중간 수식과 입력값 변경 회귀 테스트를 원본 엑셀 재계산값과 비교해 검증합니다."
        ),
    ),
    "chicken": IndustryInputSchema(
        industry_code="chicken",
        market_editors=[
            EditorSpec(
                key="apartment_size_mix",
                title="배후세대 아파트 평형별 세대수",
                columns=APARTMENT_SIZE_COLUMNS,
                help_text="치킨 원본 엑셀의 업종 전용 평형 비율 기준에 사용됩니다.",
            ),
            EditorSpec(
                key="apartment_price_mix",
                title="배후세대 아파트 가격대별 세대수",
                columns=APARTMENT_PRICE_COLUMNS,
                help_text="치킨 원본 엑셀의 업종 전용 가격대 비율 기준에 사용됩니다.",
            ),
        ],
        competitor_extra_columns=SERVICE_COLUMNS,
        exact_status="exact_excel_match_regression_verified",
        exact_note=(
            "치킨은 원본 엑셀의 take-out, 배달, 내점 고객 잠재수요와 판매 방식별 경쟁점 배분 수식을 파이썬으로 이식했습니다. "
            "기본값 중간 수식 12개 항목과 입력값 변경 회귀 테스트 12개 케이스를 원본 엑셀 재계산값과 비교해 통과했습니다."
        ),
    ),
}


def get_input_schema(industry_code: str) -> IndustryInputSchema:
    return SCHEMAS.get(
        industry_code,
        IndustryInputSchema(
            industry_code=industry_code,
            market_editors=[],
            competitor_extra_columns=[],
            exact_status="not_started",
            exact_note="아직 원본 엑셀 입력 구조가 분석되지 않은 업종입니다.",
        ),
    )


def empty_editor_row(columns: list[str]) -> dict:
    return {column: None for column in columns}


def rows_to_plain_records(rows) -> list[dict]:
    if hasattr(rows, "to_dict"):
        rows = rows.to_dict("records")
    return [dict(row) for row in rows]
