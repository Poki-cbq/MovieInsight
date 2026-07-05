"""
MovieInsight 数据初始化脚本

用法：
    cd backend
    python seed.py

说明：
    - 从 TMDB API 拉取热门 + 高分电影
    - 去重后逐部获取详情和演职人员
    - 可重复执行（已存在的 tmdb_id 自动跳过）
    - 预计耗时约 2-3 分钟
"""
import time
import sys
from app import create_app
from config import Config
from models import db
from models.database import Movie, Credit
from services.tmdb_service import TMDBService


def main():
    # 检查 API Key
    if not Config.TMDB_API_KEY or Config.TMDB_API_KEY == "your_api_key_here":
        print("错误：请先在 .env 文件中配置 TMDB_API_KEY")
        sys.exit(1)

    print("=" * 50)
    print("  MovieInsight — 数据初始化")
    print("=" * 50)

    app = create_app()
    tmdb = TMDBService(Config.TMDB_API_KEY)

    # ========== 1. 收集电影列表 ==========
    print("\n[1/4] 获取电影列表...")
    all_movies = []

    # 热门电影 8 页
    for page in range(1, 9):
        movies = tmdb.get_popular_movies(page)
        all_movies.extend(movies)
        print(f"  热门 第{page}页 → {len(movies)} 部")

    # 高分电影 5 页
    for page in range(1, 6):
        movies = tmdb.get_top_rated_movies(page)
        all_movies.extend(movies)
        print(f"  高分 第{page}页 → {len(movies)} 部")

    # 去重
    seen_ids = set()
    unique_movies = []
    for m in all_movies:
        tid = m.get("id")
        if tid and tid not in seen_ids:
            seen_ids.add(tid)
            unique_movies.append(m)

    print(f"  去重后共 {len(unique_movies)} 部电影")

    # ========== 2. 获取已存在的 movie id ==========
    print("\n[2/4] 检查已入库数据...")
    existing_tmdb_ids = set()
    with app.app_context():
        existing = db.session.query(Movie.tmdb_id).all()
        existing_tmdb_ids = {row[0] for row in existing}
    print(f"  已存在 {len(existing_tmdb_ids)} 部，将跳过")

    # ========== 3. 逐部获取详情 + 写入 ==========
    print("\n[3/4] 获取电影详情和演职人员...")
    new_movies = 0
    new_credits = 0
    skipped = 0
    errors = 0

    with app.app_context():
        for i, m in enumerate(unique_movies):
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
            movie = Movie(**detail)
            db.session.add(movie)
            db.session.flush()  # 获取 movie.id

            # 写入演职人员
            if credits_data:
                for d in credits_data.get("directors", []):
                    db.session.add(Credit(movie_id=movie.id, **d))
                    new_credits += 1
                for a in credits_data.get("actors", []):
                    db.session.add(Credit(movie_id=movie.id, **a))
                    new_credits += 1

            db.session.commit()
            new_movies += 1

            # 进度
            if (i + 1) % 10 == 0:
                print(f"  进度: {i+1}/{len(unique_movies)}  "
                      f"({new_movies} 新, {skipped} 跳过, {errors} 失败)")

    # ========== 4. 统计 ==========
    print("\n[4/4] 完成！")
    print("-" * 50)
    with app.app_context():
        total_movies = Movie.query.count()
        total_credits = Credit.query.count()
    print(f"  电影总数: {total_movies}")
    print(f"  演职记录: {total_credits}")
    print(f"  本次新增: {new_movies} 部电影")
    print(f"  API 调用: {tmdb.request_count} 次")
    print(f"  跳过(已存在): {skipped} 部")
    print(f"  失败: {errors} 部")
    print("=" * 50)


if __name__ == "__main__":
    start = time.time()
    main()
    elapsed = time.time() - start
    print(f"\n总耗时: {elapsed:.1f} 秒")
