<template>
  <div class="detail-page">
    <!-- ======== 加载状态 ======== -->
    <template v-if="loading">
      <div class="detail-layout">
        <el-skeleton style="width: 300px; height: 450px">
          <template #template>
            <el-skeleton-item variant="rect" style="width: 100%; height: 100%; border-radius: 8px" />
          </template>
        </el-skeleton>
        <div style="flex: 1">
          <el-skeleton :rows="8" animated />
        </div>
      </div>
    </template>

    <!-- ======== 404 ======== -->
    <div v-else-if="!movie" class="empty-state">
      <el-empty description="电影不存在" />
    </div>

    <!-- ======== 内容 ======== -->
    <template v-else>
      <el-button text :icon="ArrowLeft" @click="goBack" class="back-btn">返回</el-button>

      <div class="detail-layout">
        <!-- 海报 -->
        <div class="poster-section">
          <img
            v-if="movie.poster_path && !posterFailed"
            :src="getPosterUrl(movie.poster_path, movie.source)"
            :alt="movie.title"
            class="detail-poster"
            referrerpolicy="no-referrer"
            @error="() => (posterFailed = true)"
          />
          <div v-else class="movie-poster-placeholder" style="width: 300px">
            <el-icon :size="64"><VideoCamera /></el-icon>
          </div>
        </div>

        <!-- 信息 -->
        <div class="info-section">
          <h1 class="movie-title">
            {{ movie.title }}
            <el-tag
              size="small"
              :type="movie.source === 'douban' ? 'success' : ''"
              :style="movie.source === 'douban' ? 'margin-left:8px' : 'margin-left:8px;background:#01b4e4;border-color:#01b4e4;color:#fff'"
            >
              {{ movie.source === 'douban' ? '豆瓣' : 'TMDB' }}
            </el-tag>
            <span class="original-title" v-if="movie.original_title && movie.original_title !== movie.title">
              {{ movie.original_title }}
            </span>
          </h1>

          <!-- 评分与标签 -->
          <div class="meta-row">
            <el-rate
              :model-value="toStarRating(movie.vote_average)"
              disabled
              :max="5"
              :colors="['#db2360', '#d2d531', '#21d07a']"
              style="height: 20px"
            />
            <span
              :class="{
                'score-high': movie.vote_average >= 7.5,
                'score-mid': movie.vote_average >= 5 && movie.vote_average < 7.5,
                'score-low': movie.vote_average < 5,
              }"
              class="rating-number"
            >
              {{ movie.vote_average?.toFixed(1) }} / 10
            </span>
            <span v-if="movie.source === 'douban' && movie.douban_rating" class="douban-rating">
              豆瓣 {{ movie.douban_rating }}
            </span>
            <span class="vote-count">{{ movie.vote_count?.toLocaleString() }} 票</span>
          </div>

          <div class="meta-row" v-if="movie.runtime || movie.genres?.length">
            <span v-if="movie.runtime">{{ formatRuntime(movie.runtime) }}</span>
            <span v-if="movie.runtime" class="sep">·</span>
            <span v-if="movie.genres?.length">
              <el-tag
                v-for="g in movie.genres"
                :key="g"
                size="small"
                style="margin-right: 6px"
              >
                {{ g }}
              </el-tag>
            </span>
          </div>

          <div class="meta-row" v-if="movie.production_countries?.length || movie.original_language">
            <span v-if="movie.production_countries?.length">
              {{ movie.production_countries.join('、') }}
            </span>
            <span v-if="movie.production_countries?.length && movie.original_language" class="sep">·</span>
            <span v-if="movie.original_language">{{ movie.original_language?.toUpperCase() }}</span>
          </div>

          <div class="meta-row" v-if="movie.budget || movie.revenue">
            <span v-if="movie.budget">预算 {{ formatMoney(movie.budget) }}</span>
            <span v-if="movie.budget && movie.revenue" class="sep">·</span>
            <span v-if="movie.revenue">票房 {{ formatMoney(movie.revenue) }}</span>
          </div>

          <!-- 剧情简介 -->
          <div class="overview-section" v-if="movie.overview">
            <h3>剧情简介</h3>
            <p>{{ movie.overview }}</p>
          </div>

          <div class="tagline" v-if="movie.tagline">
            ❝ {{ movie.tagline }}
          </div>
        </div>
      </div>

      <!-- 演职表 -->
      <div class="credits-section">
        <template v-if="directors.length || actors.length">
          <h3>演职表</h3>
          <el-table :data="tableData" stripe style="width: 100%; margin-top: 12px" :border="false">
            <el-table-column label="" width="60">
              <template #default="{ row }">
                <img
                  v-if="row.profile_path"
                  :src="getProfileUrl(row.profile_path)"
                  class="credit-avatar"
                  @error="(e) => (e.target.style.display = 'none')"
                />
                <div v-else class="credit-avatar-placeholder">
                  <el-icon><User /></el-icon>
                </div>
              </template>
            </el-table-column>
            <el-table-column prop="name" label="姓名" width="200" />
            <el-table-column label="角色/职位">
              <template #default="{ row }">
                <el-tag v-if="row.type === 'director'" type="danger" size="small">导演</el-tag>
                <span v-else>{{ row.role }}</span>
              </template>
            </el-table-column>
          </el-table>
        </template>
        <template v-else-if="movie.source === 'douban'">
          <h3>演职表</h3>
          <p class="no-credits">暂无演职人员数据（豆瓣数据源）</p>
        </template>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { ArrowLeft, VideoCamera, User } from "@element-plus/icons-vue";
import { fetchMovieDetail } from "../api";
import { getPosterUrl, getProfileUrl, toStarRating, formatRuntime, formatMoney } from "../utils/movie";

const route = useRoute();
const router = useRouter();

const movie = ref(null);
const loading = ref(false);

const posterFailed = ref(false);

function goBack() {
  router.back();
}

// ---------------------------------------------------------------------------
// 数据加载
// ---------------------------------------------------------------------------
async function loadDetail() {
  loading.value = true;
  try {
    const id = route.params.id;
    const res = await fetchMovieDetail(id);
    movie.value = res.data.data;
  } catch (err) {
    if (err.response?.status === 404) {
      movie.value = null;
    }
    // 其他错误提示由 axios 拦截器统一处理
  } finally {
    loading.value = false;
  }
}

// ---------------------------------------------------------------------------
// 演职表数据（合并导演 + 演员）
// ---------------------------------------------------------------------------
const directors = computed(() => {
  if (!movie.value?.directors) return [];
  return movie.value.directors.map((d) => ({ ...d, type: "director" }));
});

const actors = computed(() => {
  if (!movie.value?.actors) return [];
  return movie.value.actors.map((a) => ({ ...a, type: "actor" }));
});

const tableData = computed(() => [...directors.value, ...actors.value]);

// ---------------------------------------------------------------------------
onMounted(() => {
  loadDetail();
});

// 监听路由参数变化：同一组件内从 /movie/1 跳转到 /movie/2 时重新加载
watch(
  () => route.params.id,
  (newId, oldId) => {
    if (newId && newId !== oldId) {
      posterFailed.value = false;
      loadDetail();
    }
  }
);
</script>

<style scoped>
.detail-page {
  max-width: 1100px;
  margin: 0 auto;
}

.back-btn {
  margin-bottom: 16px;
}

/* 布局 */
.detail-layout {
  display: flex;
  gap: 32px;
}

.poster-section {
  flex-shrink: 0;
}

.detail-poster {
  width: 300px;
  border-radius: 10px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  display: block;
}

/* 信息区 */
.info-section {
  flex: 1;
  min-width: 0;
}

.movie-title {
  font-size: 28px;
  font-weight: 700;
  margin-bottom: 4px;
}

.original-title {
  display: block;
  font-size: 16px;
  font-weight: 400;
  color: #999;
  margin-top: 4px;
}

.meta-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 12px;
  font-size: 14px;
  flex-wrap: wrap;
}

.rating-number {
  font-size: 18px;
}

.vote-count {
  color: #999;
  font-size: 13px;
}

.sep {
  color: #ccc;
}

.overview-section {
  margin-top: 24px;
}

.overview-section h3 {
  font-size: 16px;
  margin-bottom: 8px;
  padding-bottom: 6px;
  border-bottom: 2px solid var(--tmdb-light-blue);
  display: inline-block;
}

.overview-section p {
  line-height: 1.8;
  color: #555;
  font-size: 14px;
}

.tagline {
  margin-top: 16px;
  font-style: italic;
  color: #888;
  display: flex;
  align-items: center;
  gap: 6px;
}

/* 演职表 */
.credits-section {
  margin-top: 40px;
  background: #fff;
  border-radius: 10px;
  padding: 20px 24px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
}

.credits-section h3 {
  font-size: 18px;
}

.credit-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  object-fit: cover;
}

.credit-avatar-placeholder {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: #e8e8e8;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #bbb;
}

.douban-rating {
  font-size: 14px;
  color: #21d07a;
  font-weight: 600;
  margin-left: 4px;
}

.no-credits {
  color: #999;
  font-size: 14px;
  padding: 20px 0;
}

.empty-state {
  padding: 80px 0;
}

/* 响应式：小屏上下布局 */
@media (max-width: 768px) {
  .detail-layout {
    flex-direction: column;
    gap: 20px;
  }

  .detail-poster {
    width: 100%;
    max-width: 300px;
  }

  .movie-poster-placeholder {
    width: 100% !important;
    max-width: 300px;
    aspect-ratio: 2 / 3;
  }
}
</style>
