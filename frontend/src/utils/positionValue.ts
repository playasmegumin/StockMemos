import type { Stock } from '@/types/stock'
import { getPrice } from '@/api/market'
import { getKline } from '@/api/market'
import { getTransactionsByStock } from '@/api/transactions'

export interface PositionValue {
  price: number
  value: number   // price * position
  source: 'current' | 'kline' | 'average_buy' | 'none'
}

/**
 * Computes position market value for a stock with three-tier fallback:
 * 1. Current price API
 * 2. Latest kline close price
 * 3. Weighted average buy price from transactions
 */
export async function computePositionValue(stock: Stock): Promise<PositionValue> {
  if (stock.position <= 0) {
    return { price: 0, value: 0, source: 'none' }
  }

  // Tier 1: Current price
  const priceR = await getPrice(stock.id)
  if (priceR.ok && priceR.data.price > 0) {
    return {
      price: priceR.data.price,
      value: priceR.data.price * stock.position,
      source: 'current',
    }
  }

  // Tier 2: Last kline close
  const klineR = await getKline(stock.id)
  if (klineR.ok && klineR.data.length > 0) {
    const lastClose = klineR.data[klineR.data.length - 1].close
    if (lastClose > 0) {
      return {
        price: lastClose,
        value: lastClose * stock.position,
        source: 'kline',
      }
    }
  }

  // Tier 3: Weighted average buy price
  const txnR = await getTransactionsByStock(stock.id)
  if (txnR.ok && txnR.data.length > 0) {
    const buys = txnR.data.filter(t => t.quantity > 0)
    if (buys.length > 0) {
      const totalQty = buys.reduce((s, t) => s + t.quantity, 0)
      const totalCost = buys.reduce((s, t) => s + t.quantity * t.price, 0)
      const avgPrice = totalCost / totalQty
      return {
        price: avgPrice,
        value: avgPrice * stock.position,
        source: 'average_buy',
      }
    }
  }

  return { price: 0, value: 0, source: 'none' }
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
