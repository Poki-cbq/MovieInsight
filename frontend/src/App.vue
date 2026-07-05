<template>
  <div class="app-sidebar">
    <div class="logo">🎬 MovieInsight</div>
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
      <span>数据来源：<a href="https://www.themoviedb.org/" target="_blank">TMDB</a></span>
      <span>·</span>
      <a href="https://github.com/Poki-cbq/MovieInsight" target="_blank">GitHub</a>
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
