"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports[Symbol.toStringTag] = "Module";
var vue = require("vue");
var serverRenderer = require("vue/server-renderer");
var vueRouter = require("vue-router");
var vuex = require("vuex");
var App_vue_vue_type_style_index_0_lang = "";
var _export_sfc = (sfc, props) => {
  for (const [key, val] of props) {
    sfc[key] = val;
  }
  return sfc;
};
const _sfc_main$3 = {};
function _sfc_ssrRender$2(_ctx, _push, _parent, _attrs) {
  const _component_router_link = vue.resolveComponent("router-link");
  const _component_router_view = vue.resolveComponent("router-view");
  _push(`<div${serverRenderer.ssrRenderAttrs(_attrs)}>`);
  _push(serverRenderer.ssrRenderComponent(_component_router_link, { to: "/" }, {
    default: vue.withCtx((_, _push2, _parent2, _scopeId) => {
      if (_push2) {
        _push2(`Home`);
      } else {
        return [
          vue.createTextVNode("Home")
        ];
      }
    }),
    _: 1
  }, _parent));
  _push(`| `);
  _push(serverRenderer.ssrRenderComponent(_component_router_link, { to: "/about" }, {
    default: vue.withCtx((_, _push2, _parent2, _scopeId) => {
      if (_push2) {
        _push2(`About`);
      } else {
        return [
          vue.createTextVNode("About")
        ];
      }
    }),
    _: 1
  }, _parent));
  _push(serverRenderer.ssrRenderComponent(_component_router_view, null, {
    default: vue.withCtx(({ Component }, _push2, _parent2, _scopeId) => {
      if (_push2) {
        serverRenderer.ssrRenderSuspense(_push2, {
          default: () => {
            serverRenderer.ssrRenderVNode(_push2, vue.createVNode(vue.resolveDynamicComponent(Component), null, null), _parent2, _scopeId);
          },
          _: 2
        });
      } else {
        return [
          (vue.openBlock(), vue.createBlock(vue.Suspense, null, {
            default: vue.withCtx(() => [
              (vue.openBlock(), vue.createBlock(vue.resolveDynamicComponent(Component)))
            ]),
            _: 2
          }, 1024))
        ];
      }
    }),
    _: 1
  }, _parent));
  _push(`</div>`);
}
const _sfc_setup$3 = _sfc_main$3.setup;
_sfc_main$3.setup = (props, ctx) => {
  const ssrContext = vue.useSSRContext();
  (ssrContext.modules || (ssrContext.modules = new Set())).add("src/App.vue");
  return _sfc_setup$3 ? _sfc_setup$3(props, ctx) : void 0;
};
var App = /* @__PURE__ */ _export_sfc(_sfc_main$3, [["ssrRender", _sfc_ssrRender$2]]);
const pages = { "./pages/About.vue": () => Promise.resolve().then(function() {
  return About$1;
}), "./pages/Home.vue": () => Promise.resolve().then(function() {
  return Home$1;
}), "./pages/Store.vue": () => Promise.resolve().then(function() {
  return Store$1;
}) };
const routes = Object.keys(pages).map((path) => {
  const name = path.match(/\.\/pages(.*)\.vue$/)[1].toLowerCase();
  return {
    path: name === "/home" ? "/" : name,
    component: pages[path]
  };
});
function createRouter() {
  return vueRouter.createRouter({
    history: vueRouter.createMemoryHistory(),
    routes
  });
}
function createApp() {
  const app = vue.createSSRApp(App);
  const router = createRouter();
  app.use(router);
  return { app, router };
}
async function render(url, manifest, rootDir) {
  const { app, router } = createApp();
  router.push(url);
  await router.isReady();
  const ctx = {};
  let html = await serverRenderer.renderToString(app, ctx);
  const preloadLinks = renderPreloadLinks(ctx.modules, manifest);
  return [html, preloadLinks];
}
function renderPreloadLinks(modules, manifest) {
  let links = "";
  const seen = new Set();
  modules.forEach((id) => {
    const files = manifest[id];
    if (files) {
      files.forEach((file) => {
        if (!seen.has(file)) {
          seen.add(file);
          links += renderPreloadLink(file);
        }
      });
    }
  });
  return links;
}
function renderPreloadLink(file) {
  if (file.endsWith(".js")) {
    return `<link rel="modulepreload" crossorigin href="${file}">`;
  } else if (file.endsWith(".css")) {
    return `<link rel="stylesheet" href="${file}">`;
  } else if (file.endsWith(".woff")) {
    return ` <link rel="preload" href="${file}" as="font" type="font/woff" crossorigin>`;
  } else if (file.endsWith(".woff2")) {
    return ` <link rel="preload" href="${file}" as="font" type="font/woff2" crossorigin>`;
  } else if (file.endsWith(".gif")) {
    return ` <link rel="preload" href="${file}" as="image" type="image/gif">`;
  } else if (file.endsWith(".jpg") || file.endsWith(".jpeg")) {
    return ` <link rel="preload" href="${file}" as="image" type="image/jpeg">`;
  } else if (file.endsWith(".png")) {
    return ` <link rel="preload" href="${file}" as="image" type="image/png">`;
  } else {
    return "";
  }
}
var About_vue_vue_type_style_index_0_scoped_true_lang = "";
const _sfc_main$2 = {
  async setup() {
    return {
      msg: "About"
    };
  }
};
function _sfc_ssrRender$1(_ctx, _push, _parent, _attrs, $props, $setup, $data, $options) {
  _push(`<h1${serverRenderer.ssrRenderAttrs(_attrs)} data-v-765f7c32>${serverRenderer.ssrInterpolate($setup.msg)}</h1>`);
}
const _sfc_setup$2 = _sfc_main$2.setup;
_sfc_main$2.setup = (props, ctx) => {
  const ssrContext = vue.useSSRContext();
  (ssrContext.modules || (ssrContext.modules = new Set())).add("src/pages/About.vue");
  return _sfc_setup$2 ? _sfc_setup$2(props, ctx) : void 0;
};
var About = /* @__PURE__ */ _export_sfc(_sfc_main$2, [["ssrRender", _sfc_ssrRender$1], ["__scopeId", "data-v-765f7c32"]]);
var About$1 = /* @__PURE__ */ Object.freeze({
  __proto__: null,
  [Symbol.toStringTag]: "Module",
  "default": About
});
var _imports_0 = "/assets/logo.03d6d6da.png";
var Home_vue_vue_type_style_index_0_scoped_true_lang = "";
const _sfc_main$1 = {
  __ssrInlineRender: true,
  setup(__props) {
    const url = typeof document === "undefined" ? new (require("url")).URL("file:" + __filename).href : document.currentScript && document.currentScript.src || new URL("entry-server.js", document.baseURI).href;
    const protocol = new URL(url).protocol;
    const state = vue.reactive({
      count: 0,
      protocol,
      url
    });
    return (_ctx, _push, _parent, _attrs) => {
      _push(`<!--[--><h1 data-v-6254821a>Home</h1><p data-v-6254821a><img${serverRenderer.ssrRenderAttr("src", _imports_0)} alt="logo" data-v-6254821a></p><button data-v-6254821a>count is: ${serverRenderer.ssrInterpolate(vue.unref(state).count)}</button><p class="inter" data-v-6254821a>this will be styled with a font-face</p><p class="import-meta-url" data-v-6254821a>${serverRenderer.ssrInterpolate(vue.unref(state).url)}</p><p class="protocol" data-v-6254821a>${serverRenderer.ssrInterpolate(vue.unref(state).protocol)}</p><!--]-->`);
    };
  }
};
const _sfc_setup$1 = _sfc_main$1.setup;
_sfc_main$1.setup = (props, ctx) => {
  const ssrContext = vue.useSSRContext();
  (ssrContext.modules || (ssrContext.modules = new Set())).add("src/pages/Home.vue");
  return _sfc_setup$1 ? _sfc_setup$1(props, ctx) : void 0;
};
var Home = /* @__PURE__ */ _export_sfc(_sfc_main$1, [["__scopeId", "data-v-6254821a"]]);
var Home$1 = /* @__PURE__ */ Object.freeze({
  __proto__: null,
  [Symbol.toStringTag]: "Module",
  "default": Home
});
var Store_vue_vue_type_style_index_0_scoped_true_lang = "";
const _sfc_main = {
  async setup() {
    const store = vuex.createStore({
      state: {
        foo: "bar"
      }
    });
    return store.state;
  }
};
function _sfc_ssrRender(_ctx, _push, _parent, _attrs, $props, $setup, $data, $options) {
  _push(`<h1${serverRenderer.ssrRenderAttrs(_attrs)} data-v-056cb602>${serverRenderer.ssrInterpolate(_ctx.foo)}</h1>`);
}
const _sfc_setup = _sfc_main.setup;
_sfc_main.setup = (props, ctx) => {
  const ssrContext = vue.useSSRContext();
  (ssrContext.modules || (ssrContext.modules = new Set())).add("src/pages/Store.vue");
  return _sfc_setup ? _sfc_setup(props, ctx) : void 0;
};
var Store = /* @__PURE__ */ _export_sfc(_sfc_main, [["ssrRender", _sfc_ssrRender], ["__scopeId", "data-v-056cb602"]]);
var Store$1 = /* @__PURE__ */ Object.freeze({
  __proto__: null,
  [Symbol.toStringTag]: "Module",
  "default": Store
});
exports.render = render;
