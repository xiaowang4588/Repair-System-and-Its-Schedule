<template>
    <view class="page">
        <view class="container">
            <!-- 全部/我的切换 -->
            <view class="toggle-bar">
                <view class="toggle-item" :class="{ active: listType === 'all' }" @click="switchListType('all')">全部记录</view>
                <view class="toggle-item" :class="{ active: listType === 'my' }" @click="switchListType('my')">我的记录</view>
            </view>

            <!-- 状态筛选 -->
            <view class="filter-bar">
                <view class="filter-item" :class="{ active: currentFilter === 'all' }" @click="setFilter('all')">全部</view>
                <view class="filter-item" :class="{ active: currentFilter === '未处理' }" @click="setFilter('未处理')">待处理</view>
                <view class="filter-item" :class="{ active: currentFilter === '已处理' }" @click="setFilter('已处理')">已处理</view>
            </view>

            <!-- 报修列表 -->
            <view class="repair-list" v-if="records.length > 0">
                <view class="repair-item" v-for="item in records" :key="item.id" @click="viewDetail(item)">
                    <view class="repair-header">
                        <text class="repair-room">{{ item.classroom }}</text>
                        <text class="repair-status" :class="statusClass(item.status)">{{ item.status }}</text>
                    </view>
                    <view class="repair-info">
                        <text>{{ item.fault_type }} · {{ item.status }}</text>
                    </view>
                    <view class="repair-detail-row">
                        <text class="repair-label">报修人：</text>
                        <text class="repair-value">{{ item.reporter_name }}</text>
                    </view>
                    <view class="repair-detail-row" v-if="item.handler_name">
                        <text class="repair-label">处理人：</text>
                        <text class="repair-value">{{ item.handler_name }}</text>
                    </view>
                    <view class="repair-time">{{ item.report_time }}</view>
                    <view class="repair-action">
                        <text class="view-detail-btn">查看详情</text>
                    </view>
                </view>
            </view>

            <!-- 空状态 -->
            <view class="empty" v-else-if="!loading">
                <text class="empty-icon">📋</text>
                <text class="empty-text">暂无报修记录</text>
            </view>

            <!-- 加载中 -->
            <view class="loading" v-if="loading">
                <text>加载中...</text>
            </view>

            <!-- 加载更多 -->
            <view class="load-more" v-if="records.length > 0">
                <view v-if="loadingMore" class="loading">
                    <text>加载更多中...</text>
                </view>
                <view v-else-if="hasMore" @click="loadMore" class="load-more-btn">
                    <text>点击加载更多</text>
                </view>
                <view v-else class="no-more">
                    <text>没有更多数据了</text>
                </view>
            </view>
        </view>

        <!-- 详情弹窗 -->
        <view class="modal-mask" v-if="showDetail" @click="closeDetail">
            <view class="modal-content" @click.stop>
                <view class="modal-header">
                    <text class="modal-title">报修详情</text>
                    <text class="modal-close" @click="closeDetail">✕</text>
                </view>
                <view class="modal-body" v-if="loadingDetail">
                    <view class="loading-spinner-wrap">
                        <view class="spinner-ring"></view>
                        <text>加载中...</text>
                    </view>
                </view>
                <view class="modal-body" v-else-if="detailData">
                    <view class="detail-row">
                        <text class="detail-label">故障教室</text>
                        <text class="detail-value">{{ detailData.classroom || '-' }}</text>
                    </view>
                    <view class="detail-row">
                        <text class="detail-label">报修时间</text>
                        <text class="detail-value">{{ detailData.report_time || '-' }}</text>
                    </view>
                    <view class="detail-row">
                        <text class="detail-label">周次</text>
                        <text class="detail-value">{{ detailData.week_number ? '第' + detailData.week_number + '周' : '-' }}</text>
                    </view>
                    <view class="detail-row">
                        <text class="detail-label">报修类型</text>
                        <text class="detail-value">{{ detailData.fault_type || '-' }}</text>
                    </view>
                    <view class="detail-row">
                        <text class="detail-label">报修人</text>
                        <text class="detail-value">{{ detailData.reporter_name || '-' }}</text>
                    </view>
                    <view class="detail-row">
                        <text class="detail-label">报修人学院</text>
                        <text class="detail-value">{{ detailData.reporter_college || '-' }}</text>
                    </view>
                    <view class="detail-row">
                        <text class="detail-label">外聘教师</text>
                        <text class="detail-value">{{ detailData.is_external_teacher ? '是' : '否' }}</text>
                    </view>
                    <view class="detail-row">
                        <text class="detail-label">报修方式</text>
                        <text class="detail-value">{{ detailData.report_method || '-' }}</text>
                    </view>
                    <view class="detail-row">
                        <text class="detail-label">处理人</text>
                        <text class="detail-value">{{ detailData.handler_name || '-' }}</text>
                    </view>
                    <view class="detail-row">
                        <text class="detail-label">更换设备</text>
                        <text class="detail-value">{{ detailData.is_device_replaced ? '是' : '否' }}{{ detailData.device_replace_note ? ' - ' + detailData.device_replace_note : '' }}</text>
                    </view>
                    <view class="detail-row">
                        <text class="detail-label">处理情况</text>
                        <text class="detail-value">
                            <text class="repair-status" :class="statusClass(detailData.status)">{{ detailData.status || '-' }}</text>
                        </text>
                    </view>
                    <view class="detail-row">
                        <text class="detail-label">故障原因</text>
                        <text class="detail-value">{{ detailData.fault_cause || '-' }}</text>
                    </view>
                    <view class="detail-row">
                        <text class="detail-label">处理方式</text>
                        <text class="detail-value">{{ detailData.solution || '-' }}</text>
                    </view>
                    <view class="detail-row">
                        <text class="detail-label">备注</text>
                        <text class="detail-value">{{ detailData.notes || '-' }}</text>
                    </view>
                    <view class="detail-row" v-if="detailData.handle_time">
                        <text class="detail-label">处理时间</text>
                        <text class="detail-value">{{ detailData.handle_time }}</text>
                    </view>
                </view>
                <!-- 操作按钮：自己的记录且状态为"未处理"时显示 -->
                <view class="modal-footer" v-if="detailData && detailData.status === '未处理' && isMyRecord(detailData)">
                    <view class="edit-btn" @click="openEdit">编辑</view>
                    <view class="delete-btn" @click="deleteRecord(detailData.id)">删除</view>
                </view>
            </view>
        </view>

        <!-- 编辑弹窗 -->
        <view class="modal-mask" v-if="showEdit" @click="closeEdit">
            <view class="modal-content modal-large" @click.stop>
                <view class="modal-header">
                    <text class="modal-title">编辑报修</text>
                    <text class="modal-close" @click="closeEdit">✕</text>
                </view>
                <view class="modal-body">
                    <view class="form-item">
                        <text class="form-label">故障教室</text>
                        <input class="form-input" v-model="editForm.classroom" placeholder="请输入教室" />
                    </view>
                    <view class="form-item">
                        <text class="form-label">报修时间</text>
                        <input class="form-input" v-model="editForm.report_time" placeholder="如：2026-05-30" />
                    </view>
                    <view class="form-item">
                        <text class="form-label">周次</text>
                        <input class="form-input" type="number" v-model="editForm.week_number" placeholder="如：14" />
                    </view>
                    <view class="form-item">
                        <text class="form-label">报修类型</text>
                        <picker :range="faultTypeOptions" @change="onEditFaultTypeChange">
                            <view class="form-select">{{ editForm.fault_type || '请选择' }} <text class="arrow">▼</text></view>
                        </picker>
                    </view>
                    <view class="form-item">
                        <text class="form-label">报修人（教师）</text>
                        <input class="form-input" v-model="editForm.reporter_name" placeholder="请输入报修人" />
                    </view>
                    <view class="form-item">
                        <text class="form-label">报修人学院</text>
                        <input class="form-input" v-model="editForm.reporter_college" placeholder="请输入学院" />
                    </view>
                    <view class="form-item">
                        <text class="form-label">是否外聘教师</text>
                        <view class="radio-group">
                            <view class="radio-item" :class="{ active: !editForm.is_external_teacher }" @click="editForm.is_external_teacher = false">否</view>
                            <view class="radio-item" :class="{ active: editForm.is_external_teacher }" @click="editForm.is_external_teacher = true">是</view>
                        </view>
                    </view>
                    <view class="form-item">
                        <text class="form-label">报修方式</text>
                        <picker :range="reportMethodOptions" @change="onEditMethodChange">
                            <view class="form-select">{{ editForm.report_method || '请选择' }} <text class="arrow">▼</text></view>
                        </picker>
                    </view>
                    <view class="form-item">
                        <text class="form-label">处理人</text>
                        <input class="form-input" v-model="editForm.handler_name" placeholder="请输入处理人" />
                    </view>
                    <view class="form-item">
                        <text class="form-label">是否更换设备</text>
                        <view class="radio-group">
                            <view class="radio-item" :class="{ active: !editForm.is_device_replaced }" @click="editForm.is_device_replaced = false">否</view>
                            <view class="radio-item" :class="{ active: editForm.is_device_replaced }" @click="editForm.is_device_replaced = true">是</view>
                        </view>
                    </view>
                    <view class="form-item" v-if="editForm.is_device_replaced">
                        <text class="form-label">设备更换备注</text>
                        <textarea class="form-textarea" v-model="editForm.device_replace_note" placeholder="请填写更换的设备信息" />
                    </view>
                    <view class="form-item">
                        <text class="form-label">处理情况</text>
                        <picker :range="statusOptions" @change="onEditStatusChange">
                            <view class="form-select">{{ editForm.status || '请选择' }} <text class="arrow">▼</text></view>
                        </picker>
                    </view>
                    <view class="form-item">
                        <text class="form-label">故障原因</text>
                        <textarea class="form-textarea" v-model="editForm.fault_cause" placeholder="请描述故障现象" />
                    </view>
                    <view class="form-item">
                        <text class="form-label">处理方式</text>
                        <textarea class="form-textarea" v-model="editForm.solution" placeholder="请描述处理方式" />
                    </view>
                    <view class="form-item">
                        <text class="form-label">备注</text>
                        <textarea class="form-textarea" v-model="editForm.notes" placeholder="补充说明（可选）" />
                    </view>
                    <view class="form-item">
                        <text class="form-label">备注图片</text>
                        <view class="image-upload-area">
                            <view class="image-list">
                                <view class="image-item" v-for="(img, index) in editForm.note_images" :key="index">
                                    <image :src="getImageUrl(img)" mode="aspectFill" class="preview-image" />
                                    <view class="image-delete" @click="deleteEditImage(index)">×</view>
                                </view>
                                <view class="image-add" @click="chooseEditImage" v-if="editForm.note_images.length < 3">
                                    <text class="add-icon">📷</text>
                                    <text class="add-text">添加图片</text>
                                </view>
                            </view>
                        </view>
                    </view>
                </view>
                <view class="modal-footer">
                    <view class="save-btn" @click="saveEdit">保存修改</view>
                </view>
            </view>
        </view>
    </view>
</template>

<script>
import config, { getImageUrl as resolveImageUrl } from '../../config/index.js'
import { request, post } from '../../api/index.js'

export default {
    data() {
        return {
            studentId: '',
            studentName: '',
            records: [],
            listType: 'all',      // 'all' 全部记录 / 'my' 我的记录
            currentFilter: 'all',  // 'all' / '未处理' / '已处理'
            loading: false,
            loadingMore: false,
            currentPage: 1,
            totalPages: 1,
            hasMore: true,
            showDetail: false,
            detailData: null,
            loadingDetail: false,
            showEdit: false,
            faultTypeOptions: ['中控', '电脑', '投影仪', '音响', '麦克风', '展台', '幕布', '网络', '软件', '其他'],
            reportMethodOptions: ['多媒体报修群', '电话', '其他'],
            statusOptions: ['未处理', '处理中', '已处理'],
            editForm: {
                id: '',
                classroom: '',
                report_time: '',
                week_number: '',
                fault_type: '',
                reporter_name: '',
                reporter_college: '',
                is_external_teacher: false,
                report_method: '',
                handler_name: '',
                is_device_replaced: false,
                device_replace_note: '',
                status: '',
                fault_cause: '',
                solution: '',
                notes: '',
                note_images: []
            }
        }
    },
    onLoad() {
        // 检查登录状态
        const token = uni.getStorageSync('student_token')
        if (!token) {
            uni.reLaunch({ url: '/pages/login/login' })
            return
        }
        this.studentId = uni.getStorageSync('student_id') || ''
        this.studentName = uni.getStorageSync('student_name') || ''
        this.loadRecords()
    },
    onShow() {
        this.studentId = uni.getStorageSync('student_id') || ''
        this.studentName = uni.getStorageSync('student_name') || ''
        if (this.studentId) this.loadRecords()
    },
    methods: {
        // 切换全部/我的
        switchListType(type) {
            if (this.listType === type) return
            this.listType = type
            this.currentPage = 1
            this.records = []
            this.hasMore = true
            this.loadRecords()
        },

        // 切换状态筛选
        setFilter(filter) {
            if (this.currentFilter === filter) return
            this.currentFilter = filter
            this.currentPage = 1
            this.records = []
            this.hasMore = true
            this.loadRecords()
        },

        // 加载报修记录（首次加载或刷新）
        async loadRecords() {
            this.loading = true
            this.currentPage = 1
            const params = { page: 1, page_size: 20 }

            if (this.currentFilter !== 'all') {
                params.status = this.currentFilter
            }

            try {
                let res
                if (this.listType === 'my') {
                    res = await request('/api/repair/my-list', params)
                } else {
                    res = await request('/api/repair/list', params)
                }

                if (res && res.status === 'ok') {
                    this.records = res.records || []
                    this.totalPages = res.total_pages || 1
                    this.hasMore = this.currentPage < this.totalPages
                } else {
                    this.records = []
                    console.error('API返回异常:', res)
                }
            } catch (err) {
                console.error('请求失败:', err)
                uni.showToast({ title: '网络错误', icon: 'none' })
                this.records = []
            } finally {
                this.loading = false
            }
        },

        // 加载更多（上拉加载）
        async loadMore() {
            if (this.loadingMore || !this.hasMore) return
            this.loadingMore = true
            this.currentPage++

            const params = { page: this.currentPage, page_size: 20 }
            if (this.currentFilter !== 'all') {
                params.status = this.currentFilter
            }

            try {
                let res
                if (this.listType === 'my') {
                    res = await request('/api/repair/my-list', params)
                } else {
                    res = await request('/api/repair/list', params)
                }

                if (res && res.status === 'ok') {
                    const newRecords = res.records || []
                    this.records = [...this.records, ...newRecords]
                    this.totalPages = res.total_pages || 1
                    this.hasMore = this.currentPage < this.totalPages
                }
            } catch (err) {
                console.error('加载更多失败:', err)
                this.currentPage--
            } finally {
                this.loadingMore = false
            }
        },

        // 状态样式
        statusClass(status) {
            if (status === '已处理' || status === '已解决') return 'status-done'
            if (status === '处理中') return 'status-processing'
            return 'status-pending'
        },

        // 查看详情
        async viewDetail(item) {
            this.showDetail = true
            this.loadingDetail = true
            this.detailData = null
            try {
                const res = await request('/api/repair/drill/repair', { id: item.id })
                if (res && res.status === 'ok') {
                    // API返回 {data: {repair: {...}, same_room_history: [...]}}
                    this.detailData = (res.data && res.data.repair) || item
                } else {
                    this.detailData = item
                }
            } catch (err) {
                this.detailData = item
            } finally {
                this.loadingDetail = false
            }
        },

        // 关闭详情弹窗
        closeDetail() {
            this.showDetail = false
        },

        // 判断是否是自己的记录
        isMyRecord(record) {
            if (!record) return false
            // student_id 匹配 或 handler_name 匹配
            return (record.student_id && record.student_id === this.studentId) ||
                   (record.handler_name && record.handler_name === this.studentName)
        },

        // 删除记录
        deleteRecord(id) {
            uni.showModal({
                title: '确认删除',
                content: '确定要删除这条报修记录吗？此操作不可恢复。',
                success: async (res) => {
                    if (res.confirm) {
                        try {
                            const resp = await post('/api/repair/student-delete', { id: id })
                            if (resp && resp.status === 'ok') {
                                uni.showToast({ title: '删除成功', icon: 'success' })
                                this.showDetail = false
                                this.loadRecords()
                            } else {
                                uni.showToast({ title: (resp && resp.message) || '删除失败', icon: 'none' })
                            }
                        } catch (err) {
                            uni.showToast({ title: '网络错误', icon: 'none' })
                        }
                    }
                }
            })
        },

        // 打开编辑弹窗
        openEdit() {
            if (!this.detailData) return
            this.editForm = {
                id: this.detailData.id,
                classroom: this.detailData.classroom || '',
                report_time: this.detailData.report_time || '',
                week_number: this.detailData.week_number || '',
                fault_type: this.detailData.fault_type || '',
                reporter_name: this.detailData.reporter_name || '',
                reporter_college: this.detailData.reporter_college || '',
                is_external_teacher: this.detailData.is_external_teacher || false,
                report_method: this.detailData.report_method || '',
                handler_name: this.detailData.handler_name || '',
                is_device_replaced: this.detailData.is_device_replaced || false,
                device_replace_note: this.detailData.device_replace_note || '',
                status: this.detailData.status || '未处理',
                fault_cause: this.detailData.fault_cause || '',
                solution: this.detailData.solution || '',
                notes: this.detailData.notes || '',
                note_images: Array.isArray(this.detailData.note_images) ? [...this.detailData.note_images] : []
            }
            this.showDetail = false
            this.showEdit = true
        },

        // 关闭编辑弹窗
        closeEdit() {
            this.showEdit = false
        },

        // 编辑弹窗 - 报修类型选择
        onEditFaultTypeChange(e) {
            this.editForm.fault_type = this.faultTypeOptions[e.detail.value]
        },

        // 编辑弹窗 - 报修方式选择
        onEditMethodChange(e) {
            this.editForm.report_method = this.reportMethodOptions[e.detail.value]
        },

        // 编辑弹窗 - 处理情况选择
        onEditStatusChange(e) {
            this.editForm.status = this.statusOptions[e.detail.value]
        },

        // 编辑弹窗 - 选择图片
        chooseEditImage() {
            uni.chooseImage({
                count: 3 - this.editForm.note_images.length,
                sizeType: ['compressed'],
                sourceType: ['album', 'camera'],
                success: (res) => {
                    res.tempFilePaths.forEach(path => {
                        this.uploadEditImage(path)
                    })
                }
            })
        },

        // 编辑弹窗 - 上传图片
        uploadEditImage(filePath) {
            const token = uni.getStorageSync('student_token')
            const header = {}
            if (token) header['Authorization'] = `Bearer ${token}`
            uni.uploadFile({
                url: config.API_BASE + '/api/repair/upload-image',
                filePath: filePath,
                name: 'file',
                header: header,
                success: (res) => {
                    try {
                        if (res.statusCode === 200) {
                            const data = JSON.parse(res.data)
                            if (data.status === 'ok') {
                                this.editForm.note_images.push(data.data.url)
                            } else {
                                uni.showToast({ title: data.message || '上传失败', icon: 'none' })
                            }
                        } else {
                            uni.showToast({ title: '上传失败(' + res.statusCode + ')', icon: 'none' })
                        }
                    } catch (e) {
                        uni.showToast({ title: '上传响应解析失败', icon: 'none' })
                    }
                },
                fail: () => {
                    uni.showToast({ title: '图片上传失败', icon: 'none' })
                }
            })
        },

        // 编辑弹窗 - 删除图片
        deleteEditImage(index) {
            this.editForm.note_images.splice(index, 1)
        },

        // 获取图片完整URL（委托给共享工具函数）
        getImageUrl(img) { return resolveImageUrl(img) },

        // 保存编辑
        async saveEdit() {
            if (!this.editForm.classroom.trim()) {
                uni.showToast({ title: '请输入教室', icon: 'none' })
                return
            }

            try {
                const res = await post('/api/repair/student-update', {
                    id: this.editForm.id,
                    classroom: this.editForm.classroom,
                    report_time: this.editForm.report_time,
                    week_number: parseInt(this.editForm.week_number) || 0,
                    fault_type: this.editForm.fault_type,
                    reporter_name: this.editForm.reporter_name,
                    reporter_college: this.editForm.reporter_college,
                    is_external_teacher: this.editForm.is_external_teacher,
                    report_method: this.editForm.report_method,
                    handler_name: this.editForm.handler_name,
                    is_device_replaced: this.editForm.is_device_replaced,
                    device_replace_note: this.editForm.device_replace_note,
                    status: this.editForm.status,
                    fault_cause: this.editForm.fault_cause,
                    solution: this.editForm.solution,
                    notes: this.editForm.notes,
                    note_images: this.editForm.note_images
                })

                if (res && res.status === 'ok') {
                    uni.showToast({ title: '保存成功', icon: 'success' })
                    this.showEdit = false
                    this.loadRecords()
                } else {
                    uni.showToast({ title: (res && res.message) || '保存失败', icon: 'none' })
                }
            } catch (err) {
                uni.showToast({ title: '网络错误', icon: 'none' })
            }
        }
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
}

/* ---- 全部/我的切换 ---- */
.toggle-bar {
    display: flex;
    background: var(--color-surface);
    border-radius: var(--radius-md);
    padding: 6rpx;
    margin-bottom: 16rpx;
    box-shadow: var(--shadow-sm);
    border: 1rpx solid var(--color-border-light);
}

.toggle-item {
    flex: 1;
    height: 68rpx;
    line-height: 68rpx;
    text-align: center;
    font-size: 28rpx;
    color: var(--color-text-secondary);
    border-radius: var(--radius-sm);
    transition: all var(--transition-normal);
    font-weight: 500;
}
.toggle-item.active {
    background: var(--color-primary-gradient);
    color: white;
    font-weight: 600;
    box-shadow: 0 4rpx 12rpx rgba(108, 92, 231, 0.25);
}

/* ---- 状态筛选 ---- */
.filter-bar {
    display: flex;
    gap: 12rpx;
    margin-bottom: 20rpx;
}

.filter-item {
    flex: 1;
    height: 60rpx;
    line-height: 60rpx;
    text-align: center;
    font-size: 26rpx;
    color: var(--color-text-secondary);
    background: var(--color-surface);
    border-radius: var(--radius-full);
    transition: all var(--transition-fast);
    font-weight: 500;
    border: 1rpx solid var(--color-border-light);
}
.filter-item.active {
    background: var(--color-primary-bg);
    color: var(--color-primary);
    border-color: var(--color-primary-light);
    font-weight: 600;
}

/* ---- 报修列表 ---- */
.repair-item {
    background: var(--color-surface);
    border-radius: var(--radius-lg);
    padding: 28rpx;
    margin-bottom: 16rpx;
    box-shadow: var(--shadow-sm);
    border: 1rpx solid var(--color-border-light);
    transition: all var(--transition-fast);
    animation: fadeInUp 0.3s ease both;
}
.repair-item:active {
    transform: scale(0.985);
    box-shadow: var(--shadow-xs);
    background: var(--color-bg-secondary);
}

.repair-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 10rpx;
}

.repair-room {
    font-size: 32rpx;
    font-weight: 700;
    color: var(--color-text);
}

.repair-status {
    padding: 4rpx 14rpx;
    border-radius: var(--radius-xs);
    font-size: 22rpx;
    font-weight: 600;
    letter-spacing: 0.5rpx;
}

.status-done {
    background: var(--color-success-bg);
    color: var(--color-success);
}
.status-processing {
    background: var(--color-info-bg);
    color: var(--color-info);
}
.status-pending {
    background: var(--color-warning-bg);
    color: #D97706;
}

.repair-info {
    font-size: 26rpx;
    color: var(--color-text-secondary);
    margin-bottom: 8rpx;
}

.repair-detail-row {
    font-size: 26rpx;
    color: var(--color-text-secondary);
    margin-bottom: 4rpx;
}

.repair-label { color: var(--color-text-tertiary); }
.repair-value { color: var(--color-text); }

.repair-time {
    font-size: 24rpx;
    color: var(--color-text-tertiary);
    margin-top: 8rpx;
}

.repair-action {
    margin-top: 14rpx;
    text-align: right;
}

.view-detail-btn {
    font-size: 26rpx;
    color: var(--color-primary);
    padding: 8rpx 24rpx;
    border: 1rpx solid var(--color-primary-light);
    border-radius: var(--radius-full);
    font-weight: 500;
    display: inline-block;
    transition: all var(--transition-fast);
}
.view-detail-btn:active {
    background: var(--color-primary-bg);
}

/* ---- 空状态 ---- */
.empty {
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 120rpx 0;
}
.empty-icon {
    font-size: 80rpx;
    margin-bottom: 24rpx;
    opacity: 0.45;
}
.empty-text {
    font-size: 28rpx;
    color: var(--color-text-tertiary);
}

/* ---- 加载中 ---- */
.loading {
    text-align: center;
    padding: 40rpx 0;
    font-size: 26rpx;
    color: var(--color-text-tertiary);
}

/* ---- 加载更多 ---- */
.load-more {
    padding: 20rpx 0;
    text-align: center;
}
.load-more-btn {
    padding: 20rpx;
    font-size: 28rpx;
    color: var(--color-primary);
    font-weight: 500;
}
.load-more-btn:active { opacity: 0.7; }
.no-more {
    padding: 20rpx;
    font-size: 26rpx;
    color: var(--color-text-tertiary);
}

/* ---- 弹窗通用 ---- */
.modal-mask {
    position: fixed;
    top: 0; left: 0; right: 0; bottom: 0;
    background: rgba(15, 23, 42, 0.5);
    backdrop-filter: blur(4rpx);
    z-index: 999;
    display: flex;
    align-items: center;
    justify-content: center;
    animation: fadeIn 0.2s ease both;
}
@keyframes fadeIn {
    from { opacity: 0; }
    to   { opacity: 1; }
}

.modal-content {
    width: 85%;
    max-height: 80vh;
    background: var(--color-surface);
    border-radius: var(--radius-xl);
    overflow: hidden;
    display: flex;
    flex-direction: column;
    animation: scaleIn 0.25s ease both;
    box-shadow: var(--shadow-xl);
}
@keyframes scaleIn {
    from { opacity: 0; transform: scale(0.92); }
    to   { opacity: 1; transform: scale(1); }
}

.modal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 28rpx 32rpx;
    border-bottom: 1rpx solid var(--color-divider);
}

.modal-title {
    font-size: 32rpx;
    font-weight: 700;
    color: var(--color-text);
}

.modal-close {
    font-size: 36rpx;
    color: var(--color-text-tertiary);
    padding: 8rpx;
    width: 48rpx;
    height: 48rpx;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 50%;
    transition: all var(--transition-fast);
}
.modal-close:active {
    background: var(--color-bg-secondary);
    color: var(--color-text);
}

.modal-body {
    padding: 24rpx 32rpx;
    overflow-y: auto;
    flex: 1;
}

.modal-footer {
    padding: 20rpx 32rpx 28rpx;
    border-top: 1rpx solid var(--color-divider);
    display: flex;
    gap: 16rpx;
}

/* ---- 详情弹窗 ---- */
.detail-row {
    display: flex;
    padding: 16rpx 0;
    border-bottom: 1rpx solid var(--color-divider);
}
.detail-row:last-child { border-bottom: none; }

.detail-label {
    width: 160rpx;
    font-size: 26rpx;
    color: var(--color-text-tertiary);
    flex-shrink: 0;
}

.detail-value {
    flex: 1;
    font-size: 26rpx;
    color: var(--color-text);
    word-break: break-all;
}

/* 详情弹窗加载 */
.loading-spinner-wrap {
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 60rpx 0;
    gap: 16rpx;
    font-size: 26rpx;
    color: var(--color-text-tertiary);
}
.spinner-ring {
    width: 44rpx;
    height: 44rpx;
    border: 3rpx solid var(--color-border);
    border-top: 3rpx solid var(--color-primary);
    border-radius: 50%;
    animation: ring-spin 0.7s linear infinite;
}
@keyframes ring-spin { to { transform: rotate(360deg); } }

/* ---- 按钮 ---- */
.edit-btn {
    background: var(--color-primary-gradient);
    color: white;
    text-align: center;
    height: 80rpx;
    line-height: 80rpx;
    border-radius: var(--radius-sm);
    font-size: 28rpx;
    font-weight: 600;
    flex: 1;
    box-shadow: 0 4rpx 14rpx rgba(108, 92, 231, 0.25);
    transition: all var(--transition-fast);
}
.edit-btn:active { transform: scale(0.97); }

.delete-btn {
    background: var(--color-surface);
    color: var(--color-danger);
    text-align: center;
    height: 80rpx;
    line-height: 80rpx;
    border: 2rpx solid var(--color-danger-light);
    border-radius: var(--radius-sm);
    font-size: 28rpx;
    font-weight: 600;
    margin-left: 16rpx;
    flex: 1;
    transition: all var(--transition-fast);
}
.delete-btn:active {
    background: var(--color-danger-bg);
    transform: scale(0.97);
}

/* ---- 编辑弹窗表单 ---- */
.form-item {
    margin-bottom: 24rpx;
}

.form-label {
    display: block;
    font-size: 24rpx;
    color: var(--color-text-secondary);
    margin-bottom: 10rpx;
    font-weight: 500;
}

.form-input {
    width: 100%;
    height: 72rpx;
    border: 2rpx solid var(--color-border);
    border-radius: var(--radius-sm);
    padding: 0 20rpx;
    font-size: 28rpx;
    color: var(--color-text);
    background: var(--color-bg-secondary);
    box-sizing: border-box;
    transition: all var(--transition-fast);
}
.form-input:focus {
    border-color: var(--color-primary);
    background: var(--color-surface);
    box-shadow: 0 0 0 4rpx rgba(108, 92, 231, 0.06);
}

.form-textarea {
    width: 100%;
    height: 150rpx;
    border: 2rpx solid var(--color-border);
    border-radius: var(--radius-sm);
    padding: 16rpx 20rpx;
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
    box-shadow: 0 0 0 4rpx rgba(108, 92, 231, 0.06);
}

.save-btn {
    background: var(--color-primary-gradient);
    color: white;
    text-align: center;
    height: 80rpx;
    line-height: 80rpx;
    border-radius: var(--radius-sm);
    font-size: 30rpx;
    font-weight: 600;
    flex: 1;
    box-shadow: 0 4rpx 16rpx rgba(108, 92, 231, 0.25);
    transition: all var(--transition-fast);
}
.save-btn:active { transform: scale(0.97); }

/* 编辑弹窗 - 大尺寸 */
.modal-large {
    width: 92%;
    max-height: 85vh;
}

/* ---- 表单选择器 ---- */
.form-select {
    display: flex;
    justify-content: space-between;
    align-items: center;
    width: 100%;
    height: 72rpx;
    border: 2rpx solid var(--color-border);
    border-radius: var(--radius-sm);
    padding: 0 20rpx;
    font-size: 28rpx;
    color: var(--color-text);
    background: var(--color-bg-secondary);
    box-sizing: border-box;
    transition: all var(--transition-fast);
}

.arrow {
    font-size: 20rpx;
    color: var(--color-text-tertiary);
}

/* ---- 单选按钮组 ---- */
.radio-group {
    display: flex;
    gap: 12rpx;
}

.radio-item {
    flex: 1;
    height: 72rpx;
    line-height: 72rpx;
    text-align: center;
    border: 2rpx solid var(--color-border);
    border-radius: var(--radius-sm);
    font-size: 28rpx;
    color: var(--color-text-secondary);
    background: var(--color-bg-secondary);
    transition: all var(--transition-fast);
    font-weight: 500;
}
.radio-item.active {
    border-color: var(--color-primary);
    background: var(--color-primary-bg);
    color: var(--color-primary);
    font-weight: 600;
}

/* ---- 图片上传 ---- */
.image-upload-area { width: 100%; }

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
    width: 160rpx;
    height: 160rpx;
    border-radius: var(--radius-sm);
    border: 1rpx solid var(--color-border);
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
    box-shadow: 0 2rpx 8rpx rgba(239, 68, 68, 0.3);
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
    transition: all var(--transition-fast);
}
.image-add:active {
    border-color: var(--color-primary-light);
    background: var(--color-primary-bg);
}

.add-icon { font-size: 38rpx; opacity: 0.6; }
.add-text { font-size: 22rpx; color: var(--color-text-tertiary); }
</style>
