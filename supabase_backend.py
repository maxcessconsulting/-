from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime
from typing import Any


@dataclass
class SupabaseContext:
    client: Any


def init_supabase(secrets: Any) -> SupabaseContext:
    try:
        url = secrets["SUPABASE_URL"]
        key = secrets["SUPABASE_KEY"]
    except Exception as exc:
        raise RuntimeError(".streamlit/secrets.toml에 SUPABASE_URL과 SUPABASE_KEY를 설정해야 합니다.") from exc

    from supabase import create_client

    return SupabaseContext(client=create_client(url, key))


def get_admin_user_ids(secrets_obj: Any | None = None) -> set[str]:
    raw_value = None
    if secrets_obj is not None:
        try:
            raw_value = secrets_obj.get("ADMIN_EMAILS") or secrets_obj.get("ADMIN_USER_IDS")
        except Exception:
            raw_value = None
    raw_value = raw_value or "admin@example.com"
    return {item.strip().lower() for item in str(raw_value).split(",") if item.strip()}


def register_user(
    context: SupabaseContext,
    *,
    user_id: str,
    password: str,
    name: str,
    admin_user_ids: set[str] | None = None,
) -> dict:
    email = normalize_email(user_id)
    if len(password) < 6:
        raise ValueError("비밀번호는 6자 이상이어야 합니다.")
    if "@" not in email:
        raise ValueError("Supabase 로그인 아이디는 이메일 형식이어야 합니다.")

    try:
        response = context.client.auth.sign_up(
            {
                "email": email,
                "password": password,
                "options": {"data": {"name": name.strip() or email}},
            }
        )
    except Exception as exc:
        raise ValueError(_friendly_auth_error(exc)) from exc

    if response.user is None:
        raise ValueError("회원가입에 실패했습니다. Supabase 설정을 확인하세요.")
    if response.session is None:
        raise ValueError(
            "회원가입 요청은 완료됐지만 이메일 인증이 필요합니다. "
            "Supabase에서 발송한 인증 메일을 확인한 뒤 로그인하세요."
        )

    role = "Admin" if email.lower() in (admin_user_ids or get_admin_user_ids()) else "User"
    payment_status = "paid" if role == "Admin" else "unpaid"
    user = {
        "id": response.user.id,
        "user_id": response.user.id,
        "email": email,
        "name": name.strip() or email,
        "role": role,
        "payment_status": payment_status,
        "access_token": getattr(response.session, "access_token", None) if response.session else None,
        "refresh_token": getattr(response.session, "refresh_token", None) if response.session else None,
    }
    set_auth_session(context, response.session)
    upsert_profile(context, user)
    return user


def authenticate_user(context: SupabaseContext, *, user_id: str, password: str) -> dict | None:
    email = normalize_email(user_id)
    try:
        response = context.client.auth.sign_in_with_password({"email": email, "password": password})
    except Exception:
        return None
    if response.user is None or response.session is None:
        return None

    set_auth_session(context, response.session)
    profile = get_or_create_profile(context, response.user, response.session)
    return {
        "id": response.user.id,
        "user_id": response.user.id,
        "email": email,
        "name": profile.get("name") or response.user.user_metadata.get("name") or email,
        "role": profile.get("role") or "User",
        "payment_status": profile.get("payment_status") or "unpaid",
        "access_token": response.session.access_token,
        "refresh_token": response.session.refresh_token,
    }


def sign_out_user(context: SupabaseContext) -> None:
    try:
        context.client.auth.sign_out()
    except Exception:
        pass


def set_access_token(context: SupabaseContext, access_token: str | None) -> None:
    if not access_token:
        return
    try:
        context.client.postgrest.auth(access_token)
    except Exception:
        pass


def has_result_access(user: dict) -> bool:
    return user.get("role") == "Admin" or user.get("payment_status") == "paid"


def mark_user_paid(context: SupabaseContext, *, user_id: str, payment_data: dict | None = None) -> None:
    context.client.table("profiles").update({"payment_status": "paid"}).eq("id", user_id).execute()
    if payment_data:
        context.client.table("payment_records").insert(
            {
                "user_id": user_id,
                "merchant_uid": payment_data.get("merchant_uid"),
                "imp_uid": payment_data.get("imp_uid"),
                "amount": payment_data.get("amount"),
                "status": payment_data.get("status", "paid"),
                "raw_response": payment_data,
            }
        ).execute()


def save_analysis_result(
    context: SupabaseContext,
    *,
    user_key: str,
    industry_code: str,
    industry_name: str,
    input_data: Any,
    result: dict,
) -> str:
    payload = {
        "user_id": user_key,
        "industry_code": industry_code,
        "industry_name": industry_name,
        "store_name": str(result.get("store_name") or getattr(input_data, "store_name", "")),
        "daily_sales_thousand": float(result["daily_sales_thousand"]),
        "monthly_sales_thousand": float(result["monthly_sales_thousand"]),
        "contribution_profit_thousand": float(result["contribution_profit_thousand"]),
        "input_json": to_jsonable(input_data),
        "result_json": to_jsonable(result),
    }
    response = context.client.table("analysis_results").insert(payload).execute()
    data = response.data or []
    return str(data[0].get("id", "")) if data else ""


def list_analysis_results(context: SupabaseContext, *, user_key: str, limit: int = 20, include_all: bool = False) -> list[dict]:
    query = (
        context.client.table("analysis_results")
        .select("id,created_at,user_id,industry_name,store_name,daily_sales_thousand,monthly_sales_thousand,contribution_profit_thousand")
        .order("created_at", desc=True)
        .limit(limit)
    )
    if not include_all:
        query = query.eq("user_id", user_key)
    response = query.execute()
    rows = response.data or []
    return [
        {
            "id": row.get("id"),
            "created_at": row.get("created_at"),
            "user_key": row.get("user_id"),
            "industry_name": row.get("industry_name"),
            "store_name": row.get("store_name"),
            "daily_sales_thousand": row.get("daily_sales_thousand"),
            "monthly_sales_thousand": row.get("monthly_sales_thousand"),
            "contribution_profit_thousand": row.get("contribution_profit_thousand"),
        }
        for row in rows
    ]


def get_or_create_profile(context: SupabaseContext, auth_user: Any, session: Any) -> dict:
    response = context.client.table("profiles").select("*").eq("id", auth_user.id).limit(1).execute()
    if response.data:
        return response.data[0]
    profile = {
        "id": auth_user.id,
        "email": auth_user.email,
        "name": auth_user.user_metadata.get("name") or auth_user.email,
        "role": "User",
        "payment_status": "unpaid",
    }
    context.client.table("profiles").insert(profile).execute()
    return profile


def upsert_profile(context: SupabaseContext, user: dict) -> None:
    context.client.table("profiles").upsert(
        {
            "id": user["id"],
            "email": user["email"],
            "name": user["name"],
            "role": user["role"],
            "payment_status": user["payment_status"],
        }
    ).execute()


def set_auth_session(context: SupabaseContext, session: Any) -> None:
    try:
        context.client.postgrest.auth(session.access_token)
    except Exception:
        pass


def normalize_email(value: str) -> str:
    return str(value or "").strip().lower()


def _friendly_auth_error(exc: Exception) -> str:
    raw_message = str(exc).lower()
    if "already" in raw_message or "registered" in raw_message or "exists" in raw_message:
        return "이미 가입된 이메일입니다. 로그인하거나 다른 이메일을 사용하세요."
    if "password" in raw_message and ("weak" in raw_message or "short" in raw_message or "least" in raw_message):
        return "비밀번호가 Supabase 보안 기준을 충족하지 않습니다. 더 긴 비밀번호를 사용하세요."
    if "email" in raw_message and ("invalid" in raw_message or "not valid" in raw_message):
        return "이메일 형식이 올바르지 않습니다."
    if "signup" in raw_message and ("disabled" in raw_message or "not allowed" in raw_message):
        return "Supabase Auth 설정에서 이메일 회원가입이 비활성화되어 있습니다."
    if "rate" in raw_message or "too many" in raw_message:
        return "회원가입 요청이 너무 많습니다. 잠시 후 다시 시도하세요."
    if "confirm" in raw_message or "verification" in raw_message:
        return "이메일 인증이 필요합니다. 인증 메일을 확인한 뒤 로그인하세요."
    return (
        "Supabase 회원가입 처리 중 오류가 발생했습니다. "
        "SUPABASE_URL, SUPABASE_KEY, Auth 이메일 가입 설정을 확인하세요."
    )


def to_jsonable(value: Any) -> Any:
    if is_dataclass(value):
        return to_jsonable(asdict(value))
    if isinstance(value, dict):
        return {str(key): to_jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_jsonable(item) for item in value]
    if isinstance(value, datetime):
        return value.isoformat()
    if hasattr(value, "item"):
        return value.item()
    return value
