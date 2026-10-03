var Q=globalThis,z=Q.ShadowRoot&&(Q.ShadyCSS===void 0||Q.ShadyCSS.nativeShadow)&&"adoptedStyleSheets"in Document.prototype&&"replace"in CSSStyleSheet.prototype,M1=Symbol(),f1=new WeakMap,R=class{constructor(C,H,V){if(this._$cssResult$=!0,V!==M1)throw Error("CSSResult is not constructable. Use `unsafeCSS` or `css` instead.");this.cssText=C,this.t=H}get styleSheet(){let C=this.o,H=this.t;if(z&&C===void 0){let V=H!==void 0&&H.length===1;V&&(C=f1.get(H)),C===void 0&&((this.o=C=new CSSStyleSheet).replaceSync(this.cssText),V&&f1.set(H,C))}return C}toString(){return this.cssText}},k1=M=>new R(typeof M=="string"?M:M+"",void 0,M1),r1=(M,...C)=>{let H=M.length===1?M[0]:C.reduce((V,L,r)=>V+(e=>{if(e._$cssResult$===!0)return e.cssText;if(typeof e=="number")return e;throw Error("Value passed to 'css' function must be a 'css' function result: "+e+". Use 'unsafeCSS' to pass non-literal values, but take care to ensure page security.")})(L)+M[r+1],M[0]);return new R(H,M,M1)},b1=(M,C)=>{if(z)M.adoptedStyleSheets=C.map(H=>H instanceof CSSStyleSheet?H:H.styleSheet);else for(let H of C){let V=document.createElement("style"),L=Q.litNonce;L!==void 0&&V.setAttribute("nonce",L),V.textContent=H.cssText,M.appendChild(V)}},e1=z?M=>M:M=>M instanceof CSSStyleSheet?(C=>{let H="";for(let V of C.cssRules)H+=V.cssText;return k1(H)})(M):M;var{is:w2,defineProperty:B2,getOwnPropertyDescriptor:y2,getOwnPropertyNames:P2,getOwnPropertySymbols:T2,getPrototypeOf:F2}=Object,K=globalThis,w1=K.trustedTypes,R2=w1?w1.emptyScript:"",_2=K.reactiveElementPolyfillSupport,_=(M,C)=>M,t1={toAttribute(M,C){switch(C){case Boolean:M=M?R2:null;break;case Object:case Array:M=M==null?M:JSON.stringify(M)}return M},fromAttribute(M,C){let H=M;switch(C){case Boolean:H=M!==null;break;case Number:H=M===null?null:Number(M);break;case Object:case Array:try{H=JSON.parse(M)}catch{H=null}}return H}},y1=(M,C)=>!w2(M,C),B1={attribute:!0,type:String,converter:t1,reflect:!1,useDefault:!1,hasChanged:y1};Symbol.metadata??=Symbol("metadata"),K.litPropertyMetadata??=new WeakMap;var h=class extends HTMLElement{static addInitializer(C){this._$Ei(),(this.l??=[]).push(C)}static get observedAttributes(){return this.finalize(),this._$Eh&&[...this._$Eh.keys()]}static createProperty(C,H=B1){if(H.state&&(H.attribute=!1),this._$Ei(),this.prototype.hasOwnProperty(C)&&((H=Object.create(H)).wrapped=!0),this.elementProperties.set(C,H),!H.noAccessor){let V=Symbol(),L=this.getPropertyDescriptor(C,V,H);L!==void 0&&B2(this.prototype,C,L)}}static getPropertyDescriptor(C,H,V){let{get:L,set:r}=y2(this.prototype,C)??{get(){return this[H]},set(e){this[H]=e}};return{get:L,set(e){let t=L?.call(this);r?.call(this,e),this.requestUpdate(C,t,V)},configurable:!0,enumerable:!0}}static getPropertyOptions(C){return this.elementProperties.get(C)??B1}static _$Ei(){if(this.hasOwnProperty(_("elementProperties")))return;let C=F2(this);C.finalize(),C.l!==void 0&&(this.l=[...C.l]),this.elementProperties=new Map(C.elementProperties)}static finalize(){if(this.hasOwnProperty(_("finalized")))return;if(this.finalized=!0,this._$Ei(),this.hasOwnProperty(_("properties"))){let H=this.properties,V=[...P2(H),...T2(H)];for(let L of V)this.createProperty(L,H[L])}let C=this[Symbol.metadata];if(C!==null){let H=litPropertyMetadata.get(C);if(H!==void 0)for(let[V,L]of H)this.elementProperties.set(V,L)}this._$Eh=new Map;for(let[H,V]of this.elementProperties){let L=this._$Eu(H,V);L!==void 0&&this._$Eh.set(L,H)}this.elementStyles=this.finalizeStyles(this.styles)}static finalizeStyles(C){let H=[];if(Array.isArray(C)){let V=new Set(C.flat(1/0).reverse());for(let L of V)H.unshift(e1(L))}else C!==void 0&&H.push(e1(C));return H}static _$Eu(C,H){let V=H.attribute;return V===!1?void 0:typeof V=="string"?V:typeof C=="string"?C.toLowerCase():void 0}constructor(){super(),this._$Ep=void 0,this.isUpdatePending=!1,this.hasUpdated=!1,this._$Em=null,this._$Ev()}_$Ev(){this._$ES=new Promise(C=>this.enableUpdating=C),this._$AL=new Map,this._$E_(),this.requestUpdate(),this.constructor.l?.forEach(C=>C(this))}addController(C){(this._$EO??=new Set).add(C),this.renderRoot!==void 0&&this.isConnected&&C.hostConnected?.()}removeController(C){this._$EO?.delete(C)}_$E_(){let C=new Map,H=this.constructor.elementProperties;for(let V of H.keys())this.hasOwnProperty(V)&&(C.set(V,this[V]),delete this[V]);C.size>0&&(this._$Ep=C)}createRenderRoot(){let C=this.shadowRoot??this.attachShadow(this.constructor.shadowRootOptions);return b1(C,this.constructor.elementStyles),C}connectedCallback(){this.renderRoot??=this.createRenderRoot(),this.enableUpdating(!0),this._$EO?.forEach(C=>C.hostConnected?.())}enableUpdating(C){}disconnectedCallback(){this._$EO?.forEach(C=>C.hostDisconnected?.())}attributeChangedCallback(C,H,V){this._$AK(C,V)}_$ET(C,H){let V=this.constructor.elementProperties.get(C),L=this.constructor._$Eu(C,V);if(L!==void 0&&V.reflect===!0){let r=(V.converter?.toAttribute!==void 0?V.converter:t1).toAttribute(H,V.type);this._$Em=C,r==null?this.removeAttribute(L):this.setAttribute(L,r),this._$Em=null}}_$AK(C,H){let V=this.constructor,L=V._$Eh.get(C);if(L!==void 0&&this._$Em!==L){let r=V.getPropertyOptions(L),e=typeof r.converter=="function"?{fromAttribute:r.converter}:r.converter?.fromAttribute!==void 0?r.converter:t1;this._$Em=L;let t=e.fromAttribute(H,r.type);this[L]=t??this._$Ej?.get(L)??t,this._$Em=null}}requestUpdate(C,H,V,L=!1,r){if(C!==void 0){let e=this.constructor;if(L===!1&&(r=this[C]),V??=e.getPropertyOptions(C),!((V.hasChanged??y1)(r,H)||V.useDefault&&V.reflect&&r===this._$Ej?.get(C)&&!this.hasAttribute(e._$Eu(C,V))))return;this.C(C,H,V)}this.isUpdatePending===!1&&(this._$ES=this._$EP())}C(C,H,{useDefault:V,reflect:L,wrapped:r},e){V&&!(this._$Ej??=new Map).has(C)&&(this._$Ej.set(C,e??H??this[C]),r!==!0||e!==void 0)||(this._$AL.has(C)||(this.hasUpdated||V||(H=void 0),this._$AL.set(C,H)),L===!0&&this._$Em!==C&&(this._$Eq??=new Set).add(C))}async _$EP(){this.isUpdatePending=!0;try{await this._$ES}catch(H){Promise.reject(H)}let C=this.scheduleUpdate();return C!=null&&await C,!this.isUpdatePending}scheduleUpdate(){return this.performUpdate()}performUpdate(){if(!this.isUpdatePending)return;if(!this.hasUpdated){if(this.renderRoot??=this.createRenderRoot(),this._$Ep){for(let[L,r]of this._$Ep)this[L]=r;this._$Ep=void 0}let V=this.constructor.elementProperties;if(V.size>0)for(let[L,r]of V){let{wrapped:e}=r,t=this[L];e!==!0||this._$AL.has(L)||t===void 0||this.C(L,void 0,r,t)}}let C=!1,H=this._$AL;try{C=this.shouldUpdate(H),C?(this.willUpdate(H),this._$EO?.forEach(V=>V.hostUpdate?.()),this.update(H)):this._$EM()}catch(V){throw C=!1,this._$EM(),V}C&&this._$AE(H)}willUpdate(C){}_$AE(C){this._$EO?.forEach(H=>H.hostUpdated?.()),this.hasUpdated||(this.hasUpdated=!0,this.firstUpdated(C)),this.updated(C)}_$EM(){this._$AL=new Map,this.isUpdatePending=!1}get updateComplete(){return this.getUpdateComplete()}getUpdateComplete(){return this._$ES}shouldUpdate(C){return!0}update(C){this._$Eq&&=this._$Eq.forEach(H=>this._$ET(H,this[H])),this._$EM()}updated(C){}firstUpdated(C){}};h.elementStyles=[],h.shadowRootOptions={mode:"open"},h[_("elementProperties")]=new Map,h[_("finalized")]=new Map,_2?.({ReactiveElement:h}),(K.reactiveElementVersions??=[]).push("2.1.2");var m1=globalThis,P1=M=>M,q=m1.trustedTypes,T1=q?q.createPolicy("lit-html",{createHTML:M=>M}):void 0,W1="$lit$",g=`lit$${Math.random().toFixed(9).slice(2)}$`,N1="?"+g,D2=`<${N1}>`,b=document,E=()=>b.createComment(""),W=M=>M===null||typeof M!="object"&&typeof M!="function",n1=Array.isArray,E2=M=>n1(M)||typeof M?.[Symbol.iterator]=="function",i1=`[ 	
\f\r]`,D=/<(?:(!--|\/[^a-zA-Z])|(\/?[a-zA-Z][^>\s]*)|(\/?$))/g,F1=/-->/g,R1=/>/g,f=RegExp(`>|${i1}(?:([^\\s"'>=/]+)(${i1}*=${i1}*(?:[^ 	
\f\r"'\`<>=]|("|')|))|$)`,"g"),_1=/'/g,D1=/"/g,$1=/^(?:script|style|textarea|title)$/i,v1=M=>(C,...H)=>({_$litType$:M,strings:C,values:H}),p=v1(1),l1=v1(2),t5=v1(3),w=Symbol.for("lit-noChange"),d=Symbol.for("lit-nothing"),E1=new WeakMap,k=b.createTreeWalker(b,129);function I1(M,C){if(!n1(M)||!M.hasOwnProperty("raw"))throw Error("invalid template strings array");return T1!==void 0?T1.createHTML(C):C}var W2=(M,C)=>{let H=M.length-1,V=[],L,r=C===2?"<svg>":C===3?"<math>":"",e=D;for(let t=0;t<H;t++){let i=M[t],A,a,o=-1,m=0;for(;m<i.length&&(e.lastIndex=m,a=e.exec(i),a!==null);)m=e.lastIndex,e===D?a[1]==="!--"?e=F1:a[1]!==void 0?e=R1:a[2]!==void 0?($1.test(a[2])&&(L=RegExp("</"+a[2],"g")),e=f):a[3]!==void 0&&(e=f):e===f?a[0]===">"?(e=L??D,o=-1):a[1]===void 0?o=-2:(o=e.lastIndex-a[2].length,A=a[1],e=a[3]===void 0?f:a[3]==='"'?D1:_1):e===D1||e===_1?e=f:e===F1||e===R1?e=D:(e=f,L=void 0);let n=e===f&&M[t+1].startsWith("/>")?" ":"";r+=e===D?i+D2:o>=0?(V.push(A),i.slice(0,o)+W1+i.slice(o)+g+n):i+g+(o===-2?t:n)}return[I1(M,r+(M[H]||"<?>")+(C===2?"</svg>":C===3?"</math>":"")),V]},N=class M{constructor({strings:C,_$litType$:H},V){let L;this.parts=[];let r=0,e=0,t=C.length-1,i=this.parts,[A,a]=W2(C,H);if(this.el=M.createElement(A,V),k.currentNode=this.el.content,H===2||H===3){let o=this.el.content.firstChild;o.replaceWith(...o.childNodes)}for(;(L=k.nextNode())!==null&&i.length<t;){if(L.nodeType===1){if(L.hasAttributes())for(let o of L.getAttributeNames())if(o.endsWith(W1)){let m=a[e++],n=L.getAttribute(o).split(g),v=/([.?@])?(.*)/.exec(m);i.push({type:1,index:r,name:v[2],strings:n,ctor:v[1]==="."?A1:v[1]==="?"?a1:v[1]==="@"?d1:P}),L.removeAttribute(o)}else o.startsWith(g)&&(i.push({type:6,index:r}),L.removeAttribute(o));if($1.test(L.tagName)){let o=L.textContent.split(g),m=o.length-1;if(m>0){L.textContent=q?q.emptyScript:"";for(let n=0;n<m;n++)L.append(o[n],E()),k.nextNode(),i.push({type:2,index:++r});L.append(o[m],E())}}}else if(L.nodeType===8)if(L.data===N1)i.push({type:2,index:r});else{let o=-1;for(;(o=L.data.indexOf(g,o+1))!==-1;)i.push({type:7,index:r}),o+=g.length-1}r++}}static createElement(C,H){let V=b.createElement("template");return V.innerHTML=C,V}};function y(M,C,H=M,V){if(C===w)return C;let L=V!==void 0?H._$Co?.[V]:H._$Cl,r=W(C)?void 0:C._$litDirective$;return L?.constructor!==r&&(L?._$AO?.(!1),r===void 0?L=void 0:(L=new r(M),L._$AT(M,H,V)),V!==void 0?(H._$Co??=[])[V]=L:H._$Cl=L),L!==void 0&&(C=y(M,L._$AS(M,C.values),L,V)),C}var o1=class{constructor(C,H){this._$AV=[],this._$AN=void 0,this._$AD=C,this._$AM=H}get parentNode(){return this._$AM.parentNode}get _$AU(){return this._$AM._$AU}u(C){let{el:{content:H},parts:V}=this._$AD,L=(C?.creationScope??b).importNode(H,!0);k.currentNode=L;let r=k.nextNode(),e=0,t=0,i=V[0];for(;i!==void 0;){if(e===i.index){let A;i.type===2?A=new $(r,r.nextSibling,this,C):i.type===1?A=new i.ctor(r,i.name,i.strings,this,C):i.type===6&&(A=new p1(r,this,C)),this._$AV.push(A),i=V[++t]}e!==i?.index&&(r=k.nextNode(),e++)}return k.currentNode=b,L}p(C){let H=0;for(let V of this._$AV)V!==void 0&&(V.strings!==void 0?(V._$AI(C,V,H),H+=V.strings.length-2):V._$AI(C[H])),H++}},$=class M{get _$AU(){return this._$AM?._$AU??this._$Cv}constructor(C,H,V,L){this.type=2,this._$AH=d,this._$AN=void 0,this._$AA=C,this._$AB=H,this._$AM=V,this.options=L,this._$Cv=L?.isConnected??!0}get parentNode(){let C=this._$AA.parentNode,H=this._$AM;return H!==void 0&&C?.nodeType===11&&(C=H.parentNode),C}get startNode(){return this._$AA}get endNode(){return this._$AB}_$AI(C,H=this){C=y(this,C,H),W(C)?C===d||C==null||C===""?(this._$AH!==d&&this._$AR(),this._$AH=d):C!==this._$AH&&C!==w&&this._(C):C._$litType$!==void 0?this.$(C):C.nodeType!==void 0?this.T(C):E2(C)?this.k(C):this._(C)}O(C){return this._$AA.parentNode.insertBefore(C,this._$AB)}T(C){this._$AH!==C&&(this._$AR(),this._$AH=this.O(C))}_(C){this._$AH!==d&&W(this._$AH)?this._$AA.nextSibling.data=C:this.T(b.createTextNode(C)),this._$AH=C}$(C){let{values:H,_$litType$:V}=C,L=typeof V=="number"?this._$AC(C):(V.el===void 0&&(V.el=N.createElement(I1(V.h,V.h[0]),this.options)),V);if(this._$AH?._$AD===L)this._$AH.p(H);else{let r=new o1(L,this),e=r.u(this.options);r.p(H),this.T(e),this._$AH=r}}_$AC(C){let H=E1.get(C.strings);return H===void 0&&E1.set(C.strings,H=new N(C)),H}k(C){n1(this._$AH)||(this._$AH=[],this._$AR());let H=this._$AH,V,L=0;for(let r of C)L===H.length?H.push(V=new M(this.O(E()),this.O(E()),this,this.options)):V=H[L],V._$AI(r),L++;L<H.length&&(this._$AR(V&&V._$AB.nextSibling,L),H.length=L)}_$AR(C=this._$AA.nextSibling,H){for(this._$AP?.(!1,!0,H);C!==this._$AB;){let V=P1(C).nextSibling;P1(C).remove(),C=V}}setConnected(C){this._$AM===void 0&&(this._$Cv=C,this._$AP?.(C))}},P=class{get tagName(){return this.element.tagName}get _$AU(){return this._$AM._$AU}constructor(C,H,V,L,r){this.type=1,this._$AH=d,this._$AN=void 0,this.element=C,this.name=H,this._$AM=L,this.options=r,V.length>2||V[0]!==""||V[1]!==""?(this._$AH=Array(V.length-1).fill(new String),this.strings=V):this._$AH=d}_$AI(C,H=this,V,L){let r=this.strings,e=!1;if(r===void 0)C=y(this,C,H,0),e=!W(C)||C!==this._$AH&&C!==w,e&&(this._$AH=C);else{let t=C,i,A;for(C=r[0],i=0;i<r.length-1;i++)A=y(this,t[V+i],H,i),A===w&&(A=this._$AH[i]),e||=!W(A)||A!==this._$AH[i],A===d?C=d:C!==d&&(C+=(A??"")+r[i+1]),this._$AH[i]=A}e&&!L&&this.j(C)}j(C){C===d?this.element.removeAttribute(this.name):this.element.setAttribute(this.name,C??"")}},A1=class extends P{constructor(){super(...arguments),this.type=3}j(C){this.element[this.name]=C===d?void 0:C}},a1=class extends P{constructor(){super(...arguments),this.type=4}j(C){this.element.toggleAttribute(this.name,!!C&&C!==d)}},d1=class extends P{constructor(C,H,V,L,r){super(C,H,V,L,r),this.type=5}_$AI(C,H=this){if((C=y(this,C,H,0)??d)===w)return;let V=this._$AH,L=C===d&&V!==d||C.capture!==V.capture||C.once!==V.once||C.passive!==V.passive,r=C!==d&&(V===d||L);L&&this.element.removeEventListener(this.name,this,V),r&&this.element.addEventListener(this.name,this,C),this._$AH=C}handleEvent(C){typeof this._$AH=="function"?this._$AH.call(this.options?.host??this.element,C):this._$AH.handleEvent(C)}},p1=class{constructor(C,H,V){this.element=C,this.type=6,this._$AN=void 0,this._$AM=H,this.options=V}get _$AU(){return this._$AM._$AU}_$AI(C){y(this,C)}};var N2=m1.litHtmlPolyfillSupport;N2?.(N,$),(m1.litHtmlVersions??=[]).push("3.3.3");var G1=(M,C,H)=>{let V=H?.renderBefore??C,L=V._$litPart$;if(L===void 0){let r=H?.renderBefore??null;V._$litPart$=L=new $(C.insertBefore(E(),r),r,void 0,H??{})}return L._$AI(M),L};var x1=globalThis,c=class extends h{constructor(){super(...arguments),this.renderOptions={host:this},this._$Do=void 0}createRenderRoot(){let C=super.createRenderRoot();return this.renderOptions.renderBefore??=C.firstChild,C}update(C){let H=this.render();this.hasUpdated||(this.renderOptions.isConnected=this.isConnected),super.update(C),this._$Do=G1(H,this.renderRoot,this.renderOptions)}connectedCallback(){super.connectedCallback(),this._$Do?.setConnected(!0)}disconnectedCallback(){super.disconnectedCallback(),this._$Do?.setConnected(!1)}render(){return w}};c._$litElement$=!0,c.finalized=!0,x1.litElementHydrateSupport?.({LitElement:c});var $2=x1.litElementPolyfillSupport;$2?.({LitElement:c});(x1.litElementVersions??=[]).push("4.2.2");var U1="M11,15H13V17H11V15M11,7H13V13H11V7M12,2C6.47,2 2,6.5 2,12A10,10 0 0,0 12,22A10,10 0 0,0 22,12A10,10 0 0,0 12,2M12,20A8,8 0 0,1 4,12A8,8 0 0,1 12,4A8,8 0 0,1 20,12A8,8 0 0,1 12,20Z";var Q1="M11,4H13V16L18.5,10.5L19.92,11.92L12,19.84L4.08,11.92L5.5,10.5L11,16V4Z";var z1="M20,11V13H8L13.5,18.5L12.08,19.92L4.16,12L12.08,4.08L13.5,5.5L8,11H20Z";var K1="M4,11V13H16L10.5,18.5L11.92,19.92L19.84,12L11.92,4.08L10.5,5.5L16,11H4Z";var q1="M13,20H11V8L5.5,13.5L4.08,12.08L12,4.16L19.92,12.08L18.5,13.5L13,8V20Z";var j1="M16 20H8V6H16M16.67 4H15V2H9V4H7.33C6.6 4 6 4.6 6 5.33V20.67C6 21.4 6.6 22 7.33 22H16.67C17.41 22 18 21.41 18 20.67V5.33C18 4.6 17.4 4 16.67 4M15 16H9V19H15V16M15 7H9V10H15V7M15 11.5H9V14.5H15V11.5Z";var X1="M16 20H8V6H16M16.67 4H15V2H9V4H7.33C6.6 4 6 4.6 6 5.33V20.67C6 21.4 6.6 22 7.33 22H16.67C17.41 22 18 21.41 18 20.67V5.33C18 4.6 17.4 4 16.67 4M15 16H9V19H15V16",J1="M16 20H8V6H16M16.67 4H15V2H9V4H7.33C6.6 4 6 4.6 6 5.33V20.67C6 21.4 6.6 22 7.33 22H16.67C17.41 22 18 21.41 18 20.67V5.33C18 4.6 17.4 4 16.67 4M15 16H9V19H15V16M15 11.5H9V14.5H15V11.5Z";var Y1="M16,20H8V6H16M16.67,4H15V2H9V4H7.33A1.33,1.33 0 0,0 6,5.33V20.67C6,21.4 6.6,22 7.33,22H16.67A1.33,1.33 0 0,0 18,20.67V5.33C18,4.6 17.4,4 16.67,4Z";var C2="M15,13H16.5V15.82L18.94,17.23L18.19,18.53L15,16.69V13M19,8H5V19H9.67C9.24,18.09 9,17.07 9,16A7,7 0 0,1 16,9C17.07,9 18.09,9.24 19,9.67V8M5,21C3.89,21 3,20.1 3,19V5C3,3.89 3.89,3 5,3H6V1H8V3H16V1H18V3H19A2,2 0 0,1 21,5V11.1C22.24,12.36 23,14.09 23,16A7,7 0 0,1 16,23C14.09,23 12.36,22.24 11.1,21H5M16,11.15A4.85,4.85 0 0,0 11.15,16C11.15,18.68 13.32,20.85 16,20.85A4.85,4.85 0 0,0 20.85,16C20.85,13.32 18.68,11.15 16,11.15Z";var H2="M19,19H5V8H19M19,3H18V1H16V3H8V1H6V3H5C3.89,3 3,3.9 3,5V19A2,2 0 0,0 5,21H19A2,2 0 0,0 21,19V5A2,2 0 0,0 19,3M9.31,17L11.75,14.56L14.19,17L15.25,15.94L12.81,13.5L15.25,11.06L14.19,10L11.75,12.44L9.31,10L8.25,11.06L10.69,13.5L8.25,15.94L9.31,17Z";var V2="M19.8 22.6L17.15 20H6.5Q4.2 20 2.6 18.4T1 14.5Q1 12.58 2.19 11.08 3.38 9.57 5.25 9.15 5.33 8.95 5.4 8.76 5.5 8.57 5.55 8.35L1.4 4.2L2.8 2.8L21.2 21.2M6.5 18H15.15L7.1 9.95Q7.05 10.23 7.03 10.5 7 10.73 7 11H6.5Q5.05 11 4.03 12.03 3 13.05 3 14.5 3 15.95 4.03 17 5.05 18 6.5 18M11.13 14M21.6 18.75L20.15 17.35Q20.58 17 20.79 16.54 21 16.08 21 15.5 21 14.45 20.27 13.73 19.55 13 18.5 13H17V11Q17 8.93 15.54 7.46 14.08 6 12 6 11.33 6 10.7 6.16 10.07 6.33 9.5 6.68L8.05 5.23Q8.93 4.63 9.91 4.31 10.9 4 12 4 14.93 4 16.96 6.04 19 8.07 19 11 20.73 11.2 21.86 12.5 23 13.78 23 15.5 23 16.5 22.63 17.31 22.25 18.15 21.6 18.75M14.83 12.03Z";var L2="M18,11H6A2,2 0 0,0 4,13V21A2,2 0 0,0 6,23H18A2,2 0 0,0 20,21V13A2,2 0 0,0 18,11M18,21H6V17H18V21M18,15H6V13H18V15M4.93,4.92L6.34,6.33C9.46,3.2 14.53,3.2 17.66,6.33L19.07,4.92C15.17,1 8.84,1 4.93,4.92M7.76,7.75L9.17,9.16C10.73,7.6 13.26,7.6 14.83,9.16L16.24,7.75C13.9,5.41 10.1,5.41 7.76,7.75Z";var M2="M15 18.5C12.5 18.5 10.32 17.08 9.24 15H15L16 13H8.58C8.53 12.67 8.5 12.34 8.5 12S8.53 11.33 8.58 11H15L16 9H9.24C10.32 6.92 12.5 5.5 15 5.5C16.61 5.5 18.09 6.09 19.23 7.07L21 5.3C19.41 3.87 17.3 3 15 3C11.08 3 7.76 5.5 6.5 9H3L2 11H6.06C6 11.33 6 11.66 6 12S6 12.67 6.06 13H3L2 15H6.5C7.76 18.5 11.08 21 15 21C17.31 21 19.41 20.13 21 18.7L19.22 16.93C18.09 17.91 16.62 18.5 15 18.5Z";var j="M19.77,7.23L19.78,7.22L16.06,3.5L15,4.56L17.11,6.67C16.17,7.03 15.5,7.93 15.5,9A2.5,2.5 0 0,0 18,11.5C18.36,11.5 18.69,11.42 19,11.29V18.5A1,1 0 0,1 18,19.5A1,1 0 0,1 17,18.5V14A2,2 0 0,0 15,12H14V5A2,2 0 0,0 12,3H6A2,2 0 0,0 4,5V21H14V13.5H15.5V18.5A2.5,2.5 0 0,0 18,21A2.5,2.5 0 0,0 20.5,18.5V9C20.5,8.31 20.22,7.68 19.77,7.23M18,10A1,1 0 0,1 17,9A1,1 0 0,1 18,8A1,1 0 0,1 19,9A1,1 0 0,1 18,10M8,18V13.5H6L10,6V11H12L8,18Z";var r2="M7,2V13H10V22L17,10H13L17,2H7Z";var e2="M7,5H21V7H7V5M7,13V11H21V13H7M4,4.5A1.5,1.5 0 0,1 5.5,6A1.5,1.5 0 0,1 4,7.5A1.5,1.5 0 0,1 2.5,6A1.5,1.5 0 0,1 4,4.5M4,10.5A1.5,1.5 0 0,1 5.5,12A1.5,1.5 0 0,1 4,13.5A1.5,1.5 0 0,1 2.5,12A1.5,1.5 0 0,1 4,10.5M7,19V17H21V19H7M4,16.5A1.5,1.5 0 0,1 5.5,18A1.5,1.5 0 0,1 4,19.5A1.5,1.5 0 0,1 2.5,18A1.5,1.5 0 0,1 4,16.5Z";var t2="M13.5,8H12V13L16.28,15.54L17,14.33L13.5,12.25V8M13,3A9,9 0 0,0 4,12H1L4.96,16.03L9,12H6A7,7 0 0,1 13,5A7,7 0 0,1 20,12A7,7 0 0,1 13,19C11.07,19 9.32,18.21 8.06,16.94L6.64,18.36C8.27,20 10.5,21 13,21A9,9 0 0,0 22,12A9,9 0 0,0 13,3";var i2="M5 20V12H2L12 3L22 12H19V20H5M12 5.69L7 10.19V18H17V10.19L12 5.69M11.5 18V14H9L12.5 7V11H15L11.5 18Z";var o2="M11 15H6L13 1V9H18L11 23V15Z";var A2="M12,17A2,2 0 0,0 14,15C14,13.89 13.1,13 12,13A2,2 0 0,0 10,15A2,2 0 0,0 12,17M18,8A2,2 0 0,1 20,10V20A2,2 0 0,1 18,22H6A2,2 0 0,1 4,20V10C4,8.89 4.9,8 6,8H7V6A5,5 0 0,1 12,1A5,5 0 0,1 17,6V8H18M12,3A3,3 0 0,0 9,6V8H15V6A3,3 0 0,0 12,3Z";var Z1="M18 1C15.24 1 13 3.24 13 6V8H4C2.9 8 2 8.89 2 10V20C2 21.11 2.9 22 4 22H16C17.11 22 18 21.11 18 20V10C18 8.9 17.11 8 16 8H15V6C15 4.34 16.34 3 18 3C19.66 3 21 4.34 21 6V8H23V6C23 3.24 20.76 1 18 1M10 13C11.1 13 12 13.89 12 15C12 16.11 11.11 17 10 17C8.9 17 8 16.11 8 15C8 13.9 8.9 13 10 13Z";var a2="M7,10L12,15L17,10H7Z";var d2="M8,5.14V19.14L19,12.14L8,5.14Z";var p2="M13.13 22.19L11.5 18.36C13.07 17.78 14.54 17 15.9 16.09L13.13 22.19M5.64 12.5L1.81 10.87L7.91 8.1C7 9.46 6.22 10.93 5.64 12.5M21.61 2.39C21.61 2.39 16.66 .269 11 5.93C8.81 8.12 7.5 10.53 6.65 12.64C6.37 13.39 6.56 14.21 7.11 14.77L9.24 16.89C9.79 17.45 10.61 17.63 11.36 17.35C13.5 16.53 15.88 15.19 18.07 13C23.73 7.34 21.61 2.39 21.61 2.39M14.54 9.46C13.76 8.68 13.76 7.41 14.54 6.63S16.59 5.85 17.37 6.63C18.14 7.41 18.15 8.68 17.37 9.46C16.59 10.24 15.32 10.24 14.54 9.46M8.88 16.53L7.47 15.12L8.88 16.53M6.24 22L9.88 18.36C9.54 18.27 9.21 18.12 8.91 17.91L4.83 22H6.24M2 22H3.41L8.18 17.24L6.76 15.83L2 20.59V22M2 19.17L6.09 15.09C5.88 14.79 5.73 14.47 5.64 14.12L2 17.76V19.17Z";var X="M11.45,2V5.55L15,3.77L11.45,2M10.45,8L8,10.46L11.75,11.71L10.45,8M2,11.45L3.77,15L5.55,11.45H2M10,2H2V10C2.57,10.17 3.17,10.25 3.77,10.25C7.35,10.26 10.26,7.35 10.27,3.75C10.26,3.16 10.17,2.57 10,2M17,22V16H14L19,7V13H22L17,22Z";var m2="M18,18H6V6H18V18Z";var n2="M15 13V5A3 3 0 0 0 9 5V13A5 5 0 1 0 15 13M12 4A1 1 0 0 1 13 5V8H11V5A1 1 0 0 1 12 4Z";var v2="M12,20A7,7 0 0,1 5,13A7,7 0 0,1 12,6A7,7 0 0,1 19,13A7,7 0 0,1 12,20M19.03,7.39L20.45,5.97C20,5.46 19.55,5 19.04,4.56L17.62,6C16.07,4.74 14.12,4 12,4A9,9 0 0,0 3,13A9,9 0 0,0 12,22C17,22 21,17.97 21,13C21,10.88 20.26,8.93 19.03,7.39M11,14H13V8H11M15,1H9V3H15V1Z";var S1="M8.28,5.45L6.5,4.55L7.76,2H16.23L17.5,4.55L15.72,5.44L15,4H9L8.28,5.45M18.62,8H14.09L13.3,5H10.7L9.91,8H5.38L4.1,10.55L5.89,11.44L6.62,10H17.38L18.1,11.45L19.89,10.56L18.62,8M17.77,22H15.7L15.46,21.1L12,15.9L8.53,21.1L8.3,22H6.23L9.12,11H11.19L10.83,12.35L12,14.1L13.16,12.35L12.81,11H14.88L17.77,22M11.4,15L10.5,13.65L9.32,18.13L11.4,15M14.68,18.12L13.5,13.64L12.6,15L14.68,18.12Z";var s1="M17.75,4.09L15.22,6.03L16.13,9.09L13.5,7.28L10.87,9.09L11.78,6.03L9.25,4.09L12.44,4L13.5,1L14.56,4L17.75,4.09M21.25,11L19.61,12.25L20.2,14.23L18.5,13.06L16.8,14.23L17.39,12.25L15.75,11L17.81,10.95L18.5,9L19.19,10.95L21.25,11M18.97,15.95C19.8,15.87 20.69,17.05 20.16,17.8C19.84,18.25 19.5,18.67 19.08,19.07C15.17,23 8.84,23 4.94,19.07C1.03,15.17 1.03,8.83 4.94,4.93C5.34,4.53 5.76,4.17 6.21,3.85C6.96,3.32 8.14,4.21 8.06,5.04C7.79,7.9 8.75,10.87 10.95,13.06C13.14,15.26 16.1,16.22 18.97,15.95M17.33,17.97C14.5,17.81 11.7,16.64 9.53,14.5C7.36,12.31 6.2,9.5 6.04,6.68C3.23,9.82 3.34,14.64 6.35,17.66C9.37,20.67 14.19,20.78 17.33,17.97Z";var J="growatt_thor_cloud",u1=["charging","suspended_ev","suspended_evse"],l2=[...u1,"finishing"];function x2(M){let C=new Set;for(let H of Object.values(M.entities))H.platform===J&&H.device_id&&C.add(H.device_id);return[...C]}function Z2(M,C){let H=new Map;if(!C)return H;for(let V of Object.values(M.entities))V.platform!==J||V.device_id!==C||!V.translation_key||H.set(`${V.entity_id.split(".")[0]}.${V.translation_key}`,V.entity_id);return H}var Y={card_name:"THOR Wallbox",card_description:"Status, power, session and controls of a Growatt THOR wallbox.",no_device:"Pick the wallbox in the card editor.",device_not_found:"Wallbox not found: check the device in the card editor.",plug_in:"Plug in the car to start",car_connected:"Car connected",waiting_surplus:"Waiting for surplus",waiting_slot:"Waiting for the off-peak slot",start:"Start charging",stop:"Stop",unlock:"Unlock connector",cancel:"Cancel start",charge_mode:"Charge mode",locked_note:"Mode and settings can be changed once the session is over and the car is unplugged.",energy:"Energy",duration:"Duration",cost:"Cost",last_session:"Last charge",scheduled_start:"Scheduled start",every_day:"Every day at {time}",cable_locked:"Cable locked",cable_unlocked:"Cable unlocked",surplus_only:"Surplus only",grid_import:"Grid import",grid_import_power:"Grid import \xB7 {power}",boost:"Boost \xB7 {type}",slots:"Off-peak slots",warm_up:"Warm-up",limit_energy:"Energy limit",limit_cost:"Cost limit",limit_duration:"Duration limit",boost_by:"Smart Boost by {time}",done_of:"{done} of {target}",fault:"Fault",vendor_code:"Vendor code: {code}.",fault_hint:"If it persists, contact your installer.",offline_title:"Wallbox unreachable",offline_text:"It is not connected to the Growatt cloud: data and controls come back once it reconnects.",rfid_title:"RFID mode",rfid_text:"Start and stop with the card only. Scheduled starts still work.",solar:"Solar",wallbox:"Wallbox",grid:"Grid",battery:"Battery",from_solar:"from solar {value}",from_battery:"from the battery {value}",from_grid:"from the grid {value}",surplus:"Available surplus: {value}.",battery_charging:"The home battery is taking {value}: while it charges, the wallbox only gets what is left over.",battery_charging_soc:"The home battery ({soc}) is taking {value}: while it charges, the wallbox only gets what is left over.",power:"Charging power",editor_device_id:"Wallbox",editor_name:"Name",editor_flow:"Energy flow",editor_solar_power:"Solar production",editor_home_power:"Home consumption",editor_grid_import_power:"Grid import",editor_grid_export_power:"Grid export",editor_battery_power:"Home battery power",editor_battery_charging_positive:"Battery power is positive while charging",editor_battery_soc:"Home battery charge",editor_home_includes_wallbox:"Home consumption includes the wallbox",editor_content:"Content",editor_show_session:"Session",editor_show_progress:"Progress",editor_show_controls:"Controls",editor_show_last_session:"Last charge",helper_solar_power:"Power sensors of the inverter, to show where the wallbox power comes from.",helper_home_power:"Optional: with it the card works out the solar surplus.",helper_grid_export_power:"Recommended for PV Linkage: the surplus becomes the power exported to the grid, the same value the wallbox reads from the meter.",helper_battery_power:"Optional: shows the home battery, which takes the surplus first while it charges.",helper_battery_charging_positive:"On when the sensor is positive while charging and negative while discharging.",helper_home_includes_wallbox:"On when the wallbox is downstream of the home consumption sensor.",helper_show_session:"Energy, duration and cost while a session is open.",helper_show_progress:"Fast limit or smart Boost energy reached.",helper_show_controls:"Start, stop, unlock and charge mode.",helper_show_last_session:"While no session is open."},I2={card_name:"THOR Wallbox",card_description:"Stato, potenza, sessione e comandi di una wallbox Growatt THOR.",no_device:"Scegli la wallbox nell'editor della card.",device_not_found:"Wallbox non trovata: controlla il dispositivo nell'editor della card.",plug_in:"Collega l'auto per iniziare",car_connected:"Auto collegata",waiting_surplus:"In attesa di surplus",waiting_slot:"In attesa della fascia Off-peak",start:"Avvia ricarica",stop:"Arresta",unlock:"Sblocca connettore",cancel:"Annulla avvio",charge_mode:"Modalit\xE0 di ricarica",locked_note:"Modalit\xE0 e impostazioni si cambiano a sessione chiusa, con l'auto scollegata.",energy:"Energia",duration:"Durata",cost:"Costo",last_session:"Ultima ricarica",scheduled_start:"Avvio programmato",every_day:"Ogni giorno alle {time}",cable_locked:"Cavo bloccato",cable_unlocked:"Cavo sbloccato",surplus_only:"Solo surplus",grid_import:"Importa da rete",grid_import_power:"Importa da rete \xB7 {power}",boost:"Boost \xB7 {type}",slots:"Fasce Off-peak",warm_up:"Warm-up",limit_energy:"Limite di energia",limit_cost:"Limite di costo",limit_duration:"Limite di durata",boost_by:"Boost smart entro le {time}",done_of:"{done} di {target}",fault:"Guasto",vendor_code:"Codice del produttore: {code}.",fault_hint:"Se il guasto resta, contatta l'installatore.",offline_title:"Wallbox non raggiungibile",offline_text:"Non risulta connessa al cloud Growatt: dati e comandi tornano appena si riconnette.",rfid_title:"Modalit\xE0 RFID",rfid_text:"Avvio e arresto solo con la tessera. Gli avvii programmati funzionano comunque.",solar:"Fotovoltaico",wallbox:"Wallbox",grid:"Rete",battery:"Batteria",from_solar:"dal fotovoltaico {value}",from_battery:"dalla batteria {value}",from_grid:"dalla rete {value}",surplus:"Surplus disponibile: {value}.",battery_charging:"La batteria di casa sta assorbendo {value}: finch\xE9 si carica, alla wallbox arriva solo quello che avanza.",battery_charging_soc:"La batteria di casa ({soc}) sta assorbendo {value}: finch\xE9 si carica, alla wallbox arriva solo quello che avanza.",power:"Potenza di ricarica",editor_device_id:"Wallbox",editor_name:"Nome",editor_flow:"Flusso di energia",editor_solar_power:"Produzione fotovoltaica",editor_home_power:"Consumo della casa",editor_grid_import_power:"Prelievo dalla rete",editor_grid_export_power:"Immissione in rete",editor_battery_power:"Potenza della batteria di casa",editor_battery_charging_positive:"La potenza della batteria \xE8 positiva quando si carica",editor_battery_soc:"Carica della batteria di casa",editor_home_includes_wallbox:"Il consumo della casa include la wallbox",editor_content:"Contenuto",editor_show_session:"Sessione",editor_show_progress:"Avanzamento",editor_show_controls:"Comandi",editor_show_last_session:"Ultima ricarica",helper_solar_power:"Sensori di potenza dell'inverter, per mostrare da dove arriva l'energia della wallbox.",helper_home_power:"Facoltativo: serve a calcolare il surplus fotovoltaico.",helper_grid_export_power:"Consigliato in PV Linkage: il surplus diventa la potenza immessa in rete, lo stesso valore che la wallbox legge dal contatore.",helper_battery_power:"Facoltativo: mostra la batteria di casa, che quando si carica prende il surplus per prima.",helper_battery_charging_positive:"Attivo se il sensore \xE8 positivo mentre si carica e negativo mentre si scarica.",helper_home_includes_wallbox:"Attivo se la wallbox \xE8 a valle del sensore dei consumi della casa.",helper_show_session:"Energia, durata e costo mentre una sessione \xE8 aperta.",helper_show_progress:"Quanto manca al limite Fast o all'energia del Boost smart.",helper_show_controls:"Avvio, arresto, sblocco e modalit\xE0 di ricarica.",helper_show_last_session:"Quando nessuna sessione \xE8 aperta."},G2={en:Y,it:I2};function U2(M){return(M?.locale?.language||M?.language||document.documentElement.lang||navigator.language||"en").split("-")[0]}function O(M,C,H={}){let V=(G2[U2(M)]??Y)[C]??Y[C];for(let[L,r]of Object.entries(H))V=V.replace(`{${L}}`,r);return V}function c1(M){return M in Y}var Q2=Promise.race([customElements.whenDefined("home-assistant"),customElements.whenDefined("hc-main"),new Promise(M=>setTimeout(M,3e4))]);function C1(M,C){Q2.then(()=>{customElements.get(M)||customElements.define(M,C)})}var S2={home_includes_wallbox:!0,battery_charging_positive:!1,show_session:!0,show_progress:!0,show_controls:!0,show_last_session:!0},z2=["name","solar_power","home_power","grid_import_power","grid_export_power","battery_power","battery_soc"];async function K2(){if(customElements.get("ha-form"))return;await(await(await window.loadCardHelpers?.())?.createCardElement({type:"entities",entities:[]}))?.constructor?.getConfigElement?.()}var H1=class extends c{constructor(){super(...arguments);this._label=H=>{let V=`editor_${H.name}`;return c1(V)?O(this.hass,V):H.name};this._helper=H=>{let V=`helper_${H.name}`;return c1(V)?O(this.hass,V):void 0}}setConfig(H){this._config=H}connectedCallback(){super.connectedCallback(),K2().then(()=>customElements.whenDefined("ha-form")).then(()=>this.requestUpdate())}render(){return!this.hass||!this._config?d:p`
      <ha-form
        .hass=${this.hass}
        .data=${{...S2,...this._config}}
        .schema=${this._schema()}
        .computeLabel=${this._label}
        .computeHelper=${this._helper}
        @value-changed=${this._valueChanged}
      ></ha-form>
    `}_schema(){let H={entity:{filter:{domain:"sensor",device_class:"power"}}};return[{name:"device_id",required:!0,selector:{device:{filter:{integration:J}}}},{name:"name",selector:{text:{}}},{name:"flow",type:"expandable",flatten:!0,iconPath:i2,title:O(this.hass,"editor_flow"),schema:[{name:"solar_power",selector:H},{name:"home_power",selector:H},{name:"grid_import_power",selector:H},{name:"grid_export_power",selector:H},{name:"battery_power",selector:H},{name:"battery_charging_positive",selector:{boolean:{}}},{name:"battery_soc",selector:{entity:{filter:{domain:"sensor",device_class:"battery"}}}},{name:"home_includes_wallbox",selector:{boolean:{}}}]},{name:"content",type:"expandable",flatten:!0,iconPath:e2,title:O(this.hass,"editor_content"),schema:[{name:"show_session",selector:{boolean:{}}},{name:"show_progress",selector:{boolean:{}}},{name:"show_controls",selector:{boolean:{}}},{name:"show_last_session",selector:{boolean:{}}}]}]}_valueChanged(H){let V={...H.detail.value};for(let[L,r]of Object.entries(S2))V[L]===r&&delete V[L];for(let L of z2)V[L]||delete V[L];this.dispatchEvent(new CustomEvent("config-changed",{detail:{config:V},bubbles:!0,composed:!0}))}};H1.properties={hass:{attribute:!1},_config:{state:!0}};C1("thor-wallbox-card-editor",H1);function s2(M){let C=Math.max(0,M.battery??0),H=Math.max(0,-(M.battery??0)),V;M.home!==void 0?V=Math.max(0,M.home-(M.homeIncludesWallbox?M.wallbox:0)):M.solar!==void 0&&M.gridImport!==void 0&&M.gridExport!==void 0&&(V=Math.max(0,M.solar+M.gridImport+C-M.gridExport-H-M.wallbox));let L;M.gridExport!==void 0?L=Math.max(0,M.gridExport-(M.gridImport??0)):M.solar!==void 0&&V!==void 0&&(L=Math.max(0,M.solar-V-H));let r=0,e=0,t=0;if(M.charging){let A=Math.max(0,(M.solar??0)-H-(M.gridExport??0)),a=V??0,o=Math.min(a,A);a-=o,r=Math.min(M.wallbox,A-o);let m=Math.min(a,C);e=Math.min(M.wallbox-r,C-m),t=Math.max(0,M.wallbox-r-e),M.gridImport!==void 0&&(t=Math.min(t,M.gridImport))}let i=Math.min(H,Math.max(0,(M.solar??0)-(M.gridExport??0)));return{fromSolar:r,fromBattery:e,fromGrid:t,surplus:L,batteryCharging:H,batteryDischarging:C,batteryFromSolar:i}}function q2(M){switch(M.locale?.number_format){case"comma_decimal":return"en-US";case"decimal_comma":return"de";case"space_comma":return"fr";case"system":return;default:return M.locale?.language||M.language}}function x(M,C,H){return new Intl.NumberFormat(q2(M),{minimumFractionDigits:H,maximumFractionDigits:H,useGrouping:M.locale?.number_format!=="none"}).format(C)}function s(M,C){return`${x(M,C/1e3,1)} kW`}function h1(M){let C=Math.round(M),H=Math.floor(C/60),V=C%60;return H?V?`${H} h ${V} min`:`${H} h`:`${V} min`}function V1(M){let C=/^(\d{2}):(\d{2})/.exec(M??"");return C?`${C[1]}:${C[2]}`:void 0}function u2(M,C){let H=M.locale?.language||M.language;return C.toDateString()===new Date().toDateString()?new Intl.DateTimeFormat(H,{hour:"2-digit",minute:"2-digit"}).format(C):new Intl.DateTimeFormat(H,{day:"numeric",month:"short"}).format(C)}function B(M){if(!M)return;let C=Number(M.state);if(!(M.state===""||!Number.isFinite(C)))switch(M.attributes.unit_of_measurement){case"kW":return C*1e3;case"MW":return C*1e6;default:return C}}function S(M){if(!M||M.state==="")return;let C=Number(M.state);return Number.isFinite(C)?C:void 0}var c2=r1`
  :host {
    --tile-color: var(--state-inactive-color, #9e9e9e);
  }
  ha-card {
    height: 100%;
    overflow: hidden;
  }
  svg {
    display: block;
    flex: none;
    fill: currentColor;
  }
  .message {
    padding: 16px;
    color: var(--secondary-text-color);
  }

  .tile {
    display: flex;
    align-items: center;
    gap: 10px;
    min-height: 64px;
    padding: 8px 16px 0;
    box-sizing: border-box;
    cursor: pointer;
    outline: none;
    border-radius: var(--ha-card-border-radius, 12px);
  }
  .tile:focus-visible {
    box-shadow: inset 0 0 0 2px var(--tile-color);
  }
  .tile-icon {
    position: relative;
    flex: none;
    width: 36px;
    height: 36px;
  }
  .tile-icon .shape {
    position: relative;
    width: 36px;
    height: 36px;
    border-radius: 18px;
    overflow: hidden;
    display: flex;
    align-items: center;
    justify-content: center;
    color: var(--tile-color);
  }
  .tile-icon .shape::before {
    content: "";
    position: absolute;
    inset: 0;
    background: var(--tile-color);
    opacity: 0.2;
  }
  .tile-icon .shape svg {
    position: relative;
  }
  .tile-badge {
    position: absolute;
    top: -3px;
    right: -3px;
    width: 16px;
    height: 16px;
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: var(--mode-color, var(--primary-color));
    color: var(--white-color, #fff);
  }
  .tile-info {
    flex: 1;
    min-width: 0;
    display: flex;
    flex-direction: column;
    justify-content: center;
  }
  .primary,
  .secondary {
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    color: var(--primary-text-color);
  }
  .primary {
    font-size: var(--ha-font-size-m, 14px);
    font-weight: var(--ha-font-weight-medium, 500);
    line-height: var(--ha-line-height-normal, 1.6);
    letter-spacing: 0.1px;
  }
  .secondary {
    font-size: var(--ha-font-size-s, 12px);
    line-height: var(--ha-line-height-condensed, 1.2);
    letter-spacing: 0.4px;
  }

  .value {
    display: flex;
    align-items: baseline;
    gap: 4px;
    padding: 0 16px 16px;
    line-height: var(--ha-line-height-condensed, 1.2);
  }
  .value .number {
    font-size: var(--ha-font-size-3xl, 28px);
  }
  .value .unit {
    font-size: var(--ha-font-size-l, 16px);
    color: var(--secondary-text-color);
  }

  .alert {
    position: relative;
    display: flex;
    margin: 0 16px 16px;
    padding: 12px;
    border-radius: var(--ha-border-radius-lg, 12px);
    overflow: hidden;
  }
  .alert::before {
    content: "";
    position: absolute;
    inset: 0;
    background: var(--alert-color);
    opacity: 0.12;
  }
  .alert svg {
    position: relative;
    color: var(--alert-color);
  }
  .alert .text {
    position: relative;
    margin-inline: 8px;
    line-height: normal;
    color: var(--primary-text-color);
  }
  .alert .title {
    margin-top: 2px;
    font-weight: var(--ha-font-weight-bold, 700);
  }

  .flow {
    position: relative;
    display: flex;
    flex-direction: column;
    gap: 8px;
    padding: 0 16px 16px;
  }
  .flow .row {
    display: flex;
    align-items: flex-start;
    justify-content: center;
  }
  .node {
    flex: none;
    width: 80px;
    display: flex;
    flex-direction: column;
    align-items: center;
  }
  .node .label {
    height: 20px;
    max-width: 80px;
    font-size: var(--ha-font-size-s, 12px);
    color: var(--secondary-text-color);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  .node .circle {
    width: 80px;
    height: 80px;
    box-sizing: border-box;
    border: 2px solid var(--node-color);
    border-radius: 50%;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 2px;
    font-size: var(--ha-font-size-s, 12px);
    line-height: 12px;
    text-align: center;
    color: var(--primary-text-color);
  }
  .node.solar {
    --node-color: var(--energy-solar-color, #ff9800);
  }
  .node.grid {
    --node-color: var(--energy-grid-consumption-color, #488fc2);
  }
  .node.wallbox {
    --node-color: var(--tile-color);
  }
  /* Centred on the circles, below their 20px label. */
  .line {
    flex: 1;
    max-width: 120px;
    display: flex;
    align-items: center;
    height: 6px;
    margin-top: 57px;
    color: var(--disabled-color, #bdbdbd);
    opacity: 0.5;
  }
  .line.active {
    opacity: 1;
  }
  .line.solar.active {
    color: var(--energy-solar-color, #ff9800);
  }
  .line.grid.active {
    color: var(--energy-grid-consumption-color, #488fc2);
  }
  .line .track {
    position: relative;
    flex: 1;
    height: 1px;
    background: currentColor;
  }
  /* Runs towards the wallbox, faster as more power flows. */
  .line .dot {
    position: absolute;
    top: -2px;
    left: 0;
    width: 5px;
    height: 5px;
    border-radius: 50%;
    background: currentColor;
    animation: flow var(--flow-duration, 3s) linear infinite;
  }
  .line.reverse .dot {
    animation-direction: reverse;
  }
  @keyframes flow {
    from {
      left: 0;
    }
    to {
      left: calc(100% - 5px);
    }
  }
  .node.spacer,
  .line.spacer {
    visibility: hidden;
  }
  .circle .import,
  .circle .export,
  .circle .charging,
  .circle .discharging {
    display: flex;
    align-items: center;
    gap: 2px;
  }
  .circle .import svg {
    color: var(--energy-grid-consumption-color, #488fc2);
  }
  .circle .export svg {
    color: var(--energy-grid-return-color, #8353d1);
  }
  .circle .charging svg {
    color: var(--energy-battery-in-color, #f06292);
  }
  .circle .discharging svg {
    color: var(--energy-battery-out-color, #4db6ac);
  }

  /* The home battery below the wallbox, its label underneath. */
  .node.battery {
    --node-color: var(--energy-battery-out-color, #4db6ac);
    align-self: center;
    margin-top: 20px;
  }
  .node.battery .label {
    margin-top: 4px;
  }
  /* The battery's links, drawn over the flow once the circles are laid out. */
  .links {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    overflow: visible;
    pointer-events: none;
  }
  .link {
    color: var(--disabled-color, #bdbdbd);
    opacity: 0.5;
  }
  .link path {
    fill: none;
    stroke: currentColor;
    stroke-width: 1;
  }
  .link circle {
    fill: currentColor;
  }
  .link.active {
    opacity: 1;
  }
  .link.battery-out.active {
    color: var(--energy-battery-out-color, #4db6ac);
  }
  .link.battery-in.active {
    color: var(--energy-battery-in-color, #f06292);
  }

  @media (prefers-reduced-motion: reduce) {
    .line .dot {
      animation: none;
      left: calc(50% - 2.5px);
    }
  }
  .flow .note,
  .note {
    margin: 0;
    font-size: var(--ha-font-size-s, 12px);
    line-height: 1.4;
    color: var(--secondary-text-color);
  }

  .badges {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    padding: 0 16px 16px;
  }
  .badge {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    height: 36px;
    min-width: 36px;
    box-sizing: border-box;
    padding: 0 12px;
    border-width: var(--ha-card-border-width, 1px);
    border-style: solid;
    border-color: var(--ha-card-border-color, var(--divider-color, #e0e0e0));
    border-radius: 18px;
    background: var(--ha-card-background, var(--card-background-color, #fff));
  }
  .badge svg {
    margin-inline-start: -4px;
    color: var(--badge-color, var(--secondary-text-color));
  }
  .badge .info {
    display: flex;
    flex-direction: column;
    align-items: flex-start;
  }
  .badge .label {
    font-size: var(--ha-font-size-xs, 10px);
    font-weight: var(--ha-font-weight-medium, 500);
    line-height: 10px;
    letter-spacing: 0.1px;
    color: var(--secondary-text-color);
  }
  .badge .content {
    font-size: var(--ha-font-size-s, 12px);
    font-weight: var(--ha-font-weight-medium, 500);
    line-height: var(--ha-line-height-condensed, 1.2);
    letter-spacing: 0.1px;
    color: var(--primary-text-color);
  }

  .features {
    display: flex;
    flex-direction: column;
    gap: 12px;
    padding: 0 16px 16px;
  }
  .progress .caption {
    display: flex;
    justify-content: space-between;
    gap: 12px;
    padding: 0 4px 4px;
    font-size: var(--ha-font-size-s, 12px);
    line-height: var(--ha-line-height-condensed, 1.2);
    letter-spacing: 0.4px;
    color: var(--primary-text-color);
  }
  .progress .caption .pct {
    font-weight: var(--ha-font-weight-medium, 500);
  }
  .bar {
    display: flex;
    height: 42px;
    border-radius: var(--ha-card-features-border-radius, 12px);
    overflow: hidden;
  }
  .bar .done {
    background: var(--tile-color);
  }
  .bar .rest {
    flex: 1;
    background: var(--tile-color);
    opacity: 0.2;
  }
  .buttons {
    display: flex;
    gap: 12px;
  }
  .button {
    position: relative;
    overflow: hidden;
    z-index: 0;
    flex: 1 1 0;
    min-width: 0;
    height: 42px;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    padding: 0 8px;
    border: none;
    border-radius: var(--ha-card-features-border-radius, 12px);
    background: none;
    font-family: inherit;
    font-size: var(--ha-font-size-m, 14px);
    font-weight: var(--ha-font-weight-medium, 500);
    color: var(--primary-text-color);
    cursor: pointer;
    outline: none;
  }
  .button::before,
  .select::before {
    content: "";
    position: absolute;
    inset: 0;
    background: var(--disabled-color, #bdbdbd);
    opacity: 0.2;
    transition: opacity 180ms ease-in-out;
    pointer-events: none;
  }
  .button:hover:not(:disabled)::before,
  .select:not(.disabled):hover::before {
    opacity: 0.3;
  }
  .button:focus-visible,
  .select:focus-within {
    box-shadow: 0 0 0 2px var(--tile-color);
  }
  .button:disabled {
    cursor: not-allowed;
    color: var(--disabled-text-color, #bdbdbd);
  }
  .button svg,
  .button span {
    position: relative;
  }
  .button span {
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  .select {
    position: relative;
    overflow: hidden;
    height: 42px;
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 6px 10px;
    box-sizing: border-box;
    border-radius: var(--ha-card-features-border-radius, 12px);
    letter-spacing: 0.25px;
    color: var(--primary-text-color);
  }
  .select.disabled {
    color: var(--disabled-color, #bdbdbd);
  }
  .select svg,
  .select .content {
    position: relative;
  }
  .select .content {
    flex: 1;
    min-width: 0;
    display: flex;
    flex-direction: column;
    line-height: var(--ha-line-height-condensed, 1.2);
  }
  .select .label {
    font-size: var(--ha-font-size-s, 12px);
    letter-spacing: 0.4px;
  }
  .select .current {
    font-size: var(--ha-font-size-m, 14px);
  }
  .select select {
    position: absolute;
    inset: 0;
    width: 100%;
    height: 100%;
    margin: 0;
    opacity: 0;
    cursor: pointer;
    font-size: 16px;
  }
  .select select:disabled {
    cursor: not-allowed;
  }
  .features .note {
    padding: 0 4px;
  }
`;var j2={charging:"var(--success-color, #43a047)",suspended_ev:"var(--warning-color, #ffa600)",suspended_evse:"var(--warning-color, #ffa600)",preparing:"var(--info-color, #039be5)",finishing:"var(--teal-color, #009688)",reserved:"var(--purple-color, #926bc7)",faulted:"var(--error-color, #db4437)",available:"var(--state-inactive-color, #9e9e9e)"},X2="var(--state-unavailable-color, #bdbdbd)",f2="var(--energy-solar-color, #ff9800)",J2="var(--energy-grid-consumption-color, #488fc2)",k2="var(--deep-purple-color, #6e41ab)",O1={fast:{icon:r2,color:"var(--primary-color, #009ac7)"},pv_linkage:{icon:X,color:f2},off_peak:{icon:s1,color:k2}},Y2=["","unknown","unavailable","NoError"],u=50,h2=6,C5=.75,H5=7400;function O2(M){let C=Math.min(1,Math.max(0,(M-u)/(H5-u))),H=h2-C*(h2-C5);return Math.round(H*4)/4}var V5=24;function Z(M,C=24){return p`<svg viewBox="0 0 24 24" width=${C} height=${C} aria-hidden="true">
    <path d=${M}></path>
  </svg>`}function I(M){return M!==void 0&&!Y2.includes(M)}var G=class extends c{constructor(){super(...arguments);this._ids=new Map;this._modeChanged=H=>{let V=H.target,L=this._id("select.charge_mode"),r=this._state("select.charge_mode")??"",e=V.value;V.value=r,L&&e!==r&&this._call("select","select_option",L,{option:e})};this._moreInfo=()=>{let H=this._id("sensor.status");H&&this.dispatchEvent(new CustomEvent("hass-more-info",{detail:{entityId:H},bubbles:!0,composed:!0}))};this._tileKeydown=H=>{(H.key==="Enter"||H.key===" ")&&(H.preventDefault(),this._moreInfo())}}static getConfigElement(){return document.createElement("thor-wallbox-card-editor")}static getStubConfig(H){let[V]=x2(H);return V?{device_id:V}:{}}setConfig(H){if(!H)throw new Error("Invalid configuration");this._config={...H}}getCardSize(){return 7}getGridOptions(){return{columns:12,min_columns:6}}connectedCallback(){super.connectedCallback(),this.hasUpdated&&this.requestUpdate()}disconnectedCallback(){super.disconnectedCallback(),this._resizeObserver?.disconnect(),this._observedFlow=void 0}updated(H){super.updated(H);let V=this.renderRoot.querySelector(".flow")??void 0;V!==this._observedFlow&&(this._resizeObserver??=new ResizeObserver(()=>this._measureLinks()),this._resizeObserver.disconnect(),V&&this._resizeObserver.observe(V),this._observedFlow=V),this._measureLinks()}shouldUpdate(H){if(H.has("_config")||!this.hass)return!0;let V=H.get("hass");return!V||V.entities!==this.hass.entities||V.locale!==this.hass.locale||V.language!==this.hass.language||V.themes!==this.hass.themes?!0:this._watched().some(L=>V.states[L]!==this.hass.states[L])}_watched(){let H=this._config,V=[...this._entityIds().values()];for(let L of[H?.solar_power,H?.home_power,H?.grid_import_power,H?.grid_export_power,H?.battery_power,H?.battery_soc])L&&V.push(L);return V}_entityIds(){let H=this.hass,V=this._config?.device_id;return(this._idsSource?.entities!==H.entities||this._idsSource?.device!==V)&&(this._ids=Z2(H,V),this._idsSource={entities:H.entities,device:V}),this._ids}_id(H){return this._entityIds().get(H)}_obj(H){let V=this._id(H);return V?this.hass.states[V]:void 0}_state(H){return this._obj(H)?.state}_available(H){let V=this._state(H);return V!==void 0&&V!=="unavailable"}_configured(H){return H?this.hass.states[H]:void 0}_t(H,V){return O(this.hass,H,V)}render(){if(!this._config||!this.hass)return d;if(!this._config.device_id)return this._renderMessage(this._t("no_device"));let H=this._obj("sensor.status");if(!H)return this._renderMessage(this._t("device_not_found"));let V=H.state,L=this._state("select.charge_mode"),r=V==="unavailable",e=l2.includes(V),t=B(this._obj("sensor.power")),i=[`--tile-color: ${j2[V]??X2}`,`--mode-color: ${L&&O1[L]?.color||"var(--primary-color)"}`].join("; ");return p`
      <ha-card style=${i}>
        ${this._renderTile(H,V,L)}
        ${r||t===void 0?d:p`<div class="value" aria-label=${this._t("power")}>
              <span class="number">${x(this.hass,t/1e3,1)}</span>
              <span class="unit">kW</span>
            </div>`}
        ${this._alerts(V).map(A=>this._renderAlert(A))}
        ${r?d:this._renderFlow(V,L,t??0)}
        ${this._renderBadges(V,L,e)}
        ${this._renderFeatures(V,e)}
      </ha-card>
    `}_renderMessage(H){return p`<ha-card><div class="message">${H}</div></ha-card>`}_renderTile(H,V,L){let r=this.hass,e=r.devices?.[this._config.device_id],t=this._config.name||e?.name_by_user||e?.name||"THOR",i=[r.formatEntityState(H),this._detail(V,L)].filter(Boolean).join(" \xB7 "),A=L?O1[L]?.icon:void 0;return p`
      <div
        class="tile"
        role="button"
        tabindex="0"
        @click=${this._moreInfo}
        @keydown=${this._tileKeydown}
      >
        <div class="tile-icon">
          <div class="shape">${Z(j)}</div>
          ${A?p`<div class="tile-badge">${Z(A,12)}</div>`:d}
        </div>
        <div class="tile-info">
          <span class="primary">${t}</span>
          <span class="secondary">${i}</span>
        </div>
      </div>
    `}_detail(H,V){let L=this.hass;switch(H){case"charging":{let r=S(this._obj("sensor.current")),e=S(this._obj("sensor.voltage"));return[r===void 0?"":`${x(L,r,1)} A`,e===void 0?"":`${x(L,e,0)} V`].filter(Boolean).join(" \xB7 ")}case"available":return this._t("plug_in");case"preparing":return this._t("car_connected");case"suspended_evse":return V==="pv_linkage"?this._t("waiting_surplus"):V==="off_peak"?this._t("waiting_slot"):"";case"reserved":return this._reservation()??"";case"faulted":{let r=this._state("sensor.error_code");return I(r)?r:""}default:return""}}_reservation(){let H=this.hass,V=this._obj("sensor.next_reservation");if(!V||!I(V.state))return;let L=new Date(V.state);if(V.attributes.every_day&&!Number.isNaN(L.getTime())){let r=new Intl.DateTimeFormat(H.locale?.language||H.language,{hour:"2-digit",minute:"2-digit"}).format(L);return this._t("every_day",{time:r})}return H.formatEntityState(V)}_alerts(H){let V=[];if(H==="unavailable"&&V.push({icon:V2,color:"var(--warning-color, #ffa600)",title:this._t("offline_title"),text:this._t("offline_text")}),H==="faulted"){let L=this._state("sensor.error_code"),r=this._state("sensor.vendor_error_code");V.push({icon:U1,color:"var(--error-color, #db4437)",title:I(L)?`${this._t("fault")}: ${L}`:this._t("fault"),text:[I(r)?this._t("vendor_code",{code:r}):"",this._t("fault_hint")].filter(Boolean).join(" ")})}return this._state("select.authorization_mode")==="rfid"&&["available","preparing"].includes(H)&&V.push({icon:L2,color:"var(--info-color, #039be5)",title:this._t("rfid_title"),text:this._t("rfid_text")}),V}_renderAlert(H){return p`
      <div class="alert" style=${`--alert-color: ${H.color}`}>
        ${Z(H.icon)}
        <div class="text">
          <div class="title">${H.title}</div>
          <div>${H.text}</div>
        </div>
      </div>
    `}_renderFlow(H,V,L){let r=this._config,e=!!r.solar_power,t=!!(r.grid_import_power||r.grid_export_power),i=!!r.battery_power;if(!e&&!t&&!i)return d;let A=this.hass,a=B(this._configured(r.solar_power)),o=B(this._configured(r.grid_import_power)),m=B(this._configured(r.grid_export_power)),n=B(this._configured(r.battery_power)),v=H==="charging"&&L>u,l=s2({wallbox:L,charging:v,solar:a,gridImport:o,gridExport:m,home:B(this._configured(r.home_power)),homeIncludesWallbox:r.home_includes_wallbox!==!1,battery:n===void 0?void 0:r.battery_charging_positive?-n:n}),L1=S(this._configured(r.battery_soc)),T=[];if(v){let F=[l.fromSolar>u?this._t("from_solar",{value:s(A,l.fromSolar)}):"",l.fromBattery>u?this._t("from_battery",{value:s(A,l.fromBattery)}):"",l.fromGrid>u?this._t("from_grid",{value:s(A,l.fromGrid)}):""].filter(Boolean);if(F.length){let g1=F.join(", ");T.push(`${g1.charAt(0).toUpperCase()}${g1.slice(1)}.`)}}else V==="pv_linkage"&&(l.surplus!==void 0&&T.push(this._t("surplus",{value:s(A,l.surplus)})),l.batteryFromSolar>u&&T.push(L1===void 0?this._t("battery_charging",{value:s(A,l.batteryCharging)}):this._t("battery_charging_soc",{value:s(A,l.batteryCharging),soc:`${x(A,L1,0)} %`})));let U=F=>F===void 0?"-":s(A,F),b2=p`<div class="node spacer"></div><div class="line spacer"></div>`;return p`
      <div class="flow">
        <div class="row">
          ${e?p`
                <div class="node solar">
                  <span class="label">${this._t("solar")}</span>
                  <div class="circle">${Z(X)}<span>${U(a)}</span></div>
                </div>
                ${this._renderLine("solar",l.fromSolar,!1)}
              `:b2}
          <div class="node wallbox">
            <span class="label">${this._t("wallbox")}</span>
            <div class="circle">${Z(j)}<span>${s(A,L)}</span></div>
          </div>
          ${t?p`
                ${this._renderLine("grid",l.fromGrid,!0)}
                <div class="node grid">
                  <span class="label">${this._t("grid")}</span>
                  <div class="circle">
                    ${Z(S1)}
                    ${r.grid_export_power?p`<span class="import">${Z(z1,12)}${U(o)}</span>
                          <span class="export">${Z(K1,12)}${U(m)}</span>`:p`<span>${U(o)}</span>`}
                  </div>
                </div>
              `:p`<div class="line spacer"></div><div class="node spacer"></div>`}
        </div>
        ${i?this._renderBattery(l,L1):d}
        ${T.length?p`<p class="note">${T.join(" ")}</p>`:d}
        ${i&&this._links?this._renderLinks(this._links,l):d}
      </div>
    `}_renderBattery(H,V){let L=this.hass,r=j1;V!==void 0&&(V<10?r=Y1:V<=32.5?r=X1:V<=72.5&&(r=J1));let e=p`<span>${s(L,0)}</span>`;return H.batteryDischarging>u?e=p`<span class="discharging">${Z(q1,12)}${s(L,H.batteryDischarging)}</span>`:H.batteryCharging>u&&(e=p`<span class="charging">${Z(Q1,12)}${s(L,H.batteryCharging)}</span>`),p`
      <div class="node battery">
        <div class="circle">
          ${Z(r)}
          ${V===void 0?d:p`<span>${x(L,V,0)} %</span>`}
          ${e}
        </div>
        <span class="label">${this._t("battery")}</span>
      </div>
    `}_measureLinks(){let H=this.renderRoot.querySelector(".flow"),V=t=>H?.querySelector(`.node.${t} .circle`)??void 0,L=V("battery"),r=V("wallbox"),e;if(L&&r&&L.offsetWidth){let t=m=>Math.round(m.offsetLeft+m.offsetWidth/2)+.5,i=m=>m.offsetTop+m.offsetHeight,A=Math.round(L.offsetTop+L.offsetHeight/2)+.5,a=V("solar"),o;if(a){let m=t(a),n=i(a),v=Math.max(0,Math.min(V5,A-n,L.offsetLeft-m));o=`M${m} ${n}V${A-v}A${v} ${v} 0 0 0 ${m+v} ${A}H${L.offsetLeft}`}e={wallbox:`M${t(L)} ${L.offsetTop}V${i(r)}`,solar:o}}JSON.stringify(e)!==JSON.stringify(this._links)&&(this._links=e)}_renderLinks(H,V){let L=window.matchMedia?.("(prefers-reduced-motion: reduce)").matches,r=(e,t,i)=>{if(!e)return d;let A=i>u,a=L?"0.5;0.5":"0;1";return l1`
        <g class="link ${t} ${A?"active":""}">
          <path d=${e}></path>
          ${A?l1`<circle r="2.5">
                <animateMotion
                  path=${e}
                  dur="${O2(i)}s"
                  repeatCount="indefinite"
                  calcMode="linear"
                  keyPoints=${a}
                  keyTimes="0;1"
                ></animateMotion>
              </circle>`:d}
        </g>
      `};return p`
      <svg class="links" aria-hidden="true">
        ${r(H.wallbox,"battery-out",V.fromBattery)}
        ${r(H.solar,"battery-in",V.batteryFromSolar)}
      </svg>
    `}_renderLine(H,V,L){let r=V>u;return p`
      <div
        class="line ${H} ${r?"active":""} ${L?"reverse":""}"
        style=${r?`--flow-duration: ${O2(V)}s`:""}
      >
        <div class="track">${r?p`<span class="dot"></span>`:d}</div>
      </div>
    `}_badges(H,V,L){let r=this.hass,e=this._config,t=[];if(L&&e.show_session!==!1){let a=S(this._obj("sensor.session_energy")),o=S(this._obj("sensor.session_duration")),m=this._obj("sensor.session_cost");a!==void 0&&t.push({icon:o2,label:this._t("energy"),text:`${x(r,a,2)} kWh`}),o!==void 0&&t.push({icon:v2,label:this._t("duration"),text:h1(o)}),m&&S(m)!==void 0&&t.push({icon:M2,label:this._t("cost"),text:r.formatEntityState(m)})}if(!L&&e.show_last_session!==!1){let a=new Date(this._state("sensor.last_session")??""),o=S(this._obj("sensor.last_session_energy"));Number.isNaN(a.getTime())||t.push({icon:t2,label:this._t("last_session"),text:[u2(r,a),o===void 0?"":`${x(r,o,2)} kWh`].filter(Boolean).join(" \xB7 ")})}let i=this._state("binary_sensor.cable_lock");if(i==="off"?t.push({icon:A2,text:this._t("cable_locked")}):i==="on"&&t.push({icon:Z1,text:this._t("cable_unlocked")}),V==="pv_linkage"){let a=this._state("switch.import_grid"),o=S(this._obj("number.import_grid_power"));a==="on"?t.push({icon:S1,color:J2,text:o===void 0?this._t("grid_import"):this._t("grid_import_power",{power:`${x(r,o,1)} kW`})}):a==="off"&&t.push({icon:X,color:f2,text:this._t("surplus_only")})}if(this._state("switch.boost")==="on"){let a=this._obj("select.boost_type");t.push({icon:p2,color:"var(--primary-color, #009ac7)",text:a&&I(a.state)?this._t("boost",{type:r.formatEntityState(a)}):"Boost"})}if(V==="off_peak"){let a=[1,2,3].map(o=>[V1(this._state(`time.off_peak_${o}_from`)),V1(this._state(`time.off_peak_${o}_to`))]).filter(([o,m])=>o&&m&&o!==m).map(([o,m])=>`${o}-${m}`);a.length&&t.push({icon:s1,color:k2,label:this._t("slots"),text:a.join(", ")})}let A=H==="reserved"?void 0:this._reservation();return A&&t.push({icon:C2,color:"var(--purple-color, #926bc7)",label:this._t("scheduled_start"),text:A}),H==="suspended_ev"&&this._state("switch.warm_up")==="on"&&t.push({icon:n2,color:"var(--deep-orange-color, #ff6f22)",text:this._t("warm_up")}),t}_renderBadges(H,V,L){let r=this._badges(H,V,L);return r.length?p`
      <div class="badges">
        ${r.map(e=>p`
            <div class="badge" style=${e.color?`--badge-color: ${e.color}`:""}>
              ${Z(e.icon,18)}
              <div class="info">
                ${e.label?p`<span class="label">${e.label}</span>`:d}
                <span class="content">${e.text}</span>
              </div>
            </div>
          `)}
      </div>
    `:d}_renderFeatures(H,V){let L=this._config,r=L.show_progress===!1?d:this._renderProgress(),e=L.show_controls===!1?d:this._renderControls(H,V);return r===d&&e===d?d:p`<div class="features">${r}${e}</div>`}_renderProgress(){let H=this.hass,V=S(this._obj("sensor.session_progress"));if(V===void 0)return d;let L=this._progressCaption(),r=Math.min(100,Math.max(0,V));return p`
      <div class="progress">
        <div class="caption">
          <span>${L}</span>
          <span class="pct">${x(H,V,0)} %</span>
        </div>
        <div
          class="bar"
          role="progressbar"
          aria-label=${L}
          aria-valuenow=${r}
          aria-valuemin="0"
          aria-valuemax="100"
        >
          <div class="done" style=${`width: ${r}%`}></div>
          <div class="rest"></div>
        </div>
      </div>
    `}_progressCaption(){let H=this.hass,V=this._obj("sensor.session_limit"),L=V?.state;if(L==="energy"||L==="cost"||L==="duration"){let A=this._t(`limit_${L}`),a=V?.attributes.value,o=this._obj(`sensor.session_${L}`),m=S(o);if(m===void 0||typeof a!="number")return A;let n=v=>L==="duration"?h1(v):L==="energy"?`${x(H,v,1)} kWh`:`${x(H,v,2)} ${o?.attributes.unit_of_measurement??""}`.trim();return`${A} \xB7 ${this._t("done_of",{done:n(m),target:n(a)})}`}let r=V1(this._state("time.boost_departure")),e=r?this._t("boost_by",{time:r}):"Boost",t=S(this._obj("sensor.session_energy")),i=S(this._obj("number.boost_energy"));return t===void 0||i===void 0?e:`${e} \xB7 ${this._t("done_of",{done:`${x(H,t,1)} kWh`,target:`${x(H,i,1)} kWh`})}`}_renderControls(H,V){let L=H==="unavailable",r=this._state("select.authorization_mode")==="rfid",e=this._id("switch.charging"),t=this._id("button.cancel_reservation"),i=this._id("button.unlock"),A=[];if(t&&this._available("button.cancel_reservation"))A.push({icon:H2,label:this._t("cancel"),disabled:L,action:()=>this._call("button","press",t)});else if(e){let o=!L&&this._available("switch.charging");u1.includes(H)?A.push({icon:m2,label:this._t("stop"),disabled:r||!o,action:()=>this._call("switch","turn_off",e)}):A.push({icon:d2,label:this._t("start"),disabled:r||!o||!["available","preparing"].includes(H),action:()=>this._call("switch","turn_on",e)})}i&&A.push({icon:Z1,label:this._t("unlock"),disabled:L||!this._available("button.unlock"),action:()=>this._call("button","press",i)});let a=this._obj("select.charge_mode");return!A.length&&!a?d:p`
      ${A.length?p`<div class="buttons">
            ${A.map(o=>p`
                <button class="button" type="button" ?disabled=${o.disabled} @click=${o.action}>
                  ${Z(o.icon,20)}
                  <span>${o.label}</span>
                </button>
              `)}
          </div>`:d}
      ${a?this._renderModeSelect(a,V||L):d}
      ${V?p`<p class="note">${this._t("locked_note")}</p>`:d}
    `}_renderModeSelect(H,V){let L=this.hass,r=H.state,e=H.attributes.options??[],t=V||r==="unavailable";return p`
      <div class="select ${t?"disabled":""}">
        ${Z(O1[r]?.icon??j,20)}
        <div class="content">
          <span class="label">${this._t("charge_mode")}</span>
          <span class="current">${L.formatEntityState(H)}</span>
        </div>
        ${Z(a2,20)}
        <select aria-label=${this._t("charge_mode")} ?disabled=${t} @change=${this._modeChanged}>
          ${e.map(i=>p`<option value=${i} ?selected=${i===r}>
                ${L.formatEntityState(H,i)}
              </option>`)}
        </select>
      </div>
    `}async _call(H,V,L,r={}){try{await this.hass.callService(H,V,{entity_id:L,...r})}catch(e){let t=e?.message??String(e);this.dispatchEvent(new CustomEvent("hass-notification",{detail:{message:t},bubbles:!0,composed:!0}))}}};G.styles=c2,G.properties={hass:{attribute:!1},_config:{state:!0},_links:{state:!0}};C1("thor-wallbox-card",G);var g2=window.customCards??=[];g2.some(M=>M.type==="thor-wallbox-card")||g2.push({type:"thor-wallbox-card",name:O(void 0,"card_name"),description:O(void 0,"card_description"),preview:!0,documentationURL:"https://github.com/fabioscarparo/ha-growatt-thor-cloud#wallbox-card-beta"});console.info("%c THOR-WALLBOX-CARD %c 0.8.1 ","color: #fff; background: #43a047","");
/*! Bundled license information:

@lit/reactive-element/css-tag.js:
  (**
   * @license
   * Copyright 2019 Google LLC
   * SPDX-License-Identifier: BSD-3-Clause
   *)

@lit/reactive-element/reactive-element.js:
lit-html/lit-html.js:
lit-element/lit-element.js:
  (**
   * @license
   * Copyright 2017 Google LLC
   * SPDX-License-Identifier: BSD-3-Clause
   *)

lit-html/is-server.js:
  (**
   * @license
   * Copyright 2022 Google LLC
   * SPDX-License-Identifier: BSD-3-Clause
   *)
*/
