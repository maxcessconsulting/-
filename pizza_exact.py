from __future__ import annotations

from copy import deepcopy
from typing import Any

from pure_model import AGE_COLUMNS, Competitor, ModelInput


TIME_DISTRIBUTION = {
    1: [
        0.05859053631008827,
        0.08464808566578395,
        0.0765419610431217,
        0.06299096043220596,
        0.07750441920980211,
        0.07434289655161005,
        0.095596073973962,
        0.1174088109951279,
        0.1253577148257791,
        0.12592431518885433,
        0.10109422580366459,
    ],
    2: [
        0.06311363693469212,
        0.10030618089636392,
        0.08661114090808215,
        0.08250700871254381,
        0.08020235621520155,
        0.08756567856083528,
        0.10134097989065785,
        0.11445116430942726,
        0.11478637581376967,
        0.0993095162442159,
        0.06980596151421051,
    ],
}

TRADE_AREA_THRESHOLD = 0.32801
TAKEOUT_PRICES = {
    1: [
        12938.888888888889,
        12688.888888888889,
        0,
        12900,
        15210,
        14716.666666666666,
        12488.888888888889,
        10450,
        0,
        9500,
        0,
        26900,
    ],
    2: [
        16900,
        7700,
        14940.90909090909,
        14566.666666666666,
        18091.02564102564,
        17575.641025641027,
        14716.666666666666,
        16561.904761904763,
        16320,
        14748.611111111111,
        5450,
        11460,
    ],
}
HALL_PRICES = {
    1: [0, 0, 8591.666666666668, 0, 0, 0, 0, 0, 0, 7250, 0, 0],
    2: [0, 0, 25400, 0, 0, 14900, 0, 0, 0, 0, 0, 0],
}
DELIVERY_PRICE = {1: 20376, 2: 21832}

REGION_DINING_RATE = {
    "서울 경기": 0.851,
    "충청권": 0.823,
    "호남권": 0.738,
    "대구경북": 0.825,
    "부산 경남": 0.836,
    "강원권": 0.705,
}
VISIT_DINING_RATE = 0.2927631578947369
TAKEOUT_DINING_RATE = 0.06578947368421052
PIZZA_DELIVERY_RATE = 0.11
TAKEOUT_RATIO = 0.5839181286549707

MONTH_INDEX = {month: 1.0 for month in range(1, 13)}
WEEKDAY_INDEX = {day: 1.0 for day in ["월", "화", "수", "목", "금", "토", "일"]}
FINAL_ALLOCATION_DEMOGRAPHICS = [0, 1, 2, 3, 5, 6, 7, 8, 9, 10, 11]


def exact_calculate(data: ModelInput) -> dict:
    extra_inputs = getattr(data, "extra_inputs", {}) or {}
    traffic = _normalized_pizza_traffic(data.traffic)
    observed_totals = [sum(row) for row in traffic]
    observed_total = sum(observed_totals)
    if observed_total <= 0:
        raise ValueError("통행량 합계가 0입니다.")

    demographic_totals = [sum(row[index] for row in traffic) for index in range(12)]
    demographic_shares = [value / observed_total for value in demographic_totals]
    trade_decision_ratio = sum(demographic_shares[index] for index in [8, 9, 10, 11])
    area_type = 2 if trade_decision_ratio >= TRADE_AREA_THRESHOLD else 1
    time_distribution = TIME_DISTRIBUTION[area_type]
    observed_time_share = sum(time_distribution[index] for index, total in enumerate(observed_totals) if total >= 1)
    daily_traffic = observed_total / observed_time_share
    daily_traffic_by_demo = [daily_traffic * share for share in demographic_shares]

    weights = _demand_weights(data, demographic_shares, extra_inputs)
    direct_scores = [
        _competitor_score(comp, index == 0, _candidate_distance_basis(data.direct_competitors))
        for index, comp in enumerate(data.direct_competitors)
    ]
    candidate_score = direct_scores[0] if direct_scores else 0
    total_score = sum(direct_scores)
    if total_score <= 0:
        raise ValueError("경쟁점 총점이 0입니다.")

    takeout_by_demo, takeout_potential = _takeout_potential(daily_traffic_by_demo, weights, area_type, total_score)
    delivery_potential, delivery_per_point = _delivery_potential(data, weights, area_type, total_score)
    hall_by_demo, hall_potential = _hall_potential(daily_traffic_by_demo, weights, area_type, total_score)

    direct_services = _service_rows(extra_inputs.get("direct_competitor_rows", []), len(data.direct_competitors))
    candidate_services = direct_services[0] if direct_services else _default_service_flags()
    candidate_takeout_sales = (
        candidate_score * sum(takeout_by_demo[index] for index in FINAL_ALLOCATION_DEMOGRAPHICS)
        if candidate_services["테이크아웃 여부"]
        else 0
    )
    candidate_delivery_sales = (
        candidate_score * delivery_per_point / 12 * len(FINAL_ALLOCATION_DEMOGRAPHICS)
        if candidate_services["배달 여부"]
        else 0
    )
    candidate_hall_sales = (
        candidate_score * sum(hall_by_demo[index] for index in FINAL_ALLOCATION_DEMOGRAPHICS)
        if candidate_services["홀판매여부"]
        else 0
    )
    allocation_by_demo = [
        candidate_score
        * (
            (takeout_by_demo[index] if candidate_services["테이크아웃 여부"] else 0)
            + (delivery_per_point / 12 if candidate_services["배달 여부"] else 0)
            + (hall_by_demo[index] if candidate_services["홀판매여부"] else 0)
        )
        for index in range(12)
    ]

    pre_date_sales = candidate_takeout_sales + candidate_delivery_sales + candidate_hall_sales
    month_index = MONTH_INDEX[max(1, min(12, int(data.survey_month)))]
    weekday_index = WEEKDAY_INDEX.get(data.weekday, 1.0)
    daily_sales_thousand = pre_date_sales / month_index / weekday_index / 1000
    monthly_sales_thousand = daily_sales_thousand * data.business_days
    monthly_sales_ex_vat_thousand = daily_sales_thousand / 11 * 10 * data.business_days
    cogs_thousand = monthly_sales_ex_vat_thousand * data.cogs_rate
    royalty_thousand = monthly_sales_ex_vat_thousand * data.royalty_rate
    rent_and_fee_thousand = data.monthly_rent + data.management_fee
    contribution_profit_thousand = (
        monthly_sales_ex_vat_thousand
        - cogs_thousand
        - royalty_thousand
        - rent_and_fee_thousand
    )
    initial_investment_thousand = (
        data.deposit
        + data.goodwill
        + data.franchise_fee
        + data.education_fee
        + data.guarantee_deposit
        + data.opening_promo_fee
    )

    return {
        "store_name": data.store_name,
        "trade_area_type": area_type,
        "trade_area_label": "50대 이상 적은 상권" if area_type == 1 else "50대 이상 많은 상권",
        "main_customer_ratio": trade_decision_ratio,
        "twenties_ratio": demographic_shares[2] + demographic_shares[3],
        "daily_traffic": daily_traffic,
        "candidate_score": candidate_score,
        "total_competition_score": total_score,
        "traffic_potential_total": takeout_potential,
        "household_potential_total": delivery_potential,
        "worker_potential_total": hall_potential,
        "candidate_traffic_sales": candidate_takeout_sales,
        "candidate_household_sales": candidate_delivery_sales,
        "candidate_worker_sales": candidate_hall_sales,
        "daily_sales_thousand": daily_sales_thousand,
        "monthly_sales_thousand": monthly_sales_thousand,
        "monthly_sales_ex_vat_thousand": monthly_sales_ex_vat_thousand,
        "cogs_thousand": cogs_thousand,
        "royalty_thousand": royalty_thousand,
        "rent_and_fee_thousand": rent_and_fee_thousand,
        "contribution_profit_thousand": contribution_profit_thousand,
        "initial_investment_thousand": initial_investment_thousand,
        "month_index": month_index,
        "weekday_index": weekday_index,
        "weights": weights,
        "channel_scores": {
            "total_score": total_score,
            "candidate_score": candidate_score,
        },
        "channel_potentials": {
            "takeout": takeout_potential,
            "delivery": delivery_potential,
            "hall": hall_potential,
            "pre_date_sales": pre_date_sales,
            "takeout_per_demo": takeout_by_demo,
            "delivery_per_point": delivery_per_point,
            "hall_per_demo": hall_by_demo,
            "allocation_by_demo": allocation_by_demo,
        },
    }


def with_pizza_default_extras(data: ModelInput) -> ModelInput:
    copied = deepcopy(data)
    copied.extra_inputs = {
        "apartment_size_mix": [{"0~20평": 0, "20~29평": 0, "30~39평": 128, "40~49평": 370, "50평 이상": 0, "단독/다세대": 0}],
        "apartment_price_mix": [{"1억 미만": 0, "1억원대": 0, "2억원대": 0, "3억원대": 6, "4억원대": 180, "5억원대": 189, "6억원 이상": 123}],
        "direct_competitor_rows": [
            {"홀판매여부": 1, "배달 여부": 1, "테이크아웃 여부": 1},
            {"홀판매여부": 1, "배달 여부": 1, "테이크아웃 여부": 1},
        ],
        "indirect_competitor_rows": [],
    }
    return copied


def _normalized_pizza_traffic(traffic: list[list[float]]) -> list[list[float]]:
    return [[float(value or 0) for value in row[:12]] for row in traffic[:11]]


def _demand_weights(data: ModelInput, demographic_shares: list[float], extra_inputs: dict[str, Any]) -> dict[str, float]:
    total_households = data.total_households
    apartment_ratio = data.apartment_households / total_households if total_households else 0
    return {
        "region_rate": REGION_DINING_RATE.get(data.region, REGION_DINING_RATE["서울 경기"]),
        "household_weight": _lookup(total_households, [(0, 2065.287711972069, 0.8), (2066.287711972069, 5450, 0.9), (5451, 8834.712288027931, 1), (8835.712288027931, 12219.424576055862, 1.1), (12220.424576055862, 100000, 1.2)]),
        "apartment_weight": _lookup(apartment_ratio, [(0, 0.2934373580939635, 0.9), (0.2935373580939635, 0.6874886856060366, 1), (0.6875886856060366, 1, 1.1)]),
        "apartment_size_weight": _lookup(_apartment_size_30_plus_ratio(data, extra_inputs), [(0, 0.18476420999999998, 0.9), (0.19476421, 0.3838525281621333, 1), (0.3938525281621333, 1, 1.1)]),
        "apartment_price_weight": _lookup(_apartment_price_3_plus_ratio(extra_inputs), [(0, 0.461, 0.9), (0.4611, 1, 1)]),
        "worker_weight": _lookup(data.worker_population, [(0, 2685.8, 0.9), (2686.8, 4560.87387935032, 1), (4561.87387935032, 50000, 1.1)]),
        "pedestrian_quality": _lookup(sum(demographic_shares[index] for index in [2, 3, 4, 5, 6, 7]), [(0, 0.5377867024285978, 0.8), (0.5387867024285978, 0.6443056089, 0.9), (0.6453056089, 0.7508245153714022, 1), (0.7518245153714022, 0.8573434218428043, 1.1), (0.8583434218428043, 1, 1.2)]),
    }


def _apartment_size_30_plus_ratio(data: ModelInput, extra_inputs: dict[str, Any]) -> float:
    row = _first_extra_row(extra_inputs, "apartment_size_mix")
    over_30 = _num(row.get("30~39평")) + _num(row.get("40~49평")) + _num(row.get("50평 이상"))
    total = sum(_num(row.get(key)) for key in ["0~20평", "20~29평", "30~39평", "40~49평", "50평 이상"])
    single_households = max(data.total_households - data.apartment_households, 0)
    denominator = total + single_households
    return over_30 / denominator if denominator else 0


def _apartment_price_3_plus_ratio(extra_inputs: dict[str, Any]) -> float:
    row = _first_extra_row(extra_inputs, "apartment_price_mix")
    total = sum(_num(row.get(key)) for key in ["1억 미만", "1억원대", "2억원대", "3억원대", "4억원대", "5억원대", "6억원 이상"])
    over_3 = sum(_num(row.get(key)) for key in ["3억원대", "4억원대", "5억원대", "6억원 이상"])
    return over_3 / total if total else 0


def _takeout_potential(daily_traffic_by_demo: list[float], weights: dict[str, float], area_type: int, total_score: float) -> tuple[list[float], float]:
    by_demo = []
    total = 0.0
    for index, traffic in enumerate(daily_traffic_by_demo):
        value = traffic * TAKEOUT_PRICES[area_type][index] * weights["region_rate"] * TAKEOUT_DINING_RATE
        value *= weights["household_weight"] * weights["apartment_weight"] * weights["apartment_size_weight"]
        value *= weights["worker_weight"] * weights["pedestrian_quality"] * TAKEOUT_RATIO
        total += value
        by_demo.append(value / total_score)
    return by_demo, total


def _delivery_potential(data: ModelInput, weights: dict[str, float], area_type: int, total_score: float) -> tuple[float, float]:
    total = data.total_households * DELIVERY_PRICE[area_type] * weights["region_rate"] * PIZZA_DELIVERY_RATE
    total *= weights["household_weight"] * weights["apartment_weight"] * weights["apartment_size_weight"]
    total *= weights["apartment_price_weight"] * weights["worker_weight"]
    return total, total / total_score


def _hall_potential(daily_traffic_by_demo: list[float], weights: dict[str, float], area_type: int, total_score: float) -> tuple[list[float], float]:
    by_demo = []
    total = 0.0
    for index, traffic in enumerate(daily_traffic_by_demo):
        value = traffic * HALL_PRICES[area_type][index] * weights["region_rate"] * VISIT_DINING_RATE
        value *= weights["household_weight"] * weights["apartment_weight"] * weights["apartment_size_weight"]
        value *= weights["apartment_price_weight"] * weights["worker_weight"] * weights["pedestrian_quality"]
        total += value
        by_demo.append(value / total_score)
    return by_demo, total


def _competitor_score(comp: Competitor, candidate: bool, candidate_distance_basis: float) -> float:
    score = 0.0
    score += {1.0: 8, 2.0: 12, 3.0: 15}.get(float(comp.location or 0), 0)
    score += {1.0: 1, 2.0: 3, 3.0: 5}.get(float(comp.visibility or 0), 0)
    score += {1.0: 1, 2.0: 3, 3.0: 5}.get(float(comp.accessibility or 0), 0)
    score += _lookup(comp.area, [(0, 9.848239016741235, -1), (9.849239016741235, 11.817910920231297, 0), (11.818910920231296, 100, 1)], 0)
    score += {1.0: 0, 2.0: -1, 3.0: -3}.get(float(comp.floor or 0), 0)
    score += {1.0: 1, 2.0: 3, 3.0: 5}.get(float(comp.sides or 0), 0)
    score += _lookup(comp.frontage, [(0, 6.9, -1), (7, 11.9, 0)], 0)
    score += {1.0: 0, 2.0: -1, 3.0: -1}.get(float(comp.facility or 0), 0)
    score += _lookup(comp.parking, [(0, 0, -2), (1, 3, 0), (4, 100, 2)], 0)
    score += {3.0: -2, 2.0: 0, 1.0: 2}.get(float(comp.price or 0), 0)
    if candidate:
        score += _lookup(candidate_distance_basis, [(0, 100, -3), (101, 200, -2), (200, 1000, -1)], 0)
    else:
        score += _lookup(comp.distance, [(0, 100, 1), (101, 200, 2), (200, 1000, 3)], 0)
    return score


def _candidate_distance_basis(direct_competitors: list[Competitor]) -> float:
    distances = [float(comp.distance or 0) for comp in direct_competitors if float(comp.distance or 0) > 0]
    return sum(distances) / len(distances) if distances else 0


def _service_rows(rows: Any, fallback_count: int) -> list[dict[str, int]]:
    if hasattr(rows, "to_dict"):
        rows = rows.to_dict("records")
    records = [dict(row) for row in rows] if rows else []
    while len(records) < fallback_count:
        records.append(_default_service_flags())
    return [
        {
            "홀판매여부": int(_num(row.get("홀판매여부"), 1)),
            "배달 여부": int(_num(row.get("배달 여부"), 1)),
            "테이크아웃 여부": int(_num(row.get("테이크아웃 여부"), 1)),
        }
        for row in records[:fallback_count]
    ]


def _default_service_flags() -> dict[str, int]:
    return {"홀판매여부": 1, "배달 여부": 1, "테이크아웃 여부": 1}


def _first_extra_row(extra_inputs: dict[str, Any], key: str) -> dict[str, Any]:
    rows = extra_inputs.get(key, [])
    if hasattr(rows, "to_dict"):
        rows = rows.to_dict("records")
    return dict(rows[0]) if rows else {}


def _lookup(value: float, rules: list[tuple[float, float, float]], default: float = 0.0) -> float:
    value = float(value or 0)
    for lower, upper, result in rules:
        if lower <= value <= upper:
            return result
    return default


def _num(value: Any, default: float = 0.0) -> float:
    if value is None or value == "":
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default
