import logging
import os

from flask import Flask
from flask_caching import Cache
from flask_cors import CORS
from config import Config
from models import db

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

cache = Cache()


def create_app(config_class=Config):
    """Flask 应用工厂函数"""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # 缓存配置（内存缓存，适合单机部署）
    app.config.setdefault("CACHE_TYPE", "SimpleCache")
    app.config.setdefault("CACHE_DEFAULT_TIMEOUT", 600)  # 10 分钟

    # 初始化扩展
    CORS(app)
    cache.init_app(app)
    db.init_app(app)

    # 注册蓝图
    from api.health import health_bp
    from api.movies import movies_bp
    from api.stats import stats_bp
    app.register_blueprint(health_bp)
    app.register_blueprint(movies_bp)
    app.register_blueprint(stats_bp)

    # 自动建表
    with app.app_context():
        db.create_all()

    return app


if __name__ == "__main__":
    app = create_app()
    debug = os.getenv("FLASK_DEBUG", "0") == "1"
    app.run(host="0.0.0.0", port=5000, debug=debug)
