<template>
  <view class="user-container">
    
    <view class="header-card">
      <view class="user-info">
        <image class="avatar" :src="isLoggedIn ? 'https://api.dicebear.com/7.x/avataaars/svg?seed=' + currentChildId + '&backgroundColor=e1f0ff' : 'https://api.dicebear.com/7.x/avataaars/svg?seed=guest&backgroundColor=f0f0f0'"></image>
        <view class="text-info">
          <text class="name">{{ isLoggedIn ? currentChildId : '未登录' }}</text>
          
          <view v-if="isLoggedIn" class="action-row">
            <text class="slogan">坚持就是胜利 🌟</text>
            <text class="logout-text" @click="handleLogout">[退出登录]</text>
          </view>
          
          <button v-else class="login-btn" @click="showLoginDialog = true">点击验证身份</button>
        </view>
      </view>

      <view class="stats-row">
        <view class="stat-item">
          <text class="stat-num correct">{{ todayStats.correct }}</text>
          <text class="stat-label">今日答对</text>
        </view>
        <view class="stat-divider"></view>
        <view class="stat-item">
          <text class="stat-num wrong">{{ todayStats.wrong }}</text>
          <text class="stat-label">今日写错</text>
        </view>
      </view>
    </view>

    <view class="section-card">
      <view class="section-header">
        <text class="section-title">学习范围设置</text>
        <text class="section-desc">包含 1-{{ maxGrade }} 年级字库</text>
      </view>
      <view class="grade-selector">
        <view 
          class="grade-btn" 
          :class="{ 'active': maxGrade === n }" 
          v-for="n in 6" :key="n"
          @click="changeGrade(n)"
        >
          {{ n }}年级
        </view>
      </view>
    </view>

    <view class="section-card">
      <view class="section-header">
        <text class="section-title">开发者选项</text>
        <text class="section-desc" style="background-color: #fce4ec; color: #e91e63;">开源管理</text>
      </view>
      <button class="manage-btn" @click="goToDictManager">管理字库 (添加/编辑/搜索)</button>
    </view>

    <view class="section-card feedback-card">
      <text class="section-title">意见与建议</text>
      <textarea 
        class="feedback-input" 
        v-model="feedbackText" 
        placeholder="软件哪里不好用？告诉我，我连夜改！" 
        placeholder-class="placeholder-style"
        maxlength="200"
      ></textarea>
      <button class="submit-btn" :disabled="!feedbackText" @click="submitFeedback">发送给开发者</button>
    </view>

    <view class="dialog-overlay" v-if="showLoginDialog">
      <view class="dialog-card">
        <text class="dialog-title">账号登录</text>
        <text class="dialog-desc">请输入孩子的专属 ID 恢复学习进度</text>
        <input 
          class="dialog-input" 
          v-model="tempInputId" 
          placeholder="请输入孩子ID" 
          focus
        />
        <view class="dialog-actions">
          <button class="dialog-btn cancel" @click="showLoginDialog = false">取消</button>
          <button class="dialog-btn confirm" @click="confirmLogin">确认</button>
        </view>
      </view>
    </view>

  </view>
</template>

<script setup>
import { ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'

// 状态
const isLoggedIn = ref(false)
const currentChildId = ref('')
const todayStats = ref({ correct: 0, wrong: 0 })
const maxGrade = ref(6) 
const feedbackText = ref('')

// 登录弹窗状态
const showLoginDialog = ref(false)
const tempInputId = ref('admin')

// 页面跳转逻辑
const goToDictManager = () => {
  uni.navigateTo({
    url: '/pages/dict_manager/dict_manager'
  })
}

// ⭐️ 核心：每次切换到“我的”页面，都重新读取一次本地缓存
onShow(() => {
  // 1. 同步登录状态
  const savedId = uni.getStorageSync('child_id')
  if (savedId) {
    currentChildId.value = savedId
    isLoggedIn.value = true
  } else {
    currentChildId.value = ''
    isLoggedIn.value = false
  }

  // 2. 同步统计数据
  const today = new Date().toISOString().split('T')[0]
  const stats = uni.getStorageSync('study_stats') || {}
  if (stats[today]) {
    todayStats.value = stats[today]
  } else {
    todayStats.value = { correct: 0, wrong: 0 }
  }
  
  // 3. 同步年级设置
  const savedGrade = uni.getStorageSync('user_max_grade')
  if (savedGrade) maxGrade.value = savedGrade
})

// 确认登录
const confirmLogin = () => {
  const id = tempInputId.value.trim()
  if (!id) {
    uni.showToast({ title: 'ID 不能为空', icon: 'none' })
    return
  }
  uni.setStorageSync('child_id', id)
  currentChildId.value = id
  isLoggedIn.value = true
  showLoginDialog.value = false
  uni.showToast({ title: '登录成功' })
}

// 退出登录
const handleLogout = () => {
  uni.showModal({
    title: '退出登录',
    content: '退出后将无法记录学习进度，确认退出吗？',
    success: (res) => {
      if (res.confirm) {
        uni.removeStorageSync('child_id')
        isLoggedIn.value = false
        currentChildId.value = ''
      }
    }
  })
}

// 年级切换
const changeGrade = (grade) => {
  maxGrade.value = grade
  uni.setStorageSync('user_max_grade', grade)
  uni.showToast({ title: `已设置学习 1-${grade} 年级生字`, icon: 'none' })
}

const submitFeedback = () => {
  uni.showToast({ title: '收到啦，感谢反馈！', icon: 'success' })
  feedbackText.value = ''
}
</script>

<style scoped>
.user-container { padding: 30rpx; background-color: #f5f7fa; height: 100%; box-sizing: border-box; overflow-y: auto; }
.header-card { background: linear-gradient(135deg, #ffffff 0%, #f8fbff 100%); border-radius: 40rpx; padding: 40rpx; box-shadow: 0 12rpx 30rpx rgba(0, 50, 150, 0.05); margin-bottom: 40rpx; }
.user-info { display: flex; align-items: center; margin-bottom: 50rpx; }
.avatar { width: 120rpx; height: 120rpx; border-radius: 60rpx; border: 4rpx solid #fff; box-shadow: 0 8rpx 20rpx rgba(0,0,0,0.05); margin-right: 30rpx; background-color: #f0f0f0;}
.text-info { display: flex; flex-direction: column; }
.name { font-size: 40rpx; font-weight: bold; color: #333; margin-bottom: 10rpx; }

.action-row { display: flex; align-items: center; gap: 20rpx; }
.slogan { font-size: 26rpx; color: #999; }
.logout-text { font-size: 24rpx; color: #f56c6c; text-decoration: underline; padding: 10rpx 0;}

.login-btn { font-size: 26rpx; background-color: #409eff; color: #fff; margin: 0; padding: 0 30rpx; height: 56rpx; line-height: 56rpx; border-radius: 28rpx; }

.stats-row { display: flex; align-items: center; justify-content: space-around; background-color: rgba(255,255,255,0.6); border-radius: 24rpx; padding: 20rpx 0; }
.stat-item { display: flex; flex-direction: column; align-items: center; flex: 1; }
.stat-divider { width: 2rpx; height: 60rpx; background-color: #eee; }
.stat-num { font-size: 48rpx; font-weight: bold; margin-bottom: 6rpx; font-family: 'Courier New', Courier, monospace; }
.stat-num.correct { color: #67c23a; }
.stat-num.wrong { color: #f56c6c; }
.stat-label { font-size: 24rpx; color: #999; }

.section-card { background-color: #fff; border-radius: 40rpx; padding: 40rpx; margin-bottom: 40rpx; box-shadow: 0 8rpx 20rpx rgba(0,0,0,0.03); }
.section-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 30rpx; }
.section-title { font-size: 32rpx; font-weight: bold; color: #333; }
.section-desc { font-size: 24rpx; color: #409eff; background-color: #e1f0ff; padding: 6rpx 20rpx; border-radius: 20rpx; }

.grade-selector { display: flex; flex-wrap: wrap; gap: 20rpx; justify-content: space-between; }
.grade-btn { width: 30%; text-align: center; background-color: #f5f7fa; color: #999; padding: 20rpx 0; border-radius: 20rpx; font-size: 28rpx; transition: all 0.2s; font-weight: bold; border: 2rpx solid transparent; }
.grade-btn.active { background-color: #e1f0ff; color: #409eff; border-color: #a1c4fd; box-shadow: 0 4rpx 12rpx rgba(64, 158, 255, 0.15); }

.feedback-card { padding-bottom: 30rpx; }
.feedback-input { width: 100%; height: 180rpx; background-color: #f5f7fa; border-radius: 20rpx; padding: 24rpx; font-size: 28rpx; color: #333; margin-top: 20rpx; margin-bottom: 30rpx; box-sizing: border-box; }
.placeholder-style { color: #ccc; }
.submit-btn { background-color: #333; color: #fff; border-radius: 20rpx; font-size: 30rpx; font-weight: bold; height: 88rpx; line-height: 88rpx; box-shadow: 0 8rpx 20rpx rgba(0,0,0,0.1); }
.submit-btn[disabled] { background-color: #ccc; color: #fff; opacity: 0.6; }

.manage-btn { background-color: #f8f9fa; color: #333; border: 2rpx solid #e4e7ed; border-radius: 20rpx; font-size: 30rpx; font-weight: bold; height: 88rpx; line-height: 88rpx; width: 100%; }
.manage-btn:active { background-color: #e4e7ed; }

/* 登录弹窗样式 */
.dialog-overlay { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background-color: rgba(0,0,0,0.5); display: flex; justify-content: center; align-items: center; z-index: 999; animation: fadeIn 0.2s ease; }
.dialog-card { width: 80%; background-color: white; border-radius: 30rpx; padding: 50rpx 40rpx; display: flex; flex-direction: column; align-items: center; box-shadow: 0 20rpx 50rpx rgba(0,0,0,0.15); }
.dialog-title { font-size: 36rpx; font-weight: bold; color: #333; margin-bottom: 10rpx; }
.dialog-desc { font-size: 26rpx; color: #999; text-align: center; margin-bottom: 40rpx; }
.dialog-input { width: 100%; height: 90rpx; background-color: #f5f7fa; border-radius: 20rpx; padding: 0 30rpx; font-size: 32rpx; color: #333; margin-bottom: 50rpx; box-sizing: border-box; text-align: center; border: 2rpx solid transparent; transition: all 0.2s; }
.dialog-input:focus { border-color: #409eff; background-color: #e1f0ff; }
.dialog-actions { display: flex; justify-content: space-between; width: 100%; }
.dialog-btn { width: 45%; height: 80rpx; line-height: 80rpx; border-radius: 40rpx; font-size: 30rpx; font-weight: bold; }
.dialog-btn.cancel { background-color: #f5f7fa; color: #666; }
.dialog-btn.confirm { background-color: #409eff; color: white; box-shadow: 0 8rpx 20rpx rgba(64,158,255,0.3); }

@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
</style>