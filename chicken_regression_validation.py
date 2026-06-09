from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from industries.chicken_calc import calculate, get_default_input
from excel_validation import chicken_default_validation_report, chicken_excel_updates_from_model, recalc_excel_output


TOLERANCE = 1e-6


@dataclass(frozen=True)
class RegressionResult:
    name: str
    description: str
    python_value: float
    excel_value: float

    @property
    def diff(self) -> float:
        return self.python_value - self.excel_value

    @property
    def passed(self) -> bool:
        return abs(self.diff) <= TOLERANCE


def regression_cases() -> list[tuple[str, str, Callable]]:
    return [
        ("default", "원본 기본 입력값", lambda data: None),
        ("weekday_friday", "조사요일 수 -> 금", lambda data: setattr(data, "weekday", "금")),
        ("weekday_monday", "조사요일 수 -> 월", lambda data: setattr(data, "weekday", "월")),
        ("month_3", "조사월 8 -> 3", lambda data: setattr(data, "survey_month", 3)),
        ("traffic_d43_f43_up", "19~20시 20대 남 통행량 22 -> 80", lambda data: data.traffic[8].__setitem__(2, 80)),
        (
            "households_4500",
            "아파트 3,200 / 주택계 4,500",
            lambda data: (setattr(data, "apartment_households", 3200), setattr(data, "total_households", 4500)),
        ),
        ("worker_5000", "상주인구 863 -> 5,000", lambda data: setattr(data, "worker_population", 5000)),
        (
            "apt_size_high",
            "30평 이상 아파트 비율 상승",
            lambda data: data.extra_inputs["apartment_size_mix"].__setitem__(
                0,
                {"0~20평": 300, "20~29평": 300, "30~39평": 800, "40~49평": 200, "50평 이상": 100, "단독/다세대": 831},
            ),
        ),
        (
            "apt_price_high",
            "3억원 이상 아파트 가격대 비율 상승",
            lambda data: data.extra_inputs["apartment_price_mix"].__setitem__(
                0,
                {"1억 미만": 100, "1억원대": 100, "2억원대": 100, "3억원대": 500, "4억원대": 300, "5억원대": 200, "6억원 이상": 100},
            ),
        ),
        ("candidate_no_delivery", "후보점 배달 여부 1 -> 0", lambda data: data.extra_inputs["direct_competitor_rows"][0].update({"배달 여부": 0})),
        ("candidate_no_takeout", "후보점 테이크아웃 여부 1 -> 0", lambda data: data.extra_inputs["direct_competitor_rows"][0].update({"테이크아웃 여부": 0})),
        ("candidate_area_25", "후보점 면적 11평 -> 25평", lambda data: setattr(data.direct_competitors[0], "area", 25)),
    ]


def run_regressions() -> list[RegressionResult]:
    results: list[RegressionResult] = []
    for name, description, mutator in regression_cases():
        data = get_default_input()
        mutator(data)
        python_value = calculate(data)["daily_sales_thousand"]
        excel_value = recalc_excel_output("chicken", chicken_excel_updates_from_model(data), timeout_seconds=30)
        results.append(RegressionResult(name, description, python_value, excel_value))
    return results


def run_default_intermediate_checks() -> list[dict]:
    result = calculate(get_default_input())
    return chicken_default_validation_report(result, tolerance=TOLERANCE)


def main() -> None:
    print("Intermediate checks")
    for row in run_default_intermediate_checks():
        print(row)
    print("\nRegression checks")
    for row in run_regressions():
        print(
            {
                "name": row.name,
                "description": row.description,
                "python_value": row.python_value,
                "excel_value": row.excel_value,
                "diff": row.diff,
                "passed": row.passed,
            }
        )


if __name__ == "__main__":
    main()
