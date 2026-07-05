"""API 集成测试 — 14 条用例"""

import pytest


# ===================================================================
# GET /api/movies  —  基础 + 分页 + 筛选 + 搜索 + 排序
# ===================================================================

class TestMovieList:
    """电影列表接口测试"""

    def test_basic_list(self, client, seed_data):
        """T1: GET /api/movies — 返回全部 3 部电影"""
        resp = client.get("/api/movies")
        assert resp.status_code == 200

        body = resp.get_json()
        assert len(body["data"]) == 3
        assert body["total"] == 3

    def test_pagination(self, client, seed_data):
        """T2: 分页 per_page=1 — data 长度=1, total_pages=3"""
        resp = client.get("/api/movies?per_page=1")
        assert resp.status_code == 200

        body = resp.get_json()
        assert len(body["data"]) == 1
        assert body["total_pages"] == 3

    def test_filter_by_genre(self, client, seed_data):
        """T3: 筛选 genre=动作 — 仅返回《黑暗骑士》"""
        resp = client.get("/api/movies?genre=动作")
        assert resp.status_code == 200

        body = resp.get_json()
        assert len(body["data"]) == 1
        assert body["data"][0]["title"] == "黑暗骑士"

    def test_filter_by_year_range(self, client, seed_data):
        """T4: 筛选 year_start=1994, year_end=1994 — 仅返回《低俗小说》"""
        resp = client.get("/api/movies?year_start=1994&year_end=1994")
        assert resp.status_code == 200

        body = resp.get_json()
        assert len(body["data"]) == 1
        assert body["data"][0]["title"] == "低俗小说"

    def test_filter_by_country(self, client, seed_data):
        """T5: 筛选 country=美国 — 返回全部 3 部"""
        resp = client.get("/api/movies?country=美国")
        assert resp.status_code == 200

        body = resp.get_json()
        assert len(body["data"]) == 3

    def test_search(self, client, seed_data):
        """T6: 搜索 search=搏击 — 仅返回《搏击俱乐部》"""
        resp = client.get("/api/movies?search=搏击")
        assert resp.status_code == 200

        body = resp.get_json()
        assert len(body["data"]) == 1
        assert "搏击" in body["data"][0]["title"]

    def test_sort_ascending(self, client, seed_data):
        """T7: 按评分升序 — data[0] 评分 ≤ data[-1] 评分"""
        resp = client.get("/api/movies?sort=vote_average&order=asc")
        assert resp.status_code == 200

        data = resp.get_json()["data"]
        assert len(data) >= 2
        assert data[0]["vote_average"] <= data[-1]["vote_average"]


# ===================================================================
# GET /api/movies/<id>  —  详情 + 404
# ===================================================================

class TestMovieDetail:
    """电影详情接口测试"""

    def test_detail(self, client, seed_data):
        """T8: GET /api/movies/1 — 含 title + overview + directors + actors"""
        resp = client.get("/api/movies/1")
        assert resp.status_code == 200

        movie = resp.get_json()["data"]
        assert movie["title"] == "搏击俱乐部"
        assert len(movie["overview"]) > 0
        assert len(movie["directors"]) >= 1
        assert len(movie["actors"]) >= 1

    def test_not_found(self, client, seed_data):
        """T9: GET /api/movies/99999 — 返回 404"""
        resp = client.get("/api/movies/99999")
        assert resp.status_code == 404
        assert "error" in resp.get_json()


# ===================================================================
# GET /api/stats
# ===================================================================

class TestStats:
    """Dashboard 统计接口测试"""

    def test_stats(self, client, seed_data):
        """T10: GET /api/stats — 汇总 + 3 组分布数据"""
        resp = client.get("/api/stats")
        assert resp.status_code == 200

        data = resp.get_json()["data"]
        assert data["total_movies"] == 3
        assert data["avg_rating"] > 0
        # 评分分布
        assert len(data["rating_distribution"]) > 0
        # 类型分布
        assert len(data["genre_distribution"]) > 0
        # 年代趋势
        assert len(data["yearly_trend"]) > 0


# ===================================================================
# 枚举接口 — /api/genres /api/years /api/countries
# ===================================================================

class TestEnums:
    """枚举接口测试"""

    def test_genres(self, client, seed_data):
        """T11: GET /api/genres — 包含「剧情」"""
        resp = client.get("/api/genres")
        assert resp.status_code == 200

        names = [g["name"] for g in resp.get_json()["data"]]
        assert "剧情" in names

    def test_years(self, client, seed_data):
        """T12: GET /api/years — 包含 2008"""
        resp = client.get("/api/years")
        assert resp.status_code == 200

        years = [y["year"] for y in resp.get_json()["data"]]
        assert 2008 in years

    def test_countries(self, client, seed_data):
        """T13: GET /api/countries — 包含「美国」"""
        resp = client.get("/api/countries")
        assert resp.status_code == 200

        names = [c["name"] for c in resp.get_json()["data"]]
        assert "美国" in names


# ===================================================================
# GET /api/health
# ===================================================================

class TestHealth:
    """健康检查接口测试"""

    def test_health(self, client, seed_data):
        """T14: GET /api/health — status=healthy, total_movies=3"""
        resp = client.get("/api/health")
        assert resp.status_code == 200

        body = resp.get_json()
        assert body["status"] == "healthy"
        assert body["total_movies"] == 3
