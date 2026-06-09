from __future__ import annotations

from copy import deepcopy
from typing import Any

from pure_model import AGE_COLUMNS, Competitor, ModelInput


TIME_DISTRIBUTION = {
    1: [
        0.08161867266961999,
        0.07901860209859128,
        0.12533728495846969,
        0.15054304559676135,
        0.18125306322263102,
        0.1555796311365801,
        0.11882106142010118,
        0.10782863889724538,
    ],
    2: [
        0.09738130709807033,
        0.0891629327897316,
        0.10652686517742013,
        0.15303207851351164,
        0.1533820739035001,
        0.14259491579077288,
        0.12844337152370036,
        0.1294764552032929,
    ],
}

TRADE_AREA_THRESHOLD = 0.4079123229083133
TAKEOUT_PRICES = [0, 0, 15131.818181818182, 14562.5, 20500, 20122, 28500, 17400, 15425, 8616.666666666666, 0, 13900]
HALL_PRICES = [9633.333333333334, 0, 11438.333333333334, 12059.09090909091, 12352.412280701756, 14065.277777777777, 14024.404761904763, 13522.916666666668, 13747.916666666668, 9673.666666666668, 8337.5, 14725]
DELIVERY_PRICE = 22794.652406417114

DINING_RATE = 0.836
VISIT_DINING_RATE = 0.2927631578947369
TAKEOUT_DINING_RATE = 0.06578947368421052
DELIVERY_DINING_RATE = 0.308
CHICKEN_DELIVERY_RATE = 0.524

MONTH_INDEX_BY_TYPE = {
    1: 0.9932423214047369,
    2: 1.0307808503678482,
}
WEEKDAY_INDEX_BY_TYPE = {
    1: {
        "월": 0.7535644115869643,
        "화": 0.8930641880490744,
        "수": 0.875773300618315,
        "목": 0.9079196783635322,
        "금": 1.2518598800828797,
        "토": 1.2874087576575755,
        "일": 1.0304097836416586,
    },
    2: {
        "월": 0.8274271143934917,
        "화": 0.8536958896721132,
        "수": 0.8601369002806009,
        "목": 0.8598199097866892,
        "금": 1.220752546139655,
        "토": 1.2967667212562837,
        "일": 1.081400918471166,
    },
}


def exact_calculate(data: ModelInput) -> dict:
    extra_inputs = getattr(data, "extra_inputs", {}) or {}
    traffic = _normalized_chicken_traffic(data.traffic)
    observed_totals = [sum(row) for row in traffic]
    observed_total = sum(observed_totals)
    if observed_total <= 0:
        raise ValueError("통행량 합계가 0입니다.")

    demographic_totals = [sum(row[index] for row in traffic) for index in range(12)]
    demographic_shares = [value / observed_total for value in demographic_totals]
    trade_decision_ratio = demographic_shares[2] + demographic_shares[4] + demographic_shares[5] + demographic_shares[8]
    area_type = 1 if trade_decision_ratio >= TRADE_AREA_THRESHOLD else 2
    time_distribution = TIME_DISTRIBUTION[area_type]
    observed_time_share = sum(time_distribution[index] for index, total in enumerate(observed_totals) if total >= 1)
    daily_traffic = observed_total / observed_time_share
    daily_traffic_by_demo = [daily_traffic * share for share in demographic_shares]

    weights = _demand_weights(data, demographic_shares, extra_inputs)
    candidate_distance_basis = _candidate_distance_basis(data.direct_competitors, data.indirect_competitors)
    direct_scores = [
        _competitor_score(comp, index == 0, False, candidate_distance_basis)
        for index, comp in enumerate(data.direct_competitors)
    ]
    indirect_scores = [_competitor_score(comp, False, True, candidate_distance_basis) for comp in data.indirect_competitors]
    direct_services = _service_rows(extra_inputs.get("direct_competitor_rows", []), len(data.direct_competitors))
    indirect_services = _service_rows(extra_inputs.get("indirect_competitor_rows", []), len(data.indirect_competitors))

    takeout_total_score = _channel_total_score(direct_scores, indirect_scores, direct_services, indirect_services, "테이크아웃 여부", add_synthetic_second=True)
    delivery_total_score = _channel_total_score(direct_scores, indirect_scores, direct_services, indirect_services, "배달 여부", add_synthetic_second=True)
    hall_total_score = _channel_total_score(direct_scores, indirect_scores, direct_services, indirect_services, "홀판매여부", add_synthetic_second=False)
    if takeout_total_score <= 0 or delivery_total_score <= 0 or hall_total_score <= 0:
        raise ValueError("판매 방식별 경쟁점 총점이 0입니다.")

    takeout_potential, takeout_per_point = _takeout_potential(daily_traffic_by_demo, weights, takeout_total_score)
    delivery_potential, delivery_per_point = _delivery_potential(data, weights, delivery_total_score)
    hall_potential, hall_per_point = _hall_potential(daily_traffic_by_demo, weights, takeout_total_score, hall_total_score)

    candidate_score = direct_scores[0] if direct_scores else 0
    candidate_services = direct_services[0] if direct_services else _default_service_flags()
    candidate_takeout_sales = candidate_score * takeout_per_point if candidate_services["테이크아웃 여부"] else 0
    candidate_delivery_sales = candidate_score * delivery_per_point if candidate_services["배달 여부"] else 0
    candidate_hall_sales = candidate_score * hall_per_point if candidate_services["홀판매여부"] else 0

    pre_date_sales = candidate_takeout_sales + candidate_delivery_sales + candidate_hall_sales
    month_index = MONTH_INDEX_BY_TYPE[area_type]
    weekday_index = WEEKDAY_INDEX_BY_TYPE[area_type].get(data.weekday, 1.0)
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
        "trade_area_label": "큰점포 기준 상권" if area_type == 1 else "작은점포 기준 상권",
        "main_customer_ratio": trade_decision_ratio,
        "twenties_ratio": demographic_shares[2] + demographic_shares[3],
        "daily_traffic": daily_traffic,
        "candidate_score": candidate_score,
        "total_competition_score": takeout_total_score + delivery_total_score + hall_total_score,
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
            "takeout_total_score": takeout_total_score,
            "delivery_total_score": delivery_total_score,
            "hall_total_score": hall_total_score,
        },
        "channel_potentials": {
            "takeout": takeout_potential,
            "delivery": delivery_potential,
            "hall": hall_potential,
            "pre_date_sales": pre_date_sales,
        },
    }


def with_chicken_default_extras(data: ModelInput) -> ModelInput:
    copied = deepcopy(data)
    copied.extra_inputs = {
        "apartment_size_mix": [{"0~20평": 913, "20~29평": 874, "30~39평": 228, "40~49평": 38, "50평 이상": 0, "단독/다세대": 831}],
        "apartment_price_mix": [{"1억 미만": 629, "1억원대": 678, "2억원대": 746, "3억원대": 0, "4억원대": 0, "5억원대": 0, "6억원 이상": 0}],
        "direct_competitor_rows": [
            {"홀판매여부": 1, "배달 여부": 1, "테이크아웃 여부": 1},
            {"홀판매여부": 1, "배달 여부": 0, "테이크아웃 여부": 0},
            {"홀판매여부": 0, "배달 여부": 1, "테이크아웃 여부": 0},
            {"홀판매여부": 1, "배달 여부": 0, "테이크아웃 여부": 1},
            {"홀판매여부": 1, "배달 여부": 1, "테이크아웃 여부": 1},
            {"홀판매여부": 0, "배달 여부": 1, "테이크아웃 여부": 1},
        ],
        "indirect_competitor_rows": [],
    }
    return copied


def _normalized_chicken_traffic(traffic: list[list[float]]) -> list[list[float]]:
    return [[float(value or 0) for value in row[:12]] for row in traffic[4:12]]


def _demand_weights(data: ModelInput, demographic_shares: list[float], extra_inputs: dict[str, Any]) -> dict[str, float]:
    total_households = data.total_households
    apartment_ratio = data.apartment_households / total_households if total_households else 0
    apartment_size_ratio = _apartment_size_30_plus_ratio(data, extra_inputs)
    apartment_price_ratio = _apartment_price_3_plus_ratio(extra_inputs)
    trade_quality_ratio = demographic_shares[2] + demographic_shares[4] + demographic_shares[5] + demographic_shares[8]
    return {
        "household_weight": _lookup(total_households, [(0, 477.03259136236375, 0.9), (478.03259136236375, 2394.15, 0.95), (2395.15, 4311.267408637636, 1.0), (4312.267408637636, 6228.384817275273, 1.05), (6229.384817275273, 100000, 1.0)]),
        "apartment_weight": _lookup(apartment_ratio, [(0, 0.51823686685, 0.8), (0.52823686685, 0.9400307995378785, 0.85), (0.9500307995378785, 1, 0.9)]),
        "apartment_size_weight": _lookup(apartment_size_ratio, [(0, 0.15402221875, 0.9), (0.16402221875, 0.4047812994726653, 0.95), (0.4057812994726653, 1, 1.0)]),
        "apartment_price_weight": _lookup(apartment_price_ratio, [(0, 0.3371040834, 0.9), (0.3381040834, 0.7100054822848865, 0.925), (0.7100154822848864, 1, 0.95)]),
        "worker_weight": _lookup(data.worker_population, [(0, 4227, 0.9), (4228, 8383.89183537883, 1.0), (8384.89183537883, 20000, 1.1)]),
        "pedestrian_quality": _lookup(trade_quality_ratio, [(0, 0.30659447193382583, 0.75), (0.30759447193382583, 0.34523690487500003, 0.85), (0.34623690487500003, 0.3838793378161742, 0.95), (0.3848793378161742, 0.4225217707573484, 1.05), (0.4235217707573484, 1, 1.15)]),
    }


def _apartment_size_30_plus_ratio(data: ModelInput, extra_inputs: dict[str, Any]) -> float:
    row = _first_extra_row(extra_inputs, "apartment_size_mix")
    over_30 = _num(row.get("30~39평")) + _num(row.get("40~49평")) + _num(row.get("50평 이상"))
    total = sum(_num(row.get(key)) for key in ["0~20평", "20~29평", "30~39평", "40~49평", "50평 이상"])
    single_households = _num(row.get("단독/다세대"), max(data.total_households - data.apartment_households, 0))
    denominator = total + single_households
    return over_30 / denominator if denominator else 0


def _apartment_price_3_plus_ratio(extra_inputs: dict[str, Any]) -> float:
    row = _first_extra_row(extra_inputs, "apartment_price_mix")
    total = sum(_num(row.get(key)) for key in ["1억 미만", "1억원대", "2억원대", "3억원대", "4억원대", "5억원대", "6억원 이상"])
    over_3 = sum(_num(row.get(key)) for key in ["3억원대", "4억원대", "5억원대", "6억원 이상"])
    return over_3 / total if total else 0


def _takeout_potential(daily_traffic_by_demo: list[float], weights: dict[str, float], total_score: float) -> tuple[float, float]:
    total = 0.0
    for index, traffic in enumerate(daily_traffic_by_demo):
        value = traffic * TAKEOUT_PRICES[index] * DINING_RATE * TAKEOUT_DINING_RATE
        value *= weights["household_weight"] * weights["apartment_weight"] * weights["apartment_size_weight"]
        value *= weights["worker_weight"] * weights["pedestrian_quality"]
        total += value
    return total, total / total_score


def _delivery_potential(data: ModelInput, weights: dict[str, float], total_score: float) -> tuple[float, float]:
    total = data.total_households * DELIVERY_PRICE * DINING_RATE * DELIVERY_DINING_RATE * CHICKEN_DELIVERY_RATE
    total *= weights["household_weight"] * weights["apartment_weight"] * weights["apartment_size_weight"]
    total *= weights["apartment_price_weight"] * weights["worker_weight"]
    return total, total / total_score


def _hall_potential(daily_traffic_by_demo: list[float], weights: dict[str, float], takeout_score: float, hall_score: float) -> tuple[float, float]:
    total = 0.0
    per_point = 0.0
    for index, traffic in enumerate(daily_traffic_by_demo):
        value = traffic * HALL_PRICES[index] * DINING_RATE * VISIT_DINING_RATE
        value *= weights["household_weight"] * weights["apartment_weight"] * weights["apartment_size_weight"]
        value *= weights["apartment_price_weight"] * weights["worker_weight"] * weights["pedestrian_quality"]
        total += value
        denominator = hall_score if index == 11 else takeout_score
        per_point += value / denominator if denominator else 0
    return total, per_point


def _competitor_score(comp: Competitor, candidate: bool, indirect: bool, candidate_distance_basis: float) -> float:
    score = 0.0
    score += {1.0: 8, 2.0: 12, 3.0: 15}.get(float(comp.location or 0), 0)
    score += {1.0: 1, 2.0: 3, 3.0: 5}.get(float(comp.visibility or 0), 0)
    score += {1.0: 5, 2.0: 3, 3.0: 1}.get(float(comp.accessibility or 0), 0)
    score += _lookup(comp.area, [(0, 18.81112448979592, -2), (18.81122448979592, 29.182292556871268, 1), (30.182292556871268, 100, 5)], 0)
    score += {1.0: 0, 2.0: -3, 3.0: -5}.get(float(comp.floor or 0), 0)
    score += {1.0: 1, 2.0: 3, 3.0: 5}.get(float(comp.sides or 0), 0)
    score += _lookup(comp.frontage, [(0, 6.9, -1), (7, 11.9, 0), (12, 50, 1)], 0)
    score += {1.0: 0, 2.0: -1, 3.0: -1}.get(float(comp.facility or 0), 0)
    score += _lookup(comp.parking, [(0, 0, -2), (1, 3, 0), (4, 100, 2)], 0)
    score += {3.0: 0, 2.0: 0, 1.0: 2}.get(float(comp.price or 0), 0)
    if candidate:
        score += _lookup(candidate_distance_basis, [(0, 100, -3), (101, 200, -2), (200, 1000, -1)], 0)
    else:
        score += _lookup(comp.distance, [(0, 100, 1), (101, 200, 2), (200, 1000, 3)], 0)
    return score * (0.6 if indirect else 1.0)


def _candidate_distance_basis(direct_competitors: list[Competitor], indirect_competitors: list[Competitor]) -> float:
    distances = [float(comp.distance or 0) for comp in direct_competitors + indirect_competitors]
    return sum(distances) / len(distances) if distances else 0


def _channel_total_score(
    direct_scores: list[float],
    indirect_scores: list[float],
    direct_services: list[dict[str, int]],
    indirect_services: list[dict[str, int]],
    service_key: str,
    add_synthetic_second: bool,
) -> float:
    total = 0.0
    active_count = 0
    for score, services in zip(direct_scores, direct_services):
        if services.get(service_key, 0):
            total += score
            active_count += 1
    for score, services in zip(indirect_scores, indirect_services):
        if services.get(service_key, 0):
            total += score
            active_count += 1
    if add_synthetic_second and active_count >= 2 and len(direct_scores) > 1:
        total += direct_scores[1]
    return total


def _service_rows(rows: Any, fallback_count: int) -> list[dict[str, int]]:
    if hasattr(rows, "to_dict"):
        rows = rows.to_dict("records")
    records = [dict(row) for row in rows] if rows else []
    while len(records) < fallback_count:
        records.append(_default_service_flags())
    normalized = []
    for row in records[:fallback_count]:
        normalized.append(
            {
                "홀판매여부": int(_num(row.get("홀판매여부"), 1)),
                "배달 여부": int(_num(row.get("배달 여부"), 1)),
                "테이크아웃 여부": int(_num(row.get("테이크아웃 여부"), 1)),
            }
        )
    return normalized


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
