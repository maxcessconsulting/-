from __future__ import annotations

from dataclasses import dataclass, field


AGE_COLUMNS = [
    "10대 남", "10대 여", "20대 남", "20대 여", "30대 남", "30대 여",
    "40대 남", "40대 여", "50대 남", "50대 여", "60대이상 남", "60대이상 여",
]

TIME_LABELS = ["11~12", "12~13", "13~14", "14~15", "15~16", "16~17", "17~18", "18~19", "19~20", "20~21", "21~22"]

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

TIME_DISTRIBUTION = {
    1: [0.08964955175224124, 0.12306438467807661, 0.06927465362673187, 0.06845965770171149, 0.06519967400162999, 0.07416462917685411, 0.08394458027709861, 0.12550937245313773, 0.10839445802770986, 0.08883455582722087, 0.10350448247758762],
    2: [0.06361323155216285, 0.1005089058524173, 0.039440203562340966, 0.05343511450381679, 0.058524173027989825, 0.10687022900763359, 0.09796437659033079, 0.1450381679389313, 0.12468193384223919, 0.1183206106870229, 0.0916030534351145],
    3: [0.05859375, 0.09895833333333333, 0.06770833333333333, 0.0703125, 0.09244791666666667, 0.06640625, 0.08333333333333333, 0.14453125, 0.09635416666666667, 0.140625, 0.08072916666666667],
}

LUNCH_PRICES = [0, 9000, 10666.66667, 9000, 10011.11111, 9000, 11166.66667, 11000, 9880, 10500, 10233.33333, 9000]
DINNER_PRICES = [0, 0, 9500, 7000, 10000, 0, 9333.333333, 0, 9500, 9666.666667, 15333.33333, 9166.666667]

REGION_DINING_RATE = {
    "서울 경기": 0.818,
    "충청권": 0.716,
    "호남권": 0.757,
    "대구경북": 0.746,
    "부산 경남": 0.815,
    "강원권": 0.822,
}

MONTH_INDEX = {
    1: [0.9903780347797327, 0.9817892254468221, 0.9896835508964487, 1.0344297556433877, 0.9312327219515674, 0.9174783138575914, 0.9710148104672685, 0.9919406132726949, 1.1075507885623352, 1.0631227241751162, 1.026340322833412, 1.0278556102814433],
    2: [0.9548615434373651, 1.0297205959711278, 1.0458404371862695, 1.0310810412456035, 0.9119134815641755, 0.9127426812559454, 0.9686172939997548, 1.0356197202399402, 1.0125899777623424, 0.9819427571545236, 1.0307086633515912, 1.090079361282323],
    3: [0.946492734591396, 0.880802737834574, 0.8707110768960913, 0.9626884397626171, 0.9579608333604955, 0.9309350607587289, 0.9088612346103817, 1.0293050860044404, 1.216626970672568, 1.1826183910062138, 1.1059367660959472, 0.988417568031194],
}

WEEKDAY_INDEX = {
    1: {"월": 0.8126838287177175, "화": 0.7747307446114948, "수": 0.8913096427385457, "목": 0.9048834803382326, "금": 0.9355191317761604, "토": 1.2809556148925785, "일": 1.3999175569252706},
    2: {"월": 0.9007786379820555, "화": 0.9281089146671789, "수": 0.9191449736510243, "목": 0.9815677802925066, "금": 0.9820955485588563, "토": 1.1800313830729987, "일": 1.10827276177538},
    3: {"월": 0.5408748957826303, "화": 0.8661993551776153, "수": 0.8586258247027696, "목": 0.8625896992274661, "금": 0.9858577631699429, "토": 1.3958741969840818, "일": 1.4899782649554938},
}

HOUSEHOLD_WEIGHT_RULES = [(0.0, 439.7703603, 0.85), (440.7703603, 2861.904762, 0.9), (2862.904762, 5284.039163, 0.95), (5285.039163, 7706.173565, 1.0), (7707.173565, 100000.0, 1.05)]
APARTMENT_WEIGHT_RULES = [(0.0, 0.04679643021, 0.9), (0.04689643021, 0.3186534803, 0.95), (0.3196534803, 0.5914105305, 1.0), (0.5924105305, 0.8641675806, 1.05), (0.8651675806, 1.0, 1.1)]
INCOME_WEIGHT_RULES = [(1, 748.029, 0.9), (749.029, 1608.985, 0.925), (1609.985, 2433.672, 0.95), (2434.672, 3140.517, 0.975), (3141.517, 3836.174, 1.0), (3837.174, 100000.0, 1.05)]
PEDESTRIAN_QUALITY_RULES = [(0.0, 0.3851781658, 0.8), (0.3851791658, 0.425296226, 0.9), (0.426296226, 0.4664132862, 1.0), (0.4654132862, 0.5055303464, 1.1), (0.5065303464, 1.0, 1.2)]
TWENTIES_ADJUST_RULES = [(0.2473022465, 1.0, 0.2), (0.1788653188, 0.2472022465, 0.4), (0.1104283911, 0.1787653188, 0.6)]

GUKBAP_PREFERENCE = 0.317
AVG_DINING_PRICE = 10447.85153
FAMILY_DINING_PRICE = 25074.84367
MAIN_CUSTOMER_THRESHOLD = 0.353
WORKER_VISIT_RATE = 0.07
DEFAULT_STORE_COUNT = 152


@dataclass
class Competitor:
    name: str
    area: float
    distance: float
    location: float
    visibility: float
    accessibility: float
    floor: float
    sides: float
    frontage: float
    facility: float
    parking: float
    price: float


@dataclass
class ModelInput:
    store_name: str = "천안신부점"
    survey_month: int = 6
    weekday: str = "금"
    region: str = "충청권"
    admin_unit: str = "시 단위"
    apartment_households: float = 918
    total_households: float = 1834
    resident_population: float = 3578
    worker_population: float = 3326
    annual_income: float = 5124
    operation_type: str = "가맹점"
    deposit: float = 50000
    goodwill: float = 0
    monthly_rent: float = 5000
    management_fee: float = 500
    royalty_rate: float = 0.025
    business_days: float = 30
    cogs_rate: float = 0.45
    franchise_fee: float = 5000
    education_fee: float = 5000
    guarantee_deposit: float = 3000
    opening_promo_fee: float = 0
    traffic: list[list[float]] = field(default_factory=lambda: [row[:] for row in DEFAULT_TRAFFIC])
    direct_competitors: list[Competitor] = field(default_factory=list)
    indirect_competitors: list[Competitor] = field(default_factory=list)


def default_input() -> ModelInput:
    data = ModelInput()
    data.direct_competitors = [
        Competitor("천안신부점", 80, 1, 1, 3, 3, 2, 1, 15, 1, 0, 2),
        Competitor("두래해장국", 30, 100, 2, 2, 1, 1, 1, 7, 3, 0, 2),
        Competitor("노걸대 터미널점1", 40, 100, 3, 3, 1, 1, 2, 10, 3, 1, 2),
        Competitor("노걸대 터미널점2.", 20, 100, 2, 1, 1, 1, 1, 7, 3, 0, 2),
    ]
    data.indirect_competitors = [
        Competitor("병천순대", 30, 200, 2, 1, 1, 1, 1, 7, 3, 1, 2),
        Competitor("옛날 아우내순대보쌈", 10, 158, 1, 1, 1, 1, 1, 3, 3, 0, 2),
        Competitor("큰할매순댓국", 30, 100, 2, 3, 1, 1, 1, 7, 3, 3, 2),
    ]
    return data


def lookup(value: float, rules: list[tuple[float, float, float]], default: float = 1.0) -> float:
    for lower, upper, score in rules:
        if lower <= value <= upper:
            return score
    return default


def by_code(value: float, mapping: dict[float, float], default: float = 0.0) -> float:
    return mapping.get(float(value), default)


def competitor_score(c: Competitor, indirect: bool = False, candidate: bool = False) -> float:
    location = by_code(c.location, {1.0: 10, 2.0: 20, 3.0: 30})
    visibility = by_code(c.visibility, {1.0: 1, 2.0: 3, 3.0: 5})
    access = by_code(c.accessibility, {1.0: 5, 2.0: 3, 3.0: 1})
    area = lookup(c.area, [(0, 32.61962885, -3), (32.62062885, 44.52280952, -2), (44.52380952, 58.11827619, 1), (58.11727619, 71.71174285, 2), (71.71274285, 1000, 3)], 0)
    floor = by_code(c.floor, {1.0: 2, 2.0: 1, 3.0: -2})
    sides = by_code(c.sides, {1.0: 1, 2.0: 3, 3.0: 5})
    frontage = lookup(c.frontage, [(0, 6, 1), (6.1, 12, 2), (13, 100, 3)], 0)
    facility = by_code(c.facility, {1.0: 1, 2.0: -2, 3.0: -3})
    parking = lookup(c.parking, [(0, 0, -3), (1, 3, 0), (4, 1000, 3)], 0)
    price = by_code(c.price, {3.0: -2, 2.0: 0, 1.0: 2})
    if candidate:
        distance = lookup(c.distance, [(0, 100, -3), (101, 200, -2), (200, 1000, -1)], 0)
    else:
        distance = lookup(c.distance, [(0, 100, 1), (101, 200, 2), (200, 1000, 3)], 0)
    raw = location + visibility + access + area + floor + sides + frontage + facility + parking + price + distance
    return raw * (0.6 if indirect else 1.0)


def trade_area_type(main_customer_ratio: float, admin_unit: str) -> int:
    if admin_unit == "군 단위":
        return 3
    return 2 if main_customer_ratio <= MAIN_CUSTOMER_THRESHOLD else 1


def trade_area_label(area_type: int) -> str:
    return {1: "주고객비율 많은 상권", 2: "주고객비율 적은 상권", 3: "군단위 이하 상권"}[area_type]


def calculate(data: ModelInput) -> dict:
    row_totals = [sum(row) for row in data.traffic]
    observed_total = sum(row_totals)
    if observed_total <= 0:
        raise ValueError("통행량 합계가 0입니다.")

    demographic_totals = [sum(row[i] for row in data.traffic) for i in range(12)]
    demographic_shares = [v / observed_total for v in demographic_totals]
    main_ratio = demographic_shares[4] + demographic_shares[6] + demographic_shares[8] + demographic_shares[10]
    twenties_ratio = demographic_shares[2] + demographic_shares[3]
    area_type = trade_area_type(main_ratio, data.admin_unit)

    time_dist = TIME_DISTRIBUTION[area_type]
    observed_time_share = sum(time_dist[i] for i, total in enumerate(row_totals) if total > 0)
    daily_traffic = observed_total / observed_time_share

    reconstructed = [
        [daily_traffic * time_dist[row_idx] * demographic_shares[col_idx] for col_idx in range(12)]
        for row_idx in range(11)
    ]
    lunch_traffic = [sum(reconstructed[row][col] for row in range(5)) for col in range(12)]
    dinner_traffic = [sum(reconstructed[row][col] for row in range(5, 11)) for col in range(12)]

    twenties_adjust = lookup(twenties_ratio, TWENTIES_ADJUST_RULES, 1.0)
    for idx in (2, 3):
        lunch_traffic[idx] *= twenties_adjust
        dinner_traffic[idx] *= twenties_adjust

    region_rate = REGION_DINING_RATE[data.region]
    household_weight = lookup(data.total_households, HOUSEHOLD_WEIGHT_RULES)
    apartment_ratio = data.apartment_households / data.total_households if data.total_households else 0
    apartment_weight = lookup(apartment_ratio, APARTMENT_WEIGHT_RULES)
    income_weight = lookup(data.annual_income, INCOME_WEIGHT_RULES)
    pedestrian_quality = lookup(main_ratio, PEDESTRIAN_QUALITY_RULES)

    traffic_potential_by_demo = []
    for idx in range(12):
        base_sales = LUNCH_PRICES[idx] * lunch_traffic[idx] + DINNER_PRICES[idx] * dinner_traffic[idx]
        adjusted = base_sales * region_rate * GUKBAP_PREFERENCE * household_weight * apartment_weight * income_weight * pedestrian_quality
        traffic_potential_by_demo.append(adjusted)
    traffic_potential_total = sum(traffic_potential_by_demo)

    direct_scores = [competitor_score(c, False, idx == 0) for idx, c in enumerate(data.direct_competitors)]
    indirect_scores = [competitor_score(c, True) for c in data.indirect_competitors]
    candidate_score = direct_scores[0] if direct_scores else 0
    total_score = sum(direct_scores) + sum(indirect_scores)
    if total_score <= 0:
        raise ValueError("경쟁점 총점이 0입니다.")

    household_base_count = data.total_households * 0.08
    household_total = (
        household_base_count * FAMILY_DINING_PRICE * 1.0 * region_rate
        * household_weight * apartment_weight * income_weight * 1.0 * pedestrian_quality
    )
    worker_total = (
        data.worker_population * WORKER_VISIT_RATE * AVG_DINING_PRICE
        * region_rate * GUKBAP_PREFERENCE * income_weight
    )

    candidate_traffic_sales = traffic_potential_total * candidate_score / total_score
    candidate_household_sales = household_total * candidate_score / total_score
    candidate_worker_sales = worker_total * candidate_score / total_score

    month_index = MONTH_INDEX[area_type][max(1, min(12, int(data.survey_month))) - 1]
    weekday_index = WEEKDAY_INDEX[area_type].get(data.weekday, 1.0)

    hall_sales = candidate_traffic_sales + candidate_household_sales + candidate_worker_sales
    adjusted_sales = hall_sales / month_index / weekday_index
    daily_sales_thousand = adjusted_sales / 1000
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
        "trade_area_label": trade_area_label(area_type),
        "main_customer_ratio": main_ratio,
        "twenties_ratio": twenties_ratio,
        "daily_traffic": daily_traffic,
        "candidate_score": candidate_score,
        "total_competition_score": total_score,
        "traffic_potential_total": traffic_potential_total,
        "household_potential_total": household_total,
        "worker_potential_total": worker_total,
        "candidate_traffic_sales": candidate_traffic_sales,
        "candidate_household_sales": candidate_household_sales,
        "candidate_worker_sales": candidate_worker_sales,
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
        "weights": {
            "region_dining_rate": region_rate,
            "household_weight": household_weight,
            "apartment_weight": apartment_weight,
            "income_weight": income_weight,
            "pedestrian_quality": pedestrian_quality,
            "twenties_adjust": twenties_adjust,
        },
    }


if __name__ == "__main__":
    result = calculate(default_input())
    for key, value in result.items():
        print(key, value)
