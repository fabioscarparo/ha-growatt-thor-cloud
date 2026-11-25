var J=globalThis,C1=J.ShadowRoot&&(J.ShadyCSS===void 0||J.ShadyCSS.nativeShadow)&&"adoptedStyleSheets"in Document.prototype&&"replace"in CSSStyleSheet.prototype,i1=Symbol(),R1=new WeakMap,E=class{constructor(H,C,V){if(this._$cssResult$=!0,V!==i1)throw Error("CSSResult is not constructable. Use `unsafeCSS` or `css` instead.");this.cssText=H,this.t=C}get styleSheet(){let H=this.o,C=this.t;if(C1&&H===void 0){let V=C!==void 0&&C.length===1;V&&(H=R1.get(C)),H===void 0&&((this.o=H=new CSSStyleSheet).replaceSync(this.cssText),V&&R1.set(C,H))}return H}toString(){return this.cssText}},D1=L=>new E(typeof L=="string"?L:L+"",void 0,i1),$=(L,...H)=>{let C=L.length===1?L[0]:H.reduce((V,M,r)=>V+(e=>{if(e._$cssResult$===!0)return e.cssText;if(typeof e=="number")return e;throw Error("Value passed to 'css' function must be a 'css' function result: "+e+". Use 'unsafeCSS' to pass non-literal values, but take care to ensure page security.")})(M)+L[r+1],L[0]);return new E(C,L,i1)},E1=(L,H)=>{if(C1)L.adoptedStyleSheets=H.map(C=>C instanceof CSSStyleSheet?C:C.styleSheet);else for(let C of H){let V=document.createElement("style"),M=J.litNonce;M!==void 0&&V.setAttribute("nonce",M),V.textContent=C.cssText,L.appendChild(V)}},o1=C1?L=>L:L=>L instanceof CSSStyleSheet?(H=>{let C="";for(let V of H.cssRules)C+=V.cssText;return D1(C)})(L):L;var{is:H5,defineProperty:V5,getOwnPropertyDescriptor:L5,getOwnPropertyNames:M5,getOwnPropertySymbols:r5,getPrototypeOf:e5}=Object,H1=globalThis,$1=H1.trustedTypes,t5=$1?$1.emptyScript:"",i5=H1.reactiveElementPolyfillSupport,N=(L,H)=>L,a1={toAttribute(L,H){switch(H){case Boolean:L=L?t5:null;break;case Object:case Array:L=L==null?L:JSON.stringify(L)}return L},fromAttribute(L,H){let C=L;switch(H){case Boolean:C=L!==null;break;case Number:C=L===null?null:Number(L);break;case Object:case Array:try{C=JSON.parse(L)}catch{C=null}}return C}},W1=(L,H)=>!H5(L,H),N1={attribute:!0,type:String,converter:a1,reflect:!1,useDefault:!1,hasChanged:W1};Symbol.metadata??=Symbol("metadata"),H1.litPropertyMetadata??=new WeakMap;var O=class extends HTMLElement{static addInitializer(H){this._$Ei(),(this.l??=[]).push(H)}static get observedAttributes(){return this.finalize(),this._$Eh&&[...this._$Eh.keys()]}static createProperty(H,C=N1){if(C.state&&(C.attribute=!1),this._$Ei(),this.prototype.hasOwnProperty(H)&&((C=Object.create(C)).wrapped=!0),this.elementProperties.set(H,C),!C.noAccessor){let V=Symbol(),M=this.getPropertyDescriptor(H,V,C);M!==void 0&&V5(this.prototype,H,M)}}static getPropertyDescriptor(H,C,V){let{get:M,set:r}=L5(this.prototype,H)??{get(){return this[C]},set(e){this[C]=e}};return{get:M,set(e){let i=M?.call(this);r?.call(this,e),this.requestUpdate(H,i,V)},configurable:!0,enumerable:!0}}static getPropertyOptions(H){return this.elementProperties.get(H)??N1}static _$Ei(){if(this.hasOwnProperty(N("elementProperties")))return;let H=e5(this);H.finalize(),H.l!==void 0&&(this.l=[...H.l]),this.elementProperties=new Map(H.elementProperties)}static finalize(){if(this.hasOwnProperty(N("finalized")))return;if(this.finalized=!0,this._$Ei(),this.hasOwnProperty(N("properties"))){let C=this.properties,V=[...M5(C),...r5(C)];for(let M of V)this.createProperty(M,C[M])}let H=this[Symbol.metadata];if(H!==null){let C=litPropertyMetadata.get(H);if(C!==void 0)for(let[V,M]of C)this.elementProperties.set(V,M)}this._$Eh=new Map;for(let[C,V]of this.elementProperties){let M=this._$Eu(C,V);M!==void 0&&this._$Eh.set(M,C)}this.elementStyles=this.finalizeStyles(this.styles)}static finalizeStyles(H){let C=[];if(Array.isArray(H)){let V=new Set(H.flat(1/0).reverse());for(let M of V)C.unshift(o1(M))}else H!==void 0&&C.push(o1(H));return C}static _$Eu(H,C){let V=C.attribute;return V===!1?void 0:typeof V=="string"?V:typeof H=="string"?H.toLowerCase():void 0}constructor(){super(),this._$Ep=void 0,this.isUpdatePending=!1,this.hasUpdated=!1,this._$Em=null,this._$Ev()}_$Ev(){this._$ES=new Promise(H=>this.enableUpdating=H),this._$AL=new Map,this._$E_(),this.requestUpdate(),this.constructor.l?.forEach(H=>H(this))}addController(H){(this._$EO??=new Set).add(H),this.renderRoot!==void 0&&this.isConnected&&H.hostConnected?.()}removeController(H){this._$EO?.delete(H)}_$E_(){let H=new Map,C=this.constructor.elementProperties;for(let V of C.keys())this.hasOwnProperty(V)&&(H.set(V,this[V]),delete this[V]);H.size>0&&(this._$Ep=H)}createRenderRoot(){let H=this.shadowRoot??this.attachShadow(this.constructor.shadowRootOptions);return E1(H,this.constructor.elementStyles),H}connectedCallback(){this.renderRoot??=this.createRenderRoot(),this.enableUpdating(!0),this._$EO?.forEach(H=>H.hostConnected?.())}enableUpdating(H){}disconnectedCallback(){this._$EO?.forEach(H=>H.hostDisconnected?.())}attributeChangedCallback(H,C,V){this._$AK(H,V)}_$ET(H,C){let V=this.constructor.elementProperties.get(H),M=this.constructor._$Eu(H,V);if(M!==void 0&&V.reflect===!0){let r=(V.converter?.toAttribute!==void 0?V.converter:a1).toAttribute(C,V.type);this._$Em=H,r==null?this.removeAttribute(M):this.setAttribute(M,r),this._$Em=null}}_$AK(H,C){let V=this.constructor,M=V._$Eh.get(H);if(M!==void 0&&this._$Em!==M){let r=V.getPropertyOptions(M),e=typeof r.converter=="function"?{fromAttribute:r.converter}:r.converter?.fromAttribute!==void 0?r.converter:a1;this._$Em=M;let i=e.fromAttribute(C,r.type);this[M]=i??this._$Ej?.get(M)??i,this._$Em=null}}requestUpdate(H,C,V,M=!1,r){if(H!==void 0){let e=this.constructor;if(M===!1&&(r=this[H]),V??=e.getPropertyOptions(H),!((V.hasChanged??W1)(r,C)||V.useDefault&&V.reflect&&r===this._$Ej?.get(H)&&!this.hasAttribute(e._$Eu(H,V))))return;this.C(H,C,V)}this.isUpdatePending===!1&&(this._$ES=this._$EP())}C(H,C,{useDefault:V,reflect:M,wrapped:r},e){V&&!(this._$Ej??=new Map).has(H)&&(this._$Ej.set(H,e??C??this[H]),r!==!0||e!==void 0)||(this._$AL.has(H)||(this.hasUpdated||V||(C=void 0),this._$AL.set(H,C)),M===!0&&this._$Em!==H&&(this._$Eq??=new Set).add(H))}async _$EP(){this.isUpdatePending=!0;try{await this._$ES}catch(C){Promise.reject(C)}let H=this.scheduleUpdate();return H!=null&&await H,!this.isUpdatePending}scheduleUpdate(){return this.performUpdate()}performUpdate(){if(!this.isUpdatePending)return;if(!this.hasUpdated){if(this.renderRoot??=this.createRenderRoot(),this._$Ep){for(let[M,r]of this._$Ep)this[M]=r;this._$Ep=void 0}let V=this.constructor.elementProperties;if(V.size>0)for(let[M,r]of V){let{wrapped:e}=r,i=this[M];e!==!0||this._$AL.has(M)||i===void 0||this.C(M,void 0,r,i)}}let H=!1,C=this._$AL;try{H=this.shouldUpdate(C),H?(this.willUpdate(C),this._$EO?.forEach(V=>V.hostUpdate?.()),this.update(C)):this._$EM()}catch(V){throw H=!1,this._$EM(),V}H&&this._$AE(C)}willUpdate(H){}_$AE(H){this._$EO?.forEach(C=>C.hostUpdated?.()),this.hasUpdated||(this.hasUpdated=!0,this.firstUpdated(H)),this.updated(H)}_$EM(){this._$AL=new Map,this.isUpdatePending=!1}get updateComplete(){return this.getUpdateComplete()}getUpdateComplete(){return this._$ES}shouldUpdate(H){return!0}update(H){this._$Eq&&=this._$Eq.forEach(C=>this._$ET(C,this[C])),this._$EM()}updated(H){}firstUpdated(H){}};O.elementStyles=[],O.shadowRootOptions={mode:"open"},O[N("elementProperties")]=new Map,O[N("finalized")]=new Map,i5?.({ReactiveElement:O}),(H1.reactiveElementVersions??=[]).push("2.1.2");var v1=globalThis,I1=L=>L,V1=v1.trustedTypes,G1=V1?V1.createPolicy("lit-html",{createHTML:L=>L}):void 0,q1="$lit$",g=`lit$${Math.random().toFixed(9).slice(2)}$`,X1="?"+g,o5=`<${X1}>`,k=document,I=()=>k.createComment(""),G=L=>L===null||typeof L!="object"&&typeof L!="function",x1=Array.isArray,a5=L=>x1(L)||typeof L?.[Symbol.iterator]=="function",A1=`[ 	
\f\r]`,W=/<(?:(!--|\/[^a-zA-Z])|(\/?[a-zA-Z][^>\s]*)|(\/?$))/g,U1=/-->/g,Q1=/>/g,f=RegExp(`>|${A1}(?:([^\\s"'>=/]+)(${A1}*=${A1}*(?:[^ 	
\f\r"'\`<>=]|("|')|))|$)`,"g"),z1=/'/g,K1=/"/g,Y1=/^(?:script|style|textarea|title)$/i,Z1=L=>(H,...C)=>({_$litType$:L,strings:H,values:C}),p=Z1(1),s1=Z1(2),D5=Z1(3),y=Symbol.for("lit-noChange"),d=Symbol.for("lit-nothing"),j1=new WeakMap,b=k.createTreeWalker(k,129);function J1(L,H){if(!x1(L)||!L.hasOwnProperty("raw"))throw Error("invalid template strings array");return G1!==void 0?G1.createHTML(H):H}var A5=(L,H)=>{let C=L.length-1,V=[],M,r=H===2?"<svg>":H===3?"<math>":"",e=W;for(let i=0;i<C;i++){let t=L[i],A,o,a=-1,m=0;for(;m<t.length&&(e.lastIndex=m,o=e.exec(t),o!==null);)m=e.lastIndex,e===W?o[1]==="!--"?e=U1:o[1]!==void 0?e=Q1:o[2]!==void 0?(Y1.test(o[2])&&(M=RegExp("</"+o[2],"g")),e=f):o[3]!==void 0&&(e=f):e===f?o[0]===">"?(e=M??W,a=-1):o[1]===void 0?a=-2:(a=e.lastIndex-o[2].length,A=o[1],e=o[3]===void 0?f:o[3]==='"'?K1:z1):e===K1||e===z1?e=f:e===U1||e===Q1?e=W:(e=f,M=void 0);let n=e===f&&L[i+1].startsWith("/>")?" ":"";r+=e===W?t+o5:a>=0?(V.push(A),t.slice(0,a)+q1+t.slice(a)+g+n):t+g+(a===-2?i:n)}return[J1(L,r+(L[C]||"<?>")+(H===2?"</svg>":H===3?"</math>":"")),V]},U=class L{constructor({strings:H,_$litType$:C},V){let M;this.parts=[];let r=0,e=0,i=H.length-1,t=this.parts,[A,o]=A5(H,C);if(this.el=L.createElement(A,V),b.currentNode=this.el.content,C===2||C===3){let a=this.el.content.firstChild;a.replaceWith(...a.childNodes)}for(;(M=b.nextNode())!==null&&t.length<i;){if(M.nodeType===1){if(M.hasAttributes())for(let a of M.getAttributeNames())if(a.endsWith(q1)){let m=o[e++],n=M.getAttribute(a).split(g),v=/([.?@])?(.*)/.exec(m);t.push({type:1,index:r,name:v[2],strings:n,ctor:v[1]==="."?p1:v[1]==="?"?m1:v[1]==="@"?n1:P}),M.removeAttribute(a)}else a.startsWith(g)&&(t.push({type:6,index:r}),M.removeAttribute(a));if(Y1.test(M.tagName)){let a=M.textContent.split(g),m=a.length-1;if(m>0){M.textContent=V1?V1.emptyScript:"";for(let n=0;n<m;n++)M.append(a[n],I()),b.nextNode(),t.push({type:2,index:++r});M.append(a[m],I())}}}else if(M.nodeType===8)if(M.data===X1)t.push({type:2,index:r});else{let a=-1;for(;(a=M.data.indexOf(g,a+1))!==-1;)t.push({type:7,index:r}),a+=g.length-1}r++}}static createElement(H,C){let V=k.createElement("template");return V.innerHTML=H,V}};function B(L,H,C=L,V){if(H===y)return H;let M=V!==void 0?C._$Co?.[V]:C._$Cl,r=G(H)?void 0:H._$litDirective$;return M?.constructor!==r&&(M?._$AO?.(!1),r===void 0?M=void 0:(M=new r(L),M._$AT(L,C,V)),V!==void 0?(C._$Co??=[])[V]=M:C._$Cl=M),M!==void 0&&(H=B(L,M._$AS(L,H.values),M,V)),H}var d1=class{constructor(H,C){this._$AV=[],this._$AN=void 0,this._$AD=H,this._$AM=C}get parentNode(){return this._$AM.parentNode}get _$AU(){return this._$AM._$AU}u(H){let{el:{content:C},parts:V}=this._$AD,M=(H?.creationScope??k).importNode(C,!0);b.currentNode=M;let r=b.nextNode(),e=0,i=0,t=V[0];for(;t!==void 0;){if(e===t.index){let A;t.type===2?A=new Q(r,r.nextSibling,this,H):t.type===1?A=new t.ctor(r,t.name,t.strings,this,H):t.type===6&&(A=new l1(r,this,H)),this._$AV.push(A),t=V[++i]}e!==t?.index&&(r=b.nextNode(),e++)}return b.currentNode=k,M}p(H){let C=0;for(let V of this._$AV)V!==void 0&&(V.strings!==void 0?(V._$AI(H,V,C),C+=V.strings.length-2):V._$AI(H[C])),C++}},Q=class L{get _$AU(){return this._$AM?._$AU??this._$Cv}constructor(H,C,V,M){this.type=2,this._$AH=d,this._$AN=void 0,this._$AA=H,this._$AB=C,this._$AM=V,this.options=M,this._$Cv=M?.isConnected??!0}get parentNode(){let H=this._$AA.parentNode,C=this._$AM;return C!==void 0&&H?.nodeType===11&&(H=C.parentNode),H}get startNode(){return this._$AA}get endNode(){return this._$AB}_$AI(H,C=this){H=B(this,H,C),G(H)?H===d||H==null||H===""?(this._$AH!==d&&this._$AR(),this._$AH=d):H!==this._$AH&&H!==y&&this._(H):H._$litType$!==void 0?this.$(H):H.nodeType!==void 0?this.T(H):a5(H)?this.k(H):this._(H)}O(H){return this._$AA.parentNode.insertBefore(H,this._$AB)}T(H){this._$AH!==H&&(this._$AR(),this._$AH=this.O(H))}_(H){this._$AH!==d&&G(this._$AH)?this._$AA.nextSibling.data=H:this.T(k.createTextNode(H)),this._$AH=H}$(H){let{values:C,_$litType$:V}=H,M=typeof V=="number"?this._$AC(H):(V.el===void 0&&(V.el=U.createElement(J1(V.h,V.h[0]),this.options)),V);if(this._$AH?._$AD===M)this._$AH.p(C);else{let r=new d1(M,this),e=r.u(this.options);r.p(C),this.T(e),this._$AH=r}}_$AC(H){let C=j1.get(H.strings);return C===void 0&&j1.set(H.strings,C=new U(H)),C}k(H){x1(this._$AH)||(this._$AH=[],this._$AR());let C=this._$AH,V,M=0;for(let r of H)M===C.length?C.push(V=new L(this.O(I()),this.O(I()),this,this.options)):V=C[M],V._$AI(r),M++;M<C.length&&(this._$AR(V&&V._$AB.nextSibling,M),C.length=M)}_$AR(H=this._$AA.nextSibling,C){for(this._$AP?.(!1,!0,C);H!==this._$AB;){let V=I1(H).nextSibling;I1(H).remove(),H=V}}setConnected(H){this._$AM===void 0&&(this._$Cv=H,this._$AP?.(H))}},P=class{get tagName(){return this.element.tagName}get _$AU(){return this._$AM._$AU}constructor(H,C,V,M,r){this.type=1,this._$AH=d,this._$AN=void 0,this.element=H,this.name=C,this._$AM=M,this.options=r,V.length>2||V[0]!==""||V[1]!==""?(this._$AH=Array(V.length-1).fill(new String),this.strings=V):this._$AH=d}_$AI(H,C=this,V,M){let r=this.strings,e=!1;if(r===void 0)H=B(this,H,C,0),e=!G(H)||H!==this._$AH&&H!==y,e&&(this._$AH=H);else{let i=H,t,A;for(H=r[0],t=0;t<r.length-1;t++)A=B(this,i[V+t],C,t),A===y&&(A=this._$AH[t]),e||=!G(A)||A!==this._$AH[t],A===d?H=d:H!==d&&(H+=(A??"")+r[t+1]),this._$AH[t]=A}e&&!M&&this.j(H)}j(H){H===d?this.element.removeAttribute(this.name):this.element.setAttribute(this.name,H??"")}},p1=class extends P{constructor(){super(...arguments),this.type=3}j(H){this.element[this.name]=H===d?void 0:H}},m1=class extends P{constructor(){super(...arguments),this.type=4}j(H){this.element.toggleAttribute(this.name,!!H&&H!==d)}},n1=class extends P{constructor(H,C,V,M,r){super(H,C,V,M,r),this.type=5}_$AI(H,C=this){if((H=B(this,H,C,0)??d)===y)return;let V=this._$AH,M=H===d&&V!==d||H.capture!==V.capture||H.once!==V.once||H.passive!==V.passive,r=H!==d&&(V===d||M);M&&this.element.removeEventListener(this.name,this,V),r&&this.element.addEventListener(this.name,this,H),this._$AH=H}handleEvent(H){typeof this._$AH=="function"?this._$AH.call(this.options?.host??this.element,H):this._$AH.handleEvent(H)}},l1=class{constructor(H,C,V){this.element=H,this.type=6,this._$AN=void 0,this._$AM=C,this.options=V}get _$AU(){return this._$AM._$AU}_$AI(H){B(this,H)}};var d5=v1.litHtmlPolyfillSupport;d5?.(U,Q),(v1.litHtmlVersions??=[]).push("3.3.3");var C2=(L,H,C)=>{let V=C?.renderBefore??H,M=V._$litPart$;if(M===void 0){let r=C?.renderBefore??null;V._$litPart$=M=new Q(H.insertBefore(I(),r),r,void 0,C??{})}return M._$AI(L),M};var u1=globalThis,S=class extends O{constructor(){super(...arguments),this.renderOptions={host:this},this._$Do=void 0}createRenderRoot(){let H=super.createRenderRoot();return this.renderOptions.renderBefore??=H.firstChild,H}update(H){let C=this.render();this.hasUpdated||(this.renderOptions.isConnected=this.isConnected),super.update(H),this._$Do=C2(C,this.renderRoot,this.renderOptions)}connectedCallback(){super.connectedCallback(),this._$Do?.setConnected(!0)}disconnectedCallback(){super.disconnectedCallback(),this._$Do?.setConnected(!1)}render(){return y}};S._$litElement$=!0,S.finalized=!0,u1.litElementHydrateSupport?.({LitElement:S});var p5=u1.litElementPolyfillSupport;p5?.({LitElement:S});(u1.litElementVersions??=[]).push("4.2.2");var H2="M11,15H13V17H11V15M11,7H13V13H11V7M12,2C6.47,2 2,6.5 2,12A10,10 0 0,0 12,22A10,10 0 0,0 22,12A10,10 0 0,0 12,2M12,20A8,8 0 0,1 4,12A8,8 0 0,1 12,4A8,8 0 0,1 20,12A8,8 0 0,1 12,20Z";var V2="M11,4H13V16L18.5,10.5L19.92,11.92L12,19.84L4.08,11.92L5.5,10.5L11,16V4Z";var L2="M20,11V13H8L13.5,18.5L12.08,19.92L4.16,12L12.08,4.08L13.5,5.5L8,11H20Z";var M2="M4,11V13H16L10.5,18.5L11.92,19.92L19.84,12L11.92,4.08L10.5,5.5L16,11H4Z";var r2="M13,20H11V8L5.5,13.5L4.08,12.08L12,4.16L19.92,12.08L18.5,13.5L13,8V20Z";var e2="M16 20H8V6H16M16.67 4H15V2H9V4H7.33C6.6 4 6 4.6 6 5.33V20.67C6 21.4 6.6 22 7.33 22H16.67C17.41 22 18 21.41 18 20.67V5.33C18 4.6 17.4 4 16.67 4M15 16H9V19H15V16M15 7H9V10H15V7M15 11.5H9V14.5H15V11.5Z";var t2="M16 20H8V6H16M16.67 4H15V2H9V4H7.33C6.6 4 6 4.6 6 5.33V20.67C6 21.4 6.6 22 7.33 22H16.67C17.41 22 18 21.41 18 20.67V5.33C18 4.6 17.4 4 16.67 4M15 16H9V19H15V16",i2="M16 20H8V6H16M16.67 4H15V2H9V4H7.33C6.6 4 6 4.6 6 5.33V20.67C6 21.4 6.6 22 7.33 22H16.67C17.41 22 18 21.41 18 20.67V5.33C18 4.6 17.4 4 16.67 4M15 16H9V19H15V16M15 11.5H9V14.5H15V11.5Z";var o2="M16,20H8V6H16M16.67,4H15V2H9V4H7.33A1.33,1.33 0 0,0 6,5.33V20.67C6,21.4 6.6,22 7.33,22H16.67A1.33,1.33 0 0,0 18,20.67V5.33C18,4.6 17.4,4 16.67,4Z";var S1="M15,13H16.5V15.82L18.94,17.23L18.19,18.53L15,16.69V13M19,8H5V19H9.67C9.24,18.09 9,17.07 9,16A7,7 0 0,1 16,9C17.07,9 18.09,9.24 19,9.67V8M5,21C3.89,21 3,20.1 3,19V5C3,3.89 3.89,3 5,3H6V1H8V3H16V1H18V3H19A2,2 0 0,1 21,5V11.1C22.24,12.36 23,14.09 23,16A7,7 0 0,1 16,23C14.09,23 12.36,22.24 11.1,21H5M16,11.15A4.85,4.85 0 0,0 11.15,16C11.15,18.68 13.32,20.85 16,20.85A4.85,4.85 0 0,0 20.85,16C20.85,13.32 18.68,11.15 16,11.15Z";var a2="M19,19H5V8H19M19,3H18V1H16V3H8V1H6V3H5C3.89,3 3,3.9 3,5V19A2,2 0 0,0 5,21H19A2,2 0 0,0 21,19V5A2,2 0 0,0 19,3M9.31,17L11.75,14.56L14.19,17L15.25,15.94L12.81,13.5L15.25,11.06L14.19,10L11.75,12.44L9.31,10L8.25,11.06L10.69,13.5L8.25,15.94L9.31,17Z";var A2="M3,6H21V18H3V6M12,9A3,3 0 0,1 15,12A3,3 0 0,1 12,15A3,3 0 0,1 9,12A3,3 0 0,1 12,9M7,8A2,2 0 0,1 5,10V14A2,2 0 0,1 7,16H17A2,2 0 0,1 19,14V10A2,2 0 0,1 17,8H7Z";var d2="M8.59,16.58L13.17,12L8.59,7.41L10,6L16,12L10,18L8.59,16.58Z";var p2="M19.8 22.6L17.15 20H6.5Q4.2 20 2.6 18.4T1 14.5Q1 12.58 2.19 11.08 3.38 9.57 5.25 9.15 5.33 8.95 5.4 8.76 5.5 8.57 5.55 8.35L1.4 4.2L2.8 2.8L21.2 21.2M6.5 18H15.15L7.1 9.95Q7.05 10.23 7.03 10.5 7 10.73 7 11H6.5Q5.05 11 4.03 12.03 3 13.05 3 14.5 3 15.95 4.03 17 5.05 18 6.5 18M11.13 14M21.6 18.75L20.15 17.35Q20.58 17 20.79 16.54 21 16.08 21 15.5 21 14.45 20.27 13.73 19.55 13 18.5 13H17V11Q17 8.93 15.54 7.46 14.08 6 12 6 11.33 6 10.7 6.16 10.07 6.33 9.5 6.68L8.05 5.23Q8.93 4.63 9.91 4.31 10.9 4 12 4 14.93 4 16.96 6.04 19 8.07 19 11 20.73 11.2 21.86 12.5 23 13.78 23 15.5 23 16.5 22.63 17.31 22.25 18.15 21.6 18.75M14.83 12.03Z";var m2="M18,11H6A2,2 0 0,0 4,13V21A2,2 0 0,0 6,23H18A2,2 0 0,0 20,21V13A2,2 0 0,0 18,11M18,21H6V17H18V21M18,15H6V13H18V15M4.93,4.92L6.34,6.33C9.46,3.2 14.53,3.2 17.66,6.33L19.07,4.92C15.17,1 8.84,1 4.93,4.92M7.76,7.75L9.17,9.16C10.73,7.6 13.26,7.6 14.83,9.16L16.24,7.75C13.9,5.41 10.1,5.41 7.76,7.75Z";var n2="M15 18.5C12.5 18.5 10.32 17.08 9.24 15H15L16 13H8.58C8.53 12.67 8.5 12.34 8.5 12S8.53 11.33 8.58 11H15L16 9H9.24C10.32 6.92 12.5 5.5 15 5.5C16.61 5.5 18.09 6.09 19.23 7.07L21 5.3C19.41 3.87 17.3 3 15 3C11.08 3 7.76 5.5 6.5 9H3L2 11H6.06C6 11.33 6 11.66 6 12S6 12.67 6.06 13H3L2 15H6.5C7.76 18.5 11.08 21 15 21C17.31 21 19.41 20.13 21 18.7L19.22 16.93C18.09 17.91 16.62 18.5 15 18.5Z";var l2="M14 21C15.93 21 17.62 19.83 18 18L16.25 17.12C16 18.21 15.33 19 14 19H9.1C9.93 18 10.6 16.66 10.6 15C10.6 14.65 10.57 14.31 10.5 14H14V12H9.82C9 10.42 8 9.6 8 8C8 6.07 9.57 4.5 11.5 4.5C13 4.5 14.29 5.45 14.78 6.78L16.63 6C15.83 3.95 13.84 2.5 11.5 2.5C8.46 2.5 6 4.96 6 8C6 9.78 6.79 10.9 7.5 12H6V14H8.47C8.55 14.31 8.6 14.64 8.6 15C8.6 17.7 6 19 6 19V21H14Z";var v2="M7,15H9C9,16.08 10.37,17 12,17C13.63,17 15,16.08 15,15C15,13.9 13.96,13.5 11.76,12.97C9.64,12.44 7,11.78 7,9C7,7.21 8.47,5.69 10.5,5.18V3H13.5V5.18C15.53,5.69 17,7.21 17,9H15C15,7.92 13.63,7 12,7C10.37,7 9,7.92 9,9C9,10.1 10.04,10.5 12.24,11.03C14.36,11.56 17,12.22 17,15C17,16.79 15.53,18.31 13.5,18.82V21H10.5V18.82C8.47,18.31 7,16.79 7,15Z";var L1="M19.77,7.23L19.78,7.22L16.06,3.5L15,4.56L17.11,6.67C16.17,7.03 15.5,7.93 15.5,9A2.5,2.5 0 0,0 18,11.5C18.36,11.5 18.69,11.42 19,11.29V18.5A1,1 0 0,1 18,19.5A1,1 0 0,1 17,18.5V14A2,2 0 0,0 15,12H14V5A2,2 0 0,0 12,3H6A2,2 0 0,0 4,5V21H14V13.5H15.5V18.5A2.5,2.5 0 0,0 18,21A2.5,2.5 0 0,0 20.5,18.5V9C20.5,8.31 20.22,7.68 19.77,7.23M18,10A1,1 0 0,1 17,9A1,1 0 0,1 18,8A1,1 0 0,1 19,9A1,1 0 0,1 18,10M8,18V13.5H6L10,6V11H12L8,18Z";var x2="M7,2V13H10V22L17,10H13L17,2H7Z";var Z2="M7,5H21V7H7V5M7,13V11H21V13H7M4,4.5A1.5,1.5 0 0,1 5.5,6A1.5,1.5 0 0,1 4,7.5A1.5,1.5 0 0,1 2.5,6A1.5,1.5 0 0,1 4,4.5M4,10.5A1.5,1.5 0 0,1 5.5,12A1.5,1.5 0 0,1 4,13.5A1.5,1.5 0 0,1 2.5,12A1.5,1.5 0 0,1 4,10.5M7,19V17H21V19H7M4,16.5A1.5,1.5 0 0,1 5.5,18A1.5,1.5 0 0,1 4,19.5A1.5,1.5 0 0,1 2.5,18A1.5,1.5 0 0,1 4,16.5Z";var s2="M13.5,8H12V13L16.28,15.54L17,14.33L13.5,12.25V8M13,3A9,9 0 0,0 4,12H1L4.96,16.03L9,12H6A7,7 0 0,1 13,5A7,7 0 0,1 20,12A7,7 0 0,1 13,19C11.07,19 9.32,18.21 8.06,16.94L6.64,18.36C8.27,20 10.5,21 13,21A9,9 0 0,0 22,12A9,9 0 0,0 13,3";var u2="M5 20V12H2L12 3L22 12H19V20H5M12 5.69L7 10.19V18H17V10.19L12 5.69M11.5 18V14H9L12.5 7V11H15L11.5 18Z";var S2="M11 15H6L13 1V9H18L11 23V15Z";var c2="M12,17A2,2 0 0,0 14,15C14,13.89 13.1,13 12,13A2,2 0 0,0 10,15A2,2 0 0,0 12,17M18,8A2,2 0 0,1 20,10V20A2,2 0 0,1 18,22H6A2,2 0 0,1 4,20V10C4,8.89 4.9,8 6,8H7V6A5,5 0 0,1 12,1A5,5 0 0,1 17,6V8H18M12,3A3,3 0 0,0 9,6V8H15V6A3,3 0 0,0 12,3Z";var c1="M18 1C15.24 1 13 3.24 13 6V8H4C2.9 8 2 8.89 2 10V20C2 21.11 2.9 22 4 22H16C17.11 22 18 21.11 18 20V10C18 8.9 17.11 8 16 8H15V6C15 4.34 16.34 3 18 3C19.66 3 21 4.34 21 6V8H23V6C23 3.24 20.76 1 18 1M10 13C11.1 13 12 13.89 12 15C12 16.11 11.11 17 10 17C8.9 17 8 16.11 8 15C8 13.9 8.9 13 10 13Z";var h2="M7,10L12,15L17,10H7Z";var O2="M8,5.14V19.14L19,12.14L8,5.14Z";var g2="M13.13 22.19L11.5 18.36C13.07 17.78 14.54 17 15.9 16.09L13.13 22.19M5.64 12.5L1.81 10.87L7.91 8.1C7 9.46 6.22 10.93 5.64 12.5M21.61 2.39C21.61 2.39 16.66 .269 11 5.93C8.81 8.12 7.5 10.53 6.65 12.64C6.37 13.39 6.56 14.21 7.11 14.77L9.24 16.89C9.79 17.45 10.61 17.63 11.36 17.35C13.5 16.53 15.88 15.19 18.07 13C23.73 7.34 21.61 2.39 21.61 2.39M14.54 9.46C13.76 8.68 13.76 7.41 14.54 6.63S16.59 5.85 17.37 6.63C18.14 7.41 18.15 8.68 17.37 9.46C16.59 10.24 15.32 10.24 14.54 9.46M8.88 16.53L7.47 15.12L8.88 16.53M6.24 22L9.88 18.36C9.54 18.27 9.21 18.12 8.91 17.91L4.83 22H6.24M2 22H3.41L8.18 17.24L6.76 15.83L2 20.59V22M2 19.17L6.09 15.09C5.88 14.79 5.73 14.47 5.64 14.12L2 17.76V19.17Z";var M1="M11.45,2V5.55L15,3.77L11.45,2M10.45,8L8,10.46L11.75,11.71L10.45,8M2,11.45L3.77,15L5.55,11.45H2M10,2H2V10C2.57,10.17 3.17,10.25 3.77,10.25C7.35,10.26 10.26,7.35 10.27,3.75C10.26,3.16 10.17,2.57 10,2M17,22V16H14L19,7V13H22L17,22Z";var f2="M18,18H6V6H18V18Z";var b2="M15 13V5A3 3 0 0 0 9 5V13A5 5 0 1 0 15 13M12 4A1 1 0 0 1 13 5V8H11V5A1 1 0 0 1 12 4Z";var k2="M12,20A7,7 0 0,1 5,13A7,7 0 0,1 12,6A7,7 0 0,1 19,13A7,7 0 0,1 12,20M19.03,7.39L20.45,5.97C20,5.46 19.55,5 19.04,4.56L17.62,6C16.07,4.74 14.12,4 12,4A9,9 0 0,0 3,13A9,9 0 0,0 12,22C17,22 21,17.97 21,13C21,10.88 20.26,8.93 19.03,7.39M11,14H13V8H11M15,1H9V3H15V1Z";var h1="M8.28,5.45L6.5,4.55L7.76,2H16.23L17.5,4.55L15.72,5.44L15,4H9L8.28,5.45M18.62,8H14.09L13.3,5H10.7L9.91,8H5.38L4.1,10.55L5.89,11.44L6.62,10H17.38L18.1,11.45L19.89,10.56L18.62,8M17.77,22H15.7L15.46,21.1L12,15.9L8.53,21.1L8.3,22H6.23L9.12,11H11.19L10.83,12.35L12,14.1L13.16,12.35L12.81,11H14.88L17.77,22M11.4,15L10.5,13.65L9.32,18.13L11.4,15M14.68,18.12L13.5,13.64L12.6,15L14.68,18.12Z";var O1="M17.75,4.09L15.22,6.03L16.13,9.09L13.5,7.28L10.87,9.09L11.78,6.03L9.25,4.09L12.44,4L13.5,1L14.56,4L17.75,4.09M21.25,11L19.61,12.25L20.2,14.23L18.5,13.06L16.8,14.23L17.39,12.25L15.75,11L17.81,10.95L18.5,9L19.19,10.95L21.25,11M18.97,15.95C19.8,15.87 20.69,17.05 20.16,17.8C19.84,18.25 19.5,18.67 19.08,19.07C15.17,23 8.84,23 4.94,19.07C1.03,15.17 1.03,8.83 4.94,4.93C5.34,4.53 5.76,4.17 6.21,3.85C6.96,3.32 8.14,4.21 8.06,5.04C7.79,7.9 8.75,10.87 10.95,13.06C13.14,15.26 16.1,16.22 18.97,15.95M17.33,17.97C14.5,17.81 11.7,16.64 9.53,14.5C7.36,12.31 6.2,9.5 6.04,6.68C3.23,9.82 3.34,14.64 6.35,17.66C9.37,20.67 14.19,20.78 17.33,17.97Z";function g1(L){switch(L.locale?.number_format){case"comma_decimal":return"en-US";case"decimal_comma":return"de";case"space_comma":return"fr";case"system":return;default:return L.locale?.language||L.language}}function x(L,H,C){return new Intl.NumberFormat(g1(L),{minimumFractionDigits:C,maximumFractionDigits:C,useGrouping:L.locale?.number_format!=="none"}).format(H)}function w2(L,H,C){return new Intl.NumberFormat(g1(L),{minimumFractionDigits:0,maximumFractionDigits:C,useGrouping:L.locale?.number_format!=="none"}).format(H)}function B2(L,H,C){if(C&&/^[A-Z]{3}$/.test(C))try{return new Intl.NumberFormat(g1(L),{style:"currency",currency:C}).format(H)}catch{}return`${x(L,H,2)}${C?` ${C}`:""}`}function c(L,H){return`${x(L,H/1e3,1)} kW`}function z(L){let H=Math.round(L),C=Math.floor(H/60),V=H%60;return C?V?`${C} h ${V} min`:`${C} h`:`${V} min`}function K(L){let H=/^(\d{2}):(\d{2})/.exec(L??"");return H?`${H[1]}:${H[2]}`:void 0}function P2(L,H,C){let V=L.locale?.language||L.language,M=L.config?.time_zone;try{return new Intl.DateTimeFormat(V,{...C,timeZone:M}).format(H)}catch{return new Intl.DateTimeFormat(V,C).format(H)}}function y2(L,H){let C={year:"numeric",month:"2-digit",day:"2-digit"};try{return new Intl.DateTimeFormat("en-CA",{...C,timeZone:H}).format(L)}catch{return new Intl.DateTimeFormat("en-CA",C).format(L)}}function f1(L,H){return P2(L,H,{hour:"2-digit",minute:"2-digit"})}function T2(L,H,C=new Date){let V=L.config?.time_zone;return y2(H,V)===y2(C,V)?f1(L,H):P2(L,H,{day:"numeric",month:"short"})}function w(L){if(!L)return;let H=Number(L.state);if(!(L.state===""||!Number.isFinite(H)))switch(L.attributes.unit_of_measurement){case"kW":return H*1e3;case"MW":return H*1e6;default:return H}}function Z(L){if(!L||L.state==="")return;let H=Number(L.state);return Number.isFinite(H)?H:void 0}var r1={card_name:"THOR Wallbox",card_description:"Status, power, session and controls of a Growatt THOR wallbox.",no_device:"Pick the wallbox in the card editor.",device_not_found:"Wallbox not found: check the device in the card editor.",plug_in:"Plug in the car to start",car_connected:"Car connected",waiting_surplus:"Waiting for surplus",waiting_slot:"Waiting for the off-peak slot",start:"Start charging",stop:"Stop",unlock:"Unlock connector",cancel:"Cancel start",charge_mode:"Charge mode",locked_note:"Mode and settings can be changed once the session is over and the car is unplugged.",energy:"Energy",duration:"Duration",cost:"Cost",last_session:"Last charge",scheduled_start:"Scheduled start",schedule:"Schedule charging",booking_start:"Start",start_now:"Now",start_at_time:"At a time",start_every_day:"Every day",booking_time:"Start at",booking_limit:"Limit",limit_none:"None",booking_cancel:"Cancel",booking_confirm:"Schedule",booking_rfid:"In RFID mode only a start at a time can be set here: otherwise charging starts with the card.",booking_replaces:"Replaces the scheduled start.",summary:"{start} {limit}.",summary_now:"Starts now",summary_today:"Starts today at {time}",summary_tomorrow:"Starts tomorrow at {time}",summary_every_day:"Starts every day at {time}",summary_no_limit:"with no limit",summary_stops_at:"and stops at {value}",summary_stops_after:"and stops after {value}",error_time:"Choose the start time.",error_energy:"Enter an energy above 0.",error_cost:"Enter a cost above 0.",error_duration:"Enter a duration from 1 minute to 23 h 59 min.",every_day:"Every day at {time}",cable_locked:"Cable locked",cable_unlocked:"Cable unlocked",surplus_only:"Surplus only",grid_import:"Grid import",grid_import_power:"Grid import \xB7 {power}",boost:"Boost \xB7 {type}",slots:"Off-peak slots",warm_up:"Warm-up",limit_energy:"Energy limit",limit_cost:"Cost limit",limit_duration:"Duration limit",boost_by:"Smart Boost by {time}",done_of:"{done} of {target}",fault:"Fault",vendor_code:"Vendor code: {code}.",fault_hint:"If it persists, contact your installer.",offline_title:"Wallbox unreachable",offline_text:"It is not connected to the Growatt cloud: data and controls come back once it reconnects.",rfid_title:"RFID mode",rfid_text:"Start and stop with the card only. Scheduled starts still work.",solar:"Solar",wallbox:"Wallbox",grid:"Grid",battery:"Battery",from_solar:"from solar {value}",from_battery:"from the battery {value}",from_grid:"from the grid {value}",surplus:"Available surplus: {value}.",battery_charging:"The home battery is taking {value}: while it charges, the wallbox only gets what is left over.",battery_charging_soc:"The home battery ({soc}) is taking {value}: while it charges, the wallbox only gets what is left over.",power:"Charging power",editor_device_id:"Wallbox",editor_name:"Name",editor_flow:"Energy flow",editor_solar_power:"Solar production",editor_home_power:"Home consumption",editor_grid_import_power:"Grid import",editor_grid_export_power:"Grid export",editor_battery_power:"Home battery power",editor_battery_charging_positive:"Battery power is positive while charging",editor_battery_soc:"Home battery charge",editor_home_includes_wallbox:"Home consumption includes the wallbox",editor_content:"Content",editor_show_session:"Session",editor_show_progress:"Progress",editor_show_controls:"Controls",editor_show_last_session:"Last charge",helper_solar_power:"Power sensors of the inverter, to show where the wallbox power comes from.",helper_home_power:"Optional: with it the card works out the solar surplus.",helper_grid_export_power:"Recommended for PV Linkage: the surplus becomes the power exported to the grid, the same value the wallbox reads from the meter.",helper_battery_power:"Optional: shows the home battery, which takes the surplus first while it charges.",helper_battery_charging_positive:"On when the sensor is positive while charging and negative while discharging.",helper_home_includes_wallbox:"On when the wallbox is downstream of the home consumption sensor.",helper_show_session:"Energy, duration and cost while a session is open.",helper_show_progress:"Fast limit or smart Boost energy reached.",helper_show_controls:"Start, stop, scheduling, unlock and charge mode.",helper_show_last_session:"While no session is open."},m5={card_name:"THOR Wallbox",card_description:"Stato, potenza, sessione e comandi di una wallbox Growatt THOR.",no_device:"Scegli la wallbox nell'editor della card.",device_not_found:"Wallbox non trovata: controlla il dispositivo nell'editor della card.",plug_in:"Collega l'auto per iniziare",car_connected:"Auto collegata",waiting_surplus:"In attesa di surplus",waiting_slot:"In attesa della fascia Off-peak",start:"Avvia ricarica",stop:"Arresta",unlock:"Sblocca connettore",cancel:"Annulla avvio",charge_mode:"Modalit\xE0 di ricarica",locked_note:"Modalit\xE0 e impostazioni si cambiano a sessione chiusa, con l'auto scollegata.",energy:"Energia",duration:"Durata",cost:"Costo",last_session:"Ultima ricarica",scheduled_start:"Avvio programmato",schedule:"Programma la ricarica",booking_start:"Avvio",start_now:"Subito",start_at_time:"All'orario",start_every_day:"Ogni giorno",booking_time:"Alle",booking_limit:"Limite",limit_none:"Nessuno",booking_cancel:"Annulla",booking_confirm:"Programma",booking_rfid:"In modalit\xE0 RFID qui si pu\xF2 solo programmare un orario: altrimenti la ricarica parte con la tessera.",booking_replaces:"Sostituisce l'avvio programmato.",summary:"{start} {limit}.",summary_now:"Parte subito",summary_today:"Parte oggi alle {time}",summary_tomorrow:"Parte domani alle {time}",summary_every_day:"Parte ogni giorno alle {time}",summary_no_limit:"senza limite",summary_stops_at:"e si ferma a {value}",summary_stops_after:"e si ferma dopo {value}",error_time:"Scegli l'orario di avvio.",error_energy:"Inserisci un'energia maggiore di 0.",error_cost:"Inserisci un costo maggiore di 0.",error_duration:"Inserisci una durata da 1 minuto a 23 h 59 min.",every_day:"Ogni giorno alle {time}",cable_locked:"Cavo bloccato",cable_unlocked:"Cavo sbloccato",surplus_only:"Solo surplus",grid_import:"Importa da rete",grid_import_power:"Importa da rete \xB7 {power}",boost:"Boost \xB7 {type}",slots:"Fasce Off-peak",warm_up:"Warm-up",limit_energy:"Limite di energia",limit_cost:"Limite di costo",limit_duration:"Limite di durata",boost_by:"Boost smart entro le {time}",done_of:"{done} di {target}",fault:"Guasto",vendor_code:"Codice del produttore: {code}.",fault_hint:"Se il guasto resta, contatta l'installatore.",offline_title:"Wallbox non raggiungibile",offline_text:"Non risulta connessa al cloud Growatt: dati e comandi tornano appena si riconnette.",rfid_title:"Modalit\xE0 RFID",rfid_text:"Avvio e arresto solo con la tessera. Gli avvii programmati funzionano comunque.",solar:"Fotovoltaico",wallbox:"Wallbox",grid:"Rete",battery:"Batteria",from_solar:"dal fotovoltaico {value}",from_battery:"dalla batteria {value}",from_grid:"dalla rete {value}",surplus:"Surplus disponibile: {value}.",battery_charging:"La batteria di casa sta assorbendo {value}: finch\xE9 si carica, alla wallbox arriva solo quello che avanza.",battery_charging_soc:"La batteria di casa ({soc}) sta assorbendo {value}: finch\xE9 si carica, alla wallbox arriva solo quello che avanza.",power:"Potenza di ricarica",editor_device_id:"Wallbox",editor_name:"Nome",editor_flow:"Flusso di energia",editor_solar_power:"Produzione fotovoltaica",editor_home_power:"Consumo della casa",editor_grid_import_power:"Prelievo dalla rete",editor_grid_export_power:"Immissione in rete",editor_battery_power:"Potenza della batteria di casa",editor_battery_charging_positive:"La potenza della batteria \xE8 positiva quando si carica",editor_battery_soc:"Carica della batteria di casa",editor_home_includes_wallbox:"Il consumo della casa include la wallbox",editor_content:"Contenuto",editor_show_session:"Sessione",editor_show_progress:"Avanzamento",editor_show_controls:"Comandi",editor_show_last_session:"Ultima ricarica",helper_solar_power:"Sensori di potenza dell'inverter, per mostrare da dove arriva l'energia della wallbox.",helper_home_power:"Facoltativo: serve a calcolare il surplus fotovoltaico.",helper_grid_export_power:"Consigliato in PV Linkage: il surplus diventa la potenza immessa in rete, lo stesso valore che la wallbox legge dal contatore.",helper_battery_power:"Facoltativo: mostra la batteria di casa, che quando si carica prende il surplus per prima.",helper_battery_charging_positive:"Attivo se il sensore \xE8 positivo mentre si carica e negativo mentre si scarica.",helper_home_includes_wallbox:"Attivo se la wallbox \xE8 a valle del sensore dei consumi della casa.",helper_show_session:"Energia, durata e costo mentre una sessione \xE8 aperta.",helper_show_progress:"Quanto manca al limite Fast o all'energia del Boost smart.",helper_show_controls:"Avvio, arresto, programmazione, sblocco e modalit\xE0 di ricarica.",helper_show_last_session:"Quando nessuna sessione \xE8 aperta."},n5={en:r1,it:m5};function l5(L){return(L?.locale?.language||L?.language||document.documentElement.lang||navigator.language||"en").split("-")[0]}function u(L,H,C={}){let V=(n5[l5(L)]??r1)[H]??r1[H];for(let[M,r]of Object.entries(C))V=V.replace(`{${M}}`,r);return V}function b1(L){return L in r1}var k1=["now","at_time","every_day"],y1=["none","energy","cost","duration"],v5=1439,F2=/^([01]\d|2[0-3]):[0-5]\d$/;function x5(L){return k1.includes(L??"")}function Z5(L){return y1.includes(L??"")}function _2(L){return L!==void 0&&Number.isFinite(L)?String(L):""}function R2(L,H){let C={hour:"2-digit",minute:"2-digit",hourCycle:"h23"},V;try{V=new Intl.DateTimeFormat("en-GB",{...C,timeZone:H}).formatToParts(L)}catch{V=new Intl.DateTimeFormat("en-GB",C).formatToParts(L)}let M=r=>V.find(e=>e.type===r)?.value??"00";return`${M("hour")}:${M("minute")}`}function D2(L,H,C){let V=new Date(L??"");if(Number.isNaN(V.getTime()))return;let M=typeof H.limit=="string"?H.limit:"none",r=typeof H.limit_value=="number"?H.limit_value:void 0;return{start:H.every_day?"every_day":"at_time",time:R2(V,C),limit:M,energy:M==="energy"?r:void 0,cost:M==="cost"?r:void 0,duration:M==="duration"?r:void 0}}function E2(L,H){let C=x5(L.start)?L.start:"now",V=L.duration!==void 0&&L.duration>0?Math.round(L.duration):void 0;return{start:H&&C==="now"?"at_time":C,time:F2.test(L.time??"")?L.time:"",limit:Z5(L.limit)?L.limit:"none",energy:_2(L.energy),cost:_2(L.cost),hours:V===void 0?"":String(Math.floor(V/60)),minutes:V===void 0?"":String(V%60)}}function j(L){let H=L.trim().replace(",",".");return H===""?NaN:Number(H)}function w1(L){let H=L.hours.trim()===""?0:Number(L.hours),C=L.minutes.trim()===""?0:Number(L.minutes);return!Number.isInteger(H)||!Number.isInteger(C)||H<0||C<0||C>59?NaN:H*60+C}function B1(L){if(L.start!=="now"&&!F2.test(L.time))return"error_time";switch(L.limit){case"energy":return j(L.energy)>0?void 0:"error_energy";case"cost":return j(L.cost)>0?void 0:"error_cost";case"duration":{let H=w1(L);return H>=1&&H<=v5?void 0:"error_duration"}default:return}}function $2(L,H){let C={device_id:H,limit:L.limit};return L.limit==="energy"?C.value=j(L.energy):L.limit==="cost"?C.value=j(L.cost):L.limit==="duration"&&(C.value=w1(L)),L.start!=="now"&&(C.start_time=L.time,C.every_day=L.start==="every_day"),C}function s5(L,H){let[C,V]=H.split(":").map(Number);return new Intl.DateTimeFormat(L.locale?.language||L.language,{hour:"2-digit",minute:"2-digit"}).format(new Date(2e3,0,1,C,V))}function P1(L,H,C,V){switch(H){case"energy":return`${w2(L,C,2)} kWh`;case"cost":return B2(L,C,V);case"duration":return z(C);default:return""}}function N2(L,H,C,V,M){let r=(t,A)=>u(L,t,A),e;if(H.start==="now")e=r("summary_now");else{let t=s5(L,H.time);H.start==="every_day"?e=r("summary_every_day",{time:t}):e=H.time>R2(C,M)?r("summary_today",{time:t}):r("summary_tomorrow",{time:t})}let i;if(H.limit==="none")i=r("summary_no_limit");else{let t=H.limit==="duration"?w1(H):j(H.limit==="energy"?H.energy:H.cost),A=P1(L,H.limit,t,V);i=H.limit==="duration"?r("summary_stops_after",{value:A}):r("summary_stops_at",{value:A})}return r("summary",{start:e,limit:i})}var T="growatt_thor_cloud",T1=["charging","suspended_ev","suspended_evse"],W2=[...T1,"finishing"];function I2(L){let H=new Set;for(let C of Object.values(L.entities))C.platform===T&&C.device_id&&H.add(C.device_id);return[...H]}function G2(L,H){let C=new Map;if(!H)return C;for(let V of Object.values(L.entities))V.platform!==T||V.device_id!==H||!V.translation_key||C.set(`${V.entity_id.split(".")[0]}.${V.translation_key}`,V.entity_id);return C}var u5=Promise.race([customElements.whenDefined("home-assistant"),customElements.whenDefined("hc-main"),new Promise(L=>setTimeout(L,3e4))]);function _(L,H){u5.then(()=>{customElements.get(L)||customElements.define(L,H)})}var S5={now:"start_now",at_time:"start_at_time",every_day:"start_every_day"},c5={none:"limit_none",energy:"energy",cost:"cost",duration:"duration"};function h5(L,H){if(!H||!/^[A-Z]{3}$/.test(H))return H??"";try{return new Intl.NumberFormat(L.locale?.language||L.language,{style:"currency",currency:H}).formatToParts(0).find(V=>V.type==="currency")?.value??H}catch{return H}}var q=class extends S{constructor(){super();this.close=()=>{this._dialog?.close()};this._submit=async()=>{let C=this._form;if(!(!C||!this.hass||!this.deviceId||B1(C)||this._busy)){this._busy=!0,this._error=void 0;try{await this.hass.callService(T,"start_charging",$2(C,this.deviceId)),this.close()}catch(V){this._error=V?.message??String(V)}finally{this._busy=!1}}};this._backdropClick=C=>{let V=this._dialog;if(!V||C.target!==V)return;let M=V.getBoundingClientRect();C.clientX>=M.left&&C.clientX<=M.right&&C.clientY>=M.top&&C.clientY<=M.bottom||this.close()};this._closed=()=>{this.dispatchEvent(new CustomEvent("closed"))};this.rfid=!1,this.replaces=!1,this._busy=!1}_t(C,V){return u(this.hass,C,V)}get _dialog(){return this.renderRoot.querySelector("dialog")}willUpdate(C){super.willUpdate(C),!this._form&&this.form&&(this._form={...this.form})}firstUpdated(){this._dialog?.showModal()}render(){let C=this._form;if(!C||!this.hass)return d;let V=B1(C),M=k1.filter(e=>!(this.rfid&&e==="now")),r=!!this.hass.themes?.darkMode;return p`
      <dialog
        aria-labelledby="title"
        style=${`color-scheme: ${r?"dark":"light"}`}
        @click=${this._backdropClick}
        @close=${this._closed}
      >
        <h2 id="title" class="title">${this._t("schedule")}</h2>
        <div class="content">
          <div class="field">
            <span class="field-label" id="start-label">${this._t("booking_start")}</span>
            ${this._segmented("start-label",M,S5,C.start,e=>this._set({start:e}))}
            ${this.rfid?p`<p class="note">${this._t("booking_rfid")}</p>`:d}
          </div>
          ${C.start==="now"?d:p`<label class="input">
                <span class="name">${this._t("booking_time")}</span>
                <input
                  type="time"
                  required
                  .value=${C.time}
                  @input=${e=>this._set({time:e.target.value})}
                />
              </label>`}
          <div class="field">
            <span class="field-label" id="limit-label">${this._t("booking_limit")}</span>
            ${this._segmented("limit-label",y1,c5,C.limit,e=>this._set({limit:e}))}
          </div>
          ${this._renderValue(C)}
          <p class="summary ${V?"missing":""}" aria-live="polite">
            ${V?this._t(V):N2(this.hass,C,new Date,this.currency,this.hass.config?.time_zone)}
          </p>
          ${this.replaces&&C.start!=="now"?p`<p class="note">${this._t("booking_replaces")}</p>`:d}
          ${this._error?p`<div class="alert" role="alert">${this._error}</div>`:d}
        </div>
        <div class="actions">
          <button class="action text" type="button" @click=${this.close}>${this._t("booking_cancel")}</button>
          <button class="action filled" type="button" ?disabled=${!!V||this._busy} @click=${this._submit}>
            ${C.start==="now"?this._t("start"):this._t("booking_confirm")}
          </button>
        </div>
      </dialog>
    `}_segmented(C,V,M,r,e){let i=(t,A)=>{let o=0;if(t.key==="ArrowRight"||t.key==="ArrowDown")o=1;else if(t.key==="ArrowLeft"||t.key==="ArrowUp")o=-1;else return;t.preventDefault();let a=(A+o+V.length)%V.length;e(V[a]),t.currentTarget.parentElement?.querySelectorAll('[role="radio"]')[a]?.focus()};return p`
      <div class="segmented" role="radiogroup" aria-labelledby=${C}>
        ${V.map((t,A)=>p`
            <button
              class="option ${t===r?"selected":""}"
              type="button"
              role="radio"
              tabindex=${t===r?"0":"-1"}
              aria-checked=${t===r?"true":"false"}
              @click=${()=>e(t)}
              @keydown=${o=>i(o,A)}
            >
              <span>${this._t(M[t])}</span>
            </button>
          `)}
      </div>
    `}_renderValue(C){let V=(M,r,e,i)=>p`<input
      type="text"
      inputmode=${e}
      autocomplete="off"
      placeholder="0"
      aria-label=${r}
      .value=${M}
      @input=${t=>i(t.target.value)}
    />`;switch(C.limit){case"energy":return p`<label class="input">
          <span class="name">${this._t("energy")}</span>
          ${V(C.energy,this._t("energy"),"decimal",M=>this._set({energy:M}))}
          <span class="unit">kWh</span>
        </label>`;case"cost":return p`<label class="input">
          <span class="name">${this._t("cost")}</span>
          ${V(C.cost,this._t("cost"),"decimal",M=>this._set({cost:M}))}
          <span class="unit">${h5(this.hass,this.currency)}</span>
        </label>`;case"duration":return p`<div class="input">
          <span class="name">${this._t("duration")}</span>
          ${V(C.hours,`${this._t("duration")} (h)`,"numeric",M=>this._set({hours:M}))}
          <span class="unit">h</span>
          ${V(C.minutes,`${this._t("duration")} (min)`,"numeric",M=>this._set({minutes:M}))}
          <span class="unit">min</span>
        </div>`;default:return d}}_set(C){this._form={...this._form,...C},this._error=void 0}};q.properties={hass:{attribute:!1},deviceId:{attribute:!1},form:{attribute:!1},currency:{attribute:!1},rfid:{attribute:!1},replaces:{attribute:!1},_form:{state:!0},_busy:{state:!0},_error:{state:!0}},q.styles=$`
    :host {
      --accent: var(--primary-color, #009ac7);
    }
    dialog {
      width: min(580px, 95vw);
      max-width: 95vw;
      max-height: min(80vh, 720px);
      box-sizing: border-box;
      padding: 0;
      border: none;
      overflow: hidden;
      border-radius: var(--ha-dialog-border-radius, var(--ha-border-radius-3xl, 24px));
      background: var(--ha-dialog-surface-background, var(--card-background-color, #fff));
      color: var(--primary-text-color);
      box-shadow: var(--ha-box-shadow-l, 0 16px 32px -6px rgba(0, 0, 0, 0.2));
      font-family: var(--ha-font-family-body, Roboto, Noto, sans-serif);
      -webkit-font-smoothing: antialiased;
    }
    dialog[open] {
      display: flex;
      flex-direction: column;
      animation: dialog-in 200ms ease-out;
    }
    dialog::backdrop {
      background: rgba(0, 0, 0, 0.32);
    }
    .title {
      margin: 0;
      padding: 24px 24px 16px;
      font-size: var(--ha-font-size-2xl, 24px);
      line-height: 1.2;
      font-weight: var(--ha-font-weight-normal, 400);
    }
    .content {
      flex: 1;
      min-height: 0;
      overflow: auto;
      display: flex;
      flex-direction: column;
      gap: 16px;
      padding: 0 24px;
    }
    .field {
      display: flex;
      flex-direction: column;
      gap: 8px;
    }
    .field-label {
      font-size: var(--ha-font-size-m, 14px);
      font-weight: var(--ha-font-weight-medium, 500);
    }
    .note,
    .summary {
      margin: 0;
      font-size: var(--ha-font-size-s, 12px);
      line-height: 1.4;
      color: var(--secondary-text-color);
    }
    .summary {
      font-size: var(--ha-font-size-m, 14px);
      color: var(--primary-text-color);
    }
    .summary.missing {
      color: var(--secondary-text-color);
    }

    /* Segmented control, like ha-control-select. */
    .segmented {
      position: relative;
      display: flex;
      gap: 4px;
      padding: 4px;
      height: 44px;
      box-sizing: border-box;
      border-radius: var(--ha-border-radius-lg, 12px);
    }
    .segmented::before {
      content: "";
      position: absolute;
      inset: 0;
      border-radius: inherit;
      background: var(--disabled-color, #bdbdbd);
      opacity: 0.2;
    }
    .option {
      position: relative;
      flex: 1;
      min-width: 0;
      padding: 0 4px;
      border: none;
      border-radius: calc(var(--ha-border-radius-lg, 12px) - 4px);
      background: none;
      font-family: inherit;
      font-size: var(--ha-font-size-m, 14px);
      font-weight: var(--ha-font-weight-medium, 500);
      color: var(--primary-text-color);
      cursor: pointer;
      outline: none;
    }
    .option::before {
      content: "";
      position: absolute;
      inset: 0;
      border-radius: inherit;
      background: var(--accent);
      opacity: 0;
      transition: opacity 80ms ease-in-out;
    }
    .option:hover::before {
      opacity: 0.2;
    }
    .option.selected {
      color: var(--text-primary-color, #fff);
    }
    .option.selected::before {
      opacity: 1;
    }
    .option:focus-visible {
      box-shadow: 0 0 0 2px var(--accent);
    }
    .option span {
      position: relative;
      display: block;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }

    /* A labelled field on the neutral fill of Home Assistant's controls. */
    .input {
      position: relative;
      display: flex;
      align-items: center;
      gap: 8px;
      min-height: 48px;
      padding: 0 12px;
      box-sizing: border-box;
      border-radius: var(--ha-border-radius-lg, 12px);
    }
    .input::before {
      content: "";
      position: absolute;
      inset: 0;
      border-radius: inherit;
      background: var(--disabled-color, #bdbdbd);
      opacity: 0.2;
      pointer-events: none;
    }
    .input > * {
      position: relative;
    }
    .input:focus-within {
      box-shadow: 0 0 0 2px var(--accent);
    }
    .input .name {
      flex: 1;
      min-width: 0;
      font-size: var(--ha-font-size-m, 14px);
    }
    .input .unit {
      font-size: var(--ha-font-size-m, 14px);
      color: var(--secondary-text-color);
    }
    /* 16px: smaller text makes iOS zoom into the field. */
    .input input {
      width: 64px;
      min-width: 0;
      padding: 8px 0;
      border: none;
      background: none;
      font-family: inherit;
      font-size: 16px;
      text-align: end;
      color: var(--primary-text-color);
      outline: none;
    }
    .input input::placeholder {
      color: var(--secondary-text-color);
      opacity: 0.6;
    }
    .input input[type="time"] {
      width: auto;
    }

    .alert {
      position: relative;
      padding: 12px;
      border-radius: var(--ha-border-radius-lg, 12px);
      overflow: hidden;
      font-size: var(--ha-font-size-m, 14px);
      line-height: 1.4;
    }
    .alert::before {
      content: "";
      position: absolute;
      inset: 0;
      background: var(--error-color, #db4437);
      opacity: 0.12;
    }

    /* Buttons, like ha-button: plain for Cancel, filled for the main action. */
    .actions {
      display: flex;
      justify-content: flex-end;
      gap: 8px;
      padding: 24px;
    }
    .action {
      position: relative;
      overflow: hidden;
      height: 40px;
      padding: 0 16px;
      border: none;
      border-radius: var(--ha-border-radius-pill, 9999px);
      background: none;
      font-family: inherit;
      font-size: var(--ha-font-size-m, 14px);
      font-weight: var(--ha-font-weight-medium, 500);
      cursor: pointer;
      outline: none;
    }
    .action:focus-visible {
      box-shadow: 0 0 0 2px var(--accent);
    }
    .action.text {
      color: var(--accent);
    }
    .action.text::before {
      content: "";
      position: absolute;
      inset: 0;
      background: var(--accent);
      opacity: 0;
      transition: opacity 180ms ease-in-out;
    }
    .action.text:hover::before {
      opacity: 0.12;
    }
    .action.filled {
      background: var(--accent);
      color: var(--text-primary-color, #fff);
    }
    .action:disabled {
      cursor: not-allowed;
      opacity: 0.5;
    }

    /* Phones and short screens: a bottom sheet, as Home Assistant's adaptive dialogs. */
    @media (max-width: 870px), (max-height: 500px) {
      dialog {
        width: 100vw;
        max-width: 100vw;
        max-height: 90vh;
        margin: auto 0 0;
        border-radius: var(--ha-border-radius-2xl, 20px) var(--ha-border-radius-2xl, 20px) 0 0;
        padding-bottom: var(--safe-area-inset-bottom, 0px);
      }
      dialog[open] {
        animation-name: sheet-in;
      }
    }
    @keyframes dialog-in {
      from {
        opacity: 0;
        transform: scale(0.96);
      }
    }
    @keyframes sheet-in {
      from {
        transform: translateY(100%);
      }
    }
    @media (prefers-reduced-motion: reduce) {
      dialog[open] {
        animation: none;
      }
    }
  `;_("thor-wallbox-booking",q);var U2={home_includes_wallbox:!0,battery_charging_positive:!1,show_session:!0,show_progress:!0,show_controls:!0,show_last_session:!0},O5=["name","solar_power","home_power","grid_import_power","grid_export_power","battery_power","battery_soc"];async function g5(){if(customElements.get("ha-form"))return;await(await(await window.loadCardHelpers?.())?.createCardElement({type:"entities",entities:[]}))?.constructor?.getConfigElement?.()}var e1=class extends S{constructor(){super(...arguments);this._label=C=>{let V=`editor_${C.name}`;return b1(V)?u(this.hass,V):C.name};this._helper=C=>{let V=`helper_${C.name}`;return b1(V)?u(this.hass,V):void 0}}setConfig(C){this._config=C}connectedCallback(){super.connectedCallback(),g5().then(()=>customElements.whenDefined("ha-form")).then(()=>this.requestUpdate())}render(){return!this.hass||!this._config?d:p`
      <ha-form
        .hass=${this.hass}
        .data=${{...U2,...this._config}}
        .schema=${this._schema()}
        .computeLabel=${this._label}
        .computeHelper=${this._helper}
        @value-changed=${this._valueChanged}
      ></ha-form>
    `}_schema(){let C={entity:{filter:{domain:"sensor",device_class:"power"}}};return[{name:"device_id",required:!0,selector:{device:{filter:{integration:T}}}},{name:"name",selector:{text:{}}},{name:"flow",type:"expandable",flatten:!0,iconPath:u2,title:u(this.hass,"editor_flow"),schema:[{name:"solar_power",selector:C},{name:"home_power",selector:C},{name:"grid_import_power",selector:C},{name:"grid_export_power",selector:C},{name:"battery_power",selector:C},{name:"battery_charging_positive",selector:{boolean:{}}},{name:"battery_soc",selector:{entity:{filter:{domain:"sensor",device_class:"battery"}}}},{name:"home_includes_wallbox",selector:{boolean:{}}}]},{name:"content",type:"expandable",flatten:!0,iconPath:Z2,title:u(this.hass,"editor_content"),schema:[{name:"show_session",selector:{boolean:{}}},{name:"show_progress",selector:{boolean:{}}},{name:"show_controls",selector:{boolean:{}}},{name:"show_last_session",selector:{boolean:{}}}]}]}_valueChanged(C){let V={...C.detail.value};for(let[M,r]of Object.entries(U2))V[M]===r&&delete V[M];for(let M of O5)V[M]||delete V[M];this.dispatchEvent(new CustomEvent("config-changed",{detail:{config:V},bubbles:!0,composed:!0}))}};e1.properties={hass:{attribute:!1},_config:{state:!0}};_("thor-wallbox-card-editor",e1);function Q2(L){let H=Math.max(0,L.battery??0),C=Math.max(0,-(L.battery??0)),V;L.home!==void 0?V=Math.max(0,L.home-(L.homeIncludesWallbox?L.wallbox:0)):L.solar!==void 0&&L.gridImport!==void 0&&L.gridExport!==void 0&&(V=Math.max(0,L.solar+L.gridImport+H-L.gridExport-C-L.wallbox));let M;L.gridExport!==void 0?M=Math.max(0,L.gridExport-(L.gridImport??0)):L.solar!==void 0&&V!==void 0&&(M=Math.max(0,L.solar-V-C));let r=0,e=0,i=0;if(L.charging){let A=Math.max(0,(L.solar??0)-C-(L.gridExport??0)),o=V??0,a=Math.min(o,A);o-=a,r=Math.min(L.wallbox,A-a);let m=Math.min(o,H);e=Math.min(L.wallbox-r,H-m),i=Math.max(0,L.wallbox-r-e),L.gridImport!==void 0&&(i=Math.min(i,L.gridImport))}let t=Math.min(C,Math.max(0,(L.solar??0)-(L.gridExport??0)));return{fromSolar:r,fromBattery:e,fromGrid:i,surplus:M,batteryCharging:C,batteryDischarging:H,batteryFromSolar:t}}var z2=$`
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
  /* The scheduled start row: a button that looks like the select rows and opens the
     booking dialog. */
  button.select {
    width: 100%;
    border: none;
    background: none;
    font-family: inherit;
    font-size: inherit;
    text-align: start;
    cursor: pointer;
    outline: none;
  }
  button.select:focus-visible {
    box-shadow: 0 0 0 2px var(--tile-color);
  }
  /* A tap focuses the button too: the ring is only for the keyboard. */
  button.select:focus:not(:focus-visible) {
    box-shadow: none;
  }
  .select.schedule .current {
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  .features .note {
    padding: 0 4px;
  }
`;var f5={charging:"var(--success-color, #43a047)",suspended_ev:"var(--warning-color, #ffa600)",suspended_evse:"var(--warning-color, #ffa600)",preparing:"var(--info-color, #039be5)",finishing:"var(--teal-color, #009688)",reserved:"var(--purple-color, #926bc7)",faulted:"var(--error-color, #db4437)",available:"var(--state-inactive-color, #9e9e9e)"},b5="var(--state-unavailable-color, #bdbdbd)",X2="var(--energy-solar-color, #ff9800)",k5="var(--energy-grid-consumption-color, #488fc2)",Y2="var(--deep-purple-color, #6e41ab)",_1={fast:{icon:x2,color:"var(--primary-color, #009ac7)"},pv_linkage:{icon:M1,color:X2},off_peak:{icon:O1,color:Y2}},y5=["","unknown","unavailable","NoError"],h=50,K2=6,w5=.75,J2=7400;function j2(L,H=J2){let C=Math.max(1,H-h),V=Math.min(1,Math.max(0,(L-h)/C)),M=K2-V*(K2-w5);return Math.round(M*4)/4}function B5(L){switch(L){case"EUR":return n2;case"USD":return v2;case"GBP":return l2;default:return A2}}var P5=24;function l(L,H=24){return p`<svg viewBox="0 0 24 24" width=${H} height=${H} aria-hidden="true">
    <path d=${L}></path>
  </svg>`}function F(L){return L!==void 0&&!y5.includes(L)}var X=class extends S{constructor(){super();this._ids=new Map;this._openBooking=()=>{let C=this._obj("sensor.next_reservation"),V=C&&F(C.state)?D2(C.state,C.attributes,this.hass.config?.time_zone):void 0,M=V??{start:this._state("select.start_mode"),time:K(this._state("time.start_time")),limit:this._state("select.charge_limit"),energy:Z(this._obj("number.limit_energy")),cost:Z(this._obj("number.limit_cost")),duration:Z(this._obj("number.limit_duration"))};this._booking={form:E2(M,this._rfid()),replaces:V!==void 0}};this._bookingClosed=()=>{this._booking=void 0};this._modeChanged=C=>{let V=C.target,M=this._id("select.charge_mode"),r=this._state("select.charge_mode")??"",e=V.value;V.value=r,M&&e!==r&&this._call("select","select_option",M,{option:e})};this._moreInfo=()=>{let C=this._id("sensor.status");C&&this.dispatchEvent(new CustomEvent("hass-more-info",{detail:{entityId:C},bubbles:!0,composed:!0}))};this._tileKeydown=C=>{(C.key==="Enter"||C.key===" ")&&(C.preventDefault(),this._moreInfo())};this._busy=!1}static getConfigElement(){return document.createElement("thor-wallbox-card-editor")}static getStubConfig(C){let[V]=I2(C);return V?{device_id:V}:{}}setConfig(C){if(!C)throw new Error("Invalid configuration");this._config={...C}}getCardSize(){return 7}getGridOptions(){return{columns:12,min_columns:6}}connectedCallback(){super.connectedCallback(),this.hasUpdated&&this.requestUpdate()}disconnectedCallback(){super.disconnectedCallback(),this._resizeObserver?.disconnect(),this._observedFlow=void 0}updated(C){super.updated(C);let V=this.renderRoot.querySelector(".flow")??void 0;V!==this._observedFlow&&(this._resizeObserver??=new ResizeObserver(()=>this._measureLinks()),this._resizeObserver.disconnect(),V&&this._resizeObserver.observe(V),this._observedFlow=V),this._measureLinks()}shouldUpdate(C){if(C.has("_config")||C.has("_links")||C.has("_booking")||C.has("_busy")||!this.hass)return!0;let V=C.get("hass");return!V||V.entities!==this.hass.entities||V.devices!==this.hass.devices||V.config!==this.hass.config||V.locale!==this.hass.locale||V.language!==this.hass.language||V.themes!==this.hass.themes?!0:this._watched().some(M=>V.states[M]!==this.hass.states[M])}_watched(){let C=this._config,V=[...this._entityIds().values()];for(let M of[C?.solar_power,C?.home_power,C?.grid_import_power,C?.grid_export_power,C?.battery_power,C?.battery_soc])M&&V.push(M);return V}_entityIds(){let C=this.hass,V=this._config?.device_id;return(this._idsSource?.entities!==C.entities||this._idsSource?.device!==V)&&(this._ids=G2(C,V),this._idsSource={entities:C.entities,device:V}),this._ids}_id(C){return this._entityIds().get(C)}_obj(C){let V=this._id(C);return V?this.hass.states[V]:void 0}_state(C){return this._obj(C)?.state}_available(C){let V=this._state(C);return V!==void 0&&V!=="unavailable"}_configured(C){return C?this.hass.states[C]:void 0}_t(C,V){return u(this.hass,C,V)}render(){if(!this._config||!this.hass)return d;if(!this._config.device_id)return this._renderMessage(this._t("no_device"));let C=this._obj("sensor.status");if(!C)return this._renderMessage(this._t("device_not_found"));let V=C.state,M=this._state("select.charge_mode"),r=V==="unavailable",e=W2.includes(V),i=w(this._obj("sensor.power")),t=[`--tile-color: ${f5[V]??b5}`,`--mode-color: ${M&&_1[M]?.color||"var(--primary-color)"}`].join("; ");return p`
      <ha-card style=${t}>
        ${this._renderTile(C,V,M)}
        ${r||i===void 0?d:p`<div class="value" aria-label=${this._t("power")}>
              <span class="number">${x(this.hass,i/1e3,1)}</span>
              <span class="unit">kW</span>
            </div>`}
        ${this._alerts(V).map(A=>this._renderAlert(A))}
        ${r?d:this._renderFlow(V,M,i??0)}
        ${this._renderBadges(V,M,e)}
        ${this._renderFeatures(V,e)}
        ${this._booking?p`<thor-wallbox-booking
              .hass=${this.hass}
              .deviceId=${this._config.device_id}
              .form=${this._booking.form}
              .currency=${this._currency()}
              .rfid=${this._rfid()}
              .replaces=${this._booking.replaces}
              @closed=${this._bookingClosed}
            ></thor-wallbox-booking>`:d}
      </ha-card>
    `}_renderMessage(C){return p`<ha-card><div class="message">${C}</div></ha-card>`}_renderTile(C,V,M){let r=this.hass,e=r.devices?.[this._config.device_id],i=this._config.name||e?.name_by_user||e?.name||"THOR",t=[r.formatEntityState(C),this._detail(V,M)].filter(Boolean).join(" \xB7 "),A=M?_1[M]?.icon:void 0;return p`
      <div
        class="tile"
        role="button"
        tabindex="0"
        @click=${this._moreInfo}
        @keydown=${this._tileKeydown}
      >
        <div class="tile-icon">
          <div class="shape">${l(L1)}</div>
          ${A?p`<div class="tile-badge">${l(A,12)}</div>`:d}
        </div>
        <div class="tile-info">
          <span class="primary">${i}</span>
          <span class="secondary">${t}</span>
        </div>
      </div>
    `}_detail(C,V){let M=this.hass;switch(C){case"charging":{let r=Z(this._obj("sensor.current")),e=Z(this._obj("sensor.voltage"));return[r===void 0?"":`${x(M,r,1)} A`,e===void 0?"":`${x(M,e,0)} V`].filter(Boolean).join(" \xB7 ")}case"available":return this._t("plug_in");case"preparing":return this._t("car_connected");case"suspended_evse":return V==="pv_linkage"?this._t("waiting_surplus"):V==="off_peak"?this._t("waiting_slot"):"";case"reserved":return this._reservation()??"";case"faulted":{let r=this._state("sensor.error_code");return F(r)?r:""}default:return""}}_reservation(){let C=this.hass,V=this._obj("sensor.next_reservation");if(!V||!F(V.state))return;let M=new Date(V.state);return V.attributes.every_day&&!Number.isNaN(M.getTime())?this._t("every_day",{time:f1(C,M)}):C.formatEntityState(V)}_alerts(C){let V=[];if(C==="unavailable"&&V.push({icon:p2,color:"var(--warning-color, #ffa600)",title:this._t("offline_title"),text:this._t("offline_text")}),C==="faulted"){let M=this._state("sensor.error_code"),r=this._state("sensor.vendor_error_code");V.push({icon:H2,color:"var(--error-color, #db4437)",title:F(M)?`${this._t("fault")}: ${M}`:this._t("fault"),text:[F(r)?this._t("vendor_code",{code:r}):"",this._t("fault_hint")].filter(Boolean).join(" ")})}return this._state("select.authorization_mode")==="rfid"&&["available","preparing"].includes(C)&&V.push({icon:m2,color:"var(--info-color, #039be5)",title:this._t("rfid_title"),text:this._t("rfid_text")}),V}_renderAlert(C){return p`
      <div class="alert" style=${`--alert-color: ${C.color}`}>
        ${l(C.icon)}
        <div class="text">
          <div class="title">${C.title}</div>
          <div>${C.text}</div>
        </div>
      </div>
    `}_renderFlow(C,V,M){let r=this._config,e=!!r.solar_power,i=!!(r.grid_import_power||r.grid_export_power),t=!!r.battery_power;if(!e&&!i&&!t)return d;let A=this.hass,o=w(this._configured(r.solar_power)),a=w(this._configured(r.grid_import_power)),m=w(this._configured(r.grid_export_power)),n=w(this._configured(r.battery_power)),v=C==="charging"&&M>h,s=Q2({wallbox:M,charging:v,solar:o,gridImport:a,gridExport:m,home:w(this._configured(r.home_power)),homeIncludesWallbox:r.home_includes_wallbox!==!1,battery:n===void 0?void 0:r.battery_charging_positive?-n:n}),t1=Z(this._configured(r.battery_soc)),R=[];if(v){let D=[s.fromSolar>h?this._t("from_solar",{value:c(A,s.fromSolar)}):"",s.fromBattery>h?this._t("from_battery",{value:c(A,s.fromBattery)}):"",s.fromGrid>h?this._t("from_grid",{value:c(A,s.fromGrid)}):""].filter(Boolean);if(D.length){let F1=D.join(", ");R.push(`${F1.charAt(0).toUpperCase()}${F1.slice(1)}.`)}}else V==="pv_linkage"&&(s.surplus!==void 0&&R.push(this._t("surplus",{value:c(A,s.surplus)})),s.batteryFromSolar>h&&R.push(t1===void 0?this._t("battery_charging",{value:c(A,s.batteryCharging)}):this._t("battery_charging_soc",{value:c(A,s.batteryCharging),soc:`${x(A,t1,0)} %`})));let Y=D=>D===void 0?"-":c(A,D),C5=p`<div class="node spacer"></div><div class="line spacer"></div>`;return p`
      <div class="flow">
        <div class="row">
          ${e?p`
                <div class="node solar">
                  <span class="label">${this._t("solar")}</span>
                  <div class="circle">${l(M1)}<span>${Y(o)}</span></div>
                </div>
                ${this._renderLine("solar",s.fromSolar,!1)}
              `:C5}
          <div class="node wallbox">
            <span class="label">${this._t("wallbox")}</span>
            <div class="circle">${l(L1)}<span>${c(A,M)}</span></div>
          </div>
          ${i?p`
                ${this._renderLine("grid",s.fromGrid,!0)}
                <div class="node grid">
                  <span class="label">${this._t("grid")}</span>
                  <div class="circle">
                    ${l(h1)}
                    ${r.grid_export_power?p`<span class="import">${l(L2,12)}${Y(a)}</span>
                          <span class="export">${l(M2,12)}${Y(m)}</span>`:p`<span>${Y(a)}</span>`}
                  </div>
                </div>
              `:p`<div class="line spacer"></div><div class="node spacer"></div>`}
        </div>
        ${t?this._renderBattery(s,t1):d}
        ${R.length?p`<p class="note">${R.join(" ")}</p>`:d}
        ${t&&this._links?this._renderLinks(this._links,s):d}
      </div>
    `}_renderBattery(C,V){let M=this.hass,r=e2;V!==void 0&&(V<10?r=o2:V<=32.5?r=t2:V<=72.5&&(r=i2));let e=p`<span>${c(M,0)}</span>`;return C.batteryDischarging>h?e=p`<span class="discharging">${l(r2,12)}${c(M,C.batteryDischarging)}</span>`:C.batteryCharging>h&&(e=p`<span class="charging">${l(V2,12)}${c(M,C.batteryCharging)}</span>`),p`
      <div class="node battery">
        <div class="circle">
          ${l(r)}
          ${V===void 0?d:p`<span>${x(M,V,0)} %</span>`}
          ${e}
        </div>
        <span class="label">${this._t("battery")}</span>
      </div>
    `}_measureLinks(){let C=this.renderRoot.querySelector(".flow"),V=i=>C?.querySelector(`.node.${i} .circle`)??void 0,M=V("battery"),r=V("wallbox"),e;if(M&&r&&M.offsetWidth){let i=m=>Math.round(m.offsetLeft+m.offsetWidth/2)+.5,t=m=>m.offsetTop+m.offsetHeight,A=Math.round(M.offsetTop+M.offsetHeight/2)+.5,o=V("solar"),a;if(o){let m=i(o),n=t(o),v=Math.max(0,Math.min(P5,A-n,M.offsetLeft-m));a=`M${m} ${n}V${A-v}A${v} ${v} 0 0 0 ${m+v} ${A}H${M.offsetLeft}`}e={wallbox:`M${i(M)} ${M.offsetTop}V${t(r)}`,solar:a}}JSON.stringify(e)!==JSON.stringify(this._links)&&(this._links=e)}_fullPower(){let C=Number(this._obj("number.import_grid_power")?.attributes.max);return Number.isFinite(C)&&C>0?C*1e3:J2}_renderLinks(C,V){let M=window.matchMedia?.("(prefers-reduced-motion: reduce)").matches,r=this._fullPower(),e=(i,t,A)=>{if(!i)return d;let o=A>h,a=M?"0.5;0.5":"0;1";return s1`
        <g class="link ${t} ${o?"active":""}">
          <path d=${i}></path>
          ${o?s1`<circle r="2.5">
                <animateMotion
                  path=${i}
                  dur="${j2(A,r)}s"
                  repeatCount="indefinite"
                  calcMode="linear"
                  keyPoints=${a}
                  keyTimes="0;1"
                ></animateMotion>
              </circle>`:d}
        </g>
      `};return p`
      <svg class="links" aria-hidden="true">
        ${e(C.wallbox,"battery-out",V.fromBattery)}
        ${e(C.solar,"battery-in",V.batteryFromSolar)}
      </svg>
    `}_renderLine(C,V,M){let r=V>h;return p`
      <div
        class="line ${C} ${r?"active":""} ${M?"reverse":""}"
        style=${r?`--flow-duration: ${j2(V,this._fullPower())}s`:""}
      >
        <div class="track">${r?p`<span class="dot"></span>`:d}</div>
      </div>
    `}_badges(C,V,M){let r=this.hass,e=this._config,i=[];if(M&&e.show_session!==!1){let o=Z(this._obj("sensor.session_energy")),a=Z(this._obj("sensor.session_duration")),m=this._obj("sensor.session_cost");o!==void 0&&i.push({icon:S2,label:this._t("energy"),text:`${x(r,o,2)} kWh`}),a!==void 0&&i.push({icon:k2,label:this._t("duration"),text:z(a)}),m&&Z(m)!==void 0&&i.push({icon:B5(m.attributes.unit_of_measurement),label:this._t("cost"),text:r.formatEntityState(m)})}if(!M&&e.show_last_session!==!1){let o=new Date(this._state("sensor.last_session")??""),a=Z(this._obj("sensor.last_session_energy"));Number.isNaN(o.getTime())||i.push({icon:s2,label:this._t("last_session"),text:[T2(r,o),a===void 0?"":`${x(r,a,2)} kWh`].filter(Boolean).join(" \xB7 ")})}let t=this._state("binary_sensor.cable_lock");if(t==="off"?i.push({icon:c2,text:this._t("cable_locked")}):t==="on"&&i.push({icon:c1,text:this._t("cable_unlocked")}),V==="pv_linkage"){let o=this._state("switch.import_grid"),a=Z(this._obj("number.import_grid_power"));o==="on"?i.push({icon:h1,color:k5,text:a===void 0?this._t("grid_import"):this._t("grid_import_power",{power:`${x(r,a,1)} kW`})}):o==="off"&&i.push({icon:M1,color:X2,text:this._t("surplus_only")})}if(this._state("switch.boost")==="on"){let o=this._obj("select.boost_type");i.push({icon:g2,color:"var(--primary-color, #009ac7)",text:o&&F(o.state)?this._t("boost",{type:r.formatEntityState(o)}):"Boost"})}if(V==="off_peak"){let o=[1,2,3].map(a=>[K(this._state(`time.off_peak_${a}_from`)),K(this._state(`time.off_peak_${a}_to`))]).filter(([a,m])=>a&&m&&a!==m).map(([a,m])=>`${a}-${m}`);o.length&&i.push({icon:O1,color:Y2,label:this._t("slots"),text:o.join(", ")})}let A=C==="reserved"||this._canSchedule(C,V,M)?void 0:this._reservation();return A&&i.push({icon:S1,color:"var(--purple-color, #926bc7)",label:this._t("scheduled_start"),text:A}),C==="suspended_ev"&&this._state("switch.warm_up")==="on"&&i.push({icon:b2,color:"var(--deep-orange-color, #ff6f22)",text:this._t("warm_up")}),i}_renderBadges(C,V,M){let r=this._badges(C,V,M);return r.length?p`
      <div class="badges">
        ${r.map(e=>p`
            <div class="badge" style=${e.color?`--badge-color: ${e.color}`:""}>
              ${l(e.icon,18)}
              <div class="info">
                ${e.label?p`<span class="label">${e.label}</span>`:d}
                <span class="content">${e.text}</span>
              </div>
            </div>
          `)}
      </div>
    `:d}_renderFeatures(C,V){let M=this._config,r=M.show_progress===!1?d:this._renderProgress(),e=M.show_controls===!1?d:this._renderControls(C,V);return r===d&&e===d?d:p`<div class="features">${r}${e}</div>`}_renderProgress(){let C=this.hass,V=Z(this._obj("sensor.session_progress"));if(V===void 0)return d;let M=this._progressCaption(),r=Math.min(100,Math.max(0,V));return p`
      <div class="progress">
        <div class="caption">
          <span>${M}</span>
          <span class="pct">${x(C,V,0)} %</span>
        </div>
        <div
          class="bar"
          role="progressbar"
          aria-label=${M}
          aria-valuenow=${r}
          aria-valuemin="0"
          aria-valuemax="100"
        >
          <div class="done" style=${`width: ${r}%`}></div>
          <div class="rest"></div>
        </div>
      </div>
    `}_progressCaption(){let C=this.hass,V=this._obj("sensor.session_limit"),M=V?.state;if(M==="energy"||M==="cost"||M==="duration"){let A=this._t(`limit_${M}`),o=V?.attributes.value,a=this._obj(`sensor.session_${M}`),m=Z(a);if(m===void 0||typeof o!="number")return A;let n=v=>M==="duration"?z(v):M==="energy"?`${x(C,v,1)} kWh`:`${x(C,v,2)} ${a?.attributes.unit_of_measurement??""}`.trim();return`${A} \xB7 ${this._t("done_of",{done:n(m),target:n(o)})}`}let r=K(this._state("time.boost_departure")),e=r?this._t("boost_by",{time:r}):"Boost",i=Z(this._obj("sensor.session_energy")),t=Z(this._obj("number.boost_energy"));return i===void 0||t===void 0?e:`${e} \xB7 ${this._t("done_of",{done:`${x(C,i,1)} kWh`,target:`${x(C,t,1)} kWh`})}`}_renderControls(C,V){let M=C==="unavailable",r=this._rfid(),e=this._state("select.charge_mode"),i=this._id("switch.charging"),t=this._id("button.cancel_reservation"),A=this._id("button.unlock"),o=[];if(t&&this._available("button.cancel_reservation"))o.push({icon:a2,label:this._t("cancel"),disabled:M,action:()=>this._call("button","press",t)});else if(i){let n=!M&&this._available("switch.charging");T1.includes(C)?o.push({icon:f2,label:this._t("stop"),disabled:r||!n,action:()=>this._call("switch","turn_off",i)}):o.push({icon:O2,label:this._t("start"),disabled:r||!n||!["available","preparing"].includes(C),action:()=>this._call("switch","turn_on",i)})}A&&o.push({icon:c1,label:this._t("unlock"),disabled:M||!this._available("button.unlock"),action:()=>this._call("button","press",A)});let a=this._obj("select.charge_mode"),m=this._canSchedule(C,e,V);return!o.length&&!a&&!m?d:p`
      ${o.length?p`<div class="buttons">
            ${o.map(n=>p`
                <button class="button" type="button" ?disabled=${n.disabled||this._busy} @click=${n.action}>
                  ${l(n.icon,20)}
                  <span>${n.label}</span>
                </button>
              `)}
          </div>`:d}
      ${m?this._renderSchedule():d}
      ${a?this._renderModeSelect(a,V||M||this._busy):d}
      ${V?p`<p class="note">${this._t("locked_note")}</p>`:d}
    `}_rfid(){return this._state("select.authorization_mode")==="rfid"}_currency(){return this._obj("number.limit_cost")?.attributes.unit_of_measurement??this._obj("sensor.session_cost")?.attributes.unit_of_measurement}_canSchedule(C,V,M){return this._config.show_controls!==!1&&V==="fast"&&!M&&C!=="unavailable"&&C!=="faulted"}_renderSchedule(){let C=this.hass,V=this._reservation(),M=this._t("schedule");if(V){let r=this._obj("sensor.next_reservation")?.attributes??{},e=typeof r.limit=="string"&&typeof r.limit_value=="number"?P1(C,r.limit,r.limit_value,this._currency()):"";M=[V,e].filter(Boolean).join(" \xB7 ")}return p`
      <button class="select schedule" type="button" @click=${this._openBooking}>
        ${l(S1,20)}
        <div class="content">
          <span class="label">${this._t("scheduled_start")}</span>
          <span class="current">${M}</span>
        </div>
        ${l(d2,20)}
      </button>
    `}_renderModeSelect(C,V){let M=this.hass,r=C.state,e=C.attributes.options??[],i=V||r==="unavailable";return p`
      <div class="select ${i?"disabled":""}">
        ${l(_1[r]?.icon??L1,20)}
        <div class="content">
          <span class="label">${this._t("charge_mode")}</span>
          <span class="current">${M.formatEntityState(C)}</span>
        </div>
        ${l(h2,20)}
        <select aria-label=${this._t("charge_mode")} ?disabled=${i} @change=${this._modeChanged}>
          ${e.map(t=>p`<option value=${t} ?selected=${t===r}>
                ${M.formatEntityState(C,t)}
              </option>`)}
        </select>
      </div>
    `}async _call(C,V,M,r={}){if(!this._busy){this._busy=!0;try{await this.hass.callService(C,V,{entity_id:M,...r})}catch(e){let i=e?.message??String(e);this.dispatchEvent(new CustomEvent("hass-notification",{detail:{message:i},bubbles:!0,composed:!0}))}finally{this._busy=!1}}}};X.styles=z2,X.properties={hass:{attribute:!1},_config:{state:!0},_links:{state:!0},_booking:{state:!0},_busy:{state:!0}};_("thor-wallbox-card",X);var q2=window.customCards??=[];q2.some(L=>L.type==="thor-wallbox-card")||q2.push({type:"thor-wallbox-card",name:u(void 0,"card_name"),description:u(void 0,"card_description"),preview:!0,documentationURL:"https://github.com/fabioscarparo/ha-growatt-thor-cloud#wallbox-card"});console.info("%c THOR-WALLBOX-CARD %c 0.11.1 ","color: #fff; background: #43a047","");
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
