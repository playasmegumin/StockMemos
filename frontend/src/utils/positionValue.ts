import type { Stock } from '@/types/stock'
import { getPrice } from '@/api/market'
import { getKline } from '@/api/market'
import { getTransactionsByStock } from '@/api/transactions'
import { toCNY } from '@/config/exchangeRates'

export interface PositionValue {
  price: number       // raw price in stock's currency
  value: number       // price * position * exchange rate (converted to CNY)
  source: 'current' | 'kline' | 'average_buy' | 'none'
  currency: string    // stock's currency (CNY/HKD/USD)
  rate: number        // exchange rate used for conversion
}

/**
 * Computes position market value for a stock with three-tier fallback.
 * Value = exchangeRate × price × position (converted to CNY).
 */
export async function computePositionValue(stock: Stock): Promise<PositionValue> {
  if (stock.position <= 0) {
    return { price: 0, value: 0, source: 'none', currency: stock.currency, rate: 0 }
  }

  let price = 0
  let source: PositionValue['source'] = 'none'

  // Tier 1: Current price
  const priceR = await getPrice(stock.id)
  if (priceR.ok && priceR.data.price > 0) {
    price = priceR.data.price
    source = 'current'
  }

  // Tier 2: Last kline close
  if (source === 'none') {
    const klineR = await getKline(stock.id)
    if (klineR.ok && klineR.data.length > 0) {
      price = klineR.data[klineR.data.length - 1].close
      source = 'kline'
    }
  }

  // Tier 3: Weighted average buy price
  if (source === 'none') {
    const txnR = await getTransactionsByStock(stock.id)
    if (txnR.ok && txnR.data.length > 0) {
      const buys = txnR.data.filter(t => t.quantity > 0)
      if (buys.length > 0) {
        const totalQty = buys.reduce((s, t) => s + t.quantity, 0)
        const totalCost = buys.reduce((s, t) => s + t.quantity * t.price, 0)
        price = totalCost / totalQty
        source = 'average_buy'
      }
    }
  }

  const rate = price > 0 ? toCNY(1, stock.currency) : 0
  return {
    price,
    value: price * stock.position * rate,
    source,
    currency: stock.currency,
    rate,
  }
}

/**
 * Computes position market values for multiple stocks in parallel.
 */
export async function computeAllPositionValues(
  stocks: Stock[],
): Promise<Map<string, PositionValue>> {
  const results = await Promise.all(
    stocks.map(s => computePositionValue(s)),
  )
  const map = new Map<string, PositionValue>()
  stocks.forEach((s, i) => map.set(s.id, results[i]))
  return map
}
