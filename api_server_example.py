from __future__ import annotations

from dataclasses import asdict

from fastapi import FastAPI
from pydantic import BaseModel

from calculation_engine import (
    CalculationInput,
    CommonMarketInput,
    CompetitorInput,
    InvestmentInput,
    get_calculator,
    list_industries,
)


app = FastAPI(title="Sales Forecast API")


class CompetitorPayload(BaseModel):
    name: str
    area: float = 0
    distance: float = 0
    location: float = 0
    visibility: float = 0
    accessibility: float = 0
    floor: float = 0
    sides: float = 0
    frontage: float = 0
    facility: float = 0
    parking: float = 0
    price: float = 0
    extra: dict = {}


class MarketPayload(BaseModel):
    store_name: str
    region: str
    admin_unit: str
    survey_month: int
    weekday: str
    apartment_households: float
    total_households: float
    resident_population: float
    worker_population: float
    annual_income: float
    traffic: list[list[float]]
    direct_competitors: list[CompetitorPayload] = []
    indirect_competitors: list[CompetitorPayload] = []


class InvestmentPayload(BaseModel):
    operation_type: str = "가맹점"
    deposit: float = 0
    goodwill: float = 0
    monthly_rent: float = 0
    management_fee: float = 0
    royalty_rate: float = 0
    business_days: float = 30
    cogs_rate: float = 0
    franchise_fee: float = 0
    education_fee: float = 0
    guarantee_deposit: float = 0
    opening_promo_fee: float = 0


class CalculationPayload(BaseModel):
    industry_code: str
    market: MarketPayload
    investment: InvestmentPayload
    industry_specific: dict = {}


@app.get("/industries")
def industries():
    return list_industries()


@app.post("/calculations")
def calculate(payload: CalculationPayload):
    market = CommonMarketInput(
        **payload.market.model_dump(exclude={"direct_competitors", "indirect_competitors"}),
        direct_competitors=[CompetitorInput(**item.model_dump()) for item in payload.market.direct_competitors],
        indirect_competitors=[CompetitorInput(**item.model_dump()) for item in payload.market.indirect_competitors],
    )
    data = CalculationInput(
        industry_code=payload.industry_code,
        market=market,
        investment=InvestmentInput(**payload.investment.model_dump()),
        industry_specific=payload.industry_specific,
    )
    result = get_calculator(payload.industry_code).calculate(data)
    return asdict(result)
