from __future__ import annotations

from pure_model import ModelInput, calculate as calculate_common, default_input


CODE = "haejang"
NAME = "음식점 / 해장국"
MVP_NOTE = "울엄마해장 엑셀 로직을 기준으로 변환한 계산기입니다."
STATUS = "ready"


def get_default_input() -> ModelInput:
    return default_input()


def calculate(data: ModelInput) -> dict:
    result = calculate_common(data)
    result["industry_code"] = CODE
    result["industry_name"] = NAME
    result["mvp_note"] = MVP_NOTE
    return result

