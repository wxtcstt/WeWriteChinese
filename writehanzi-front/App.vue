<script>
	export default {
		onLaunch: function() {
			console.log('App Launch')
		},
		onShow: function() {
			console.log('App Show')
		},
		onHide: function() {
			console.log('App Hide')
		}
	}
</script>

<style>
/* 全局样式 */
page {
  /* ⭐️ 魔法属性：让所有页面的可用高度严格等于屏幕减去 TabBar 的高度 */
  height: 100%; 
}
</style>
