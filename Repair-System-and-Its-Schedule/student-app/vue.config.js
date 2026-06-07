/**
 * Uni-app 构建配置
 * devServer 代理从 server.json 读取后端地址，无需手动修改 manifest.json
 */
const fs = require('fs')
const path = require('path')

// 读取 server.json 中的后端地址
let backendUrl = 'http://localhost:5000'
try {
    const serverConfig = JSON.parse(fs.readFileSync(path.resolve(__dirname, 'server.json'), 'utf-8'))
    if (serverConfig.backend_url) backendUrl = serverConfig.backend_url
} catch (e) {
    console.warn('[vue.config.js] 未找到 server.json，使用默认地址:', backendUrl)
}

module.exports = {
    devServer: {
        port: 8080,
        proxy: {
            '/api': {
                target: backendUrl,
                changeOrigin: true
            },
            '/admin': {
                target: backendUrl,
                changeOrigin: true
            }
        }
    }
}
