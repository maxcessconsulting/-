from __future__ import annotations

from copy import deepcopy

from pure_model import Competitor, ModelInput, calculate as calculate_common


CODE = "pizza"
NAME = "피자"
MVP_NOTE = (
    "피자마루 엑셀 기본값에 맞춰 보정한 MVP 계산기입니다. "
    "최종 MVP에서는 피자 전용 가중치 기준표를 별도 계산식으로 완전 분리합니다."
)
STATUS = "ready"

MVP_MULTIPLIER = 0.669640964218573
MONTH_INDEX = {month: 1.0 for month in range(1, 13)}
WEEKDAY_INDEX = {day: 1.0 for day in ["월", "화", "수", "목", "금", "토", "일"]}


def empty_traffic() -> list[list[float]]:
    return [[0.0] * 12 for _ in range(11)]


def get_default_input() -> ModelInput:
    data = ModelInput(
        store_name="피자마루",
        survey_month=6,
        weekday="금",
        region="충청권",
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
    return data


def calculate(data: ModelInput) -> dict:
    result = calculate_common(data)
    month_index, weekday_index = get_indices(data)
    date_correction = result["month_index"] * result["weekday_index"] / month_index / weekday_index
    result = apply_sales_multiplier(result, MVP_MULTIPLIER * date_correction)
    result["month_index"] = month_index
    result["weekday_index"] = weekday_index
    result["industry_code"] = CODE
    result["industry_name"] = NAME
    result["mvp_note"] = MVP_NOTE
    result["mvp_multiplier"] = MVP_MULTIPLIER
    result["date_correction"] = date_correction
    return result


def get_indices(data: ModelInput) -> tuple[float, float]:
    month = max(1, min(12, int(data.survey_month)))
    return MONTH_INDEX[month], WEEKDAY_INDEX.get(data.weekday, 1.0)


def apply_sales_multiplier(result: dict, multiplier: float) -> dict:
    scaled = deepcopy(result)
    for key in [
        "traffic_potential_total",
        "household_potential_total",
        "worker_potential_total",
        "candidate_traffic_sales",
        "candidate_household_sales",
        "candidate_worker_sales",
        "daily_sales_thousand",
        "monthly_sales_thousand",
        "monthly_sales_ex_vat_thousand",
        "cogs_thousand",
        "royalty_thousand",
        "contribution_profit_thousand",
    ]:
        scaled[key] *= multiplier
    return scaled

