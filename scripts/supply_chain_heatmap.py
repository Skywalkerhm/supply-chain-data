"""
Supply Chain Heatmap Data Generator
Fetches latest stock data and MTD/YTD returns for AI hardware supply chain companies via yfinance.
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
# Stock Universe: AI Hardware Supply Chain
# sector codes: raw_mat / ccl / pcb / ic_sub / cowos /
#               optical_chip / optical_mod / optical_infra / glass
# ============================================================

STOCKS = [
    # === STEP 0: Raw Materials ===
    # Copper foil
    {"ticker": "5706.T",    "name": "三井金属",   "sector": "raw_mat"},
    {"ticker": "5801.T",    "name": "古河电工",   "sector": "raw_mat"},
    {"ticker": "301511.SZ", "name": "德福科技",   "sector": "raw_mat"},
    {"ticker": "301217.SZ", "name": "铜冠铜箔",   "sector": "raw_mat"},
    {"ticker": "301389.SZ", "name": "隆扬电子",   "sector": "raw_mat"},
    {"ticker": "8358.TWO",   "name": "金居开发",   "sector": "raw_mat"},
    {"ticker": "336370.KS", "name": "索路思Solus","sector": "raw_mat"},

    # E-cloth
    {"ticker": "3110.T",    "name": "日东纺",     "sector": "raw_mat"},
    {"ticker": "3407.T",    "name": "旭化成",     "sector": "raw_mat"},
    {"ticker": "002080.SZ", "name": "中材科技",   "sector": "raw_mat"},
    {"ticker": "603256.SS", "name": "宏和科技",   "sector": "raw_mat"},
    {"ticker": "300395.SZ", "name": "菲利华",     "sector": "raw_mat"},
    {"ticker": "301526.SZ", "name": "国际复材",   "sector": "raw_mat"},
    {"ticker": "600176.SS", "name": "中国巨石",   "sector": "raw_mat"},
    # Resin
    {"ticker": "4182.T",    "name": "MGC三菱瓦斯","sector": "raw_mat"},
    {"ticker": "605589.SS", "name": "圣泉集团",   "sector": "raw_mat"},
    {"ticker": "4004.T",     "name": "Resonac", "sector": "raw_mat"},
    {"ticker": "4203.T",     "name": "住友电木", "sector": "raw_mat"},

    # === STEP 1: CCL ===
    {"ticker": "2383.TW",   "name": "台光电子",   "sector": "ccl"},
    {"ticker": "6213.TW",  "name": "联茂电子",   "sector": "ccl"},
    {"ticker": "6274.TWO",  "name": "台燿科技",   "sector": "ccl"},
    {"ticker": "600183.SS", "name": "生益科技",   "sector": "ccl"},
    {"ticker": "603186.SS", "name": "华正新材",   "sector": "ccl"},
    {"ticker": "1888.HK",   "name": "建滔积层板", "sector": "ccl"},
    {"ticker": "6752.T",    "name": "Panasonic",  "sector": "ccl"},
    {"ticker": "ROG",       "name": "Rogers",     "sector": "ccl"},

    # === STEP 2: PCB ===
    {"ticker": "002938.SZ", "name": "鹏鼎控股",   "sector": "pcb"},
    {"ticker": "3037.TW",   "name": "欣兴电子",   "sector": "pcb"},
    {"ticker": "2368.TW",   "name": "金像电子",   "sector": "pcb"},
    {"ticker": "3044.TW",   "name": "健鼎科技",   "sector": "pcb"},
    {"ticker": "002463.SZ", "name": "沪电股份",   "sector": "pcb"},
    {"ticker": "300476.SZ", "name": "胜宏科技",   "sector": "pcb"},
    {"ticker": "688183.SS", "name": "生益电子",   "sector": "pcb"},
    {"ticker": "002916.SZ", "name": "深南电路",   "sector": "pcb"},

    # === STEP 3: IC Substrate / ABF ===
    {"ticker": "4062.T",    "name": "Ibiden",     "sector": "ic_sub"},
    {"ticker": "6967.T",    "name": "Shinko",     "sector": "ic_sub"},
    {"ticker": "2802.T",    "name": "味之素",     "sector": "ic_sub"},
    {"ticker": "8046.TW",   "name": "南亚电路板", "sector": "ic_sub"},
    {"ticker": "3264.TWO",   "name": "景硕科技",   "sector": "ic_sub"},
    {"ticker": "4958.TW",   "name": "臻鼎",   "sector": "ic_sub"},
    {"ticker": "009150.KS", "name": "三星电机",   "sector": "ic_sub"},
    {"ticker": "222800.KQ", "name": "Simmtech",   "sector": "ic_sub"},
    {"ticker": "353200.KS", "name": "Daeduck",    "sector": "ic_sub"},
    {"ticker": "ATS.VI",    "name": "AT&S",       "sector": "ic_sub"},

    # === STEP 3.5: CoWoS / Advanced Packaging ===
    {"ticker": "600584.SS", "name": "长电科技",   "sector": "cowos"},
    {"ticker": "002156.SZ", "name": "通富微电",   "sector": "cowos"},
    {"ticker": "002436.SZ", "name": "兴森科技",   "sector": "cowos"},

    #  === STEP 4: Optical - InP/GaAs substrate & epitaxy (光芯片上游) ===
    {"ticker": "AXTI",      "name": "AXT Inc",    "sector": "optical_chip"},
    {"ticker": "IQE.L",     "name": "IQE",        "sector": "optical_chip"},
    {"ticker": "5016.T",    "name": "JX金属",      "sector": "optical_chip"},
    {"ticker": "2455.TW",   "name": "全新光电",    "sector": "optical_chip"},
    {"ticker": "4971.TW",   "name": "英特磊",      "sector": "optical_chip"},
    {"ticker": "002428.SZ", "name": "云南锗业",    "sector": "optical_chip"},
    # === STEP 4: Optical - Chips & Components ===
    {"ticker": "AVGO",      "name": "Broadcom",   "sector": "optical_chip"},
    {"ticker": "MRVL",      "name": "Marvell",    "sector": "optical_chip"},
    {"ticker": "LITE",      "name": "Lumentum",   "sector": "optical_chip"},
    {"ticker": "688498.SS", "name": "源杰科技",   "sector": "optical_chip"},
    {"ticker": "300394.SZ", "name": "天孚通信",   "sector": "optical_chip"},
    {"ticker": "002281.SZ", "name": "光迅科技",   "sector": "optical_chip"},
    {"ticker": "300620.SZ", "name": "光库科技",   "sector": "optical_chip"},
    {"ticker": "688048.SS", "name": "长光华芯",   "sector": "optical_chip"},

    # === STEP 4: Optical - Modules ===
    {"ticker": "300308.SZ", "name": "中际旭创",   "sector": "optical_mod"},
    {"ticker": "300502.SZ", "name": "新易盛",     "sector": "optical_mod"},
    {"ticker": "COHR",      "name": "Coherent",   "sector": "optical_mod"},
    {"ticker": "000988.SZ", "name": "华工科技",   "sector": "optical_mod"},
    {"ticker": "603083.SS", "name": "剑桥科技",   "sector": "optical_mod"},
    {"ticker": "AAOI",      "name": "AAOI",       "sector": "optical_mod"},
    {"ticker": "FN",        "name": "Fabrinet",   "sector": "optical_mod"},

    # === STEP 4: Optical - Infra ===
    {"ticker": "601869.SS", "name": "长飞光纤",   "sector": "optical_infra"},
    {"ticker": "600487.SS", "name": "亨通光电",   "sector": "optical_infra"},
    {"ticker": "GLW",       "name": "Corning",    "sector": "optical_infra"},

    # === STEP 5: Glass Substrate ===
    {"ticker": "INTC",      "name": "Intel",      "sector": "glass"},
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
        queue.put({
            "pe": info.get("forwardPE") or info.get("trailingPE"),
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

    # One year of adjusted closes is still lightweight, and gives us the
    # trading-day base immediately before month/year start for MTD/YTD.
    # Each ticker is downloaded in a child process so a Yahoo timeout cannot
    # hang the entire GitHub Actions job.
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
                "pe": None,       # will fill below
                "mkt_cap_b": None,  # will fill below
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
                "mkt_cap_b": None,
                "currency": None,
            })

    if os.getenv("FETCH_HEATMAP_METADATA", "1") == "0":
        print("\nSkipping PE / market cap metadata because FETCH_HEATMAP_METADATA=0.")
        return results

    # Second pass: fetch PE and market cap. Each ticker has its own timeout so
    # Yahoo metadata failures never block the heatmap JSON generation.
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
        mkt_cap = metadata.get("mkt_cap")
        currency = metadata.get("currency", "")

        item["pe"] = round(pe, 1) if pe else None
        item["mkt_cap_b"] = round(mkt_cap / 1e9, 1) if mkt_cap else None
        item["currency"] = currency
        print(f"  OK {tk}: PE={item['pe']}, MktCap={item['mkt_cap_b']}B {currency}")

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
        "stocks": stocks,
    }

    outfile = "supply_chain_heatmap.json"
    with open(outfile, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\nDone! {len(stocks)} stocks written to {outfile}")
    print(f"   Updated: {output['updated']}")

    # Summary
    fail = len(stocks) - ok
    print(f"   Success: {ok}, Failed: {fail}")


if __name__ == "__main__":
    main()
