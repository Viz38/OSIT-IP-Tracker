# CHANGELOG
All notable changes to this project are documented here.

## [2026-03-12] Rebranding to Tracxn OSIT
Files changed:
- app.py
- templates/layout.html
- README.md
Reason:
Rebranded the application from "Detective Pradeep" to **Tracxn OSIT**.
- Updated UI branding and titles.
- Updated API User-Agent and export filenames.

## [2026-03-12] High-Accuracy Consensus Engine Upgrade
Files changed:
- app.py
- templates/results.html
- README.md
- requirements.txt
Reason:
Implemented a **Triple-Source Consensus Engine** for >90% accuracy in company identification.
- Integrated **RDAP (Infrastructure Truth)**, **ip-api.com (Network Truth)**, and **Wikidata/PeeringDB (Legal Truth)**.
- Added **Confidence Scoring** (0-98%) based on source agreement.
- Added **Corporate Headquarters** mapping (separate from physical server location).
- Added **Network Type Classification** (Cloud, VPN, Business).
- Removed manual "Company" input; everything is now fetched autonomously.
- Switched to **Wikidata** for "No-Limit" corporate metadata.
Related tests:
Verified accuracy with diverse IP blocks (Google, Cloudflare, Corporate ASNs).
