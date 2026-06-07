/**
 * 报修表填写助手 - API 服务层
 * 封装所有后端 API 调用
 */
import config, { initConfig } from '../config/index.js'

// 配置初始化状态
let _configReady = null

/**
 * 确保配置已初始化（首次请求时自动调用，后续请求直接跳过）
 */
function ensureConfig() {
    if (!_configReady) {
        _configReady = initConfig().catch(() => {})
    }
    return _configReady
}

/**
 * 获取认证头
 * 从本地存储获取token，添加到请求头
 * @returns {Object} 请求头对象
 */
function getAuthHeader() {
    const token = uni.getStorageSync('student_token')
    const header = {
        'Content-Type': 'application/json'
    }
    if (token) {
        header['Authorization'] = `Bearer ${token}`
    }
    return header
}

/**
 * 统一错误处理
 * @param {number} statusCode - HTTP 状态码
 * @param {Object} data - 响应数据
 * @returns {string} 错误信息
 */
function getErrorMessage(statusCode, data) {
    const message = data?.message || data?.error
    switch (statusCode) {
        case 400: return message || '请求参数错误'
        case 401: return '登录已过期，请重新登录'
        case 403: return '没有操作权限'
        case 404: return '请求的资源不存在'
        case 500: return '服务器内部错误，请稍后重试'
        case 502: case 503: case 504:
            return '服务暂时不可用，请稍后重试'
        default: return message || `请求失败(${statusCode})`
    }
}

/**
 * 显示错误提示（防抖，避免多次 toast 重叠）
 */
let lastToastTime = 0
function showErrorToast(message) {
    const now = Date.now()
    if (now - lastToastTime > 2000) {
        lastToastTime = now
        uni.showToast({
            title: message,
            icon: 'none',
            duration: 2500
        })
    }
}

/**
 * 401 跳转登录防重复标记
 */
let _isRedirectingToLogin = false

function handle401(requestUrl) {
    if (_isRedirectingToLogin) return
    _isRedirectingToLogin = true
    console.error('[AUTH] 401 triggered by:', requestUrl)
    console.error('[AUTH] Current token:', uni.getStorageSync('student_token') ? 'exists' : 'MISSING')
    uni.removeStorageSync('student_token')
    uni.removeStorageSync('student_id')
    uni.removeStorageSync('student_name')
    showErrorToast('登录已过期，请重新登录')
    setTimeout(() => {
        uni.reLaunch({
            url: '/pages/login/login',
            complete: () => { _isRedirectingToLogin = false }
        })
    }, 1500)
}

/**
 * 通用请求核心逻辑
 */
async function doRequest(url, method, data, resolve, reject) {
    const isGet = method === 'GET'
    // 等待配置初始化完成，确保 API_BASE 有值
    await ensureConfig()
    let fullUrl = config.API_BASE + url

    if (isGet && data && Object.keys(data).length > 0) {
        const qs = Object.keys(data)
            .filter(key => data[key] !== undefined && data[key] !== '')
            .map(key => `${encodeURIComponent(key)}=${encodeURIComponent(data[key])}`)
            .join('&')
        if (qs) fullUrl += '?' + qs
    }

    uni.request({
        url: fullUrl,
        method: method,
        data: isGet ? undefined : data,
        header: getAuthHeader(),
        success: (res) => {
            if (res.statusCode === 200) {
                resolve(res.data)
            } else if (res.statusCode === 401) {
                handle401(url)
                reject(new Error('登录已过期，请重新登录'))
            } else {
                const errMsg = getErrorMessage(res.statusCode, res.data)
                console.error('API错误:', res.statusCode, res.data)
                showErrorToast(errMsg)
                reject(new Error(errMsg))
            }
        },
        fail: (err) => {
            console.error('请求失败:', err)
            const errMsg = err?.errMsg || ''
            let msg
            if (errMsg.includes('timeout')) {
                msg = '请求超时，请检查网络'
            } else if (errMsg.includes('abort')) {
                msg = '请求已取消'
            } else {
                msg = '网络连接失败，请检查网络'
            }
            showErrorToast(msg)
            reject(new Error(msg))
        }
    })
}

/**
 * 通用 GET 请求
 * @param {string} url - API 路径
 * @param {Object} params - 查询参数
 * @returns {Promise}
 */
export function request(url, params = {}) {
    return ensureConfig().then(() => new Promise((resolve, reject) => {
        doRequest(url, 'GET', params, resolve, reject)
    }))
}

/**
 * 通用 POST 请求
 * @param {string} url - API 路径
 * @param {Object} data - 请求体数据
 * @returns {Promise}
 */
export function post(url, data = {}) {
    return ensureConfig().then(() => new Promise((resolve, reject) => {
        doRequest(url, 'POST', data, resolve, reject)
    }))
}

/**
 * 获取当前时间和节次信息
 */
export function getTime() {
    return request('/api/time')
}

/**
 * 按条件查询课程
 * @param {Object} params - { day_of_week, section, classroom }
 */
export function queryCourses(params) {
    return request('/api/query', params)
}

/**
 * 按课程名称查询
 * @param {string} keyword - 课程名称关键词
 */
export function queryByCourse(keyword) {
    return request('/api/query/course', { keyword })
}

/**
 * 按教师姓名查询
 * @param {string} keyword - 教师姓名关键词
 */
export function queryByTeacher(keyword) {
    return request('/api/query/teacher', { keyword })
}

/**
 * 获取一周课表
 * @param {string} keyword - 班级名称或教师姓名
 * @param {string} type - 'class' 或 'teacher'
 */
export function getWeeklySchedule(keyword, type = 'class') {
    return request('/api/query/weekly', { keyword, type })
}

/**
 * 查询空教室
 * @param {Object} params - { weekday, sections, building, classroom_type, keyword, exclude_special }
 */
export function getEmptyRooms(params) {
    return request('/api/empty-rooms', params)
}

/**
 * 获取楼栋列表
 */
export function getBuildings() {
    return request('/api/buildings')
}

/**
 * 获取统计数据
 */
export function getStats() {
    return request('/api/stats')
}

// ============================================================
// 防坑指南 API
// ============================================================

/**
 * 发布防坑指南
 * @param {Object} data - { content, images, video_url, video_duration, device_tags, location_tag }
 */
export function createGuide(data) {
    return post('/api/guide/create', data)
}

/**
 * 获取动态列表
 * @param {Object} params - { page, page_size, device_tag, location_tag, keyword }
 */
export function getGuideList(params) {
    return request('/api/guide/list', params)
}

/**
 * 获取动态详情
 * @param {number} id - 动态ID
 */
export function getGuideDetail(id) {
    return request('/api/guide/detail', { id })
}

/**
 * 编辑动态
 * @param {Object} data - { id, content, images, video_url, video_duration, device_tags, location_tag }
 */
export function updateGuide(data) {
    return post('/api/guide/update', data)
}

/**
 * 删除动态
 * @param {number} id - 动态ID
 */
export function deleteGuide(id) {
    return post('/api/guide/delete', { id })
}

/**
 * 搜索动态
 * @param {Object} params - { keyword, page, page_size }
 */
export function searchGuide(params) {
    return request('/api/guide/search', params)
}

/**
 * 获取所有标签及数量
 */
export function getGuideTags() {
    return request('/api/guide/tags')
}

/**
 * 获取系统中所有可用的设备标签和地点标签（与项目数据联动）
 */
export function getGuideAvailableTags() {
    return request('/api/guide/available-tags')
}

/**
 * 点赞/取消点赞
 * @param {number} id - 动态ID
 */
export function toggleGuideLike(id) {
    return post('/api/guide/like', { id })
}

/**
 * 发表评论
 * @param {Object} data - { post_id, content, reply_to_id }
 */
export function createGuideComment(data) {
    return post('/api/guide/comment', data)
}

/**
 * 获取评论列表
 * @param {Object} params - { post_id, page, page_size }
 */
export function getGuideComments(params) {
    return request('/api/guide/comment/list', params)
}

/**
 * 删除评论
 * @param {number} id - 评论ID
 */
export function deleteGuideComment(id) {
    return post('/api/guide/comment/delete', { id })
}

/**
 * 收藏/取消收藏
 * @param {number} id - 动态ID
 */
export function toggleGuideFavorite(id) {
    return post('/api/guide/favorite', { id })
}

/**
 * 获取我的发布
 * @param {Object} params - { page, page_size }
 */
export function getMyGuidePosts(params) {
    return request('/api/guide/my-posts', params)
}

/**
 * 获取我的收藏
 * @param {Object} params - { page, page_size }
 */
export function getMyGuideFavorites(params) {
    return request('/api/guide/my-favorites', params)
}

/**
 * 获取防坑指南个人统计
 * 注意：此接口不走全局 401 处理，因为有 student_id 参数兜底，
 * 即使 token 失效（如服务器重启密钥变化）也不会触发强制登出。
 */
export function getGuideStats() {
    ensureConfig()
    const studentId = uni.getStorageSync('student_id') || ''
    const token = uni.getStorageSync('student_token')
    const header = { 'Content-Type': 'application/json' }
    if (token) header['Authorization'] = `Bearer ${token}`

    const qs = `student_id=${encodeURIComponent(studentId)}`
    const fullUrl = `${config.API_BASE}/api/guide/stats?${qs}`

    return new Promise((resolve) => {
        uni.request({
            url: fullUrl,
            method: 'GET',
            header: header,
            success: (res) => {
                if (res.statusCode === 200) {
                    resolve(res.data)
                } else {
                    // 不触发 handle401，静默降级返回空数据
                    resolve({ status: 'ok', data: { post_count: 0, favorite_count: 0 } })
                }
            },
            fail: () => {
                resolve({ status: 'ok', data: { post_count: 0, favorite_count: 0 } })
            }
        })
    })
}

/**
 * 上传视频
 * @param {string} filePath - 临时文件路径
 * @returns {Promise}
 */
export function uploadGuideVideo(filePath) {
    return ensureConfig().then(() => new Promise((resolve, reject) => {
        // 注意：uni.uploadFile 不能设置 Content-Type: application/json
        // 否则会覆盖 multipart/form-data 的 boundary，导致服务器收不到文件
        const token = uni.getStorageSync('student_token')
        const header = {}
        if (token) {
            header['Authorization'] = `Bearer ${token}`
        }
        uni.uploadFile({
            url: config.API_BASE + '/api/guide/upload-video',
            filePath: filePath,
            name: 'file',
            header: header,
            success: (res) => {
                try {
                    const data = JSON.parse(res.data)
                    resolve(data)
                } catch (e) {
                    reject(e)
                }
            },
            fail: (err) => {
                reject(err)
            }
        })
    }))
}

/**
 * 上传报修备注图片
 * @param {string} filePath - 临时文件路径
 * @returns {Promise} 返回 { status, data: { url, filename } }
 */
export function uploadImage(filePath) {
    return ensureConfig().then(() => new Promise((resolve, reject) => {
        const token = uni.getStorageSync('student_token')
        const header = {}
        if (token) {
            header['Authorization'] = `Bearer ${token}`
        }
        uni.uploadFile({
            url: config.API_BASE + '/api/repair/upload-image',
            filePath: filePath,
            name: 'file',
            header: header,
            success: (res) => {
                try {
                    const data = JSON.parse(res.data)
                    resolve(data)
                } catch (e) {
                    reject(e)
                }
            },
            fail: (err) => {
                reject(err)
            }
        })
    }))
}
