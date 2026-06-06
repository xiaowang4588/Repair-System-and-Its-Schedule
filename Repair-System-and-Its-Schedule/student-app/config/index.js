/**
 * 学生端 API 地址配置
 *
 * ============================================================
 *  本地测试时：
 *    FALLBACK_URL 填 'http://localhost:5000'
 *
 *  打包成 APP 部署时：
 *    FALLBACK_URL 填你的后端服务器地址，例如 'https://api.xxx.com'
 * ============================================================
 *
 * 工作原理：
 *   APP 启动 → 用 FALLBACK_URL 访问后端 /api/config → 获取正式 API 地址 → 后续请求用这个地址
 *   如果后端 .env 中配置了 API_BASE_URL，以后端返回的为准，FALLBACK_URL 只是第一次访问的跳板
 */

// ============================================================
//  【需要修改的地方】
//  本地测试填：'http://localhost:5000'
//  部署上线填：'https://你的后端服务器地址'
// ============================================================
const FALLBACK_URL = 'http://150.109.233.46:5000'


// ============================================================
//  以下代码不需要修改
// ============================================================

// 运行时 API 地址（启动后自动获取，不需要手动填）
let API_BASE = ''

/**
 * 初始化配置：从后端获取 API 地址
 * APP 启动时自动调用，不需要手动触发
 */
export async function initConfig() {
    try {
        // 尝试用当前页面地址访问后端（网页版有效，APP 里 origin 为空）
        const origin = (typeof window !== 'undefined' && window.location && window.location.origin && window.location.origin !== 'null')
            ? window.location.origin : ''

        if (origin) {
            const resp = await new Promise((resolve, reject) => {
                uni.request({
                    url: origin + '/api/config',
                    method: 'GET',
                    timeout: 5000,
                    success: (res) => resolve(res),
                    fail: (err) => reject(err)
                })
            })

            if (resp.statusCode === 200 && resp.data?.data?.api_base_url) {
                API_BASE = resp.data.data.api_base_url
                console.log('[CONFIG] API 地址（from /api/config）:', API_BASE)
                return
            }

            // 后端没有配置 API_BASE_URL，用当前页面地址
            if (origin) {
                API_BASE = origin
                console.log('[CONFIG] API 地址（from origin）:', API_BASE)
                return
            }
        }
    } catch (e) {
        console.warn('[CONFIG] 获取配置失败，使用兜底地址:', e)
    }

    // 兜底：用 FALLBACK_URL
    API_BASE = FALLBACK_URL
    console.log('[CONFIG] API 地址（fallback）:', API_BASE)
}

/**
 * 获取当前 API 地址
 */
export function getApiBase() {
    return API_BASE
}

export default {
    get API_BASE() { return API_BASE },
    initConfig,
    getApiBase
}
