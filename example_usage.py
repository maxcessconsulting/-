from __future__ import annotations

from calculation_engine import (
    CalculationInput,
    CommonMarketInput,
    CompetitorInput,
    InvestmentInput,
    get_calculator,
)


DEFAULT_TRAFFIC = [
    [2, 4, 22, 90, 36, 96, 16, 34, 20, 64, 22, 122],
    [0, 0, 74, 112, 72, 94, 24, 54, 36, 78, 44, 158],
    [0, 6, 72, 164, 66, 74, 18, 36, 28, 68, 68, 104],
    [2, 0, 54, 156, 34, 62, 18, 48, 38, 64, 68, 118],
    [22, 0, 98, 194, 24, 56, 16, 48, 32, 70, 54, 150],
    [30, 30, 100, 242, 36, 62, 22, 30, 30, 52, 70, 106],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
]


def build_sample_input() -> CalculationInput:
    direct = [
        CompetitorInput("천안신부점", 80, 1, 1, 3, 3, 2, 1, 15, 1, 0, 2),
        CompetitorInput("두래해장국", 30, 100, 2, 2, 1, 1, 1, 7, 3, 0, 2),
        CompetitorInput("노걸대 터미널점1", 40, 100, 3, 3, 1, 1, 2, 10, 3, 1, 2),
        CompetitorInput("노걸대 터미널점2.", 20, 100, 2, 1, 1, 1, 1, 7, 3, 0, 2),
    ]
    indirect = [
        CompetitorInput("병천순대", 30, 200, 2, 1, 1, 1, 1, 7, 3, 1, 2),
        CompetitorInput("옛날 아우내순대보쌈", 10, 158, 1, 1, 1, 1, 1, 3, 3, 0, 2),
        CompetitorInput("큰할매순댓국", 30, 100, 2, 3, 1, 1, 1, 7, 3, 3, 2),
    ]
    return CalculationInput(
        industry_code="restaurant",
        market=CommonMarketInput(
            store_name="천안신부점",
            region="충청권",
            admin_unit="시 단위",
            survey_month=6,
            weekday="금",
            apartment_households=918,
            total_households=1834,
            resident_population=3578,
            worker_population=3326,
            annual_income=5124,
            traffic=DEFAULT_TRAFFIC,
            direct_competitors=direct,
            indirect_competitors=indirect,
        ),
        investment=InvestmentInput(
            operation_type="가맹점",
            deposit=50000,
            monthly_rent=5000,
            management_fee=500,
            royalty_rate=0.025,
            business_days=30,
            cogs_rate=0.45,
            franchise_fee=5000,
            education_fee=5000,
            guarantee_deposit=3000,
        ),
    )


if __name__ == "__main__":
    payload = build_sample_input()
    result = get_calculator(payload.industry_code).calculate(payload)
    print(result.sales.daily_sales_thousand)
    print(result.sales.monthly_sales_thousand)
    print(result.profit.estimated_payback_months)
