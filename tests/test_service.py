from __future__ import annotations

import pandas as pd
import pytest

from mortgage_free_analysis.models import MortgageInputs, ScenarioRange, validate_inputs, validate_scenario_range
from mortgage_free_analysis.service import MortgageAnalysisService, default_inputs


@pytest.fixture
def service() -> MortgageAnalysisService:
    return MortgageAnalysisService()


def test_default_inputs_are_generic() -> None:
    defaults = default_inputs()
    assert defaults.property_value == 300000.0
    assert defaults.loan_amount == 240000.0
    assert defaults.annual_rate_percent == 5.0


def test_validate_inputs_rejects_unrealistic_rate() -> None:
    with pytest.raises(ValueError, match="unrealistic"):
        validate_inputs(
            MortgageInputs(
                property_value=300000,
                loan_amount=240000,
                annual_rate_percent=35,
                term_years=30,
                annual_insurance=1200,
                annual_ground_rent=0,
                annual_overpayment=0,
            )
        )


def test_validate_scenario_range_normalizes_low_high() -> None:
    scenario = validate_scenario_range(ScenarioRange(low_rate=7, high_rate=3, step=0.5))
    assert scenario.low_rate == 3
    assert scenario.high_rate == 7


def test_monthly_payment_zero_rate(service: MortgageAnalysisService) -> None:
    payment = service.monthly_payment(principal=120000, annual_rate_percent=0.0, term_years=10)
    assert payment == pytest.approx(1000)


def test_amortization_schedule_finishes(service: MortgageAnalysisService) -> None:
    schedule = service.amortization_schedule(default_inputs())
    assert not schedule.empty
    assert schedule.iloc[-1]["Ending Balance"] == pytest.approx(0.0, abs=1e-4)


def test_annual_view_has_expected_columns(service: MortgageAnalysisService) -> None:
    schedule = service.amortization_schedule(default_inputs())
    annual = service.annual_view(schedule)
    assert set(annual.columns) == {
        "Year",
        "Annual Payment",
        "Annual Interest",
        "Annual Principal",
        "Annual Overpayment",
        "Ending Balance",
    }


def test_scenario_analysis_row_count(service: MortgageAnalysisService) -> None:
    df = service.scenario_analysis(default_inputs(), ScenarioRange(low_rate=3, high_rate=4, step=0.5))
    assert len(df) == 3
    assert "Total Interest" in df.columns


def test_heatmap_data_shape(service: MortgageAnalysisService) -> None:
    df = service.build_heatmap_data(
        default_inputs(),
        ScenarioRange(low_rate=3, high_rate=4, step=0.5),
        [0, 6000],
    )
    assert len(df) == 6
    assert df["Annual Overpayment"].isin([0, 6000]).all()


def test_summary_empty_schedule(service: MortgageAnalysisService) -> None:
    summary = service.summarize_schedule(pd.DataFrame(), annual_costs=100)
    assert summary["months"] == 0
    assert summary["all_in_housing_cost"] == 0
