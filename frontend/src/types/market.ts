export interface CurrentPrice {
  symbol: string
  exchange: string
  price: number
  price_time: string | null
  currency: string
  volume: number | null
  source: string
}

export interface DailyKline {
  date: string
  open: number
  high: number
  low: number
  close: number
  volume: number
  amount: number
}
