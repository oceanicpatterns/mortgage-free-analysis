from __future__ import annotations

import math
from dataclasses import asdict

import numpy as np
import pandas as pd

from .models import MortgageInputs, ScenarioRange, validate_inputs, validate_scenario_range


class MortgageAnalysisService:
    """Pure calculation service that can be reused in UI, API, or tests."""

    def monthly_payment(
        self, principal: float, annual_rate_percent: float, term_years: int
    ) -> float:
        r = annual_rate_percent / 100 / 12
        n = term_years * 12
        if principal <= 0 or n <= 0:
            return 0.0
        if r == 0:
            return principal / n
        return principal * (r * (1 + r) ** n) / ((1 + r) ** n - 1)

    def amortization_schedule(self, inputs: MortgageInputs) -> pd.DataFrame:
        checked = validate_inputs(inputs)
        balance = checked.loan_amount
        monthly_rate = checked.annual_rate_percent / 100 / 12
        standard_monthly = self.monthly_payment(
            checked.loan_amount, checked.annual_rate_percent, checked.term_years
        )

        rows: list[dict[str, float | int]] = []
        month = 0
        total_interest = 0.0
        total_principal = 0.0
        total_overpay = 0.0
        max_months = checked.term_years * 12

        while balance > 1e-8 and month < max_months + 1200:
            month += 1
            interest = balance * monthly_rate

            if monthly_rate == 0:
                principal_component = min(balance, standard_monthly)
            else:
                principal_component = min(balance, max(0.0, standard_monthly - interest))

            payment = principal_component + interest
            balance_after_payment = max(0.0, balance - principal_component)

            overpayment = 0.0
            if checked.annual_overpayment > 0 and month % 12 == 0 and balance_after_payment > 0:
                overpayment = min(checked.annual_overpayment, balance_after_payment)
                balance_after_payment -= overpayment

            total_interest += interest
            total_principal += principal_component
            total_overpay += overpayment

            rows.append(
                {
                    "Month": month,
                    "Year": math.ceil(month / 12),
                    "Starting Balance": balance,
                    "Payment": payment,
                    "Interest": interest,
                    "Principal": principal_component,
                    "Overpayment": overpayment,
                    "Ending Balance": balance_after_payment,
                    "Cumulative Interest": total_interest,
                    "Cumulative Principal": total_principal,
                    "Cumulative Overpayment": total_overpay,
                }
            )

            balance = balance_after_payment

            if month > max_months + 600 and abs(rows[-1]["Principal"]) < 1e-9:
                break

        return pd.DataFrame(rows)

    def summarize_schedule(self, schedule: pd.DataFrame, annual_costs: float) -> dict[str, float]:
        if schedule.empty:
            return {
                "months": 0.0,
                "years": 0.0,
                "total_interest": 0.0,
                "total_paid_to_bank": 0.0,
                "total_overpayment": 0.0,
                "all_in_housing_cost": 0.0,
            }

        months = float(schedule["Month"].max())
        total_interest = float(schedule["Interest"].sum())
        total_payment = float(schedule["Payment"].sum())
        total_overpayment = float(schedule["Overpayment"].sum())
        years = months / 12
        recurring_costs = annual_costs * years

        return {
            "months": months,
            "years": years,
            "total_interest": total_interest,
            "total_paid_to_bank": total_payment + total_overpayment,
            "total_overpayment": total_overpayment,
            "all_in_housing_cost": total_payment + total_overpayment + recurring_costs,
        }

    def annual_view(self, schedule: pd.DataFrame) -> pd.DataFrame:
        grouped = (
            schedule.groupby("Year", as_index=False)[
                ["Payment", "Interest", "Principal", "Overpayment"]
            ]
            .sum()
            .rename(
                columns={
                    "Payment": "Annual Payment",
                    "Interest": "Annual Interest",
                    "Principal": "Annual Principal",
                    "Overpayment": "Annual Overpayment",
                }
            )
        )
        ending_balance = schedule.groupby("Year", as_index=False)["Ending Balance"].last()
        return grouped.merge(ending_balance, on="Year", how="left")

    def scenario_result(
        self,
        base_inputs: MortgageInputs,
        rate: float,
        annual_overpayment: float,
    ) -> dict[str, float | pd.DataFrame]:
        scenario_inputs = validate_inputs(
            MortgageInputs(
                property_value=base_inputs.property_value,
                loan_amount=base_inputs.loan_amount,
                annual_rate_percent=rate,
                term_years=base_inputs.term_years,
                annual_insurance=base_inputs.annual_insurance,
                annual_ground_rent=base_inputs.annual_ground_rent,
                annual_overpayment=annual_overpayment,
            )
        )
        schedule = self.amortization_schedule(scenario_inputs)
        summary = self.summarize_schedule(
            schedule,
            annual_costs=scenario_inputs.annual_insurance + scenario_inputs.annual_ground_rent,
        )
        return {
            "rate": float(rate),
            "annual_overpayment": float(annual_overpayment),
            "monthly_payment": self.monthly_payment(
                scenario_inputs.loan_amount,
                scenario_inputs.annual_rate_percent,
                scenario_inputs.term_years,
            ),
            "years": summary["years"],
            "months": summary["months"],
            "interest": summary["total_interest"],
            "paid_to_bank": summary["total_paid_to_bank"],
            "all_in": summary["all_in_housing_cost"],
            "schedule": schedule,
        }

    def scenario_analysis(
        self,
        inputs: MortgageInputs,
        scenario_range: ScenarioRange,
    ) -> pd.DataFrame:
        checked = validate_inputs(inputs)
        rates = validate_scenario_range(scenario_range)

        values = np.round(np.arange(rates.low_rate, rates.high_rate + rates.step / 2, rates.step), 4)
        values = np.sort(values)

        rows: list[dict[str, float]] = []
        for rate in values:
            result = self.scenario_result(checked, float(rate), checked.annual_overpayment)
            rows.append(
                {
                    "Rate %": float(rate),
                    "Monthly Payment (before overpay)": result["monthly_payment"],
                    "Mortgage-Free in Years": result["years"],
                    "Mortgage-Free in Months": result["months"],
                    "Total Interest": result["interest"],
                    "Total Paid to Lender": result["paid_to_bank"],
                    "All-in Cost": result["all_in"],
                }
            )

        return pd.DataFrame(rows)

    def build_heatmap_data(
        self,
        inputs: MortgageInputs,
        scenario_range: ScenarioRange,
        annual_overpayment_options: list[float],
    ) -> pd.DataFrame:
        checked = validate_inputs(inputs)
        rates = validate_scenario_range(scenario_range)

        rate_values = np.round(
            np.arange(rates.low_rate, rates.high_rate + rates.step / 2, rates.step), 4
        )
        rows: list[dict[str, float]] = []

        for rate in rate_values:
            for overpay in annual_overpayment_options:
                result = self.scenario_result(checked, float(rate), float(overpay))
                rows.append(
                    {
                        "Rate %": float(rate),
                        "Annual Overpayment": float(overpay),
                        "Mortgage-Free in Years": float(result["years"]),
                        "Total Interest": float(result["interest"]),
                    }
                )
        return pd.DataFrame(rows)

    def serialize_inputs(self, inputs: MortgageInputs) -> dict[str, float | int]:
        checked = validate_inputs(inputs)
        data = asdict(checked)
        data["deposit"] = checked.deposit
        data["ltv_percent"] = checked.ltv_percent
        return data


def default_inputs() -> MortgageInputs:
    """Agnostic starter values that are intentionally generic."""

    return MortgageInputs(
        property_value=300000.0,
        loan_amount=240000.0,
        annual_rate_percent=5.0,
        term_years=30,
        annual_insurance=1200.0,
        annual_ground_rent=0.0,
        annual_overpayment=6000.0,
    )
