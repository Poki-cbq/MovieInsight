"""Movies API — 分页、筛选、排序、搜索 / 电影详情 / 枚举接口"""

import re
from collections import Counter

from flask import Blueprint, abort, jsonify, request
from sqlalchemy import or_

from app import cache
from models import db
from models.database import Movie, Credit

movies_bp = Blueprint("movies", __name__)

# ---------------------------------------------------------------------------
# 可排序字段白名单（防 SQL 注入）
# ---------------------------------------------------------------------------
ALLOWED_SORT_FIELDS = {
    "vote_average": Movie.vote_average,
    "release_date": Movie.release_date,
    "popularity": Movie.popularity,
    "vote_count": Movie.vote_count,
    "title": Movie.title,
    "runtime": Movie.runtime,
    "budget": Movie.budget,
    "revenue": Movie.revenue,
}


def _parse_pagination():
    """解析分页参数，返回 (page, per_page)。"""
    try:
        page = max(1, int(request.args.get("page", 1)))
    except (ValueError, TypeError):
        page = 1
    try:
        per_page = max(1, min(100, int(request.args.get("per_page", 20))))
    except (ValueError, TypeError):
        per_page = 20
    return page, per_page


def _exact_genre_match(column, genre):
    """精确匹配逗号分隔列表中的类型（避免子串误匹配）。

    例如搜索 "剧" 不会匹配到 "剧情"、"喜剧"；只匹配完整 token。
    """
    return or_(
        column == genre,
        column.like(f"{genre},%"),
        column.like(f"%,{genre},%"),
        column.like(f"%,{genre}"),
    )


def _validate_year(val, label):
    """校验年份参数，合法返回 int 年份，非法返回 None 并设置错误。"""
    if not val:
        return None
    if not re.match(r"^\d{4}$", val):
        abort(400, description=f"{label} 格式错误，需要 4 位数字年份，如 2024")
    year = int(val)
    if year < 1870 or year > 2100:
        abort(400, description=f"{label} 年份超出合理范围 (1870-2100)")
    return year


def _apply_filters(query, model=Movie):
    """在 query 上叠加 genre / year / country / search 过滤。"""
    genre = request.args.get("genre", "").strip()
    year_start_raw = request.args.get("year_start", "").strip()
    year_end_raw = request.args.get("year_end", "").strip()
    country = request.args.get("country", "").strip()
    search = request.args.get("search", "").strip()

    year_start = _validate_year(year_start_raw, "year_start")
    year_end = _validate_year(year_end_raw, "year_end")

    if genre:
        query = query.filter(_exact_genre_match(model.genres, genre))
    if year_start is not None:
        query = query.filter(model.release_date >= f"{year_start}-01-01")
    if year_end is not None:
        query = query.filter(model.release_date <= f"{year_end}-12-31")
    if country:
        query = query.filter(model.production_countries.contains(country))
    if search:
        query = query.filter(model.title.contains(search))

    return query


def _apply_sort(query, model=Movie):
    """在 query 上叠加排序。"""
    sort_key = request.args.get("sort", "").strip().lower()
    order = request.args.get("order", "desc").strip().lower()

    if order not in ("asc", "desc"):
        order = "desc"

    sort_col = ALLOWED_SORT_FIELDS.get(sort_key, Movie.vote_count)
    if order == "asc":
        query = query.order_by(sort_col.asc())
    else:
        query = query.order_by(sort_col.desc())

    return query


# ===================================================================
# GET /api/movies  —  分页 + 筛选 + 排序 + 搜索
# ===================================================================
@movies_bp.route("/api/movies", methods=["GET"])
def get_movies():
    """分页获取电影列表。"""
    page, per_page = _parse_pagination()

    query = Movie.query
    query = _apply_filters(query)
    total = query.count()
    query = _apply_sort(query)

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    movies = [m.to_dict(include_overview=False) for m in pagination.items]

    return jsonify({
        "data": movies,
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": pagination.pages,
    })


# ===================================================================
# GET /api/movies/<id>  —  电影详情 + 导演 + Top 10 演员
# ===================================================================
@movies_bp.route("/api/movies/<int:movie_id>", methods=["GET"])
def get_movie_detail(movie_id):
    """获取电影详情，包含导演和前 10 位演员。"""
    movie = db.session.get(Movie, movie_id)
    if not movie:
        return jsonify({"error": "电影不存在"}), 404

    # 导演
    directors = (
        Credit.query
        .filter_by(movie_id=movie_id, credit_type="crew", role="Director")
        .all()
    )

    # Top 10 演员（按 order 排序）
    actors = (
        Credit.query
        .filter_by(movie_id=movie_id, credit_type="cast")
        .order_by(Credit.order.asc())
        .limit(10)
        .all()
    )

    return jsonify({
        "data": {
            **movie.to_dict(include_overview=True),
            "directors": [d.to_dict() for d in directors],
            "actors": [a.to_dict() for a in actors],
        }
    })


# ===================================================================
# GET /api/genres  —  类型列表 + 每类数量
# ===================================================================
@movies_bp.route("/api/genres", methods=["GET"])
@cache.cached(timeout=600)
def get_genres():
    """获取所有电影类型及各自数量。"""
    rows = Movie.query.with_entities(Movie.genres).all()
    counter = Counter()

    for (genres_str,) in rows:
        if not genres_str:
            continue
        for g in genres_str.split(","):
            g = g.strip()
            if g:
                counter[g] += 1

    data = [
        {"name": genre, "count": count}
        for genre, count in counter.most_common()
    ]

    return jsonify({"data": data})


# ===================================================================
# GET /api/years  —  年份列表 + 每年数量
# ===================================================================
@movies_bp.route("/api/years", methods=["GET"])
@cache.cached(timeout=600)
def get_years():
    """获取所有上映年份及各自数量。"""
    rows = Movie.query.with_entities(Movie.release_date).all()
    counter = Counter()

    for (date_str,) in rows:
        if not date_str or len(date_str) < 4:
            continue
        year = date_str[:4]
        counter[year] += 1

    data = [
        {"year": int(year), "count": count}
        for year, count in sorted(counter.items())
    ]

    return jsonify({"data": data})


# ===================================================================
# GET /api/countries  —  国家列表 + 每国数量
# ===================================================================
@movies_bp.route("/api/countries", methods=["GET"])
@cache.cached(timeout=600)
def get_countries():
    """获取所有制片国家及各自数量。"""
    rows = Movie.query.with_entities(Movie.production_countries).all()
    counter = Counter()

    for (countries_str,) in rows:
        if not countries_str:
            continue
        for c in countries_str.split(","):
            c = c.strip()
            if c:
                counter[c] += 1

    data = [
        {"name": country, "count": count}
        for country, count in counter.most_common()
    ]

    return jsonify({"data": data})
