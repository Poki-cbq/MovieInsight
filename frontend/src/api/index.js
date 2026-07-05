import axios from "axios";
import { ElMessage } from "element-plus";

const api = axios.create({
  baseURL: "/api",
  timeout: 10000,
});

// =========================================================================
// 统一错误拦截
// =========================================================================
api.interceptors.response.use(
  (res) => res,
  (err) => {
    const status = err.response?.status;
    const message = err.response?.data?.error || err.response?.data?.message;
    if (status && status >= 400) {
      ElMessage.error(message || `请求失败 (${status})`);
    } else if (!status) {
      ElMessage.error("网络异常，请确认后端已启动");
    }
    return Promise.reject(err);
  }
);

// =========================================================================
// 电影列表（分页 + 筛选 + 排序 + 搜索）
// =========================================================================
export function fetchMovies(params = {}) {
  return api.get("/movies", { params });
}

// =========================================================================
// 电影详情（含演职表）
// =========================================================================
export function fetchMovieDetail(id) {
  return api.get(`/movies/${id}`);
}

// =========================================================================
// Dashboard 统计数据
// =========================================================================
export function fetchStats() {
  return api.get("/stats");
}

// =========================================================================
// 筛选下拉选项
// =========================================================================
export function fetchGenres() {
  return api.get("/genres");
}

export function fetchYears() {
  return api.get("/years");
}

export function fetchCountries() {
  return api.get("/countries");
}
