from __future__ import annotations

import json
import os
from typing import Any

import gradio as gr
import pandas as pd

from paymind import PayMind
from paymind.runtime import (
    APP_CHANNEL_OPTIONS,
    COUNTRY_OPTIONS,
    DEFAULT_DEMO_ROUTES,
    ROUTE_OPTIONS,
    normalize_transaction_context,
)


PAYMIND = PayMind()
MODEL_SUMMARY = PAYMIND.models()
REFERENCE_DISCLAIMER = MODEL_SUMMARY.disclaimer

COUNTRY_TO_CURRENCY = {
    code: normalize_transaction_context({"country": code, "currency": ""})["local_currency"]
    for _, code in COUNTRY_OPTIONS
}
COUNTRY_LABELS = {code: label for label, code in COUNTRY_OPTIONS}
ROUTE_LABELS = {value: label for label, value in ROUTE_OPTIONS}
APP_LABELS = {value: label for label, value in APP_CHANNEL_OPTIONS}

REASON_COPY = {
    "HIGH_SUCCESS_PROBABILITY": "Strong predicted reliability",
    "FAST_EXPECTED_SETTLEMENT": "Fast expected settlement",
    "LOWEST_OR_COMPETITIVE_FEE": "Competitive estimated cost",
    "HIGH_CANDIDATE_RELEVANCE": "Strong fit for this transaction",
    "BEST_AVAILABLE_COMBINED_SCORE": "Best overall route for this setup",
}



CUSTOM_CSS = """
html {
    overflow-y: scroll;
    scrollbar-gutter: stable;
}

body {
    min-height: 100vh;
}
.gradio-container {
    max-width: 1350px !important;
    margin: 0 auto !important;
    padding: 24px !important;

    font-family:
        Inter,
        ui-sans-serif,
        system-ui,
        -apple-system,
        BlinkMacSystemFont,
        "Segoe UI",
        Arial,
        sans-serif !important;

    --primary-50: #EEF2FF;
    --primary-100: #E0E7FF;
    --primary-200: #C7D2FE;
    --primary-300: #A5B4FC;
    --primary-400: #818CF8;
    --primary-500: #6366F1;
    --primary-600: #4F46E5;
    --primary-700: #4338CA;
    --primary-800: #3730A3;
    --primary-900: #312E81;
    --primary-950: #1E1B4B;
}

.gradio-container * {
    font-family: inherit !important;
}

.pm-header {
    margin-bottom: 18px;
}

.pm-title {
    font-size: 30px;
    font-weight: 700;
    margin-bottom: 4px;
}

.pm-subtitle {
    color: #667085;
    font-size: 14px;
    line-height: 1.5;
    max-width: 850px;
}

.pm-note {
    color: #98A2B3;
    font-size: 12px;
    margin-top: 8px;
}

.pm-section-title {
    font-size: 18px;
    font-weight: 600;
    margin-bottom: 4px;
}

.pm-muted {
    color: #667085;
    font-size: 13px;
    line-height: 1.5;
}

.pm-result {
    min-height: 260px;
}

.pm-empty-state {
    min-height: 260px;
    display: flex;
    align-items: center;
    justify-content: center;
    text-align: center;
}

.pm-empty-content {
    max-width: 560px;
    padding: 20px;
}

.pm-empty-title {
    font-size: 22px;
    font-weight: 600;
    margin-bottom: 8px;
}

.pm-empty-copy {
    color: #667085;
    font-size: 13px;
    line-height: 1.55;
}

.pm-hero {
    padding: 6px 0;
}

.pm-hero-top {
    display: flex;
    justify-content: space-between;
    gap: 18px;
    align-items: flex-start;
}

.pm-kicker {
    color: #667085;
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: .06em;
}

.pm-route-name {
    font-size: 28px;
    font-weight: 700;
    margin-top: 4px;
}

.pm-route-subcopy {
    color: #667085;
    font-size: 13px;
    margin-top: 4px;
}

.pm-score {
    font-size: 36px;
    font-weight: 700;
    text-align: right;
    color: #4F46E5;
}

.pm-score small {
    display: block;
    font-size: 11px;
    font-weight: 500;
    color: #667085;
}

.pm-metric-strip {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 12px;
    margin-top: 18px;
}

.pm-metric-item {
    padding: 12px 0;
}

.pm-metric-label {
    color: #667085;
    font-size: 11px;
}

.pm-metric-value {
    font-size: 18px;
    font-weight: 600;
    margin-top: 3px;
}

.pm-hero-reasons {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    margin-top: 10px;
}

.pm-hero-reason {
    font-size: 12px;
    color: #475467;
}

.pm-reasons-list {
    display: grid;
    gap: 8px;
    margin-top: 10px;
}

.pm-reason-row {
    display: flex;
    gap: 8px;
    align-items: flex-start;
    font-size: 13px;
}

.pm-reason-mark {
    font-weight: 700;
}

.pm-bars {
    display: grid;
    gap: 10px;
    margin-top: 12px;
}

.pm-bar-row {
    display: grid;
    grid-template-columns: 110px 1fr 48px;
    gap: 10px;
    align-items: center;
}

.pm-bar-label,
.pm-bar-value {
    font-size: 12px;
}

.pm-bar-track {
    height: 7px;
    border-radius: 999px;
    background: rgba(127,127,127,.18);
    overflow: hidden;
}

.pm-bar-fill {
    height: 100%;
    border-radius: 999px;
    background: #4F46E5;
}

.pm-route-rows {
    margin-top: 12px;
}

.pm-route-row {
    display: grid;
    grid-template-columns: 42px 1.2fr 70px repeat(3, minmax(0, 1fr));
    gap: 10px;
    align-items: center;
    padding: 11px 0;
    border-bottom: 1px solid rgba(127,127,127,.18);
}

.pm-route-rank {
    font-size: 12px;
    font-weight: 700;
}

.pm-route-provider {
    font-size: 14px;
    font-weight: 600;
}

.pm-route-meta-label {
    color: #667085;
    font-size: 10px;
}

.pm-route-meta-value {
    font-size: 12px;
    font-weight: 600;
    margin-top: 2px;
}

.pm-model-grid {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 12px;
    width: 100%;
    margin-top: 16px;
}

.pm-model-item {
    padding: 14px;
    border: 1px solid rgba(127,127,127,.18);
    border-radius: 10px;
}

.pm-model-title {
    font-size: 16px;
    font-weight: 600;
}

.pm-model-subcopy {
    color: #667085;
    font-size: 12px;
    margin-top: 3px;
}

.pm-model-stats {
    display: grid;
    gap: 5px;
    margin-top: 10px;
}

.pm-model-stat {
    display: flex;
    justify-content: space-between;
    gap: 12px;
    font-size: 12px;
}

.pm-pipeline-row {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 10px;
    width: 100%;
    margin: 14px 0 0 0;
    align-items: stretch;
}

.pm-node {
    padding: 10px 8px;
    border: 1px solid rgba(127,127,127,.18);
    border-radius: 8px;
    text-align: center;
    font-size: 12px;
    font-weight: 600;
}

.pm-train-steps {
    display: grid;
    gap: 8px;
    margin-top: 12px;
}

.pm-train-step {
    display: grid;
    grid-template-columns: 36px 1fr;
    gap: 10px;
    align-items: center;
}

.pm-step-index {
    font-weight: 700;
    color: #4F46E5;
}

.pm-code-block {
    margin-top: 14px;
    padding: 12px;
    border-radius: 8px;
    overflow: auto;
}

.pm-primary button {
    min-height: 46px !important;
    font-weight: 600 !important;
    background: #4F46E5 !important;
    border-color: #4F46E5 !important;
}

.pm-primary button:hover {
    background: #4338CA !important;
    border-color: #4338CA !important;
}

@media (max-width: 900px) {
    .pm-metric-strip,
    .pm-model-grid,
    .pm-pipeline-row {
        grid-template-columns: 1fr 1fr;
    }

    .pm-route-row {
        grid-template-columns: 36px 1fr 60px;
    }

    .pm-route-row .pm-route-meta:nth-of-type(n+4) {
        display: none;
    }
}


.pm-info-wrap {
    width: 100%;
    max-width: none;
    margin: 0;
    padding: 0;
    text-align: left;
}

.pm-info-wrap h2 {
    margin: 0 0 8px 0;
    font-size: 24px;
    font-weight: 650;
}

.pm-info-wrap h3 {
    text-align: left;
}

.pm-info-lead {
    max-width: 900px;
    color: #667085;
    font-size: 13px;
    line-height: 1.6;
    margin-bottom: 18px;
}

.pm-info-section {
    margin-top: 22px;
}

.pm-info-section h3 {
    margin: 0 0 8px 0;
    font-size: 16px;
    font-weight: 600;
}

.pm-info-section p {
    color: #667085;
    font-size: 13px;
    line-height: 1.6;
    margin: 6px 0;
}

.pm-training-grid {
    display: grid;
    grid-template-columns: repeat(5, minmax(0, 1fr));
    gap: 10px;
    margin-top: 14px;
}

.pm-training-card {
    border: 1px solid rgba(127,127,127,.18);
    border-radius: 10px;
    padding: 12px;
}

.pm-training-card strong {
    display: block;
    margin-bottom: 4px;
    font-size: 13px;
}

.pm-training-card span {
    color: #667085;
    font-size: 12px;
    line-height: 1.45;
}

.pm-schema-list {
    margin: 10px 0 0 18px;
    padding: 0;
    color: #475467;
    font-size: 13px;
    line-height: 1.7;
}

.pm-command-block {
    margin-top: 10px;
    padding: 12px 14px;
    border-radius: 8px;
    background: rgba(127,127,127,.08);
    overflow-x: auto;
    font-size: 12px;
}

.pm-callout {
    margin-top: 14px;
    padding: 12px 14px;
    border-left: 3px solid #4F46E5;
    background: rgba(99,102,241,.06);
    border-radius: 6px;
    color: #475467;
    font-size: 12px;
    line-height: 1.6;
}

.pm-kv {
    display: grid;
    grid-template-columns: 180px 1fr;
    gap: 6px 14px;
    margin-top: 12px;
    font-size: 12px;
}

.pm-kv div:nth-child(odd) {
    color: #667085;
}

.pm-kv div:nth-child(even) {
    color: #344054;
    font-weight: 500;
}

@media (max-width: 1050px) {
    .pm-model-grid {
        grid-template-columns: repeat(2, minmax(0, 1fr));
    }

    .pm-training-grid {
        grid-template-columns: repeat(2, minmax(0, 1fr));
    }
}

@media (max-width: 700px) {
    .pm-model-grid,
    .pm-training-grid {
        grid-template-columns: 1fr;
    }

    .pm-kv {
        grid-template-columns: 1fr;
    }
}

@media (max-width: 700px) {
    .gradio-container {
        padding: 14px !important;
    }

    .pm-hero-top {
        flex-direction: column;
    }

    .pm-score {
        text-align: left;
    }

    .pm-metric-strip,
    .pm-model-grid,
    .pm-pipeline-row,
    .pm-bar-row {
        grid-template-columns: 1fr;
    }
}
"""



def format_percent(value: float) -> str:
    return f"{value * 100:.0f}%"


def format_score(value: float) -> str:
    return f"{value * 100:.0f}"


def format_fee(value: float, currency: str) -> str:
    return f"{currency.upper()} {value:,.2f}"


def format_duration(minutes: float) -> str:
    seconds = max(float(minutes), 0.0) * 60.0
    if seconds < 1:
        return "< 1 sec"
    if seconds < 60:
        return f"{seconds:.0f} sec"
    if seconds < 3600:
        return f"{seconds / 60:.1f} min"
    if seconds < 86400:
        return f"{seconds / 3600:.1f} hr"
    return f"{seconds / 86400:.1f} days"


def format_reason(reason: str) -> str:
    return REASON_COPY.get(reason, reason.replace("_", " ").title())


def route_display_name(route: str) -> str:
    return ROUTE_LABELS.get(route, route.replace("_", " ").title())


def build_demo_request(
    *,
    transaction_type: str,
    amount: float,
    currency: str,
    country: str,
    ip_country: str,
    app_type: str,
    available_routes: list[str],
    cross_border_override: str,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "transaction_type": transaction_type,
        "amount": float(amount),
        "currency": currency,
        "country": country,
        "ip_country": ip_country,
        "app_type": app_type,
        "available_payment_routes": available_routes,
    }
    if cross_border_override == "force_local":
        payload["is_cross_border"] = 0
    elif cross_border_override == "force_cross_border":
        payload["is_cross_border"] = 1
    return normalize_transaction_context(payload)


def build_comparison_frame(
    recommendations: list[dict[str, Any]],
    currency: str,
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for row in recommendations:
        rows.append(
            {
                "Rank": row["rank"],
                "Route": route_display_name(str(row["payment_method"])),
                "Score": format_score(float(row["final_score"])),
                "Success": format_percent(float(row["success_probability"])),
                "P50": format_duration(float(row["arrival_p50_minutes"])),
                "P90": format_duration(float(row["arrival_p90_minutes"])),
                "Fee": format_fee(float(row["estimated_fee"]), currency),
                "Fee Rate": format_percent(float(row["effective_fee_rate"])),
            }
        )
    return pd.DataFrame(rows)


def build_empty_state() -> str:
    return """
    <div class="pm-empty-state">
      <div class="pm-empty-content">
        <div class="pm-empty-title">Configure a transaction to see the recommendation</div>
        <div class="pm-empty-copy">
          PayMind will compare the selected routes using candidate fit, predicted reliability,
          settlement expectations and estimated cost.
        </div>
      </div>
    </div>
    """


def build_hero(route: dict[str, Any], request: dict[str, Any]) -> str:
    return f"""
    <div class="pm-hero">
      <div class="pm-hero-top">
        <div>
          <div class="pm-kicker">Recommended route</div>
          <div class="pm-route-name">#{route["rank"]} {route_display_name(str(route["payment_method"]))}</div>
          <div class="pm-route-subcopy">
            {COUNTRY_LABELS.get(str(request["country"]), request["country"])} ·
            {APP_LABELS.get(str(request["app_type"]), request["app_type"])} ·
            {request["transaction_type"].title()}
          </div>
          <div class="pm-hero-reasons">
            {''.join(f'<span class="pm-hero-reason">{format_reason(reason)}</span>' for reason in route["reasons"][:3])}
          </div>
        </div>
        <div class="pm-score">
          {format_score(float(route["final_score"]))}
          <small>Final score / 100</small>
        </div>
      </div>
      <div class="pm-metric-strip">
        <div class="pm-metric-item">
          <div class="pm-metric-label">Success</div>
          <div class="pm-metric-value">{format_percent(float(route["success_probability"]))}</div>
        </div>
        <div class="pm-metric-item">
          <div class="pm-metric-label">P50 arrival</div>
          <div class="pm-metric-value">{format_duration(float(route["arrival_p50_minutes"]))}</div>
        </div>
        <div class="pm-metric-item">
          <div class="pm-metric-label">P90 arrival</div>
          <div class="pm-metric-value">{format_duration(float(route["arrival_p90_minutes"]))}</div>
        </div>
        <div class="pm-metric-item">
          <div class="pm-metric-label">Est. fee</div>
          <div class="pm-metric-value">{format_fee(float(route["estimated_fee"]), str(request["currency"]))}</div>
        </div>
      </div>
    </div>
    """


def build_reasons(route: dict[str, Any]) -> str:
    rows = "".join(
        f'<div class="pm-reason-row"><span class="pm-reason-mark">✓</span><span>{format_reason(reason)}</span></div>'
        for reason in route["reasons"]
    )
    return f"""
    <div>
      <div class="pm-subsection-title">Why PayMind selected this route</div>
      <div class="pm-subsection-copy">Readable explanation of the strongest recommendation.</div>
      <div class="pm-reasons-list" style="margin-top:16px;">{rows}</div>
    </div>
    """


def build_score_breakdown(route: dict[str, Any]) -> str:
    rows = [
        ("Reliability", float(route["reliability_score"])),
        ("Settlement", float(route["settlement_score"])),
        ("Fee", float(route["fee_score"])),
        ("Route fit", float(route["candidate_score"])),
    ]
    markup = "".join(
        f"""
        <div class="pm-bar-row">
          <div class="pm-bar-label">{label}</div>
          <div class="pm-bar-track"><div class="pm-bar-fill" style="width:{value * 100:.1f}%"></div></div>
          <div class="pm-bar-value">{format_percent(value)}</div>
        </div>
        """
        for label, value in rows
    )
    return f"""
    <div>
      <div class="pm-subsection-title">Score composition</div>
      <div class="pm-subsection-copy">How the recommendation balances reliability, settlement, cost and route fit.</div>
      <div class="pm-bars" style="margin-top:16px;">{markup}</div>
    </div>
    """


def build_alternatives(
    recommendations: list[dict[str, Any]],
    currency: str,
) -> str:
    rows = []
    for route in recommendations[1:6]:
        rows.append(
            f"""
            <div class="pm-route-row">
              <div class="pm-route-rank">{route["rank"]}</div>
              <div class="pm-route-provider">{route_display_name(str(route["payment_method"]))}</div>
              <div class="pm-route-meta">
                <div class="pm-route-meta-label">Score</div>
                <div class="pm-route-meta-value">{format_score(float(route["final_score"]))}</div>
              </div>
              <div class="pm-route-meta">
                <div class="pm-route-meta-label">Success</div>
                <div class="pm-route-meta-value">{format_percent(float(route["success_probability"]))}</div>
              </div>
              <div class="pm-route-meta">
                <div class="pm-route-meta-label">P90</div>
                <div class="pm-route-meta-value">{format_duration(float(route["arrival_p90_minutes"]))}</div>
              </div>
              <div class="pm-route-meta">
                <div class="pm-route-meta-label">Fee</div>
                <div class="pm-route-meta-value">{format_fee(float(route["estimated_fee"]), currency)}</div>
              </div>
            </div>
            """
        )

    if not rows:
        rows_markup = '<div class="pm-copy" style="margin-top:16px;">No next-best routes remained after eligibility filtering.</div>'
    else:
        rows_markup = f'<div class="pm-route-rows">{"".join(rows)}</div>'

    return f"""
    <div>
      <div class="pm-subsection-title">Alternative routes</div>
      <div class="pm-subsection-copy">Compare the next-best eligible options.</div>
      {rows_markup}
    </div>
    """


def build_result_group(
    recommendations: list[dict[str, Any]],
    request: dict[str, Any],
) -> tuple[str, str, str]:
    top_route = recommendations[0]
    hero = build_hero(top_route, request)
    alternatives = build_alternatives(recommendations, str(request["currency"]))
    breakdown = build_reasons(top_route) + build_score_breakdown(top_route)
    return hero, alternatives, breakdown



def render_models_tab() -> str:
    items: list[str] = []

    for model in MODEL_SUMMARY.models:
        metadata = model.metadata
        metrics = metadata.get("metrics", {})

        if model.key == "arrival":
            rows = metadata.get("rows", {})
            for label, description, metric_label, metric_value in [
                (
                    "Settlement P50",
                    "Typical expected arrival time.",
                    "P50 MAE",
                    metrics.get("p50_mae_minutes", "n/a"),
                ),
                (
                    "Settlement P90",
                    "Conservative settlement estimate.",
                    "P90 Coverage",
                    metrics.get("p90_coverage", "n/a"),
                ),
            ]:
                items.append(
                    f"""
                    <div class="pm-model-item">
                      <div class="pm-model-title">{label}</div>
                      <div class="pm-model-subcopy">{description}</div>
                      <div class="pm-model-stats">
                        <div class="pm-model-stat"><span>Status</span><strong class="pm-ready">Ready</strong></div>
                        <div class="pm-model-stat"><span>Version</span><strong>{model.version}</strong></div>
                        <div class="pm-model-stat"><span>Training rows</span><strong>{rows.get("train", "n/a")}</strong></div>
                        <div class="pm-model-stat"><span>{metric_label}</span><strong>{metric_value}</strong></div>
                      </div>
                    </div>
                    """
                )
            continue

        if model.key == "payment_method":
            description = "Ranks payment routes by transaction fit."
            primary = f"Top-3 Accuracy: {metrics.get('top3_accuracy', 'n/a')}"
            secondary = f"Top-1 Accuracy: {metrics.get('top1_accuracy', 'n/a')}"
        else:
            description = "Estimates the probability that a route succeeds."
            primary = f"ROC-AUC: {metrics.get('roc_auc', 'n/a')}"
            secondary = f"PR-AUC: {metrics.get('pr_auc', 'n/a')}"

        items.append(
            f"""
            <div class="pm-model-item">
              <div class="pm-model-title">{model.display_name}</div>
              <div class="pm-model-subcopy">{description}</div>
              <div class="pm-model-stats">
                <div class="pm-model-stat"><span>Status</span><strong class="pm-ready">Ready</strong></div>
                <div class="pm-model-stat"><span>Version</span><strong>{model.version}</strong></div>
                <div class="pm-model-stat"><span>Training rows</span><strong>{metadata.get("training_rows", metadata.get("rows", {}).get("train", "n/a"))}</strong></div>
                <div class="pm-model-stat"><span>Primary metric</span><strong>{primary}</strong></div>
                <div class="pm-model-stat"><span>Secondary metric</span><strong>{secondary}</strong></div>
              </div>
            </div>
            """
        )

    return f"""
    <div class="pm-info-wrap">
      <h2>Reference Models</h2>
      <div class="pm-info-lead">
        These are the reference models currently loaded by the demo. They are intended to show the
        PayMind architecture and should be retrained on a user's own payment environment before real use.
      </div>
      <div class="pm-model-grid">{"".join(items)}</div>

      <div class="pm-callout">
        Reference/demo metrics are only meaningful for the synthetic/reference dataset used to train these models.
        They should not be interpreted as real-world provider performance.
      </div>
    </div>
    """





def render_pipeline_tab() -> str:
    stages = [
        ("Transaction", "Normalize amount, currency, country, type, channel and time context."),
        ("Eligibility", "Remove routes that are unavailable for the current request."),
        ("Candidate Fit", "Estimate which payment methods best match the transaction."),
        ("Reliability", "Estimate the probability that each candidate route succeeds."),
        ("Settlement", "Predict typical P50 and conservative P90 arrival time."),
        ("Fees", "Calculate configured estimated route cost."),
        ("Ranking", "Combine reliability, settlement, fee and route-fit scores."),
        ("Recommendation", "Return the best route, alternatives and readable reasons."),
    ]

    cards = "".join(
        f"""
        <div class="pm-model-item">
          <div class="pm-model-title">{title}</div>
          <div class="pm-model-subcopy">{copy}</div>
        </div>
        """
        for title, copy in stages
    )

    return f"""
    <div class="pm-info-wrap">
      <h2>How It Works</h2>
      <div class="pm-info-lead">
        PayMind evaluates available payment routes and ranks them before a payment is sent.
        It does not execute the payment itself.
      </div>

      <div class="pm-pipeline-row">
        {cards}
      </div>

      <div class="pm-info-section">
        <h3>Runtime flow</h3>
        <div class="pm-kv">
          <div>Input</div><div>Transaction context enters through the SDK, API or connector.</div>
          <div>Feature building</div><div>Derived fields such as hour, day, weekend and cross-border context are created internally.</div>
          <div>Route evaluation</div><div>Only eligible/available routes continue into model scoring.</div>
          <div>Model scoring</div><div>Candidate fit, reliability and settlement expectations are predicted per route.</div>
          <div>Commercial scoring</div><div>Configured fees are calculated and normalized against other eligible routes.</div>
          <div>Output</div><div>PayMind returns a ranked recommendation with alternatives and explanations.</div>
        </div>
      </div>

      <div class="pm-callout">
        PayMind is designed to run inside the user's environment. The core ranking engine does not require
        a hosted database or payment credentials and does not execute the payment itself.
      </div>
    </div>
    """



def render_train_tab() -> str:
    return """
    <div class="pm-info-wrap">
      <h2>Train Your Own</h2>
      <div class="pm-info-lead">
        PayMind is designed to be forked and retrained. The hosted demo uses reference models only;
        contributors provide their own local payment data and generate models for their own environment.
      </div>

      <div class="pm-training-grid">
        <div class="pm-training-card">
          <strong>01 · Clone</strong>
          <span>Fork or clone the repository and create a Python virtual environment.</span>
        </div>
        <div class="pm-training-card">
          <strong>02 · Add data</strong>
          <span>Place your own three canonical training CSVs under <code>data/training/</code>.</span>
        </div>
        <div class="pm-training-card">
          <strong>03 · Train</strong>
          <span>Run the single training command. PayMind inspects, cleans, splits and trains all models.</span>
        </div>
        <div class="pm-training-card">
          <strong>04 · Review</strong>
          <span>Check the generated model reports and validation metrics before using the artifacts.</span>
        </div>
        <div class="pm-training-card">
          <strong>05 · Run</strong>
          <span>Load the generated models through the SDK, FastAPI endpoint or your own connector.</span>
        </div>
      </div>

      <div class="pm-info-section">
        <h3>Quick start</h3>
        <pre class="pm-command-block"><code>git clone &lt;your-fork-url&gt;
cd navcore_paymind

python3 -m venv .venv
source .venv/bin/activate

python3 -m pip install -e ".[training]"

# Add your own files:
# data/training/payment_method.csv
# data/training/success.csv
# data/training/arrival.csv

python3 scripts/train_all.py</code></pre>
      </div>

      <div class="pm-info-section">
        <h3>Training files</h3>
        <ul class="pm-schema-list">
          <li><code>payment_method.csv</code> — candidate/payment-method training data.</li>
          <li><code>success.csv</code> — binary success/reliability training data.</li>
          <li><code>arrival.csv</code> — settlement-duration data used for P50/P90 models.</li>
        </ul>
        <p>
          Exact column definitions should be kept in <code>docs/data-schemas.md</code>.
          Synthetic templates can be provided under <code>examples/csv/</code>.
        </p>
      </div>

      <div class="pm-info-section">
        <h3>What the training command does</h3>
        <div class="pm-kv">
          <div>Inspect</div><div>Checks schema, date ranges, methods, currencies and target distributions.</div>
          <div>Clean</div><div>Removes invalid rows and applies the configured payment-method class policy.</div>
          <div>Split</div><div>Creates chronological train, validation and test datasets.</div>
          <div>Features</div><div>Builds the same model features used by runtime inference.</div>
          <div>Candidate model</div><div>Trains the payment-method / route-fit classifier.</div>
          <div>Reliability model</div><div>Trains the binary success-probability classifier.</div>
          <div>Settlement models</div><div>Trains P50 and P90 arrival-time quantile models.</div>
          <div>Validation</div><div>Runs reports and tests so a broken pipeline stops before models are accepted.</div>
        </div>
      </div>

      <div class="pm-info-section">
        <h3>Generated artifacts</h3>
        <p>After a successful run, PayMind generates model artifacts and metadata under the local <code>models/</code> directory and evaluation reports under <code>data/reports/</code>.</p>
      </div>

      <div class="pm-callout">
        Bring your own data. PayMind does not require proprietary data to be published, and the public demo
        should never include production transaction CSVs. Reference models and synthetic data exist only to
        demonstrate how the architecture works.
      </div>
    </div>
    """



def select_all_routes() -> list[str]:
    return list(DEFAULT_DEMO_ROUTES)


def clear_routes() -> list[str]:
    return []


def default_country_updates(country: str) -> tuple[str, str]:
    return COUNTRY_TO_CURRENCY.get(country, "USD"), country


def evaluate_demo(
    transaction_type: str,
    amount: float,
    currency: str,
    country: str,
    ip_country: str,
    app_type: str,
    available_routes: list[str],
    cross_border_override: str,
) -> tuple[Any, Any, Any, Any, Any, Any, Any, Any, Any]:
    if not available_routes:
        empty = build_empty_state()
        message = """
        <div>
          <div class="pm-subsection-title">No routes selected</div>
          <div class="pm-subsection-copy">Choose at least one available route to run the evaluation.</div>
        </div>
        """
        return (
            gr.update(value=empty, visible=True),
            gr.update(visible=False),
            gr.update(value=message, visible=True),
            gr.update(visible=False),
            gr.update(visible=False),
            gr.update(visible=False),
            gr.update(value=pd.DataFrame(), visible=False),
            gr.update(value=json.dumps({"response": {"recommendations": []}}, indent=2), visible=True),
            gr.update(value=json.dumps({"available_payment_routes": []}, indent=2), visible=True),
        )

    request = build_demo_request(
        transaction_type=transaction_type,
        amount=amount,
        currency=currency,
        country=country,
        ip_country=ip_country,
        app_type=app_type,
        available_routes=available_routes,
        cross_border_override=cross_border_override,
    )

    response = PAYMIND.evaluate(request).model_dump(mode="json")
    recommendations = response["recommendations"]

    if not recommendations:
        empty = """
        <div class="pm-section pm-empty-state">
          <div class="pm-empty-content">
            <div class="pm-empty-title">No eligible routes remain</div>
            <div class="pm-empty-copy">Try enabling more routes, switching country or IP country, or changing the channel or transaction type.</div>
          </div>
        </div>
        """
        return (
            gr.update(value=empty, visible=True),
            gr.update(visible=False),
            gr.update(visible=False),
            gr.update(visible=False),
            gr.update(visible=False),
            gr.update(visible=True),
            gr.update(value=pd.DataFrame(), visible=False),
            gr.update(value=json.dumps(response, indent=2), visible=True),
            gr.update(value=json.dumps(request, indent=2), visible=True),
        )

    hero, alternatives, breakdown = build_result_group(recommendations, request)
    frame = build_comparison_frame(recommendations[:5], str(request["currency"]))

    return (
        gr.update(visible=False),
        gr.update(value=hero, visible=True),
        gr.update(value=alternatives, visible=True),
        gr.update(value=breakdown, visible=True),
        gr.update(visible=True),
        gr.update(visible=True),
        gr.update(value=frame, visible=True),
        gr.update(value=json.dumps(response, indent=2), visible=True),
        gr.update(value=json.dumps(request, indent=2), visible=True),
    )



def build_demo() -> gr.Blocks:
    with gr.Blocks(
        title="NavCore PayMind",
        fill_width=True,
    ) as demo:
        gr.HTML(f"<style>{CUSTOM_CSS}</style>")
        gr.HTML(
            """
            <div class="pm-header">
              <div class="pm-title">PayMind</div>
              <div class="pm-subtitle">
                Open-source payment intelligence for comparing eligible payment routes using
                route fit, predicted reliability, settlement expectations and estimated cost.
              </div>
              <div class="pm-note">
                Demo uses synthetic/reference training data. Scores do not represent actual provider performance.
              </div>
            </div>
            """
        )

        with gr.Tabs():
            with gr.Tab("Try PayMind"):
                with gr.Row(equal_height=False):
                    with gr.Column(scale=5, min_width=340):
                        gr.Markdown("### Transaction")
                        gr.Markdown(
                            "Set the payment context and choose which routes PayMind may consider.",
                            elem_classes=["pm-muted"],
                        )

                        transaction_type = gr.Radio(
                            choices=["deposit", "withdrawal"],
                            value="deposit",
                            label="Transaction type",
                        )

                        with gr.Row():
                            amount = gr.Number(
                                value=500.0,
                                minimum=0.01,
                                label="Amount",
                            )
                            currency = gr.Dropdown(
                                choices=sorted(set(COUNTRY_TO_CURRENCY.values())),
                                value="AUD",
                                label="Currency",
                            )

                        with gr.Row():
                            country = gr.Dropdown(
                                choices=COUNTRY_OPTIONS,
                                value="AU",
                                label="Country",
                            )
                            ip_country = gr.Dropdown(
                                choices=COUNTRY_OPTIONS,
                                value="AU",
                                label="IP country",
                            )

                        app_type = gr.Dropdown(
                            choices=APP_CHANNEL_OPTIONS,
                            value="web_checkout",
                            label="Channel",
                        )

                        gr.Markdown("#### Available routes")
                        gr.Markdown(
                            "Only selected routes will be considered.",
                            elem_classes=["pm-muted"],
                        )

                        available_routes = gr.CheckboxGroup(
                            choices=ROUTE_OPTIONS,
                            value=list(DEFAULT_DEMO_ROUTES),
                            label="Routes",
                        )

                        with gr.Row():
                            select_all_button = gr.Button("Select all", size="sm")
                            clear_button = gr.Button("Clear", size="sm")

                        with gr.Accordion("Advanced", open=False):
                            cross_border_override = gr.Radio(
                                choices=[
                                    ("Auto", "auto"),
                                    ("Force local", "force_local"),
                                    ("Force cross-border", "force_cross_border"),
                                ],
                                value="auto",
                                label="Cross-border override",
                            )

                        evaluate_button = gr.Button(
                            "Evaluate Routes",
                            variant="primary",
                            elem_classes=["pm-primary"],
                        )

                    with gr.Column(scale=7, min_width=480):
                        gr.Markdown("### Recommendation")

                        empty_state = gr.HTML(
                            build_empty_state(),
                            visible=True,
                            elem_classes=["pm-result"],
                        )
                        hero = gr.HTML(visible=False)

                        gr.Markdown("### Alternative Routes")
                        alternatives = gr.HTML(visible=False)

                        gr.Markdown("### Score Breakdown")
                        breakdown = gr.HTML(visible=False)

                        with gr.Accordion(
                            "Detailed Comparison",
                            open=False,
                            visible=False,
                        ) as comparison_wrap:
                            comparison = gr.Dataframe(
                                headers=[
                                    "Rank",
                                    "Route",
                                    "Score",
                                    "Success",
                                    "P50",
                                    "P90",
                                    "Fee",
                                    "Fee Rate",
                                ],
                                interactive=False,
                                wrap=True,
                            )

                        with gr.Accordion(
                            "Developer Details",
                            open=False,
                            visible=False,
                        ) as developer_wrap:
                            gr.Markdown("**Raw evaluation response**")
                            raw_response = gr.Code(
                                language="json",
                                interactive=False,
                            )
                            gr.Markdown("**Derived transaction context**")
                            derived_request = gr.Code(
                                language="json",
                                interactive=False,
                            )

                evaluate_button.click(
                    evaluate_demo,
                    inputs=[
                        transaction_type,
                        amount,
                        currency,
                        country,
                        ip_country,
                        app_type,
                        available_routes,
                        cross_border_override,
                    ],
                    outputs=[
                        empty_state,
                        hero,
                        alternatives,
                        breakdown,
                        comparison_wrap,
                        developer_wrap,
                        comparison,
                        raw_response,
                        derived_request,
                    ],
                )

                country.change(
                    default_country_updates,
                    inputs=[country],
                    outputs=[currency, ip_country],
                )

                select_all_button.click(
                    select_all_routes,
                    outputs=[available_routes],
                )

                clear_button.click(
                    clear_routes,
                    outputs=[available_routes],
                )

            with gr.Tab("Models"):
                gr.HTML(render_models_tab())

            with gr.Tab("How It Works"):
                gr.HTML(render_pipeline_tab())

            with gr.Tab("Train Your Own"):
                gr.HTML(render_train_tab())

    return demo



app = build_demo()
demo = app


def launch_demo() -> None:
    launch_kwargs: dict[str, object] = {}
    server_name = os.getenv("GRADIO_SERVER_NAME")
    server_port = os.getenv("GRADIO_SERVER_PORT")
    if server_name:
        launch_kwargs["server_name"] = server_name
    if server_port:
        launch_kwargs["server_port"] = int(server_port)
    app.launch(**launch_kwargs)


if __name__ == "__main__":
    launch_demo()
