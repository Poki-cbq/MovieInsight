import time
import requests
from config import Config, GENRE_MAP, COUNTRY_MAP


class TMDBService:
    """TMDB API 封装类"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = Config.TMDB_BASE_URL
        self.image_base_url = Config.TMDB_IMAGE_BASE_URL
        self.session = requests.Session()
        self.session.params = {"api_key": api_key, "language": "zh-CN"}
        self.request_count = 0

    def _get(self, endpoint: str, params: dict = None):
        """发送 GET 请求，自动间隔 0.3 秒"""
        time.sleep(0.3)
        url = f"{self.base_url}{endpoint}"
        merged_params = {}
        if params:
            merged_params.update(params)
        try:
            resp = self.session.get(url, params=merged_params, timeout=10)
            self.request_count += 1
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.RequestException as e:
            print(f"  [API ERROR] {url}: {e}")
            return None

    # ========== 电影列表 ==========

    def get_popular_movies(self, page: int = 1) -> list:
        """获取流行电影列表"""
        data = self._get("/movie/popular", {"page": page})
        if data and "results" in data:
            return data["results"]
        return []

    def get_top_rated_movies(self, page: int = 1) -> list:
        """获取高分电影列表"""
        data = self._get("/movie/top_rated", {"page": page})
        if data and "results" in data:
            return data["results"]
        return []

    # ========== 电影详情 ==========

    def get_movie_detail(self, tmdb_id: int) -> dict | None:
        """获取电影完整详情（含中文翻译）"""
        data = self._get(f"/movie/{tmdb_id}")
        if not data:
            return None

        return {
            "tmdb_id": data.get("id"),
            "title": data.get("title") or data.get("original_title", ""),
            "original_title": data.get("original_title", ""),
            "overview": data.get("overview", ""),
            "poster_path": data.get("poster_path", ""),
            "backdrop_path": data.get("backdrop_path", ""),
            "release_date": data.get("release_date", ""),
            "runtime": data.get("runtime"),
            "vote_average": data.get("vote_average", 0.0),
            "vote_count": data.get("vote_count", 0),
            "popularity": data.get("popularity", 0.0),
            "budget": data.get("budget"),
            "revenue": data.get("revenue"),
            "original_language": data.get("original_language", ""),
            "tagline": data.get("tagline", ""),
            "genres": ",".join([
                GENRE_MAP.get(g["id"], g["name"])
                for g in data.get("genres", [])
            ]),
            "production_countries": ",".join([
                COUNTRY_MAP.get(c["iso_3166_1"], c["name"])
                for c in data.get("production_countries", [])
            ]),
        }

    def get_movie_credits(self, tmdb_id: int) -> dict | None:
        """获取电影的演职人员"""
        data = self._get(f"/movie/{tmdb_id}/credits")
        if not data:
            return None

        # 导演
        directors = []
        for person in data.get("crew", []):
            if person.get("job") == "Director":
                directors.append({
                    "person_id": person["id"],
                    "name": person.get("name", ""),
                    "profile_path": person.get("profile_path", ""),
                    "role": "Director",
                    "credit_type": "crew",
                    "department": person.get("department", ""),
                    "popularity": person.get("popularity", 0.0),
                    "order": 0,
                })

        # 演员（前 10 位）
        actors = []
        for i, person in enumerate(data.get("cast", [])[:10]):
            actors.append({
                "person_id": person["id"],
                "name": person.get("name", ""),
                "profile_path": person.get("profile_path", ""),
                "role": person.get("character", ""),
                "credit_type": "cast",
                "department": "Acting",
                "popularity": person.get("popularity", 0.0),
                "order": i,
            })

        return {"directors": directors, "actors": actors}
