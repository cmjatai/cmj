(window.webpackJsonp=window.webpackJsonp||[]).push([["chunk-753c49cc"],{"06f0":function(t,e,a){"use strict";a("68e0")},"0c47":function(t,e,a){"use strict";var i=a("cfe9");a("d44e")(i.JSON,"JSON",!0)},"131a":function(t,e,a){"use strict";a("23e7")({target:"Object",stat:!0},{setPrototypeOf:a("d2bb")})},"1da1":function(t,e,a){"use strict";a.d(e,"a",(function(){return n}));a("d3b7");function i(t,e,a,i,n,o,s){try{var r=t[o](s),c=r.value}catch(t){return void a(t)}r.done?e(c):Promise.resolve(c).then(i,n)}function n(t){return function(){var e=this,a=arguments;return new Promise((function(n,o){var s=t.apply(e,a);function r(t){i(s,n,o,r,c,"next",t)}function c(t){i(s,n,o,r,c,"throw",t)}r(void 0)}))}}},"1e7d":function(t,e,a){"use strict";a("5170")},"1f68":function(t,e,a){"use strict";var i=a("83ab"),n=a("edd0"),o=a("861d"),s=a("1787"),r=a("7b0b"),c=a("1d80"),l=Object.getPrototypeOf,u=Object.setPrototypeOf,d=Object.prototype;if(i&&l&&u&&!("__proto__"in d))try{n(d,"__proto__",{configurable:!0,get:function(){return l(r(this))},set:function(t){var e=c(this);s(t)&&o(e)&&u(e,t)}})}catch(t){}},2130:function(t,e,a){"use strict";(function(t){a("99af"),a("4de4"),a("d3b7");var i=a("d827");e.a={name:"pauta-online",props:["sessao"],components:{ItemDePauta:i.a},data:function(){return{itens:{expedientesessao_list:[],ordemdia_list:{},expedientemateria_list:{}},init:!1,app:["sessao"],model:["expedientemateria","ordemdia"]}},computed:{itensDaOrdemDia:{get:function(){return t.orderBy(this.itens.ordemdia_list,"numero_ordem")}},itensDoExpediente:{get:function(){return t.orderBy(this.itens.expedientemateria_list,"numero_ordem")}}},mounted:function(){var t=this;setTimeout((function(){t.fetchItens(),t.fetchExpedienteSessao()}),1e3)},methods:{expediente:function(e){var a=this.itens.expedientesessao_list,i=t.filter(a,["tipo",e]);return i.length>0?i[0].conteudo:""},fetch:function(t){if("post_delete"!==t.action){var e=this;e.getObject(t).then((function(a){if(a.sessao_plenaria===e.sessao.id&&null===a.parent){var i=e.itens["".concat(t.model,"_list")],n=t.id;e.$nextTick().then((function(){e.$set(i,n,a)}))}"post_save"===t.action&&t.created&&(t.app="materia",t.model="materialegislativa",t.id=a.materia,e.getObject(t).then((function(t){e.sendMessage({alert:"info",message:"<strong>".concat(t.__str__," adicionado a esta sessão.</strong><br><i>").concat(t.ementa,"</i>"),time:25})})))}))}else this.$delete(this.itens["".concat(t.model,"_list")],t.id)},fetchItens:function(){var e=arguments.length>0&&void 0!==arguments[0]?arguments[0]:this.model,a=this;t.mapKeys(e,(function(e,i){t.mapKeys(a.itens["".concat(e,"_list")],(function(t,e){t.vue_validate=!1})),a.$nextTick().then((function(){a.fetchList(1,e)}))}))},fetchExpedienteSessao:function(){var t=this;return t.utils.getByMetadata({action:"expedientes",app:"sessao",model:"sessaoplenaria",id:t.sessao.id}).then((function(e){t.$set(t.itens,"expedientesessao_list",e.data.results)})).then((function(t){}))},fetchList:function(){var e=arguments.length>0&&void 0!==arguments[0]?arguments[0]:null,a=arguments.length>1&&void 0!==arguments[1]?arguments[1]:null,i=this,n="&sessao_plenaria=".concat(this.sessao.id,"&parent__isnull=True");i.utils.getModelOrderedList("sessao",a,"numero_ordem",null===e?1:e,n).then((function(e){i.init=!0,t.each(e.data.results,(function(t,e){t.vue_validate=!0,t.id in i.itens["".concat(a,"_list")]?i.itens["".concat(a,"_list")][t.id]=t:i.$set(i.itens["".concat(a,"_list")],t.id,t)})),i.$nextTick().then((function(){null!==e.data.pagination.next_page?i.fetchList(e.data.pagination.next_page,a):t.mapKeys(i.itens["".concat(a,"_list")],(function(t,e){t.vue_validate||i.$delete(i.itens["".concat(a,"_list")],t.id)}))}))})).catch((function(t){i.init=!0,i.sendMessage({alert:"danger",message:"Não foi possível recuperar a Ordem do Dia.",time:5})}))}}}}).call(this,a("2ef0"))},"23a4":function(t,e,a){"use strict";(function(t){a("99af"),a("d3b7"),a("3ca3"),a("ddb0"),a("2b3d"),a("bf19"),a("9861"),a("88a7"),a("271a"),a("5494");e.a={name:"materia-pauta",props:["materia","type"],data:function(){return{app:["materia"],model:["materialegislativa","tramitacao","anexada","autoria"],autores:{},tramitacao:{ultima:{},status:{}},tipo_string:"",blob:null,baixando:!1}},watch:{materia:function(t){this.refresh()}},computed:{data_apresentacao:function(){try{var t=this.stringToDate(this.materia.data_apresentacao,"yyyy-mm-dd","-");return"".concat(t.getDate(),"/").concat(t.getMonth()+1,"/").concat(t.getFullYear())}catch(t){return""}},autores_list:{get:function(){return t.orderBy(this.autores,"nome")}}},mounted:function(){var t=this;t.blob||void 0===t.materia.id||t.refresh()},methods:{fetchUltimaTramitacao:function(){var t=this;return t.utils.getByMetadata({action:"ultima_tramitacao",app:"materia",model:"materialegislativa",id:t.materia.id}).then((function(e){t.tramitacao.ultima=e.data,void 0!==t.tramitacao.ultima.id&&t.getObject({action:"",app:"materia",model:"statustramitacao",id:t.tramitacao.ultima.status}).then((function(e){t.tramitacao.status=e}))}))},clickFile:function(t){var e=window.URL.createObjectURL(this.blob);window.location=e},fetch:function(t){var e=this;void 0!==e.materia&&e.materia.id===t.id&&t.model===e.model[0]&&this.refresh()},refresh:function(){var e=this;void 0!==e.materia&&void 0!==e.materia.id&&(e.getObject({app:"materia",model:"tipomaterialegislativa",id:e.materia.tipo}).then((function(t){e.tipo_string=t.descricao})),e.$set(e,"autores",{}),e.$nextTick().then((function(){t.each(e.materia.autores,(function(t){e.getObject({app:"base",model:"autor",id:t}).then((function(t){e.$set(e.autores,t.id,t),e.fetchUltimaTramitacao()}))}))})))}}}}).call(this,a("2ef0"))},"23dc":function(t,e,a){"use strict";a("d44e")(Math,"Math",!0)},"24c5":function(t,e,a){"use strict";(function(t,i){var n=a("c7eb"),o=a("1da1"),s=(a("99af"),a("caad"),a("fb6a"),a("ac1f"),a("2532"),a("5319"),a("edd2")),r=a("9e1e"),c=a("6c99");e.a={name:"item-de-pauta",props:["item","type"],components:{MateriaPauta:s.a,VotoParlamentar:r.a,NormaSimpleModalView:c.a},data:function(){return{app:["materia","norma","sessao"],model:["materialegislativa","tramitacao","anexada","autoria","legislacaocitada","documentoacessorio","registrovotacao","registroleitura","votoparlamentar"],materia:{},tramitacao:{ultima:{},status:{}},anexadas:{},legislacaocitada:{},documentoacessorio:{},modal_legis_citada:null,registro:null}},watch:{modal_legis_citada:function(e,a){var i=this;null!==e&&this.$nextTick().then((function(){t("#modal-legis-citada-".concat(e.id)).modal("show"),t("#modal-legis-citada-".concat(e.id)).on("hidden.bs.modal",(function(t){i.modal_legis_citada=null}))}))},item:function(t,e){var a=this;this.$nextTick().then((function(){a.registro=null})).then((function(){a.fetchRegistroDeVoto()}))}},computed:{data_apresentacao:function(){try{var t=this.stringToDate(this.materia.data_apresentacao,"yyyy-mm-dd","-");return"".concat(t.getDate(),"/").concat(t.getMonth()+1,"/").concat(t.getFullYear())}catch(t){return""}},observacao:function(){var t=this.item.observacao;return t=(t=(t=(t=t.replace(/^\r\n/g,"")).replace(/\r\n/g,"<br />")).replace(/\r/g," ")).replace(/\n/g,"<br />")},itensAnexados:{get:function(){return i.orderBy(this.anexadas,["-tipo","data_apresentacao","id"])}},itensLegislacaoCitada:{get:function(){return i.orderBy(this.legislacaocitada,"norma")}},itensDocumentosAcessorios:{get:function(){return i.orderBy(this.documentoacessorio,"data")}},votacaoAberta:{get:function(){return this.item.votacao_aberta&&this.item.tipo_votacao<=2}},votacaoPedidoPrazoAberta:{get:function(){return this.item.votacao_aberta_pedido_prazo&&this.item.tipo_votacao<=2}},statusVotacao:{get:function(){var t="",e=this.item.resultado;return this.votacaoAberta?t="votacao-aberta":"Aprovado"===e?t="result-aprovado":"Rejeitado"===e?t="result-rejeitado":"Pedido de Vista"===e?t="result-vista":"Prazo Regimental"===e&&(t="result-prazo"),t}}},mounted:function(){this.refresh()},methods:{refresh:function(){var t=this;t.fetchMateria().then((function(e){i.each(t.materia.anexadas,(function(e,a){t.fetchMateria({action:"post_save",app:t.app[0],model:t.model[0],id:e})}))})),t.$nextTick().then((function(){})).then((function(){t.fetchLegislacaoCitada()})).then((function(){t.fetchDocumentoAcessorio()})).then((function(){t.fetchRegistroDeVoto()}))},fetch:function(t){var e=this;void 0!==t&&("materia"===t.app&&"materialegislativa"===t.model?(t.id===e.item.materia||t.id in e.materia.anexadas)&&e.fetchMateria(t):"materia"===t.app&&"anexada"===t.model?(e.$set(e,"anexadas",{}),e.refreshState({action:"",app:e.app[0],model:e.model[0],id:e.item.materia}).then((function(t){e.refresh()}))):"materia"===t.app&&"autoria"===t.model?e.refreshState({action:"",app:e.app[0],model:e.model[0],id:e.item.materia}).then((function(t){e.refresh()})):"materia"===t.app&&"tramitacao"===t.model?e.fetchUltimaTramitacao(t):"norma"===t.app&&"legislacaocitada"===t.model?e.fetchLegislacaoCitada():"materia"===t.app&&"documentoacessorio"===t.model?e.fetchDocumentoAcessorio():"sessao"===t.app&&["registrovotacao","registroleitura","votoparlamentar"].includes(t.model)&&e.fetchRegistroDeVoto(t))},fetchRegistroDeVoto:function(t){var e=this;return Object(o.a)(Object(n.a)().mark((function a(){var o,s,r,c;return Object(n.a)().wrap((function(a){for(;;)switch(a.prev=a.next){case 0:s=4===(o=e).item.tipo_votacao?"registroleitura":"registrovotacao",r="expedientemateria"===o.type?"expediente":"ordem",o.item.resultado.length>0&&null===o.registro&&(c="&".concat(r,"=").concat(o.item.id,"&o=-id"),o.utils.getModelList("sessao",s,1,c).then((function(t){i.each(t.data.results.slice(0,1),(function(t){o.registro=t,o.refreshState({app:"sessao",model:s,value:t,id:t.id})}))})).catch((function(t){o.sendMessage({alert:"danger",message:"Não foi possível recuperar o Registro de Votos/Leitura.",time:5})}))),o.nulls.includes(t)||o.nulls.includes(o.registro)||o.registro.id!==t.id||o.getObject(t).then((function(t){o.nulls.includes(t)?o.registro=null:t.materia===o.item.materia&&(o.registro=t)}));case 5:case"end":return a.stop()}}),a)})))()},fetchDocumentoAcessorio:function(){var t=arguments.length>0&&void 0!==arguments[0]?arguments[0]:1,e=this,a="&materia=".concat(e.item.materia);e.utils.getModelList("materia","documentoacessorio",t,a).then((function(t){i.each(t.data.results,(function(t){e.$set(e.documentoacessorio,t.id,t)})),null!==t.data.pagination.next_page&&e.$nextTick().then((function(){e.fetchDocumentoAcessorio(t.data.pagination.next_page)}))})).catch((function(t){e.sendMessage({alert:"danger",message:"Não foi possível recuperar a lista de Documentos Acessórios.",time:5})}))},fetchLegislacaoCitada:function(){var t=arguments.length>0&&void 0!==arguments[0]?arguments[0]:1,e=this,a="&materia=".concat(e.item.materia);e.utils.getModelList("norma","legislacaocitada",t,a).then((function(t){i.each(t.data.results,(function(t){e.$set(e.legislacaocitada,t.id,t)})),null!==t.data.pagination.next_page&&e.$nextTick().then((function(){e.fetchLegislacaoCitada(t.data.pagination.next_page)}))})).catch((function(t){e.sendMessage({alert:"danger",message:"Não foi possível recuperar a lista de Legislação Citada.",time:5})}))},fetchMateria:function(t){var e=this;return e.getObject({action:"",app:e.app[0],model:e.model[0],id:void 0!==t?t.id:e.item.materia}).then((function(t){return t.id===e.item.materia?e.materia=t:e.$set(e.anexadas,t.id,t),t}))},fetchUltimaTramitacao:function(){var t=this;return t.utils.getByMetadata({action:"ultima_tramitacao",app:"materia",model:"materialegislativa",id:t.item.materia}).then((function(e){t.tramitacao.ultima=e.data,void 0!==t.tramitacao.ultima.id&&t.getObject({action:"",app:"materia",model:"statustramitacao",id:t.tramitacao.ultima.status}).then((function(e){t.tramitacao.status=e}))}))}}}}).call(this,a("1157"),a("2ef0"))},"2a27":function(t,e,a){"use strict";a("722a")},3410:function(t,e,a){"use strict";var i=a("23e7"),n=a("d039"),o=a("7b0b"),s=a("e163"),r=a("e177");i({target:"Object",stat:!0,forced:n((function(){s(1)})),sham:!r},{getPrototypeOf:function(t){return s(o(t))}})},4670:function(t,e,a){"use strict";a.r(e);var i=a("5530"),n=(a("14d9"),a("eeb8").a),o=(a("fe51"),a("2877")),s=Object(o.a)(n,(function(){var t=this,e=t._self._c;return e("div",{class:"sessao-plenaria-topo"},[e("div",{staticClass:"tit"},[t._v(" "+t._s(t.titulo)+" ")]),e("div",{staticClass:"subtitulo"},[e("span",[t._v(t._s(t.subtitulo))]),t._v(" – "),e("span",[t._v(t._s(t.date_text))])])])}),[],!1,null,null,null).exports,r=a("2130").a,c=(a("1e7d"),Object(o.a)(r,(function(){var t=this,e=t._self._c;return e("div",{staticClass:"pauta-online"},[0===t.itens.ordemdia_list.length&&t.init?e("div",{staticClass:"empty-list"},[t._v(" Não existem Itens na Ordem do Dia com seus critérios de busca! ")]):t._e(),t.init?t._e():e("div",{staticClass:"empty-list"},[t._v(" Carregando listagem... ")]),e("div",{class:["item-expediente",t.nivel(t.NIVEL3,t.itens.expedientesessao_list.length>0)]},[e("div",{staticClass:"inner",domProps:{innerHTML:t._s(t.expediente(1))}})]),e("div",{staticClass:"container-expedientemateria"},[t.itensDoExpediente.length?e("div",{staticClass:"titulo-container"},[t._v("Matérias do Grande Expediente")]):t._e(),e("div",{staticClass:"inner"},t._l(t.itensDoExpediente,(function(t){return e("item-de-pauta",{key:"exp".concat(t.id),attrs:{item:t,type:"expedientemateria"}})})),1)]),e("div",{class:["item-expediente",t.nivel(t.NIVEL3,t.itens.expedientesessao_list.length>0)]},[e("div",{staticClass:"inner",domProps:{innerHTML:t._s(t.expediente(3))}})]),e("div",{staticClass:"container-ordemdia"},[t.itensDaOrdemDia.length?e("div",{staticClass:"titulo-container"},[t._v("Matérias da Ordem do Dia")]):t._e(),e("div",{staticClass:"inner"},t._l(t.itensDaOrdemDia,(function(t){return e("item-de-pauta",{key:"od".concat(t.id),attrs:{item:t,type:"ordemdia"}})})),1)]),e("div",{class:["item-expediente",t.nivel(t.NIVEL3,t.itens.expedientesessao_list.length>0)]},[e("div",{staticClass:"inner",domProps:{innerHTML:t._s(t.expediente(4))}})])])}),[],!1,null,null,null).exports),l=a("2f62"),u={name:"sessao-plenaria-online",components:{SessaoPlenariaTopo:s,PautaOnline:c},data:function(){return{sessao:null,idd:parseInt(this.$route.params.id),app:["sessao"],model:["sessaoplenaria"]}},beforeDestroy:function(){this.setNivelDetalheVisivel(!1)},mounted:function(){var t=this,e=this;e.setNivelDetalheVisivel(!0),e.$nextTick((function(){e.getObject({action:"",id:e.idd,app:e.app[0],model:e.model[0]}).then((function(e){t.sessao=e})).catch((function(){t.sessao=void 0!==t.cache.sessao&&void 0!==t.cache.sessao.sessaoplenaria&&void 0!==t.cache.sessao.sessaoplenaria[t.idd]?t.cache.sessao.sessaoplenaria[t.idd]:null}))}))},methods:Object(i.a)(Object(i.a)({},l.a.mapActions(["setNivelDetalheVisivel"])),{},{fetch:function(t){var e=this;t.id===this.idd&&t.app===this.app[0]&&t.model===this.model[0]&&("post_delete"===t.action?setTimeout((function(){e.sendMessage({alert:"danger",message:"Sessão Plenária foi excluída",time:5}),e.$router.push({name:"sessao_list_link"})}),500):this.sessao=this.cache.sessao.sessaoplenaria[this.idd])}})},d=(a("2a27"),Object(o.a)(u,(function(){var t=this._self._c;return t("div",{staticClass:"sessao-plenaria-online"},[this.sessao?[t("sessao-plenaria-topo",{attrs:{sessao:this.sessao}}),t("pauta-online",{attrs:{sessao:this.sessao}})]:this._e()],2)}),[],!1,null,null,null));e.default=d.exports},"49ae":function(t,e,a){},5170:function(t,e,a){},"68e0":function(t,e,a){},"68e5":function(t,e,a){"use strict";a("79e9")},"6aa6":function(t,e,a){"use strict";a("fca8")},"722a":function(t,e,a){},"79e9":function(t,e,a){},"944a":function(t,e,a){"use strict";var i=a("d066"),n=a("e065"),o=a("d44e");n("toStringTag"),o(i("Symbol"),"Symbol")},"9e1e":function(t,e,a){"use strict";var i={name:"voto-parlamentar",props:["item"],components:{},data:function(){return{app:[],model:[]}},watch:{},computed:{},mounted:function(){this.refresh()},methods:{refresh:function(){}}},n=(a("06f0"),a("2877")),o=Object(n.a)(i,(function(){var t=this._self._c;return t("div",{class:["voto-parlamentar"]},[t("a",{staticClass:"btn btn-lg btn-success",attrs:{href:"#"}},[this._v("SIM")]),t("a",{staticClass:"btn btn-lg btn-danger",attrs:{href:"#"}},[this._v("NÃO")]),t("a",{staticClass:"btn btn-lg btn-warning",attrs:{href:"#"}},[this._v("Abstenção")])])}),[],!1,null,null,null);e.a=o.exports},b636:function(t,e,a){"use strict";a("e065")("asyncIterator")},c7eb:function(t,e,a){"use strict";a.d(e,"a",(function(){return n}));a("a4d3"),a("e01a"),a("b636"),a("d28b"),a("944a"),a("d9e2"),a("14d9"),a("fb6a"),a("b0c0"),a("0c47"),a("23dc"),a("3410"),a("1f68"),a("131a"),a("d3b7"),a("3ca3"),a("159b"),a("ddb0");var i=a("53ca");function n(){
/*! regenerator-runtime -- Copyright (c) 2014-present, Facebook, Inc. -- license (MIT): https://github.com/facebook/regenerator/blob/main/LICENSE */
n=function(){return e};var t,e={},a=Object.prototype,o=a.hasOwnProperty,s=Object.defineProperty||function(t,e,a){t[e]=a.value},r="function"==typeof Symbol?Symbol:{},c=r.iterator||"@@iterator",l=r.asyncIterator||"@@asyncIterator",u=r.toStringTag||"@@toStringTag";function d(t,e,a){return Object.defineProperty(t,e,{value:a,enumerable:!0,configurable:!0,writable:!0}),t[e]}try{d({},"")}catch(t){d=function(t,e,a){return t[e]=a}}function f(t,e,a,i){var n=e&&e.prototype instanceof _?e:_,o=Object.create(n.prototype),r=new T(i||[]);return s(o,"_invoke",{value:k(t,a,r)}),o}function m(t,e,a){try{return{type:"normal",arg:t.call(e,a)}}catch(t){return{type:"throw",arg:t}}}e.wrap=f;var h="suspendedStart",p="executing",v="completed",g={};function _(){}function b(){}function y(){}var x={};d(x,c,(function(){return this}));var w=Object.getPrototypeOf,O=w&&w(w(M([])));O&&O!==a&&o.call(O,c)&&(x=O);var C=y.prototype=_.prototype=Object.create(x);function L(t){["next","throw","return"].forEach((function(e){d(t,e,(function(t){return this._invoke(e,t)}))}))}function j(t,e){function a(n,s,r,c){var l=m(t[n],t,s);if("throw"!==l.type){var u=l.arg,d=u.value;return d&&"object"==Object(i.a)(d)&&o.call(d,"__await")?e.resolve(d.__await).then((function(t){a("next",t,r,c)}),(function(t){a("throw",t,r,c)})):e.resolve(d).then((function(t){u.value=t,r(u)}),(function(t){return a("throw",t,r,c)}))}c(l.arg)}var n;s(this,"_invoke",{value:function(t,i){function o(){return new e((function(e,n){a(t,i,e,n)}))}return n=n?n.then(o,o):o()}})}function k(e,a,i){var n=h;return function(o,s){if(n===p)throw Error("Generator is already running");if(n===v){if("throw"===o)throw s;return{value:t,done:!0}}for(i.method=o,i.arg=s;;){var r=i.delegate;if(r){var c=D(r,i);if(c){if(c===g)continue;return c}}if("next"===i.method)i.sent=i._sent=i.arg;else if("throw"===i.method){if(n===h)throw n=v,i.arg;i.dispatchException(i.arg)}else"return"===i.method&&i.abrupt("return",i.arg);n=p;var l=m(e,a,i);if("normal"===l.type){if(n=i.done?v:"suspendedYield",l.arg===g)continue;return{value:l.arg,done:i.done}}"throw"===l.type&&(n=v,i.method="throw",i.arg=l.arg)}}}function D(e,a){var i=a.method,n=e.iterator[i];if(n===t)return a.delegate=null,"throw"===i&&e.iterator.return&&(a.method="return",a.arg=t,D(e,a),"throw"===a.method)||"return"!==i&&(a.method="throw",a.arg=new TypeError("The iterator does not provide a '"+i+"' method")),g;var o=m(n,e.iterator,a.arg);if("throw"===o.type)return a.method="throw",a.arg=o.arg,a.delegate=null,g;var s=o.arg;return s?s.done?(a[e.resultName]=s.value,a.next=e.nextLoc,"return"!==a.method&&(a.method="next",a.arg=t),a.delegate=null,g):s:(a.method="throw",a.arg=new TypeError("iterator result is not an object"),a.delegate=null,g)}function A(t){var e={tryLoc:t[0]};1 in t&&(e.catchLoc=t[1]),2 in t&&(e.finallyLoc=t[2],e.afterLoc=t[3]),this.tryEntries.push(e)}function E(t){var e=t.completion||{};e.type="normal",delete e.arg,t.completion=e}function T(t){this.tryEntries=[{tryLoc:"root"}],t.forEach(A,this),this.reset(!0)}function M(e){if(e||""===e){var a=e[c];if(a)return a.call(e);if("function"==typeof e.next)return e;if(!isNaN(e.length)){var n=-1,s=function a(){for(;++n<e.length;)if(o.call(e,n))return a.value=e[n],a.done=!1,a;return a.value=t,a.done=!0,a};return s.next=s}}throw new TypeError(Object(i.a)(e)+" is not iterable")}return b.prototype=y,s(C,"constructor",{value:y,configurable:!0}),s(y,"constructor",{value:b,configurable:!0}),b.displayName=d(y,u,"GeneratorFunction"),e.isGeneratorFunction=function(t){var e="function"==typeof t&&t.constructor;return!!e&&(e===b||"GeneratorFunction"===(e.displayName||e.name))},e.mark=function(t){return Object.setPrototypeOf?Object.setPrototypeOf(t,y):(t.__proto__=y,d(t,u,"GeneratorFunction")),t.prototype=Object.create(C),t},e.awrap=function(t){return{__await:t}},L(j.prototype),d(j.prototype,l,(function(){return this})),e.AsyncIterator=j,e.async=function(t,a,i,n,o){void 0===o&&(o=Promise);var s=new j(f(t,a,i,n),o);return e.isGeneratorFunction(a)?s:s.next().then((function(t){return t.done?t.value:s.next()}))},L(C),d(C,u,"Generator"),d(C,c,(function(){return this})),d(C,"toString",(function(){return"[object Generator]"})),e.keys=function(t){var e=Object(t),a=[];for(var i in e)a.push(i);return a.reverse(),function t(){for(;a.length;){var i=a.pop();if(i in e)return t.value=i,t.done=!1,t}return t.done=!0,t}},e.values=M,T.prototype={constructor:T,reset:function(e){if(this.prev=0,this.next=0,this.sent=this._sent=t,this.done=!1,this.delegate=null,this.method="next",this.arg=t,this.tryEntries.forEach(E),!e)for(var a in this)"t"===a.charAt(0)&&o.call(this,a)&&!isNaN(+a.slice(1))&&(this[a]=t)},stop:function(){this.done=!0;var t=this.tryEntries[0].completion;if("throw"===t.type)throw t.arg;return this.rval},dispatchException:function(e){if(this.done)throw e;var a=this;function i(i,n){return r.type="throw",r.arg=e,a.next=i,n&&(a.method="next",a.arg=t),!!n}for(var n=this.tryEntries.length-1;n>=0;--n){var s=this.tryEntries[n],r=s.completion;if("root"===s.tryLoc)return i("end");if(s.tryLoc<=this.prev){var c=o.call(s,"catchLoc"),l=o.call(s,"finallyLoc");if(c&&l){if(this.prev<s.catchLoc)return i(s.catchLoc,!0);if(this.prev<s.finallyLoc)return i(s.finallyLoc)}else if(c){if(this.prev<s.catchLoc)return i(s.catchLoc,!0)}else{if(!l)throw Error("try statement without catch or finally");if(this.prev<s.finallyLoc)return i(s.finallyLoc)}}}},abrupt:function(t,e){for(var a=this.tryEntries.length-1;a>=0;--a){var i=this.tryEntries[a];if(i.tryLoc<=this.prev&&o.call(i,"finallyLoc")&&this.prev<i.finallyLoc){var n=i;break}}n&&("break"===t||"continue"===t)&&n.tryLoc<=e&&e<=n.finallyLoc&&(n=null);var s=n?n.completion:{};return s.type=t,s.arg=e,n?(this.method="next",this.next=n.finallyLoc,g):this.complete(s)},complete:function(t,e){if("throw"===t.type)throw t.arg;return"break"===t.type||"continue"===t.type?this.next=t.arg:"return"===t.type?(this.rval=this.arg=t.arg,this.method="return",this.next="end"):"normal"===t.type&&e&&(this.next=e),g},finish:function(t){for(var e=this.tryEntries.length-1;e>=0;--e){var a=this.tryEntries[e];if(a.finallyLoc===t)return this.complete(a.completion,a.afterLoc),E(a),g}},catch:function(t){for(var e=this.tryEntries.length-1;e>=0;--e){var a=this.tryEntries[e];if(a.tryLoc===t){var i=a.completion;if("throw"===i.type){var n=i.arg;E(a)}return n}}throw Error("illegal catch attempt")},delegateYield:function(e,a,i){return this.delegate={iterator:M(e),resultName:a,nextLoc:i},"next"===this.method&&(this.arg=t),g}},e}},d827:function(t,e,a){"use strict";a("99af");var i=a("24c5").a,n=(a("68e5"),a("2877")),o=Object(n.a)(i,(function(){var t=this,e=t._self._c;return e("div",{class:["item-de-pauta",t.type]},[e("div",{class:["empty-list",void 0===t.materia.id?"":"d-none"]},[t._v(" Carregando Matéria... ")]),t.votacaoAberta&&t.user&&t.user.votante?e("voto-parlamentar"):t._e(),e("div",{staticClass:"status-votacao"},[t.registro&&!t.votacaoAberta&&4!=t.item.tipo_votacao?e("div",{staticClass:"votos"},[t.registro.numero_abstencoes?e("div",{staticClass:"voto-abs"},[e("span",{staticClass:"valor"},[t._v(t._s(t.registro.numero_abstencoes))]),e("span",{staticClass:"titulo"},[t._v("ABS")])]):t._e(),e("div",{staticClass:"voto-nao"},[e("span",{staticClass:"valor"},[t._v(t._s(t.registro.numero_votos_nao))]),e("span",{staticClass:"titulo"},[t._v("NÃO")])]),e("div",{staticClass:"voto-sim"},[e("span",{staticClass:"valor"},[t._v(t._s(t.registro.numero_votos_sim))]),e("span",{staticClass:"titulo"},[t._v("SIM")])])]):t._e(),e("div",{class:[t.statusVotacao]},[t.votacaoPedidoPrazoAberta?e("span",[t._v("VOTAÇÃO ABERTA PARA PEDIDO DE ADIAMENTO")]):t.votacaoAberta?e("span",[t._v("VOTAÇÃO ABERTA")]):t.item.resultado?e("span",[t._v(t._s(t.item.resultado))]):e("span",[t._v("Tramitando")])])]),e("materia-pauta",{attrs:{materia:t.materia,type:t.type}}),e("div",{class:["item-body"]}),e("div",{class:["item-body",void 0!==t.materia.id&&t.materia.anexadas.length>0?"col-anexadas":""]},[e("div",{staticClass:"col-1-body"},[e("div",{staticClass:"status-tramitacao"},[e("div",{class:["observacao",t.nivel(t.NIVEL3,t.observacao.length>0)],domProps:{innerHTML:t._s(t.observacao)}})]),e("div",{class:["sub-containers",0===t.itensLegislacaoCitada.length?"d-none":"container-legis-citada"]},[t._m(0),e("div",{staticClass:"inner"},t._l(t.itensLegislacaoCitada,(function(a){return e("button",{key:"legiscit".concat(a.id),staticClass:"btn btn-link",attrs:{type:"button","data-toggle":"modal","data-target":"modal-legis-citada-".concat(a.id)},on:{click:function(e){t.modal_legis_citada=a}}},[t._v(" "+t._s(a.__str__)+" ")])})),0)]),e("div",{class:["sub-containers",t.nivel(t.NIVEL2,t.itensDocumentosAcessorios.length>0),0===t.itensDocumentosAcessorios.length?"d-none":"container-docs-acessorios"]},[t._m(1),e("div",{staticClass:"inner"},t._l(t.itensDocumentosAcessorios,(function(a){return e("a",{key:"docsacc".concat(a.id),staticClass:"btn btn-link",attrs:{href:a.arquivo}},[t._v(" "+t._s(a.__str__)+" ")])})),0)])]),e("div",{staticClass:"col-2-body"},[e("div",{class:["sub-containers",t.nivel(t.NIVEL1,t.itensAnexados.length>0)]},[t._m(2),e("div",{staticClass:"inner"},t._l(t.itensAnexados,(function(a){return e("div",{key:"".concat(t.type).concat(a.id)},[e("materia-pauta",{attrs:{materia:a,type:t.type}})],1)})),0)])])]),t.modal_legis_citada?e("norma-simple-modal-view",{attrs:{html_id:"modal-legis-citada-".concat(t.modal_legis_citada.id),modal_norma:null,idd:t.modal_legis_citada.norma}}):t._e()],1)}),[function(){var t=this._self._c;return t("div",{staticClass:"title"},[t("span",[this._v(" Legislação Citada ")])])},function(){var t=this._self._c;return t("div",{staticClass:"title"},[t("span",[this._v(" Documentos Acessórios ")])])},function(){var t=this._self._c;return t("div",{staticClass:"title"},[t("span",[this._v(" Matérias Anexadas em Tramitação")])])}],!1,null,null,null);e.a=o.exports},edd2:function(t,e,a){"use strict";a("99af");var i=a("23a4").a,n=(a("6aa6"),a("2877")),o=Object(n.a)(i,(function(){var t=this,e=t._self._c;return e("div",{class:["materia-pauta"]},[e("a",{staticClass:"epigrafe",attrs:{href:t.materia.link_detail_backend,target:"_blank"}},[t._v(t._s(t.tipo_string)+" nº "+t._s(t.materia.numero)+"/"+t._s(t.materia.ano))]),e("div",{class:["item-header",t.tipo_string?"":"d-none"]},[e("div",{staticClass:"link-file",attrs:{id:"".concat(t.type,"-").concat(t.materia.id)}},[e("a",{class:["btn btn-link","link-file-".concat(t.materia.id),t.blob?"":"d-none"],on:{click:t.clickFile}},[e("i",{staticClass:"far fa-2x fa-file-pdf"})]),e("a",{class:["btn btn-link","link-file-".concat(t.materia.id)],attrs:{href:t.materia.texto_original,target:"_blank"}},[e("i",{staticClass:"far fa-2x fa-file-pdf"})]),e("small",{class:t.baixando?"":"d-none"},[t._v("Baixando"),e("br"),t._v("Arquivo")])]),e("div",{staticClass:"data-header"},[e("div",{staticClass:"detail-header"},[e("div",{staticClass:"protocolo-data"},[e("span",[t._v(" Protocolo: "),e("strong",[t._v(t._s(t.materia.numero_protocolo))])]),e("span",[t._v(t._s(t.data_apresentacao))])]),e("div",{staticClass:"autoria"},t._l(t.autores_list,(function(a,i){return e("span",{key:"au".concat(i)},[t._v(t._s(a.nome))])})),0)]),e("div",{staticClass:"ementa",domProps:{innerHTML:t._s(t.materia.ementa)}}),e("div",{staticClass:"status-tramitacao"},[e("div",{class:["ultima_tramitacao",t.nivel(t.NIVEL2,null!==t.tramitacao.ultima)]},[e("strong",[t._v("Situação:")]),t._v(" "+t._s(t.tramitacao.status.descricao)),e("br"),e("strong",[t._v("Ultima Ação:")]),t._v(" "+t._s(t.tramitacao.ultima.texto)+" ")])])])])])}),[],!1,null,null,null);e.a=o.exports},eeb8:function(t,e,a){"use strict";(function(t){a("99af");e.a={name:"sessao-plenaria-topo",props:["sessao"],data:function(){return{app:["sessao","parlamentares"],model:["sessaoplenaria","sessaolegislativa","tiposessaoplenaria","legislatura"],data_inicio:new Date,sessao_legislativa:{numero:""},tipo:{nome:""},legislatura:{numero:""},metadata:{sessao_legislativa:{app:"parlamentares",model:"sessaolegislativa",id:this.sessao.sessao_legislativa},legislatura:{app:"parlamentares",model:"legislatura",id:this.sessao.legislatura},tipo:{app:"sessao",model:"tiposessaoplenaria",id:this.sessao.tipo}}}},watch:{sessao:function(t){this.updateSessao(),this.fetch()}},computed:{titulo:function(){var t=this.sessao,e=this.tipo,a=this.data_inicio;return"".concat(t.numero,"ª ").concat(e.nome," da\n              ").concat(a.getDate()>15?2:1,"ª Quinzena do Mês de\n              ").concat(this.month_text(a.getMonth())," de\n              ").concat(a.getFullYear(),"\n              ")},subtitulo:function(){return"".concat(this.sessao_legislativa.numero,"ª Sessão Legislativa da\n              ").concat(this.legislatura.numero,"ª Legislatura")},date_text:function(){return"".concat(this.data_inicio.getDate()," de\n              ").concat(this.month_text(this.data_inicio.getMonth())," de\n              ").concat(this.data_inicio.getFullYear()," – ").concat(this.sessao.hora_inicio)}},methods:{fetch:function(e){var a=this;t.mapKeys(a.metadata,(function(t,e){var i=a.metadata[e];a.getObject(i).then((function(t){a[e]=t}))}))},updateSessao:function(){this.data_inicio=this.stringToDate(this.sessao.data_inicio,"yyyy-mm-dd","-"),this.metadata.sessao_legislativa.id=this.sessao.sessao_legislativa,this.metadata.tipo.id=this.sessao.tipo,this.metadata.legislatura.id=this.sessao.legislatura}},mounted:function(){this.updateSessao(),this.fetch()}}}).call(this,a("2ef0"))},fb6a:function(t,e,a){"use strict";var i=a("23e7"),n=a("e8b5"),o=a("68ee"),s=a("861d"),r=a("23cb"),c=a("07fa"),l=a("fc6a"),u=a("8418"),d=a("b622"),f=a("1dde"),m=a("f36a"),h=f("slice"),p=d("species"),v=Array,g=Math.max;i({target:"Array",proto:!0,forced:!h},{slice:function(t,e){var a,i,d,f=l(this),h=c(f),_=r(t,h),b=r(void 0===e?h:e,h);if(n(f)&&(a=f.constructor,(o(a)&&(a===v||n(a.prototype))||s(a)&&null===(a=a[p]))&&(a=void 0),a===v||void 0===a))return m(f,_,b);for(i=new(void 0===a?v:a)(g(b-_,0)),d=0;_<b;_++,d++)_ in f&&u(i,d,f[_]);return i.length=d,i}})},fca8:function(t,e,a){},fe51:function(t,e,a){"use strict";a("49ae")}}]);