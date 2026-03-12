# CHANGELOG
All notable changes to this project are documented here.

## [2026-03-12] Switch Core Logic to IP-to-Intel
Files changed:
- app.py
- templates/index.html
- templates/results.html
Reason:
Changed the core logic from fetching IPs for a list of domains to fetching location and associated domains for a list of IPs.
Related tests:
Manual verification of IP resolution and geolocation.
