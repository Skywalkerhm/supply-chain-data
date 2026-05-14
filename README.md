# supply-chain-data

Static JSON data and generators for GitHub Pages heatmaps.

## Supply chain heatmap

`scripts/supply_chain_heatmap.py` generates `supply_chain_heatmap.json` with:

- latest price
- daily percentage change (`change_pct`)
- month-to-date return (`mtd_pct`)
- year-to-date return (`ytd_pct`)
- PE and market cap metadata when available

The `Supply Chain Heatmap` GitHub Actions workflow runs on weekdays and can also be triggered manually.

## New energy heatmap

`new_energy_heatmap.json` is also hosted here for the new energy diagram.
