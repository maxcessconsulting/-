from __future__ import annotations

from pure_model import Competitor, ModelInput

try:
    from industries.chicken_excel_map import assert_default_parity, base_input_cell_map
    from industries.chicken_exact import exact_calculate, with_chicken_default_extras
except ModuleNotFoundError:
    from chicken_excel_map import assert_default_parity, base_input_cell_map
    from chicken_exact import exact_calculate, with_chicken_default_extras


CODE = "chicken"
NAME = "치킨"
MVP_NOTE = (
    "푸라닭/치킨 업종 원본 엑셀의 take-out, 배달, 내점 고객 잠재수요와 판매 방식별 경쟁점 배분 수식을 이식한 계산기입니다."
)
STATUS = "ready"
ACCURACY_STATUS = "exact_excel_match_regression_verified"


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
    return with_chicken_default_extras(data)


def calculate(data: ModelInput) -> dict:
    result = exact_calculate(data)
    result["industry_code"] = CODE
    result["industry_name"] = NAME
    result["mvp_note"] = MVP_NOTE
    result["accuracy_status"] = ACCURACY_STATUS
    result["excel_input_cells"] = base_input_cell_map()
    return result


def validate_default_excel_parity() -> None:
    assert_default_parity(calculate(get_default_input()))
