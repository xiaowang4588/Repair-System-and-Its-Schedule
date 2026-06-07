<template>
    <view class="page">
        <!-- 顶部子Tab -->
        <view class="top-tabs">
            <view class="top-tab" :class="{ active: currentTab === 'schedule' }" @click="currentTab = 'schedule'">课表查询</view>
            <view class="top-tab" :class="{ active: currentTab === 'empty' }" @click="currentTab = 'empty'">空教室</view>
        </view>

        <!-- 课表查询Tab -->
        <view class="container" v-if="currentTab === 'schedule'">
            <!-- 查询区域 -->
            <view class="card">
                <view class="card-title">课表查询</view>
                <view class="form-group">
                    <text class="form-label">查询方式</text>
                    <view class="radio-group">
                        <view class="radio-item" :class="{ active: queryType === 'class' }" @click="queryType = 'class'">按班级</view>
                        <view class="radio-item" :class="{ active: queryType === 'teacher' }" @click="queryType = 'teacher'">按教师</view>
                    </view>
                </view>
                <view class="search-row">
                    <input class="search-input" v-model="keyword" :placeholder="queryType === 'class' ? '请输入班级名称' : '请输入教师姓名'" @confirm="querySchedule" />
                    <button class="btn-search" @click="querySchedule">查询</button>
                </view>
            </view>

            <!-- 课表表格 -->
            <view class="card" v-if="weeklyData">
                <view class="card-title">一周课表</view>
                <view class="table-wrapper">
                    <table class="schedule-table">
                        <thead>
                            <tr>
                                <th class="section-col">节次</th>
                                <th v-for="(name, idx) in displayWeekdays" :key="idx">{{ name }}</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr v-for="section in sections" :key="section">
                                <td class="section-col section-label">{{ section }}</td>
                                <td v-for="dayIdx in displayDays" :key="dayIdx">
                                    <view v-if="weeklyData[dayIdx] && weeklyData[dayIdx][section] && weeklyData[dayIdx][section].length > 0" class="course-list">
                                        <view class="course-item" v-for="(item, cIdx) in weeklyData[dayIdx][section]" :key="cIdx">
                                            <text class="course-name">{{ item.course_name }}</text>
                                            <text class="course-teacher">{{ item.teacher }}</text>
                                            <text class="course-room">{{ item.classroom }}</text>
                                        </view>
                                    </view>
                                    <text v-else class="no-course">-</text>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </view>
            </view>

            <!-- 空状态 -->
            <view class="empty" v-if="queried && !weeklyData">
                <text class="empty-text">未查询到课表数据</text>
            </view>
        </view>

        <!-- 空教室Tab -->
        <view class="container" v-if="currentTab === 'empty'">
            <!-- 筛选区域 -->
            <view class="card">
                <view class="card-title">空教室查询</view>
                <view class="form-group">
                    <text class="form-label">选择楼栋</text>
                    <picker :range="buildingOptions" range-key="label" @change="onBuildingChange">
                        <view class="form-select">
                            {{ buildingOptions[buildingIndex].label }}
                            <text class="arrow">▼</text>
                        </view>
                    </picker>
                </view>
                <view class="form-group">
                    <text class="form-label">选择星期</text>
                    <picker :range="weekdayPickerOptions" range-key="label" @change="onEmptyWeekdayChange">
                        <view class="form-select">
                            {{ weekdayPickerOptions[emptyWeekdayIndex].label }}
                            <text class="arrow">▼</text>
                        </view>
                    </picker>
                </view>
                <view class="form-group">
                    <text class="form-label">选择节次（可多选）</text>
                    <view class="checkbox-group">
                        <view class="checkbox-item" v-for="(opt, idx) in sectionPickerOptions" :key="idx"
                              :class="{ checked: emptySections.includes(opt.value) }"
                              @click="toggleSection(opt.value)">
                            <text class="checkbox-icon">{{ emptySections.includes(opt.value) ? '☑' : '☐' }}</text>
                            <text class="checkbox-text">{{ opt.label }}</text>
                        </view>
                    </view>
                </view>
                <button class="btn-search" @click="queryEmptyRooms">查询空教室</button>
            </view>

            <!-- 结果统计 -->
            <view class="result-summary" v-if="emptyRooms.length > 0">
                <text class="summary-text">共找到 <text class="summary-num">{{ emptyRooms.length }}</text> 间空教室</text>
            </view>

            <!-- 结果：按楼栋分组 -->
            <view v-if="emptyRooms.length > 0">
                <view class="building-section" v-for="group in groupedRooms" :key="group.building">
                    <view class="building-header">
                        <text class="building-name">🏢 {{ group.building || '未知楼栋' }}</text>
                        <text class="building-count">{{ group.rooms.length }}间</text>
                    </view>
                    <view class="room-card" v-for="room in group.rooms" :key="room.classroom">
                        <view class="room-top">
                            <text class="room-name">{{ room.classroom }}</text>
                            <text class="room-type" v-if="room.classroom_type">{{ room.classroom_type }}</text>
                        </view>
                        <view class="room-bottom">
                            <text class="room-label">空闲节次：</text>
                            <view class="room-tags">
                                <text class="room-tag" v-for="s in formatSections(room.sections_available)" :key="s">{{ s }}</text>
                            </view>
                        </view>
                    </view>
                </view>
            </view>

            <!-- 空状态 -->
            <view class="empty" v-if="emptyQueried && emptyRooms.length === 0">
                <text class="empty-text">未查询到空教室</text>
            </view>
        </view>
    </view>
</template>

<script>
import { request } from '../../api/index.js'

export default {
    data() {
        return {
            currentTab: 'schedule',
            // 课表查询
            queryType: 'class',
            keyword: '',
            weeklyData: null,
            sections: [],
            weekdayNames: [],
            queried: false,
            // 空教室
            buildingOptions: [{ label: '全部楼栋', value: '' }],
            buildingIndex: 0,
            emptyWeekdayIndex: 0,
            weekdayPickerOptions: [
                { label: '周一', value: 1 },
                { label: '周二', value: 2 },
                { label: '周三', value: 3 },
                { label: '周四', value: 4 },
                { label: '周五', value: 5 },
                { label: '周六', value: 6 },
                { label: '周日', value: 7 }
            ],
            sectionPickerOptions: [
                { label: '1-2节', value: 1 },
                { label: '3-4节', value: 3 },
                { label: '5-6节', value: 5 },
                { label: '7-8节', value: 7 },
                { label: '9-10节', value: 9 },
                { label: '11-12节', value: 11 }
            ],
            emptySections: [],
            emptyRooms: [],
            emptyQueried: false
        }
    },
    computed: {
        // 显示的星期名称（周一~周五）
        displayWeekdays() {
            return this.weekdayNames.slice(0, 5)
        },
        // 显示的天数索引（1~5）
        displayDays() {
            return [1, 2, 3, 4, 5]
        },
        // 按楼栋分组
        groupedRooms() {
            const map = {}
            for (const room of this.emptyRooms) {
                const building = room.building || '未知楼栋'
                if (!map[building]) {
                    map[building] = { building, rooms: [] }
                }
                map[building].rooms.push(room)
            }
            return Object.values(map)
        }
    },
    onLoad() {
        const token = uni.getStorageSync('student_token')
        if (!token) {
            uni.reLaunch({ url: '/pages/login/login' })
            return
        }
        this.loadBuildings()
    },
    methods: {
        // 加载楼栋列表
        async loadBuildings() {
            try {
                const res = await request('/api/buildings')
                console.log('[BUILDINGS] API 返回:', JSON.stringify(res))
                if (res && res.status === 'ok' && Array.isArray(res.data) && res.data.length > 0) {
                    this.buildingOptions = [
                        { label: '全部楼栋', value: '' },
                        ...res.data.map(b => ({ label: b, value: b }))
                    ]
                    console.log('[BUILDINGS] 楼栋列表:', this.buildingOptions)
                } else {
                    console.warn('[BUILDINGS] 返回数据为空或格式异常:', res)
                }
            } catch (e) {
                console.error('[BUILDINGS] 加载楼栋列表失败:', e)
                uni.showToast({ title: '加载楼栋列表失败', icon: 'none' })
            }
        },

        // 楼栋选择
        onBuildingChange(e) {
            this.buildingIndex = e.detail.value
        },

        // 查询课表
        async querySchedule() {
            if (!this.keyword.trim()) {
                uni.showToast({ title: this.queryType === 'class' ? '请输入班级名称' : '请输入教师姓名', icon: 'none' })
                return
            }
            uni.showLoading({ title: '查询中...' })
            try {
                const res = await request('/api/query/weekly', {
                    keyword: this.keyword.trim(),
                    type: this.queryType
                })
                if (res && res.status === 'ok' && res.data) {
                    this.weeklyData = res.data.weekly_data || null
                    this.sections = res.data.sections || []
                    this.weekdayNames = res.data.weekday_names || ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
                    this.queried = true
                    if (!this.weeklyData || Object.keys(this.weeklyData).length === 0) {
                        uni.showToast({ title: '未查询到课表', icon: 'none' })
                    }
                } else {
                    this.weeklyData = null
                    this.queried = true
                    uni.showToast({ title: (res && res.message) || '查询失败', icon: 'none' })
                }
            } catch (e) {
                console.error('查询课表失败:', e)
                uni.showToast({ title: '查询失败', icon: 'none' })
            } finally {
                uni.hideLoading()
            }
        },

        // 格式化节次显示
        formatSections(sections) {
            if (!sections || !Array.isArray(sections)) return ['--']
            return sections.map(s => {
                if (typeof s === 'number') {
                    const map = { 1: '1-2节', 3: '3-4节', 5: '5-6节', 7: '7-8节', 9: '9-10节', 11: '11-12节' }
                    return map[s] || `第${s}节`
                }
                return s
            })
        },

        // 空教室星期选择
        onEmptyWeekdayChange(e) {
            this.emptyWeekdayIndex = e.detail.value
        },

        // 切换节次多选
        toggleSection(value) {
            const idx = this.emptySections.indexOf(value)
            if (idx >= 0) {
                this.emptySections.splice(idx, 1)
            } else {
                this.emptySections.push(value)
            }
        },

        // 查询空教室
        async queryEmptyRooms() {
            if (this.emptySections.length === 0) {
                uni.showToast({ title: '请至少选择一个节次', icon: 'none' })
                return
            }
            const weekday = this.weekdayPickerOptions[this.emptyWeekdayIndex].value
            const sections = this.emptySections.sort((a, b) => a - b).join(',')
            const building = this.buildingOptions[this.buildingIndex].value
            uni.showLoading({ title: '查询中...' })
            try {
                const params = {
                    weekday: weekday,
                    sections: sections,
                    exclude_special: true
                }
                if (building) params.building = building
                const res = await request('/api/empty-rooms', params)
                if (res && res.status === 'ok') {
                    this.emptyRooms = res.data || []
                    this.emptyQueried = true
                } else {
                    this.emptyRooms = []
                    this.emptyQueried = true
                    uni.showToast({ title: (res && res.message) || '查询失败', icon: 'none' })
                }
            } catch (e) {
                console.error('查询空教室失败:', e)
                uni.showToast({ title: '查询失败', icon: 'none' })
            } finally {
                uni.hideLoading()
            }
        },

    }
}
</script>

<style scoped>
.page { min-height: 100vh; background: var(--color-bg); }

/* 顶部子Tab */
.top-tabs { display: flex; background: var(--color-primary-gradient); padding-top: 8rpx; }
.top-tab {
    flex: 1; height: 80rpx; line-height: 80rpx; text-align: center;
    font-size: 30rpx; color: rgba(255,255,255,0.7); position: relative; font-weight: 500;
}
.top-tab.active { color: #fff; font-weight: 700; }
.top-tab.active::after {
    content: ''; position: absolute; bottom: 0; left: 50%;
    transform: translateX(-50%); width: 56rpx; height: 4rpx;
    background: #fff; border-radius: 2rpx;
}

.container { padding: 24rpx; }

.card {
    background: var(--color-surface); border-radius: var(--radius-lg); padding: 28rpx;
    margin-bottom: 20rpx; box-shadow: var(--shadow-sm); border: 1rpx solid var(--color-border-light);
}
.card-title { font-size: 30rpx; font-weight: 700; color: var(--color-text); margin-bottom: 24rpx; padding-bottom: 16rpx; border-bottom: 1rpx solid var(--color-divider); }

/* 查询方式 */
.form-group { margin-bottom: 24rpx; }
.form-label { font-size: 26rpx; color: var(--color-text-secondary); margin-bottom: 12rpx; display: block; font-weight: 500; }

.radio-group { display: flex; gap: 12rpx; }
.radio-item {
    flex: 1; height: 72rpx; line-height: 72rpx; text-align: center;
    border: 2rpx solid var(--color-border); border-radius: var(--radius-sm);
    font-size: 28rpx; color: var(--color-text-secondary); background: var(--color-bg-secondary);
    transition: all var(--transition-fast); font-weight: 500;
}
.radio-item.active { border-color: var(--color-primary); background: var(--color-primary-bg); color: var(--color-primary); font-weight: 600; }

/* 搜索区域 */
.search-row { display: flex; gap: 16rpx; align-items: center; }
.search-input {
    flex: 1; height: 80rpx; padding: 0 24rpx; border: 2rpx solid var(--color-border);
    border-radius: var(--radius-sm); font-size: 28rpx; color: var(--color-text);
    background: var(--color-bg-secondary); box-sizing: border-box; transition: all var(--transition-fast);
}
.search-input:focus { border-color: var(--color-primary); background: var(--color-surface); box-shadow: 0 0 0 4rpx rgba(108,92,231,0.06); }

.btn-search {
    height: 80rpx; line-height: 80rpx; padding: 0 36rpx;
    background: var(--color-accent-gradient); color: white; border: none;
    border-radius: var(--radius-sm); font-size: 28rpx; font-weight: 600;
    white-space: nowrap; box-shadow: 0 4rpx 14rpx rgba(79,124,255,0.25);
    transition: all var(--transition-fast);
}
.btn-search:active { transform: scale(0.96); }

/* 课表表格 */
.table-wrapper { overflow-x: auto; -webkit-overflow-scrolling: touch; }
.schedule-table { width: 100%; border-collapse: collapse; table-layout: fixed; }
.schedule-table th, .schedule-table td { border: 1rpx solid var(--color-divider); padding: 12rpx 8rpx; text-align: center; font-size: 22rpx; vertical-align: middle; }
.schedule-table th { background: var(--color-primary-bg); color: var(--color-primary); font-weight: 600; font-size: 24rpx; }
.section-col { width: 100rpx; flex-shrink: 0; }
.section-label { color: var(--color-primary); font-weight: 600; background: var(--color-primary-bg); }
.course-list { display: flex; flex-direction: column; gap: 8rpx; }
.course-item { display: flex; flex-direction: column; align-items: center; padding: 4rpx 0; }
.course-name { font-size: 22rpx; font-weight: 600; color: var(--color-text); text-align: center; word-break: break-all; }
.course-teacher { font-size: 20rpx; color: var(--color-primary); text-align: center; }
.course-room { font-size: 20rpx; color: var(--color-text-tertiary); text-align: center; }
.no-course { font-size: 24rpx; color: var(--color-text-placeholder); }

/* 表单选择器 */
.form-select {
    display: flex; justify-content: space-between; align-items: center;
    width: 100%; height: 88rpx; padding: 0 24rpx; border: 2rpx solid var(--color-border);
    border-radius: var(--radius-sm); font-size: 28rpx; color: var(--color-text);
    background: var(--color-bg-secondary); box-sizing: border-box;
}
.arrow { font-size: 20rpx; color: var(--color-text-tertiary); }

/* 多选checkbox */
.checkbox-group { display: flex; flex-wrap: wrap; gap: 12rpx; }
.checkbox-item {
    display: flex; align-items: center; gap: 8rpx; padding: 12rpx 20rpx;
    border: 2rpx solid var(--color-border); border-radius: var(--radius-sm);
    background: var(--color-bg-secondary); transition: all var(--transition-fast);
}
.checkbox-item.checked { border-color: var(--color-primary); background: var(--color-primary-bg); }
.checkbox-icon { font-size: 26rpx; color: var(--color-primary); }
.checkbox-text { font-size: 26rpx; color: var(--color-text); }

/* 空教室结果 */
.result-summary { margin-bottom: 16rpx; padding: 16rpx 24rpx; background: var(--color-primary-bg); border-radius: var(--radius-sm); }
.summary-text { font-size: 26rpx; color: var(--color-text-secondary); }
.summary-num { font-size: 30rpx; font-weight: 700; color: var(--color-primary); }

/* 楼栋分组 */
.building-section { margin-bottom: 24rpx; border-radius: var(--radius-lg); box-shadow: var(--shadow-md); overflow: hidden; border: 1rpx solid var(--color-border-light); }
.building-header { display: flex; justify-content: space-between; align-items: center; padding: 16rpx 24rpx; background: var(--color-primary-gradient); border-radius: var(--radius-lg) var(--radius-lg) 0 0; }
.building-name { font-size: 30rpx; font-weight: 600; color: white; }
.building-count { font-size: 24rpx; color: rgba(255,255,255,0.8); background: rgba(255,255,255,0.18); padding: 4rpx 16rpx; border-radius: 20rpx; }

/* 教室卡片 */
.room-card { background: var(--color-surface); padding: 22rpx 24rpx; border-bottom: 1rpx solid var(--color-divider); transition: background var(--transition-fast); }
.room-card:last-child { border-bottom: none; border-radius: 0 0 var(--radius-lg) var(--radius-lg); }
.room-card:active { background: var(--color-bg-secondary); }
.room-top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12rpx; }
.room-name { font-size: 30rpx; font-weight: 600; color: var(--color-text); }
.room-type { font-size: 22rpx; color: var(--color-primary); background: var(--color-primary-bg); padding: 4rpx 12rpx; border-radius: 6rpx; font-weight: 500; }
.room-bottom { display: flex; align-items: flex-start; gap: 8rpx; }
.room-label { font-size: 24rpx; color: var(--color-text-tertiary); flex-shrink: 0; line-height: 44rpx; }
.room-tags { display: flex; flex-wrap: wrap; gap: 8rpx; }
.room-tag { font-size: 22rpx; color: var(--color-primary); background: var(--color-primary-bg); padding: 6rpx 16rpx; border-radius: 6rpx; font-weight: 500; }

/* 空状态 */
.empty { display: flex; flex-direction: column; align-items: center; padding: 120rpx 0; }
.empty-text { font-size: 28rpx; color: var(--color-text-tertiary); }
</style>
