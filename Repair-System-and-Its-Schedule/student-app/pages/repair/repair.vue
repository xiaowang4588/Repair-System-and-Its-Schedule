<template>
    <view class="page">
        <view class="container">
            <!-- 设备报修信息 -->
            <view class="card">
                <view class="card-title">📝 设备报修</view>
                <view class="form-group">
                    <text class="form-label">故障教室</text>
                    <input class="form-input" v-model="form.classroom"
                           placeholder="请输入教室名称，如：行者楼408" />
                </view>
                <view class="form-group">
                    <text class="form-label">星期几</text>
                    <picker :range="weekdayOptions" range-key="label" @change="onWeekdayChange">
                        <view class="form-select">
                            {{ weekdayOptions[weekdayIndex].label }}
                            <text class="arrow">▼</text>
                        </view>
                    </picker>
                </view>
                <view class="form-group">
                    <text class="form-label">第几节课</text>
                    <picker :range="sectionOptions" range-key="label" @change="onSectionChange">
                        <view class="form-select">
                            {{ sectionOptions[sectionIndex].label }}
                            <text class="arrow">▼</text>
                        </view>
                    </picker>
                </view>
                <button class="btn-match" @click="doAutoFill">🔍 一键匹配</button>

                <!-- 自动填充的课程信息（仅显示） -->
                <view class="info-box" v-if="courseInfo">
                    <view class="info-title">📚 当前课程信息（自动匹配）</view>
                    <view class="info-row">
                        <text class="info-label">课程</text>
                        <text class="info-value">{{ courseInfo.course_name }}</text>
                    </view>
                    <view class="info-row">
                        <text class="info-label">教师</text>
                        <text class="info-value">{{ courseInfo.teacher_name }}（{{ courseInfo.teacher_id }}）</text>
                    </view>
                    <view class="info-row">
                        <text class="info-label">学院</text>
                        <text class="info-value">{{ courseInfo.teacher_college }}</text>
                    </view>
                    <view class="info-row">
                        <text class="info-label">班级</text>
                        <text class="info-value">{{ courseInfo.class_name }}</text>
                    </view>
                </view>
            </view>

            <!-- 报修信息 -->
            <view class="card">
                <view class="card-title">报修信息</view>
                <view class="form-group">
                    <text class="form-label">报修时间</text>
                    <input class="form-input" v-model="form.report_time" placeholder="自动填充" />
                </view>
                <view class="form-group">
                    <text class="form-label">周次</text>
                    <input class="form-input" type="number" v-model="form.week_number" placeholder="自动填充" />
                </view>
                <view class="form-group">
                    <text class="form-label">报修人（教师）</text>
                    <input class="form-input" v-model="form.reporter_name" placeholder="自动匹配，可修改" />
                </view>
                <view class="form-group">
                    <text class="form-label">报修人学院</text>
                    <input class="form-input" v-model="form.reporter_college" placeholder="自动匹配，可修改" />
                </view>
                <view class="form-group">
                    <text class="form-label">报修方式</text>
                    <picker :range="reportMethodOptions" @change="onReportMethodChange">
                        <view class="form-select">
                            {{ form.report_method || '请选择报修方式' }}
                            <text class="arrow">▼</text>
                        </view>
                    </picker>
                </view>
                <view class="form-group">
                    <text class="form-label">是否外聘教师</text>
                    <view class="radio-group">
                        <view class="radio-item" :class="{ active: !form.is_external_teacher }" @click="form.is_external_teacher = false">
                            否
                        </view>
                        <view class="radio-item" :class="{ active: form.is_external_teacher }" @click="form.is_external_teacher = true">
                            是
                        </view>
                    </view>
                </view>
            </view>

            <!-- 故障信息 -->
            <view class="card">
                <view class="card-title">故障信息</view>
                <view class="form-group">
                    <text class="form-label">报修类型</text>
                    <picker :range="faultTypeOptions" @change="onFaultTypeChange">
                        <view class="form-select">
                            {{ form.fault_type || '请选择报修类型' }}
                            <text class="arrow">▼</text>
                        </view>
                    </picker>
                </view>
                <view class="form-group">
                    <text class="form-label">故障原因</text>
                    <textarea class="form-textarea" v-model="form.fault_cause" placeholder="请描述故障现象" />
                </view>
                <view class="form-group">
                    <text class="form-label">处理方式</text>
                    <textarea class="form-textarea" v-model="form.solution" placeholder="请描述处理方式" />
                </view>
                <view class="form-group">
                    <text class="form-label">处理人（学生）</text>
                    <input class="form-input" v-model="form.handler_name" placeholder="登录后自动填入" :disabled="true" />
                </view>
                <view class="form-group">
                    <text class="form-label">是否更换设备</text>
                    <picker :range="deviceReplaceOptions" range-key="label" @change="onDeviceReplaceChange">
                        <view class="form-select">
                            {{ form.is_device_replaced ? '是' : '否' }}
                            <text class="arrow">▼</text>
                        </view>
                    </picker>
                </view>
                <view class="form-group" v-if="form.is_device_replaced">
                    <text class="form-label">设备更换备注</text>
                    <textarea class="form-textarea" v-model="form.device_replace_note" placeholder="请填写更换的设备信息，如：更换了投影仪型号XXX" />
                </view>
            </view>

            <!-- 换教室推荐 -->
            <view class="card" v-if="nearbyRooms.length > 0">
                <view class="card-title">🔄 换教室推荐（同楼栋）</view>
                <view class="recommend-list">
                    <view class="recommend-item" v-for="room in displayedRooms" :key="room.classroom"
                          @click="selectRoom(room.classroom)">
                        <view class="recommend-left">
                            <text class="recommend-name">{{ room.classroom }}</text>
                            <text class="recommend-tag" :class="room.tag === '同层' ? 'tag-same-floor' : 'tag-same-building'">
                                {{ room.tag }}
                            </text>
                        </view>
                        <text class="recommend-action">选用</text>
                    </view>
                </view>
                <view class="show-more" v-if="nearbyRooms.length > 2" @click="showMoreRooms = !showMoreRooms">
                    <text>{{ showMoreRooms ? '收起' : '查看更多推荐（' + (nearbyRooms.length - 2) + '间）' }}</text>
                </view>
            </view>

            <!-- 备注 -->
            <view class="card">
                <view class="card-title">📝 备注（可选）</view>
                <view class="form-group">
                    <text class="form-label">备注文字</text>
                    <textarea class="form-textarea" v-model="form.notes" placeholder="补充说明（可选）" />
                </view>
                <view class="form-group">
                    <text class="form-label">上传图片</text>
                    <view class="image-upload-area">
                        <view class="image-list">
                            <view class="image-item" v-for="(img, index) in form.note_images" :key="index">
                                <image :src="img" mode="aspectFill" class="preview-image" />
                                <view class="image-delete" @click="deleteImage(index)">×</view>
                            </view>
                            <view class="image-add" @click="chooseImage" v-if="form.note_images.length < 3">
                                <text class="add-icon">📷</text>
                                <text class="add-text">点击或拖拽添加</text>
                            </view>
                        </view>
                        <text class="image-hint">最多上传3张图片，支持拖拽上传</text>
                    </view>
                </view>
            </view>

            <!-- 提交按钮 -->
            <button class="btn-primary submit-btn" @click="submitRepair">📝 提交报修单</button>
        </view>
    </view>
</template>

<script>
import config from '../../config/index.js'
const API_BASE = config.API_BASE

export default {
    data() {
        return {
            courseInfo: null,
            nearbyRooms: [],
            showMoreRooms: false,
            weekdayIndex: 0,
            sectionIndex: 0,
            weekdayOptions: [
                { label: '周一（1）', value: '1' },
                { label: '周二（2）', value: '2' },
                { label: '周三（3）', value: '3' },
                { label: '周四（4）', value: '4' },
                { label: '周五（5）', value: '5' },
                { label: '周六（6）', value: '6' },
                { label: '周日（7）', value: '7' }
            ],
            sectionOptions: [
                { label: '1-2节（08:00-09:40）', value: '1-2节' },
                { label: '3-4节（10:05-11:45）', value: '3-4节' },
                { label: '5-6节（14:00-15:40）', value: '5-6节' },
                { label: '7-8节（16:05-17:45）', value: '7-8节' },
                { label: '9-10节（19:00-20:40）', value: '9-10节' },
                { label: '11-12节（20:50-22:30）', value: '11-12节' }
            ],
            faultTypeOptions: ['中控', '电脑', '投影仪', '音响', '麦克风', '展台', '幕布', '网络', '软件', '其他'],
            reportMethodOptions: ['多媒体报修群', '电话', '其他'],
            deviceReplaceOptions: [
                { label: '否', value: false },
                { label: '是', value: true }
            ],
            form: {
                classroom: '',
                weekday: '1',
                section: '1-2节',
                report_time: '',
                week_number: '',
                student_id: uni.getStorageSync('student_id') || '',
                student_name: uni.getStorageSync('student_name') || '',
                reporter_name: '',
                reporter_college: '',
                report_method: '多媒体报修群',
                is_external_teacher: false,
                fault_type: '',
                fault_cause: '',
                solution: '',
                handler_name: uni.getStorageSync('student_name') || '',
                status: '未处理',
                is_device_replaced: false,
                device_replace_note: '',
                new_classroom: '',
                notes: '',
                note_images: [],
            }
        }
    },
    computed: {
        // 显示的推荐教室（默认显示2个，点击查看更多显示全部）
        displayedRooms() {
            if (this.showMoreRooms) {
                return this.nearbyRooms
            }
            return this.nearbyRooms.slice(0, 2)
        }
    },
    onLoad() {
        this.initData()
    },
    methods: {
        // 初始化数据
        async initData() {
            // 获取当前时间
            try {
                const res = await this.apiGet('/api/time')
                if (res && res.status === 'ok') {
                    // 只取日期部分（年-月-日）
                    this.form.report_time = res.data.current_time ? res.data.current_time.substring(0, 10) : ''

                    // 自动选中当前星期
                    const weekday = res.data.weekday
                    const weekdayIndex = this.weekdayOptions.findIndex(opt => opt.value === String(weekday))
                    if (weekdayIndex >= 0) {
                        this.weekdayIndex = weekdayIndex
                        this.form.weekday = String(weekday)
                    }

                    // 自动选中当前节次
                    if (res.data.current_section) {
                        const sectionIndex = this.sectionOptions.findIndex(opt => opt.value === res.data.current_section)
                        if (sectionIndex >= 0) {
                            this.sectionIndex = sectionIndex
                            this.form.section = res.data.current_section
                        }
                    }
                }
            } catch (e) {
                console.error('获取时间失败:', e)
            }

            // 获取当前周次（与教师端周次管理同步）
            try {
                const res = await this.apiGet('/api/current-week')
                if (res && res.status === 'ok' && res.data.current_week) {
                    this.form.week_number = res.data.current_week
                }
            } catch (e) {
                console.error('获取周次失败:', e)
            }
        },

        // 星期选择
        onWeekdayChange(e) {
            this.weekdayIndex = e.detail.value
            this.form.weekday = this.weekdayOptions[e.detail.value].value
        },

        // 节次选择
        onSectionChange(e) {
            this.sectionIndex = e.detail.value
            this.form.section = this.sectionOptions[e.detail.value].value
        },

        // 一键匹配按钮
        async doAutoFill() {
            const classroom = this.form.classroom.trim()
            if (!classroom) {
                uni.showToast({ title: '请先输入教室名称', icon: 'none' })
                return
            }

            uni.showLoading({ title: '匹配中...' })
            await this.autoFill(classroom)
            await this.getNearbyRooms(classroom)
            uni.hideLoading()
        },

        // 自动填充
        async autoFill(classroom) {
            try {
                // 获取当前时间（只取日期）
                const timeRes = await this.apiGet('/api/time')
                if (timeRes && timeRes.status === 'ok') {
                    this.form.report_time = timeRes.data.current_time ? timeRes.data.current_time.substring(0, 10) : ''
                }

                // 调用自动填充接口，传入教室、星期、节次
                const res = await this.apiGet('/api/repair/auto-fill', {
                    classroom: classroom,
                    weekday: this.form.weekday,
                    section: this.form.section
                })
                if (res && res.status === 'ok') {
                    const data = res.data

                    // 填充周次
                    if (data.week_number) {
                        this.form.week_number = data.week_number
                    }

                    // 填充时间
                    if (data.report_time) {
                        this.form.report_time = data.report_time
                    }

                    // 填充课程信息
                    if (data.course_info) {
                        this.courseInfo = data.course_info
                        this.form.reporter_name = data.course_info.teacher_name || ''
                        this.form.reporter_college = data.course_info.teacher_college || ''
                        uni.showToast({ title: '已匹配到课程信息', icon: 'success' })
                    } else {
                        this.courseInfo = null
                        uni.showToast({ title: '未匹配到课程，请手动填写', icon: 'none' })
                    }
                }
            } catch (e) {
                console.error('自动填充失败:', e)
                uni.showToast({ title: '自动填充失败', icon: 'none' })
            }
        },

        // 获取空教室推荐
        async getNearbyRooms(classroom) {
            try {
                const res = await this.apiGet('/api/repair/nearby-rooms', {
                    classroom: classroom,
                    weekday: this.form.weekday,
                    section: this.form.section
                })

                if (res && res.status === 'ok') {
                    this.nearbyRooms = res.data.recommendations || []
                }
            } catch (e) {
                console.error('获取空教室失败:', e)
            }
        },

        // 选择推荐的教室
        selectRoom(classroom) {
            this.form.new_classroom = classroom
            uni.showToast({ title: `已选择 ${classroom}`, icon: 'success' })
        },

        // 报修类型选择
        onFaultTypeChange(e) {
            this.form.fault_type = this.faultTypeOptions[e.detail.value]
        },

        onReportMethodChange(e) {
            this.form.report_method = this.reportMethodOptions[e.detail.value]
        },

        // 设备更换选择
        onDeviceReplaceChange(e) {
            const index = e.detail.value
            this.form.is_device_replaced = this.deviceReplaceOptions[index].value
            if (!this.form.is_device_replaced) {
                this.form.device_replace_note = ''
            }
        },

        // 选择图片
        chooseImage() {
            uni.chooseImage({
                count: 3 - this.form.note_images.length,
                sizeType: ['compressed'],
                sourceType: ['album', 'camera'],
                success: async (res) => {
                    for (const tempPath of res.tempFilePaths) {
                        // 校验文件大小（最大10MB）
                        try {
                            const fileInfo = await new Promise((resolve, reject) => {
                                uni.getFileInfo({
                                    filePath: tempPath,
                                    success: resolve,
                                    fail: reject
                                })
                            })

                            if (fileInfo.size > 10 * 1024 * 1024) {
                                uni.showToast({ title: '图片大小不能超过10MB', icon: 'none' })
                                continue
                            }

                            // 校验文件格式
                            const allowedExtensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
                            const ext = tempPath.substring(tempPath.lastIndexOf('.')).toLowerCase()
                            if (!allowedExtensions.includes(ext)) {
                                uni.showToast({ title: '只支持jpg/png/gif/webp格式', icon: 'none' })
                                continue
                            }

                            const uploadRes = await this.uploadFile(tempPath)
                            if (uploadRes && uploadRes.status === 'ok') {
                                // 只存储相对路径，不包含 API_BASE
                                this.form.note_images.push(uploadRes.data.url)
                            }
                        } catch (e) {
                            uni.showToast({ title: '图片上传失败', icon: 'none' })
                        }
                    }
                }
            })
        },

        // 删除图片
        deleteImage(index) {
            this.form.note_images.splice(index, 1)
        },

        // 提交报修
        async submitRepair() {
            // 验证必填字段
            if (!this.form.classroom.trim()) {
                uni.showToast({ title: '请输入故障教室', icon: 'none' })
                return
            }
            if (!this.form.reporter_name.trim()) {
                uni.showToast({ title: '请填写报修人', icon: 'none' })
                return
            }
            if (!this.form.fault_type) {
                uni.showToast({ title: '请选择报修类型', icon: 'none' })
                return
            }
            if (!this.form.handler_name.trim()) {
                uni.showToast({ title: '请填写处理人', icon: 'none' })
                return
            }

            uni.showLoading({ title: '提交中...' })
            try {
                const res = await this.apiPost('/api/repair/create', this.form)
                if (res && res.status === 'ok') {
                    uni.showToast({ title: '报修提交成功', icon: 'success' })
                    setTimeout(() => {
                        uni.navigateTo({ url: '/pages/repair/list' })
                    }, 1500)
                } else {
                    uni.showToast({ title: res.message || '提交失败', icon: 'none' })
                }
            } catch (e) {
                uni.showToast({ title: '提交失败', icon: 'none' })
            } finally {
                uni.hideLoading()
            }
        },

        // ============================================================
        // API 请求封装
        // ============================================================
        apiGet(url, params = {}) {
            return new Promise((resolve, reject) => {
                // 构建查询参数
                let queryString = Object.keys(params)
                    .filter(key => params[key] !== undefined && params[key] !== '')
                    .map(key => `${encodeURIComponent(key)}=${encodeURIComponent(params[key])}`)
                    .join('&')

                const fullUrl = queryString ? `${API_BASE}${url}?${queryString}` : `${API_BASE}${url}`

                uni.request({
                    url: fullUrl,
                    method: 'GET',
                    header: {
                        'Content-Type': 'application/json'
                    },
                    success: (res) => {
                        if (res.statusCode === 200) {
                            resolve(res.data)
                        } else {
                            console.error('API错误:', res.statusCode, res.data)
                            resolve(null)
                        }
                    },
                    fail: (err) => {
                        console.error('请求失败:', err)
                        reject(err)
                    }
                })
            })
        },

        apiPost(url, data = {}) {
            return new Promise((resolve, reject) => {
                uni.request({
                    url: API_BASE + url,
                    method: 'POST',
                    data: data,
                    header: {
                        'Content-Type': 'application/json'
                    },
                    success: (res) => {
                        if (res.statusCode === 200) {
                            resolve(res.data)
                        } else {
                            const errMsg = res.data?.message || `请求失败(${res.statusCode})`
                            console.error('API错误:', res.statusCode, res.data)
                            reject(new Error(errMsg))
                        }
                    },
                    fail: (err) => {
                        console.error('请求失败:', err)
                        reject(new Error('网络请求失败'))
                    }
                })
            })
        },

        uploadFile(filePath) {
            return new Promise((resolve, reject) => {
                uni.uploadFile({
                    url: API_BASE + '/api/repair/upload-image',
                    filePath: filePath,
                    name: 'file',
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
            })
        }
    }
}
</script>

<style scoped>
.page {
    min-height: 100vh;
    background: #F5F7FA;
}

.container {
    padding: 24rpx;
    padding-bottom: 120rpx;
}

.card {
    background: white;
    border-radius: 16rpx;
    padding: 32rpx;
    margin-bottom: 24rpx;
    box-shadow: 0 2rpx 8rpx rgba(0,0,0,0.06);
}

.card-title {
    font-size: 32rpx;
    font-weight: 600;
    color: #333;
    margin-bottom: 24rpx;
    padding-bottom: 16rpx;
    border-bottom: 1rpx solid #f0f0f0;
}

.form-group {
    margin-bottom: 24rpx;
}

.form-label {
    font-size: 28rpx;
    color: #555;
    margin-bottom: 12rpx;
    display: block;
}

.form-input {
    width: 100%;
    height: 88rpx;
    padding: 0 24rpx;
    border: 1rpx solid #d9d9d9;
    border-radius: 12rpx;
    font-size: 28rpx;
    background: #fafafa;
    box-sizing: border-box;
}

.form-input:focus {
    border-color: #4F7CFF;
    background: white;
}

.classroom-input-row {
    display: flex;
    gap: 16rpx;
    align-items: center;
}

.classroom-input {
    flex: 1;
}

.btn-match {
    width: 100%;
    height: 88rpx;
    line-height: 88rpx;
    background: #4F7CFF;
    color: white;
    border: none;
    border-radius: 12rpx;
    font-size: 30rpx;
    font-weight: 500;
    text-align: center;
    margin-top: 16rpx;
}

.btn-match:active {
    opacity: 0.8;
}

.form-select {
    display: flex;
    justify-content: space-between;
    align-items: center;
    width: 100%;
    height: 88rpx;
    padding: 0 24rpx;
    border: 1rpx solid #d9d9d9;
    border-radius: 12rpx;
    font-size: 28rpx;
    background: #fafafa;
    box-sizing: border-box;
}

.arrow {
    font-size: 24rpx;
    color: #999;
}

.form-textarea {
    width: 100%;
    height: 160rpx;
    padding: 16rpx 24rpx;
    border: 1rpx solid #d9d9d9;
    border-radius: 12rpx;
    font-size: 28rpx;
    background: #fafafa;
    box-sizing: border-box;
}

.info-box {
    background: #f8f9ff;
    border: 1rpx solid #e0e6ff;
    border-radius: 12rpx;
    padding: 20rpx;
    margin-top: 16rpx;
}

.info-title {
    font-size: 26rpx;
    font-weight: 600;
    color: #4F7CFF;
    margin-bottom: 12rpx;
}

.info-row {
    display: flex;
    padding: 8rpx 0;
    font-size: 26rpx;
}

.info-label {
    width: 80rpx;
    color: #999;
}

.info-value {
    flex: 1;
    color: #333;
}

.radio-group {
    display: flex;
    gap: 16rpx;
}

.radio-item {
    flex: 1;
    height: 80rpx;
    line-height: 80rpx;
    text-align: center;
    border: 1rpx solid #d9d9d9;
    border-radius: 12rpx;
    font-size: 28rpx;
    color: #666;
    background: white;
}

.radio-item.active {
    background: #4F7CFF;
    color: white;
    border-color: #4F7CFF;
}

.recommend-list {
    margin-top: 16rpx;
}

.recommend-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 20rpx;
    background: #f8f9ff;
    border-radius: 12rpx;
    margin-bottom: 12rpx;
}

.recommend-left {
    display: flex;
    align-items: center;
    gap: 12rpx;
}

.recommend-name {
    font-size: 28rpx;
    font-weight: 600;
    color: #333;
}

.recommend-tag {
    padding: 4rpx 12rpx;
    border-radius: 8rpx;
    font-size: 22rpx;
}

.tag-same-floor {
    background: #f6ffed;
    border: 1rpx solid #b7eb8f;
    color: #389e0d;
}

.tag-same-building {
    background: #e6f7ff;
    border: 1rpx solid #91d5ff;
    color: #1890ff;
}

.recommend-action {
    color: #4F7CFF;
    font-size: 28rpx;
    font-weight: 500;
}

.show-more {
    text-align: center;
    padding: 16rpx 0;
    color: #4F7CFF;
    font-size: 26rpx;
    cursor: pointer;
}

.show-more:active {
    opacity: 0.7;
}

.image-upload-area {
    margin-top: 8rpx;
}

.image-list {
    display: flex;
    flex-wrap: wrap;
    gap: 16rpx;
}

.image-item {
    position: relative;
    width: 160rpx;
    height: 160rpx;
}

.preview-image {
    width: 100%;
    height: 100%;
    border-radius: 8rpx;
}

.image-delete {
    position: absolute;
    top: -12rpx;
    right: -12rpx;
    width: 36rpx;
    height: 36rpx;
    background: #ff4d4f;
    color: white;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 24rpx;
}

.image-add {
    width: 160rpx;
    height: 160rpx;
    border: 2rpx dashed #d9d9d9;
    border-radius: 8rpx;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 8rpx;
}

.image-add:active {
    border-color: #4F7CFF;
    background: #f8f9ff;
}

.add-icon {
    font-size: 40rpx;
}

.add-text {
    font-size: 22rpx;
    color: #999;
}

.image-hint {
    font-size: 22rpx;
    color: #999;
    margin-top: 8rpx;
}

.submit-btn {
    position: fixed;
    bottom: 24rpx;
    left: 24rpx;
    right: 24rpx;
    z-index: 100;
    height: 88rpx;
    line-height: 88rpx;
    background: #4F7CFF;
    color: white;
    border: none;
    border-radius: 12rpx;
    font-size: 32rpx;
    font-weight: 500;
}

.submit-btn:active {
    opacity: 0.8;
}
</style>
