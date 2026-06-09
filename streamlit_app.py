from __future__ import annotations

import math
import uuid
import json

import streamlit as st
import streamlit.components.v1 as components

from supabase_backend import (
    authenticate_user,
    get_admin_user_ids,
    has_result_access,
    init_supabase,
    list_analysis_results,
    mark_user_paid,
    register_user,
    save_analysis_result,
    set_access_token,
    sign_out_user,
)
try:
    from industries.registry import INDUSTRIES, calculate_industry
except ModuleNotFoundError:
    from registry import INDUSTRIES, calculate_industry
from pure_model import AGE_COLUMNS, TIME_LABELS, Competitor, ModelInput


def inject_custom_css() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

        :root {
            --app-bg: #f7f9fb;
            --surface: #ffffff;
            --surface-soft: #eef6f5;
            --text-main: #17212b;
            --text-muted: #637083;
            --line: #dde6ee;
            --accent: #0f766e;
            --accent-hover: #0b5f59;
            --accent-soft: #dff4f1;
            --warning-bg: #fff7ed;
            --warning-line: #fed7aa;
        }

        html, body, [class*="css"] {
            font-family: 'Inter', 'Noto Sans KR', system-ui, -apple-system, BlinkMacSystemFont, sans-serif;
        }

        .stApp {
            background:
                radial-gradient(circle at top left, rgba(15, 118, 110, 0.10), transparent 30rem),
                var(--app-bg);
            color: var(--text-main);
        }

        .block-container {
            max-width: 1180px;
            padding-top: 2.2rem;
            padding-bottom: 4rem;
        }

        h1 {
            font-weight: 800 !important;
            letter-spacing: 0 !important;
            color: var(--text-main);
        }

        h2, h3 {
            letter-spacing: 0 !important;
            color: var(--text-main);
        }

        [data-testid="stSidebar"] {
            background: #ffffff;
            border-right: 1px solid var(--line);
        }

        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
            color: var(--text-muted);
        }

        .stButton > button,
        .stFormSubmitButton > button {
            border-radius: 10px !important;
            border: 1px solid var(--accent) !important;
            background: var(--accent) !important;
            color: #ffffff !important;
            font-weight: 700 !important;
            min-height: 2.8rem;
            box-shadow: 0 8px 20px rgba(15, 118, 110, 0.18);
            transition: transform 140ms ease, box-shadow 140ms ease, background 140ms ease;
        }

        .stButton > button:hover,
        .stFormSubmitButton > button:hover {
            background: var(--accent-hover) !important;
            border-color: var(--accent-hover) !important;
            transform: translateY(-1px);
            box-shadow: 0 12px 26px rgba(15, 118, 110, 0.24);
        }

        .stButton > button:disabled {
            background: #e6edf3 !important;
            border-color: #d7e1ea !important;
            color: #8a99a8 !important;
            box-shadow: none;
            transform: none;
        }

        [data-testid="stTextInput"] input,
        [data-testid="stNumberInput"] input,
        [data-baseweb="select"] > div {
            border-radius: 10px !important;
            border-color: var(--line) !important;
            background: #ffffff !important;
            min-height: 2.65rem;
        }

        [data-testid="stTextInput"] input:focus,
        [data-testid="stNumberInput"] input:focus {
            border-color: var(--accent) !important;
            box-shadow: 0 0 0 3px rgba(15, 118, 110, 0.12) !important;
        }

        [data-testid="stDataFrame"],
        [data-testid="stDataEditor"] {
            border-radius: 12px;
            overflow: hidden;
            border: 1px solid var(--line);
            background: #ffffff;
        }

        [data-testid="stMetric"] {
            background: var(--surface);
            border: 1px solid var(--line);
            border-radius: 12px;
            padding: 1rem;
            box-shadow: 0 10px 26px rgba(23, 33, 43, 0.05);
        }

        .stAlert {
            border-radius: 12px;
        }

        .wizard-card {
            background: rgba(255, 255, 255, 0.86);
            border: 1px solid var(--line);
            border-radius: 14px;
            padding: 1rem 1.1rem;
            margin: 0.5rem 0 1.2rem;
            box-shadow: 0 14px 34px rgba(23, 33, 43, 0.06);
        }

        .wizard-progress-head {
            display: flex;
            justify-content: space-between;
            gap: 1rem;
            align-items: center;
            margin-bottom: 0.75rem;
        }

        .wizard-progress-title {
            font-size: 0.95rem;
            color: var(--text-muted);
            font-weight: 600;
        }

        .wizard-progress-count {
            color: var(--accent);
            font-weight: 800;
        }

        .wizard-track {
            width: 100%;
            height: 10px;
            background: #e5edf2;
            border-radius: 999px;
            overflow: hidden;
            margin-bottom: 0.85rem;
        }

        .wizard-track-fill {
            height: 100%;
            background: linear-gradient(90deg, #0f766e, #14b8a6);
            border-radius: 999px;
            transition: width 180ms ease;
        }

        .wizard-steps {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 0.5rem;
        }

        .wizard-step {
            border: 1px solid var(--line);
            border-radius: 999px;
            padding: 0.45rem 0.65rem;
            font-size: 0.83rem;
            color: var(--text-muted);
            background: #ffffff;
            text-align: center;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        .wizard-step.done {
            border-color: var(--accent);
            background: var(--accent-soft);
            color: var(--accent);
            font-weight: 700;
        }

        .wizard-step.active {
            border-color: var(--accent);
            background: var(--accent);
            color: #ffffff;
            font-weight: 800;
            box-shadow: 0 10px 22px rgba(15, 118, 110, 0.18);
        }

        @media (max-width: 760px) {
            .block-container {
                padding-left: 1rem;
                padding-right: 1rem;
            }

            .wizard-steps {
                grid-template-columns: 1fr;
            }

            .wizard-step {
                text-align: left;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


st.set_page_config(page_title="상권 입지 평가 매출예측 SaaS MVP", layout="wide")
inject_custom_css()

admin_user_ids = get_admin_user_ids(st.secrets)
database_engine = None
database_error = None
try:
    database_engine = init_supabase(st.secrets)
except Exception as exc:
    database_error = exc


def render_auth_screen() -> None:
    st.title("상권 입지 평가 매출예측 SaaS MVP")
    st.caption("로그인 후 업종별 상권 분석과 저장 기록을 이용할 수 있습니다.")
    if database_engine is None:
        st.error(f"데이터베이스 연결 실패: {database_error}")
        st.stop()

    login_tab, signup_tab = st.tabs(["로그인", "회원가입"])

    with login_tab:
        with st.form("login_form"):
            user_id = st.text_input("이메일")
            password = st.text_input("비밀번호", type="password")
            submitted = st.form_submit_button("로그인", type="primary")
        if submitted:
            user = authenticate_user(database_engine, user_id=user_id, password=password)
            if user is None:
                st.error("아이디 또는 비밀번호가 올바르지 않습니다.")
            else:
                st.session_state["current_user"] = user
                st.rerun()

    with signup_tab:
        with st.form("signup_form"):
            new_user_id = st.text_input("이메일")
            name = st.text_input("이름")
            new_password = st.text_input("새 비밀번호", type="password")
            confirm_password = st.text_input("비밀번호 확인", type="password")
            submitted = st.form_submit_button("회원가입")
        if submitted:
            if new_password != confirm_password:
                st.error("비밀번호 확인이 일치하지 않습니다.")
            else:
                try:
                    user = register_user(
                        database_engine,
                        user_id=new_user_id,
                        password=new_password,
                        name=name,
                        admin_user_ids=admin_user_ids,
                    )
                except ValueError as exc:
                    st.error(str(exc))
                else:
                    st.session_state["current_user"] = user
                    st.success(f"{user['role']} 권한으로 가입되었습니다.")
                    st.rerun()


def value_to_float(value) -> float:
    if value is None:
        return 0.0
    if isinstance(value, float) and math.isnan(value):
        return 0.0
    return float(value) if value is not None else 0.0


def value_to_optional_float(value):
    return None if value in (None, "") else float(value)


def validate_input(data: ModelInput) -> list[str]:
    errors = []
    if not data.store_name.strip():
        errors.append("후보점명을 입력하세요.")
    if data.survey_month < 1 or data.survey_month > 12:
        errors.append("조사월을 선택하세요.")
    if not data.weekday:
        errors.append("요일을 선택하세요.")
    if not data.region:
        errors.append("지역 권역을 선택하세요.")
    if not data.admin_unit:
        errors.append("행정 단위를 선택하세요.")
    if not data.operation_type:
        errors.append("운영 형태를 선택하세요.")
    if data.total_households <= 0:
        errors.append("주택계를 입력하세요.")
    if sum(sum(row) for row in data.traffic) <= 0:
        errors.append("통행량을 1명 이상 입력하세요.")
    if not data.direct_competitors:
        errors.append("직접 경쟁점을 1개 이상 입력하세요. 첫 번째 행은 후보점으로 입력해야 합니다.")
    if data.business_days <= 0:
        errors.append("영업일수를 입력하세요.")
    return errors


def get_secret_value(name: str, default=None):
    try:
        return st.secrets.get(name, default)
    except Exception:
        return default


def empty_competitor_row() -> dict:
    return {
        "점명": None,
        "면적(평)": None,
        "거리": None,
        "입지": None,
        "시계성": None,
        "접근성": None,
        "층": None,
        "면(각)": None,
        "전면 길이": None,
        "집기 설비": None,
        "주차": None,
        "가격": None,
    }


def rows_to_competitors(rows) -> list[Competitor]:
    if hasattr(rows, "to_dict"):
        rows = rows.to_dict("records")
    converted = []
    for row in rows:
        name = str(row.get("점명", "") or "").strip()
        if not name:
            continue
        converted.append(
            Competitor(
                name=name,
                area=value_to_float(row.get("면적(평)")),
                distance=value_to_float(row.get("거리")),
                location=value_to_float(row.get("입지")),
                visibility=value_to_float(row.get("시계성")),
                accessibility=value_to_float(row.get("접근성")),
                floor=value_to_float(row.get("층")),
                sides=value_to_float(row.get("면(각)")),
                frontage=value_to_float(row.get("전면 길이")),
                facility=value_to_float(row.get("집기 설비")),
                parking=value_to_float(row.get("주차")),
                price=value_to_float(row.get("가격")),
            )
        )
    return converted


def process_portone_success(industry_code: str) -> None:
    if database_engine is None:
        return
    params = st.query_params
    if params.get("portone_paid") != "1":
        return

    merchant_uid = params.get("merchant_uid", "")
    expected_merchant_uid = st.session_state.get(f"{industry_code}_merchant_uid")
    if not merchant_uid or merchant_uid != expected_merchant_uid:
        st.warning("결제 신호를 확인했지만 주문번호가 현재 세션과 일치하지 않습니다.")
        return

    amount = value_to_float(params.get("amount"))
    payment_data = {
        "merchant_uid": merchant_uid,
        "imp_uid": params.get("imp_uid", ""),
        "amount": amount,
        "status": "paid",
    }
    mark_user_paid(database_engine, user_id=current_user["user_id"], payment_data=payment_data)
    st.session_state["current_user"]["payment_status"] = "paid"
    st.session_state[f"{industry_code}_payment_completed"] = True
    st.query_params.clear()
    st.rerun()


def render_portone_payment(industry_code: str, data: ModelInput) -> None:
    imp_code = get_secret_value("PORTONE_IMP_CODE", "")
    pg_provider = get_secret_value("PORTONE_PG", "html5_inicis")
    pay_method = get_secret_value("PORTONE_PAY_METHOD", "card")
    amount = int(value_to_float(get_secret_value("PORTONE_PAYMENT_AMOUNT", 1000)))
    product_name = get_secret_value("PORTONE_PRODUCT_NAME", "상권 매출 예측 분석 리포트")

    if not imp_code:
        st.error(".streamlit/secrets.toml에 PORTONE_IMP_CODE를 설정해야 결제창을 열 수 있습니다.")
        return

    merchant_key = f"{industry_code}_merchant_uid"
    if merchant_key not in st.session_state:
        st.session_state[merchant_key] = f"analysis-{current_user['user_id']}-{uuid.uuid4().hex[:12]}"
    merchant_uid = st.session_state[merchant_key]
    buyer_email = current_user.get("email", "")
    buyer_name = current_user.get("name", "")
    store_name = data.store_name or "상권 분석"
    payment_name = f"{product_name} - {store_name}"

    html = f"""
    <div style="font-family: system-ui, -apple-system, BlinkMacSystemFont, sans-serif; padding: 12px 0;">
      <button
        onclick="requestPortOnePayment()"
        style="
          width: 100%;
          min-height: 48px;
          border: 0;
          border-radius: 10px;
          background: #0f766e;
          color: white;
          font-size: 16px;
          font-weight: 800;
          cursor: pointer;
          box-shadow: 0 10px 24px rgba(15, 118, 110, 0.22);
        "
      >
        카드 결제창 열기
      </button>
      <p id="payment-status" style="margin-top: 10px; color: #637083; font-size: 13px;">
        결제 금액: {amount:,}원
      </p>
    </div>
    <script src="https://cdn.iamport.kr/v1/iamport.js"></script>
    <script>
      const IMP = window.IMP;
      IMP.init("{imp_code}");

      function notifyParent(payload) {{
        window.parent.postMessage({{
          type: "PORTONE_PAYMENT_RESULT",
          payload
        }}, "*");
      }}

      function requestPortOnePayment() {{
        document.getElementById("payment-status").innerText = "결제창을 여는 중입니다...";
        IMP.request_pay({{
          pg: {json.dumps(pg_provider, ensure_ascii=False)},
          pay_method: {json.dumps(pay_method, ensure_ascii=False)},
          merchant_uid: {json.dumps(merchant_uid, ensure_ascii=False)},
          name: {json.dumps(payment_name, ensure_ascii=False)},
          amount: {amount},
          buyer_email: {json.dumps(buyer_email, ensure_ascii=False)},
          buyer_name: {json.dumps(buyer_name, ensure_ascii=False)}
        }}, function (rsp) {{
          notifyParent(rsp);
          if (rsp.success || rsp.imp_uid) {{
            const params = new URLSearchParams(window.parent.location.search);
            params.set("portone_paid", "1");
            params.set("merchant_uid", "{merchant_uid}");
            params.set("imp_uid", rsp.imp_uid || "");
            params.set("amount", String({amount}));
            window.parent.location.search = params.toString();
          }} else {{
            const message = rsp.error_msg || "결제가 취소되었거나 실패했습니다.";
            document.getElementById("payment-status").innerText = message;
          }}
        }});
      }}
    </script>
    """
    components.html(html, height=110)


if "current_user" not in st.session_state:
    render_auth_screen()
    st.stop()

current_user = st.session_state["current_user"]
is_admin = current_user["role"] == "Admin"
if database_engine is not None:
    set_access_token(database_engine, current_user.get("access_token"))

STEP_LABELS = [
    "1단계: 업종 선택 및 기본 정보",
    "2단계: 배후 세대 및 통행량 입력",
    "3단계: 주변 경쟁점 정보",
    "4단계: 투자금 및 비용 입력",
    "5단계: 결제 및 분석 결과",
    "저장 기록",
]

if "wizard_step" not in st.session_state:
    st.session_state["wizard_step"] = 0


def set_wizard_step(step: int) -> None:
    st.session_state["wizard_step"] = max(0, min(step, len(STEP_LABELS) - 1))


def render_step_controls() -> None:
    current_step = st.session_state["wizard_step"]
    input_step = min(current_step + 1, 4)
    progress_percent = int(input_step / 4 * 100)
    input_labels = [
        "업종/기본정보",
        "세대/통행량",
        "경쟁점",
        "투자/비용",
    ]
    step_items = []
    for index, label in enumerate(input_labels, start=1):
        if input_step == index and current_step <= 3:
            css_class = "wizard-step active"
        elif input_step >= index:
            css_class = "wizard-step done"
        else:
            css_class = "wizard-step"
        step_items.append(f'<div class="{css_class}">{index}. {label}</div>')

    st.markdown(
        f"""
        <div class="wizard-card">
            <div class="wizard-progress-head">
                <div class="wizard-progress-title">입력 진행률</div>
                <div class="wizard-progress-count">{input_step} / 4 단계</div>
            </div>
            <div class="wizard-track">
                <div class="wizard-track-fill" style="width: {progress_percent}%"></div>
            </div>
            <div class="wizard-steps">
                {''.join(step_items)}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.caption(f"현재 화면: {STEP_LABELS[current_step]}")
    nav_cols = st.columns([1, 1, 2])
    with nav_cols[0]:
        if st.button("이전", disabled=current_step == 0):
            set_wizard_step(current_step - 1)
            st.rerun()
    with nav_cols[1]:
        if st.button("다음", type="primary", disabled=current_step >= len(STEP_LABELS) - 1):
            set_wizard_step(current_step + 1)
            st.rerun()
    with nav_cols[2]:
        st.write("")


def get_selected_industry():
    selected_label = st.session_state.get("wizard_industry_label")
    if not selected_label:
        return None
    return next((industry for industry in INDUSTRIES if industry.label == selected_label), None)


def build_base_input(industry_code: str) -> ModelInput:
    data = ModelInput()
    data.store_name = st.session_state.get(f"{industry_code}_store_name", "") or ""
    data.survey_month = int(st.session_state.get(f"{industry_code}_survey_month") or 0)
    data.weekday = st.session_state.get(f"{industry_code}_weekday", "") or ""
    data.region = st.session_state.get(f"{industry_code}_region", "") or ""
    data.admin_unit = st.session_state.get(f"{industry_code}_admin_unit", "") or ""
    data.operation_type = st.session_state.get(f"{industry_code}_operation_type", "") or ""
    data.apartment_households = value_to_float(st.session_state.get(f"{industry_code}_apartment_households"))
    data.total_households = value_to_float(st.session_state.get(f"{industry_code}_total_households"))
    data.resident_population = value_to_float(st.session_state.get(f"{industry_code}_resident_population"))
    data.worker_population = value_to_float(st.session_state.get(f"{industry_code}_worker_population"))
    data.annual_income = value_to_float(st.session_state.get(f"{industry_code}_annual_income"))
    data.deposit = value_to_float(st.session_state.get(f"{industry_code}_deposit"))
    data.goodwill = value_to_float(st.session_state.get(f"{industry_code}_goodwill"))
    data.monthly_rent = value_to_float(st.session_state.get(f"{industry_code}_monthly_rent"))
    data.management_fee = value_to_float(st.session_state.get(f"{industry_code}_management_fee"))
    data.royalty_rate = value_to_float(st.session_state.get(f"{industry_code}_royalty_rate"))
    data.business_days = value_to_float(st.session_state.get(f"{industry_code}_business_days"))
    data.cogs_rate = value_to_float(st.session_state.get(f"{industry_code}_cogs_rate"))
    data.franchise_fee = value_to_float(st.session_state.get(f"{industry_code}_franchise_fee"))
    data.education_fee = value_to_float(st.session_state.get(f"{industry_code}_education_fee"))
    data.guarantee_deposit = value_to_float(st.session_state.get(f"{industry_code}_guarantee_deposit"))
    data.opening_promo_fee = value_to_float(st.session_state.get(f"{industry_code}_opening_promo_fee"))

    traffic_rows = st.session_state.get(f"{industry_code}_traffic", default_traffic_rows())
    if hasattr(traffic_rows, "to_dict"):
        traffic_rows = traffic_rows.to_dict("records")
    data.traffic = [[value_to_float(row.get(col)) for col in AGE_COLUMNS] for row in traffic_rows]

    direct_rows = st.session_state.get(f"{industry_code}_direct_competitors", [empty_competitor_row()])
    indirect_rows = st.session_state.get(f"{industry_code}_indirect_competitors", [empty_competitor_row()])
    data.direct_competitors = rows_to_competitors(direct_rows)
    data.indirect_competitors = rows_to_competitors(indirect_rows)
    return data


def default_traffic_rows() -> list[dict]:
    return [{"시간": label, **{column: None for column in AGE_COLUMNS}} for label in TIME_LABELS]


def render_account_sidebar() -> None:
    with st.sidebar:
        st.header("계정")
        st.write(f"{current_user['name']}님")
        st.caption(f"권한: {current_user['role']}")
        st.caption(f"결제 상태: {current_user.get('payment_status', 'unpaid')}")
        if st.button("로그아웃"):
            st.session_state.pop("current_user", None)
            st.rerun()

        st.header("저장소 상태")
        if database_engine is None:
            st.error("DB 연결 실패")
        else:
            st.success("Supabase 연결")
        if is_admin:
            st.caption("Admin 계정은 전체 저장 기록을 조회할 수 있습니다.")
        else:
            st.caption("User 계정은 본인이 저장한 기록만 조회합니다.")


def render_step_1(industry_code: str | None) -> None:
    st.subheader("1단계: 업종 선택 및 기본 정보")
    industry_labels = [industry.label for industry in INDUSTRIES]
    st.selectbox(
        "업종 선택",
        industry_labels,
        index=None,
        placeholder="선택 안 됨",
        key="wizard_industry_label",
    )

    selected_industry = get_selected_industry()
    if selected_industry is None:
        st.info("업종을 먼저 선택하세요.")
        return
    if selected_industry.status != "ready":
        st.info(
            f"{selected_industry.name} 업종은 등록 예정입니다. "
            "해당 업종의 엑셀 파일을 분석해 전용 계산 모듈을 만든 뒤 활성화합니다."
        )
        return

    st.info(selected_industry.note)
    if selected_industry.accuracy_status != "exact_excel_match":
        st.warning(
            "이 업종은 아직 원본 엑셀 전체 수식을 100% 완전 이식한 상태가 아닙니다. "
            "최종 상업용 MVP에서는 원본 엑셀과 입력 변경 테스트를 통과한 업종만 결과 공개 대상으로 전환해야 합니다."
        )

    weekdays = ["월", "화", "수", "목", "금", "토", "일"]
    regions = ["서울 경기", "충청권", "호남권", "대구경북", "부산 경남", "강원권"]
    admin_units = ["시 단위", "군 단위"]
    operation_types = ["직영점", "가맹점", "위탁운영"]

    col1, col2, col3 = st.columns(3)
    with col1:
        st.text_input("후보점명", value="", key=f"{industry_code}_store_name")
        st.number_input("조사월", min_value=1, max_value=12, value=None, key=f"{industry_code}_survey_month")
    with col2:
        st.number_input("조사일", min_value=1, max_value=31, value=None, key=f"{industry_code}_survey_day")
        st.selectbox("요일", weekdays, index=None, placeholder="선택 안 됨", key=f"{industry_code}_weekday")
    with col3:
        st.checkbox("24시간 영업", value=False, key=f"{industry_code}_is_24h")
        st.selectbox("운영 형태", operation_types, index=None, placeholder="선택 안 됨", key=f"{industry_code}_operation_type")

    col1, col2 = st.columns(2)
    with col1:
        st.selectbox("지역 권역", regions, index=None, placeholder="선택 안 됨", key=f"{industry_code}_region")
    with col2:
        st.selectbox("행정 단위", admin_units, index=None, placeholder="선택 안 됨", key=f"{industry_code}_admin_unit")


def render_step_2(industry_code: str) -> None:
    st.subheader("2단계: 배후 세대 및 통행량 입력")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.number_input("아파트 세대수", value=None, step=10.0, key=f"{industry_code}_apartment_households")
        st.number_input("주택계", value=None, step=10.0, key=f"{industry_code}_total_households")
    with col2:
        apartment = value_to_float(st.session_state.get(f"{industry_code}_apartment_households"))
        total = value_to_float(st.session_state.get(f"{industry_code}_total_households"))
        st.number_input("단독/다세대", value=float(max(total - apartment, 0)), step=10.0, disabled=True, key=f"{industry_code}_single_households")
        st.number_input("주거인구", value=None, step=10.0, key=f"{industry_code}_resident_population")
    with col3:
        st.number_input("직장인구", value=None, step=10.0, key=f"{industry_code}_worker_population")
        st.number_input("가구당 연간 소득(만원)", value=None, step=10.0, key=f"{industry_code}_annual_income")

    st.subheader("통행량 조사")
    st.data_editor(
        default_traffic_rows(),
        use_container_width=True,
        hide_index=True,
        num_rows="fixed",
        key=f"{industry_code}_traffic",
    )


def render_step_3(industry_code: str) -> None:
    st.subheader("3단계: 주변 경쟁점 정보")
    st.caption("직접 경쟁점의 첫 번째 행은 후보점 정보로 입력하세요.")
    st.subheader("직접 경쟁점")
    st.data_editor(
        [empty_competitor_row()],
        use_container_width=True,
        hide_index=True,
        num_rows="dynamic",
        key=f"{industry_code}_direct_competitors",
    )
    st.subheader("간접 경쟁점")
    st.data_editor(
        [empty_competitor_row()],
        use_container_width=True,
        hide_index=True,
        num_rows="dynamic",
        key=f"{industry_code}_indirect_competitors",
    )


def render_step_4(industry_code: str) -> None:
    st.subheader("4단계: 투자금 및 비용 입력")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.number_input("임차보증금(천원)", value=None, step=100.0, key=f"{industry_code}_deposit")
    with col2:
        st.number_input("영업권(천원)", value=None, step=100.0, key=f"{industry_code}_goodwill")
    with col3:
        st.number_input("월임대료(천원)", value=None, step=100.0, key=f"{industry_code}_monthly_rent")
    with col4:
        st.number_input("관리비(천원)", value=None, step=10.0, key=f"{industry_code}_management_fee")

    st.subheader("투자손익 입력")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.number_input("로열티율", value=None, min_value=0.0, max_value=1.0, step=0.005, format="%.3f", key=f"{industry_code}_royalty_rate")
        st.number_input("가입비(천원)", value=None, step=100.0, key=f"{industry_code}_franchise_fee")
    with col2:
        st.number_input("영업일수", value=None, min_value=1.0, max_value=31.0, step=1.0, key=f"{industry_code}_business_days")
        st.number_input("교육비(천원)", value=None, step=100.0, key=f"{industry_code}_education_fee")
    with col3:
        st.number_input("평균 매출원가율", value=None, min_value=0.0, max_value=1.0, step=0.01, format="%.2f", key=f"{industry_code}_cogs_rate")
        st.number_input("보증금(천원)", value=None, step=100.0, key=f"{industry_code}_guarantee_deposit")
    st.number_input("개점홍보비(천원)", value=None, step=100.0, key=f"{industry_code}_opening_promo_fee")


def render_step_5(industry_code: str, selected_industry) -> None:
    st.subheader("5단계: 결제 및 분석 결과")
    process_portone_success(industry_code)
    data = build_base_input(industry_code)
    if st.button("분석 결과 보기", type="primary", key=f"{industry_code}_show_result"):
        st.session_state[f"{industry_code}_analysis_requested"] = True

    if not st.session_state.get(f"{industry_code}_analysis_requested", False):
        st.info("입력값을 확인한 뒤 `분석 결과 보기` 버튼을 누르면 결과 확인 절차가 시작됩니다.")
        return

    validation_errors = validate_input(data)
    if validation_errors:
        st.warning("계산 전에 필요한 입력값이 남아 있습니다.")
        for message in validation_errors:
            st.write(f"- {message}")
        return
    if database_engine is None:
        st.warning(f"데이터베이스에 연결하지 못해 결제 상태를 확인할 수 없습니다: {database_error}")
        return
    if not has_result_access(current_user):
        st.warning("결제가 필요합니다.")
        st.write("일반 User 계정은 카드 결제 완료 후 최종 매출 예측 결과를 확인할 수 있습니다.")
        render_portone_payment(industry_code, data)
        st.caption("결제 완료 후 자동으로 결과 화면이 열립니다.")
        return

    if is_admin:
        st.success("Admin 권한으로 결제 없이 결과를 열람합니다.")

    try:
        result = calculate_industry(industry_code, data)
    except Exception as exc:
        st.error(f"계산 중 오류가 발생했습니다: {exc}")
        return

    st.subheader("계산 결과")
    metric_cols = st.columns(4)
    metric_cols[0].metric("예상 일매출액", f"{result['daily_sales_thousand']:,.2f} 천원")
    metric_cols[1].metric("월간 평균 매출액", f"{result['monthly_sales_thousand']:,.2f} 천원")
    metric_cols[2].metric("상권 유형", result["trade_area_label"])
    metric_cols[3].metric("1일 후보점 전면 통행량", f"{result['daily_traffic']:,.2f} 명")

    st.subheader("손익 요약")
    profit_cols = st.columns(4)
    profit_cols[0].metric("월 매출, VAT 제외", f"{result['monthly_sales_ex_vat_thousand']:,.2f} 천원")
    profit_cols[1].metric("매출원가", f"{result['cogs_thousand']:,.2f} 천원")
    profit_cols[2].metric("로열티", f"{result['royalty_thousand']:,.2f} 천원")
    profit_cols[3].metric("공헌이익", f"{result['contribution_profit_thousand']:,.2f} 천원")

    st.subheader("계산 분해")
    st.dataframe(
        [
            {"항목": "주고객 비율", "값": f"{result['main_customer_ratio'] * 100:,.2f}%"},
            {"항목": "후보점 경쟁력 점수", "값": f"{result['candidate_score']:,.2f}"},
            {"항목": "경쟁점 총점", "값": f"{result['total_competition_score']:,.2f}"},
            {"항목": "후보점 통행인 매출", "값": f"{result['candidate_traffic_sales']:,.2f} 원"},
            {"항목": "후보점 세대수 매출", "값": f"{result['candidate_household_sales']:,.2f} 원"},
            {"항목": "후보점 직장인구 매출", "값": f"{result['candidate_worker_sales']:,.2f} 원"},
            {"항목": "월별 보정지수", "값": f"{result['month_index']:,.6f}"},
            {"항목": "요일별 보정지수", "값": f"{result['weekday_index']:,.6f}"},
            {"항목": "초기 투자금", "값": f"{result['initial_investment_thousand']:,.2f} 천원"},
        ],
        use_container_width=True,
        hide_index=True,
    )

    st.subheader("분석 결과 저장")
    if st.button("현재 분석 결과 저장", type="primary", key=f"{industry_code}_save_result"):
        saved_id = save_analysis_result(
            database_engine,
            user_key=current_user["user_id"],
            industry_code=industry_code,
            industry_name=result["industry_name"],
            input_data=data,
            result=result,
        )
        st.success(f"저장 완료: 분석 번호 {saved_id}")


def render_history() -> None:
    st.subheader("저장 기록")
    if database_engine is None:
        st.warning(f"데이터베이스에 연결하지 못해 저장 기록을 불러올 수 없습니다: {database_error}")
        return
    saved_rows = list_analysis_results(
        database_engine,
        user_key=current_user["user_id"],
        limit=200 if is_admin else 20,
        include_all=is_admin,
    )
    if not saved_rows:
        st.info("아직 저장된 분석 결과가 없습니다.")
        return
    if is_admin:
        st.info("Admin 권한으로 모든 회원의 분석 결과를 조회 중입니다.")
    st.dataframe(saved_rows, use_container_width=True, hide_index=True)


st.title("상권 입지 평가 매출예측 SaaS MVP")
st.caption("단계별 입력 화면으로 업종별 엑셀 계산 로직을 실행합니다.")
render_account_sidebar()
render_step_controls()

selected_industry = get_selected_industry()
industry_code = selected_industry.code if selected_industry is not None else "wizard"

current_step = st.session_state["wizard_step"]
if current_step == 0:
    render_step_1(industry_code)
elif selected_industry is None:
    st.info("1단계에서 업종을 먼저 선택하세요.")
elif selected_industry.status != "ready":
    st.info(f"{selected_industry.name} 업종은 아직 준비 중입니다.")
elif current_step == 1:
    render_step_2(industry_code)
elif current_step == 2:
    render_step_3(industry_code)
elif current_step == 3:
    render_step_4(industry_code)
elif current_step == 4:
    render_step_5(industry_code, selected_industry)
else:
    render_history()

st.stop()
