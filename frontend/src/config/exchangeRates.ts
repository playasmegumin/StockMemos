/**
 * Currency exchange rates (基准: CNY)
 * 数据来源: 中国人民银行/国家外管局 人民币汇率中间价
 * 更新日期: 2026-07-03
 *
 * 如需后续自动刷新，可替换此文件为动态获取逻辑。
 */
export const EXCHANGE_RATES: Record<string, number> = {
  CNY: 1,
  USD: 6.8047,
  HKD: 0.86754,
  // 扩展其他货币请添加在此处
}

export function toCNY(amount: number, currency: string): number {
  const rate = EXCHANGE_RATES[currency]
  if (rate == null) {
    console.warn(`[exchangeRates] unknown currency: ${currency}, using 1.0`)
    return amount
  }
  return amount * rate
}
