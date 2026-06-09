from __future__ import annotations

from dataclasses import dataclass
from types import ModuleType

try:
    from industries import chicken_calc, haejang_calc, pizza_calc
except ModuleNotFoundError:
    import chicken_calc
    import haejang_calc
    import pizza_calc
from pure_model import ModelInput


@dataclass(frozen=True)
class IndustryInfo:
    code: str
    name: str
    module: ModuleType | None
    status: str = "ready"
    note: str = ""
    accuracy_status: str = "calibrated_mvp"

    @property
    def label(self) -> str:
        suffix = "" if self.status == "ready" else " (준비 중)"
        return f"{self.name}{suffix}"


READY_INDUSTRIES = [
    IndustryInfo(
        haejang_calc.CODE,
        haejang_calc.NAME,
        haejang_calc,
        haejang_calc.STATUS,
        haejang_calc.MVP_NOTE,
        "excel_conversion_in_progress",
    ),
    IndustryInfo(
        pizza_calc.CODE,
        pizza_calc.NAME,
        pizza_calc,
        pizza_calc.STATUS,
        pizza_calc.MVP_NOTE,
        "calibrated_mvp",
    ),
    IndustryInfo(
        chicken_calc.CODE,
        chicken_calc.NAME,
        chicken_calc,
        chicken_calc.STATUS,
        chicken_calc.MVP_NOTE,
        "calibrated_mvp",
    ),
]

COMING_SOON_NAMES = [
    "카페",
    "베이커리",
    "분식",
    "한식",
    "중식",
    "일식",
    "양식",
    "패스트푸드",
    "아이스크림",
    "도시락",
    "편의점",
    "마트",
    "정육점",
    "반찬가게",
    "미용실",
    "네일샵",
    "피부관리",
    "헬스장",
    "필라테스",
    "학원",
    "스터디카페",
    "독서실",
    "PC방",
    "노래방",
    "세탁소",
    "약국",
    "병원",
    "동물병원",
    "애견미용",
    "부동산",
    "휴대폰매장",
    "안경점",
    "꽃집",
    "주점",
    "호프",
    "배달전문점",
    "무인점포",
    "키즈카페",
    "자동차정비",
]

COMING_SOON_INDUSTRIES = [
    IndustryInfo(
        f"future_{index:02d}",
        name,
        None,
        "coming_soon",
        "업종별 엑셀 로직을 추출한 뒤 활성화합니다.",
        "not_started",
    )
    for index, name in enumerate(COMING_SOON_NAMES, start=1)
]

INDUSTRIES = READY_INDUSTRIES + COMING_SOON_INDUSTRIES
INDUSTRY_BY_CODE = {industry.code: industry for industry in INDUSTRIES}
INDUSTRY_BY_LABEL = {industry.label: industry for industry in INDUSTRIES}


def get_default_input(industry_code: str) -> ModelInput:
    industry = get_ready_industry(industry_code)
    return industry.module.get_default_input()


def calculate_industry(industry_code: str, data: ModelInput) -> dict:
    industry = get_ready_industry(industry_code)
    return industry.module.calculate(data)


def get_ready_industry(industry_code: str) -> IndustryInfo:
    industry = INDUSTRY_BY_CODE[industry_code]
    if industry.status != "ready" or industry.module is None:
        raise ValueError(f"{industry.name} 업종은 아직 계산 엔진이 연결되지 않았습니다.")
    return industry
