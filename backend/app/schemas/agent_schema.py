
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, Field


class AgentTripRequest(BaseModel):
    origin: str = Field(min_length=2, max_length=150)
    destination: str = Field(min_length=2, max_length=150)

    start_date: str
    end_date: str

    travelers: int = Field(ge=1, le=50)
    budget: Decimal = Field(gt=0)
    currency: str = Field(default="USD", pattern=r"^[A-Z]{3}$")

    preferences: dict[str, Any] = Field(default_factory=dict)


class BudgetAllocation(BaseModel):
    flights: Decimal = Field(ge=0)
    hotels: Decimal = Field(ge=0)
    food: Decimal = Field(ge=0)
    activities: Decimal = Field(ge=0)
    transportation: Decimal = Field(ge=0)
    emergency: Decimal = Field(ge=0)


class BudgetAnalysis(BaseModel):
    total_budget: Decimal
    estimated_total: Decimal
    remaining_budget: Decimal
    is_within_budget: bool
    allocation: BudgetAllocation
    warnings: list[str] = Field(default_factory=list)


class AgentResult(BaseModel):
    agent_name: Literal[
        "flight",
        "hotel",
        "places",
        "budget",
        "orchestrator",
    ]

    status: Literal["success", "failed", "skipped"]
    data: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None
