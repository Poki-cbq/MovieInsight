"""pytest fixtures：内存 SQLite + 3 部种子电影 + 演职人员"""

import pytest

from app import create_app
from models import db
from models.database import Credit, Movie


# ---------------------------------------------------------------------------
# 测试配置 — SQLite 内存数据库，跑完即丢
# ---------------------------------------------------------------------------
class TestConfig:
    SECRET_KEY = "test-secret-key"
    TMDB_API_KEY = ""
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    TMDB_BASE_URL = "https://api.themoviedb.org/3"
    TMDB_IMAGE_BASE_URL = "https://image.tmdb.org/t/p"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def app():
    """创建已建表的 Flask 应用（内存 SQLite）。"""
    application = create_app(TestConfig)
    return application


@pytest.fixture
def client(app):
    """Flask 测试客户端。"""
    return app.test_client()


@pytest.fixture
def seed_data(app):
    """预置 3 部电影 + 演职人员，返回电影列表。"""
    with app.app_context():
        # -- 电影 ----------------------------------------------------------
        m1 = Movie(
            tmdb_id=550,
            title="搏击俱乐部",
            original_title="Fight Club",
            overview="一个患有失眠症的白领遇到了神秘的肥皂商人泰勒·德顿。",
            release_date="1999-10-15",
            runtime=139,
            vote_average=8.4,
            vote_count=20000,
            popularity=50.0,
            genres="剧情,惊悚",
            production_countries="美国",
        )
        m2 = Movie(
            tmdb_id=680,
            title="低俗小说",
            original_title="Pulp Fiction",
            overview="一部由几个相互交织的故事组成的犯罪电影。",
            release_date="1994-10-14",
            runtime=154,
            vote_average=8.5,
            vote_count=22000,
            popularity=55.0,
            genres="犯罪,剧情",
            production_countries="美国",
        )
        m3 = Movie(
            tmdb_id=155,
            title="黑暗骑士",
            original_title="The Dark Knight",
            overview="蝙蝠侠必须在混乱中对抗小丑的恐怖统治。",
            release_date="2008-07-18",
            runtime=152,
            vote_average=8.5,
            vote_count=25000,
            popularity=60.0,
            genres="动作,犯罪,剧情",
            production_countries="美国",
        )
        db.session.add_all([m1, m2, m3])
        db.session.flush()  # 拿到自增 id

        # -- 演职人员 ------------------------------------------------------
        credits = [
            # 搏击俱乐部
            Credit(movie_id=m1.id, person_id=1, name="大卫·芬奇",
                   role="Director", credit_type="crew", department="Directing", order=0),
            Credit(movie_id=m1.id, person_id=2, name="布拉德·皮特",
                   role="Tyler Durden", credit_type="cast", department="", order=1),
            Credit(movie_id=m1.id, person_id=3, name="爱德华·诺顿",
                   role="Narrator", credit_type="cast", department="", order=2),
            # 低俗小说
            Credit(movie_id=m2.id, person_id=4, name="昆汀·塔伦蒂诺",
                   role="Director", credit_type="crew", department="Directing", order=0),
            Credit(movie_id=m2.id, person_id=5, name="约翰·特拉沃尔塔",
                   role="Vincent Vega", credit_type="cast", department="", order=1),
            # 黑暗骑士
            Credit(movie_id=m3.id, person_id=6, name="克里斯托弗·诺兰",
                   role="Director", credit_type="crew", department="Directing", order=0),
            Credit(movie_id=m3.id, person_id=7, name="克里斯蒂安·贝尔",
                   role="Bruce Wayne", credit_type="cast", department="", order=1),
        ]
        db.session.add_all(credits)
        db.session.commit()

    return [m1, m2, m3]
