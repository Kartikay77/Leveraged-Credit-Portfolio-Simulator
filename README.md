cat > README.md <<'EOF'
# Leveraged Credit Portfolio Implementation Simulator

A Python-based leveraged credit portfolio implementation and trade compliance simulator that models trade execution workflows across mock credit funds. The project evaluates trade readiness through portfolio rules, forecasts post-trade cash, updates holdings, and exports Excel/CSV reports for portfolio analytics and operational review.

## Demo

![Portfolio Analyst Dashboard](MEDIA/Portfolio_Analyst.png)

## Overview

This project simulates the day-to-day workflow of a portfolio implementation analyst supporting leveraged credit portfolios. It processes holdings and trade blotters, applies compliance checks, updates positions for approved trades, and generates reporting outputs that can be used by portfolio management, trading, operations, and technology teams.

It is built to reflect key responsibilities commonly seen in portfolio implementation and trade support roles, including:
- trade sizing validation
- execution readiness checks
- cash forecasting
- issuer and sector exposure analysis
- portfolio reporting automation

## Features

- Trade blotter processing for buy and sell instructions
- Rule-based compliance engine
- Cash balance forecasting after each trade
- Issuer concentration analysis
- Sector concentration analysis
- Approved vs. rejected trade reporting
- Updated holdings generation
- Excel and CSV report exports
- SQLite-backed storage for reproducibility

## Tech Stack

- Python
- Pandas
- SQLite
- XlsxWriter
- Openpyxl

## Project Structure

```text
leveraged-credit-portfolio-simulator/
├── app.py
├── requirements.txt
├── README.md
├── portfolio.db
├── data/
│   ├── holdings.csv
│   ├── trades.csv
│   └── rules.json
├── outputs/
│   ├── approved_trades.csv
│   ├── rejected_trades.csv
│   ├── updated_holdings.csv
│   ├── portfolio_summary.csv
│   └── portfolio_report_<timestamp>.xlsx
└── MEDIA/
    └── Portfolio_Analyst.png
```
## Input Files

### `data/holdings.csv`
Contains the starting portfolio positions.

Example columns:
- `portfolio`
- `asset_id`
- `issuer`
- `sector`
- `rating`
- `par_amount`
- `price`
- `market_value`
- `duration`
- `spread`
- `country`

### `data/trades.csv`
Contains the trade blotter to be processed.

Example columns:
- `trade_id`
- `portfolio`
- `asset_id`
- `issuer`
- `sector`
- `rating`
- `side`
- `par_amount`
- `price`
- `country`

### `data/rules.json`
Contains portfolio-wide and fund-specific compliance rules.

Examples:
- max issuer concentration
- max sector concentration
- minimum cash buffer
- disallowed ratings
- allowed countries
- portfolio-specific overrides

## Compliance Checks

The simulator evaluates trades using rule-driven controls such as:
- issuer concentration limits
- sector concentration thresholds
- rating restrictions
- country eligibility filters
- minimum cash buffer requirements

Rejected trades are logged with clear breach reasons to support execution review.

## How It Works

1. Load holdings, trades, and rules
2. Store holdings and trades in SQLite
3. Process each trade sequentially
4. Forecast projected cash impact
5. Test projected holdings against compliance rules
6. Approve or reject the trade
7. Update holdings for approved trades
8. Generate analytics and reporting outputs

## Installation

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
## Outputs
The script generates the following artifacts inside outputs/:
approved_trades.csv
Approved trades that passed compliance checks
rejected_trades.csv
Rejected trades with breach explanations
updated_holdings.csv
Portfolio positions after applying approved trades
portfolio_summary.csv
Summary metrics including total market value, cash, AUM, and average portfolio characteristics
portfolio_report_<timestamp>.xlsx
Consolidated Excel workbook with:
Updated Holdings
Approved Trades
Rejected Trades
Portfolio Summary
Issuer Exposure
Sector Exposure
## Current Scope
This version supports:
sequential trade simulation
single-pass compliance validation
post-trade cash tracking
portfolio-level exposure reporting
exportable analytics for review
## Why This Project Matters
This project was built to reflect real-world portfolio implementation workflows in leveraged credit environments. It demonstrates:
financial and operational reasoning
Python-based data tooling
reporting automation
rule-driven trade validation
portfolio analytics under execution constraints
It is especially relevant for roles involving:
trade support
portfolio analytics
liquidity monitoring
compliance checks
workflow automation
coordination across investment, operations, and technology teams
## Resume Impact
Built a Leveraged Credit Portfolio Implementation Simulator in Python, Pandas, SQLite, and Excel to automate trade sizing, compliance checks, cash forecasting, and portfolio analytics.
Implemented rule-based controls for issuer/sector limits, rating restrictions, country eligibility, and minimum cash buffers, processing 40 trades with 21 approvals and 19 rejections.
Generated automated Excel/CSV trade blotters, updated holdings, exposure summaries, and cash reports, ending with a simulated post-trade cash balance of $907,775.
## Future Enhancements
Planned improvements include:
Streamlit dashboard for file upload and interactive analytics
multi-portfolio trade allocation engine
liquidity scoring framework
portfolio rebalancing recommendations
historical run storage and SQL-based comparison queries
richer compliance policies and fund-specific mandate support
## Quick Start on Mac
```
cd ~/Downloads
mkdir leveraged-credit-portfolio-simulator
cd leveraged-credit-portfolio-simulator
mkdir data outputs MEDIA
```
