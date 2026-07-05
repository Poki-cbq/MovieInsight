from models import db


class Movie(db.Model):
    """电影主表"""
    __tablename__ = "movies"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    source = db.Column(db.String(16), default="tmdb")  # 'tmdb' | 'douban'
    tmdb_id = db.Column(db.Integer, nullable=True, index=True)  # 豆瓣数据为 NULL
    douban_id = db.Column(db.Integer, nullable=True, index=True)  # TMDB 数据为 NULL
    douban_rating = db.Column(db.Float, nullable=True)  # 豆瓣评分（TMDB 数据为 NULL）
    title = db.Column(db.String(255), nullable=False)
    original_title = db.Column(db.String(255), default="")
    overview = db.Column(db.Text, default="")
    poster_path = db.Column(db.String(255), default="")
    backdrop_path = db.Column(db.String(255), default="")
    release_date = db.Column(db.String(10), default="")
    runtime = db.Column(db.Integer)
    vote_average = db.Column(db.Float, default=0.0)
    vote_count = db.Column(db.Integer, default=0)
    popularity = db.Column(db.Float, default=0.0)
    budget = db.Column(db.Integer)
    revenue = db.Column(db.Integer)
    original_language = db.Column(db.String(10), default="")
    tagline = db.Column(db.String(500), default="")
    genres = db.Column(db.String(255), default="")
    production_countries = db.Column(db.String(255), default="")
    created_at = db.Column(db.DateTime, server_default=db.func.current_timestamp())

    # 一对多关系
    credits = db.relationship("Credit", backref="movie", lazy="dynamic", cascade="all, delete-orphan")

    def to_dict(self, include_overview=True):
        """序列化为字典"""
        data = {
            "id": self.id,
            "source": self.source,
            "tmdb_id": self.tmdb_id,
            "douban_id": self.douban_id,
            "douban_rating": self.douban_rating,
            "title": self.title,
            "original_title": self.original_title,
            "poster_path": self.poster_path,
            "backdrop_path": self.backdrop_path,
            "release_date": self.release_date,
            "runtime": self.runtime,
            "vote_average": self.vote_average,
            "vote_count": self.vote_count,
            "popularity": self.popularity,
            "budget": self.budget,
            "revenue": self.revenue,
            "original_language": self.original_language,
            "tagline": self.tagline,
            "genres": self.genres.split(",") if self.genres else [],
            "production_countries": self.production_countries.split(",") if self.production_countries else [],
        }
        if include_overview:
            data["overview"] = self.overview
        return data


class Credit(db.Model):
    """演职人员表"""
    __tablename__ = "credits"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    movie_id = db.Column(db.Integer, db.ForeignKey("movies.id", ondelete="CASCADE"), nullable=False)
    person_id = db.Column(db.Integer, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    profile_path = db.Column(db.String(255), default="")
    role = db.Column(db.String(255), default="")
    credit_type = db.Column(db.String(16), default="cast")
    department = db.Column(db.String(64), default="")
    popularity = db.Column(db.Float, default=0.0)
    order = db.Column("`order`", db.Integer, default=0)

    def to_dict(self):
        return {
            "id": self.id,
            "person_id": self.person_id,
            "name": self.name,
            "profile_path": self.profile_path,
            "role": self.role,
            "credit_type": self.credit_type,
            "department": self.department,
            "popularity": self.popularity,
            "order": self.order,
        }
