(window.webpackJsonp=window.webpackJsonp||[]).push([["chunk-7c767211"],{"0d3b":function(e,t,a){var n=a("d039"),i=a("b622"),s=a("c430"),r=i("iterator");e.exports=!n((function(){var e=new URL("b?a=1&b=2&c=3","http://a"),t=e.searchParams,a="";return e.pathname="c%20d",t.forEach((function(e,n){t.delete("b"),a+=n+e})),s&&!e.toJSON||!t.sort||"http://a/c%20d?a=1&c=3"!==e.href||"3"!==t.get("c")||"a=1"!==String(new URLSearchParams("?a=1"))||!t[r]||"a"!==new URL("https://a@b").username||"b"!==new URLSearchParams(new URLSearchParams("a=b")).get("a")||"xn--e1aybc"!==new URL("http://тест").host||"#%D0%B1"!==new URL("http://a#б").hash||"a1c3"!==a||"x"!==new URL("http://x",void 0).host}))},"2b3d":function(e,t,a){"use strict";a("3ca3");var n,i=a("23e7"),s=a("83ab"),r=a("0d3b"),o=a("da84"),c=a("37e8"),l=a("6eeb"),u=a("19aa"),d=a("5135"),h=a("60da"),f=a("4df4"),p=a("6547").codeAt,m=a("5fb2"),v=a("d44e"),g=a("9861"),_=a("69f3"),b=o.URL,y=g.URLSearchParams,x=g.getState,L=_.set,k=_.getterFor("URL"),w=Math.floor,C=Math.pow,R=/[A-Za-z]/,U=/[\d+-.A-Za-z]/,S=/\d/,A=/^(0x|0X)/,E=/^[0-7]+$/,I=/^\d+$/,P=/^[\dA-Fa-f]+$/,D=/[\u0000\u0009\u000A\u000D #%/:?@[\\]]/,B=/[\u0000\u0009\u000A\u000D #/:?@[\\]]/,$=/^[\u0000-\u001F ]+|[\u0000-\u001F ]+$/g,T=/[\u0009\u000A\u000D]/g,M=function(e,t){var a,n,i;if("["==t.charAt(0)){if("]"!=t.charAt(t.length-1))return"Invalid host";if(!(a=q(t.slice(1,-1))))return"Invalid host";e.host=a}else if(K(e)){if(t=m(t),D.test(t))return"Invalid host";if(null===(a=j(t)))return"Invalid host";e.host=a}else{if(B.test(t))return"Invalid host";for(a="",n=f(t),i=0;i<n.length;i++)a+=H(n[i],F);e.host=a}},j=function(e){var t,a,n,i,s,r,o,c=e.split(".");if(c.length&&""==c[c.length-1]&&c.pop(),(t=c.length)>4)return e;for(a=[],n=0;n<t;n++){if(""==(i=c[n]))return e;if(s=10,i.length>1&&"0"==i.charAt(0)&&(s=A.test(i)?16:8,i=i.slice(8==s?1:2)),""===i)r=0;else{if(!(10==s?I:8==s?E:P).test(i))return e;r=parseInt(i,s)}a.push(r)}for(n=0;n<t;n++)if(r=a[n],n==t-1){if(r>=C(256,5-t))return null}else if(r>255)return null;for(o=a.pop(),n=0;n<a.length;n++)o+=a[n]*C(256,3-n);return o},q=function(e){var t,a,n,i,s,r,o,c=[0,0,0,0,0,0,0,0],l=0,u=null,d=0,h=function(){return e.charAt(d)};if(":"==h()){if(":"!=e.charAt(1))return;d+=2,u=++l}for(;h();){if(8==l)return;if(":"!=h()){for(t=a=0;a<4&&P.test(h());)t=16*t+parseInt(h(),16),d++,a++;if("."==h()){if(0==a)return;if(d-=a,l>6)return;for(n=0;h();){if(i=null,n>0){if(!("."==h()&&n<4))return;d++}if(!S.test(h()))return;for(;S.test(h());){if(s=parseInt(h(),10),null===i)i=s;else{if(0==i)return;i=10*i+s}if(i>255)return;d++}c[l]=256*c[l]+i,2!=++n&&4!=n||l++}if(4!=n)return;break}if(":"==h()){if(d++,!h())return}else if(h())return;c[l++]=t}else{if(null!==u)return;d++,u=++l}}if(null!==u)for(r=l-u,l=7;0!=l&&r>0;)o=c[l],c[l--]=c[u+r-1],c[u+--r]=o;else if(8!=l)return;return c},O=function(e){var t,a,n,i;if("number"==typeof e){for(t=[],a=0;a<4;a++)t.unshift(e%256),e=w(e/256);return t.join(".")}if("object"==typeof e){for(t="",n=function(e){for(var t=null,a=1,n=null,i=0,s=0;s<8;s++)0!==e[s]?(i>a&&(t=n,a=i),n=null,i=0):(null===n&&(n=s),++i);return i>a&&(t=n,a=i),t}(e),a=0;a<8;a++)i&&0===e[a]||(i&&(i=!1),n===a?(t+=a?":":"::",i=!0):(t+=e[a].toString(16),a<7&&(t+=":")));return"["+t+"]"}return e},F={},N=h({},F,{" ":1,'"':1,"<":1,">":1,"`":1}),V=h({},N,{"#":1,"?":1,"{":1,"}":1}),z=h({},V,{"/":1,":":1,";":1,"=":1,"@":1,"[":1,"\\":1,"]":1,"^":1,"|":1}),H=function(e,t){var a=p(e,0);return a>32&&a<127&&!d(t,e)?e:encodeURIComponent(e)},J={ftp:21,file:null,http:80,https:443,ws:80,wss:443},K=function(e){return d(J,e.scheme)},Y=function(e){return""!=e.username||""!=e.password},G=function(e){return!e.host||e.cannotBeABaseURL||"file"==e.scheme},Z=function(e,t){var a;return 2==e.length&&R.test(e.charAt(0))&&(":"==(a=e.charAt(1))||!t&&"|"==a)},Q=function(e){var t;return e.length>1&&Z(e.slice(0,2))&&(2==e.length||"/"===(t=e.charAt(2))||"\\"===t||"?"===t||"#"===t)},X=function(e){var t=e.path,a=t.length;!a||"file"==e.scheme&&1==a&&Z(t[0],!0)||t.pop()},W=function(e){return"."===e||"%2e"===e.toLowerCase()},ee={},te={},ae={},ne={},ie={},se={},re={},oe={},ce={},le={},ue={},de={},he={},fe={},pe={},me={},ve={},ge={},_e={},be={},ye={},xe=function(e,t,a,i){var s,r,o,c,l,u=a||ee,h=0,p="",m=!1,v=!1,g=!1;for(a||(e.scheme="",e.username="",e.password="",e.host=null,e.port=null,e.path=[],e.query=null,e.fragment=null,e.cannotBeABaseURL=!1,t=t.replace($,"")),t=t.replace(T,""),s=f(t);h<=s.length;){switch(r=s[h],u){case ee:if(!r||!R.test(r)){if(a)return"Invalid scheme";u=ae;continue}p+=r.toLowerCase(),u=te;break;case te:if(r&&(U.test(r)||"+"==r||"-"==r||"."==r))p+=r.toLowerCase();else{if(":"!=r){if(a)return"Invalid scheme";p="",u=ae,h=0;continue}if(a&&(K(e)!=d(J,p)||"file"==p&&(Y(e)||null!==e.port)||"file"==e.scheme&&!e.host))return;if(e.scheme=p,a)return void(K(e)&&J[e.scheme]==e.port&&(e.port=null));p="","file"==e.scheme?u=fe:K(e)&&i&&i.scheme==e.scheme?u=ne:K(e)?u=oe:"/"==s[h+1]?(u=ie,h++):(e.cannotBeABaseURL=!0,e.path.push(""),u=_e)}break;case ae:if(!i||i.cannotBeABaseURL&&"#"!=r)return"Invalid scheme";if(i.cannotBeABaseURL&&"#"==r){e.scheme=i.scheme,e.path=i.path.slice(),e.query=i.query,e.fragment="",e.cannotBeABaseURL=!0,u=ye;break}u="file"==i.scheme?fe:se;continue;case ne:if("/"!=r||"/"!=s[h+1]){u=se;continue}u=ce,h++;break;case ie:if("/"==r){u=le;break}u=ge;continue;case se:if(e.scheme=i.scheme,r==n)e.username=i.username,e.password=i.password,e.host=i.host,e.port=i.port,e.path=i.path.slice(),e.query=i.query;else if("/"==r||"\\"==r&&K(e))u=re;else if("?"==r)e.username=i.username,e.password=i.password,e.host=i.host,e.port=i.port,e.path=i.path.slice(),e.query="",u=be;else{if("#"!=r){e.username=i.username,e.password=i.password,e.host=i.host,e.port=i.port,e.path=i.path.slice(),e.path.pop(),u=ge;continue}e.username=i.username,e.password=i.password,e.host=i.host,e.port=i.port,e.path=i.path.slice(),e.query=i.query,e.fragment="",u=ye}break;case re:if(!K(e)||"/"!=r&&"\\"!=r){if("/"!=r){e.username=i.username,e.password=i.password,e.host=i.host,e.port=i.port,u=ge;continue}u=le}else u=ce;break;case oe:if(u=ce,"/"!=r||"/"!=p.charAt(h+1))continue;h++;break;case ce:if("/"!=r&&"\\"!=r){u=le;continue}break;case le:if("@"==r){m&&(p="%40"+p),m=!0,o=f(p);for(var _=0;_<o.length;_++){var b=o[_];if(":"!=b||g){var y=H(b,z);g?e.password+=y:e.username+=y}else g=!0}p=""}else if(r==n||"/"==r||"?"==r||"#"==r||"\\"==r&&K(e)){if(m&&""==p)return"Invalid authority";h-=f(p).length+1,p="",u=ue}else p+=r;break;case ue:case de:if(a&&"file"==e.scheme){u=me;continue}if(":"!=r||v){if(r==n||"/"==r||"?"==r||"#"==r||"\\"==r&&K(e)){if(K(e)&&""==p)return"Invalid host";if(a&&""==p&&(Y(e)||null!==e.port))return;if(c=M(e,p))return c;if(p="",u=ve,a)return;continue}"["==r?v=!0:"]"==r&&(v=!1),p+=r}else{if(""==p)return"Invalid host";if(c=M(e,p))return c;if(p="",u=he,a==de)return}break;case he:if(!S.test(r)){if(r==n||"/"==r||"?"==r||"#"==r||"\\"==r&&K(e)||a){if(""!=p){var x=parseInt(p,10);if(x>65535)return"Invalid port";e.port=K(e)&&x===J[e.scheme]?null:x,p=""}if(a)return;u=ve;continue}return"Invalid port"}p+=r;break;case fe:if(e.scheme="file","/"==r||"\\"==r)u=pe;else{if(!i||"file"!=i.scheme){u=ge;continue}if(r==n)e.host=i.host,e.path=i.path.slice(),e.query=i.query;else if("?"==r)e.host=i.host,e.path=i.path.slice(),e.query="",u=be;else{if("#"!=r){Q(s.slice(h).join(""))||(e.host=i.host,e.path=i.path.slice(),X(e)),u=ge;continue}e.host=i.host,e.path=i.path.slice(),e.query=i.query,e.fragment="",u=ye}}break;case pe:if("/"==r||"\\"==r){u=me;break}i&&"file"==i.scheme&&!Q(s.slice(h).join(""))&&(Z(i.path[0],!0)?e.path.push(i.path[0]):e.host=i.host),u=ge;continue;case me:if(r==n||"/"==r||"\\"==r||"?"==r||"#"==r){if(!a&&Z(p))u=ge;else if(""==p){if(e.host="",a)return;u=ve}else{if(c=M(e,p))return c;if("localhost"==e.host&&(e.host=""),a)return;p="",u=ve}continue}p+=r;break;case ve:if(K(e)){if(u=ge,"/"!=r&&"\\"!=r)continue}else if(a||"?"!=r)if(a||"#"!=r){if(r!=n&&(u=ge,"/"!=r))continue}else e.fragment="",u=ye;else e.query="",u=be;break;case ge:if(r==n||"/"==r||"\\"==r&&K(e)||!a&&("?"==r||"#"==r)){if(".."===(l=(l=p).toLowerCase())||"%2e."===l||".%2e"===l||"%2e%2e"===l?(X(e),"/"==r||"\\"==r&&K(e)||e.path.push("")):W(p)?"/"==r||"\\"==r&&K(e)||e.path.push(""):("file"==e.scheme&&!e.path.length&&Z(p)&&(e.host&&(e.host=""),p=p.charAt(0)+":"),e.path.push(p)),p="","file"==e.scheme&&(r==n||"?"==r||"#"==r))for(;e.path.length>1&&""===e.path[0];)e.path.shift();"?"==r?(e.query="",u=be):"#"==r&&(e.fragment="",u=ye)}else p+=H(r,V);break;case _e:"?"==r?(e.query="",u=be):"#"==r?(e.fragment="",u=ye):r!=n&&(e.path[0]+=H(r,F));break;case be:a||"#"!=r?r!=n&&("'"==r&&K(e)?e.query+="%27":e.query+="#"==r?"%23":H(r,F)):(e.fragment="",u=ye);break;case ye:r!=n&&(e.fragment+=H(r,N))}h++}},Le=function(e){var t,a,n=u(this,Le,"URL"),i=arguments.length>1?arguments[1]:void 0,r=String(e),o=L(n,{type:"URL"});if(void 0!==i)if(i instanceof Le)t=k(i);else if(a=xe(t={},String(i)))throw TypeError(a);if(a=xe(o,r,null,t))throw TypeError(a);var c=o.searchParams=new y,l=x(c);l.updateSearchParams(o.query),l.updateURL=function(){o.query=String(c)||null},s||(n.href=we.call(n),n.origin=Ce.call(n),n.protocol=Re.call(n),n.username=Ue.call(n),n.password=Se.call(n),n.host=Ae.call(n),n.hostname=Ee.call(n),n.port=Ie.call(n),n.pathname=Pe.call(n),n.search=De.call(n),n.searchParams=Be.call(n),n.hash=$e.call(n))},ke=Le.prototype,we=function(){var e=k(this),t=e.scheme,a=e.username,n=e.password,i=e.host,s=e.port,r=e.path,o=e.query,c=e.fragment,l=t+":";return null!==i?(l+="//",Y(e)&&(l+=a+(n?":"+n:"")+"@"),l+=O(i),null!==s&&(l+=":"+s)):"file"==t&&(l+="//"),l+=e.cannotBeABaseURL?r[0]:r.length?"/"+r.join("/"):"",null!==o&&(l+="?"+o),null!==c&&(l+="#"+c),l},Ce=function(){var e=k(this),t=e.scheme,a=e.port;if("blob"==t)try{return new URL(t.path[0]).origin}catch(e){return"null"}return"file"!=t&&K(e)?t+"://"+O(e.host)+(null!==a?":"+a:""):"null"},Re=function(){return k(this).scheme+":"},Ue=function(){return k(this).username},Se=function(){return k(this).password},Ae=function(){var e=k(this),t=e.host,a=e.port;return null===t?"":null===a?O(t):O(t)+":"+a},Ee=function(){var e=k(this).host;return null===e?"":O(e)},Ie=function(){var e=k(this).port;return null===e?"":String(e)},Pe=function(){var e=k(this),t=e.path;return e.cannotBeABaseURL?t[0]:t.length?"/"+t.join("/"):""},De=function(){var e=k(this).query;return e?"?"+e:""},Be=function(){return k(this).searchParams},$e=function(){var e=k(this).fragment;return e?"#"+e:""},Te=function(e,t){return{get:e,set:t,configurable:!0,enumerable:!0}};if(s&&c(ke,{href:Te(we,(function(e){var t=k(this),a=String(e),n=xe(t,a);if(n)throw TypeError(n);x(t.searchParams).updateSearchParams(t.query)})),origin:Te(Ce),protocol:Te(Re,(function(e){var t=k(this);xe(t,String(e)+":",ee)})),username:Te(Ue,(function(e){var t=k(this),a=f(String(e));if(!G(t)){t.username="";for(var n=0;n<a.length;n++)t.username+=H(a[n],z)}})),password:Te(Se,(function(e){var t=k(this),a=f(String(e));if(!G(t)){t.password="";for(var n=0;n<a.length;n++)t.password+=H(a[n],z)}})),host:Te(Ae,(function(e){var t=k(this);t.cannotBeABaseURL||xe(t,String(e),ue)})),hostname:Te(Ee,(function(e){var t=k(this);t.cannotBeABaseURL||xe(t,String(e),de)})),port:Te(Ie,(function(e){var t=k(this);G(t)||(""==(e=String(e))?t.port=null:xe(t,e,he))})),pathname:Te(Pe,(function(e){var t=k(this);t.cannotBeABaseURL||(t.path=[],xe(t,e+"",ve))})),search:Te(De,(function(e){var t=k(this);""==(e=String(e))?t.query=null:("?"==e.charAt(0)&&(e=e.slice(1)),t.query="",xe(t,e,be)),x(t.searchParams).updateSearchParams(t.query)})),searchParams:Te(Be),hash:Te($e,(function(e){var t=k(this);""!=(e=String(e))?("#"==e.charAt(0)&&(e=e.slice(1)),t.fragment="",xe(t,e,ye)):t.fragment=null}))}),l(ke,"toJSON",(function(){return we.call(this)}),{enumerable:!0}),l(ke,"toString",(function(){return we.call(this)}),{enumerable:!0}),b){var Me=b.createObjectURL,je=b.revokeObjectURL;Me&&l(Le,"createObjectURL",(function(e){return Me.apply(b,arguments)})),je&&l(Le,"revokeObjectURL",(function(e){return je.apply(b,arguments)}))}v(Le,"URL"),i({global:!0,forced:!r,sham:!s},{URL:Le})},"2bf8":function(e,t,a){},"327c":function(e,t,a){"use strict";(function(e){a("4de4");var n=a("82ea");t.a={name:"pauta-online",props:["sessao"],components:{ItemDePauta:n.a},data:function(){return{itens:{expedientesessao_list:[],ordemdia_list:{},expedientemateria_list:{}},init:!1,app:["sessao"],model:["expedientemateria","ordemdia"]}},computed:{itensDaOrdemDia:{get:function(){return e.orderBy(this.itens.ordemdia_list,"numero_ordem")}},itensDoExpediente:{get:function(){return e.orderBy(this.itens.expedientemateria_list,"numero_ordem")}}},mounted:function(){var e=this;setTimeout((function(){e.fetchItens(),e.fetchExpedienteSessao()}),1e3)},methods:{expediente:function(t){var a=this.itens.expedientesessao_list,n=e.filter(a,["tipo",t]);return n.length>0?n[0].conteudo:""},fetch:function(e){if("post_delete"!==e.action){var t=this;t.getObject(e).then((function(a){t.$set(t.itens["".concat(e.model,"_list")],e.id,a)}))}else this.$delete(this.itens["".concat(e.model,"_list")],e.id)},fetchItens:function(){var t=arguments.length>0&&void 0!==arguments[0]?arguments[0]:this.model,a=this;e.mapKeys(t,(function(t,n){e.mapKeys(a.itens["".concat(t,"_list")],(function(e,t){e.vue_validate=!1})),a.$nextTick().then((function(){a.fetchList(1,t)}))}))},fetchExpedienteSessao:function(){var e=this;return e.utils.getByMetadata({action:"expedientes",app:"sessao",model:"sessaoplenaria",id:e.sessao.id}).then((function(t){e.$set(e.itens,"expedientesessao_list",t.data.results)})).then((function(e){}))},fetchList:function(){var t=arguments.length>0&&void 0!==arguments[0]?arguments[0]:null,a=arguments.length>1&&void 0!==arguments[1]?arguments[1]:null,n=this,i="&sessao_plenaria=".concat(this.sessao.id);n.utils.getModelOrderedList("sessao",a,"numero_ordem",null===t?1:t,i).then((function(t){n.init=!0,e.each(t.data.results,(function(e,t){e.vue_validate=!0,e.id in n.itens["".concat(a,"_list")]?n.itens["".concat(a,"_list")][e.id]=e:n.$set(n.itens["".concat(a,"_list")],e.id,e)})),n.$nextTick().then((function(){null!==t.data.pagination.next_page?n.fetchList(t.data.pagination.next_page,a):e.mapKeys(n.itens["".concat(a,"_list")],(function(e,t){e.vue_validate||n.$delete(n.itens["".concat(a,"_list")],e.id)}))}))})).catch((function(e){n.init=!0,n.sendMessage({alert:"danger",message:"Não foi possível recuperar a Ordem do Dia.",time:5})}))}}}}).call(this,a("2ef0"))},"4a7e":function(e,t,a){"use strict";a.r(t);var n=a("c2e8").a,i=(a("c0c6"),a("2877")),s=Object(i.a)(n,(function(){var e=this,t=e.$createElement,a=e._self._c||t;return a("div",{class:"sessao-plenaria-topo"},[a("div",{staticClass:"tit"},[e._v(" "+e._s(e.titulo)+" ")]),a("div",{staticClass:"subtitulo"},[a("span",[e._v(e._s(e.subtitulo))]),e._v(" – "),a("span",[e._v(e._s(e.date_text))])])])}),[],!1,null,null,null).exports,r=a("327c").a,o=(a("ce85"),{name:"sessao-plenaria-online",components:{SessaoPlenariaTopo:s,PautaOnline:Object(i.a)(r,(function(){var e=this,t=e.$createElement,a=e._self._c||t;return a("div",{staticClass:"pauta-online"},[0===e.itens.ordemdia_list.length&&e.init?a("div",{staticClass:"empty-list"},[e._v(" Não existem Itens na Ordem do Dia com seus critérios de busca! ")]):e._e(),e.init?e._e():a("div",{staticClass:"empty-list"},[e._v(" Carregando listagem... ")]),a("div",{class:["item-expediente",e.nivel(e.NIVEL3,e.itens.expedientesessao_list.length>0)]},[a("div",{staticClass:"inner",domProps:{innerHTML:e._s(e.expediente(1))}})]),a("div",{staticClass:"container-expedientemateria"},[e.itensDoExpediente.length?a("div",{staticClass:"titulo-container"},[e._v("Matérias do Grande Expediente")]):e._e(),a("div",{staticClass:"inner"},e._l(e.itensDoExpediente,(function(e){return a("item-de-pauta",{key:"exp"+e.id,attrs:{item:e,type:"expedientemateria"}})})),1)]),a("div",{class:["item-expediente",e.nivel(e.NIVEL3,e.itens.expedientesessao_list.length>0)]},[a("div",{staticClass:"inner",domProps:{innerHTML:e._s(e.expediente(3))}})]),a("div",{staticClass:"container-ordemdia"},[e.itensDaOrdemDia.length?a("div",{staticClass:"titulo-container"},[e._v("Matérias da Ordem do Dia")]):e._e(),a("div",{staticClass:"inner"},e._l(e.itensDaOrdemDia,(function(e){return a("item-de-pauta",{key:"od"+e.id,attrs:{item:e,type:"ordemdia"}})})),1)]),a("div",{class:["item-expediente",e.nivel(e.NIVEL3,e.itens.expedientesessao_list.length>0)]},[a("div",{staticClass:"inner",domProps:{innerHTML:e._s(e.expediente(4))}})])])}),[],!1,null,null,null).exports},data:function(){return{sessao:null,idd:parseInt(this.$route.params.id),app:["sessao"],model:["sessaoplenaria"]}},mounted:function(){var e=this,t=this;t.$nextTick((function(){t.getObject({action:"",id:t.idd,app:t.app[0],model:t.model[0]}).then((function(t){e.sessao=t})).catch((function(){e.sessao=void 0!==e.cache.sessao&&void 0!==e.cache.sessao.sessaoplenaria&&void 0!==e.cache.sessao.sessaoplenaria[e.idd]?e.cache.sessao.sessaoplenaria[e.idd]:null}))}))},methods:{fetch:function(e){var t=this;e.id===this.idd&&e.app===this.app[0]&&e.model===this.model[0]&&("post_delete"===e.action?setTimeout((function(){t.sendMessage({alert:"danger",message:"Sessão Plenária foi excluída",time:5}),t.$router.push({name:"sessao_list_link"})}),500):this.sessao=this.cache.sessao.sessaoplenaria[this.idd])}}}),c=(a("8e03"),Object(i.a)(o,(function(){var e=this.$createElement,t=this._self._c||e;return t("div",{staticClass:"sessao-plenaria-online"},[this.sessao?[t("sessao-plenaria-topo",{attrs:{sessao:this.sessao}}),t("pauta-online",{attrs:{sessao:this.sessao}})]:this._e()],2)}),[],!1,null,null,null));t.default=c.exports},"5fb2":function(e,t,a){"use strict";var n=/[^\0-\u007E]/,i=/[.\u3002\uFF0E\uFF61]/g,s="Overflow: input needs wider integers to process",r=Math.floor,o=String.fromCharCode,c=function(e){return e+22+75*(e<26)},l=function(e,t,a){var n=0;for(e=a?r(e/700):e>>1,e+=r(e/t);e>455;n+=36)e=r(e/35);return r(n+36*e/(e+38))},u=function(e){var t,a,n=[],i=(e=function(e){for(var t=[],a=0,n=e.length;a<n;){var i=e.charCodeAt(a++);if(i>=55296&&i<=56319&&a<n){var s=e.charCodeAt(a++);56320==(64512&s)?t.push(((1023&i)<<10)+(1023&s)+65536):(t.push(i),a--)}else t.push(i)}return t}(e)).length,u=128,d=0,h=72;for(t=0;t<e.length;t++)(a=e[t])<128&&n.push(o(a));var f=n.length,p=f;for(f&&n.push("-");p<i;){var m=2147483647;for(t=0;t<e.length;t++)(a=e[t])>=u&&a<m&&(m=a);var v=p+1;if(m-u>r((2147483647-d)/v))throw RangeError(s);for(d+=(m-u)*v,u=m,t=0;t<e.length;t++){if((a=e[t])<u&&++d>2147483647)throw RangeError(s);if(a==u){for(var g=d,_=36;;_+=36){var b=_<=h?1:_>=h+26?26:_-h;if(g<b)break;var y=g-b,x=36-b;n.push(o(c(b+y%x))),g=r(y/x)}n.push(o(c(g))),h=l(d,v,p==f),d=0,++p}}++d,++u}return n.join("")};e.exports=function(e){var t,a,s=[],r=e.toLowerCase().replace(i,".").split(".");for(t=0;t<r.length;t++)a=r[t],s.push(n.test(a)?"xn--"+u(a):a);return s.join(".")}},"82ea":function(e,t,a){"use strict";var n=a("86e3").a,i=(a("f4d5"),a("2877")),s=Object(i.a)(n,(function(){var e=this,t=e.$createElement,a=e._self._c||t;return a("div",{class:["item-de-pauta",e.type]},[a("div",{class:["empty-list",void 0===e.materia.id?"":"d-none"]},[e._v(" Carregando Matéria... ")]),a("div",{class:[e.resultadoVotacao]},[e.item.resultado?a("span",[e._v(e._s(e.item.resultado))]):a("span",[e._v("Tramitando")])]),a("materia-pauta",{attrs:{materia:e.materia,type:e.type}}),a("div",{class:["item-body"]}),a("div",{class:["item-body",void 0!==e.materia.id&&e.materia.anexadas.length>0?"col-anexadas":""]},[a("div",{staticClass:"col-1-body"},[a("div",{staticClass:"status-tramitacao"},[a("div",{class:["ultima_tramitacao",e.nivel(e.NIVEL2,e.tramitacao.ultima!=={})]},[a("strong",[e._v("Situação:")]),e._v(" "+e._s(e.tramitacao.status.descricao)),a("br"),a("strong",[e._v("Ultima Ação:")]),e._v(" "+e._s(e.tramitacao.ultima.texto)+" ")]),a("div",{class:["observacao",e.nivel(e.NIVEL3,e.observacao.length>0)],domProps:{innerHTML:e._s(e.observacao)}})]),a("div",{class:["sub-containers",0===e.itensLegislacaoCitada.length?"d-none":"container-legis-citada"]},[e._m(0),a("div",{staticClass:"inner"},e._l(e.itensLegislacaoCitada,(function(t){return a("button",{key:"legiscit"+t.id,staticClass:"btn btn-link",attrs:{type:"button","data-toggle":"modal","data-target":"modal-legis-citada-"+t.id},on:{click:function(a){e.modal_legis_citada=t}}},[e._v(" "+e._s(t.__str__)+" ")])})),0)]),a("div",{class:["sub-containers",e.nivel(e.NIVEL2,e.itensDocumentosAcessorios.length>0),0===e.itensDocumentosAcessorios.length?"d-none":"container-docs-acessorios"]},[e._m(1),a("div",{staticClass:"inner"},e._l(e.itensDocumentosAcessorios,(function(t){return a("a",{key:"docsacc"+t.id,staticClass:"btn btn-link",attrs:{href:t.arquivo}},[e._v(" "+e._s(t.__str__)+" ")])})),0)])]),a("div",{staticClass:"col-2-body"},[a("div",{class:["sub-containers",e.nivel(e.NIVEL2,e.itensAnexados.length>0)]},[e._m(2),a("div",{staticClass:"inner"},e._l(e.itensAnexados,(function(t){return a("div",{key:""+e.type+t.id},[a("materia-pauta",{attrs:{materia:t,type:e.type}})],1)})),0)])])]),e.modal_legis_citada?a("norma-simple-modal-view",{attrs:{html_id:"modal-legis-citada-"+e.modal_legis_citada.id,modal_norma:null,idd:e.modal_legis_citada.norma}}):e._e()],1)}),[function(){var e=this.$createElement,t=this._self._c||e;return t("div",{staticClass:"title"},[t("span",[this._v(" Legislação Citada ")])])},function(){var e=this.$createElement,t=this._self._c||e;return t("div",{staticClass:"title"},[t("span",[this._v(" Documentos Acessórios ")])])},function(){var e=this.$createElement,t=this._self._c||e;return t("div",{staticClass:"title"},[t("span",[this._v(" Matérias Anexadas ")])])}],!1,null,null,null);t.a=s.exports},"84f6":function(e,t,a){"use strict";var n=a("a209f").a,i=(a("e7c6"),a("2877")),s=Object(i.a)(n,(function(){var e=this,t=e.$createElement,a=e._self._c||t;return a("div",{class:["materia-pauta"]},[a("a",{staticClass:"epigrafe",attrs:{href:e.materia.link_detail_backend,target:"_blank"}},[e._v(e._s(e.tipo_string)+" nº "+e._s(e.materia.numero)+"/"+e._s(e.materia.ano))]),a("div",{class:["item-header",e.tipo_string?"":"d-none"]},[a("div",{staticClass:"link-file",attrs:{id:e.type+"-"+e.materia.id}},[a("a",{class:["btn btn-link","link-file-"+e.materia.id,e.blob?"":"d-none"],on:{click:e.clickFile}},[a("i",{staticClass:"far fa-2x fa-file-pdf"})]),a("small",{class:e.baixando?"":"d-none"},[e._v("Baixando"),a("br"),e._v("Arquivo")])]),a("div",{staticClass:"data-header"},[a("div",{staticClass:"detail-header"},[a("div",{staticClass:"protocolo-data"},[a("span",[e._v(" Protocolo: "),a("strong",[e._v(e._s(e.materia.numero_protocolo))])]),a("span",[e._v(e._s(e.data_apresentacao))])]),a("div",{staticClass:"autoria"},e._l(e.autores_list,(function(t,n){return a("span",{key:"au"+n},[e._v(e._s(t.nome))])})),0)]),a("div",{staticClass:"ementa"},[e._v(e._s(e.materia.ementa))])])])])}),[],!1,null,null,null);t.a=s.exports},"86e3":function(e,t,a){"use strict";(function(e,n){a("99af"),a("ac1f"),a("5319");var i=a("84f6"),s=a("6c99");t.a={name:"item-de-pauta",props:["item","type"],components:{MateriaPauta:i.a,NormaSimpleModalView:s.a},data:function(){return{app:["materia","norma"],model:["materialegislativa","tramitacao","anexada","autoria","legislacaocitada","documentoacessorio"],materia:{},tramitacao:{ultima:{},status:{}},anexadas:{},legislacaocitada:{},documentoacessorio:{},modal_legis_citada:null}},watch:{modal_legis_citada:function(t,a){var n=this;null!==t&&this.$nextTick().then((function(){e("#modal-legis-citada-".concat(t.id)).modal("show"),e("#modal-legis-citada-".concat(t.id)).on("hidden.bs.modal",(function(e){n.modal_legis_citada=null}))}))}},computed:{data_apresentacao:function(){try{var e=this.stringToDate(this.materia.data_apresentacao,"yyyy-mm-dd","-");return"".concat(e.getDate(),"/").concat(e.getMonth()+1,"/").concat(e.getFullYear())}catch(e){return""}},observacao:function(){var e=this.item.observacao;return e=(e=(e=(e=e.replace(/^\r\n/g,"")).replace(/\r\n/g,"<br />")).replace(/\r/g," ")).replace(/\n/g,"<br />")},itensAnexados:{get:function(){return n.orderBy(this.anexadas,"data_apresentacao")}},itensLegislacaoCitada:{get:function(){return n.orderBy(this.legislacaocitada,"norma")}},itensDocumentosAcessorios:{get:function(){return n.orderBy(this.documentoacessorio,"data")}},resultadoVotacao:{get:function(){var e="",t=this.item.resultado;return"Aprovado"===t?e="status-votacao result-aprovado":"Rejeitado"===t?e="status-votacao result-rejeitado":"Pedido de Vista"===t?e="status-votacao result-vista":"Prazo Regimental"===t&&(e="status-votacao result-prazo"),""!==e?e:"status-votacao"}}},mounted:function(){this.refresh()},methods:{refresh:function(){var e=this;e.fetchMateria().then((function(t){n.each(e.materia.anexadas,(function(t,a){e.fetchMateria({action:"post_save",app:e.app[0],model:e.model[0],id:t})}))})),e.$nextTick().then((function(){e.fetchUltimaTramitacao()})).then((function(){e.fetchLegislacaoCitada()})).then((function(){e.fetchDocumentoAcessorio()}))},fetch:function(e){var t=this;void 0!==e&&("materia"===e.app&&"materialegislativa"===e.model?(e.id===t.item.materia||e.id in t.materia.anexadas)&&t.fetchMateria(e):"materia"===e.app&&"anexada"===e.model?(t.$set(t,"anexadas",{}),t.refreshState({action:"",app:t.app[0],model:t.model[0],id:t.item.materia}).then((function(e){t.refresh()}))):"materia"===e.app&&"autoria"===e.model?t.refreshState({action:"",app:t.app[0],model:t.model[0],id:t.item.materia}).then((function(e){t.refresh()})):"materia"===e.app&&"tramitacao"===e.model?t.fetchUltimaTramitacao(e):"norma"===e.app&&"legislacaocitada"===e.model?t.fetchLegislacaoCitada():"materia"===e.app&&"documentoacessorio"===e.model&&t.fetchDocumentoAcessorio())},fetchDocumentoAcessorio:function(){var e=arguments.length>0&&void 0!==arguments[0]?arguments[0]:1,t=this,a="&materia=".concat(t.item.materia);t.utils.getModelList("materia","documentoacessorio",e,a).then((function(e){n.each(e.data.results,(function(e){t.$set(t.documentoacessorio,e.id,e)})),null!==e.data.pagination.next_page&&t.$nextTick().then((function(){t.fetchDocumentoAcessorio(e.data.pagination.next_page)}))})).catch((function(e){t.sendMessage({alert:"danger",message:"Não foi possível recuperar a lista de Documentos Acessórios.",time:5})}))},fetchLegislacaoCitada:function(){var e=arguments.length>0&&void 0!==arguments[0]?arguments[0]:1,t=this,a="&materia=".concat(t.item.materia);t.utils.getModelList("norma","legislacaocitada",e,a).then((function(e){n.each(e.data.results,(function(e){t.$set(t.legislacaocitada,e.id,e)})),null!==e.data.pagination.next_page&&t.$nextTick().then((function(){t.fetchLegislacaoCitada(e.data.pagination.next_page)}))})).catch((function(e){t.sendMessage({alert:"danger",message:"Não foi possível recuperar a lista de Legislação Citada.",time:5})}))},fetchMateria:function(e){var t=this;return t.getObject({action:"",app:t.app[0],model:t.model[0],id:void 0!==e?e.id:t.item.materia}).then((function(e){return e.id===t.item.materia?t.materia=e:t.$set(t.anexadas,e.id,e),e}))},fetchUltimaTramitacao:function(){var e=this;return e.utils.getByMetadata({action:"ultima_tramitacao",app:"materia",model:"materialegislativa",id:e.item.materia}).then((function(t){e.tramitacao.ultima=t.data,void 0!==e.tramitacao.ultima.id&&e.getObject({action:"",app:"materia",model:"statustramitacao",id:e.tramitacao.ultima.status}).then((function(t){e.tramitacao.status=t}))}))}}}}).call(this,a("1157"),a("2ef0"))},"8e03":function(e,t,a){"use strict";var n=a("a4b0");a.n(n).a},9861:function(e,t,a){"use strict";a("e260");var n=a("23e7"),i=a("d066"),s=a("0d3b"),r=a("6eeb"),o=a("e2cc"),c=a("d44e"),l=a("9ed3"),u=a("69f3"),d=a("19aa"),h=a("5135"),f=a("0366"),p=a("f5df"),m=a("825a"),v=a("861d"),g=a("7c73"),_=a("5c6c"),b=a("9a1f"),y=a("35a1"),x=a("b622"),L=i("fetch"),k=i("Headers"),w=x("iterator"),C=u.set,R=u.getterFor("URLSearchParams"),U=u.getterFor("URLSearchParamsIterator"),S=/\+/g,A=Array(4),E=function(e){return A[e-1]||(A[e-1]=RegExp("((?:%[\\da-f]{2}){"+e+"})","gi"))},I=function(e){try{return decodeURIComponent(e)}catch(t){return e}},P=function(e){var t=e.replace(S," "),a=4;try{return decodeURIComponent(t)}catch(e){for(;a;)t=t.replace(E(a--),I);return t}},D=/[!'()~]|%20/g,B={"!":"%21","'":"%27","(":"%28",")":"%29","~":"%7E","%20":"+"},$=function(e){return B[e]},T=function(e){return encodeURIComponent(e).replace(D,$)},M=function(e,t){if(t)for(var a,n,i=t.split("&"),s=0;s<i.length;)(a=i[s++]).length&&(n=a.split("="),e.push({key:P(n.shift()),value:P(n.join("="))}))},j=function(e){this.entries.length=0,M(this.entries,e)},q=function(e,t){if(e<t)throw TypeError("Not enough arguments")},O=l((function(e,t){C(this,{type:"URLSearchParamsIterator",iterator:b(R(e).entries),kind:t})}),"Iterator",(function(){var e=U(this),t=e.kind,a=e.iterator.next(),n=a.value;return a.done||(a.value="keys"===t?n.key:"values"===t?n.value:[n.key,n.value]),a})),F=function(){d(this,F,"URLSearchParams");var e,t,a,n,i,s,r,o,c,l=arguments.length>0?arguments[0]:void 0,u=this,f=[];if(C(u,{type:"URLSearchParams",entries:f,updateURL:function(){},updateSearchParams:j}),void 0!==l)if(v(l))if("function"==typeof(e=y(l)))for(a=(t=e.call(l)).next;!(n=a.call(t)).done;){if((r=(s=(i=b(m(n.value))).next).call(i)).done||(o=s.call(i)).done||!s.call(i).done)throw TypeError("Expected sequence with length 2");f.push({key:r.value+"",value:o.value+""})}else for(c in l)h(l,c)&&f.push({key:c,value:l[c]+""});else M(f,"string"==typeof l?"?"===l.charAt(0)?l.slice(1):l:l+"")},N=F.prototype;o(N,{append:function(e,t){q(arguments.length,2);var a=R(this);a.entries.push({key:e+"",value:t+""}),a.updateURL()},delete:function(e){q(arguments.length,1);for(var t=R(this),a=t.entries,n=e+"",i=0;i<a.length;)a[i].key===n?a.splice(i,1):i++;t.updateURL()},get:function(e){q(arguments.length,1);for(var t=R(this).entries,a=e+"",n=0;n<t.length;n++)if(t[n].key===a)return t[n].value;return null},getAll:function(e){q(arguments.length,1);for(var t=R(this).entries,a=e+"",n=[],i=0;i<t.length;i++)t[i].key===a&&n.push(t[i].value);return n},has:function(e){q(arguments.length,1);for(var t=R(this).entries,a=e+"",n=0;n<t.length;)if(t[n++].key===a)return!0;return!1},set:function(e,t){q(arguments.length,1);for(var a,n=R(this),i=n.entries,s=!1,r=e+"",o=t+"",c=0;c<i.length;c++)(a=i[c]).key===r&&(s?i.splice(c--,1):(s=!0,a.value=o));s||i.push({key:r,value:o}),n.updateURL()},sort:function(){var e,t,a,n=R(this),i=n.entries,s=i.slice();for(i.length=0,a=0;a<s.length;a++){for(e=s[a],t=0;t<a;t++)if(i[t].key>e.key){i.splice(t,0,e);break}t===a&&i.push(e)}n.updateURL()},forEach:function(e){for(var t,a=R(this).entries,n=f(e,arguments.length>1?arguments[1]:void 0,3),i=0;i<a.length;)n((t=a[i++]).value,t.key,this)},keys:function(){return new O(this,"keys")},values:function(){return new O(this,"values")},entries:function(){return new O(this,"entries")}},{enumerable:!0}),r(N,w,N.entries),r(N,"toString",(function(){for(var e,t=R(this).entries,a=[],n=0;n<t.length;)e=t[n++],a.push(T(e.key)+"="+T(e.value));return a.join("&")}),{enumerable:!0}),c(F,"URLSearchParams"),n({global:!0,forced:!s},{URLSearchParams:F}),s||"function"!=typeof L||"function"!=typeof k||n({global:!0,enumerable:!0,forced:!0},{fetch:function(e){var t,a,n,i=[e];return arguments.length>1&&(v(t=arguments[1])&&(a=t.body,"URLSearchParams"===p(a)&&((n=t.headers?new k(t.headers):new k).has("content-type")||n.set("content-type","application/x-www-form-urlencoded;charset=UTF-8"),t=g(t,{body:_(0,String(a)),headers:_(0,n)}))),i.push(t)),L.apply(this,i)}}),e.exports={URLSearchParams:F,getState:R}},"9a1f":function(e,t,a){var n=a("825a"),i=a("35a1");e.exports=function(e){var t=i(e);if("function"!=typeof t)throw TypeError(String(e)+" is not iterable");return n(t.call(e))}},a06a:function(e,t,a){},a209f:function(e,t,a){"use strict";(function(e){a("99af"),a("d3b7"),a("3ca3"),a("ddb0"),a("2b3d");var n=a("bc3a"),i=a.n(n);t.a={name:"materia-pauta",props:["materia","type"],data:function(){return{app:["materia"],model:["materialegislativa","tramitacao","anexada","autoria"],autores:{},tipo_string:"",blob:null,baixando:!1}},watch:{materia:function(e){this.refresh()}},computed:{data_apresentacao:function(){try{var e=this.stringToDate(this.materia.data_apresentacao,"yyyy-mm-dd","-");return"".concat(e.getDate(),"/").concat(e.getMonth()+1,"/").concat(e.getFullYear())}catch(e){return""}},autores_list:{get:function(){return e.orderBy(this.autores,"nome")}}},mounted:function(){var e=this;setTimeout((function(){e.blob||e.refresh()}),1e3)},methods:{clickFile:function(e){var t=window.URL.createObjectURL(this.blob);window.location=t},fetch:function(e){var t=this;void 0!==t.materia&&t.materia.id===e.id&&e.model===t.model[0]&&this.refresh()},refresh:function(){var t=this;void 0!==t.materia&&(t.getObject({app:"materia",model:"tipomaterialegislativa",id:t.materia.tipo}).then((function(e){t.tipo_string=e.descricao})),t.$set(t,"autores",{}),t.$nextTick().then((function(){if(e.each(t.materia.autores,(function(e){t.getObject({app:"base",model:"autor",id:e}).then((function(e){t.$set(t.autores,e.id,e)}))})),null!==t.materia.texto_original){var a=t.materia.texto_original;t.baixando=!0,i()({url:a,method:"GET",responseType:"blob"}).then((function(e){t.baixando=!1,t.blob=new Blob([e.data],{type:"application/pdf"})})).catch((function(){t.baixando=!1}))}})))}}}}).call(this,a("2ef0"))},a4b0:function(e,t,a){},b8da:function(e,t,a){},c0c6:function(e,t,a){"use strict";var n=a("a06a");a.n(n).a},c2e8:function(e,t,a){"use strict";(function(e){a("99af");t.a={name:"sessao-plenaria-topo",props:["sessao"],data:function(){return{app:["sessao","parlamentares"],model:["sessaoplenaria","sessaolegislativa","tiposessaoplenaria","legislatura"],data_inicio:new Date,sessao_legislativa:{numero:""},tipo:{nome:""},legislatura:{numero:""},metadata:{sessao_legislativa:{app:"parlamentares",model:"sessaolegislativa",id:this.sessao.sessao_legislativa},legislatura:{app:"parlamentares",model:"legislatura",id:this.sessao.legislatura},tipo:{app:"sessao",model:"tiposessaoplenaria",id:this.sessao.tipo}}}},watch:{sessao:function(e){this.updateSessao(),this.fetch()}},computed:{titulo:function(){var e=this.sessao,t=this.tipo,a=this.data_inicio;return"".concat(e.numero,"ª ").concat(t.nome," da \n              ").concat(a.getDate()>15?2:1,"ª Quizena do Mês de \n              ").concat(this.month_text(a.getMonth())," de \n              ").concat(a.getFullYear(),"\n              ")},subtitulo:function(){return"".concat(this.sessao_legislativa.numero,"ª Sessão Legislativa da \n              ").concat(this.legislatura.numero,"ª Legislatura")},date_text:function(){return"".concat(this.data_inicio.getDate()," de \n              ").concat(this.month_text(this.data_inicio.getMonth())," de\n              ").concat(this.data_inicio.getFullYear()," – ").concat(this.sessao.hora_inicio)}},methods:{fetch:function(t){var a=this;e.mapKeys(a.metadata,(function(e,t){var n=a.metadata[t];a.getObject(n).then((function(e){a[t]=e}))}))},updateSessao:function(){this.data_inicio=this.stringToDate(this.sessao.data_inicio,"yyyy-mm-dd","-"),this.metadata.sessao_legislativa.id=this.sessao.sessao_legislativa,this.metadata.tipo.id=this.sessao.tipo,this.metadata.legislatura.id=this.sessao.legislatura}},mounted:function(){this.updateSessao(),this.fetch()}}}).call(this,a("2ef0"))},c75c:function(e,t,a){},ce85:function(e,t,a){"use strict";var n=a("c75c");a.n(n).a},e7c6:function(e,t,a){"use strict";var n=a("b8da");a.n(n).a},f4d5:function(e,t,a){"use strict";var n=a("2bf8");a.n(n).a}}]);