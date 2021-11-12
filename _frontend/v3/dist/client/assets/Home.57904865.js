import { _ as _export_sfc } from "./index.2944b29a.js";
import { i as reactive, o as openBlock, c as createElementBlock, j as createBaseVNode, t as toDisplayString, u as unref, F as Fragment, p as pushScopeId, k as popScopeId } from "./vendor.769b82aa.js";
var _imports_0 = "/assets/logo.03d6d6da.png";
var Home_vue_vue_type_style_index_0_scoped_true_lang = "";
const _withScopeId = (n) => (pushScopeId("data-v-6254821a"), n = n(), popScopeId(), n);
const _hoisted_1 = /* @__PURE__ */ _withScopeId(() => /* @__PURE__ */ createBaseVNode("h1", null, "Home", -1));
const _hoisted_2 = /* @__PURE__ */ _withScopeId(() => /* @__PURE__ */ createBaseVNode("p", null, [
  /* @__PURE__ */ createBaseVNode("img", {
    src: _imports_0,
    alt: "logo"
  })
], -1));
const _hoisted_3 = /* @__PURE__ */ _withScopeId(() => /* @__PURE__ */ createBaseVNode("p", { class: "inter" }, "this will be styled with a font-face", -1));
const _hoisted_4 = { class: "import-meta-url" };
const _hoisted_5 = { class: "protocol" };
const _sfc_main = {
  setup(__props) {
    const url = window.location.href;
    const protocol = new URL(url).protocol;
    const state = reactive({
      count: 0,
      protocol,
      url
    });
    return (_ctx, _cache) => {
      return openBlock(), createElementBlock(Fragment, null, [
        _hoisted_1,
        _hoisted_2,
        createBaseVNode("button", {
          onClick: _cache[0] || (_cache[0] = ($event) => unref(state).count++)
        }, "count is: " + toDisplayString(unref(state).count), 1),
        _hoisted_3,
        createBaseVNode("p", _hoisted_4, toDisplayString(unref(state).url), 1),
        createBaseVNode("p", _hoisted_5, toDisplayString(unref(state).protocol), 1)
      ], 64);
    };
  }
};
var Home = /* @__PURE__ */ _export_sfc(_sfc_main, [["__scopeId", "data-v-6254821a"]]);
export { Home as default };
