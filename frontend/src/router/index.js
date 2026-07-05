import { createRouter, createWebHistory } from "vue-router";

const routes = [
  {
    path: "/",
    name: "Discover",
    component: () => import("../views/Discover.vue"),
  },
  {
    path: "/dashboard",
    name: "Dashboard",
    component: () => import("../views/Dashboard.vue"),
  },
  {
    path: "/movie/:id",
    name: "MovieDetail",
    component: () => import("../views/MovieDetail.vue"),
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior() {
    return { top: 0 };
  },
});

export default router;
