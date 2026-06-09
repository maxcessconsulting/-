from __future__ import annotations

from pure_model import Competitor, ModelInput

from .pizza_exact import exact_calculate, with_pizza_default_extras


CODE = "pizza"
NAME = "피자"
MVP_NOTE = (
    "피자마루 원본 엑셀의 업종 전용 시간대 구성비, 50대 이상 상권 유형, "
    "채널별 잠재수요, 경쟁점 점수, 최종 후보점 배분식을 파이썬으로 이식한 exact 계산기입니다."
)
STATUS = "ready"
ACCURACY_STATUS = "exact_excel_match_regression_verified"


def empty_traffic() -> list[list[float]]:
    return [[0.0] * 12 for _ in range(11)]


def get_default_input() -> ModelInput:
    data = ModelInput(
        store_name="피자마루",
        survey_month=7,
        weekday="월",
        region="서울 경기",
        admin_unit="시 단위",
        apartment_households=498,
        total_households=498,
        resident_population=1249,
        worker_population=910,
        annual_income=5124,
        deposit=30000,
        goodwill=20000,
        monthly_rent=2500,
        management_fee=0,
        business_days=26,
        cogs_rate=0.35,
        royalty_rate=0.025,
        franchise_fee=5000,
        education_fee=5000,
        guarantee_deposit=3000,
    )
    data.traffic = empty_traffic()
    data.traffic[1] = [18, 2, 0, 8, 2, 24, 8, 20, 4, 10, 4, 10]
    data.traffic[2] = [6, 42, 16, 22, 24, 12, 6, 28, 0, 46, 18, 22]
    data.traffic[7] = [4, 14, 4, 6, 0, 6, 10, 16, 4, 0, 6, 12]
    data.traffic[8] = [6, 6, 12, 8, 18, 20, 10, 30, 4, 4, 12, 8]
    data.direct_competitors = [
        Competitor("피자마루", 36, 1, 2, 2, 3, 1, 1, 5, 3, 0, 2),
        Competitor("미스터피자", 25, 158, 2, 2, 2, 2, 1, 7, 3, 0, 3),
    ]
    data.indirect_competitors = []
    return with_pizza_default_extras(data)


def calculate(data: ModelInput) -> dict:
    result = exact_calculate(data)
    result["industry_code"] = CODE
    result["industry_name"] = NAME
    result["mvp_note"] = MVP_NOTE
    return result
