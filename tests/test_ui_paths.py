from __future__ import annotations

from streamlit.testing.v1 import AppTest


def test_main_app_renders_and_tabs_exist() -> None:
    at = AppTest.from_file("app.py")
    at.run(timeout=30)

    assert not at.exception

    expected_tabs = {"Dashboard", "Scenario Lab", "Compare Plans", "Cashflow Tables"}
    actual_tabs = {tab.label for tab in at.tabs}
    assert expected_tabs.issubset(actual_tabs)
    assert len(at.metric) >= 4


def test_novice_journey_updates_inputs_without_errors() -> None:
    at = AppTest.from_file("app.py")
    at.run(timeout=30)

    at.number_input(key="property_value").set_value(450000.0)
    at.number_input(key="loan_amount").set_value(300000.0)
    at.number_input(key="annual_rate").set_value(4.25)
    at.number_input(key="annual_overpayment").set_value(8000.0)
    at.run(timeout=30)

    assert not at.exception


def test_invalid_interest_shows_validation_error() -> None:
    at = AppTest.from_file("app.py")
    at.run(timeout=30)

    at.number_input(key="property_value").set_value(100000.0)
    at.number_input(key="loan_amount").set_value(200000.0)
    at.run(timeout=30)

    errors = [e.value for e in at.error]
    assert any("Input validation error" in msg for msg in errors)


def test_compare_plan_controls_and_heatmap_render() -> None:
    at = AppTest.from_file("app.py")
    at.run(timeout=30)

    assert at.number_input(key="rate_a").value is not None
    assert at.number_input(key="rate_b").value is not None
    assert at.number_input(key="overpay_a").value is not None
    assert at.number_input(key="overpay_b").value is not None

    # Scenario inputs must exist so users can run the full exploration flow.
    assert at.number_input(key="scenario_low").value is not None
    assert at.number_input(key="scenario_high").value is not None
