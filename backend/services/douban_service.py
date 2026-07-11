"""
豆瓣 Top 250 爬虫

用法：
    from services.douban_service import DoubanService
    ds = DoubanService()
    movies = ds.scrape_top250()  # 返回 250 部电影 dict 列表

说明：
    - 爬取 https://movie.douban.com/top250 共 10 页
    - 每次请求间隔 2 秒，防止被封禁
    - 返回字段：douban_id, title, original_title, douban_rating,
      vote_count, overview, genres, poster_path, release_date
"""
import logging
import re
import time

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class DoubanService:
    """豆瓣 Top 250 爬虫封装类"""

    BASE_URL = "https://movie.douban.com/top250"
    REQUEST_INTERVAL = 2  # 请求间隔（秒）

    HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    }

    # ------------------------------------------------------------------
    # 公共入口
    # ------------------------------------------------------------------

    def scrape_top250(self) -> list:
        """爬取豆瓣 Top 250 全部 10 页，返回电影字典列表。"""
        all_movies = []

        for page in range(10):
            start = page * 25
            url = f"{self.BASE_URL}?start={start}&filter="
            movies = self._scrape_page(url, page + 1)
            all_movies.extend(movies)

            logger.info("豆瓣 第%d页 → %d 部", page + 1, len(movies))

            if page < 9:
                time.sleep(self.REQUEST_INTERVAL)

        return all_movies

    # ------------------------------------------------------------------
    # 内部方法
    # ------------------------------------------------------------------

    def _scrape_page(self, url: str, page_num: int) -> list:
        """请求单页 HTML，最多重试 2 次，返回解析后的电影列表。"""
        for attempt in range(2):
            try:
                resp = requests.get(
                    url,
                    headers=self.HEADERS,
                    timeout=15,
                )
                resp.raise_for_status()
                return self._parse_page(resp.text)
            except requests.exceptions.RequestException as e:
                logger.warning("[DOUBAN ERROR] 第%d页 第%d次尝试失败: %s", page_num, attempt + 1, e)
                if attempt < 1:
                    time.sleep(2)

        return []

    def _parse_page(self, html: str) -> list:
        """从单页 HTML 中解析出所有电影条目。"""
        soup = BeautifulSoup(html, "lxml")
        items = soup.select(".grid_view .item")
        return [self._parse_item(item) for item in items]

    def _parse_item(self, item) -> dict:
        """解析单部电影条目，返回电影信息字典。"""
        movie = {}

        # --- 豆瓣 ID ----------------------------------------------------------
        link_tag = item.select_one("a")
        if link_tag:
            href = link_tag.get("href", "")
            m = re.search(r"subject/(\d+)/", href)
            if m:
                movie["douban_id"] = int(m.group(1))

        # --- 标题 ------------------------------------------------------------
        title_tag = item.select_one(".title")
        title = title_tag.get_text(strip=True) if title_tag else ""
        movie["title"] = title

        # --- 原始标题 ---------------------------------------------------------
        original_title = ""
        if title_tag:
            # 原始标题在 <span class="title"> 后的下一个文本节点中
            # 通常结构是：<span class="title">中文名</span>&nbsp;/&nbsp;原始名
            # 取下一个 title 标签（部分电影有第二个 .title）
            all_titles = item.select(".title")
            if len(all_titles) > 1:
                orig_text = all_titles[1].get_text(strip=True)
                # 去除前导的 "&nbsp;/&nbsp;" 类似标记
                original_title = orig_text.lstrip("/").strip()
        movie["original_title"] = original_title

        # --- 豆瓣评分 ---------------------------------------------------------
        rating_tag = item.select_one(".rating_num")
        if rating_tag:
            try:
                movie["douban_rating"] = float(rating_tag.get_text(strip=True))
            except ValueError:
                movie["douban_rating"] = 0.0
        else:
            movie["douban_rating"] = 0.0

        # --- 评价人数 ---------------------------------------------------------
        vote_count = 0
        star_tags = item.select(".star span")
        for st in star_tags:
            text = st.get_text(strip=True)
            m = re.search(r"(\d+)人评价", text)
            if m:
                vote_count = int(m.group(1))
                break
        movie["vote_count"] = vote_count

        # --- 海报 -------------------------------------------------------------
        poster_path = ""
        img_tag = item.select_one("img")
        if img_tag:
            poster_path = img_tag.get("src", "")
        movie["poster_path"] = poster_path

        # --- 简介（一句话点评）-------------------------------------------------
        overview = ""
        quote_tag = item.select_one(".inq")
        if quote_tag:
            overview = quote_tag.get_text(strip=True)
        movie["overview"] = overview

        # --- 年份、类型等信息（来自 .bd p 标签）--------------------------------
        bd_tag = item.select_one(".bd")
        info_text = ""
        if bd_tag:
            p_tag = bd_tag.select_one("p")
            if p_tag:
                info_text = p_tag.get_text("\n", strip=True)

        release_date = ""
        genres = ""

        if info_text:
            # 提取年份（第一个 4 位数字）
            year_m = re.search(r"(\d{4})", info_text)
            if year_m:
                release_date = year_m.group(1)

            # 提取类型：按 / 分割后，过滤掉年份、国家、带冒号的项
            parts = [p.strip() for p in info_text.split("/")]
            filtered = []
            for p in parts:
                if p.startswith("导演") or p.startswith("主演"):
                    continue
                if ":" in p:
                    continue
                filtered.append(p)

            if filtered:
                # 过滤掉年份和纯数字项
                genre_parts = []
                for p in filtered:
                    # 跳过纯年份
                    if re.match(r"^\d{4}$", p):
                        continue
                    # 跳过国家名（后面可能还有年份和语言）
                    genre_parts.append(p)

                genres = ",".join(genre_parts)

        movie["release_date"] = release_date
        movie["genres"] = genres

        return movie
