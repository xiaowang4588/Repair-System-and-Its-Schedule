/**
 * 应用配置
 * 修改此处即可切换环境，无需逐个文件改
 */

// 后端 API 地址
// 开发环境：http://localhost:5000
// 生产环境：你的服务器地址（建议用 HTTPS）
const API_BASE = 'http://106.55.154.144:5000'

// 说明：
// 1. 部署时把上面的地址改为你的实际服务器地址
// 2. 如果服务器配了 HTTPS 证书，改为 https://xxx
// 3. 后端 .env 的 ALLOWED_ORIGINS 要包含这个地址，否则 CORS 会拦截

export default {
    API_BASE
}
