/**
 * 电影相关工具函数
 */

/**
 * 获取海报完整 URL
 * @param {string} path — TMDB 相对路径或豆瓣完整 URL
 * @param {string} source — 'tmdb' | 'douban'
 * @param {string} size — TMDB 海报尺寸，默认 'w500'
 * @returns {string}
 */
export function getPosterUrl(path, source, size = "w500") {
  if (!path) return "";
  // 豆瓣数据存的是完整 URL，直接返回
  if (source === "douban" && path.startsWith("http")) return path;
  // TMDB 数据拼接 CDN URL
  return `https://image.tmdb.org/t/p/${size}${path}`;
}

/**
 * 10 分制评分 → 5 星制
 * @param {number} voteAverage — 0-10 分
 * @returns {number} 0-5 星
 */
export function toStarRating(voteAverage) {
  if (!voteAverage) return 0;
  return voteAverage / 2;
}

/**
 * 格式化片长
 * @param {number} minutes
 * @returns {string} 如 "2h 19min"
 */
export function formatRuntime(minutes) {
  if (!minutes) return "";
  const h = Math.floor(minutes / 60);
  const m = minutes % 60;
  if (h > 0) return `${h}h ${m}min`;
  return `${m}min`;
}

/**
 * 获取头像完整 URL
 * @param {string} path — TMDB 相对路径
 * @param {string} size — TMDB 头像尺寸，默认 'w92'
 * @returns {string}
 */
export function getProfileUrl(path, size = "w92") {
  if (!path) return "";
  return `https://image.tmdb.org/t/p/${size}${path}`;
}

/**
 * 格式化金额
 * @param {number} amount
 * @returns {string} 如 "$2.8M", "$1.5B"
 */
export function formatMoney(amount) {
  if (!amount) return "—";
  if (amount >= 1_000_000_000)
    return `$${(amount / 1_000_000_000).toFixed(1)}B`;
  if (amount >= 1_000_000) return `$${Math.round(amount / 1_000_000)}M`;
  return `$${amount.toLocaleString()}`;
}
