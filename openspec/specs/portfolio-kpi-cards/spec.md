# Portfolio KPI Cards

**Purpose**: Display portfolio-level summary statistics as KPI cards with colored visual cues.

## Requirements

### Requirement: Display KPI cards with colored left border
The system SHALL display 4 KPI summary cards with a colored left border strip.

#### Scenario: KPI cards rendered
- **WHEN** user opens the portfolio dashboard
- **THEN** 4 KPI cards are displayed in a horizontal row below the treemap
- **THEN** each card has a 3px colored left border
- **THEN** each card shows a label (top) and a value (bottom, large font)

#### Scenario: Card data
- **WHEN** the cards render
- **THEN** the first card shows "收益" with total PnL (orange left border)
- **THEN** the second card shows "股票" with stock count (cyan left border)
- **THEN** the third card shows "总持仓金额" with total position market value (yellow left border)
- **THEN** the fourth card shows "现金" with total invested minus total position (purple left border)

#### Scenario: PnL color coding
- **WHEN** total PnL >= 0
- **THEN** the value text is red (profit)
- **WHEN** total PnL < 0
- **THEN** the value text is green (loss per Chinese convention)
