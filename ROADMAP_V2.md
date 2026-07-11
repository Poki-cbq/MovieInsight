# 🎬 MetaMovie 2.0 — 路线图

> 目标：个人作品集级别的全栈电影平台，一键部署，有测试覆盖，数据看板丰富。

---

## 📋 最终决策总览

| # | 问题 | 决策 |
|---|------|------|
| 1 | 暗色模式 | ❌ 先不做 |
| 2 | 分页方式 | ✅ 传统分页（保持） |
| 3 | 用户系统 | ✅ 轻量 localStorage 收藏 |
| 4 | 移动端 | ❌ 桌面优先，暂不考虑 |
| 5 | 预告片 | ❌ 不需要 |
| 6 | 数据看板 | ✅ 展示型 + **增加图表** |
| 7 | 卡片信息 | ✅ 精简（海报+标题+评分+来源标签） |
| 8 | 多语言 | ❌ 中文即可 |
| 9 | 随机推荐 | ❌ 不需要 |
| 10 | 分享 | ❌ 不需要 |
| 11 | TypeScript | ❌ 不做 |
| 12 | Pinia | ❌ 暂不引入 |
| 13 | Docker | ✅ Docker Compose 一键部署 |
| 14 | Redis | ❌ SimpleCache 够了 |
| 15 | PostgreSQL | ❌ SQLite 够了 |
| 16 | CI | ✅ GitHub Actions 自动测试 |
| 17 | 数据更新 | ✅ 手动 seed |
| 18 | 前端测试 | ✅ 工具函数 + 核心组件测试 |
| 19 | 第三数据源 | ❌ 暂不需要 |
| 20 | 目标场景 | 个人作品集 |

---

## 🗺️ 分阶段实施计划

### Phase 1 — 基础设施 + 测试（预计 2-3 小时）

**目标**：项目有 CI、有测试、一键部署。

```
[ ] 1.1 前端工具函数测试
    文件：frontend/tests/utils/movie.test.js
    内容：测试 getPosterUrl / toStarRating / formatRuntime / formatMoney
    框架：Vitest

[ ] 1.2 前端核心组件测试
    文件：frontend/tests/views/Discover.test.js
    内容：测试筛选条件变化 → API 调用、分页切换
    框架：Vitest + Vue Test Utils

[ ] 1.3 GitHub Actions CI
    文件：.github/workflows/ci.yml
    内容：push → 装依赖 → 后端 pytest → 前端 vitest → 前端 build
    触发：push 到 master / PR

[ ] 1.4 Docker Compose 一键部署
    文件：Dockerfile (前端) + Dockerfile (后端) + docker-compose.yml
    命令：docker compose up → 前端 :5173 + 后端 :5000 全启动
    包含：SQLite 数据持久化卷
```

### Phase 2 — 收藏功能（预计 1-2 小时）

**目标**：用户可以收藏电影，收藏列表持久化在浏览器中。

```
[ ] 2.1 localStorage 收藏工具
    文件：frontend/src/utils/favorites.js
    功能：
      - getFavorites()       → 返回收藏的电影 id 列表
      - toggleFavorite(id)   → 切换收藏状态
      - isFavorite(id)       → 判断是否已收藏
      - getFavoriteCount()   → 收藏数量
    细节：存 JSON 数组，用 watchEffect 保持响应式

[ ] 2.2 收藏按钮组件
    文件：frontend/src/components/FavoriteButton.vue
    功能：心形图标，点击切换收藏，el-tooltip 提示
    位置：电影卡片 + 详情页

[ ] 2.3 收藏列表页
    路由：/favorites
    内容：展示已收藏电影卡片网格（复用 Discover 的卡片布局）
    侧边栏：新增"我的收藏"菜单项
    空状态：引导用户去发现页浏览
```

### Phase 3 — 数据看板增强（预计 2-4 小时）

**目标**：Dashboard 从 4 个图表扩展到 8 个，覆盖更多分析维度。

```
现有 4 个图表（保留）：
  ✅ 1. 评分分布直方图
  ✅ 2. 类型分布饼图
  ✅ 3. 年代趋势（柱状图 + 均分折线）
  ✅ 4. 数据来源占比饼图

新增 4 个图表：
  [ ] 3.1 预算 vs 票房散点图
      数据字段：budget, revenue
      说明：每部电影一个点，X=预算 Y=票房
      附加：对角线参考线（回本线）
      后端：无需改动（Movie 表已有 budget/revenue 字段）

  [ ] 3.2 片长分布直方图
      数据字段：runtime
      说明：X=片长区间（每30分钟一个桶），Y=电影数
      后端：无需改动（Movie 表已有 runtime 字段）

  [ ] 3.3 国家/地区产量排行
      数据字段：production_countries
      说明：横向柱状图，Top 15 国家
      后端：无需改动（枚举接口 /api/countries 已返回数据）

  [ ] 3.4 评分 vs 热度散点图
      数据字段：vote_average, popularity
      说明：X=评分 Y=热度，观察"叫好不叫座"vs"叫座不叫好"
      后端：无需改动（Movie 表已有 popularity 字段）

后端改动：
  [ ] 3.5 /api/stats 返回新增图表数据
      - budget_revenue: [{title, budget, revenue}]   ← 散点图
      - runtime_distribution: [{range, count}]        ← 直方图
      - rating_popularity: [{title, vote_average, popularity}] ← 散点图
      注：前 3 个图表数据可从现有 API 计算，此条仅用于第 4 个图

看板布局（2列网格）：
  ┌──────────────┬──────────────┐
  │  评分分布     │  类型分布     │
  ├──────────────┼──────────────┤
  │  年代趋势（宽）              │
  ├──────────────┼──────────────┤
  │  预算×票房   │  片长分布     │
  ├──────────────┼──────────────┤
  │  国家排行     │  评分×热度    │
  ├──────────────┼──────────────┤
  │  数据来源     │  (备用位)     │
  └──────────────┴──────────────┘
```

### Phase 4 — 作品集润色（预计 1 小时）

**目标**：打开项目就让人感觉专业。

```
[ ] 4.1 favicon + 网页标题图标
    文件：frontend/public/favicon.svg
    设计：🎬 emoji 或简单的 M 字母图标

[ ] 4.2 README 更新
    - 加入技术栈徽章
    - 加入 Docker 启动说明
    - 加入 CI 状态徽章
    - 截图（发现页、详情页、看板）

[ ] 4.3 后端环境变量启动校验
    文件：backend/app.py 或 config.py
    逻辑：启动时检查 TMDB_API_KEY 是否存在且非空
         不存在 → 打印明确错误提示并退出
```

---

## 📊 工作量估算

| Phase | 内容 | 预估时间 |
|-------|------|----------|
| Phase 1 | CI + 测试 + Docker | 2-3 小时 |
| Phase 2 | 收藏功能 | 1-2 小时 |
| Phase 3 | 看板增强（+4 图表） | 2-4 小时 |
| Phase 4 | 作品集润色 | 1 小时 |
| **合计** | | **6-10 小时** |

---

## 🎯 完成后效果

```
MetaMovie/
├── .github/workflows/ci.yml          ← 自动测试
├── docker-compose.yml                ← 一键部署
├── Dockerfile.frontend
├── Dockerfile.backend
├── README.md                         ← 徽章 + 截图 + Docker 说明
├── ROADMAP_V2.md
├── backend/
│   ├── app.py                        ← 启动校验
│   ├── api/stats.py                  ← 新增图表数据
│   └── tests/                        ← 16 条（已有）
└── frontend/
    ├── src/
    │   ├── utils/
    │   │   ├── movie.js              ← 公共工具（已有）
    │   │   └── favorites.js          ← 收藏逻辑
    │   ├── components/
    │   │   └── FavoriteButton.vue    ← 收藏按钮
    │   └── views/
    │       ├── Discover.vue
    │       ├── Dashboard.vue         ← 8 个图表
    │       ├── MovieDetail.vue
    │       ├── Favorites.vue         ← 收藏列表
    │       └── NotFound.vue
    └── tests/
        ├── utils/
        │   └── movie.test.js
        └── views/
            └── Discover.test.js
```

---

## 📝 下一步

告诉我你想从哪个 Phase 开始，我直接动手写代码。建议顺序：**Phase 1 → Phase 2 → Phase 3 → Phase 4**。
