import json
import os
import sqlite3
from datetime import datetime

import pandas as pd


HOLDINGS_FILE = "data/holdings.csv"
TRADES_FILE = "data/trades.csv"
RULES_FILE = "data/rules.json"
DB_FILE = "portfolio.db"
OUTPUT_DIR = "outputs"


def load_data():
    holdings = pd.read_csv(HOLDINGS_FILE)
    trades = pd.read_csv(TRADES_FILE)
    with open(RULES_FILE, "r") as f:
        rules = json.load(f)
    return holdings, trades, rules


def ensure_output_dir():
    os.makedirs(OUTPUT_DIR, exist_ok=True)


def setup_database(holdings, trades):
    conn = sqlite3.connect(DB_FILE)
    holdings.to_sql("holdings", conn, if_exists="replace", index=False)
    trades.to_sql("trades", conn, if_exists="replace", index=False)
    conn.close()


def compute_portfolio_market_value(df):
    return df["market_value"].sum()


def compute_cash_after_trade(cash_balance, trade):
    notional = trade["par_amount"] * trade["price"] / 100.0
    if trade["side"] == "BUY":
        return cash_balance - notional
    return cash_balance + notional


def issuer_exposure(df):
    exposure = df.groupby("issuer", as_index=False)["market_value"].sum()
    total_mv = exposure["market_value"].sum()
    exposure["pct_of_portfolio"] = exposure["market_value"] / total_mv
    return exposure.sort_values("pct_of_portfolio", ascending=False)


def sector_exposure(df):
    exposure = df.groupby("sector", as_index=False)["market_value"].sum()
    total_mv = exposure["market_value"].sum()
    exposure["pct_of_portfolio"] = exposure["market_value"] / total_mv
    return exposure.sort_values("pct_of_portfolio", ascending=False)


def check_trade_compliance(trade, projected_holdings, projected_cash, rules):
    reasons = []

    if trade["rating"] in rules["disallowed_ratings"]:
        reasons.append(f"Disallowed rating: {trade['rating']}")

    if trade["country"] not in rules["allowed_countries"]:
        reasons.append(f"Country not allowed: {trade['country']}")

    if projected_cash < rules["min_cash_buffer"]:
        reasons.append(
            f"Cash buffer breach: projected cash {projected_cash:,.2f} < minimum {rules['min_cash_buffer']:,.2f}"
        )

    issuer_exp = issuer_exposure(projected_holdings)
    issuer_row = issuer_exp.loc[issuer_exp["issuer"] == trade["issuer"]]
    if not issuer_row.empty:
        if issuer_row.iloc[0]["pct_of_portfolio"] > rules["max_single_issuer_pct"]:
            reasons.append(
                f"Issuer concentration breach: {trade['issuer']} at {issuer_row.iloc[0]['pct_of_portfolio']:.2%}"
            )

    sector_exp = sector_exposure(projected_holdings)
    sector_row = sector_exp.loc[sector_exp["sector"] == trade["sector"]]
    if not sector_row.empty:
        if sector_row.iloc[0]["pct_of_portfolio"] > rules["max_sector_pct"]:
            reasons.append(
                f"Sector concentration breach: {trade['sector']} at {sector_row.iloc[0]['pct_of_portfolio']:.2%}"
            )

    return reasons


def apply_trade(holdings, trade):
    holdings = holdings.copy()
    notional_mv = trade["par_amount"] * trade["price"] / 100.0

    existing_mask = (
        (holdings["portfolio"] == trade["portfolio"]) &
        (holdings["asset_id"] == trade["asset_id"])
    )

    if trade["side"] == "BUY":
        if existing_mask.any():
            idx = holdings.index[existing_mask][0]
            holdings.at[idx, "par_amount"] += trade["par_amount"]
            holdings.at[idx, "price"] = trade["price"]
            holdings.at[idx, "market_value"] = holdings.at[idx, "par_amount"] * trade["price"] / 100.0
        else:
            new_row = {
                "portfolio": trade["portfolio"],
                "asset_id": trade["asset_id"],
                "issuer": trade["issuer"],
                "sector": trade["sector"],
                "rating": trade["rating"],
                "par_amount": trade["par_amount"],
                "price": trade["price"],
                "market_value": notional_mv,
                "duration": 4.0,
                "spread": 300,
                "country": trade["country"],
            }
            holdings = pd.concat([holdings, pd.DataFrame([new_row])], ignore_index=True)

    elif trade["side"] == "SELL":
        if existing_mask.any():
            idx = holdings.index[existing_mask][0]
            holdings.at[idx, "par_amount"] -= trade["par_amount"]
            if holdings.at[idx, "par_amount"] <= 0:
                holdings = holdings.drop(idx).reset_index(drop=True)
            else:
                holdings.at[idx, "price"] = trade["price"]
                holdings.at[idx, "market_value"] = holdings.at[idx, "par_amount"] * trade["price"] / 100.0

    return holdings


def generate_analytics(holdings, cash_balance):
    total_mv = compute_portfolio_market_value(holdings)
    total_aum = total_mv + cash_balance

    issuer_exp = issuer_exposure(holdings)
    sector_exp = sector_exposure(holdings)

    summary = pd.DataFrame([{
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_market_value": round(total_mv, 2),
        "cash_balance": round(cash_balance, 2),
        "total_aum": round(total_aum, 2),
        "num_positions": int(len(holdings)),
        "avg_price": round(holdings["price"].mean(), 2),
        "avg_duration": round(holdings["duration"].mean(), 2),
        "avg_spread": round(holdings["spread"].mean(), 2),
    }])

    return summary, issuer_exp, sector_exp


def process_trades(holdings, trades, rules, starting_cash=1000000):
    approved = []
    rejected = []
    cash_balance = starting_cash
    current_holdings = holdings.copy()

    for _, trade in trades.iterrows():
        projected_cash = compute_cash_after_trade(cash_balance, trade)
        projected_holdings = apply_trade(current_holdings, trade)

        reasons = check_trade_compliance(trade, projected_holdings, projected_cash, rules)

        record = trade.to_dict()
        record["projected_cash"] = round(projected_cash, 2)

        if reasons:
            record["status"] = "REJECTED"
            record["reasons"] = " | ".join(reasons)
            rejected.append(record)
        else:
            record["status"] = "APPROVED"
            record["reasons"] = ""
            approved.append(record)
            current_holdings = projected_holdings
            cash_balance = projected_cash

    approved_df = pd.DataFrame(approved)
    rejected_df = pd.DataFrame(rejected)

    return current_holdings, approved_df, rejected_df, cash_balance


def export_outputs(updated_holdings, approved_df, rejected_df, summary, issuer_exp, sector_exp):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    excel_path = os.path.join(OUTPUT_DIR, f"portfolio_report_{timestamp}.xlsx")

    with pd.ExcelWriter(excel_path, engine="xlsxwriter") as writer:
        updated_holdings.to_excel(writer, sheet_name="UpdatedHoldings", index=False)
        approved_df.to_excel(writer, sheet_name="ApprovedTrades", index=False)
        rejected_df.to_excel(writer, sheet_name="RejectedTrades", index=False)
        summary.to_excel(writer, sheet_name="PortfolioSummary", index=False)
        issuer_exp.to_excel(writer, sheet_name="IssuerExposure", index=False)
        sector_exp.to_excel(writer, sheet_name="SectorExposure", index=False)

    updated_holdings.to_csv(os.path.join(OUTPUT_DIR, "updated_holdings.csv"), index=False)
    approved_df.to_csv(os.path.join(OUTPUT_DIR, "approved_trades.csv"), index=False)
    rejected_df.to_csv(os.path.join(OUTPUT_DIR, "rejected_trades.csv"), index=False)
    summary.to_csv(os.path.join(OUTPUT_DIR, "portfolio_summary.csv"), index=False)

    return excel_path


def main():
    ensure_output_dir()
    holdings, trades, rules = load_data()
    setup_database(holdings, trades)

    updated_holdings, approved_df, rejected_df, ending_cash = process_trades(
        holdings, trades, rules, starting_cash=1000000
    )

    summary, issuer_exp, sector_exp = generate_analytics(updated_holdings, ending_cash)
    report_path = export_outputs(
        updated_holdings, approved_df, rejected_df, summary, issuer_exp, sector_exp
    )

    print("\n=== Portfolio Implementation Run Complete ===")
    print(f"Approved trades: {len(approved_df)}")
    print(f"Rejected trades: {len(rejected_df)}")
    print(f"Ending cash balance: ${ending_cash:,.2f}")
    print(f"Excel report generated: {report_path}")
    print("CSV outputs written to outputs/")


if __name__ == "__main__":
    main()