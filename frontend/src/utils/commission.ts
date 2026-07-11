/**
 * 交易佣金预填充规则
 *
 * 基于交易交易所和股票代码前缀自动计算默认佣金。
 * 规则同步自 backend 的 stock_classifier。
 */

// 上海基金/ETF 前缀
const SH_FUND_PREFIXES = new Set([
  '510', '511', '512', '513', '515', '517', '518', '520', '530',
  '560', '561', '588',
])

// 深圳基金/ETF 前缀
const SZ_FUND_PREFIXES = new Set([
  '158', '159', '184', '180', '181',
])
const SZ_LOF_RANGE = [160, 169]

function isFund(exchange: string, symbol: string): boolean {
  // 取前 3 位判断
  const prefix = symbol.slice(0, 3)
  if (exchange === 'SH') return SH_FUND_PREFIXES.has(prefix)
  if (exchange === 'SZ') {
    if (SZ_FUND_PREFIXES.has(prefix)) return true
    const num = parseInt(prefix, 10)
    if (num >= SZ_LOF_RANGE[0] && num <= SZ_LOF_RANGE[1]) return true
  }
  return false
}

/**
 * 根据交易所和股票代码计算默认佣金
 */
export function getDefaultGas(exchange: string, symbol: string): number {
  if (exchange === 'SH' || exchange === 'SZ') {
    return isFund(exchange, symbol) ? 0 : 5
  }
  if (exchange === 'HK') return 18
  if (exchange === 'US') return 1.99
  return 0
}
