"""
Semiconductor Supply Chain Heatmap Data Generator
Fetches latest stock data and MTD/YTD returns for global semiconductor
supply chain companies (chip design → EDA/IP → foundry → memory →
analog/power → equipment → materials → OSAT) via yfinance.
Outputs JSON to be served via GitHub Pages.
"""

import json
import os
import sys
import time
from multiprocessing import Process, Queue
import yfinance as yf
from datetime import datetime, timezone, timedelta, date

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


# ============================================================
# Stock Universe: Global Semiconductor Supply Chain
# sector codes:
#   chip_design / eda_ip / foundry / memory /
#   analog_power / equipment / materials / osat
# ============================================================

STOCKS = [
    # === Chip Design (芯片设计) ===
    {"ticker": "NVDA",       "name": "NVIDIA",        "sector": "chip_design"},
    {"ticker": "AMD",        "name": "AMD",           "sector": "chip_design"},
    {"ticker": "QCOM",       "name": "高通",          "sector": "chip_design"},
    {"ticker": "MRVL",       "name": "Marvell",       "sector": "chip_design"},
    {"ticker": "MCHP",       "name": "Microchip",     "sector": "chip_design"},
    {"ticker": "NXPI",       "name": "NXP",           "sector": "chip_design"},
    {"ticker": "STM",        "name": "STMicro",       "sector": "chip_design"},
    {"ticker": "2454.TW",    "name": "联发科",        "sector": "chip_design"},
    {"ticker": "603160.SS",  "name": "汇顶科技",      "sector": "chip_design"},
    {"ticker": "300661.SZ",  "name": "圣邦股份",      "sector": "chip_design"},
    {"ticker": "300782.SZ",  "name": "卓胜微",        "sector": "chip_design"},
    {"ticker": "688008.SS",  "name": "澜起科技",      "sector": "chip_design"},
    {"ticker": "688728.SS",  "name": "格科微",        "sector": "chip_design"},
    {"ticker": "002049.SZ",  "name": "紫光国微",      "sector": "chip_design"},
    {"ticker": "688536.SS",  "name": "思瑞浦",        "sector": "chip_design"},

    # === EDA & IP ===
    {"ticker": "SNPS",       "name": "Synopsys",      "sector": "eda_ip"},
    {"ticker": "CDNS",       "name": "Cadence",       "sector": "eda_ip"},
    {"ticker": "688521.SS",  "name": "芯原股份",      "sector": "eda_ip"},
    {"ticker": "688135.SS",  "name": "利扬芯片",      "sector": "eda_ip"},

    # === Foundry (晶圆代工) ===
    {"ticker": "TSM",        "name": "台积电",        "sector": "foundry"},
    {"ticker": "2330.TW",    "name": "台积电TW",      "sector": "foundry"},
    {"ticker": "UMC",        "name": "联电",          "sector": "foundry"},
    {"ticker": "2303.TW",    "name": "联电TW",        "sector": "foundry"},
    {"ticker": "688981.SS",  "name": "中芯国际",      "sector": "foundry"},
    {"ticker": "688347.SS",  "name": "华虹半导体",    "sector": "foundry"},
    {"ticker": "1347.HK",    "name": "华虹半导体HK",  "sector": "foundry"},
    {"ticker": "GFS",        "name": "GlobalFoundries","sector": "foundry"},

    # === Memory (存储芯片) ===
    {"ticker": "005930.KS",  "name": "三星电子",      "sector": "memory"},
    {"ticker": "000660.KS",  "name": "SK海力士",      "sector": "memory"},
    {"ticker": "MU",         "name": "Micron",        "sector": "memory"},
    {"ticker": "WDC",        "name": "Western Digital","sector": "memory"},
    {"ticker": "603986.SS",  "name": "兆易创新",      "sector": "memory"},
    {"ticker": "300223.SZ",  "name": "北京君正",      "sector": "memory"},
    {"ticker": "688525.SS",  "name": "佰维存储",      "sector": "memory"},
    {"ticker": "688041.SS",  "name": "海光信息",      "sector": "memory"},

    # === Analog & Power (模拟 & 功率) ===
    {"ticker": "TXN",        "name": "TI",            "sector": "analog_power"},
    {"ticker": "ADI",        "name": "ADI",           "sector": "analog_power"},
    {"ticker": "IFX.DE",     "name": "英飞凌",        "sector": "analog_power"},
    {"ticker": "ON",         "name": "ON Semi",       "sector": "analog_power"},
    {"ticker": "600460.SS",  "name": "士兰微",        "sector": "analog_power"},
    {"ticker": "603290.SS",  "name": "斯达半导",      "sector": "analog_power"},
    {"ticker": "688187.SS",  "name": "时代电气",      "sector": "analog_power"},
    {"ticker": "300623.SZ",  "name": "捷捷微电",      "sector": "analog_power"},
    {"ticker": "688396.SS",  "name": "华润微",        "sector": "analog_power"},
    {"ticker": "605111.SS",  "name": "新洁能",        "sector": "analog_power"},
    {"ticker": "300661.SZ",  "name": "圣邦股份",      "sector": "analog_power"},

    # === Semiconductor Equipment (半导体设备) ===
    {"ticker": "ASML",       "name": "ASML",          "sector": "equipment"},
    {"ticker": "AMAT",       "name": "Applied Materials","sector": "equipment"},
    {"ticker": "LRCX",       "name": "LAM Research",  "sector": "equipment"},
    {"ticker": "KLAC",       "name": "KLA",           "sector": "equipment"},
    {"ticker": "TER",        "name": "Teradyne",      "sector": "equipment"},
    {"ticker": "002371.SZ",  "name": "北方华创",      "sector": "equipment"},
    {"ticker": "688012.SS",  "name": "中微公司",      "sector": "equipment"},
    {"ticker": "688072.SS",  "name": "拓荆科技",      "sector": "equipment"},
    {"ticker": "688037.SS",  "name": "芯源微",        "sector": "equipment"},
    {"ticker": "300604.SZ",  "name": "长川科技",      "sector": "equipment"},
    {"ticker": "688120.SS",  "name": "华海清科",      "sector": "equipment"},
    {"ticker": "300567.SZ",  "name": "精测电子",      "sector": "equipment"},
    {"ticker": "688200.SS",  "name": "华峰测控",      "sector": "equipment"},

    # === Semiconductor Materials (半导体材料) ===
    {"ticker": "4063.T",     "name": "信越化学",      "sector": "materials"},
    {"ticker": "3436.T",     "name": "SUMCO",         "sector": "materials"},
    {"ticker": "688126.SS",  "name": "沪硅产业",      "sector": "materials"},
    {"ticker": "300054.SZ",  "name": "鼎龙股份",      "sector": "materials"},
    {"ticker": "688019.SS",  "name": "安集科技",      "sector": "materials"},
    {"ticker": "688268.SS",  "name": "华特气体",      "sector": "materials"},
    {"ticker": "300236.SZ",  "name": "上海新阳",      "sector": "materials"},
    {"ticker": "002409.SZ",  "name": "雅克科技",      "sector": "materials"},
    {"ticker": "688065.SS",  "name": "凯赛生物",      "sector": "materials"},
    {"ticker": "300346.SZ",  "name": "南大光电",      "sector": "materials"},
    {"ticker": "688378.SS",  "name": "奥来德",        "sector": "materials"},
    {"ticker": "688520.SS",  "name": "神州细胞",      "sector": "materials"},

    # === OSAT (封装测试) ===
    {"ticker": "3711.TW",    "name": "日月光投控",    "sector": "osat"},
    {"ticker": "AMKR",       "name": "Amkor",         "sector": "osat"},
    {"ticker": "600584.SS",  "name": "长电科技",      "sector": "osat"},
    {"ticker": "002185.SZ",  "name": "华天科技",      "sector": "osat"},
    {"ticker": "688362.SS",  "name": "甬矽电子",      "sector": "osat"},
    {"ticker": "688135.SS",  "name": "利扬芯片",      "sector": "osat"},
]


def pct_change(latest, base):
    """Return percentage change, or None when the base is unavailable."""
    if latest is None or base is None or base == 0:
        return None
    return round((latest / base - 1) * 100, 2)


def period_return(closes, start_day):
    """Return latest close vs the trading close immediately before start_day.

    If there is no pre-period close in the downloaded window, fall back to the
    first available close in the period. This keeps new listings usable while
    avoiding a separate request per ticker.
    """
    if closes.empty:
        return None

    close_dates = closes.index.date
    before = closes[close_dates < start_day]
    if not before.empty:
        base = float(before.iloc[-1])
    else:
        in_period = closes[close_dates >= start_day]
        base = float(in_period.iloc[0]) if not in_period.empty else None

    return pct_change(float(closes.iloc[-1]), base)


def _download_ticker_worker(ticker, queue):
    try:
        data = yf.download(
            ticker,
            period="1y",
            auto_adjust=True,
            threads=False,
            progress=False,
            timeout=8,
        )
        if hasattr(data.columns, "nlevels") and data.columns.nlevels > 1:
            if ticker in data.columns.get_level_values(0):
                data = data[ticker]
            elif ticker in data.columns.get_level_values(1):
                data = data.xs(ticker, axis=1, level=1)
        queue.put(data)
    except Exception as exc:
        queue.put(exc)


def download_ticker(ticker, timeout_seconds=12):
    queue = Queue()
    process = Process(target=_download_ticker_worker, args=(ticker, queue))
    process.start()
    process.join(timeout_seconds)

    if process.is_alive():
        process.terminate()
        process.join()
        print(f"  download timed out: {ticker}")
        return None

    if queue.empty():
        return None

    data = queue.get()
    if isinstance(data, Exception):
        print(f"  download failed: {ticker}: {data}")
        return None
    return data


def _metadata_worker(ticker, queue):
    try:
        info = yf.Ticker(ticker).info
        forward_pe = info.get("forwardPE")
        trailing_pe = info.get("trailingPE")
        pe = forward_pe or trailing_pe
        pe_type = "forward" if forward_pe else ("trailing" if trailing_pe else None)
        queue.put({
            "pe": pe,
            "pe_type": pe_type,
            "mkt_cap": info.get("marketCap"),
            "currency": info.get("currency", ""),
        })
    except Exception as exc:
        queue.put(exc)


def fetch_metadata(ticker, timeout_seconds=5):
    queue = Queue()
    process = Process(target=_metadata_worker, args=(ticker, queue))
    process.start()
    process.join(timeout_seconds)

    if process.is_alive():
        process.terminate()
        process.join()
        print(f"  metadata timed out: {ticker}")
        return None

    if queue.empty():
        return None

    metadata = queue.get()
    if isinstance(metadata, Exception):
        print(f"  metadata failed: {ticker}: {metadata}")
        return None
    return metadata


def fetch_data():
    """Fetch latest quote data and MTD/YTD returns for all stocks."""
    print(f"Fetching {len(STOCKS)} tickers...")

    data_by_ticker = {}
    for index, stock in enumerate(STOCKS, start=1):
        tk = stock["ticker"]
        print(f"Downloading {index}/{len(STOCKS)}: {tk}")
        data_by_ticker[tk] = download_ticker(tk)
        time.sleep(0.2)

    results = []
    for stock in STOCKS:
        tk = stock["ticker"]
        try:
            df = data_by_ticker.get(tk)

            if df is None or df.empty or df["Close"].dropna().empty:
                print(f"  WARN {tk} ({stock['name']}): no data")
                results.append({
                    **stock,
                    "price": None,
                    "change_pct": None,
                    "mtd_pct": None,
                    "ytd_pct": None,
                    "pe": None,
                    "pe_type": None,
                    "mkt_cap_b": None,
                    "currency": None,
                })
                continue

            closes = df["Close"].dropna()
            last_price = float(closes.iloc[-1])

            # Daily change %
            if len(closes) >= 2:
                prev_price = float(closes.iloc[-2])
                change_pct = pct_change(last_price, prev_price)
            else:
                change_pct = 0.0

            latest_day = closes.index[-1].date()
            month_start = date(latest_day.year, latest_day.month, 1)
            year_start = date(latest_day.year, 1, 1)
            mtd_pct = period_return(closes, month_start)
            ytd_pct = period_return(closes, year_start)

            results.append({
                **stock,
                "price": round(last_price, 2),
                "change_pct": change_pct,
                "mtd_pct": mtd_pct,
                "ytd_pct": ytd_pct,
                "pe": None,
                "pe_type": None,
                "mkt_cap_b": None,
                "currency": None,
            })
            mtd_text = f"{mtd_pct:+.2f}%" if mtd_pct is not None else "N/A"
            ytd_text = f"{ytd_pct:+.2f}%" if ytd_pct is not None else "N/A"
            print(f"  OK {tk}: {last_price} (D {change_pct:+.2f}%, MTD {mtd_text}, YTD {ytd_text})")

        except Exception as e:
            print(f"  ERR {tk} ({stock['name']}): {e}")
            results.append({
                **stock,
                "price": None,
                "change_pct": None,
                "mtd_pct": None,
                "ytd_pct": None,
                "pe": None,
                "pe_type": None,
                "mkt_cap_b": None,
                "currency": None,
            })

    if os.getenv("FETCH_HEATMAP_METADATA", "1") == "0":
        print("\nSkipping PE / market cap metadata because FETCH_HEATMAP_METADATA=0.")
        return results

    # Second pass: fetch PE and market cap
    print("\nFetching PE / market cap...")
    for item in results:
        if item["price"] is None:
            continue
        tk = item["ticker"]
        metadata = fetch_metadata(tk)
        if not metadata:
            print(f"  WARN {tk}: metadata unavailable")
            continue

        pe = metadata.get("pe")
        pe_type = metadata.get("pe_type")
        mkt_cap = metadata.get("mkt_cap")
        currency = metadata.get("currency", "")

        item["pe"] = round(pe, 1) if pe else None
        item["pe_type"] = pe_type if pe else None
        item["mkt_cap_b"] = round(mkt_cap / 1e9, 1) if mkt_cap else None
        item["currency"] = currency
        print(f"  OK {tk}: PE={item['pe']} ({item['pe_type']}), MktCap={item['mkt_cap_b']}B {currency}")

    return results


def main():
    stocks = fetch_data()
    ok = sum(1 for s in stocks if s["price"] is not None)
    min_success = int(os.getenv("MIN_HEATMAP_SUCCESS", "40"))
    if ok < min_success:
        print(f"\nOnly {ok} stocks fetched successfully; refusing to overwrite heatmap JSON.")
        print(f"Set MIN_HEATMAP_SUCCESS to adjust the threshold. Current threshold: {min_success}")
        sys.exit(1)

    # Timestamp in HKT (UTC+8)
    hkt = timezone(timedelta(hours=8))
    now = datetime.now(hkt)

    output = {
        "updated": now.strftime("%Y-%m-%d %H:%M HKT"),
        "chain": "semiconductor",
        "stocks": stocks,
    }

    outfile = "semiconductor_heatmap.json"
    with open(outfile, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\nDone! {len(stocks)} stocks written to {outfile}")
    print(f"   Updated: {output['updated']}")
    print(f"   Success: {ok}, Failed: {len(stocks) - ok}")


if __name__ == "__main__":
    main()
