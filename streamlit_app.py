from __future__ import annotations

import math
import uuid
import json

import streamlit as st
import streamlit.components.v1 as components

from commercial_exact import empty_editor_row, get_input_schema, rows_to_plain_records
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
            --app-bg: #f5f7fa;
            --surface: #ffffff;
            --surface-soft: #f0f6f5;
            --ink: #111827;
            --text-main: #17212b;
            --text-muted: #667085;
            --line: #d9e2ea;
            --accent: #0f766e;
            --accent-hover: #0b5f59;
            --accent-soft: #dff4f1;
            --accent-strong: #042f2e;
            --danger: #b42318;
            --warning-bg: #fff7ed;
            --warning-line: #fed7aa;
        }

        html, body, [class*="css"] {
            font-family: 'Inter', 'Noto Sans KR', system-ui, -apple-system, BlinkMacSystemFont, sans-serif;
        }

        .stApp {
            background:
                linear-gradient(180deg, rgba(255,255,255,0.75), rgba(255,255,255,0)),
                radial-gradient(circle at top left, rgba(15, 118, 110, 0.09), transparent 28rem),
                var(--app-bg);
            color: var(--text-main);
        }

        .block-container {
            max-width: 1240px;
            padding-top: 1.7rem;
            padding-bottom: 4rem;
        }

        h1 {
            font-weight: 800 !important;
            letter-spacing: 0 !important;
            color: var(--text-main);
            line-height: 1.12 !important;
        }

        h2, h3 {
            letter-spacing: 0 !important;
            color: var(--text-main);
        }

        [data-testid="stSidebar"] {
            background: rgba(255,255,255,0.92);
            border-right: 1px solid var(--line);
        }

        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
            color: var(--text-muted);
        }

        .stButton > button,
        .stFormSubmitButton > button {
            border-radius: 8px !important;
            border: 1px solid var(--accent) !important;
            background: var(--accent) !important;
            color: #ffffff !important;
            font-weight: 700 !important;
            min-height: 2.75rem;
            box-shadow: 0 8px 18px rgba(15, 118, 110, 0.16);
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
            border-radius: 8px !important;
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
            border-radius: 8px;
            overflow: hidden;
            border: 1px solid var(--line);
            background: #ffffff;
        }

        [data-testid="stMetric"] {
            background: var(--surface);
            border: 1px solid var(--line);
            border-radius: 8px;
            padding: 1rem;
        }

        .stAlert {
            border-radius: 8px;
        }

        .wizard-card {
            background: rgba(255, 255, 255, 0.86);
            border: 1px solid var(--line);
            border-radius: 8px;
            padding: 1rem 1.1rem;
            margin: 0.5rem 0 1.2rem;
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
            border-radius: 8px;
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
            box-shadow: 0 8px 18px rgba(15, 118, 110, 0.18);
        }

        .product-hero {
            display: grid;
            grid-template-columns: minmax(0, 1.2fr) minmax(280px, 0.8fr);
            gap: 2rem;
            align-items: stretch;
            padding: 2.2rem;
            border: 1px solid rgba(15, 118, 110, 0.16);
            border-radius: 8px;
            background:
                linear-gradient(135deg, rgba(4, 47, 46, 0.96), rgba(15, 118, 110, 0.90)),
                linear-gradient(180deg, #0f766e, #042f2e);
            color: #ffffff;
            margin-bottom: 1.4rem;
            overflow: hidden;
            position: relative;
        }

        .product-hero:after {
            content: "";
            position: absolute;
            inset: auto -6rem -8rem auto;
            width: 22rem;
            height: 22rem;
            border: 1px solid rgba(255,255,255,0.16);
            border-radius: 50%;
        }

        .product-hero h1 {
            color: #ffffff !important;
            font-size: clamp(2rem, 4vw, 3.5rem);
            margin: 0 0 0.9rem 0;
        }

        .product-hero p {
            color: rgba(255,255,255,0.78);
            max-width: 42rem;
            margin: 0;
            font-size: 1.02rem;
            line-height: 1.65;
        }

        .hero-meta {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 0.75rem;
            margin-top: 1.5rem;
        }

        .hero-meta-item {
            border: 1px solid rgba(255,255,255,0.18);
            border-radius: 8px;
            padding: 0.85rem;
            background: rgba(255,255,255,0.08);
        }

        .hero-meta-item strong {
            display: block;
            font-size: 1.15rem;
            color: #ffffff;
        }

        .hero-meta-item span {
            color: rgba(255,255,255,0.70);
            font-size: 0.82rem;
        }

        .hero-panel {
            border: 1px solid rgba(255,255,255,0.18);
            border-radius: 8px;
            padding: 1.1rem;
            background: rgba(255,255,255,0.09);
            position: relative;
            z-index: 1;
        }

        .hero-panel-title {
            font-weight: 800;
            color: #ffffff;
            margin-bottom: 0.6rem;
        }

        .hero-list {
            display: grid;
            gap: 0.62rem;
            margin-top: 0.8rem;
        }

        .hero-list div {
            color: rgba(255,255,255,0.78);
            font-size: 0.9rem;
            border-top: 1px solid rgba(255,255,255,0.12);
            padding-top: 0.62rem;
        }

        .app-topbar {
            display: flex;
            justify-content: space-between;
            gap: 1rem;
            align-items: flex-end;
            margin-bottom: 1.2rem;
            padding-bottom: 1rem;
            border-bottom: 1px solid var(--line);
        }

        .app-title {
            margin: 0;
            font-size: 1.75rem;
            font-weight: 850;
            color: var(--ink);
        }

        .app-subtitle {
            margin-top: 0.35rem;
            color: var(--text-muted);
            font-size: 0.95rem;
        }

        .status-pill-row {
            display: flex;
            flex-wrap: wrap;
            justify-content: flex-end;
            gap: 0.5rem;
        }

        .status-pill {
            border: 1px solid var(--line);
            border-radius: 999px;
            padding: 0.42rem 0.72rem;
            background: #ffffff;
            color: var(--text-muted);
            font-size: 0.82rem;
            font-weight: 700;
            white-space: nowrap;
        }

        .status-pill.good {
            border-color: rgba(15,118,110,0.24);
            background: var(--accent-soft);
            color: var(--accent);
        }

        .section-kicker {
            color: var(--accent);
            font-size: 0.78rem;
            font-weight: 800;
            text-transform: uppercase;
            margin-bottom: 0.3rem;
        }

        .section-title {
            font-size: 1.2rem;
            font-weight: 850;
            color: var(--ink);
            margin-bottom: 0.25rem;
        }

        .section-copy {
            color: var(--text-muted);
            margin-bottom: 1rem;
            line-height: 1.55;
        }

        .result-grid {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 0.75rem;
            margin: 0.6rem 0 1.2rem;
        }

        .result-tile {
            border: 1px solid var(--line);
            border-radius: 8px;
            background: #ffffff;
            padding: 1rem;
        }

        .result-label {
            color: var(--text-muted);
            font-size: 0.82rem;
            font-weight: 700;
            margin-bottom: 0.45rem;
        }

        .result-value {
            color: var(--ink);
            font-size: 1.3rem;
            font-weight: 850;
            line-height: 1.2;
        }

        .result-unit {
            color: var(--text-muted);
            font-size: 0.78rem;
            margin-top: 0.28rem;
        }

        .empty-state {
            border: 1px dashed #cbd5df;
            border-radius: 8px;
            padding: 1rem;
            color: var(--text-muted);
            background: rgba(255,255,255,0.7);
        }

        .auth-shell {
            max-width: 1080px;
            margin: 2rem auto 0;
        }

        .auth-card {
            border: 1px solid var(--line);
            border-radius: 8px;
            background: rgba(255,255,255,0.86);
            padding: 1rem;
        }

        .sidebar-brand {
            font-weight: 850;
            color: var(--ink);
            font-size: 1.05rem;
            margin-bottom: 0.25rem;
        }

        .sidebar-muted {
            color: var(--text-muted);
            font-size: 0.85rem;
        }

        @media (max-width: 760px) {
            .block-container {
                padding-left: 1rem;
                padding-right: 1rem;
            }

            .product-hero,
            .app-topbar,
            .hero-meta,
            .result-grid {
                grid-template-columns: 1fr;
            }

            .product-hero {
                padding: 1.25rem;
            }

            .app-topbar {
                display: grid;
                align-items: start;
            }

            .status-pill-row {
                justify-content: flex-start;
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


def render_product_hero() -> None:
    st.markdown(
        """
        <div class="product-hero">
            <div>
                <h1>상권 매출 예측 플랫폼</h1>
                <p>
                    업종별 원본 엑셀 계산식을 웹 계산 엔진으로 옮겨,
                    후보지의 예상 매출과 손익을 단계별로 검토합니다.
                </p>
                <div class="hero-meta">
                    <div class="hero-meta-item"><strong>3</strong><span>검증 완료 업종</span></div>
                    <div class="hero-meta-item"><strong>Exact</strong><span>엑셀 수식 대조</span></div>
                    <div class="hero-meta-item"><strong>SaaS</strong><span>회원/결제/저장</span></div>
                </div>
            </div>
            <div class="hero-panel">
                <div class="hero-panel-title">분석 흐름</div>
                <div class="hero-list">
                    <div>업종 선택 후 기본 조사 정보를 입력합니다.</div>
                    <div>배후세대, 통행량, 경쟁점 조건을 단계별로 채웁니다.</div>
                    <div>결제 또는 Admin 권한 확인 후 최종 결과를 확인합니다.</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_app_header() -> None:
    db_status = "Supabase 연결" if database_engine is not None else "DB 연결 필요"
    pay_status = current_user.get("payment_status", "unpaid")
    role = current_user.get("role", "User")
    st.markdown(
        f"""
        <div class="app-topbar">
            <div>
                <div class="app-title">상권 입지 평가</div>
                <div class="app-subtitle">업종별 엑셀 로직 기반 매출 예측과 손익 분석</div>
            </div>
            <div class="status-pill-row">
                <div class="status-pill good">{role}</div>
                <div class="status-pill">{pay_status}</div>
                <div class="status-pill">{db_status}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_section(kicker: str, title: str, copy: str = "") -> None:
    st.markdown(
        f"""
        <div class="section-kicker">{kicker}</div>
        <div class="section-title">{title}</div>
        <div class="section-copy">{copy}</div>
        """,
        unsafe_allow_html=True,
    )


def render_result_tiles(items: list[tuple[str, str, str]]) -> None:
    tiles = "".join(
        f"""
        <div class="result-tile">
            <div class="result-label">{label}</div>
            <div class="result-value">{value}</div>
            <div class="result-unit">{unit}</div>
        </div>
        """
        for label, value, unit in items
    )
    st.markdown(f'<div class="result-grid">{tiles}</div>', unsafe_allow_html=True)


def render_empty_state(message: str) -> None:
    st.markdown(f'<div class="empty-state">{message}</div>', unsafe_allow_html=True)


def render_auth_screen() -> None:
    st.markdown('<div class="auth-shell">', unsafe_allow_html=True)
    render_product_hero()
    if database_engine is None:
        st.error(f"데이터베이스 연결 실패: {database_error}")
        st.stop()

    st.markdown('<div class="auth-card">', unsafe_allow_html=True)
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
                except Exception as exc:
                    st.error(str(exc))
                else:
                    st.session_state["current_user"] = user
                    st.success(f"{user['role']} 권한으로 가입되었습니다.")
                    st.rerun()
    st.markdown("</div></div>", unsafe_allow_html=True)


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


def empty_competitor_row(extra_columns: list[str] | None = None) -> dict:
    row = {
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
    for column in extra_columns or []:
        row[column] = None
    return row


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
    schema = get_input_schema(industry_code)
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

    direct_rows = st.session_state.get(f"{industry_code}_direct_competitors", [empty_competitor_row(schema.competitor_extra_columns)])
    indirect_rows = st.session_state.get(f"{industry_code}_indirect_competitors", [empty_competitor_row(schema.competitor_extra_columns)])
    data.direct_competitors = rows_to_competitors(direct_rows)
    data.indirect_competitors = rows_to_competitors(indirect_rows)
    data.extra_inputs = {
        editor.key: rows_to_plain_records(
            st.session_state.get(f"{industry_code}_{editor.key}", [empty_editor_row(editor.columns)])
        )
        for editor in schema.market_editors
    }
    data.extra_inputs["direct_competitor_rows"] = rows_to_plain_records(direct_rows)
    data.extra_inputs["indirect_competitor_rows"] = rows_to_plain_records(indirect_rows)
    return data


def default_traffic_rows() -> list[dict]:
    return [{"시간": label, **{column: None for column in AGE_COLUMNS}} for label in TIME_LABELS]


def render_account_sidebar() -> None:
    with st.sidebar:
        st.markdown('<div class="sidebar-brand">UL-UMMA Sales</div>', unsafe_allow_html=True)
        st.markdown('<div class="sidebar-muted">상권 매출 예측 SaaS</div>', unsafe_allow_html=True)
        st.divider()
        st.subheader("계정")
        st.write(f"**{current_user['name']}님**")
        st.caption(f"권한: {current_user['role']}")
        st.caption(f"결제 상태: {current_user.get('payment_status', 'unpaid')}")
        if st.button("로그아웃"):
            st.session_state.pop("current_user", None)
            st.rerun()

        st.divider()
        st.subheader("저장소")
        if database_engine is None:
            st.error("DB 연결 실패")
        else:
            st.success("Supabase 연결")
        if is_admin:
            st.caption("Admin 계정은 전체 저장 기록을 조회할 수 있습니다.")
        else:
            st.caption("User 계정은 본인이 저장한 기록만 조회합니다.")


def render_step_1(industry_code: str | None) -> None:
    render_section("Step 01", "업종 선택 및 기본 정보", "분석할 업종과 후보점의 기본 조사 조건을 입력합니다.")
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
        render_empty_state("업종을 먼저 선택하면 해당 업종의 전용 계산 엔진과 입력 항목이 열립니다.")
        return
    if selected_industry.status != "ready":
        st.info(
            f"{selected_industry.name} 업종은 등록 예정입니다. "
            "해당 업종의 엑셀 파일을 분석해 전용 계산 모듈을 만든 뒤 활성화합니다."
        )
        return

    st.success(selected_industry.note)
    schema = get_input_schema(selected_industry.code)
    st.markdown(
        f"""
        <div class="status-pill-row" style="justify-content:flex-start;margin:0.4rem 0 1rem;">
            <div class="status-pill good">정확도: {schema.exact_status}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.caption(schema.exact_note)
    if not selected_industry.accuracy_status.startswith("exact_excel_match"):
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
    schema = get_input_schema(industry_code)
    render_section("Step 02", "배후 세대 및 통행량", "세대수, 인구, 평형/가격 분포, 시간대별 통행량을 입력합니다.")
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

    for editor in schema.market_editors:
        st.markdown(f"#### {editor.title}")
        if editor.help_text:
            st.caption(editor.help_text)
        st.data_editor(
            [empty_editor_row(editor.columns)],
            use_container_width=True,
            hide_index=True,
            num_rows="fixed",
            key=f"{industry_code}_{editor.key}",
        )

    st.markdown("#### 통행량 조사")
    st.data_editor(
        default_traffic_rows(),
        use_container_width=True,
        hide_index=True,
        num_rows="fixed",
        key=f"{industry_code}_traffic",
    )


def render_step_3(industry_code: str) -> None:
    schema = get_input_schema(industry_code)
    render_section("Step 03", "주변 경쟁점 정보", "후보점과 직접/간접 경쟁점의 입지 조건을 입력합니다.")
    st.caption("직접 경쟁점의 첫 번째 행은 후보점 정보로 입력하세요.")
    if schema.competitor_extra_columns:
        st.caption(f"이 업종은 추가 경쟁점 입력항목을 사용합니다: {', '.join(schema.competitor_extra_columns)}")
    st.markdown("#### 직접 경쟁점")
    st.data_editor(
        [empty_competitor_row(schema.competitor_extra_columns)],
        use_container_width=True,
        hide_index=True,
        num_rows="dynamic",
        key=f"{industry_code}_direct_competitors",
    )
    st.markdown("#### 간접 경쟁점")
    st.data_editor(
        [empty_competitor_row(schema.competitor_extra_columns)],
        use_container_width=True,
        hide_index=True,
        num_rows="dynamic",
        key=f"{industry_code}_indirect_competitors",
    )


def render_step_4(industry_code: str) -> None:
    render_section("Step 04", "투자금 및 비용", "임차 조건, 영업일수, 원가율, 로열티 등 손익 계산에 필요한 값을 입력합니다.")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.number_input("임차보증금(천원)", value=None, step=100.0, key=f"{industry_code}_deposit")
    with col2:
        st.number_input("영업권(천원)", value=None, step=100.0, key=f"{industry_code}_goodwill")
    with col3:
        st.number_input("월임대료(천원)", value=None, step=100.0, key=f"{industry_code}_monthly_rent")
    with col4:
        st.number_input("관리비(천원)", value=None, step=10.0, key=f"{industry_code}_management_fee")

    st.markdown("#### 투자손익 입력")
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
    render_section("Result", "결제 및 분석 결과", "입력값 검증 후 권한을 확인하고 최종 매출 예측 결과를 표시합니다.")
    process_portone_success(industry_code)
    data = build_base_input(industry_code)
    if st.button("분석 결과 보기", type="primary", key=f"{industry_code}_show_result"):
        st.session_state[f"{industry_code}_analysis_requested"] = True

    if not st.session_state.get(f"{industry_code}_analysis_requested", False):
        render_empty_state("입력값을 확인한 뒤 분석 결과 보기 버튼을 누르면 결과 확인 절차가 시작됩니다.")
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

    render_section("Forecast", "계산 결과", "원본 엑셀 계산 엔진으로 산출한 후보점 매출 예측입니다.")
    render_result_tiles(
        [
            ("예상 일매출액", f"{result['daily_sales_thousand']:,.2f}", "천원"),
            ("월간 평균 매출액", f"{result['monthly_sales_thousand']:,.2f}", "천원"),
            ("상권 유형", result["trade_area_label"], ""),
            ("1일 후보점 전면 통행량", f"{result['daily_traffic']:,.2f}", "명"),
        ]
    )

    render_section("Profit", "손익 요약", "월 매출에서 원가, 로열티, 임대료/관리비를 반영한 요약입니다.")
    render_result_tiles(
        [
            ("월 매출, VAT 제외", f"{result['monthly_sales_ex_vat_thousand']:,.2f}", "천원"),
            ("매출원가", f"{result['cogs_thousand']:,.2f}", "천원"),
            ("로열티", f"{result['royalty_thousand']:,.2f}", "천원"),
            ("공헌이익", f"{result['contribution_profit_thousand']:,.2f}", "천원"),
        ]
    )

    render_section("Breakdown", "계산 분해", "주요 가중치와 후보점 배분값을 확인합니다.")
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

    render_section("Save", "분석 결과 저장", "현재 입력값과 계산 결과를 계정 기록에 저장합니다.")
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


render_account_sidebar()
render_app_header()
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
