from __future__ import annotations

from pure_model import ModelInput, calculate as calculate_common, default_input

try:
    from industries.haejang_excel_map import assert_default_parity, base_input_cell_map
except ModuleNotFoundError:
    from haejang_excel_map import assert_default_parity, base_input_cell_map


CODE = "haejang"
NAME = "음식점 / 해장국"
MVP_NOTE = "울엄마해장 원본 엑셀 기본값과 핵심 중간값 검증을 통과한 계산기입니다."
STATUS = "ready"
ACCURACY_STATUS = "default_excel_match_input_mapped"


def get_default_input() -> ModelInput:
    return default_input()


def calculate(data: ModelInput) -> dict:
    result = calculate_common(data)
    result["industry_code"] = CODE
    result["industry_name"] = NAME
    result["mvp_note"] = MVP_NOTE
    result["accuracy_status"] = ACCURACY_STATUS
    result["excel_input_cells"] = base_input_cell_map()
    return result


def validate_default_excel_parity() -> None:
    assert_default_parity()
