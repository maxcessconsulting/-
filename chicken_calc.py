from __future__ import annotations

from copy import deepcopy

from pure_model import Competitor, ModelInput, calculate as calculate_common


CODE = "chicken"
NAME = "치킨"
MVP_NOTE = (
    "푸라닭/치킨 업종 엑셀 기본값과 월/요일 변경값에 맞춰 보정한 MVP 계산기입니다. "
    "최종 MVP에서는 치킨 전용 가중치 기준표를 별도 계산식으로 완전 분리합니다."
)
STATUS = "ready"

MVP_MULTIPLIER = 1.4944542984430171

# The source chicken workbook uses a fixed month result cell that references B208
# for every month selection. This intentionally mirrors that workbook behavior.
MONTH_INDEX = {month: 1.0307808503678482 for month in range(1, 13)}
WEEKDAY_INDEX = {
    "월": 0.8274271143934917,
    "화": 0.8536958896721132,
    "수": 0.8601369002806009,
    "목": 0.8598199097866892,
    "금": 1.220752546139655,
    "토": 1.2967667212562837,
    "일": 1.081400918471166,
}


def empty_traffic() -> list[list[float]]:
    return [[0.0] * 12 for _ in range(11)]


def get_default_input() -> ModelInput:
    data = ModelInput(
        store_name="푸라닭 개금",
        survey_month=8,
        weekday="수",
        region="부산 경남",
        admin_unit="시 단위",
        apartment_households=2174,
        total_households=3005,
        resident_population=7224,
        worker_population=863,
        annual_income=5124,
        deposit=30000,
        goodwill=20000,
        monthly_rent=2500,
        management_fee=0,
        business_days=26,
        cogs_rate=0.45,
        royalty_rate=0.025,
        franchise_fee=5000,
        education_fee=5000,
        guarantee_deposit=3000,
    )
    data.traffic = empty_traffic()
    data.traffic[4] = [0, 0, 4, 8, 2, 4, 0, 6, 4, 6, 6, 14]
    data.traffic[5] = [6, 6, 4, 10, 4, 0, 2, 18, 2, 12, 10, 8]
    data.traffic[8] = [4, 10, 22, 14, 8, 2, 14, 10, 8, 8, 4, 4]
    data.traffic[9] = [10, 2, 18, 12, 4, 2, 6, 8, 8, 6, 12, 4]
    data.direct_competitors = [
        Competitor("푸라닭 개금", 11, 1, 2, 3, 1, 1, 1, 4, 3, 0, 3),
        Competitor("문진옥숯불바베큐", 10, 92, 2, 2, 3, 1, 1, 7, 3, 0, 1),
        Competitor("멕시카나치킨", 12, 144, 1, 3, 1, 1, 1, 6, 3, 0, 1),
        Competitor("썬더치킨", 32, 249, 1, 2, 3, 2, 2, 21, 3, 0, 1),
        Competitor("치킨상파전", 9, 266, 2, 2, 2, 1, 1, 7, 2, 0, 2),
        Competitor("착한 맛집", 5, 177, 1, 2, 2, 1, 1, 2.5, 3, 0, 1),
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

