import axios from "axios";

const api = axios.create({
  baseURL: "/api",
  timeout: 10000,
});

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
