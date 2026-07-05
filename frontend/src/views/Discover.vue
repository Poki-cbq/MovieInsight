<template>
  <div class="discover-page">
    <!-- ======== 筛选栏 ======== -->
    <div class="filter-bar">
      <el-input
        v-model="filters.search"
        placeholder="搜索电影名称..."
        clearable
        style="width: 240px"
        @keyup.enter="handleSearch"
      >
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
      </el-input>

      <el-select v-model="filters.genre" placeholder="全部类型" clearable style="width: 140px">
        <el-option
          v-for="g in genreOptions"
          :key="g.name"
          :label="`${g.name} (${g.count})`"
          :value="g.name"
        />
      </el-select>

      <div class="year-range">
        <el-select v-model="filters.year_start" placeholder="起始年" clearable style="width: 100px">
          <el-option v-for="y in yearOptions" :key="y.year" :label="y.year" :value="y.year" />
        </el-select>
        <span style="color: #999">—</span>
        <el-select v-model="filters.year_end" placeholder="结束年" clearable style="width: 100px">
          <el-option v-for="y in yearOptions" :key="y.year" :label="y.year" :value="y.year" />
        </el-select>
      </div>

      <el-select v-model="filters.country" placeholder="全部国家" clearable style="width: 140px">
        <el-option
          v-for="c in countryOptions"
          :key="c.name"
          :label="`${c.name} (${c.count})`"
          :value="c.name"
        />
      </el-select>

      <el-select v-model="filters.sort" style="width: 120px">
        <el-option label="按热度" value="popularity" />
        <el-option label="按评分" value="vote_average" />
        <el-option label="按上映日期" value="release_date" />
        <el-option label="按票房" value="revenue" />
      </el-select>

      <el-button
        :icon="filters.order === 'asc' ? SortUp : SortDown"
        @click="toggleOrder"
        style="width: 40px"
      />
    </div>

    <!-- ======== 加载状态 ======== -->
    <div v-if="loading" class="loading-wrapper">
      <el-skeleton :rows="3" animated />
      <div class="card-grid">
        <el-skeleton v-for="i in 8" :key="i" style="width: 100%">
          <template #template>
            <div class="skeleton-card">
              <div class="skeleton-poster"></div>
              <div style="padding: 10px">
                <el-skeleton-item variant="text" style="width: 80%" />
                <el-skeleton-item variant="text" style="width: 50%" />
              </div>
            </div>
          </template>
        </el-skeleton>
      </div>
    </div>

    <!-- ======== 空状态 ======== -->
    <div v-else-if="movies.length === 0" class="empty-state">
      <el-empty description="暂无数据，请先运行 python seed.py 初始化数据" />
    </div>

    <!-- ======== 卡片网格 ======== -->
    <template v-else>
      <div class="card-grid">
        <div
          v-for="movie in movies"
          :key="movie.id"
          class="movie-card"
          @click="goDetail(movie.id)"
        >
          <img
            v-if="movie.poster_path && !failedImages.has(movie.id)"
            :src="getPosterUrl(movie.poster_path)"
            :alt="movie.title"
            class="movie-poster"
            loading="lazy"
            @error="() => failedImages.add(movie.id)"
          />
          <div v-else class="movie-poster-placeholder">
            <el-icon><VideoCamera /></el-icon>
          </div>

          <div class="card-info">
            <div class="card-title">{{ movie.title }}</div>
            <div class="card-rating">
              <el-rate
                :model-value="toStarRating(movie.vote_average)"
                disabled
                :max="5"
                :colors="['#db2360', '#d2d531', '#21d07a']"
                style="height: 16px"
              />
              <span
                :class="{
                  'score-high': movie.vote_average >= 7.5,
                  'score-mid': movie.vote_average >= 5 && movie.vote_average < 7.5,
                  'score-low': movie.vote_average < 5,
                }"
              >
                {{ movie.vote_average?.toFixed(1) }}
              </span>
            </div>
            <div class="card-genres" v-if="movie.genres?.length">
              <el-tag
                v-for="g in movie.genres.slice(0, 3)"
                :key="g"
                size="small"
                type="info"
                style="margin-right: 4px; margin-top: 4px"
              >
                {{ g }}
              </el-tag>
            </div>
          </div>
        </div>
      </div>

      <!-- ======== 分页 ======== -->
      <div class="pagination-wrapper" v-if="totalPages > 1">
        <el-pagination
          v-model:current-page="filters.page"
          :total="total"
          :page-size="filters.per_page"
          background
          layout="prev, pager, next"
          @current-change="handlePageChange"
        />
      </div>
    </template>
  </div>
</template>

<script setup>
import { reactive, ref, watch, onMounted } from "vue";
import { useRouter } from "vue-router";
import { Search, SortUp, SortDown, VideoCamera } from "@element-plus/icons-vue";
import { fetchMovies, fetchGenres, fetchYears, fetchCountries } from "../api";

const router = useRouter();

// ---------------------------------------------------------------------------
// 筛选状态
// ---------------------------------------------------------------------------
const filters = reactive({
  page: 1,
  per_page: 20,
  genre: "",
  year_start: "",
  year_end: "",
  country: "",
  sort: "popularity",
  order: "desc",
  search: "",
});

// ---------------------------------------------------------------------------
// 数据
// ---------------------------------------------------------------------------
const movies = ref([]);
const total = ref(0);
const totalPages = ref(0);
const loading = ref(false);

const genreOptions = ref([]);
const yearOptions = ref([]);
const countryOptions = ref([]);

// ---------------------------------------------------------------------------
// 工具函数
// ---------------------------------------------------------------------------
function getPosterUrl(path) {
  if (!path) return "";
  return `https://image.tmdb.org/t/p/w500${path}`;
}

function toStarRating(voteAverage) {
  if (!voteAverage) return 0;
  return voteAverage / 2;
}

const failedImages = reactive(new Set());

// ---------------------------------------------------------------------------
// 数据请求
// ---------------------------------------------------------------------------
async function loadMovies() {
  loading.value = true;
  try {
    const params = {};
    if (filters.page > 1) params.page = filters.page;
    params.per_page = filters.per_page;
    if (filters.genre) params.genre = filters.genre;
    if (filters.year_start) params.year_start = filters.year_start;
    if (filters.year_end) params.year_end = filters.year_end;
    if (filters.country) params.country = filters.country;
    if (filters.sort !== "popularity") params.sort = filters.sort;
    if (filters.order !== "desc") params.order = filters.order;
    if (filters.search) params.search = filters.search;

    const res = await fetchMovies(params);
    movies.value = res.data.data;
    total.value = res.data.total;
    totalPages.value = res.data.total_pages;
  } catch {
    // 错误提示由 axios 拦截器统一处理
  } finally {
    loading.value = false;
  }
}

async function loadFilterOptions() {
  try {
    const [genRes, yrRes, ctRes] = await Promise.all([
      fetchGenres(),
      fetchYears(),
      fetchCountries(),
    ]);
    genreOptions.value = genRes.data.data;
    yearOptions.value = yrRes.data.data;
    countryOptions.value = ctRes.data.data;
  } catch {
    // 筛选选项加载失败不影响主流程
  }
}

// ---------------------------------------------------------------------------
// 事件处理
// ---------------------------------------------------------------------------
function handleSearch() {
  filters.page = 1;
  loadMovies();
}

function toggleOrder() {
  filters.order = filters.order === "asc" ? "desc" : "asc";
  filters.page = 1;
  loadMovies();
}

function handlePageChange(page) {
  filters.page = page;
  loadMovies();
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function goDetail(id) {
  router.push(`/movie/${id}`);
}

// ---------------------------------------------------------------------------
// 监听筛选条件变化（除搜索、分页外）
// ---------------------------------------------------------------------------
watch(
  () => [filters.genre, filters.year_start, filters.year_end, filters.country, filters.sort],
  () => {
    filters.page = 1;
    loadMovies();
  }
);

// ---------------------------------------------------------------------------
// 初始化
// ---------------------------------------------------------------------------
onMounted(() => {
  loadMovies();
  loadFilterOptions();
});
</script>

<style scoped>
.discover-page {
  max-width: 1400px;
  margin: 0 auto;
}

/* 筛选栏 */
.filter-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  background: #fff;
  padding: 16px 20px;
  border-radius: 8px;
  margin-bottom: 20px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
}

.year-range {
  display: flex;
  align-items: center;
  gap: 4px;
}

/* 卡片网格 */
.card-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
}

.movie-card {
  background: #fff;
  border-radius: 8px;
  overflow: hidden;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
}

.movie-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
}

.card-info {
  padding: 10px 12px 14px;
}

.card-title {
  font-size: 14px;
  font-weight: 600;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-bottom: 6px;
}

.card-rating {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
}

.card-genres {
  min-height: 24px;
}

/* 分页 */
.pagination-wrapper {
  display: flex;
  justify-content: center;
  margin-top: 32px;
  padding-bottom: 24px;
}

/* 加载骨架 */
.loading-wrapper {
  margin-top: 0;
}

.skeleton-card {
  background: #fff;
  border-radius: 8px;
  overflow: hidden;
}

.skeleton-poster {
  width: 100%;
  aspect-ratio: 2 / 3;
  background: #eee;
  animation: pulse 1.5s infinite;
}

@keyframes pulse {
  0%,
  100% {
    opacity: 1;
  }
  50% {
    opacity: 0.4;
  }
}

.empty-state {
  padding: 80px 0;
}

/* 响应式 */
@media (max-width: 1200px) {
  .card-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}
@media (max-width: 900px) {
  .card-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
@media (max-width: 600px) {
  .card-grid {
    grid-template-columns: 1fr;
  }
}
</style>
