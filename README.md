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

Sectors covered: raw materials (copper foil, e-cloth, resin), CCL, PCB, IC substrate / ABF, CoWoS advanced packaging, optical chips, optical modules, optical infrastructure, glass substrate.

## New energy heatmap

`new_energy_heatmap.json` is also hosted here for the new energy diagram, covering lithium battery, solar, wind, power grid, and hydrogen supply chains.

## Semiconductor heatmap

`scripts/semiconductor_heatmap.py` generates `semiconductor_heatmap.json` with the same data fields, covering the global semiconductor supply chain:

| Sector | Code | Description |
|--------|------|-------------|
| Chip Design | `chip_design` | Logic, RF, and analog IC design houses |
| EDA & IP | `eda_ip` | Design tools and silicon IP providers |
| Foundry | `foundry` | Pure-play wafer foundries |
| Memory | `memory` | DRAM, NAND, and emerging memory |
| Analog & Power | `analog_power` | Analog ICs, IGBT, SiC, GaN power devices |
| Equipment | `equipment` | Wafer fab, test, and assembly equipment |
| Materials | `materials` | Silicon wafers, photoresist, specialty gases, targets |
| OSAT | `osat` | Outsourced semiconductor assembly and test |

The `Semiconductor Heatmap` GitHub Actions workflow runs on weekdays and can also be triggered manually.
