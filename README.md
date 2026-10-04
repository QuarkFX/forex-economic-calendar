<div align="center">
  <img src="./icons/logo.png" alt="QuarkFX Logo" width="220" />

  <h1>🛡️ QuarkFX Prop Firm News Radar™ ⚡</h1>
  <h3>📊 Automated Forex Economic Calendar Data Engine 🌐</h3>

  <p>
    <b>The Ultimate News Trading Shield Built Specifically For Prop Firm Traders.</b><br>
    <i>"Never Lose A Prop Firm Payout To News Trading Again."</i>
  </p>

  <p>
    A high-performance, serverless data engine delivering real-time, edge-cached economic calendar feeds from <b>Forex Factory</b> and <b>Myfxbook</b> to safeguard traders against high-impact news violations.
  </p>

  <p>
    <img src="https://img.shields.io/badge/Engine-QuarkFX-6C5CE7.svg?logo=radar&logoColor=white" alt="QuarkFX Engine" />
    <img src="https://img.shields.io/badge/Sources-Forex%20Factory%20%7C%20Myfxbook-00B894.svg?logo=rss&logoColor=white" alt="Data Sources" />
    <img src="https://img.shields.io/badge/Bypass-SeleniumBase%20UC%20%2B%20CDP-FF6B6B.svg?logo=googlechrome&logoColor=white" alt="Cloudflare Turnstile Bypass" />
    <img src="https://img.shields.io/badge/Python-3.11%2B-blue.svg?logo=python&logoColor=white" alt="Python 3.11+" />
    <img src="https://img.shields.io/badge/CDN-jsDelivr-E84D31.svg?logo=jsdelivr&logoColor=white" alt="jsDelivr CDN" />
    <img src="https://img.shields.io/badge/Automation-GitHub%20Actions-2088FF.svg?logo=github-actions&logoColor=white" alt="GitHub Actions" />
    <img src="https://img.shields.io/badge/CORS-Enabled-brightgreen.svg?logo=webrtc&logoColor=white" alt="CORS Enabled" />
    <img src="https://img.shields.io/badge/License-MIT-yellow.svg?logo=opensourceinitiative&logoColor=white" alt="License MIT" />
  </p>
</div>

---

## 🏛️ What is QuarkFX?

**QuarkFX** is built with one straightforward mission: **to stop prop firm traders from losing their accounts and hard-earned profits to accidental news trading.**

Most prop firms enforce strict rules against trading around major economic releases. We provide real-time radar tools that track high-impact news and alert you before executing trades, preventing rule breaches and forfeited payouts.

---

## ⚙️ About This Repository: The Calendar Engine

This open-source repository serves as the core real-time macroeconomic data pipeline powering QuarkFX tools:

- 🌐 **Dual Data Sources:** Scrapes and standardizes live feeds from **Forex Factory** and **Myfxbook**.
- 🤖 **Zero Server Costs:** Autonomous execution every 15 minutes via GitHub Actions cron runners.
- 🛡️ **Dual-Engine Anti-Bot & WAF Bypass:**
  - 🏭 **Forex Factory:** TLS Safari 15.3 impersonation (`curl_cffi`) — ultra-fast sub-second execution on datacenter IPs without browser overhead.
  - 📖 **Myfxbook:** Advanced **SeleniumBase UC + CDP Mode** (`seleniumbase.io`) with automated Cloudflare Turnstile CAPTCHA solving inside virtual display (`xvfb`).
- 🚀 **Global Edge CDN:** Instant worldwide distribution through jsDelivr with automatic cache invalidation.
- 🕒 **UTC Normalized:** Strict ISO 8601 UTC timestamps with accurate handling for tentative and all-day events.
- 🔒 **SHA-256 Hashing:** Smart change detection commits only when calendar events or live actual figures change.

---

## ⚠️ The Real Problem: How Traders Lose Accounts & Payouts

<p align="center">
  <img src="./icons/ftmo.png" width="62" height="62" alt="FTMO" /> &nbsp;
  <img src="./icons/funding_pips.png" width="62" height="62" alt="Funding Pips" /> &nbsp;
  <img src="./icons/fundednext.png" width="62" height="62" alt="FundedNext" /> &nbsp;
  <img src="./icons/alpha_capital.png" width="62" height="62" alt="Alpha Capital" /> &nbsp;
  <img src="./icons/the5ers.png" width="62" height="62" alt="The5ers" /> &nbsp;
  <img src="./icons/gft.png" width="62" height="62" alt="Goat Funded Trader" /> &nbsp;
  <img src="./icons/maven.png" width="62" height="62" alt="Maven Trading" /> &nbsp;
  <img src="./icons/aquafunded.png" width="62" height="62" alt="AquaFunded" />
</p>

Top prop firms (**Funding Pips, FTMO, FundedNext, Alpha Capital, The5ers, E8 Markets, CTI**) enforce strict news trading restrictions on evaluations and funded accounts:

- 🛑 **The $\pm 2$ to $\pm 5$ Min Blackout Window:** Opening or closing trades near high-impact (Red-Folder) events is strictly prohibited.
- 💥 **Instant Account Termination:** Entering trades inside the embargo window causes immediate failure or account revocation.
- 💸 **100% Profit Confiscation:** Gains made during news windows are wiped to $0; prop firms deduct profits entirely and withhold payouts.
- 🤦 **Accidental Correlation Traps:** Traders often forget that major **USD news** simultaneously moves Gold (**XAUUSD**), Silver, and Indices (**US30, NAS100**).

---

## 🖥️ Supported Platforms & Toolkits

<div align="center">
  <table>
    <tr>
      <td align="center" width="130">
        <img src="./icons/mt4.png" width="68" height="68" alt="MetaTrader 4" /><br>
        <sub><b>MetaTrader 4</b></sub><br>
        <sub>Desktop Indicator</sub>
      </td>
      <td align="center" width="130">
        <img src="./icons/mt5.png" width="68" height="68" alt="MetaTrader 5" /><br>
        <sub><b>MetaTrader 5</b></sub><br>
        <sub>Desktop Indicator</sub>
      </td>
      <td align="center" width="130">
        <img src="./icons/chrome.png" width="68" height="68" alt="Chrome Extension" /><br>
        <sub><b>Chrome Extension</b></sub><br>
        <sub>TradingView Overlay</sub>
      </td>
      <td align="center" width="130">
        <img src="./icons/web.png" width="68" height="68" alt="Web Dashboard" /><br>
        <sub><b>Web Dashboard</b></sub><br>
        <sub>Live Radar Terminal</sub>
      </td>
      <td align="center" width="130">
        <img src="./icons/mobile.png" width="68" height="68" alt="Mobile App" /><br>
        <sub><b>Mobile App</b></sub><br>
        <sub>iOS & Android PWA</sub>
      </td>
    </tr>
  </table>
</div>

---

## ⬇️ Public CDN Endpoints (Instant Worldwide Access)

Datasets are refreshed automatically every 15 minutes. Upon each update, the GitHub Actions runner calls the **jsDelivr Purge API** (`purge.jsdelivr.net`) to immediately flush global edge caches, ensuring your trading dashboards and automated bots receive real-time actuals without delay:

| Dataset | Coverage | Production Edge CDN Endpoint (jsDelivr) |
| :--- | :--- | :--- |
| 🔴 **Forex Factory (21 Days)** | 3 Weeks (Past + Current + Next) | `https://cdn.jsdelivr.net/gh/QuarkFX/forex-economic-calendar@main/output/forexfactory_21days.json` |
| 🔵 **Myfxbook (21 Days)** | 3 Weeks (Past + Current + Next) | `https://cdn.jsdelivr.net/gh/QuarkFX/forex-economic-calendar@main/output/myfxbook_21days.json` |
| 🟠 **Forex Factory (This Week)** | Current Trading Week | `https://cdn.jsdelivr.net/gh/QuarkFX/forex-economic-calendar@main/output/forexfactory_thisweek.json` |
| 🟢 **Myfxbook (This Week)** | Current Trading Week | `https://cdn.jsdelivr.net/gh/QuarkFX/forex-economic-calendar@main/output/myfxbook_thisweek.json` |

<details>
<summary><b>🔗 Need Direct Raw GitHub URLs? (Origin Fallback)</b></summary>
<br>

If your environment restricts CDNs, you can fetch directly from GitHub origin:
- **Forex Factory (21 Days):** `https://raw.githubusercontent.com/QuarkFX/forex-economic-calendar/main/output/forexfactory_21days.json`
- **Myfxbook (21 Days):** `https://raw.githubusercontent.com/QuarkFX/forex-economic-calendar/main/output/myfxbook_21days.json`
- **Forex Factory (This Week):** `https://raw.githubusercontent.com/QuarkFX/forex-economic-calendar/main/output/forexfactory_thisweek.json`
- **Myfxbook (This Week):** `https://raw.githubusercontent.com/QuarkFX/forex-economic-calendar/main/output/myfxbook_thisweek.json`

</details>

---

## 📊 Standardized JSON Schema

Every dataset in the `output/` directory adheres to a strictly standardized, clean structure:

```json
{
  "source_file": "forexfactory_thisweek.json",
  "updated_at": "2026-10-03T10:05:47Z",
  "count": 143,
  "events": [
    {
      "id": "ff_144729",
      "title": "Non-Farm Employment Change",
      "country": "USD",
      "datetime": "2026-10-02T12:30:00Z",
      "timestamp": 1790944200,
      "date": "2026-10-02",
      "time": "12:30",
      "timezone": "UTC",
      "impact": "High",
      "forecast": "142K",
      "previous": "142K",
      "actual": "254K",
      "actual_state": "better"
    }
  ]
}
```

### 🏷️ Field Definitions
- 🆔 **`id`**: Unique string identifier (`ff_<event_id>` or `mfb_<event_id>`).
- 📰 **`title`**: Name of the macroeconomic indicator or event (e.g., `CPI m/m`, `FOMC Statement`).
- 💱 **`country`**: 3-letter currency code affected (`USD`, `EUR`, `GBP`, `JPY`, `AUD`, `CAD`, `CHF`, `NZD`, `CNY`).
- 📅 **`datetime`**: Standardized ISO 8601 UTC timestamp (`YYYY-MM-DDTHH:MM:SSZ`).
- ⏱️ **`timestamp`**: Unix epoch timestamp in seconds for fast mathematical comparisons.
- 📆 **`date`** & ⏰ **`time`**: Separate `YYYY-MM-DD` and `HH:MM` strings for easy UI table binding.
- 🌍 **`timezone`**: Canonical timezone standard (`UTC`).
- 💥 **`impact`**: Standardized severity rating:
  - 🔴 `High` (Red Folder — Primary prop firm restriction target)
  - 🟠 `Medium` (Orange Folder)
  - 🟡 `Low` (Yellow Folder)
  - ⚪ `Non-Economic` (Bank holidays and speeches without forecast)
- 🔮 **`forecast`** & 📜 **`previous`**: Market consensus and prior period release numbers.
- 🎯 **`actual`**: Live reported number (updated in real time as data drops).
- 📈 **`actual_state`**: Economic sentiment evaluation (`better`, `worse`, or `neutral`).

---

## 🛡️ Production Architecture & Resilience

### 🧩 Cloudflare Datacenter Challenge: How We Solved 403 WAF

Cloudflare WAF serves interactive Turnstile challenges (`403 Attention Required!`) to cloud datacenter IPs (GitHub Actions / Azure / AWS), which breaks traditional HTTP scrapers:

| Scraping Technique | Residential IP | Cloud Datacenter IP (CI/CD) | QuarkFX Engine Status |
| :--- | :--- | :--- | :--- |
| **Standard HTTP (requests / axios)** | ❌ Blocked (`403`) | ❌ Blocked (`403 Forbidden`) | Deprecated |
| **TLS Impersonation (`curl_cffi`)** | ✅ 100% Passes | ❌ Blocked on Myfxbook (`403`) | Active for Forex Factory; Fallback for Myfxbook |
| **Headless Chrome (Puppeteer / Playwright)** | ⚠️ Unstable | ❌ Blocked (`navigator.webdriver`) | Deprecated |
| **SeleniumBase UC + CDP Mode** | ✅ 100% Passes | ✅ **100% Passes (Turnstile Solved)** | 🚀 **Active Production Engine** |

#### 🚀 The QuarkFX UC + CDP Solution
- 🔌 **Chrome DevTools Protocol (`cdp_mode`)**: Disconnects WebDriver flags to eliminate bot detection signals.
- 🖥️ **Headless-Free via Xvfb (`xvfb=True`)**: Runs headed Chrome in a virtual Linux display to bypass canvas checks.
- ⚡ **Auto Turnstile Solver (`solve_captcha`)**: Dispatches native CDP mouse clicks to clear verification in <3s.
- 🔄 **Session Clearance Reuse**: Reuses the validated `cf_clearance` session across all periods in <18s total.

```
                               [ GitHub Actions Cron ]
                                  (Every 15 Minutes)
                                          │
                  ┌───────────────────────┴───────────────────────┐
                  ▼                                               ▼
         Forex Factory Scraper                           Myfxbook Scraper
     (curl_cffi Safari Impersonation)             (SeleniumBase UC + CDP Mode)
         [Sub-Second TLS Engine]                 [Automated Turnstile Bypass]
                  │                                               │
                  └───────────────────────┬───────────────────────┘
                                          │
                                          ▼
                            [ Smart Change Detection ]
                        (Deterministic SHA-256 Hash Check)
                                          │
                         ┌────────────────┴────────────────┐
                         ▼                                 ▼
                 [ No Data Change ]                [ New Data / Actuals ]
                Skip Commit & Purge              Commit & Push to 'main'
                                                           │
                                                           ▼
                                                [ jsDelivr Edge Purge ]
                                            Instant Worldwide CDN Invalidation
```

- 🔒 **Zero-Bloat SHA-256 Hashing:** The engine computes a canonical SHA-256 hash of the scraped events array. If numbers have not changed since the last 15-minute run, the output file is not rewritten and Git commit is skipped.
- 🔄 **Automatic Weekly Rollover:** On Sunday market open, Forex Factory and Myfxbook automatically advance their current week period. The engine detects the updated calendar dates, seamlessly rolls the 21-day timeline forward, and commits the new datasets.
- 🛡️ **Fail-Safe Data Protection:** If network failures or third-party server errors occur, the scraper will never overwrite existing valid datasets with empty or corrupted payloads.
- ⚛️ **Atomic File Replacement:** Uses atomic rename (`os.replace`) to prevent file read race conditions during local concurrent API requests.
- 💓 **Autonomous 60-Day Keepalive:** A native GitHub Actions workflow monitor prevents GitHub from automatically disabling scheduled cron jobs after 60 days of inactivity.

---

## 📂 Repository Architecture & File Structure

```
📂 QuarkFX Forex Economic Calendar/
├── ⚙️ .github/
│   └── workflows/
│       └── 🤖 scrape_cron.yml       # 15-minute autonomous GitHub Actions workflow
├── 🌐 output/                       # Edge CDN datasets (Initial seeds)
│   ├── 📊 forexfactory_21days.json
│   ├── ⚡ forexfactory_thisweek.json
│   ├── 📈 myfxbook_21days.json
│   └── 🔥 myfxbook_thisweek.json
├── 🖼️ icons/                         # Logo, Prop firms (FTMO, FundedNext, etc.) & platform badges
├── 📜 scripts/                       # Core Python engine & scraper modules
│   ├── ⏱️ cron_runner.py            # Optional local continuous scheduler loop
│   ├── 🏭 forex_factory_scraper.py  # Forex Factory parser with TLS Safari impersonation
│   ├── 📖 myfxbook_scraper.py       # Myfxbook parser with SeleniumBase UC + CDP Mode
│   ├── 🚀 scraper.py                # Master orchestrator & change detector
│   └── 🖥️ server.py                 # Optional Flask REST API server with CORS
├── 🙈 .gitignore                    # Local cache, bytecode, IDE settings, AGENTS.md, GEMINI.md ignored
├── 📦 requirements.txt              # Minimal production dependencies
├── ⚖️ LICENSE                       # MIT Open Source License
└── 📖 README.md                     # Complete project documentation
```

---

## ⚖️ License

This project is open-source under the [MIT License](LICENSE). Free for traders, algorithmic developers, and prop firm communities worldwide.

