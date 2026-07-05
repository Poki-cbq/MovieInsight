<template>
  <div class="dashboard-page">
    <h2 class="page-title">数据分析</h2>

    <!-- ======== 加载状态 ======== -->
    <template v-if="loading">
      <div class="stat-cards">
        <el-skeleton v-for="i in 2" :key="i" style="width: 200px" animated>
          <template #template>
            <el-skeleton-item variant="text" style="width: 60%" />
            <el-skeleton-item variant="text" style="width: 40%" />
          </template>
        </el-skeleton>
      </div>
      <div class="charts-grid">
        <el-skeleton v-for="i in 3" :key="i" style="height: 360px" animated>
          <template #template>
            <el-skeleton-item variant="rect" style="height: 100%" />
          </template>
        </el-skeleton>
      </div>
    </template>

    <!-- ======== 空状态 ======== -->
    <el-empty
      v-else-if="!stats"
      description="暂无统计数据"
    />

    <!-- ======== 数据展示 ======== -->
    <template v-else>
      <!-- 统计卡片 -->
      <div class="stat-cards">
        <div class="stat-card">
          <div class="stat-value">{{ stats.total_movies }}</div>
          <div class="stat-label">电影总数</div>
        </div>
        <div class="stat-card">
          <div class="stat-value">{{ stats.avg_rating }}</div>
          <div class="stat-label">平均评分</div>
        </div>
      </div>

      <!-- 图表 -->
      <div class="charts-grid">
        <div class="chart-card">
          <div class="chart-header">评分分布</div>
          <div ref="ratingChartRef" class="chart-body"></div>
        </div>
        <div class="chart-card">
          <div class="chart-header">类型分布</div>
          <div ref="genreChartRef" class="chart-body"></div>
        </div>
        <div class="chart-card chart-card--wide">
          <div class="chart-header">年代趋势</div>
          <div ref="yearChartRef" class="chart-body"></div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, nextTick } from "vue";
import * as echarts from "echarts";
import { fetchStats } from "../api";

// ---------------------------------------------------------------------------
// 数据
// ---------------------------------------------------------------------------
const stats = ref(null);
const loading = ref(true);

// 图表容器引用
const ratingChartRef = ref(null);
const genreChartRef = ref(null);
const yearChartRef = ref(null);

let ratingChart = null;
let genreChart = null;
let yearChart = null;

// ---------------------------------------------------------------------------
// 暗色主题默认色板
// ---------------------------------------------------------------------------
const DARK_COLORS = [
  "#01b4e4", "#90cea1", "#21d07a", "#d2d531", "#db2360",
  "#ff6b6b", "#4ecdc4", "#45b7d1", "#f9ca24", "#6c5ce7",
  "#a29bfe", "#fd79a8", "#00cec9", "#fab1a0", "#81ecec",
  "#ffeaa7", "#dfe6e9", "#74b9ff", "#55efc4", "#e17055",
];

// ---------------------------------------------------------------------------
// ECharts 初始化工具
// ---------------------------------------------------------------------------
function makeChart(domRef) {
  if (!domRef) return null;
  const chart = echarts.init(domRef, "dark");
  chart.setOption({
    backgroundColor: "#1a1a2e",
    textStyle: { color: "#ccc" },
  });
  return chart;
}

function buildRatingChart(data) {
  if (!ratingChart || !data?.length) return;
  ratingChart.setOption({
    tooltip: {
      trigger: "axis",
      formatter: (p) => `评分 ${p[0].axisValue}<br/>电影数 ${p[0].value}`,
    },
    xAxis: {
      type: "category",
      data: data.map((d) => d.score.toFixed(1)),
      name: "评分",
      axisLabel: { interval: 4, rotate: 0 },
    },
    yAxis: { type: "value", name: "电影数" },
    series: [
      {
        type: "bar",
        data: data.map((d) => d.count),
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: "#01b4e4" },
            { offset: 1, color: "#0d253f" },
          ]),
          borderRadius: [4, 4, 0, 0],
        },
      },
    ],
    grid: { top: 20, right: 20, bottom: 40, left: 50 },
  });
}

function buildGenreChart(data) {
  if (!genreChart || !data?.length) return;
  const top12 = data.slice(0, 12);
  genreChart.setOption({
    tooltip: {
      trigger: "item",
      formatter: (p) => `${p.name}<br/>${p.value} 部 · 均分 ${top12[p.dataIndex].avg_rating}`,
    },
    series: [
      {
        type: "pie",
        radius: ["40%", "72%"],
        center: ["50%", "55%"],
        avoidLabelOverlap: false,
        itemStyle: { borderRadius: 6, borderColor: "#1a1a2e", borderWidth: 3 },
        label: { show: true, formatter: "{b}\n{d}%" },
        emphasis: {
          label: { fontSize: 16, fontWeight: "bold" },
        },
        data: top12.map((g, i) => ({
          name: g.name,
          value: g.count,
          itemStyle: { color: DARK_COLORS[i % DARK_COLORS.length] },
        })),
      },
    ],
  });
}

function buildYearChart(data) {
  if (!yearChart || !data?.length) return;
  yearChart.setOption({
    tooltip: {
      trigger: "axis",
      formatter: (p) => {
        const item = p[0];
        const avg = data[item.dataIndex]?.avg_rating ?? "-";
        return `${item.axisValue} 年<br/>${item.value} 部 · 均分 ${avg}`;
      },
    },
    xAxis: {
      type: "category",
      data: data.map((d) => d.year),
      name: "年份",
      axisLabel: { interval: 9, rotate: 0 },
    },
    yAxis: [
      {
        type: "value",
        name: "电影数",
        splitLine: { lineStyle: { color: "rgba(255,255,255,0.06)" } },
      },
      {
        type: "value",
        name: "均分",
        min: 0,
        max: 10,
        splitLine: { show: false },
      },
    ],
    series: [
      {
        type: "bar",
        data: data.map((d) => d.count),
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: "#90cea1" },
            { offset: 1, color: "#0d253f" },
          ]),
          borderRadius: [3, 3, 0, 0],
        },
        barMaxWidth: 20,
      },
      {
        type: "line",
        yAxisIndex: 1,
        data: data.map((d) => d.avg_rating),
        smooth: true,
        symbol: "none",
        lineStyle: { color: "#f9ca24", width: 2 },
        itemStyle: { color: "#f9ca24" },
      },
    ],
    grid: { top: 20, right: 50, bottom: 40, left: 50 },
    legend: {
      data: ["电影数", "均分"],
      bottom: 0,
      textStyle: { color: "#aaa" },
    },
  });
}

// ---------------------------------------------------------------------------
// 数据加载
// ---------------------------------------------------------------------------
async function loadStats() {
  loading.value = true;
  try {
    const res = await fetchStats();
    stats.value = res.data.data;
    // 必须先结束 loading，让 v-else 分支渲染出图表 DOM，再初始化 ECharts
    loading.value = false;
    await nextTick();
    initCharts();
  } catch {
    loading.value = false;
    // 错误提示由 axios 拦截器统一处理
  }
}

function initCharts() {
  if (!stats.value) return;

  if (ratingChart) ratingChart.dispose();
  if (genreChart) genreChart.dispose();
  if (yearChart) yearChart.dispose();

  ratingChart = makeChart(ratingChartRef.value);
  genreChart = makeChart(genreChartRef.value);
  yearChart = makeChart(yearChartRef.value);

  buildGenreChart(stats.value.genre_distribution);
  buildYearChart(stats.value.yearly_trend);
  buildRatingChart(stats.value.rating_distribution);
}

function handleResize() {
  ratingChart?.resize();
  genreChart?.resize();
  yearChart?.resize();
}

// ---------------------------------------------------------------------------
// 生命周期
// ---------------------------------------------------------------------------
onMounted(() => {
  loadStats();
  window.addEventListener("resize", handleResize);
});

onBeforeUnmount(() => {
  window.removeEventListener("resize", handleResize);
  ratingChart?.dispose();
  genreChart?.dispose();
  yearChart?.dispose();
});
</script>

<style scoped>
.dashboard-page {
  max-width: 1400px;
  margin: 0 auto;
}

.page-title {
  font-size: 22px;
  font-weight: 700;
  margin-bottom: 24px;
}

/* 统计卡片 */
.stat-cards {
  display: flex;
  gap: 20px;
  margin-bottom: 24px;
}

.stat-card {
  background: #fff;
  border-radius: 10px;
  padding: 24px 32px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
  text-align: center;
  min-width: 160px;
}

.stat-value {
  font-size: 36px;
  font-weight: 800;
  color: var(--tmdb-dark-blue);
}

.stat-label {
  font-size: 13px;
  color: #999;
  margin-top: 4px;
}

/* 图表网格 */
.charts-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

.chart-card {
  background: #1a1a2e;
  border-radius: 10px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

.chart-card--wide {
  grid-column: 1 / -1;
}

.chart-header {
  padding: 14px 20px;
  font-size: 15px;
  font-weight: 600;
  color: #ddd;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.chart-body {
  width: 100%;
  height: 360px;
}
</style>
