export interface Transaction {
  id: string
  stock_id: string
  quantity: number
  price: number
  gas: number
  traded_at: string
  created_at: string
}

export interface TransactionCreate {
  stock_id: string
  quantity: number
  price: number
  gas?: number
  traded_at: string
}

export interface TransactionUpdate {
  quantity?: number
  price?: number
  gas?: number
  traded_at?: string
}
