<template>
  <div class="app-sidebar">
    <div class="logo">🎬 MetaMovie</div>
    <el-menu
      :default-active="activeMenu"
      router
      background-color="transparent"
      text-color="rgba(255,255,255,0.7)"
      active-text-color="#01b4e4"
    >
      <el-menu-item index="/">
        <el-icon><Search /></el-icon>
        <span>发现电影</span>
      </el-menu-item>
      <el-menu-item index="/dashboard">
        <el-icon><DataAnalysis /></el-icon>
        <span>数据分析</span>
      </el-menu-item>
    </el-menu>
  </div>

  <div class="app-main">
    <div class="app-content">
      <router-view />
    </div>
    <footer class="app-footer">
      <span>数据来源：<a href="https://www.themoviedb.org/" target="_blank" rel="noopener noreferrer">TMDB</a> · <a href="https://movie.douban.com/top250" target="_blank" rel="noopener noreferrer">豆瓣</a></span>
      <span>·</span>
      <a href="https://github.com/Poki-cbq/MetaMovie" target="_blank" rel="noopener noreferrer">GitHub</a>
    </footer>
  </div>
</template>

<script setup>
import { computed } from "vue";
import { useRoute } from "vue-router";
import { Search, DataAnalysis } from "@element-plus/icons-vue";

const route = useRoute();
const activeMenu = computed(() => {
  if (route.path.startsWith("/movie")) return "";
  return route.path;
});
</script>

<style scoped>
/* 侧边栏 */
.app-sidebar {
  width: var(--sidebar-width);
  min-width: var(--sidebar-width);
  background: var(--tmdb-dark-blue);
  color: #fff;
  display: flex;
  flex-direction: column;
  position: fixed;
  top: 0;
  left: 0;
  bottom: 0;
  z-index: 100;
}

.app-sidebar .logo {
  padding: 24px 20px;
  font-size: 20px;
  font-weight: 700;
  letter-spacing: 1px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.app-sidebar :deep(.el-menu) {
  border-right: none;
  background: transparent;
}

.app-sidebar :deep(.el-menu-item) {
  color: rgba(255, 255, 255, 0.7);
  font-size: 15px;
}

.app-sidebar :deep(.el-menu-item:hover) {
  background: rgba(255, 255, 255, 0.08);
  color: #fff;
}

.app-sidebar :deep(.el-menu-item.is-active) {
  color: var(--tmdb-light-blue);
  background: rgba(1, 180, 228, 0.12);
}

/* 主内容区 */
.app-main {
  margin-left: var(--sidebar-width);
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

.app-content {
  flex: 1;
  padding: 24px;
  padding-bottom: calc(var(--footer-height) + 24px);
}

/* 页脚 */
.app-footer {
  height: var(--footer-height);
  background: var(--tmdb-dark-blue);
  color: rgba(255, 255, 255, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  gap: 24px;
  position: fixed;
  bottom: 0;
  left: var(--sidebar-width);
  right: 0;
  z-index: 50;
}

.app-footer a {
  color: var(--tmdb-light-blue);
  text-decoration: none;
}

.app-footer a:hover {
  text-decoration: underline;
}
</style>
