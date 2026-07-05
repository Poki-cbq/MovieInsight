from flask import Flask
from flask_cors import CORS
from config import Config
from models import db


def create_app(config_class=Config):
    """Flask 应用工厂函数"""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # 初始化扩展
    CORS(app)
    db.init_app(app)

    # 注册蓝图
    from api.health import health_bp
    from api.movies import movies_bp
    app.register_blueprint(health_bp)
    app.register_blueprint(movies_bp)

    # 自动建表
    with app.app_context():
        db.create_all()

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=True)
