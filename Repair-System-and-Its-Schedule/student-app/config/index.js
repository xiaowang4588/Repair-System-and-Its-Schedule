/**
 * 学生端 API 地址配置
 *
 * 服务器地址统一从项目根目录的 server.json 读取。
 * 换服务器时只需修改 server.json 中的 backend_url，然后重新打包即可。
 */

// 从 server.json 读取后端地址（编译时打包进去）
import serverConfig from '../server.json'
const FALLBACK_URL = serverConfig.backend_url || 'http://localhost:5000'

// 运行时 API 地址（启动后自动获取，不需要手动填）
let API_BASE = ''

/**
 * 初始化配置：从后端获取 API 地址
 * APP 启动时自动调用，不需要手动触发
 */
export async function initConfig() {
    // 直接用 server.json 中的后端地址，不走代理
    // APP 和本地开发都直接请求后端，CORS 已在后端配置
    API_BASE = FALLBACK_URL
    console.log('[CONFIG] API 地址:', API_BASE)
}

/**
 * 获取当前 API 地址
 */
export function getApiBase() {
    return API_BASE
}

/**
 * 获取图片/视频的完整URL
 * 解决 const API_BASE = config.API_BASE 在模块加载时捕获空字符串的问题：
 * 此函数每次调用时实时读取 API_BASE，确保 initConfig() 完成后能正确拼接。
 *
 * @param {string} img - 图片路径（相对路径如 /uploads/xxx.jpg 或完整 http URL）
 * @returns {string} 完整的图片URL
 */
export function getImageUrl(img) {
    if (!img) return ''
    if (img.startsWith('http')) return img
    return API_BASE + img
}

export default {
    get API_BASE() { return API_BASE },
    initConfig,
    getApiBase,
    getImageUrl
}
