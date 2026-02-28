from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from mortgage_free_analysis.models import MortgageInputs, ScenarioRange, validate_inputs
from mortgage_free_analysis.service import MortgageAnalysisService, default_inputs


st.set_page_config(
    page_title="Mortgage Planning Sandbox",
    layout="wide",
    initial_sidebar_state="expanded",
)

service = MortgageAnalysisService()
DEFAULT = default_inputs()
CURRENCY_SYMBOLS = {"USD": "$", "EUR": "EUR ", "GBP": "GBP "}


def money(value: float, currency_symbol: str) -> str:
    return f"{currency_symbol}{value:,.0f}"


def render_sidebar() -> tuple[MortgageInputs, ScenarioRange, list[float], bool, str]:
    with st.sidebar:
        currency_code = st.selectbox(
            "Display currency",
            options=["USD", "EUR", "GBP"],
            index=0,
            key="currency_code",
            help="Display formatting only. Calculations are currency-agnostic.",
        )

        st.header("1) Inputs")
        st.caption(
            "All values are local to your browser session. This app stores no personal data."
        )

        use_defaults = st.button("Reset to generic defaults", width="stretch")
        if use_defaults:
            st.session_state.clear()
            st.rerun()

        property_value = st.number_input(
            "Property value",
            min_value=0.0,
            max_value=50_000_000.0,
            value=DEFAULT.property_value,
            step=1_000.0,
            key="property_value",
        )
        loan_amount = st.number_input(
            "Loan amount",
            min_value=0.0,
            max_value=50_000_000.0,
            value=DEFAULT.loan_amount,
            step=1_000.0,
            key="loan_amount",
        )

        annual_rate = st.number_input(
            "Interest rate (% per year)",
            min_value=0.0,
            max_value=30.0,
            value=DEFAULT.annual_rate_percent,
            step=0.05,
            format="%.2f",
            key="annual_rate",
        )
        term_years = st.number_input(
            "Term (years)",
            min_value=1,
            max_value=50,
            value=DEFAULT.term_years,
            step=1,
            key="term_years",
        )

        annual_insurance = st.number_input(
            "Fixed annual cost of running the house",
            min_value=0.0,
            max_value=100_000.0,
            value=DEFAULT.annual_insurance,
            step=100.0,
            key="annual_insurance",
            help=(
                "This can include insurance, service charge, ground rent, "
                "fixed utilities, and other recurring annual housing costs."
            ),
        )
        annual_ground_rent = st.number_input(
            "Annual recurring property fee",
            min_value=0.0,
            max_value=100_000.0,
            value=DEFAULT.annual_ground_rent,
            step=50.0,
            key="annual_ground_rent",
            help="Use this for any recurring annual fee tied to the property.",
        )
        annual_overpayment = st.number_input(
            "Annual overpayment",
            min_value=0.0,
            max_value=5_000_000.0,
            value=DEFAULT.annual_overpayment,
            step=500.0,
            key="annual_overpayment",
            help="Applied once every 12th month in this model.",
        )

        st.markdown("---")
        st.header("2) Scenario Range")
        scenario_low = st.number_input(
            "Min scenario rate (%)",
            min_value=0.0,
            max_value=30.0,
            value=3.0,
            step=0.05,
            format="%.2f",
            key="scenario_low",
        )
        scenario_high = st.number_input(
            "Max scenario rate (%)",
            min_value=0.0,
            max_value=30.0,
            value=7.0,
            step=0.05,
            format="%.2f",
            key="scenario_high",
        )
        scenario_step = st.selectbox(
            "Scenario step (%)",
            options=[0.50, 0.25, 0.10, 0.05],
            index=1,
            key="scenario_step",
        )

        st.markdown("---")
        st.header("3) Heatmap Overpayment Levels")
        custom_overpay_levels = st.text_input(
            "Comma-separated annual overpayments",
            value="0, 3000, 6000, 12000, 18000",
            key="overpay_levels",
            help="Example: 0, 5000, 10000",
        )

        parsed_overpayments: list[float] = []
        for item in custom_overpay_levels.split(","):
            item = item.strip()
            if not item:
                continue
            try:
                parsed_overpayments.append(float(item))
            except ValueError:
                st.warning(f"Ignoring invalid overpayment value: {item}")

        if not parsed_overpayments:
            parsed_overpayments = [0.0, 3000.0, 6000.0]

        inputs = MortgageInputs(
            property_value=property_value,
            loan_amount=loan_amount,
            annual_rate_percent=annual_rate,
            term_years=int(term_years),
            annual_insurance=annual_insurance,
            annual_ground_rent=annual_ground_rent,
            annual_overpayment=annual_overpayment,
        )
        scenario = ScenarioRange(
            low_rate=scenario_low,
            high_rate=scenario_high,
            step=float(scenario_step),
        )

    return (
        inputs,
        scenario,
        parsed_overpayments,
        use_defaults,
        CURRENCY_SYMBOLS[currency_code],
    )


def kpi_row(
    inputs: MortgageInputs,
    summary: dict[str, float],
    baseline: dict[str, float],
    monthly_payment: float,
    currency_symbol: str,
) -> None:
    interest_saved = baseline["total_interest"] - summary["total_interest"]
    years_saved = baseline["years"] - summary["years"]
    deposit = max(0.0, inputs.property_value - inputs.loan_amount)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Monthly payment", money(monthly_payment, currency_symbol))
    c2.metric("Mortgage-free in", f"{summary['years']:.1f} years", f"{years_saved:.2f} years faster")
    c3.metric(
        "Total interest",
        money(summary["total_interest"], currency_symbol),
        f"{money(interest_saved, currency_symbol)} saved",
    )
    c4.metric(
        "Calculated deposit",
        money(deposit, currency_symbol),
        f"LTV {inputs.ltv_percent:.1f}%",
    )


def render_dashboard(inputs: MortgageInputs, schedule: pd.DataFrame, annual: pd.DataFrame) -> None:
    left, right = st.columns([1.35, 1.0])

    with left:
        chart_balance = px.line(
            schedule,
            x="Month",
            y="Ending Balance",
            title="Mortgage Balance Over Time",
            labels={"Ending Balance": "Balance"},
        )
        chart_balance.update_layout(height=380)
        st.plotly_chart(chart_balance, width="stretch")

        annual_melt = annual.melt(
            id_vars="Year",
            value_vars=["Annual Interest", "Annual Principal", "Annual Overpayment"],
            var_name="Component",
            value_name="Amount",
        )
        stacked = px.area(
            annual_melt,
            x="Year",
            y="Amount",
            color="Component",
            title="Yearly Cashflow Composition",
        )
        stacked.update_layout(height=360)
        st.plotly_chart(stacked, width="stretch")

    with right:
        total_principal = float(schedule["Principal"].sum())
        total_interest = float(schedule["Interest"].sum())
        total_overpaid = float(schedule["Overpayment"].sum())

        years = float(schedule["Month"].max()) / 12
        total_insurance = inputs.annual_insurance * years
        recurring_fee = inputs.annual_ground_rent * years

        sankey = go.Figure(
            data=[
                go.Sankey(
                    node={
                        "pad": 15,
                        "thickness": 16,
                        "label": [
                            "Total Outflow",
                            "Principal",
                            "Interest",
                            "Overpayment",
                            "Insurance",
                            "Recurring Fee",
                        ],
                    },
                    link={
                        "source": [0, 0, 0, 0, 0],
                        "target": [1, 2, 3, 4, 5],
                        "value": [
                            total_principal,
                            total_interest,
                            total_overpaid,
                            total_insurance,
                            recurring_fee,
                        ],
                    },
                )
            ]
        )
        sankey.update_layout(title_text="Where Your Money Goes", height=420)
        st.plotly_chart(sankey, width="stretch")

        yearly_balance = schedule.groupby("Year", as_index=False)["Ending Balance"].last()
        payoff = px.bar(
            yearly_balance,
            x="Year",
            y="Ending Balance",
            title="Remaining Balance by Year",
            labels={"Ending Balance": "Balance"},
        )
        payoff.update_layout(height=320)
        st.plotly_chart(payoff, width="stretch")


def render_scenario_lab(
    inputs: MortgageInputs,
    scenario: ScenarioRange,
    overpayment_levels: list[float],
    currency_symbol: str,
) -> None:
    st.subheader("Scenario Lab")
    st.caption(
        "Use this to test rate changes while keeping all other assumptions fixed."
    )

    scenarios = service.scenario_analysis(inputs, scenario)
    currency_fmt = f"{currency_symbol}" + "{:,.0f}"
    st.dataframe(
        scenarios.style.format(
            {
                "Rate %": "{:.2f}",
                "Monthly Payment (before overpay)": currency_fmt,
                "Mortgage-Free in Years": "{:.2f}",
                "Mortgage-Free in Months": "{:,.0f}",
                "Total Interest": currency_fmt,
                "Total Paid to Lender": currency_fmt,
                "All-in Cost": currency_fmt,
            }
        ),
        width="stretch",
        hide_index=True,
    )

    p1, p2 = st.columns(2)
    with p1:
        chart_interest = px.line(
            scenarios,
            x="Rate %",
            y="Total Interest",
            markers=True,
            title="Total Interest vs Rate",
        )
        chart_interest.update_layout(height=350)
        st.plotly_chart(chart_interest, width="stretch")

    with p2:
        chart_years = px.line(
            scenarios,
            x="Rate %",
            y="Mortgage-Free in Years",
            markers=True,
            title="Payoff Time vs Rate",
        )
        chart_years.update_layout(height=350)
        st.plotly_chart(chart_years, width="stretch")

    st.markdown("### Overpayment + Rate Grid")
    heatmap_df = service.build_heatmap_data(inputs, scenario, overpayment_levels)
    heatmap_table = heatmap_df.pivot(
        index="Annual Overpayment", columns="Rate %", values="Mortgage-Free in Years"
    )

    heatmap = px.imshow(
        heatmap_table,
        labels={"x": "Rate %", "y": "Annual Overpayment", "color": "Years"},
        text_auto=True,
        title="Mortgage-Free Years Heatmap",
        aspect="auto",
    )
    heatmap.update_traces(texttemplate="%{z:.1f}")
    heatmap.update_layout(height=420)
    st.plotly_chart(heatmap, width="stretch")


def render_plan_comparison(inputs: MortgageInputs, currency_symbol: str) -> None:
    st.subheader("Compare Two Plans")
    st.caption("Plan A and Plan B apply to the same principal and term.")

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Plan A**")
        rate_a = st.number_input(
            "Rate A (%)",
            min_value=0.0,
            max_value=30.0,
            value=inputs.annual_rate_percent,
            step=0.05,
            format="%.2f",
            key="rate_a",
        )
        overpay_a = st.number_input(
            "Annual overpayment A",
            min_value=0.0,
            max_value=5_000_000.0,
            value=inputs.annual_overpayment,
            step=500.0,
            key="overpay_a",
        )

    with c2:
        st.markdown("**Plan B**")
        rate_b = st.number_input(
            "Rate B (%)",
            min_value=0.0,
            max_value=30.0,
            value=max(0.0, inputs.annual_rate_percent - 1),
            step=0.05,
            format="%.2f",
            key="rate_b",
        )
        overpay_b = st.number_input(
            "Annual overpayment B",
            min_value=0.0,
            max_value=5_000_000.0,
            value=inputs.annual_overpayment,
            step=500.0,
            key="overpay_b",
        )

    plan_a = service.scenario_result(inputs, rate=float(rate_a), annual_overpayment=float(overpay_a))
    plan_b = service.scenario_result(inputs, rate=float(rate_b), annual_overpayment=float(overpay_b))

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("A: Mortgage-free", f"{plan_a['years']:.2f} yrs")
    m2.metric("B: Mortgage-free", f"{plan_b['years']:.2f} yrs", f"{plan_a['years'] - plan_b['years']:+.2f} yrs")
    m3.metric("A: Total interest", money(float(plan_a["interest"]), currency_symbol))
    interest_delta = float(plan_a["interest"]) - float(plan_b["interest"])
    delta_sign = "+" if interest_delta >= 0 else "-"
    m4.metric(
        "B: Total interest",
        money(float(plan_b["interest"]), currency_symbol),
        f"{delta_sign}{money(abs(interest_delta), currency_symbol)}",
    )

    compare_df = pd.DataFrame(
        {
            "Metric": [
                "Monthly Payment",
                "Mortgage-Free Years",
                "Total Interest",
                "Total Paid to Lender",
                "All-in Cost",
            ],
            "Plan A": [
                float(plan_a["monthly_payment"]),
                float(plan_a["years"]),
                float(plan_a["interest"]),
                float(plan_a["paid_to_bank"]),
                float(plan_a["all_in"]),
            ],
            "Plan B": [
                float(plan_b["monthly_payment"]),
                float(plan_b["years"]),
                float(plan_b["interest"]),
                float(plan_b["paid_to_bank"]),
                float(plan_b["all_in"]),
            ],
        }
    )
    compare_df["Difference (A-B)"] = compare_df["Plan A"] - compare_df["Plan B"]

    compare_display = compare_df.copy()
    currency_metrics = {
        "Monthly Payment",
        "Total Interest",
        "Total Paid to Lender",
        "All-in Cost",
    }
    for col in ["Plan A", "Plan B", "Difference (A-B)"]:
        compare_display[col] = compare_display.apply(
            lambda row: (
                money(float(row[col]), currency_symbol)
                if row["Metric"] in currency_metrics
                else f"{float(row[col]):.2f}"
            ),
            axis=1,
        )

    st.dataframe(compare_display, width="stretch", hide_index=True)


def render_cashflow(
    schedule: pd.DataFrame,
    annual: pd.DataFrame,
    currency_symbol: str,
) -> None:
    st.subheader("Cashflow Tables")
    left, right = st.columns([1.2, 1.0])

    with left:
        st.markdown("**Year-by-Year Breakdown**")
        currency_fmt = f"{currency_symbol}" + "{:,.0f}"
        st.dataframe(
            annual.style.format(
                {
                    "Annual Payment": currency_fmt,
                    "Annual Interest": currency_fmt,
                    "Annual Principal": currency_fmt,
                    "Annual Overpayment": currency_fmt,
                    "Ending Balance": currency_fmt,
                }
            ),
            width="stretch",
            hide_index=True,
        )

    with right:
        st.markdown("**First 24 Months**")
        st.dataframe(
            schedule.head(24)[
                [
                    "Month",
                    "Payment",
                    "Interest",
                    "Principal",
                    "Overpayment",
                    "Ending Balance",
                ]
            ].style.format(
                {
                    "Payment": currency_fmt,
                    "Interest": currency_fmt,
                    "Principal": currency_fmt,
                    "Overpayment": currency_fmt,
                    "Ending Balance": currency_fmt,
                }
            ),
            width="stretch",
            hide_index=True,
        )

    annual_csv = annual.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="Download annual cashflow CSV",
        data=annual_csv,
        file_name="annual_cashflow.csv",
        mime="text/csv",
        help="Exports only generated scenario data, never browser/session metadata.",
    )


st.title("Mortgage Planning Sandbox")
st.caption(
    "A generic, privacy-safe mortgage planner with scenario analysis. Not financial advice."
)

st.info(
    "Quick start: (1) Enter your numbers in the sidebar, (2) read KPI cards, (3) open Scenario Lab and Compare Plans. "
    "Defaults are intentionally generic and not based on any personal profile."
)

st.markdown(
    "**Model assumptions:** fixed interest rate for each scenario across the full term; annual overpayment is applied once every 12th month."
)

inputs, scenario, overpayment_levels, _, currency_symbol = render_sidebar()

try:
    inputs = validate_inputs(inputs)
    scenario = ScenarioRange(
        low_rate=min(scenario.low_rate, scenario.high_rate),
        high_rate=max(scenario.low_rate, scenario.high_rate),
        step=scenario.step,
    )

    schedule = service.amortization_schedule(inputs)
    summary = service.summarize_schedule(
        schedule,
        annual_costs=inputs.annual_insurance + inputs.annual_ground_rent,
    )

    no_overpay_inputs = MortgageInputs(
        property_value=inputs.property_value,
        loan_amount=inputs.loan_amount,
        annual_rate_percent=inputs.annual_rate_percent,
        term_years=inputs.term_years,
        annual_insurance=inputs.annual_insurance,
        annual_ground_rent=inputs.annual_ground_rent,
        annual_overpayment=0.0,
    )
    baseline_schedule = service.amortization_schedule(no_overpay_inputs)
    baseline_summary = service.summarize_schedule(
        baseline_schedule,
        annual_costs=inputs.annual_insurance + inputs.annual_ground_rent,
    )
    monthly_base = service.monthly_payment(
        inputs.loan_amount, inputs.annual_rate_percent, inputs.term_years
    )

    if inputs.loan_amount > inputs.property_value:
        st.warning(
            "Loan amount is higher than property value. This can still be modeled, "
            "but double-check the input context."
        )

    kpi_row(inputs, summary, baseline_summary, monthly_base, currency_symbol)
    annual = service.annual_view(schedule)

    tab1, tab2, tab3, tab4 = st.tabs(
        ["Dashboard", "Scenario Lab", "Compare Plans", "Cashflow Tables"]
    )

    with tab1:
        render_dashboard(inputs, schedule, annual)

    with tab2:
        render_scenario_lab(inputs, scenario, overpayment_levels, currency_symbol)

    with tab3:
        render_plan_comparison(inputs, currency_symbol)

    with tab4:
        render_cashflow(schedule, annual, currency_symbol)

except ValueError as exc:
    st.error(f"Input validation error: {exc}")
    st.stop()
