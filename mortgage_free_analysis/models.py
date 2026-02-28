from __future__ import annotations

from dataclasses import dataclass
import math


@dataclass(frozen=True)
class MortgageInputs:
    property_value: float
    loan_amount: float
    annual_rate_percent: float
    term_years: int
    annual_insurance: float
    annual_ground_rent: float
    annual_overpayment: float

    @property
    def deposit(self) -> float:
        return max(0.0, self.property_value - self.loan_amount)

    @property
    def ltv_percent(self) -> float:
        if self.property_value <= 0:
            return 0.0
        return (self.loan_amount / self.property_value) * 100


@dataclass(frozen=True)
class ScenarioRange:
    low_rate: float
    high_rate: float
    step: float


def ensure_finite_non_negative(value: float, label: str) -> float:
    if not math.isfinite(value):
        raise ValueError(f"{label} must be finite.")
    if value < 0:
        raise ValueError(f"{label} cannot be negative.")
    return float(value)


def validate_inputs(inputs: MortgageInputs) -> MortgageInputs:
    property_value = ensure_finite_non_negative(inputs.property_value, "Property value")
    loan_amount = ensure_finite_non_negative(inputs.loan_amount, "Loan amount")
    annual_rate_percent = ensure_finite_non_negative(
        inputs.annual_rate_percent, "Annual rate"
    )
    annual_insurance = ensure_finite_non_negative(
        inputs.annual_insurance, "Annual insurance"
    )
    annual_ground_rent = ensure_finite_non_negative(
        inputs.annual_ground_rent, "Annual recurring property fee"
    )
    annual_overpayment = ensure_finite_non_negative(
        inputs.annual_overpayment, "Annual overpayment"
    )

    if inputs.term_years < 1 or inputs.term_years > 50:
        raise ValueError("Term must be between 1 and 50 years.")
    if annual_rate_percent > 30:
        raise ValueError("Annual rate appears unrealistic (>30%).")
    if property_value > 0 and loan_amount > property_value * 1.5:
        raise ValueError(
            "Loan amount is too high relative to property value. Check your numbers."
        )

    return MortgageInputs(
        property_value=property_value,
        loan_amount=loan_amount,
        annual_rate_percent=annual_rate_percent,
        term_years=int(inputs.term_years),
        annual_insurance=annual_insurance,
        annual_ground_rent=annual_ground_rent,
        annual_overpayment=annual_overpayment,
    )


def validate_scenario_range(scenario: ScenarioRange) -> ScenarioRange:
    low_rate = ensure_finite_non_negative(scenario.low_rate, "Minimum scenario rate")
    high_rate = ensure_finite_non_negative(scenario.high_rate, "Maximum scenario rate")
    step = ensure_finite_non_negative(scenario.step, "Scenario step")

    if step <= 0:
        raise ValueError("Scenario step must be greater than zero.")

    low, high = min(low_rate, high_rate), max(low_rate, high_rate)

    if high > 30:
        raise ValueError("Scenario rates above 30% are not allowed.")
    if (high - low) / step > 300:
        raise ValueError(
            "Scenario grid is too large; reduce the range or increase step size."
        )

    return ScenarioRange(low_rate=low, high_rate=high, step=step)
