export interface StockAnalyze {
  id: string
  stock_id: string
  fundamentals_data: Record<string, any> | null
  created_at: string
  updated_at: string
}

export interface Report {
  id: string
  stock_analyze_id: string
  generated_at: string
  title: string
  content: string
  created_at: string
}

export interface TpSlPoint {
  id: string
  stock_analyze_id: string
  price: number
  label: string
  notes: string | null
  created_at: string
}

export interface StockTag {
  id: string
  stock_analyze_id: string
  tag: string
  created_at: string
}
