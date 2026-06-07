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
            <view class="submit-section">
                <button class="submit-btn" @click="submitRepair">📝 提交报修单</button>
            </view>
        </view>
    </view>
</template>

<script>
import config, { getImageUrl as resolveImageUrl } from '../../config/index.js'
import { request, post, uploadImage } from '../../api/index.js'

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
                const res = await request('/api/time')
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
                const res = await request('/api/current-week')
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
                const timeRes = await request('/api/time')
                if (timeRes && timeRes.status === 'ok') {
                    this.form.report_time = timeRes.data.current_time ? timeRes.data.current_time.substring(0, 10) : ''
                }

                // 调用自动填充接口，传入教室、星期、节次
                const res = await request('/api/repair/auto-fill', {
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
                const res = await request('/api/repair/nearby-rooms', {
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
            const maxCount = 3 - this.form.note_images.length
            if (maxCount <= 0) {
                uni.showToast({ title: '最多上传3张图片', icon: 'none' })
                return
            }
            uni.chooseImage({
                count: maxCount,
                sizeType: ['compressed'],
                sourceType: ['album', 'camera'],
                success: async (res) => {
                    for (const tempPath of res.tempFilePaths) {
                        uni.showLoading({ title: '上传中...' })
                        try {
                            // 跳过客户端文件类型校验：uni.chooseImage 在不同平台返回的
                            // tempPath 格式各异（Android content URI、H5 blob URL 等），
                            // 无法可靠提取扩展名。格式校验统一由后端 /api/repair/upload-image 完成。
                            const uploadRes = await uploadImage(tempPath)
                            if (uploadRes && uploadRes.status === 'ok') {
                                // 只存储相对路径，不包含 API_BASE
                                this.form.note_images.push(uploadRes.data.url)
                                uni.showToast({ title: '上传成功', icon: 'success', duration: 1000 })
                            } else {
                                uni.showToast({ title: uploadRes?.message || '上传失败', icon: 'none' })
                            }
                        } catch (e) {
                            console.error('图片上传异常:', e)
                            uni.showToast({ title: '上传失败，请检查网络', icon: 'none' })
                        } finally {
                            uni.hideLoading()
                        }
                    }
                },
                fail: (err) => {
                    console.error('选择图片失败:', err)
                    uni.showToast({ title: '选择图片失败', icon: 'none' })
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
                const res = await post('/api/repair/create', this.form)
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

    }
}
</script>

<style scoped>
.page {
    min-height: 100vh;
    background: var(--color-bg);
}

.container {
    padding: 24rpx;
    padding-bottom: 40rpx;
}

/* ---- 卡片 ---- */
.card {
    background: var(--color-surface);
    border-radius: var(--radius-lg);
    padding: 32rpx;
    margin-bottom: 20rpx;
    box-shadow: var(--shadow-sm);
    border: 1rpx solid var(--color-border-light);
    transition: all var(--transition-normal);
}
.card:active {
    box-shadow: var(--shadow-xs);
    transform: scale(0.985);
}

.card-title {
    font-size: 30rpx;
    font-weight: 700;
    color: var(--color-text);
    margin-bottom: 24rpx;
    padding-bottom: 16rpx;
    border-bottom: 1rpx solid var(--color-divider);
    display: flex;
    align-items: center;
    gap: 8rpx;
}

.form-group {
    margin-bottom: 24rpx;
}

.form-label {
    font-size: 26rpx;
    color: var(--color-text-secondary);
    margin-bottom: 10rpx;
    display: block;
    font-weight: 500;
}

.form-input {
    width: 100%;
    height: 88rpx;
    padding: 0 24rpx;
    border: 2rpx solid var(--color-border);
    border-radius: var(--radius-sm);
    font-size: 28rpx;
    color: var(--color-text);
    background: var(--color-bg-secondary);
    box-sizing: border-box;
    transition: all var(--transition-fast);
}
.form-input:focus {
    border-color: var(--color-primary);
    background: var(--color-surface);
    box-shadow: 0 0 0 6rpx rgba(108, 92, 231, 0.06);
}
.form-input:disabled {
    opacity: 0.6;
    background: var(--color-bg);
}

/* ---- 一键匹配按钮 ---- */
.btn-match {
    width: 100%;
    height: 88rpx;
    line-height: 88rpx;
    background: var(--color-accent-gradient);
    color: white;
    border: none;
    border-radius: var(--radius-sm);
    font-size: 30rpx;
    font-weight: 600;
    text-align: center;
    margin-top: 16rpx;
    box-shadow: 0 4rpx 16rpx rgba(79, 124, 255, 0.25);
    transition: all var(--transition-fast);
    position: relative;
    overflow: hidden;
}
.btn-match::after {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0; bottom: 0;
    background: linear-gradient(135deg, transparent 0%, rgba(255,255,255,0.18) 50%, transparent 100%);
    opacity: 0;
    transition: opacity var(--transition-fast);
}
.btn-match:active {
    transform: translateY(2rpx);
    box-shadow: 0 2rpx 8rpx rgba(79, 124, 255, 0.15);
}
.btn-match:active::after {
    opacity: 1;
}

.form-select {
    display: flex;
    justify-content: space-between;
    align-items: center;
    width: 100%;
    height: 88rpx;
    padding: 0 24rpx;
    border: 2rpx solid var(--color-border);
    border-radius: var(--radius-sm);
    font-size: 28rpx;
    color: var(--color-text);
    background: var(--color-bg-secondary);
    box-sizing: border-box;
    transition: all var(--transition-fast);
}
.form-select:active {
    border-color: var(--color-primary-light);
    background: var(--color-primary-bg);
}

.arrow {
    font-size: 20rpx;
    color: var(--color-text-tertiary);
    transition: transform var(--transition-fast);
}
.form-select:active .arrow {
    color: var(--color-primary);
}

.form-textarea {
    width: 100%;
    height: 160rpx;
    padding: 16rpx 24rpx;
    border: 2rpx solid var(--color-border);
    border-radius: var(--radius-sm);
    font-size: 28rpx;
    color: var(--color-text);
    background: var(--color-bg-secondary);
    box-sizing: border-box;
    transition: all var(--transition-fast);
    line-height: 1.6;
}
.form-textarea:focus {
    border-color: var(--color-primary);
    background: var(--color-surface);
    box-shadow: 0 0 0 6rpx rgba(108, 92, 231, 0.06);
}

/* ---- 课程信息卡片 ---- */
.info-box {
    background: var(--color-primary-bg);
    border: 1rpx solid rgba(108, 92, 231, 0.12);
    border-radius: var(--radius-sm);
    padding: 20rpx 20rpx 20rpx 28rpx;
    margin-top: 16rpx;
    border-left: 6rpx solid var(--color-primary);
}

.info-title {
    font-size: 26rpx;
    font-weight: 600;
    color: var(--color-primary);
    margin-bottom: 12rpx;
}

.info-row {
    display: flex;
    padding: 8rpx 0;
    font-size: 26rpx;
}
.info-label {
    width: 80rpx;
    color: var(--color-text-tertiary);
    flex-shrink: 0;
}
.info-value {
    flex: 1;
    color: var(--color-text);
    font-weight: 500;
}

/* ---- 单选按钮组 ---- */
.radio-group {
    display: flex;
    gap: 12rpx;
}

.radio-item {
    flex: 1;
    height: 80rpx;
    line-height: 80rpx;
    text-align: center;
    border: 2rpx solid var(--color-border);
    border-radius: var(--radius-sm);
    font-size: 28rpx;
    color: var(--color-text-secondary);
    background: var(--color-surface);
    transition: all var(--transition-fast);
    font-weight: 500;
}
.radio-item.active {
    background: var(--color-primary-bg);
    color: var(--color-primary);
    border-color: var(--color-primary);
    font-weight: 600;
    box-shadow: 0 0 0 4rpx rgba(108, 92, 231, 0.08);
}

/* ---- 推荐列表 ---- */
.recommend-list {
    margin-top: 12rpx;
}

.recommend-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 20rpx;
    background: var(--color-primary-bg);
    border-radius: var(--radius-sm);
    margin-bottom: 10rpx;
    border: 1rpx solid rgba(108, 92, 231, 0.08);
    transition: all var(--transition-fast);
}
.recommend-item:active {
    transform: scale(0.98);
    background: var(--color-accent-light);
    box-shadow: var(--shadow-xs);
}

.recommend-left {
    display: flex;
    align-items: center;
    gap: 12rpx;
}

.recommend-name {
    font-size: 28rpx;
    font-weight: 600;
    color: var(--color-text);
}

.recommend-tag {
    padding: 4rpx 12rpx;
    border-radius: var(--radius-xs);
    font-size: 20rpx;
    font-weight: 500;
}
.tag-same-floor {
    background: var(--color-success-bg);
    color: var(--color-success);
}
.tag-same-building {
    background: var(--color-info-bg);
    color: var(--color-info);
}

.recommend-action {
    color: var(--color-primary);
    font-size: 26rpx;
    font-weight: 600;
    padding: 6rpx 16rpx;
    background: rgba(108, 92, 231, 0.08);
    border-radius: var(--radius-xs);
    transition: all var(--transition-fast);
}
.recommend-item:active .recommend-action {
    background: var(--color-primary);
    color: white;
}

.show-more {
    text-align: center;
    padding: 16rpx 0;
    color: var(--color-primary);
    font-size: 26rpx;
    font-weight: 500;
    border-radius: var(--radius-sm);
    transition: all var(--transition-fast);
}
.show-more:active {
    opacity: 0.7;
    background: var(--color-primary-bg);
}

/* ---- 图片上传 ---- */
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
    border-radius: var(--radius-sm);
    border: 1rpx solid var(--color-border);
    box-shadow: var(--shadow-xs);
}

.image-delete {
    position: absolute;
    top: -12rpx;
    right: -12rpx;
    width: 40rpx;
    height: 40rpx;
    background: var(--color-danger);
    color: white;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 24rpx;
    box-shadow: 0 2rpx 10rpx rgba(239, 68, 68, 0.35);
    transition: all var(--transition-fast);
}
.image-delete:active {
    transform: scale(0.85);
    box-shadow: 0 1rpx 4rpx rgba(239, 68, 68, 0.2);
}

.image-add {
    width: 160rpx;
    height: 160rpx;
    border: 2rpx dashed var(--color-border);
    border-radius: var(--radius-sm);
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 8rpx;
    background: var(--color-bg-secondary);
    transition: all var(--transition-fast);
}
.image-add:active {
    border-color: var(--color-primary-light);
    background: var(--color-primary-bg);
    border-style: solid;
    transform: scale(0.95);
}

.add-icon { font-size: 38rpx; opacity: 0.6; }
.add-text { font-size: 22rpx; color: var(--color-text-tertiary); }
.image-hint {
    font-size: 22rpx;
    color: var(--color-text-tertiary);
    margin-top: 8rpx;
}

/* ---- 提交按钮区域 ---- */
.submit-section {
    margin-top: 8rpx;
    padding: 0;
}

.submit-btn {
    width: 100%;
    height: 96rpx;
    line-height: 96rpx;
    background: var(--color-primary-gradient);
    color: white;
    border: none;
    border-radius: var(--radius-md);
    font-size: 32rpx;
    font-weight: 600;
    letter-spacing: 2rpx;
    box-shadow: 0 8rpx 28rpx rgba(108, 92, 231, 0.35);
    transition: all var(--transition-fast);
    position: relative;
    overflow: hidden;
    box-sizing: border-box;
}
.submit-btn::after {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0; bottom: 0;
    background: linear-gradient(135deg, transparent 0%, rgba(255,255,255,0.15) 50%, transparent 100%);
    opacity: 0;
    transition: opacity var(--transition-fast);
}
.submit-btn:active {
    transform: scale(0.97);
    box-shadow: 0 4rpx 12rpx rgba(108, 92, 231, 0.2);
}
.submit-btn:active::after {
    opacity: 1;
}
</style>
