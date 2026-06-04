<template>
    <view class="page">
        <view class="container">
            <!-- 查询表单 -->
            <view class="card">
                <view class="card-title">查询空教室</view>
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
                    <text class="form-label">上课节次</text>
                    <view class="section-grid">
                        <view class="section-item" v-for="item in sectionOptions" :key="item.value"
                              :class="{ active: selectedSections.includes(item.value) }"
                              @click="toggleSection(item.value)">
                            {{ item.short }}
                        </view>
                    </view>
                </view>
                <view class="form-group">
                    <text class="form-label">楼栋筛选</text>
                    <picker :range="buildingOptions" range-key="label" @change="onBuildingChange">
                        <view class="form-select">
                            {{ buildingOptions[buildingIndex].label }}
                            <text class="arrow">▼</text>
                        </view>
                    </picker>
                </view>
                <button class="btn-primary" @click="doQuery">🔍 查询空教室</button>
            </view>

            <!-- 查询结果 -->
            <view class="card" v-if="results.length > 0">
                <view class="result-count">
                    共找到 <text class="count-num">{{ results.length }}</text> 间空教室
                </view>
                <view class="building-section" v-for="(group, building) in groupedResults" :key="building">
                    <view class="building-title">{{ building }}（{{ group.length }}间）</view>
                    <view class="room-grid">
                        <view class="room-item" v-for="room in group" :key="room.classroom">
                            <text class="room-name">{{ room.classroom }}</text>
                            <text class="room-type">{{ room.classroom_type === 'lab' ? '实验室' : room.classroom_type === 'library' ? '图书馆' : '普通' }}</text>
                        </view>
                    </view>
                </view>
            </view>

            <!-- 空结果 -->
            <view class="card" v-else-if="queried">
                <view class="empty">
                    <text class="empty-icon">🏫</text>
                    <text class="empty-text">该时段没有空教室</text>
                </view>
            </view>
        </view>
    </view>
</template>

<script>
import { getEmptyRooms, getBuildings, getTime } from '@/api/index.js'

export default {
    data() {
        return {
            weekdayIndex: 0,
            buildingIndex: 0,
            selectedSections: [],
            results: [],
            queried: false,
            weekdayOptions: [
                { label: '周一（1）', value: 1 },
                { label: '周二（2）', value: 2 },
                { label: '周三（3）', value: 3 },
                { label: '周四（4）', value: 4 },
                { label: '周五（5）', value: 5 },
                { label: '周六（6）', value: 6 },
                { label: '周日（7）', value: 7 }
            ],
            sectionOptions: [
                { label: '1-2节', short: '1-2', value: 1 },
                { label: '3-4节', short: '3-4', value: 3 },
                { label: '5-6节', short: '5-6', value: 5 },
                { label: '7-8节', short: '7-8', value: 7 },
                { label: '9-10节', short: '9-10', value: 9 },
                { label: '11-12节', short: '11-12', value: 11 }
            ],
            buildingOptions: [{ label: '全部楼栋', value: '' }]
        }
    },
    computed: {
        groupedResults() {
            const groups = {}
            this.results.forEach(room => {
                const building = room.building || '其他'
                if (!groups[building]) groups[building] = []
                groups[building].push(room)
            })
            return groups
        }
    },
    onLoad() {
        this.initData()
    },
    methods: {
        async initData() {
            try {
                // 获取当前时间
                const timeRes = await getTime()
                if (timeRes.status === 'ok') {
                    const weekday = timeRes.data.weekday
                    const index = this.weekdayOptions.findIndex(opt => opt.value === weekday)
                    if (index >= 0) this.weekdayIndex = index
                }

                // 获取楼栋列表（后端已过滤特殊楼栋）
                const buildingRes = await getBuildings()
                if (buildingRes.status === 'ok') {
                    const buildings = (buildingRes.data || [])
                        .filter(b => b && b.trim()) // 只过滤空值
                        .map(b => ({ label: b, value: b }))
                    this.buildingOptions = [{ label: '全部楼栋', value: '' }, ...buildings]
                }
            } catch (e) {
                console.error('初始化失败:', e)
            }
        },
        onWeekdayChange(e) {
            this.weekdayIndex = e.detail.value
        },
        onBuildingChange(e) {
            this.buildingIndex = e.detail.value
        },
        toggleSection(value) {
            const index = this.selectedSections.indexOf(value)
            if (index >= 0) {
                this.selectedSections.splice(index, 1)
            } else {
                this.selectedSections.push(value)
            }
        },
        async doQuery() {
            if (this.selectedSections.length === 0) {
                uni.showToast({ title: '请选择至少一个节次', icon: 'none' })
                return
            }

            uni.showLoading({ title: '查询中...' })
            try {
                const res = await getEmptyRooms({
                    weekday: this.weekdayOptions[this.weekdayIndex].value,
                    sections: this.selectedSections.join(','),
                    building: this.buildingOptions[this.buildingIndex].value,
                    classroom_type: 'all',
                    exclude_special: true
                })

                if (res.status === 'ok') {
                    this.results = res.data
                    this.queried = true
                } else {
                    uni.showToast({ title: res.message, icon: 'none' })
                }
            } catch (e) {
                uni.showToast({ title: '查询失败', icon: 'none' })
            } finally {
                uni.hideLoading()
            }
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
}

.arrow {
    font-size: 24rpx;
    color: #999;
}

.section-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 16rpx;
}

.section-item {
    height: 80rpx;
    line-height: 80rpx;
    text-align: center;
    border: 1rpx solid #d9d9d9;
    border-radius: 12rpx;
    font-size: 28rpx;
    color: #666;
    background: white;
}

.section-item.active {
    background: #4F7CFF;
    color: white;
    border-color: #4F7CFF;
}

.result-count {
    font-size: 28rpx;
    color: #888;
    margin-bottom: 24rpx;
}

.count-num {
    color: #4F7CFF;
    font-weight: 600;
    font-size: 32rpx;
}

.building-section {
    margin-bottom: 32rpx;
}

.building-title {
    font-size: 28rpx;
    font-weight: 600;
    color: #333;
    padding: 16rpx 0;
    border-bottom: 1rpx solid #e8e8e8;
    margin-bottom: 16rpx;
}

.room-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 16rpx;
}

.room-item {
    background: white;
    border: 1rpx solid #b7eb8f;
    border-radius: 12rpx;
    padding: 16rpx;
    text-align: center;
}

.room-name {
    font-size: 28rpx;
    color: #389e0d;
    font-weight: 500;
    display: block;
}

.room-type {
    font-size: 22rpx;
    color: #999;
    display: block;
    margin-top: 4rpx;
}
</style>
