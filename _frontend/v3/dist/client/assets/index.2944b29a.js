import { r as resolveComponent, o as openBlock, c as createElementBlock, a as createVNode, w as withCtx, b as createTextVNode, d as createBlock, e as resolveDynamicComponent, S as Suspense, f as createRouter$1, g as createWebHistory, h as createSSRApp } from "./vendor.769b82aa.js";
const p = function polyfill() {
  const relList = document.createElement("link").relList;
  if (relList && relList.supports && relList.supports("modulepreload")) {
    return;
  }
  for (const link of document.querySelectorAll('link[rel="modulepreload"]')) {
    processPreload(link);
  }
  new MutationObserver((mutations) => {
    for (const mutation of mutations) {
      if (mutation.type !== "childList") {
        continue;
      }
      for (const node of mutation.addedNodes) {
        if (node.tagName === "LINK" && node.rel === "modulepreload")
          processPreload(node);
      }
    }
  }).observe(document, { childList: true, subtree: true });
  function getFetchOpts(script) {
    const fetchOpts = {};
    if (script.integrity)
      fetchOpts.integrity = script.integrity;
    if (script.referrerpolicy)
      fetchOpts.referrerPolicy = script.referrerpolicy;
    if (script.crossorigin === "use-credentials")
      fetchOpts.credentials = "include";
    else if (script.crossorigin === "anonymous")
      fetchOpts.credentials = "omit";
    else
      fetchOpts.credentials = "same-origin";
    return fetchOpts;
  }
  function processPreload(link) {
    if (link.ep)
      return;
    link.ep = true;
    const fetchOpts = getFetchOpts(link);
    fetch(link.href, fetchOpts);
  }
};
p();
var App_vue_vue_type_style_index_0_lang = "";
var _export_sfc = (sfc, props) => {
  for (const [key, val] of props) {
    sfc[key] = val;
  }
  return sfc;
};
const _sfc_main = {};
const _hoisted_1 = /* @__PURE__ */ createTextVNode("Home");
const _hoisted_2 = /* @__PURE__ */ createTextVNode("| ");
const _hoisted_3 = /* @__PURE__ */ createTextVNode("About");
function _sfc_render(_ctx, _cache) {
  const _component_router_link = resolveComponent("router-link");
  const _component_router_view = resolveComponent("router-view");
  return openBlock(), createElementBlock("div", null, [
    createVNode(_component_router_link, { to: "/" }, {
      default: withCtx(() => [
        _hoisted_1
      ]),
      _: 1
    }),
    _hoisted_2,
    createVNode(_component_router_link, { to: "/about" }, {
      default: withCtx(() => [
        _hoisted_3
      ]),
      _: 1
    }),
    createVNode(_component_router_view, null, {
      default: withCtx(({ Component }) => [
        (openBlock(), createBlock(Suspense, null, {
          default: withCtx(() => [
            (openBlock(), createBlock(resolveDynamicComponent(Component)))
          ]),
          _: 2
        }, 1024))
      ]),
      _: 1
    })
  ]);
}
var App = /* @__PURE__ */ _export_sfc(_sfc_main, [["render", _sfc_render]]);
const scriptRel = "modulepreload";
const seen = {};
const base = "/";
const __vitePreload = function preload(baseModule, deps) {
  if (!deps || deps.length === 0) {
    return baseModule();
  }
  return Promise.all(deps.map((dep) => {
    dep = `${base}${dep}`;
    if (dep in seen)
      return;
    seen[dep] = true;
    const isCss = dep.endsWith(".css");
    const cssSelector = isCss ? '[rel="stylesheet"]' : "";
    if (document.querySelector(`link[href="${dep}"]${cssSelector}`)) {
      return;
    }
    const link = document.createElement("link");
    link.rel = isCss ? "stylesheet" : scriptRel;
    if (!isCss) {
      link.as = "script";
      link.crossOrigin = "";
    }
    link.href = dep;
    document.head.appendChild(link);
    if (isCss) {
      return new Promise((res, rej) => {
        link.addEventListener("load", res);
        link.addEventListener("error", rej);
      });
    }
  })).then(() => baseModule());
};
const pages = { "./pages/About.vue": () => true ? __vitePreload(() => import("./About.2de6a8a5.js"), ["assets/About.2de6a8a5.js","assets/About.41cb2065.css","assets/vendor.769b82aa.js"]) : null, "./pages/Home.vue": () => true ? __vitePreload(() => import("./Home.57904865.js"), ["assets/Home.57904865.js","assets/Home.b5c27094.css","assets/vendor.769b82aa.js"]) : null, "./pages/Store.vue": () => true ? __vitePreload(() => import("./Store.4a500029.js"), ["assets/Store.4a500029.js","assets/Store.424e932e.css","assets/vendor.769b82aa.js"]) : null };
const routes = Object.keys(pages).map((path) => {
  const name = path.match(/\.\/pages(.*)\.vue$/)[1].toLowerCase();
  return {
    path: name === "/home" ? "/" : name,
    component: pages[path]
  };
});
function createRouter() {
  return createRouter$1({
    history: createWebHistory(),
    routes
  });
}
function createApp() {
  const app2 = createSSRApp(App);
  const router2 = createRouter();
  app2.use(router2);
  return { app: app2, router: router2 };
}
const { app, router } = createApp();
router.isReady().then(() => {
  app.mount("#app");
});
export { _export_sfc as _ };
