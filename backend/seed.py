"""
MovieInsight 数据初始化脚本

用法：
    cd backend
    python seed.py

说明：
    - 从 TMDB API 拉取热门 + 高分电影
    - 爬取豆瓣 Top 250
    - TMDB 内部去重 + 豆瓣内部去重 + 跨源按标题去重
    - 逐部获取 TMDB 完整详情（含 credits）
    - 豆瓣数据直接写入（无演职人员信息）
    - 可重复执行（已存在的 id 自动跳过）
    - 预计耗时约 10-12 分钟
"""
import time
import sys
from app import create_app
from config import Config
from models import db
from models.database import Movie, Credit
from services.tmdb_service import TMDBService
from services.douban_service import DoubanService


def main():
    # 检查 API Key
    if not Config.TMDB_API_KEY or Config.TMDB_API_KEY == "your_api_key_here":
        print("错误：请先在 .env 文件中配置 TMDB_API_KEY")
        sys.exit(1)

    print("=" * 50)
    print("  MovieInsight — 数据初始化 (v1.1)")
    print("  TMDB + 豆瓣 Top 250 双数据源")
    print("=" * 50)

    app = create_app()
    tmdb = TMDBService(Config.TMDB_API_KEY)
    douban = DoubanService()

    # ==================================================================
    # [1/5] 获取 TMDB 电影列表
    # ==================================================================
    print("\n[1/5] 获取 TMDB 电影列表...")
    all_tmdb = []

    # 热门电影 8 页
    for page in range(1, 9):
        movies = tmdb.get_popular_movies(page)
        all_tmdb.extend(movies)
        print(f"  热门 第{page}页 → {len(movies)} 部")

    # 高分电影 5 页
    for page in range(1, 6):
        movies = tmdb.get_top_rated_movies(page)
        all_tmdb.extend(movies)
        print(f"  高分 第{page}页 → {len(movies)} 部")

    # TMDB 内部去重
    seen_tmdb = set()
    unique_tmdb = []
    for m in all_tmdb:
        tid = m.get("id")
        if tid and tid not in seen_tmdb:
            seen_tmdb.add(tid)
            unique_tmdb.append(m)

    print(f"  TMDB 去重后共 {len(unique_tmdb)} 部")

    # ==================================================================
    # [2/5] 爬取豆瓣 Top 250
    # ==================================================================
    print("\n[2/5] 爬取豆瓣 Top 250...")
    all_douban = douban.scrape_top250()

    # 豆瓣内部去重（按 douban_id）
    seen_douban = set()
    unique_douban = []
    for m in all_douban:
        did = m.get("douban_id")
        if did and did not in seen_douban:
            seen_douban.add(did)
            unique_douban.append(m)

    print(f"  豆瓣去重后共 {len(unique_douban)} 部")

    # ==================================================================
    # [3/5] 检查已入库数据
    # ==================================================================
    print("\n[3/5] 检查已入库数据...")
    with app.app_context():
        existing_tmdb_ids = set()
        existing_douban_ids = set()
        existing_titles = set()

        for row in db.session.query(Movie.tmdb_id, Movie.douban_id, Movie.title).all():
            if row[0]:
                existing_tmdb_ids.add(row[0])
            if row[1]:
                existing_douban_ids.add(row[1])
            existing_titles.add(row[2])

    print(f"  已存在 TMDB: {len(existing_tmdb_ids)} 部")
    print(f"  已存在 豆瓣: {len(existing_douban_ids)} 部")
    print(f"  已存在 合计: {len(existing_titles)} 部（含重复标题）")

    # ==================================================================
    # [4/5] 写库
    # ==================================================================
    print("\n[4/5] 获取详情并写入数据库...")
    new_tmdb = 0
    new_douban = 0
    new_credits = 0
    skipped = 0
    errors = 0

    with app.app_context():
        # ---------- 写入 TMDB 电影 ----------
        total_tmdb = len(unique_tmdb)
        for i, m in enumerate(unique_tmdb):
            tmdb_id = m.get("id")
            if not tmdb_id:
                continue

            if tmdb_id in existing_tmdb_ids:
                skipped += 1
                continue

            # 获取详情
            detail = tmdb.get_movie_detail(tmdb_id)
            if not detail:
                errors += 1
                continue

            # 获取演职人员
            credits_data = tmdb.get_movie_credits(tmdb_id)

            # 写入电影
            detail["source"] = "tmdb"
            movie = Movie(**detail)
            db.session.add(movie)
            db.session.flush()

            # 写入演职人员
            if credits_data:
                for d in credits_data.get("directors", []):
                    db.session.add(Credit(movie_id=movie.id, **d))
                    new_credits += 1
                for a in credits_data.get("actors", []):
                    db.session.add(Credit(movie_id=movie.id, **a))
                    new_credits += 1

            db.session.commit()
            new_tmdb += 1
            existing_titles.add(detail.get("title", ""))

            if (i + 1) % 10 == 0:
                print(f"  TMDB: {i+1}/{total_tmdb}  "
                      f"({new_tmdb} 新, {errors} 失败)")

        # ---------- 写入豆瓣电影 ----------
        total_douban = len(unique_douban)
        for i, m in enumerate(unique_douban):
            douban_id = m.get("douban_id")
            if not douban_id:
                continue

            if douban_id in existing_douban_ids:
                skipped += 1
                continue

            # 跨源去重：标题已存在则跳过
            title = m.get("title", "")
            if title in existing_titles:
                skipped += 1
                continue

            # 豆瓣评分 → vote_average 字段
            douban_rating = m.get("douban_rating")
            vote_average = douban_rating if douban_rating else 0.0

            # 年份作为 release_date（只有年份时补上默认日期，便于前端筛选）
            release_date = m.get("release_date", "")
            if release_date and len(release_date) == 4:
                release_date = f"{release_date}-01-01"

            # 写入电影（豆瓣数据无 credits）
            movie = Movie(
                source="douban",
                tmdb_id=None,
                douban_id=douban_id,
                douban_rating=douban_rating,
                title=title,
                original_title=m.get("original_title", ""),
                overview=m.get("overview", ""),
                poster_path=m.get("poster_path", ""),  # 完整 URL
                release_date=release_date,
                vote_average=vote_average,
                vote_count=m.get("vote_count", 0),
                genres=m.get("genres", ""),
                popularity=0.0,
            )
            db.session.add(movie)
            db.session.commit()
            new_douban += 1
            existing_titles.add(title)

            if (i + 1) % 25 == 0:
                print(f"  豆瓣: {i+1}/{total_douban}  "
                      f"({new_douban} 新, {skipped} 跳过)")

    # ==================================================================
    # [5/5] 统计
    # ==================================================================
    print("\n[5/5] 完成！")
    print("-" * 50)
    with app.app_context():
        total_movies = Movie.query.count()
        total_credits = Credit.query.count()
        tmdb_count = Movie.query.filter_by(source="tmdb").count()
        douban_count = Movie.query.filter_by(source="douban").count()

    print(f"  电影总数: {total_movies}")
    print(f"    - TMDB 来源: {tmdb_count} 部")
    print(f"    - 豆瓣 来源: {douban_count} 部")
    print(f"  演职记录: {total_credits}")
    print(f"  本次新增:")
    print(f"    - TMDB: {new_tmdb} 部")
    print(f"    - 豆瓣: {new_douban} 部")
    print(f"  TMDB API 调用: {tmdb.request_count} 次")
    print(f"  跳过(已存在/去重): {skipped} 部")
    print(f"  失败: {errors} 部")
    print("=" * 50)


if __name__ == "__main__":
    start = time.time()
    main()
    elapsed = time.time() - start
    print(f"\n总耗时: {elapsed:.1f} 秒 ({elapsed / 60:.1f} 分钟)")
