var ue=(e,t)=>()=>(t||e((t={exports:{}}).exports,t),t.exports);var Ee=ue((Fe,T)=>{var de=Object.defineProperty,l=(e,t)=>de(e,"name",{value:t,configurable:!0}),M=(e=>typeof require<"u"?require:typeof Proxy<"u"?new Proxy(e,{get:(t,i)=>(typeof require<"u"?require:t)[i]}):e)(function(e){if(typeof require<"u")return require.apply(this,arguments);throw new Error('Dynamic require of "'+e+'" is not supported')});function C(e){return!isNaN(parseFloat(e))&&isFinite(e)}l(C,"_isNumber");function w(e){return e.charAt(0).toUpperCase()+e.substring(1)}l(w,"_capitalize");function R(e){return function(){return this[e]}}l(R,"_getter");var F=["isConstructor","isEval","isNative","isToplevel"],O=["columnNumber","lineNumber"],k=["fileName","functionName","source"],fe=["args"],pe=["evalOrigin"],x=F.concat(O,k,fe,pe);function m(e){if(e)for(var t=0;t<x.length;t++)e[x[t]]!==void 0&&this["set"+w(x[t])](e[x[t]])}l(m,"StackFrame");m.prototype={getArgs:function(){return this.args},setArgs:function(e){if(Object.prototype.toString.call(e)!=="[object Array]")throw new TypeError("Args must be an Array");this.args=e},getEvalOrigin:function(){return this.evalOrigin},setEvalOrigin:function(e){if(e instanceof m)this.evalOrigin=e;else if(e instanceof Object)this.evalOrigin=new m(e);else throw new TypeError("Eval Origin must be an Object or StackFrame")},toString:function(){var e=this.getFileName()||"",t=this.getLineNumber()||"",i=this.getColumnNumber()||"",a=this.getFunctionName()||"";return this.getIsEval()?e?"[eval] ("+e+":"+t+":"+i+")":"[eval]:"+t+":"+i:a?a+" ("+e+":"+t+":"+i+")":e+":"+t+":"+i}};m.fromString=l(function(e){var t=e.indexOf("("),i=e.lastIndexOf(")"),a=e.substring(0,t),o=e.substring(t+1,i).split(","),r=e.substring(i+1);if(r.indexOf("@")===0)var n=/@(.+?)(?::(\d+))?(?::(\d+))?$/.exec(r,""),s=n[1],c=n[2],u=n[3];return new m({functionName:a,args:o||void 0,fileName:s,lineNumber:c||void 0,columnNumber:u||void 0})},"StackFrame$$fromString");for(g=0;g<F.length;g++)m.prototype["get"+w(F[g])]=R(F[g]),m.prototype["set"+w(F[g])]=function(e){return function(t){this[e]=!!t}}(F[g]);var g;for(v=0;v<O.length;v++)m.prototype["get"+w(O[v])]=R(O[v]),m.prototype["set"+w(O[v])]=function(e){return function(t){if(!C(t))throw new TypeError(e+" must be a Number");this[e]=Number(t)}}(O[v]);var v;for(b=0;b<k.length;b++)m.prototype["get"+w(k[b])]=R(k[b]),m.prototype["set"+w(k[b])]=function(e){return function(t){this[e]=String(t)}}(k[b]);var b,_=m;function H(){var e=/^\s*at .*(\S+:\d+|\(native\))/m,t=/^(eval@)?(\[native code])?$/;return{parse:l(function(i){if(i.stack&&i.stack.match(e))return this.parseV8OrIE(i);if(i.stack)return this.parseFFOrSafari(i);throw new Error("Cannot parse given Error object")},"ErrorStackParser$$parse"),extractLocation:l(function(i){if(i.indexOf(":")===-1)return[i];var a=/(.+?)(?::(\d+))?(?::(\d+))?$/,o=a.exec(i.replace(/[()]/g,""));return[o[1],o[2]||void 0,o[3]||void 0]},"ErrorStackParser$$extractLocation"),parseV8OrIE:l(function(i){var a=i.stack.split(`
`).filter(function(o){return!!o.match(e)},this);return a.map(function(o){o.indexOf("(eval ")>-1&&(o=o.replace(/eval code/g,"eval").replace(/(\(eval at [^()]*)|(,.*$)/g,""));var r=o.replace(/^\s+/,"").replace(/\(eval code/g,"(").replace(/^.*?\s+/,""),n=r.match(/ (\(.+\)$)/);r=n?r.replace(n[0],""):r;var s=this.extractLocation(n?n[1]:r),c=n&&r||void 0,u=["eval","<anonymous>"].indexOf(s[0])>-1?void 0:s[0];return new _({functionName:c,fileName:u,lineNumber:s[1],columnNumber:s[2],source:o})},this)},"ErrorStackParser$$parseV8OrIE"),parseFFOrSafari:l(function(i){var a=i.stack.split(`
`).filter(function(o){return!o.match(t)},this);return a.map(function(o){if(o.indexOf(" > eval")>-1&&(o=o.replace(/ line (\d+)(?: > eval line \d+)* > eval:\d+:\d+/g,":$1")),o.indexOf("@")===-1&&o.indexOf(":")===-1)return new _({functionName:o});var r=/((.*".+"[^@]*)?[^@]*)(?:@)/,n=o.match(r),s=n&&n[1]?n[1]:void 0,c=this.extractLocation(o.replace(r,""));return new _({functionName:s,fileName:c[0],lineNumber:c[1],columnNumber:c[2],source:o})},this)},"ErrorStackParser$$parseFFOrSafari")}}l(H,"ErrorStackParser");var me=new H,ye=me,y=typeof process=="object"&&typeof process.versions=="object"&&typeof process.versions.node=="string"&&!process.browser,q=y&&typeof T<"u"&&typeof T.exports<"u"&&typeof M<"u"&&typeof __dirname<"u",we=y&&!q,he=typeof Deno<"u",W=!y&&!he,ge=W&&typeof window=="object"&&typeof document=="object"&&typeof document.createElement=="function"&&typeof sessionStorage=="object"&&typeof importScripts!="function",ve=W&&typeof importScripts=="function"&&typeof self=="object";typeof navigator=="object"&&typeof navigator.userAgent=="string"&&navigator.userAgent.indexOf("Chrome")==-1&&navigator.userAgent.indexOf("Safari")>-1;var z,D,B,A,$;async function j(){if(!y||(z=(await import("./__vite-browser-external-dfc062b5.js")).default,A=await import("./__vite-browser-external-dfc062b5.js"),$=await import("./__vite-browser-external-dfc062b5.js"),B=(await import("./__vite-browser-external-dfc062b5.js")).default,D=await import("./__vite-browser-external-dfc062b5.js"),I=D.sep,typeof M<"u"))return;let e=A,t=await import("./__vite-browser-external-dfc062b5.js"),i=await import("./__vite-browser-external-dfc062b5.js"),a=await import("./__vite-browser-external-dfc062b5.js"),o={fs:e,crypto:t,ws:i,child_process:a};globalThis.require=function(r){return o[r]}}l(j,"initNodeModules");function V(e,t){return D.resolve(t||".",e)}l(V,"node_resolvePath");function Y(e,t){return t===void 0&&(t=location),new URL(e,t).toString()}l(Y,"browser_resolvePath");var P;y?P=V:P=Y;var I;y||(I="/");function J(e,t){return e.startsWith("file://")&&(e=e.slice(7)),e.includes("://")?{response:fetch(e)}:{binary:$.readFile(e).then(i=>new Uint8Array(i.buffer,i.byteOffset,i.byteLength))}}l(J,"node_getBinaryResponse");function G(e,t){let i=new URL(e,location);return{response:fetch(i,t?{integrity:t}:{})}}l(G,"browser_getBinaryResponse");var N;y?N=J:N=G;async function K(e,t){let{response:i,binary:a}=N(e,t);if(a)return a;let o=await i;if(!o.ok)throw new Error(`Failed to load '${e}': request failed.`);return new Uint8Array(await o.arrayBuffer())}l(K,"loadBinaryFile");var L;if(ge)L=l(async e=>await import(e),"loadScript");else if(ve)L=l(async e=>{try{globalThis.importScripts(e)}catch(t){if(t instanceof TypeError)await import(e);else throw t}},"loadScript");else if(y)L=Q;else throw new Error("Cannot determine runtime environment");async function Q(e){e.startsWith("file://")&&(e=e.slice(7)),e.includes("://")?B.runInThisContext(await(await fetch(e)).text()):await import(z.pathToFileURL(e).href)}l(Q,"nodeLoadScript");async function X(e){if(y){await j();let t=await $.readFile(e,{encoding:"utf8"});return JSON.parse(t)}else return await(await fetch(e)).json()}l(X,"loadLockFile");async function Z(){if(q)return __dirname;let e;try{throw new Error}catch(a){e=a}let t=ye.parse(e)[0].fileName;if(y&&!t.startsWith("file://")&&(t=`file://${t}`),we){let a=await import("./__vite-browser-external-dfc062b5.js");return(await import("./__vite-browser-external-dfc062b5.js")).fileURLToPath(a.dirname(t))}let i=t.lastIndexOf(I);if(i===-1)throw new Error("Could not extract indexURL path from pyodide module location");return t.slice(0,i)}l(Z,"calculateDirname");function ee(e){let t=e.FS,i=e.FS.filesystems.MEMFS,a=e.PATH,o={DIR_MODE:16895,FILE_MODE:33279,mount:function(r){if(!r.opts.fileSystemHandle)throw new Error("opts.fileSystemHandle is required");return i.mount.apply(null,arguments)},syncfs:async(r,n,s)=>{try{let c=o.getLocalSet(r),u=await o.getRemoteSet(r),d=n?u:c,p=n?c:u;await o.reconcile(r,d,p),s(null)}catch(c){s(c)}},getLocalSet:r=>{let n=Object.create(null);function s(d){return d!=="."&&d!==".."}l(s,"isRealDir");function c(d){return p=>a.join2(d,p)}l(c,"toAbsolute");let u=t.readdir(r.mountpoint).filter(s).map(c(r.mountpoint));for(;u.length;){let d=u.pop(),p=t.stat(d);t.isDir(p.mode)&&u.push.apply(u,t.readdir(d).filter(s).map(c(d))),n[d]={timestamp:p.mtime,mode:p.mode}}return{type:"local",entries:n}},getRemoteSet:async r=>{let n=Object.create(null),s=await be(r.opts.fileSystemHandle);for(let[c,u]of s)c!=="."&&(n[a.join2(r.mountpoint,c)]={timestamp:u.kind==="file"?(await u.getFile()).lastModifiedDate:new Date,mode:u.kind==="file"?o.FILE_MODE:o.DIR_MODE});return{type:"remote",entries:n,handles:s}},loadLocalEntry:r=>{let n=t.lookupPath(r).node,s=t.stat(r);if(t.isDir(s.mode))return{timestamp:s.mtime,mode:s.mode};if(t.isFile(s.mode))return n.contents=i.getFileDataAsTypedArray(n),{timestamp:s.mtime,mode:s.mode,contents:n.contents};throw new Error("node type not supported")},storeLocalEntry:(r,n)=>{if(t.isDir(n.mode))t.mkdirTree(r,n.mode);else if(t.isFile(n.mode))t.writeFile(r,n.contents,{canOwn:!0});else throw new Error("node type not supported");t.chmod(r,n.mode),t.utime(r,n.timestamp,n.timestamp)},removeLocalEntry:r=>{var n=t.stat(r);t.isDir(n.mode)?t.rmdir(r):t.isFile(n.mode)&&t.unlink(r)},loadRemoteEntry:async r=>{if(r.kind==="file"){let n=await r.getFile();return{contents:new Uint8Array(await n.arrayBuffer()),mode:o.FILE_MODE,timestamp:n.lastModifiedDate}}else{if(r.kind==="directory")return{mode:o.DIR_MODE,timestamp:new Date};throw new Error("unknown kind: "+r.kind)}},storeRemoteEntry:async(r,n,s)=>{let c=r.get(a.dirname(n)),u=t.isFile(s.mode)?await c.getFileHandle(a.basename(n),{create:!0}):await c.getDirectoryHandle(a.basename(n),{create:!0});if(u.kind==="file"){let d=await u.createWritable();await d.write(s.contents),await d.close()}r.set(n,u)},removeRemoteEntry:async(r,n)=>{await r.get(a.dirname(n)).removeEntry(a.basename(n)),r.delete(n)},reconcile:async(r,n,s)=>{let c=0,u=[];Object.keys(n.entries).forEach(function(f){let h=n.entries[f],E=s.entries[f];(!E||t.isFile(h.mode)&&h.timestamp.getTime()>E.timestamp.getTime())&&(u.push(f),c++)}),u.sort();let d=[];if(Object.keys(s.entries).forEach(function(f){n.entries[f]||(d.push(f),c++)}),d.sort().reverse(),!c)return;let p=n.type==="remote"?n.handles:s.handles;for(let f of u){let h=a.normalize(f.replace(r.mountpoint,"/")).substring(1);if(s.type==="local"){let E=p.get(h),ce=await o.loadRemoteEntry(E);o.storeLocalEntry(f,ce)}else{let E=o.loadLocalEntry(f);await o.storeRemoteEntry(p,h,E)}}for(let f of d)if(s.type==="local")o.removeLocalEntry(f);else{let h=a.normalize(f.replace(r.mountpoint,"/")).substring(1);await o.removeRemoteEntry(p,h)}}};e.FS.filesystems.NATIVEFS_ASYNC=o}l(ee,"initializeNativeFS");var be=l(async e=>{let t=[];async function i(o){for await(let r of o.values())t.push(r),r.kind==="directory"&&await i(r)}l(i,"collect"),await i(e);let a=new Map;a.set(".",e);for(let o of t){let r=(await e.resolve(o)).join("/");a.set(r,o)}return a},"getFsHandles");function te(e){let t={noImageDecoding:!0,noAudioDecoding:!0,noWasmDecoding:!1,preRun:ae(e),quit(i,a){throw t.exited={status:i,toThrow:a},a},print:e.stdout,printErr:e.stderr,arguments:e.args,API:{config:e},locateFile:i=>e.indexURL+i,instantiateWasm:se(e.indexURL)};return t}l(te,"createSettings");function re(e){return function(t){let i="/";try{t.FS.mkdirTree(e)}catch(a){console.error(`Error occurred while making a home directory '${e}':`),console.error(a),console.error(`Using '${i}' for a home directory instead`),e=i}t.FS.chdir(e)}}l(re,"createHomeDirectory");function ie(e){return function(t){Object.assign(t.ENV,e)}}l(ie,"setEnvironment");function ne(e){return t=>{for(let i of e)t.FS.mkdirTree(i),t.FS.mount(t.FS.filesystems.NODEFS,{root:i},i)}}l(ne,"mountLocalDirectories");function oe(e){let t=K(e);return i=>{let a=i._py_version_major(),o=i._py_version_minor();i.FS.mkdirTree("/lib"),i.FS.mkdirTree(`/lib/python${a}.${o}/site-packages`),i.addRunDependency("install-stdlib"),t.then(r=>{i.FS.writeFile(`/lib/python${a}${o}.zip`,r)}).catch(r=>{console.error("Error occurred while installing the standard library:"),console.error(r)}).finally(()=>{i.removeRunDependency("install-stdlib")})}}l(oe,"installStdlib");function ae(e){let t;return e.stdLibURL!=null?t=e.stdLibURL:t=e.indexURL+"python_stdlib.zip",[oe(t),re(e.env.HOME),ie(e.env),ne(e._node_mounts),ee]}l(ae,"getFileSystemInitializationFuncs");function se(e){let{binary:t,response:i}=N(e+"pyodide.asm.wasm");return function(a,o){return async function(){try{let r;i?r=await WebAssembly.instantiateStreaming(i,a):r=await WebAssembly.instantiate(await t,a);let{instance:n,module:s}=r;typeof WasmOffsetConverter<"u"&&(wasmOffsetConverter=new WasmOffsetConverter(wasmBinary,s)),o(n,s)}catch(r){console.warn("wasm instantiation failed!"),console.warn(r)}}(),{}}}l(se,"getInstantiateWasmFunc");var U="0.26.3";async function le(e={}){var t,i;await j();let a=e.indexURL||await Z();a=P(a),a.endsWith("/")||(a+="/"),e.indexURL=a;let o={fullStdLib:!1,jsglobals:globalThis,stdin:globalThis.prompt?globalThis.prompt:void 0,lockFileURL:a+"pyodide-lock.json",args:[],_node_mounts:[],env:{},packageCacheDir:a,packages:[],enableRunUntilComplete:!1,checkAPIVersion:!0},r=Object.assign(o,e);(t=r.env).HOME??(t.HOME="/home/pyodide"),(i=r.env).PYTHONINSPECT??(i.PYTHONINSPECT="1");let n=te(r),s=n.API;if(s.lockFilePromise=X(r.lockFileURL),typeof _createPyodideModule!="function"){let f=`${r.indexURL}pyodide.asm.js`;await L(f)}let c;if(e._loadSnapshot){let f=await e._loadSnapshot;ArrayBuffer.isView(f)?c=f:c=new Uint8Array(f),n.noInitialRun=!0,n.INITIAL_MEMORY=c.length}let u=await _createPyodideModule(n);if(n.exited)throw n.exited.toThrow;if(e.pyproxyToStringRepr&&s.setPyProxyToStringMethod(!0),s.version!==U&&r.checkAPIVersion)throw new Error(`Pyodide version does not match: '${U}' <==> '${s.version}'. If you updated the Pyodide version, make sure you also updated the 'indexURL' parameter passed to loadPyodide.`);u.locateFile=f=>{throw new Error("Didn't expect to load any more file_packager files!")};let d;c&&(d=s.restoreSnapshot(c));let p=s.finalizeBootstrap(d);return s.sys.path.insert(0,s.config.env.HOME),p.version.includes("dev")||s.setCdnUrl(`https://cdn.jsdelivr.net/pyodide/v${p.version}/full/`),s._pyodide.set_excepthook(),await s.packageIndexReady,s.initializeStreams(r.stdin,r.stdout,r.stderr),p}l(le,"loadPyodide");let S;self.onmessage=async e=>{const{type:t}=e.data;try{switch(t){case"init":S||(self.postMessage({type:"status",payload:"loading"}),S=await le({indexURL:"https://cdn.jsdelivr.net/pyodide/v0.26.3/full"}),await S.loadPackage("micropip"),await S.pyimport("micropip").install("pqg"),self.postMessage({type:"status",payload:"ready"}));break;case"run":if(!S)throw new Error("Pyodide not initialized");self.postMessage({type:"result",payload:S.runPython(e.data.payload.code)});break;default:throw new Error(`Unknown message type: ${t}`)}}catch(i){self.postMessage({type:"error",payload:i instanceof Error?i.message:"Unknown error"})}}});export default Ee();
