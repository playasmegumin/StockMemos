# Portfolio Treemap

**Purpose**: Visualize portfolio holdings distribution as a hierarchical treemap, grouped by tag.

## Requirements

### Requirement: Display portfolio treemap
The system SHALL render a treemap visualization showing the distribution of portfolio holdings.

#### Scenario: Treemap renders with data
- **WHEN** user opens the portfolio dashboard
- **THEN** a treemap chart is rendered at the top of the page
- **THEN** each block represents a stock with position > 0
- **THEN** block area is proportional to position market value (position × price × exchange rate)
- **THEN** block color is determined by the stock's primary tag color
- **THEN** stocks without tags are shown in grey

#### Scenario: Empty portfolio
- **WHEN** there are no stocks with position > 0
- **THEN** the treemap area shows a placeholder message "暂无持仓数据"

#### Scenario: Price grade-down chain
- **WHEN** the current price API returns 502/error
- **THEN** the system falls back to the latest kline close price
- **WHEN** no kline data exists
- **THEN** the system calculates weighted average buy price from transaction records
- **WHEN** none of the above yields a price
- **THEN** the stock is excluded from the treemap

### Requirement: Treemap tooltip
The system SHALL display a tooltip when hovering over a treemap block.

#### Scenario: Hover over block
- **WHEN** user hovers over a treemap block
- **THEN** tooltip shows: stock name, code, tag, position market value, PnL, percentage of total

### Requirement: Treemap visual style
The system SHALL render the treemap with a card-style container.

#### Scenario: Visual styling
- **WHEN** the treemap renders
- **THEN** the container has a white background with shadow
- **THEN** block gap is 8px
- **THEN** block corner radius is 8px
- **THEN** the container corner radius is 16px
