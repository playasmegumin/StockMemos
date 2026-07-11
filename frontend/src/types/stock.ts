export interface Stock {
  id: string
  exchange: string
  symbol: string
  name: string
  currency: string
  position: number
  historical_pnl: number
  created_at: string
  updated_at: string
}

export interface StockCreate {
  symbol: string
  name?: string
}

export interface StockUpdate {
  name?: string
  currency?: string
}
