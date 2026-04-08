var __defProp = Object.defineProperty;
var __getOwnPropNames = Object.getOwnPropertyNames;
var __require = /* @__PURE__ */ ((x) => typeof require !== "undefined" ? require : typeof Proxy !== "undefined" ? new Proxy(x, {
  get: (a, b) => (typeof require !== "undefined" ? require : a)[b]
}) : x)(function(x) {
  if (typeof require !== "undefined") return require.apply(this, arguments);
  throw Error('Dynamic require of "' + x + '" is not supported');
});
var __esm = (fn, res) => function __init() {
  return fn && (res = (0, fn[__getOwnPropNames(fn)[0]])(fn = 0)), res;
};
var __export = (target, all) => {
  for (var name in all)
    __defProp(target, name, { get: all[name], enumerable: true });
};

// node_modules/.pnpm/@jitl+quickjs-ffi-types@0.32.0/node_modules/@jitl/quickjs-ffi-types/dist/index.mjs
var EvalFlags, IntrinsicsFlags, JSPromiseStateEnum, GetOwnPropertyNamesFlags, IsEqualOp;
var init_dist = __esm({
  "node_modules/.pnpm/@jitl+quickjs-ffi-types@0.32.0/node_modules/@jitl/quickjs-ffi-types/dist/index.mjs"() {
    EvalFlags = { JS_EVAL_TYPE_GLOBAL: 0, JS_EVAL_TYPE_MODULE: 1, JS_EVAL_TYPE_DIRECT: 2, JS_EVAL_TYPE_INDIRECT: 3, JS_EVAL_TYPE_MASK: 3, JS_EVAL_FLAG_STRICT: 8, JS_EVAL_FLAG_STRIP: 16, JS_EVAL_FLAG_COMPILE_ONLY: 32, JS_EVAL_FLAG_BACKTRACE_BARRIER: 64 };
    IntrinsicsFlags = { BaseObjects: 1, Date: 2, Eval: 4, StringNormalize: 8, RegExp: 16, RegExpCompiler: 32, JSON: 64, Proxy: 128, MapSet: 256, TypedArrays: 512, Promise: 1024, BigInt: 2048, BigFloat: 4096, BigDecimal: 8192, OperatorOverloading: 16384, BignumExt: 32768 };
    JSPromiseStateEnum = { Pending: 0, Fulfilled: 1, Rejected: 2 };
    GetOwnPropertyNamesFlags = { JS_GPN_STRING_MASK: 1, JS_GPN_SYMBOL_MASK: 2, JS_GPN_PRIVATE_MASK: 4, JS_GPN_ENUM_ONLY: 16, JS_GPN_SET_ENUM: 32, QTS_GPN_NUMBER_MASK: 64, QTS_STANDARD_COMPLIANT_NUMBER: 128 };
    IsEqualOp = { IsStrictlyEqual: 0, IsSameValue: 1, IsSameValueZero: 2 };
  }
});

// node_modules/.pnpm/quickjs-emscripten-core@0.32.0/node_modules/quickjs-emscripten-core/dist/chunk-V2S4ZYJR.mjs
function debugLog(...args) {
  QTS_DEBUG && console.log("quickjs-emscripten:", ...args);
}
function* awaitYield(value) {
  return yield value;
}
function awaitYieldOf(generator) {
  return awaitYield(awaitEachYieldedPromise(generator));
}
function maybeAsyncFn(that, fn) {
  return (...args) => {
    let generator = fn.call(that, AwaitYield, ...args);
    return awaitEachYieldedPromise(generator);
  };
}
function maybeAsync(that, startGenerator) {
  let generator = startGenerator.call(that, AwaitYield);
  return awaitEachYieldedPromise(generator);
}
function awaitEachYieldedPromise(gen) {
  function handleNextStep(step) {
    return step.done ? step.value : step.value instanceof Promise ? step.value.then((value) => handleNextStep(gen.next(value)), (error) => handleNextStep(gen.throw(error))) : handleNextStep(gen.next(step.value));
  }
  return handleNextStep(gen.next());
}
function scopeFinally(scope, blockError) {
  let disposeError;
  try {
    scope.dispose();
  } catch (error) {
    disposeError = error;
  }
  if (blockError && disposeError) throw Object.assign(blockError, { message: `${blockError.message}
 Then, failed to dispose scope: ${disposeError.message}`, disposeError }), blockError;
  if (blockError || disposeError) throw blockError || disposeError;
}
function createDisposableArray(items) {
  let array = items ? Array.from(items) : [];
  function disposeAlive() {
    return array.forEach((disposable) => disposable.alive ? disposable.dispose() : void 0);
  }
  function someIsAlive() {
    return array.some((disposable) => disposable.alive);
  }
  return Object.defineProperty(array, SymbolDispose, { configurable: true, enumerable: false, value: disposeAlive }), Object.defineProperty(array, "dispose", { configurable: true, enumerable: false, value: disposeAlive }), Object.defineProperty(array, "alive", { configurable: true, enumerable: false, get: someIsAlive }), array;
}
function isDisposable(value) {
  return !!(value && (typeof value == "object" || typeof value == "function") && "alive" in value && typeof value.alive == "boolean" && "dispose" in value && typeof value.dispose == "function");
}
function intrinsicsToFlags(intrinsics) {
  if (!intrinsics) return 0;
  let result = 0;
  for (let [maybeIntrinsicName, enabled] of Object.entries(intrinsics)) {
    if (!(maybeIntrinsicName in IntrinsicsFlags)) throw new QuickJSUnknownIntrinsic(maybeIntrinsicName);
    enabled && (result |= IntrinsicsFlags[maybeIntrinsicName]);
  }
  return result;
}
function evalOptionsToFlags(evalOptions) {
  if (typeof evalOptions == "number") return evalOptions;
  if (evalOptions === void 0) return 0;
  let { type, strict, strip, compileOnly, backtraceBarrier } = evalOptions, flags = 0;
  return type === "global" && (flags |= EvalFlags.JS_EVAL_TYPE_GLOBAL), type === "module" && (flags |= EvalFlags.JS_EVAL_TYPE_MODULE), strict && (flags |= EvalFlags.JS_EVAL_FLAG_STRICT), strip && (flags |= EvalFlags.JS_EVAL_FLAG_STRIP), compileOnly && (flags |= EvalFlags.JS_EVAL_FLAG_COMPILE_ONLY), backtraceBarrier && (flags |= EvalFlags.JS_EVAL_FLAG_BACKTRACE_BARRIER), flags;
}
function getOwnPropertyNamesOptionsToFlags(options) {
  if (typeof options == "number") return options;
  if (options === void 0) return 0;
  let { strings: includeStrings, symbols: includeSymbols, quickjsPrivate: includePrivate, onlyEnumerable, numbers: includeNumbers, numbersAsStrings } = options, flags = 0;
  return includeStrings && (flags |= GetOwnPropertyNamesFlags.JS_GPN_STRING_MASK), includeSymbols && (flags |= GetOwnPropertyNamesFlags.JS_GPN_SYMBOL_MASK), includePrivate && (flags |= GetOwnPropertyNamesFlags.JS_GPN_PRIVATE_MASK), onlyEnumerable && (flags |= GetOwnPropertyNamesFlags.JS_GPN_ENUM_ONLY), includeNumbers && (flags |= GetOwnPropertyNamesFlags.QTS_GPN_NUMBER_MASK), numbersAsStrings && (flags |= GetOwnPropertyNamesFlags.QTS_STANDARD_COMPLIANT_NUMBER), flags;
}
function concat(...values) {
  let result = [];
  for (let value of values) value !== void 0 && (result = result.concat(value));
  return result;
}
function getGroupId(id) {
  return id >> 8;
}
function applyBaseRuntimeOptions(runtime, options) {
  options.interruptHandler && runtime.setInterruptHandler(options.interruptHandler), options.maxStackSizeBytes !== void 0 && runtime.setMaxStackSize(options.maxStackSizeBytes), options.memoryLimitBytes !== void 0 && runtime.setMemoryLimit(options.memoryLimitBytes);
}
function applyModuleEvalRuntimeOptions(runtime, options) {
  options.moduleLoader && runtime.setModuleLoader(options.moduleLoader), options.shouldInterrupt && runtime.setInterruptHandler(options.shouldInterrupt), options.memoryLimitBytes !== void 0 && runtime.setMemoryLimit(options.memoryLimitBytes), options.maxStackSizeBytes !== void 0 && runtime.setMaxStackSize(options.maxStackSizeBytes);
}
var __defProp2, __export2, QTS_DEBUG, errors_exports, QuickJSUnwrapError, QuickJSWrongOwner, QuickJSUseAfterFree, QuickJSNotImplemented, QuickJSAsyncifyError, QuickJSAsyncifySuspended, QuickJSMemoryLeakDetected, QuickJSEmscriptenModuleError, QuickJSUnknownIntrinsic, QuickJSPromisePending, QuickJSEmptyGetOwnPropertyNames, QuickJSHostRefRangeExceeded, QuickJSHostRefInvalid, AwaitYield, UsingDisposable, SymbolDispose, prototypeAsAny, Lifetime, StaticLifetime, WeakLifetime, Scope, AbstractDisposableResult, DisposableSuccess, DisposableFail, DisposableResult, QuickJSDeferredPromise, ModuleMemory, DefaultIntrinsics, QuickJSIterator, INT32_MIN, INT32_MAX, INVALID_HOST_REF_ID, HostRefMap, HostRef, ContextMemory, QuickJSContext, QuickJSRuntime, QuickJSEmscriptenModuleCallbacks, QuickJSModuleCallbacks, QuickJSWASMModule;
var init_chunk_V2S4ZYJR = __esm({
  "node_modules/.pnpm/quickjs-emscripten-core@0.32.0/node_modules/quickjs-emscripten-core/dist/chunk-V2S4ZYJR.mjs"() {
    init_dist();
    init_dist();
    __defProp2 = Object.defineProperty;
    __export2 = (target, all) => {
      for (var name in all) __defProp2(target, name, { get: all[name], enumerable: true });
    };
    QTS_DEBUG = false;
    errors_exports = {};
    __export2(errors_exports, { QuickJSAsyncifyError: () => QuickJSAsyncifyError, QuickJSAsyncifySuspended: () => QuickJSAsyncifySuspended, QuickJSEmptyGetOwnPropertyNames: () => QuickJSEmptyGetOwnPropertyNames, QuickJSEmscriptenModuleError: () => QuickJSEmscriptenModuleError, QuickJSHostRefInvalid: () => QuickJSHostRefInvalid, QuickJSHostRefRangeExceeded: () => QuickJSHostRefRangeExceeded, QuickJSMemoryLeakDetected: () => QuickJSMemoryLeakDetected, QuickJSNotImplemented: () => QuickJSNotImplemented, QuickJSPromisePending: () => QuickJSPromisePending, QuickJSUnknownIntrinsic: () => QuickJSUnknownIntrinsic, QuickJSUnwrapError: () => QuickJSUnwrapError, QuickJSUseAfterFree: () => QuickJSUseAfterFree, QuickJSWrongOwner: () => QuickJSWrongOwner });
    QuickJSUnwrapError = class extends Error {
      constructor(cause, context) {
        let message = typeof cause == "object" && cause && "message" in cause ? String(cause.message) : String(cause);
        super(message);
        this.cause = cause;
        this.context = context;
        this.name = "QuickJSUnwrapError";
      }
    };
    QuickJSWrongOwner = class extends Error {
      constructor() {
        super(...arguments);
        this.name = "QuickJSWrongOwner";
      }
    };
    QuickJSUseAfterFree = class extends Error {
      constructor() {
        super(...arguments);
        this.name = "QuickJSUseAfterFree";
      }
    };
    QuickJSNotImplemented = class extends Error {
      constructor() {
        super(...arguments);
        this.name = "QuickJSNotImplemented";
      }
    };
    QuickJSAsyncifyError = class extends Error {
      constructor() {
        super(...arguments);
        this.name = "QuickJSAsyncifyError";
      }
    };
    QuickJSAsyncifySuspended = class extends Error {
      constructor() {
        super(...arguments);
        this.name = "QuickJSAsyncifySuspended";
      }
    };
    QuickJSMemoryLeakDetected = class extends Error {
      constructor() {
        super(...arguments);
        this.name = "QuickJSMemoryLeakDetected";
      }
    };
    QuickJSEmscriptenModuleError = class extends Error {
      constructor() {
        super(...arguments);
        this.name = "QuickJSEmscriptenModuleError";
      }
    };
    QuickJSUnknownIntrinsic = class extends TypeError {
      constructor() {
        super(...arguments);
        this.name = "QuickJSUnknownIntrinsic";
      }
    };
    QuickJSPromisePending = class extends Error {
      constructor() {
        super(...arguments);
        this.name = "QuickJSPromisePending";
      }
    };
    QuickJSEmptyGetOwnPropertyNames = class extends Error {
      constructor() {
        super(...arguments);
        this.name = "QuickJSEmptyGetOwnPropertyNames";
      }
    };
    QuickJSHostRefRangeExceeded = class extends Error {
      constructor() {
        super(...arguments);
        this.name = "QuickJSHostRefRangeExceeded";
      }
    };
    QuickJSHostRefInvalid = class extends Error {
      constructor() {
        super(...arguments);
        this.name = "QuickJSHostRefInvalid";
      }
    };
    AwaitYield = awaitYield;
    AwaitYield.of = awaitYieldOf;
    UsingDisposable = class {
      [Symbol.dispose]() {
        return this.dispose();
      }
    };
    SymbolDispose = Symbol.dispose ?? /* @__PURE__ */ Symbol.for("Symbol.dispose");
    prototypeAsAny = UsingDisposable.prototype;
    prototypeAsAny[SymbolDispose] || (prototypeAsAny[SymbolDispose] = function() {
      return this.dispose();
    });
    Lifetime = class _Lifetime extends UsingDisposable {
      constructor(_value, copier, disposer, _owner) {
        super();
        this._value = _value;
        this.copier = copier;
        this.disposer = disposer;
        this._owner = _owner;
        this._alive = true;
        this._constructorStack = QTS_DEBUG ? new Error("Lifetime constructed").stack : void 0;
      }
      get alive() {
        return this._alive;
      }
      get value() {
        return this.assertAlive(), this._value;
      }
      get owner() {
        return this._owner;
      }
      get dupable() {
        return !!this.copier;
      }
      dup() {
        if (this.assertAlive(), !this.copier) throw new Error("Non-dupable lifetime");
        return new _Lifetime(this.copier(this._value), this.copier, this.disposer, this._owner);
      }
      consume(map) {
        this.assertAlive();
        let result = map(this);
        return this.dispose(), result;
      }
      map(map) {
        return this.assertAlive(), map(this);
      }
      tap(fn) {
        return fn(this), this;
      }
      dispose() {
        this.assertAlive(), this.disposer && this.disposer(this._value), this._alive = false;
      }
      assertAlive() {
        if (!this.alive) throw this._constructorStack ? new QuickJSUseAfterFree(`Lifetime not alive
${this._constructorStack}
Lifetime used`) : new QuickJSUseAfterFree("Lifetime not alive");
      }
    };
    StaticLifetime = class extends Lifetime {
      constructor(value, owner) {
        super(value, void 0, void 0, owner);
      }
      get dupable() {
        return true;
      }
      dup() {
        return this;
      }
      dispose() {
      }
    };
    WeakLifetime = class extends Lifetime {
      constructor(value, copier, disposer, owner) {
        super(value, copier, disposer, owner);
      }
      dispose() {
        this._alive = false;
      }
    };
    Scope = class _Scope extends UsingDisposable {
      constructor() {
        super(...arguments);
        this._disposables = new Lifetime(/* @__PURE__ */ new Set());
        this.manage = (lifetime) => (this._disposables.value.add(lifetime), lifetime);
      }
      static withScope(block) {
        let scope = new _Scope(), blockError;
        try {
          return block(scope);
        } catch (error) {
          throw blockError = error, error;
        } finally {
          scopeFinally(scope, blockError);
        }
      }
      static withScopeMaybeAsync(_this, block) {
        return maybeAsync(void 0, function* (awaited) {
          let scope = new _Scope(), blockError;
          try {
            return yield* awaited.of(block.call(_this, awaited, scope));
          } catch (error) {
            throw blockError = error, error;
          } finally {
            scopeFinally(scope, blockError);
          }
        });
      }
      static async withScopeAsync(block) {
        let scope = new _Scope(), blockError;
        try {
          return await block(scope);
        } catch (error) {
          throw blockError = error, error;
        } finally {
          scopeFinally(scope, blockError);
        }
      }
      get alive() {
        return this._disposables.alive;
      }
      dispose() {
        let lifetimes = Array.from(this._disposables.value.values()).reverse();
        for (let lifetime of lifetimes) lifetime.alive && lifetime.dispose();
        this._disposables.dispose();
      }
    };
    AbstractDisposableResult = class _AbstractDisposableResult extends UsingDisposable {
      static success(value) {
        return new DisposableSuccess(value);
      }
      static fail(error, onUnwrap) {
        return new DisposableFail(error, onUnwrap);
      }
      static is(result) {
        return result instanceof _AbstractDisposableResult;
      }
    };
    DisposableSuccess = class extends AbstractDisposableResult {
      constructor(value) {
        super();
        this.value = value;
      }
      get alive() {
        return isDisposable(this.value) ? this.value.alive : true;
      }
      dispose() {
        isDisposable(this.value) && this.value.dispose();
      }
      unwrap() {
        return this.value;
      }
      unwrapOr(_fallback) {
        return this.value;
      }
    };
    DisposableFail = class extends AbstractDisposableResult {
      constructor(error, onUnwrap) {
        super();
        this.error = error;
        this.onUnwrap = onUnwrap;
      }
      get alive() {
        return isDisposable(this.error) ? this.error.alive : true;
      }
      dispose() {
        isDisposable(this.error) && this.error.dispose();
      }
      unwrap() {
        throw this.onUnwrap(this), this.error;
      }
      unwrapOr(fallback) {
        return fallback;
      }
    };
    DisposableResult = AbstractDisposableResult;
    QuickJSDeferredPromise = class extends UsingDisposable {
      constructor(args) {
        super();
        this.resolve = (value) => {
          this.resolveHandle.alive && (this.context.unwrapResult(this.context.callFunction(this.resolveHandle, this.context.undefined, value || this.context.undefined)).dispose(), this.disposeResolvers(), this.onSettled());
        };
        this.reject = (value) => {
          this.rejectHandle.alive && (this.context.unwrapResult(this.context.callFunction(this.rejectHandle, this.context.undefined, value || this.context.undefined)).dispose(), this.disposeResolvers(), this.onSettled());
        };
        this.dispose = () => {
          this.handle.alive && this.handle.dispose(), this.disposeResolvers();
        };
        this.context = args.context, this.owner = args.context.runtime, this.handle = args.promiseHandle, this.settled = new Promise((resolve) => {
          this.onSettled = resolve;
        }), this.resolveHandle = args.resolveHandle, this.rejectHandle = args.rejectHandle;
      }
      get alive() {
        return this.handle.alive || this.resolveHandle.alive || this.rejectHandle.alive;
      }
      disposeResolvers() {
        this.resolveHandle.alive && this.resolveHandle.dispose(), this.rejectHandle.alive && this.rejectHandle.dispose();
      }
    };
    ModuleMemory = class {
      constructor(module) {
        this.module = module;
      }
      toPointerArray(handleArray) {
        let typedArray = new Int32Array(handleArray.map((handle) => handle.value)), numBytes = typedArray.length * typedArray.BYTES_PER_ELEMENT, ptr = this.module._malloc(numBytes);
        return new Uint8Array(this.module.HEAPU8.buffer, ptr, numBytes).set(new Uint8Array(typedArray.buffer)), new Lifetime(ptr, void 0, (ptr2) => this.module._free(ptr2));
      }
      newTypedArray(kind, length) {
        let zeros = new kind(new Array(length).fill(0)), numBytes = zeros.length * zeros.BYTES_PER_ELEMENT, ptr = this.module._malloc(numBytes), typedArray = new kind(this.module.HEAPU8.buffer, ptr, length);
        return typedArray.set(zeros), new Lifetime({ typedArray, ptr }, void 0, (value) => this.module._free(value.ptr));
      }
      newMutablePointerArray(length) {
        return this.newTypedArray(Int32Array, length);
      }
      newHeapCharPointer(string) {
        let strlen = this.module.lengthBytesUTF8(string), dataBytes = strlen + 1, ptr = this.module._malloc(dataBytes);
        return this.module.stringToUTF8(string, ptr, dataBytes), new Lifetime({ ptr, strlen }, void 0, (value) => this.module._free(value.ptr));
      }
      newHeapBufferPointer(buffer) {
        let numBytes = buffer.byteLength, ptr = this.module._malloc(numBytes);
        return this.module.HEAPU8.set(buffer, ptr), new Lifetime({ pointer: ptr, numBytes }, void 0, (value) => this.module._free(value.pointer));
      }
      consumeHeapCharPointer(ptr) {
        let str = this.module.UTF8ToString(ptr);
        return this.module._free(ptr), str;
      }
    };
    DefaultIntrinsics = Object.freeze({ BaseObjects: true, Date: true, Eval: true, StringNormalize: true, RegExp: true, JSON: true, Proxy: true, MapSet: true, TypedArrays: true, Promise: true });
    QuickJSIterator = class extends UsingDisposable {
      constructor(handle, context) {
        super();
        this.handle = handle;
        this.context = context;
        this._isDone = false;
        this.owner = context.runtime;
      }
      [Symbol.iterator]() {
        return this;
      }
      next(value) {
        if (!this.alive || this._isDone) return { done: true, value: void 0 };
        let nextMethod = this._next ?? (this._next = this.context.getProp(this.handle, "next"));
        return this.callIteratorMethod(nextMethod, value);
      }
      return(value) {
        if (!this.alive) return { done: true, value: void 0 };
        let returnMethod = this.context.getProp(this.handle, "return");
        if (returnMethod === this.context.undefined && value === void 0) return this.dispose(), { done: true, value: void 0 };
        let result = this.callIteratorMethod(returnMethod, value);
        return returnMethod.dispose(), this.dispose(), result;
      }
      throw(e) {
        if (!this.alive) return { done: true, value: void 0 };
        let errorHandle = e instanceof Lifetime ? e : this.context.newError(e), throwMethod = this.context.getProp(this.handle, "throw"), result = this.callIteratorMethod(throwMethod, e);
        return errorHandle.alive && errorHandle.dispose(), throwMethod.dispose(), this.dispose(), result;
      }
      get alive() {
        return this.handle.alive;
      }
      dispose() {
        this._isDone = true, this.handle.dispose(), this._next?.dispose();
      }
      callIteratorMethod(method, input) {
        let callResult = input ? this.context.callFunction(method, this.handle, input) : this.context.callFunction(method, this.handle);
        if (callResult.error) return this.dispose(), { value: callResult };
        let done = this.context.getProp(callResult.value, "done").consume((v) => this.context.dump(v)), value = this.context.getProp(callResult.value, "value");
        return callResult.value.dispose(), done && this.dispose(), { value: DisposableResult.success(value), done };
      }
    };
    INT32_MIN = -2147483648;
    INT32_MAX = 2147483647;
    INVALID_HOST_REF_ID = 0;
    HostRefMap = class {
      constructor() {
        this.nextId = INT32_MIN;
        this.freelist = [];
        this.groups = /* @__PURE__ */ new Map();
      }
      put(value) {
        let id = this.allocateId(), groupId = getGroupId(id), group = this.groups.get(groupId);
        return group || (group = /* @__PURE__ */ new Map(), this.groups.set(groupId, group)), group.set(id, value), id;
      }
      get(id) {
        if (id === INVALID_HOST_REF_ID) throw new QuickJSHostRefInvalid("no host reference id defined");
        let groupId = getGroupId(id), group = this.groups.get(groupId);
        if (!group) throw new QuickJSHostRefInvalid(`host reference id ${id} is not defined`);
        let value = group.get(id);
        if (!value) throw new QuickJSHostRefInvalid(`host reference id ${id} is not defined`);
        return value;
      }
      delete(id) {
        if (id === INVALID_HOST_REF_ID) throw new QuickJSHostRefInvalid("no host reference id defined");
        let groupId = getGroupId(id), group = this.groups.get(groupId);
        if (!group) throw new QuickJSHostRefInvalid(`host reference id ${id} is not defined`);
        group.delete(id), group.size === 0 && this.groups.delete(groupId), this.freelist.push(id);
      }
      allocateId() {
        if (this.freelist.length > 0) return this.freelist.shift();
        if (this.nextId === INVALID_HOST_REF_ID && this.nextId++, this.nextId > INT32_MAX) throw new QuickJSHostRefRangeExceeded(`HostRefMap: too many host refs created without disposing. Max simultaneous host refs: ${INT32_MAX - INT32_MIN}`);
        return this.nextId++;
      }
    };
    HostRef = class extends UsingDisposable {
      constructor(runtime, handle, id) {
        if (id === INVALID_HOST_REF_ID) throw new QuickJSHostRefInvalid("cannot create HostRef with undefined id");
        super();
        this.runtime = runtime;
        this.handle = handle;
        this.id = id;
      }
      get alive() {
        return this.handle.alive;
      }
      dispose() {
        this.handle.dispose();
      }
      get value() {
        return this.runtime.hostRefs.get(this.id);
      }
    };
    ContextMemory = class extends ModuleMemory {
      constructor(args) {
        super(args.module);
        this.scope = new Scope();
        this.copyJSValue = (ptr) => this.ffi.QTS_DupValuePointer(this.ctx.value, ptr);
        this.freeJSValue = (ptr) => {
          this.ffi.QTS_FreeValuePointer(this.ctx.value, ptr);
        };
        args.ownedLifetimes?.forEach((lifetime) => this.scope.manage(lifetime)), this.owner = args.owner, this.module = args.module, this.ffi = args.ffi, this.rt = args.rt, this.ctx = this.scope.manage(args.ctx);
      }
      get alive() {
        return this.scope.alive;
      }
      dispose() {
        return this.scope.dispose();
      }
      [Symbol.dispose]() {
        return this.dispose();
      }
      manage(lifetime) {
        return this.scope.manage(lifetime);
      }
      consumeJSCharPointer(ptr) {
        let str = this.module.UTF8ToString(ptr);
        return this.ffi.QTS_FreeCString(this.ctx.value, ptr), str;
      }
      heapValueHandle(ptr, extraDispose) {
        let dispose = extraDispose ? (val) => {
          extraDispose(), this.freeJSValue(val);
        } : this.freeJSValue;
        return new Lifetime(ptr, this.copyJSValue, dispose, this.owner);
      }
      staticHeapValueHandle(ptr) {
        return this.manage(this.heapValueHandle(ptr)), new StaticLifetime(ptr, this.owner);
      }
    };
    QuickJSContext = class extends UsingDisposable {
      constructor(args) {
        super();
        this._undefined = void 0;
        this._null = void 0;
        this._false = void 0;
        this._true = void 0;
        this._global = void 0;
        this._BigInt = void 0;
        this._Symbol = void 0;
        this._SymbolIterator = void 0;
        this._SymbolAsyncIterator = void 0;
        this.cToHostCallbacks = { callFunction: (ctx, this_ptr, argc, argv, fn_id) => {
          if (ctx !== this.ctx.value) throw new Error("QuickJSContext instance received C -> JS call with mismatched ctx");
          let fn = this.getFunction(fn_id);
          return Scope.withScopeMaybeAsync(this, function* (awaited, scope) {
            let thisHandle = scope.manage(new WeakLifetime(this_ptr, this.memory.copyJSValue, this.memory.freeJSValue, this.runtime)), argHandles = new Array(argc);
            for (let i = 0; i < argc; i++) {
              let ptr = this.ffi.QTS_ArgvGetJSValueConstPointer(argv, i);
              argHandles[i] = scope.manage(new WeakLifetime(ptr, this.memory.copyJSValue, this.memory.freeJSValue, this.runtime));
            }
            try {
              let result = yield* awaited(fn.apply(thisHandle, argHandles));
              if (result) {
                if ("error" in result && result.error) throw this.runtime.debugLog("throw error", result.error), result.error;
                let handle = scope.manage(result instanceof Lifetime ? result : result.value);
                return this.ffi.QTS_DupValuePointer(this.ctx.value, handle.value);
              }
              return 0;
            } catch (error) {
              return this.errorToHandle(error).consume((errorHandle) => this.ffi.QTS_Throw(this.ctx.value, errorHandle.value));
            }
          });
        } };
        this.runtime = args.runtime, this.module = args.module, this.ffi = args.ffi, this.rt = args.rt, this.ctx = args.ctx, this.memory = new ContextMemory({ ...args, owner: this.runtime }), args.callbacks.setContextCallbacks(this.ctx.value, this.cToHostCallbacks), this.dump = this.dump.bind(this), this.getString = this.getString.bind(this), this.getNumber = this.getNumber.bind(this), this.resolvePromise = this.resolvePromise.bind(this), this.uint32Out = this.memory.manage(this.memory.newTypedArray(Uint32Array, 1));
      }
      get alive() {
        return this.memory.alive;
      }
      dispose() {
        this.memory.dispose();
      }
      get undefined() {
        if (this._undefined) return this._undefined;
        let ptr = this.ffi.QTS_GetUndefined();
        return this._undefined = new StaticLifetime(ptr);
      }
      get null() {
        if (this._null) return this._null;
        let ptr = this.ffi.QTS_GetNull();
        return this._null = new StaticLifetime(ptr);
      }
      get true() {
        if (this._true) return this._true;
        let ptr = this.ffi.QTS_GetTrue();
        return this._true = new StaticLifetime(ptr);
      }
      get false() {
        if (this._false) return this._false;
        let ptr = this.ffi.QTS_GetFalse();
        return this._false = new StaticLifetime(ptr);
      }
      get global() {
        if (this._global) return this._global;
        let ptr = this.ffi.QTS_GetGlobalObject(this.ctx.value);
        return this._global = this.memory.staticHeapValueHandle(ptr), this._global;
      }
      newNumber(num) {
        return this.memory.heapValueHandle(this.ffi.QTS_NewFloat64(this.ctx.value, num));
      }
      newString(str) {
        let ptr = this.memory.newHeapCharPointer(str).consume((charHandle) => this.ffi.QTS_NewString(this.ctx.value, charHandle.value.ptr));
        return this.memory.heapValueHandle(ptr);
      }
      newUniqueSymbol(description) {
        let key = (typeof description == "symbol" ? description.description : description) ?? "", ptr = this.memory.newHeapCharPointer(key).consume((charHandle) => this.ffi.QTS_NewSymbol(this.ctx.value, charHandle.value.ptr, 0));
        return this.memory.heapValueHandle(ptr);
      }
      newSymbolFor(key) {
        let description = (typeof key == "symbol" ? key.description : key) ?? "", ptr = this.memory.newHeapCharPointer(description).consume((charHandle) => this.ffi.QTS_NewSymbol(this.ctx.value, charHandle.value.ptr, 1));
        return this.memory.heapValueHandle(ptr);
      }
      getWellKnownSymbol(name) {
        return this._Symbol ?? (this._Symbol = this.memory.manage(this.getProp(this.global, "Symbol"))), this.getProp(this._Symbol, name);
      }
      newBigInt(num) {
        if (!this._BigInt) {
          let bigIntHandle2 = this.getProp(this.global, "BigInt");
          this.memory.manage(bigIntHandle2), this._BigInt = new StaticLifetime(bigIntHandle2.value, this.runtime);
        }
        let bigIntHandle = this._BigInt, asString = String(num);
        return this.newString(asString).consume((handle) => this.unwrapResult(this.callFunction(bigIntHandle, this.undefined, handle)));
      }
      newObject(prototype) {
        prototype && this.runtime.assertOwned(prototype);
        let ptr = prototype ? this.ffi.QTS_NewObjectProto(this.ctx.value, prototype.value) : this.ffi.QTS_NewObject(this.ctx.value);
        return this.memory.heapValueHandle(ptr);
      }
      newArray() {
        let ptr = this.ffi.QTS_NewArray(this.ctx.value);
        return this.memory.heapValueHandle(ptr);
      }
      newArrayBuffer(buffer) {
        let array = new Uint8Array(buffer), handle = this.memory.newHeapBufferPointer(array), ptr = this.ffi.QTS_NewArrayBuffer(this.ctx.value, handle.value.pointer, array.length);
        return this.memory.heapValueHandle(ptr);
      }
      newPromise(value) {
        let deferredPromise = Scope.withScope((scope) => {
          let mutablePointerArray = scope.manage(this.memory.newMutablePointerArray(2)), promisePtr = this.ffi.QTS_NewPromiseCapability(this.ctx.value, mutablePointerArray.value.ptr), promiseHandle = this.memory.heapValueHandle(promisePtr), [resolveHandle, rejectHandle] = Array.from(mutablePointerArray.value.typedArray).map((jsvaluePtr) => this.memory.heapValueHandle(jsvaluePtr));
          return new QuickJSDeferredPromise({ context: this, promiseHandle, resolveHandle, rejectHandle });
        });
        return value && typeof value == "function" && (value = new Promise(value)), value && Promise.resolve(value).then(deferredPromise.resolve, (error) => error instanceof Lifetime ? deferredPromise.reject(error) : this.newError(error).consume(deferredPromise.reject)), deferredPromise;
      }
      newFunction(nameOrFn, maybeFn) {
        let fn = typeof nameOrFn == "function" ? nameOrFn : maybeFn;
        if (!fn) throw new TypeError("Expected a function");
        return this.newFunctionWithOptions({ name: typeof nameOrFn == "string" ? nameOrFn : void 0, length: fn.length, isConstructor: false, fn });
      }
      newConstructorFunction(nameOrFn, maybeFn) {
        let fn = typeof nameOrFn == "function" ? nameOrFn : maybeFn;
        if (!fn) throw new TypeError("Expected a function");
        return this.newFunctionWithOptions({ name: typeof nameOrFn == "string" ? nameOrFn : void 0, length: fn.length, isConstructor: true, fn });
      }
      newFunctionWithOptions(args) {
        let { name, length, isConstructor, fn } = args, refId = this.runtime.hostRefs.put(fn);
        try {
          return this.memory.heapValueHandle(this.ffi.QTS_NewFunction(this.ctx.value, name ?? "", length, isConstructor, refId));
        } catch (error) {
          throw this.runtime.hostRefs.delete(refId), error;
        }
      }
      newError(error) {
        let errorHandle = this.memory.heapValueHandle(this.ffi.QTS_NewError(this.ctx.value));
        return error && typeof error == "object" ? (error.name !== void 0 && this.newString(error.name).consume((handle) => this.setProp(errorHandle, "name", handle)), error.message !== void 0 && this.newString(error.message).consume((handle) => this.setProp(errorHandle, "message", handle))) : typeof error == "string" ? this.newString(error).consume((handle) => this.setProp(errorHandle, "message", handle)) : error !== void 0 && this.newString(String(error)).consume((handle) => this.setProp(errorHandle, "message", handle)), errorHandle;
      }
      newHostRef(value) {
        let id = this.runtime.hostRefs.put(value);
        try {
          let handle = this.memory.heapValueHandle(this.ffi.QTS_NewHostRef(this.ctx.value, id));
          return new HostRef(this.runtime, handle, id);
        } catch (error) {
          throw this.runtime.hostRefs.delete(id), error;
        }
      }
      toHostRef(handle) {
        let id = this.ffi.QTS_GetHostRefId(handle.value);
        if (id !== 0) return this.runtime.hostRefs.get(id), new HostRef(this.runtime, handle.dup(), id);
      }
      unwrapHostRef(handle) {
        let id = this.ffi.QTS_GetHostRefId(handle.value);
        if (id === 0) throw new QuickJSHostRefInvalid("handle is not a HostRef");
        return this.runtime.hostRefs.get(id);
      }
      typeof(handle) {
        return this.runtime.assertOwned(handle), this.memory.consumeHeapCharPointer(this.ffi.QTS_Typeof(this.ctx.value, handle.value));
      }
      getNumber(handle) {
        return this.runtime.assertOwned(handle), this.ffi.QTS_GetFloat64(this.ctx.value, handle.value);
      }
      getString(handle) {
        return this.runtime.assertOwned(handle), this.memory.consumeJSCharPointer(this.ffi.QTS_GetString(this.ctx.value, handle.value));
      }
      getSymbol(handle) {
        this.runtime.assertOwned(handle);
        let key = this.memory.consumeJSCharPointer(this.ffi.QTS_GetSymbolDescriptionOrKey(this.ctx.value, handle.value));
        return this.ffi.QTS_IsGlobalSymbol(this.ctx.value, handle.value) ? Symbol.for(key) : Symbol(key);
      }
      getBigInt(handle) {
        this.runtime.assertOwned(handle);
        let asString = this.getString(handle);
        return BigInt(asString);
      }
      getArrayBuffer(handle) {
        this.runtime.assertOwned(handle);
        let len = this.ffi.QTS_GetArrayBufferLength(this.ctx.value, handle.value), ptr = this.ffi.QTS_GetArrayBuffer(this.ctx.value, handle.value);
        if (!ptr) throw new Error("Couldn't allocate memory to get ArrayBuffer");
        return new Lifetime(this.module.HEAPU8.subarray(ptr, ptr + len), void 0, () => this.module._free(ptr));
      }
      getPromiseState(handle) {
        this.runtime.assertOwned(handle);
        let state = this.ffi.QTS_PromiseState(this.ctx.value, handle.value);
        if (state < 0) return { type: "fulfilled", value: handle, notAPromise: true };
        if (state === JSPromiseStateEnum.Pending) return { type: "pending", get error() {
          return new QuickJSPromisePending("Cannot unwrap a pending promise");
        } };
        let ptr = this.ffi.QTS_PromiseResult(this.ctx.value, handle.value), result = this.memory.heapValueHandle(ptr);
        if (state === JSPromiseStateEnum.Fulfilled) return { type: "fulfilled", value: result };
        if (state === JSPromiseStateEnum.Rejected) return { type: "rejected", error: result };
        throw result.dispose(), new Error(`Unknown JSPromiseStateEnum: ${state}`);
      }
      resolvePromise(promiseLikeHandle) {
        this.runtime.assertOwned(promiseLikeHandle);
        let vmResolveResult = Scope.withScope((scope) => {
          let vmPromise = scope.manage(this.getProp(this.global, "Promise")), vmPromiseResolve = scope.manage(this.getProp(vmPromise, "resolve"));
          return this.callFunction(vmPromiseResolve, vmPromise, promiseLikeHandle);
        });
        return vmResolveResult.error ? Promise.resolve(vmResolveResult) : new Promise((resolve) => {
          Scope.withScope((scope) => {
            let resolveHandle = scope.manage(this.newFunction("resolve", (value) => {
              resolve(this.success(value && value.dup()));
            })), rejectHandle = scope.manage(this.newFunction("reject", (error) => {
              resolve(this.fail(error && error.dup()));
            })), promiseHandle = scope.manage(vmResolveResult.value), promiseThenHandle = scope.manage(this.getProp(promiseHandle, "then"));
            this.callFunction(promiseThenHandle, promiseHandle, resolveHandle, rejectHandle).unwrap().dispose();
          });
        });
      }
      isEqual(a, b, equalityType = IsEqualOp.IsStrictlyEqual) {
        if (a === b) return true;
        this.runtime.assertOwned(a), this.runtime.assertOwned(b);
        let result = this.ffi.QTS_IsEqual(this.ctx.value, a.value, b.value, equalityType);
        if (result === -1) throw new QuickJSNotImplemented("WASM variant does not expose equality");
        return !!result;
      }
      eq(handle, other) {
        return this.isEqual(handle, other, IsEqualOp.IsStrictlyEqual);
      }
      sameValue(handle, other) {
        return this.isEqual(handle, other, IsEqualOp.IsSameValue);
      }
      sameValueZero(handle, other) {
        return this.isEqual(handle, other, IsEqualOp.IsSameValueZero);
      }
      getProp(handle, key) {
        this.runtime.assertOwned(handle);
        let ptr;
        return typeof key == "number" && key >= 0 ? ptr = this.ffi.QTS_GetPropNumber(this.ctx.value, handle.value, key) : ptr = this.borrowPropertyKey(key).consume((quickJSKey) => this.ffi.QTS_GetProp(this.ctx.value, handle.value, quickJSKey.value)), this.memory.heapValueHandle(ptr);
      }
      getLength(handle) {
        if (this.runtime.assertOwned(handle), !(this.ffi.QTS_GetLength(this.ctx.value, this.uint32Out.value.ptr, handle.value) < 0)) return this.uint32Out.value.typedArray[0];
      }
      getOwnPropertyNames(handle, options = { strings: true, numbersAsStrings: true }) {
        this.runtime.assertOwned(handle), handle.value;
        let flags = getOwnPropertyNamesOptionsToFlags(options);
        if (flags === 0) throw new QuickJSEmptyGetOwnPropertyNames("No options set, will return an empty array");
        return Scope.withScope((scope) => {
          let outPtr = scope.manage(this.memory.newMutablePointerArray(1)), errorPtr = this.ffi.QTS_GetOwnPropertyNames(this.ctx.value, outPtr.value.ptr, this.uint32Out.value.ptr, handle.value, flags);
          if (errorPtr) return this.fail(this.memory.heapValueHandle(errorPtr));
          let len = this.uint32Out.value.typedArray[0], ptr = outPtr.value.typedArray[0], pointerArray = new Uint32Array(this.module.HEAP8.buffer, ptr, len), handles = Array.from(pointerArray).map((ptr2) => this.memory.heapValueHandle(ptr2));
          return this.ffi.QTS_FreeVoidPointer(this.ctx.value, ptr), this.success(createDisposableArray(handles));
        });
      }
      getIterator(iterableHandle) {
        let SymbolIterator = this._SymbolIterator ?? (this._SymbolIterator = this.memory.manage(this.getWellKnownSymbol("iterator")));
        return Scope.withScope((scope) => {
          let methodHandle = scope.manage(this.getProp(iterableHandle, SymbolIterator)), iteratorCallResult = this.callFunction(methodHandle, iterableHandle);
          return iteratorCallResult.error ? iteratorCallResult : this.success(new QuickJSIterator(iteratorCallResult.value, this));
        });
      }
      setProp(handle, key, value) {
        this.runtime.assertOwned(handle), this.borrowPropertyKey(key).consume((quickJSKey) => this.ffi.QTS_SetProp(this.ctx.value, handle.value, quickJSKey.value, value.value));
      }
      defineProp(handle, key, descriptor) {
        this.runtime.assertOwned(handle), Scope.withScope((scope) => {
          let quickJSKey = scope.manage(this.borrowPropertyKey(key)), value = descriptor.value || this.undefined, configurable = !!descriptor.configurable, enumerable = !!descriptor.enumerable, hasValue = !!descriptor.value, get = descriptor.get ? scope.manage(this.newFunction(descriptor.get.name, descriptor.get)) : this.undefined, set = descriptor.set ? scope.manage(this.newFunction(descriptor.set.name, descriptor.set)) : this.undefined;
          this.ffi.QTS_DefineProp(this.ctx.value, handle.value, quickJSKey.value, value.value, get.value, set.value, configurable, enumerable, hasValue);
        });
      }
      callFunction(func, thisVal, ...restArgs) {
        this.runtime.assertOwned(func);
        let args, firstArg = restArgs[0];
        firstArg === void 0 || Array.isArray(firstArg) ? args = firstArg ?? [] : args = restArgs;
        let resultPtr = this.memory.toPointerArray(args).consume((argsArrayPtr) => this.ffi.QTS_Call(this.ctx.value, func.value, thisVal.value, args.length, argsArrayPtr.value)), errorPtr = this.ffi.QTS_ResolveException(this.ctx.value, resultPtr);
        return errorPtr ? (this.ffi.QTS_FreeValuePointer(this.ctx.value, resultPtr), this.fail(this.memory.heapValueHandle(errorPtr))) : this.success(this.memory.heapValueHandle(resultPtr));
      }
      callMethod(thisHandle, key, args = []) {
        return this.getProp(thisHandle, key).consume((func) => this.callFunction(func, thisHandle, args));
      }
      evalCode(code, filename = "eval.js", options) {
        let detectModule = options === void 0 ? 1 : 0, flags = evalOptionsToFlags(options), resultPtr = this.memory.newHeapCharPointer(code).consume((charHandle) => this.ffi.QTS_Eval(this.ctx.value, charHandle.value.ptr, charHandle.value.strlen, filename, detectModule, flags)), errorPtr = this.ffi.QTS_ResolveException(this.ctx.value, resultPtr);
        return errorPtr ? (this.ffi.QTS_FreeValuePointer(this.ctx.value, resultPtr), this.fail(this.memory.heapValueHandle(errorPtr))) : this.success(this.memory.heapValueHandle(resultPtr));
      }
      throw(error) {
        return this.errorToHandle(error).consume((handle) => this.ffi.QTS_Throw(this.ctx.value, handle.value));
      }
      borrowPropertyKey(key) {
        return typeof key == "number" ? this.newNumber(key) : typeof key == "string" ? this.newString(key) : new StaticLifetime(key.value, this.runtime);
      }
      getMemory(rt) {
        if (rt === this.rt.value) return this.memory;
        throw new Error("Private API. Cannot get memory from a different runtime");
      }
      dump(handle) {
        this.runtime.assertOwned(handle);
        let type = this.typeof(handle);
        if (type === "string") return this.getString(handle);
        if (type === "number") return this.getNumber(handle);
        if (type === "bigint") return this.getBigInt(handle);
        if (type === "undefined") return;
        if (type === "symbol") return this.getSymbol(handle);
        let asPromiseState = this.getPromiseState(handle);
        if (asPromiseState.type === "fulfilled" && !asPromiseState.notAPromise) return handle.dispose(), { type: asPromiseState.type, value: asPromiseState.value.consume(this.dump) };
        if (asPromiseState.type === "pending") return handle.dispose(), { type: asPromiseState.type };
        if (asPromiseState.type === "rejected") return handle.dispose(), { type: asPromiseState.type, error: asPromiseState.error.consume(this.dump) };
        let str = this.memory.consumeJSCharPointer(this.ffi.QTS_Dump(this.ctx.value, handle.value));
        try {
          return JSON.parse(str);
        } catch {
          return str;
        }
      }
      unwrapResult(result) {
        if (result.error) {
          let context = "context" in result.error ? result.error.context : this, cause = result.error.consume((error) => this.dump(error));
          if (cause && typeof cause == "object" && typeof cause.message == "string") {
            let { message, name, stack, ...rest } = cause, exception = new QuickJSUnwrapError(cause, context);
            typeof name == "string" && (exception.name = cause.name), exception.message = message;
            let hostStack = exception.stack;
            throw typeof stack == "string" && (exception.stack = `${name}: ${message}
${cause.stack}Host: ${hostStack}`), Object.assign(exception, rest), exception;
          }
          throw new QuickJSUnwrapError(cause);
        }
        return result.value;
      }
      [/* @__PURE__ */ Symbol.for("nodejs.util.inspect.custom")]() {
        return this.alive ? `${this.constructor.name} { ctx: ${this.ctx.value} rt: ${this.rt.value} }` : `${this.constructor.name} { disposed }`;
      }
      getFunction(fn_id) {
        let fn = this.runtime.hostRefs.get(fn_id);
        if (typeof fn != "function") throw new Error(`Host reference ${fn_id} is not a function`);
        return fn;
      }
      errorToHandle(error) {
        return error instanceof Lifetime ? error : this.newError(error);
      }
      encodeBinaryJSON(handle) {
        let ptr = this.ffi.QTS_bjson_encode(this.ctx.value, handle.value);
        return this.memory.heapValueHandle(ptr);
      }
      decodeBinaryJSON(handle) {
        let ptr = this.ffi.QTS_bjson_decode(this.ctx.value, handle.value);
        return this.memory.heapValueHandle(ptr);
      }
      success(value) {
        return DisposableResult.success(value);
      }
      fail(error) {
        return DisposableResult.fail(error, (error2) => this.unwrapResult(error2));
      }
    };
    QuickJSRuntime = class extends UsingDisposable {
      constructor(args) {
        super();
        this.scope = new Scope();
        this.contextMap = /* @__PURE__ */ new Map();
        this.hostRefs = new HostRefMap();
        this._debugMode = false;
        this.cToHostCallbacks = { freeHostRef: (rt, host_ref_id) => {
          if (rt !== this.rt.value) throw new Error("Runtime pointer mismatch");
          this.hostRefs.delete(host_ref_id);
        }, shouldInterrupt: (rt) => {
          if (rt !== this.rt.value) throw new Error("QuickJSContext instance received C -> JS interrupt with mismatched rt");
          let fn = this.interruptHandler;
          if (!fn) throw new Error("QuickJSContext had no interrupt handler");
          return fn(this) ? 1 : 0;
        }, loadModuleSource: maybeAsyncFn(this, function* (awaited, rt, ctx, moduleName) {
          let moduleLoader = this.moduleLoader;
          if (!moduleLoader) throw new Error("Runtime has no module loader");
          if (rt !== this.rt.value) throw new Error("Runtime pointer mismatch");
          let context = this.contextMap.get(ctx) ?? this.newContext({ contextPointer: ctx });
          try {
            let result = yield* awaited(moduleLoader(moduleName, context));
            if (typeof result == "object" && "error" in result && result.error) throw this.debugLog("cToHostLoadModule: loader returned error", result.error), result.error;
            let moduleSource = typeof result == "string" ? result : "value" in result ? result.value : result;
            return this.memory.newHeapCharPointer(moduleSource).value.ptr;
          } catch (error) {
            return this.debugLog("cToHostLoadModule: caught error", error), context.throw(error), 0;
          }
        }), normalizeModule: maybeAsyncFn(this, function* (awaited, rt, ctx, baseModuleName, moduleNameRequest) {
          let moduleNormalizer = this.moduleNormalizer;
          if (!moduleNormalizer) throw new Error("Runtime has no module normalizer");
          if (rt !== this.rt.value) throw new Error("Runtime pointer mismatch");
          let context = this.contextMap.get(ctx) ?? this.newContext({ contextPointer: ctx });
          try {
            let result = yield* awaited(moduleNormalizer(baseModuleName, moduleNameRequest, context));
            if (typeof result == "object" && "error" in result && result.error) throw this.debugLog("cToHostNormalizeModule: normalizer returned error", result.error), result.error;
            let name = typeof result == "string" ? result : result.value;
            return context.getMemory(this.rt.value).newHeapCharPointer(name).value.ptr;
          } catch (error) {
            return this.debugLog("normalizeModule: caught error", error), context.throw(error), 0;
          }
        }) };
        args.ownedLifetimes?.forEach((lifetime) => this.scope.manage(lifetime)), this.module = args.module, this.memory = new ModuleMemory(this.module), this.ffi = args.ffi, this.rt = args.rt, this.callbacks = args.callbacks, this.scope.manage(this.rt), this.callbacks.setRuntimeCallbacks(this.rt.value, this.cToHostCallbacks), this.executePendingJobs = this.executePendingJobs.bind(this), QTS_DEBUG && this.setDebugMode(true);
      }
      get alive() {
        return this.scope.alive;
      }
      dispose() {
        return this.scope.dispose();
      }
      newContext(options = {}) {
        let intrinsics = intrinsicsToFlags(options.intrinsics), ctx = new Lifetime(options.contextPointer || this.ffi.QTS_NewContext(this.rt.value, intrinsics), void 0, (ctx_ptr) => {
          this.contextMap.delete(ctx_ptr), this.callbacks.deleteContext(ctx_ptr), this.ffi.QTS_FreeContext(ctx_ptr);
        }), context = new QuickJSContext({ module: this.module, ctx, ffi: this.ffi, rt: this.rt, ownedLifetimes: options.ownedLifetimes, runtime: this, callbacks: this.callbacks });
        return this.contextMap.set(ctx.value, context), context;
      }
      setModuleLoader(moduleLoader, moduleNormalizer) {
        this.moduleLoader = moduleLoader, this.moduleNormalizer = moduleNormalizer, this.ffi.QTS_RuntimeEnableModuleLoader(this.rt.value, this.moduleNormalizer ? 1 : 0);
      }
      removeModuleLoader() {
        this.moduleLoader = void 0, this.ffi.QTS_RuntimeDisableModuleLoader(this.rt.value);
      }
      hasPendingJob() {
        return !!this.ffi.QTS_IsJobPending(this.rt.value);
      }
      setInterruptHandler(cb) {
        let prevInterruptHandler = this.interruptHandler;
        this.interruptHandler = cb, prevInterruptHandler || this.ffi.QTS_RuntimeEnableInterruptHandler(this.rt.value);
      }
      removeInterruptHandler() {
        this.interruptHandler && (this.ffi.QTS_RuntimeDisableInterruptHandler(this.rt.value), this.interruptHandler = void 0);
      }
      executePendingJobs(maxJobsToExecute = -1) {
        let ctxPtrOut = this.memory.newMutablePointerArray(1), valuePtr = this.ffi.QTS_ExecutePendingJob(this.rt.value, maxJobsToExecute ?? -1, ctxPtrOut.value.ptr), ctxPtr = ctxPtrOut.value.typedArray[0];
        if (ctxPtrOut.dispose(), ctxPtr === 0) return this.ffi.QTS_FreeValuePointerRuntime(this.rt.value, valuePtr), DisposableResult.success(0);
        let context = this.contextMap.get(ctxPtr) ?? this.newContext({ contextPointer: ctxPtr }), resultValue = context.getMemory(this.rt.value).heapValueHandle(valuePtr);
        if (context.typeof(resultValue) === "number") {
          let executedJobs = context.getNumber(resultValue);
          return resultValue.dispose(), DisposableResult.success(executedJobs);
        } else {
          let error = Object.assign(resultValue, { context });
          return DisposableResult.fail(error, (error2) => context.unwrapResult(error2));
        }
      }
      setMemoryLimit(limitBytes) {
        if (limitBytes < 0 && limitBytes !== -1) throw new Error("Cannot set memory limit to negative number. To unset, pass -1");
        this.ffi.QTS_RuntimeSetMemoryLimit(this.rt.value, limitBytes);
      }
      computeMemoryUsage() {
        let serviceContextMemory = this.getSystemContext().getMemory(this.rt.value);
        return serviceContextMemory.heapValueHandle(this.ffi.QTS_RuntimeComputeMemoryUsage(this.rt.value, serviceContextMemory.ctx.value));
      }
      dumpMemoryUsage() {
        return this.memory.consumeHeapCharPointer(this.ffi.QTS_RuntimeDumpMemoryUsage(this.rt.value));
      }
      setMaxStackSize(stackSize) {
        if (stackSize < 0) throw new Error("Cannot set memory limit to negative number. To unset, pass 0.");
        this.ffi.QTS_RuntimeSetMaxStackSize(this.rt.value, stackSize);
      }
      assertOwned(handle) {
        if (handle.owner && handle.owner.rt !== this.rt) throw new QuickJSWrongOwner(`Handle is not owned by this runtime: ${handle.owner.rt.value} != ${this.rt.value}`);
      }
      setDebugMode(enabled) {
        this._debugMode = enabled, this.ffi.DEBUG && this.rt.alive && this.ffi.QTS_SetDebugLogEnabled(this.rt.value, enabled ? 1 : 0);
      }
      isDebugMode() {
        return this._debugMode;
      }
      debugLog(...msg) {
        this._debugMode && console.log("quickjs-emscripten:", ...msg);
      }
      [/* @__PURE__ */ Symbol.for("nodejs.util.inspect.custom")]() {
        return this.alive ? `${this.constructor.name} { rt: ${this.rt.value} }` : `${this.constructor.name} { disposed }`;
      }
      getSystemContext() {
        return this.context || (this.context = this.scope.manage(this.newContext())), this.context;
      }
    };
    QuickJSEmscriptenModuleCallbacks = class {
      constructor(args) {
        this.freeHostRef = args.freeHostRef, this.callFunction = args.callFunction, this.shouldInterrupt = args.shouldInterrupt, this.loadModuleSource = args.loadModuleSource, this.normalizeModule = args.normalizeModule;
      }
    };
    QuickJSModuleCallbacks = class {
      constructor(module) {
        this.contextCallbacks = /* @__PURE__ */ new Map();
        this.runtimeCallbacks = /* @__PURE__ */ new Map();
        this.suspendedCount = 0;
        this.cToHostCallbacks = new QuickJSEmscriptenModuleCallbacks({ freeHostRef: (_asyncify, rt, host_ref_id) => {
          let runtimeCallbacks = this.runtimeCallbacks.get(rt);
          if (!runtimeCallbacks) throw new Error(`QuickJSRuntime(rt = ${rt}) not found when trying to free HostRef(id = ${host_ref_id})`);
          runtimeCallbacks.freeHostRef(rt, host_ref_id);
        }, callFunction: (asyncify, ctx, this_ptr, argc, argv, fn_id) => this.handleAsyncify(asyncify, () => {
          try {
            let vm = this.contextCallbacks.get(ctx);
            if (!vm) throw new Error(`QuickJSContext(ctx = ${ctx}) not found for C function call "${fn_id}"`);
            return vm.callFunction(ctx, this_ptr, argc, argv, fn_id);
          } catch (error) {
            return console.error("[C to host error: returning null]", error), 0;
          }
        }), shouldInterrupt: (asyncify, rt) => this.handleAsyncify(asyncify, () => {
          try {
            let vm = this.runtimeCallbacks.get(rt);
            if (!vm) throw new Error(`QuickJSRuntime(rt = ${rt}) not found for C interrupt`);
            return vm.shouldInterrupt(rt);
          } catch (error) {
            return console.error("[C to host interrupt: returning error]", error), 1;
          }
        }), loadModuleSource: (asyncify, rt, ctx, moduleName) => this.handleAsyncify(asyncify, () => {
          try {
            let runtimeCallbacks = this.runtimeCallbacks.get(rt);
            if (!runtimeCallbacks) throw new Error(`QuickJSRuntime(rt = ${rt}) not found for C module loader`);
            let loadModule = runtimeCallbacks.loadModuleSource;
            if (!loadModule) throw new Error(`QuickJSRuntime(rt = ${rt}) does not support module loading`);
            return loadModule(rt, ctx, moduleName);
          } catch (error) {
            return console.error("[C to host module loader error: returning null]", error), 0;
          }
        }), normalizeModule: (asyncify, rt, ctx, moduleBaseName, moduleName) => this.handleAsyncify(asyncify, () => {
          try {
            let runtimeCallbacks = this.runtimeCallbacks.get(rt);
            if (!runtimeCallbacks) throw new Error(`QuickJSRuntime(rt = ${rt}) not found for C module loader`);
            let normalizeModule = runtimeCallbacks.normalizeModule;
            if (!normalizeModule) throw new Error(`QuickJSRuntime(rt = ${rt}) does not support module loading`);
            return normalizeModule(rt, ctx, moduleBaseName, moduleName);
          } catch (error) {
            return console.error("[C to host module loader error: returning null]", error), 0;
          }
        }) });
        this.module = module, this.module.callbacks = this.cToHostCallbacks;
      }
      setRuntimeCallbacks(rt, callbacks) {
        this.runtimeCallbacks.set(rt, callbacks);
      }
      deleteRuntime(rt) {
        this.runtimeCallbacks.delete(rt);
      }
      setContextCallbacks(ctx, callbacks) {
        this.contextCallbacks.set(ctx, callbacks);
      }
      deleteContext(ctx) {
        this.contextCallbacks.delete(ctx);
      }
      handleAsyncify(asyncify, fn) {
        if (asyncify) return asyncify.handleSleep((done) => {
          try {
            let result = fn();
            if (!(result instanceof Promise)) {
              debugLog("asyncify.handleSleep: not suspending:", result), done(result);
              return;
            }
            if (this.suspended) throw new QuickJSAsyncifyError(`Already suspended at: ${this.suspended.stack}
Attempted to suspend at:`);
            this.suspended = new QuickJSAsyncifySuspended(`(${this.suspendedCount++})`), debugLog("asyncify.handleSleep: suspending:", this.suspended), result.then((resolvedResult) => {
              this.suspended = void 0, debugLog("asyncify.handleSleep: resolved:", resolvedResult), done(resolvedResult);
            }, (error) => {
              debugLog("asyncify.handleSleep: rejected:", error), console.error("QuickJS: cannot handle error in suspended function", error), this.suspended = void 0;
            });
          } catch (error) {
            throw debugLog("asyncify.handleSleep: error:", error), this.suspended = void 0, error;
          }
        });
        let value = fn();
        if (value instanceof Promise) throw new Error("Promise return value not supported in non-asyncify context.");
        return value;
      }
    };
    QuickJSWASMModule = class {
      constructor(module, ffi) {
        this.module = module, this.ffi = ffi, this.callbacks = new QuickJSModuleCallbacks(module);
      }
      newRuntime(options = {}) {
        let rt = new Lifetime(this.ffi.QTS_NewRuntime(), void 0, (rt_ptr) => {
          this.ffi.QTS_FreeRuntime(rt_ptr), this.callbacks.deleteRuntime(rt_ptr);
        }), runtime = new QuickJSRuntime({ module: this.module, callbacks: this.callbacks, ffi: this.ffi, rt });
        return applyBaseRuntimeOptions(runtime, options), options.moduleLoader && runtime.setModuleLoader(options.moduleLoader), runtime;
      }
      newContext(options = {}) {
        let runtime = this.newRuntime(), context = runtime.newContext({ ...options, ownedLifetimes: concat(runtime, options.ownedLifetimes) });
        return runtime.context = context, context;
      }
      evalCode(code, options = {}) {
        return Scope.withScope((scope) => {
          let vm = scope.manage(this.newContext());
          applyModuleEvalRuntimeOptions(vm.runtime, options);
          let result = vm.evalCode(code, "eval.js");
          if (options.memoryLimitBytes !== void 0 && vm.runtime.setMemoryLimit(-1), result.error) throw vm.dump(scope.manage(result.error));
          return vm.dump(scope.manage(result.value));
        });
      }
      getWasmMemory() {
        let memory = this.module.quickjsEmscriptenInit?.(() => {
        })?.getWasmMemory?.();
        if (!memory) throw new Error("Variant does not support getting WebAssembly.Memory");
        return memory;
      }
      getFFI() {
        return this.ffi;
      }
    };
  }
});

// node_modules/.pnpm/quickjs-emscripten-core@0.32.0/node_modules/quickjs-emscripten-core/dist/module-ES6BEMUI.mjs
var module_ES6BEMUI_exports = {};
__export(module_ES6BEMUI_exports, {
  QuickJSModuleCallbacks: () => QuickJSModuleCallbacks,
  QuickJSWASMModule: () => QuickJSWASMModule,
  applyBaseRuntimeOptions: () => applyBaseRuntimeOptions,
  applyModuleEvalRuntimeOptions: () => applyModuleEvalRuntimeOptions
});
var init_module_ES6BEMUI = __esm({
  "node_modules/.pnpm/quickjs-emscripten-core@0.32.0/node_modules/quickjs-emscripten-core/dist/module-ES6BEMUI.mjs"() {
    init_chunk_V2S4ZYJR();
  }
});

// node_modules/.pnpm/@jitl+quickjs-wasmfile-release-sync@0.32.0/node_modules/@jitl/quickjs-wasmfile-release-sync/dist/ffi.mjs
var ffi_exports = {};
__export(ffi_exports, {
  QuickJSFFI: () => QuickJSFFI
});
var QuickJSFFI;
var init_ffi = __esm({
  "node_modules/.pnpm/@jitl+quickjs-wasmfile-release-sync@0.32.0/node_modules/@jitl/quickjs-wasmfile-release-sync/dist/ffi.mjs"() {
    QuickJSFFI = class {
      constructor(module) {
        this.module = module;
        this.DEBUG = false;
        this.QTS_Throw = this.module.cwrap("QTS_Throw", "number", ["number", "number"]);
        this.QTS_NewError = this.module.cwrap("QTS_NewError", "number", ["number"]);
        this.QTS_RuntimeSetMemoryLimit = this.module.cwrap("QTS_RuntimeSetMemoryLimit", null, ["number", "number"]);
        this.QTS_RuntimeComputeMemoryUsage = this.module.cwrap("QTS_RuntimeComputeMemoryUsage", "number", ["number", "number"]);
        this.QTS_RuntimeDumpMemoryUsage = this.module.cwrap("QTS_RuntimeDumpMemoryUsage", "number", ["number"]);
        this.QTS_RecoverableLeakCheck = this.module.cwrap("QTS_RecoverableLeakCheck", "number", []);
        this.QTS_BuildIsSanitizeLeak = this.module.cwrap("QTS_BuildIsSanitizeLeak", "number", []);
        this.QTS_RuntimeSetMaxStackSize = this.module.cwrap("QTS_RuntimeSetMaxStackSize", null, ["number", "number"]);
        this.QTS_GetUndefined = this.module.cwrap("QTS_GetUndefined", "number", []);
        this.QTS_GetNull = this.module.cwrap("QTS_GetNull", "number", []);
        this.QTS_GetFalse = this.module.cwrap("QTS_GetFalse", "number", []);
        this.QTS_GetTrue = this.module.cwrap("QTS_GetTrue", "number", []);
        this.QTS_NewHostRef = this.module.cwrap("QTS_NewHostRef", "number", ["number", "number"]);
        this.QTS_GetHostRefId = this.module.cwrap("QTS_GetHostRefId", "number", ["number"]);
        this.QTS_NewRuntime = this.module.cwrap("QTS_NewRuntime", "number", []);
        this.QTS_FreeRuntime = this.module.cwrap("QTS_FreeRuntime", null, ["number"]);
        this.QTS_NewContext = this.module.cwrap("QTS_NewContext", "number", ["number", "number"]);
        this.QTS_FreeContext = this.module.cwrap("QTS_FreeContext", null, ["number"]);
        this.QTS_FreeValuePointer = this.module.cwrap("QTS_FreeValuePointer", null, ["number", "number"]);
        this.QTS_FreeValuePointerRuntime = this.module.cwrap("QTS_FreeValuePointerRuntime", null, ["number", "number"]);
        this.QTS_FreeVoidPointer = this.module.cwrap("QTS_FreeVoidPointer", null, ["number", "number"]);
        this.QTS_FreeCString = this.module.cwrap("QTS_FreeCString", null, ["number", "number"]);
        this.QTS_DupValuePointer = this.module.cwrap("QTS_DupValuePointer", "number", ["number", "number"]);
        this.QTS_NewObject = this.module.cwrap("QTS_NewObject", "number", ["number"]);
        this.QTS_NewObjectProto = this.module.cwrap("QTS_NewObjectProto", "number", ["number", "number"]);
        this.QTS_NewArray = this.module.cwrap("QTS_NewArray", "number", ["number"]);
        this.QTS_NewArrayBuffer = this.module.cwrap("QTS_NewArrayBuffer", "number", ["number", "number", "number"]);
        this.QTS_NewFloat64 = this.module.cwrap("QTS_NewFloat64", "number", ["number", "number"]);
        this.QTS_GetFloat64 = this.module.cwrap("QTS_GetFloat64", "number", ["number", "number"]);
        this.QTS_NewString = this.module.cwrap("QTS_NewString", "number", ["number", "number"]);
        this.QTS_GetString = this.module.cwrap("QTS_GetString", "number", ["number", "number"]);
        this.QTS_GetArrayBuffer = this.module.cwrap("QTS_GetArrayBuffer", "number", ["number", "number"]);
        this.QTS_GetArrayBufferLength = this.module.cwrap("QTS_GetArrayBufferLength", "number", ["number", "number"]);
        this.QTS_NewSymbol = this.module.cwrap("QTS_NewSymbol", "number", ["number", "number", "number"]);
        this.QTS_GetSymbolDescriptionOrKey = this.module.cwrap("QTS_GetSymbolDescriptionOrKey", "number", ["number", "number"]);
        this.QTS_IsGlobalSymbol = this.module.cwrap("QTS_IsGlobalSymbol", "number", ["number", "number"]);
        this.QTS_IsJobPending = this.module.cwrap("QTS_IsJobPending", "number", ["number"]);
        this.QTS_ExecutePendingJob = this.module.cwrap("QTS_ExecutePendingJob", "number", ["number", "number", "number"]);
        this.QTS_GetProp = this.module.cwrap("QTS_GetProp", "number", ["number", "number", "number"]);
        this.QTS_GetPropNumber = this.module.cwrap("QTS_GetPropNumber", "number", ["number", "number", "number"]);
        this.QTS_SetProp = this.module.cwrap("QTS_SetProp", null, ["number", "number", "number", "number"]);
        this.QTS_DefineProp = this.module.cwrap("QTS_DefineProp", null, ["number", "number", "number", "number", "number", "number", "boolean", "boolean", "boolean"]);
        this.QTS_GetOwnPropertyNames = this.module.cwrap("QTS_GetOwnPropertyNames", "number", ["number", "number", "number", "number", "number"]);
        this.QTS_Call = this.module.cwrap("QTS_Call", "number", ["number", "number", "number", "number", "number"]);
        this.QTS_ResolveException = this.module.cwrap("QTS_ResolveException", "number", ["number", "number"]);
        this.QTS_Dump = this.module.cwrap("QTS_Dump", "number", ["number", "number"]);
        this.QTS_Eval = this.module.cwrap("QTS_Eval", "number", ["number", "number", "number", "string", "number", "number"]);
        this.QTS_GetModuleNamespace = this.module.cwrap("QTS_GetModuleNamespace", "number", ["number", "number"]);
        this.QTS_Typeof = this.module.cwrap("QTS_Typeof", "number", ["number", "number"]);
        this.QTS_GetLength = this.module.cwrap("QTS_GetLength", "number", ["number", "number", "number"]);
        this.QTS_IsEqual = this.module.cwrap("QTS_IsEqual", "number", ["number", "number", "number", "number"]);
        this.QTS_GetGlobalObject = this.module.cwrap("QTS_GetGlobalObject", "number", ["number"]);
        this.QTS_NewPromiseCapability = this.module.cwrap("QTS_NewPromiseCapability", "number", ["number", "number"]);
        this.QTS_PromiseState = this.module.cwrap("QTS_PromiseState", "number", ["number", "number"]);
        this.QTS_PromiseResult = this.module.cwrap("QTS_PromiseResult", "number", ["number", "number"]);
        this.QTS_TestStringArg = this.module.cwrap("QTS_TestStringArg", null, ["string"]);
        this.QTS_GetDebugLogEnabled = this.module.cwrap("QTS_GetDebugLogEnabled", "number", ["number"]);
        this.QTS_SetDebugLogEnabled = this.module.cwrap("QTS_SetDebugLogEnabled", null, ["number", "number"]);
        this.QTS_BuildIsDebug = this.module.cwrap("QTS_BuildIsDebug", "number", []);
        this.QTS_BuildIsAsyncify = this.module.cwrap("QTS_BuildIsAsyncify", "number", []);
        this.QTS_NewFunction = this.module.cwrap("QTS_NewFunction", "number", ["number", "string", "number", "boolean", "number"]);
        this.QTS_ArgvGetJSValueConstPointer = this.module.cwrap("QTS_ArgvGetJSValueConstPointer", "number", ["number", "number"]);
        this.QTS_RuntimeEnableInterruptHandler = this.module.cwrap("QTS_RuntimeEnableInterruptHandler", null, ["number"]);
        this.QTS_RuntimeDisableInterruptHandler = this.module.cwrap("QTS_RuntimeDisableInterruptHandler", null, ["number"]);
        this.QTS_RuntimeEnableModuleLoader = this.module.cwrap("QTS_RuntimeEnableModuleLoader", null, ["number", "number"]);
        this.QTS_RuntimeDisableModuleLoader = this.module.cwrap("QTS_RuntimeDisableModuleLoader", null, ["number"]);
        this.QTS_bjson_encode = this.module.cwrap("QTS_bjson_encode", "number", ["number", "number"]);
        this.QTS_bjson_decode = this.module.cwrap("QTS_bjson_decode", "number", ["number", "number"]);
      }
    };
  }
});

// node_modules/.pnpm/@jitl+quickjs-wasmfile-release-sync@0.32.0/node_modules/@jitl/quickjs-wasmfile-release-sync/dist/emscripten-module.mjs
var emscripten_module_exports = {};
__export(emscripten_module_exports, {
  default: () => emscripten_module_default
});
async function QuickJSRaw(moduleArg = {}) {
  var moduleRtn;
  var d = moduleArg, aa = !!globalThis.window, n = !!globalThis.WorkerGlobalScope, q = globalThis.process?.versions?.node && "renderer" != globalThis.process?.type;
  if (q) {
    const { createRequire: a } = await import("node:module");
    var require2 = a(import.meta.url);
  }
  function r(a) {
    a = { log: a || function() {
    } };
    for (const c of r.Pa) c(a);
    return d.quickJSEmscriptenExtensions = a;
  }
  r.Pa = [];
  d.quickjsEmscriptenInit = r;
  r.Pa.push((a) => {
    a.getWasmMemory = function() {
      return t;
    };
  });
  var u = "./this.program", v = (a, c) => {
    throw c;
  }, w = import.meta.url, y = "", z, A;
  if (q) {
    var fs = require2("node:fs");
    w.startsWith("file:") && (y = require2("node:path").dirname(require2("node:url").fileURLToPath(w)) + "/");
    A = (a) => {
      a = B(a) ? new URL(a) : a;
      return fs.readFileSync(a);
    };
    z = async (a) => {
      a = B(a) ? new URL(a) : a;
      return fs.readFileSync(a, void 0);
    };
    1 < process.argv.length && (u = process.argv[1].replace(/\\/g, "/"));
    process.argv.slice(2);
    v = (a, c) => {
      process.exitCode = a;
      throw c;
    };
  } else if (aa || n) {
    try {
      y = new URL(".", w).href;
    } catch {
    }
    n && (A = (a) => {
      var c = new XMLHttpRequest();
      c.open("GET", a, false);
      c.responseType = "arraybuffer";
      c.send(null);
      return new Uint8Array(c.response);
    });
    z = async (a) => {
      if (B(a)) return new Promise((b, e) => {
        var f = new XMLHttpRequest();
        f.open("GET", a, true);
        f.responseType = "arraybuffer";
        f.onload = () => {
          200 == f.status || 0 == f.status && f.response ? b(f.response) : e(f.status);
        };
        f.onerror = e;
        f.send(null);
      });
      var c = await fetch(a, { credentials: "same-origin" });
      if (c.ok) return c.arrayBuffer();
      throw Error(c.status + " : " + c.url);
    };
  }
  var C = console.log.bind(console), D = console.error.bind(console), E, F = false, G, B = (a) => a.startsWith("file://"), H, I, J, K, L, M, ba = false;
  function ca() {
    var a = t.buffer;
    d.HEAP8 = J = new Int8Array(a);
    new Int16Array(a);
    d.HEAPU8 = K = new Uint8Array(a);
    new Uint16Array(a);
    L = new Int32Array(a);
    M = new Uint32Array(a);
    new Float32Array(a);
    new Float64Array(a);
    new BigInt64Array(a);
    new BigUint64Array(a);
  }
  function N(a) {
    d.onAbort?.(a);
    a = "Aborted(" + a + ")";
    D(a);
    F = true;
    a = new WebAssembly.RuntimeError(a + ". Build with -sASSERTIONS for more info.");
    I?.(a);
    throw a;
  }
  var O;
  async function da(a) {
    if (!E) try {
      var c = await z(a);
      return new Uint8Array(c);
    } catch {
    }
    if (a == O && E) a = new Uint8Array(E);
    else if (A) a = A(a);
    else throw "both async and sync fetching of the wasm failed";
    return a;
  }
  async function ea(a, c) {
    try {
      var b = await da(a);
      return await WebAssembly.instantiate(b, c);
    } catch (e) {
      D(`failed to asynchronously prepare wasm: ${e}`), N(e);
    }
  }
  async function fa(a) {
    var c = O;
    if (!E && !B(c) && !q) try {
      var b = fetch(c, { credentials: "same-origin" });
      return await WebAssembly.instantiateStreaming(b, a);
    } catch (e) {
      D(`wasm streaming compile failed: ${e}`), D("falling back to ArrayBuffer instantiation");
    }
    return ea(c, a);
  }
  class P {
    name = "ExitStatus";
    constructor(a) {
      this.message = `Program terminated with exit(${a})`;
      this.status = a;
    }
  }
  var ha = (a) => {
    for (; 0 < a.length; ) a.shift()(d);
  }, ia = [], ja = [], ka = () => {
    var a = d.preRun.shift();
    ja.push(a);
  }, Q = true, t, la = new TextDecoder(), ma = (a, c, b, e) => {
    b = c + b;
    if (e) return b;
    for (; a[c] && !(c >= b); ) ++c;
    return c;
  }, R = (a, c, b) => a ? la.decode(K.subarray(a, ma(K, a, c, b))) : "", S = 0, na = [0, 31, 60, 91, 121, 152, 182, 213, 244, 274, 305, 335], oa = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334], T = {}, pa = (a) => {
    G = a;
    Q || 0 < S || (d.onExit?.(a), F = true);
    v(a, new P(a));
  }, qa = (a) => {
    if (!F) try {
      a();
    } catch (c) {
      c instanceof P || "unwind" == c || v(1, c);
    } finally {
      if (!(Q || 0 < S)) try {
        G = a = G, pa(a);
      } catch (c) {
        c instanceof P || "unwind" == c || v(1, c);
      }
    }
  }, U = (a, c, b) => {
    var e = K;
    if (!(0 < b)) return 0;
    var f = c;
    b = c + b - 1;
    for (var g = 0; g < a.length; ++g) {
      var h = a.codePointAt(g);
      if (127 >= h) {
        if (c >= b) break;
        e[c++] = h;
      } else if (2047 >= h) {
        if (c + 1 >= b) break;
        e[c++] = 192 | h >> 6;
        e[c++] = 128 | h & 63;
      } else if (65535 >= h) {
        if (c + 2 >= b) break;
        e[c++] = 224 | h >> 12;
        e[c++] = 128 | h >> 6 & 63;
        e[c++] = 128 | h & 63;
      } else {
        if (c + 3 >= b) break;
        e[c++] = 240 | h >> 18;
        e[c++] = 128 | h >> 12 & 63;
        e[c++] = 128 | h >> 6 & 63;
        e[c++] = 128 | h & 63;
        g++;
      }
    }
    e[c] = 0;
    return c - f;
  }, V = {}, ra = () => {
    if (!W) {
      var a = {
        USER: "web_user",
        LOGNAME: "web_user",
        PATH: "/",
        PWD: "/",
        HOME: "/home/web_user",
        LANG: (globalThis.navigator?.language ?? "C").replace("-", "_") + ".UTF-8",
        _: u || "./this.program"
      }, c;
      for (c in V) void 0 === V[c] ? delete a[c] : a[c] = V[c];
      var b = [];
      for (c in a) b.push(`${c}=${a[c]}`);
      W = b;
    }
    return W;
  }, W, X = (a) => {
    for (var c = 0, b = 0; b < a.length; ++b) {
      var e = a.charCodeAt(b);
      127 >= e ? c++ : 2047 >= e ? c += 2 : 55296 <= e && 57343 >= e ? (c += 4, ++b) : c += 3;
    }
    return c;
  }, sa = [null, [], []], va = (a, c, b, e) => {
    var f = { string: (k) => {
      var l = 0;
      if (null !== k && void 0 !== k && 0 !== k) {
        l = X(k) + 1;
        var p = Y(l);
        U(
          k,
          p,
          l
        );
        l = p;
      }
      return l;
    }, array: (k) => {
      var l = Y(k.length);
      J.set(k, l);
      return l;
    } };
    a = d["_" + a];
    var g = [], h = 0;
    if (e) for (var m = 0; m < e.length; m++) {
      var x = f[b[m]];
      x ? (0 === h && (h = ta()), g[m] = x(e[m])) : g[m] = e[m];
    }
    b = a(...g);
    return b = (function(k) {
      0 !== h && ua(h);
      return "string" === c ? R(k) : "boolean" === c ? !!k : k;
    })(b);
  };
  d.wasmMemory ? t = d.wasmMemory : t = new WebAssembly.Memory({ initial: (d.INITIAL_MEMORY || 16777216) / 65536, maximum: 32768 });
  ca();
  d.noExitRuntime && (Q = d.noExitRuntime);
  d.print && (C = d.print);
  d.printErr && (D = d.printErr);
  d.wasmBinary && (E = d.wasmBinary);
  d.thisProgram && (u = d.thisProgram);
  if (d.preInit) for ("function" == typeof d.preInit && (d.preInit = [d.preInit]); 0 < d.preInit.length; ) d.preInit.shift()();
  d.cwrap = (a, c, b, e) => {
    var f = !b || b.every((g) => "number" === g || "boolean" === g);
    return "string" !== c && f && !e ? d["_" + a] : (...g) => va(a, c, b, g);
  };
  d.UTF8ToString = R;
  d.stringToUTF8 = (a, c, b) => U(a, c, b);
  d.lengthBytesUTF8 = X;
  var wa, ua, Y, ta, xa = { b: (a, c, b, e) => N(`Assertion failed: ${R(a)}, at: ` + [c ? R(c) : "unknown filename", b, e ? R(e) : "unknown function"]), q: () => N(""), l: () => {
    Q = false;
    S = 0;
  }, m: function(a, c) {
    a = -9007199254740992 > a || 9007199254740992 < a ? NaN : Number(a);
    a = new Date(1e3 * a);
    L[c >> 2] = a.getSeconds();
    L[c + 4 >> 2] = a.getMinutes();
    L[c + 8 >> 2] = a.getHours();
    L[c + 12 >> 2] = a.getDate();
    L[c + 16 >> 2] = a.getMonth();
    L[c + 20 >> 2] = a.getFullYear() - 1900;
    L[c + 24 >> 2] = a.getDay();
    var b = a.getFullYear();
    L[c + 28 >> 2] = (0 !== b % 4 || 0 === b % 100 && 0 !== b % 400 ? oa : na)[a.getMonth()] + a.getDate() - 1 | 0;
    L[c + 36 >> 2] = -(60 * a.getTimezoneOffset());
    b = new Date(a.getFullYear(), 6, 1).getTimezoneOffset();
    var e = new Date(a.getFullYear(), 0, 1).getTimezoneOffset();
    L[c + 32 >> 2] = (b != e && a.getTimezoneOffset() == Math.min(e, b)) | 0;
  }, j: (a, c) => {
    T[a] && (clearTimeout(T[a].id), delete T[a]);
    if (!c) return 0;
    var b = setTimeout(() => {
      delete T[a];
      qa(() => wa(a, performance.now()));
    }, c);
    T[a] = { id: b, Qa: c };
    return 0;
  }, n: (a, c, b, e) => {
    var f = (/* @__PURE__ */ new Date()).getFullYear(), g = new Date(f, 0, 1).getTimezoneOffset();
    f = new Date(f, 6, 1).getTimezoneOffset();
    M[a >> 2] = 60 * Math.max(g, f);
    L[c >> 2] = Number(g != f);
    c = (h) => {
      var m = Math.abs(h);
      return `UTC${0 <= h ? "-" : "+"}${String(Math.floor(m / 60)).padStart(2, "0")}${String(m % 60).padStart(2, "0")}`;
    };
    a = c(g);
    c = c(f);
    f < g ? (U(a, b, 17), U(c, e, 17)) : (U(a, e, 17), U(c, b, 17));
  }, p: () => Date.now(), k: (a) => {
    var c = K.length;
    a >>>= 0;
    if (2147483648 < a) return false;
    for (var b = 1; 4 >= b; b *= 2) {
      var e = c * (1 + 0.2 / b);
      e = Math.min(e, a + 100663296);
      a: {
        e = (Math.min(2147483648, 65536 * Math.ceil(Math.max(a, e) / 65536)) - t.buffer.byteLength + 65535) / 65536 | 0;
        try {
          t.grow(e);
          ca();
          var f = 1;
          break a;
        } catch (g) {
        }
        f = void 0;
      }
      if (f) return true;
    }
    return false;
  }, e: (a, c) => {
    var b = 0, e = 0, f;
    for (f of ra()) {
      var g = c + b;
      M[a + e >> 2] = g;
      b += U(f, g, Infinity) + 1;
      e += 4;
    }
    return 0;
  }, f: (a, c) => {
    var b = ra();
    M[a >> 2] = b.length;
    a = 0;
    for (var e of b) a += X(e) + 1;
    M[c >> 2] = a;
    return 0;
  }, d: () => 52, o: function() {
    return 70;
  }, c: (a, c, b, e) => {
    for (var f = 0, g = 0; g < b; g++) {
      var h = M[c >> 2], m = M[c + 4 >> 2];
      c += 8;
      for (var x = 0; x < m; x++) {
        var k = a, l = K[h + x], p = sa[k];
        0 === l || 10 === l ? (k = 1 === k ? C : D, l = ma(p, 0), l = la.decode(p.buffer ? p.subarray(0, l) : new Uint8Array(p.slice(0, l))), k(l), p.length = 0) : p.push(l);
      }
      f += m;
    }
    M[e >> 2] = f;
    return 0;
  }, a: t, r: pa, s: function(a, c, b, e, f) {
    return d.callbacks.callFunction(void 0, a, c, b, e, f);
  }, i: function(a) {
    return d.callbacks.shouldInterrupt(void 0, a);
  }, h: function(a, c, b) {
    b = R(b);
    return d.callbacks.loadModuleSource(void 0, a, c, b);
  }, g: function(a, c, b, e) {
    b = R(b);
    e = R(e);
    return d.callbacks.normalizeModule(void 0, a, c, b, e);
  }, t: function(a, c) {
    d.callbacks.freeHostRef(void 0, a, c);
  } }, Z;
  Z = await (async function() {
    function a(b) {
      b = Z = b.exports;
      d._malloc = b.v;
      d._QTS_Throw = b.w;
      d._QTS_NewError = b.x;
      d._QTS_RuntimeSetMemoryLimit = b.y;
      d._QTS_RuntimeComputeMemoryUsage = b.z;
      d._QTS_RuntimeDumpMemoryUsage = b.A;
      d._QTS_RecoverableLeakCheck = b.B;
      d._QTS_BuildIsSanitizeLeak = b.C;
      d._QTS_RuntimeSetMaxStackSize = b.D;
      d._QTS_GetUndefined = b.E;
      d._QTS_GetNull = b.F;
      d._QTS_GetFalse = b.G;
      d._QTS_GetTrue = b.H;
      d._QTS_NewHostRef = b.I;
      d._QTS_GetHostRefId = b.J;
      d._QTS_NewRuntime = b.K;
      d._QTS_FreeRuntime = b.L;
      d._free = b.M;
      d._QTS_NewContext = b.N;
      d._QTS_FreeContext = b.O;
      d._QTS_FreeValuePointer = b.P;
      d._QTS_FreeValuePointerRuntime = b.Q;
      d._QTS_FreeVoidPointer = b.R;
      d._QTS_FreeCString = b.S;
      d._QTS_DupValuePointer = b.T;
      d._QTS_NewObject = b.U;
      d._QTS_NewObjectProto = b.V;
      d._QTS_NewArray = b.W;
      d._QTS_NewArrayBuffer = b.X;
      d._QTS_NewFloat64 = b.Y;
      d._QTS_GetFloat64 = b.Z;
      d._QTS_NewString = b._;
      d._QTS_GetString = b.$;
      d._QTS_GetArrayBuffer = b.aa;
      d._QTS_GetArrayBufferLength = b.ba;
      d._QTS_NewSymbol = b.ca;
      d._QTS_GetSymbolDescriptionOrKey = b.da;
      d._QTS_IsGlobalSymbol = b.ea;
      d._QTS_IsJobPending = b.fa;
      d._QTS_ExecutePendingJob = b.ga;
      d._QTS_GetProp = b.ha;
      d._QTS_GetPropNumber = b.ia;
      d._QTS_SetProp = b.ja;
      d._QTS_DefineProp = b.ka;
      d._QTS_GetOwnPropertyNames = b.la;
      d._QTS_Call = b.ma;
      d._QTS_ResolveException = b.na;
      d._QTS_Dump = b.oa;
      d._QTS_Eval = b.pa;
      d._QTS_GetModuleNamespace = b.qa;
      d._QTS_Typeof = b.ra;
      d._QTS_GetLength = b.sa;
      d._QTS_IsEqual = b.ta;
      d._QTS_GetGlobalObject = b.ua;
      d._QTS_NewPromiseCapability = b.va;
      d._QTS_PromiseState = b.wa;
      d._QTS_PromiseResult = b.xa;
      d._QTS_TestStringArg = b.ya;
      d._QTS_GetDebugLogEnabled = b.za;
      d._QTS_SetDebugLogEnabled = b.Aa;
      d._QTS_BuildIsDebug = b.Ba;
      d._QTS_BuildIsAsyncify = b.Ca;
      d._QTS_NewFunction = b.Da;
      d._QTS_ArgvGetJSValueConstPointer = b.Ea;
      d._QTS_RuntimeEnableInterruptHandler = b.Fa;
      d._QTS_RuntimeDisableInterruptHandler = b.Ga;
      d._QTS_RuntimeEnableModuleLoader = b.Ha;
      d._QTS_RuntimeDisableModuleLoader = b.Ia;
      d._QTS_bjson_encode = b.Ja;
      d._QTS_bjson_decode = b.Ka;
      wa = b.La;
      ua = b.Ma;
      Y = b.Na;
      ta = b.Oa;
      return Z;
    }
    var c = { a: xa };
    if (d.instantiateWasm) return new Promise((b) => {
      d.instantiateWasm(c, (e, f) => {
        b(a(e, f));
      });
    });
    O ??= d.locateFile ? d.locateFile ? d.locateFile("emscripten-module.wasm", y) : y + "emscripten-module.wasm" : new URL("emscripten-module.wasm", import.meta.url).href;
    return a((await fa(c)).instance);
  })();
  (function() {
    function a() {
      d.calledRun = true;
      if (!F) {
        ba = true;
        Z.u();
        H?.(d);
        d.onRuntimeInitialized?.();
        if (d.postRun) for ("function" == typeof d.postRun && (d.postRun = [d.postRun]); d.postRun.length; ) {
          var c = d.postRun.shift();
          ia.push(c);
        }
        ha(ia);
      }
    }
    if (d.preRun) for ("function" == typeof d.preRun && (d.preRun = [d.preRun]); d.preRun.length; ) ka();
    ha(ja);
    d.setStatus ? (d.setStatus("Running..."), setTimeout(() => {
      setTimeout(() => d.setStatus(""), 1);
      a();
    }, 1)) : a();
  })();
  ba ? moduleRtn = d : moduleRtn = new Promise((a, c) => {
    H = a;
    I = c;
  });
  ;
  return moduleRtn;
}
var emscripten_module_default;
var init_emscripten_module = __esm({
  "node_modules/.pnpm/@jitl+quickjs-wasmfile-release-sync@0.32.0/node_modules/@jitl/quickjs-wasmfile-release-sync/dist/emscripten-module.mjs"() {
    emscripten_module_default = QuickJSRaw;
  }
});

// src/commands/js-exec/worker.ts
import { stripTypeScriptTypes } from "node:module";
import { parentPort } from "node:worker_threads";

// node_modules/.pnpm/quickjs-emscripten-core@0.32.0/node_modules/quickjs-emscripten-core/dist/index.mjs
init_dist();
async function newQuickJSWASMModuleFromVariant(variantOrPromise) {
  let variant2 = smartUnwrap(await variantOrPromise), [wasmModuleLoader, QuickJSFFI2, { QuickJSWASMModule: QuickJSWASMModule2 }] = await Promise.all([variant2.importModuleLoader().then(smartUnwrap), variant2.importFFI(), Promise.resolve().then(() => (init_module_ES6BEMUI(), module_ES6BEMUI_exports)).then(smartUnwrap)]), wasmModule = await wasmModuleLoader();
  wasmModule.type = "sync";
  let ffi = new QuickJSFFI2(wasmModule);
  return new QuickJSWASMModule2(wasmModule, ffi);
}
function smartUnwrap(val) {
  return val && "default" in val && val.default ? val.default && "default" in val.default && val.default.default ? val.default.default : val.default : val;
}

// node_modules/.pnpm/@jitl+quickjs-wasmfile-release-sync@0.32.0/node_modules/@jitl/quickjs-wasmfile-release-sync/dist/index.mjs
var variant = { type: "sync", importFFI: () => Promise.resolve().then(() => (init_ffi(), ffi_exports)).then((mod) => mod.QuickJSFFI), importModuleLoader: () => Promise.resolve().then(() => (init_emscripten_module(), emscripten_module_exports)).then((mod) => mod.default) };
var src_default = variant;

// node_modules/.pnpm/quickjs-emscripten@0.32.0/node_modules/quickjs-emscripten/dist/chunk-OHAYRCBA.mjs
async function newQuickJSWASMModule(variantOrPromise = src_default) {
  return newQuickJSWASMModuleFromVariant(variantOrPromise);
}

// node_modules/.pnpm/quickjs-emscripten@0.32.0/node_modules/quickjs-emscripten/dist/index.mjs
var singleton;
var singletonPromise;
async function getQuickJS() {
  return singletonPromise ?? (singletonPromise = newQuickJSWASMModule().then((instance) => (singleton = instance, instance))), await singletonPromise;
}

// src/security/blocked-globals.ts
function getBlockedGlobals() {
  const globals = [
    // Direct code execution vectors
    {
      prop: "Function",
      target: globalThis,
      violationType: "function_constructor",
      strategy: "throw",
      reason: "Function constructor allows arbitrary code execution"
    },
    {
      prop: "eval",
      target: globalThis,
      violationType: "eval",
      strategy: "throw",
      reason: "eval() allows arbitrary code execution"
    },
    // Timer functions with string argument allow code execution
    {
      prop: "setTimeout",
      target: globalThis,
      violationType: "setTimeout",
      strategy: "throw",
      reason: "setTimeout with string argument allows code execution"
    },
    {
      prop: "setInterval",
      target: globalThis,
      violationType: "setInterval",
      strategy: "throw",
      reason: "setInterval with string argument allows code execution"
    },
    {
      prop: "setImmediate",
      target: globalThis,
      violationType: "setImmediate",
      strategy: "throw",
      reason: "setImmediate could be used to escape sandbox context"
    },
    // Note: We intentionally do NOT block `process` entirely because:
    // 1. Node.js internals (Promise resolution, etc.) use process.nextTick
    // 2. Blocking process entirely breaks normal async operation
    // 3. The primary code execution vectors (Function, eval) are already blocked
    // However, we DO block specific dangerous process properties.
    {
      prop: "env",
      target: process,
      violationType: "process_env",
      strategy: "throw",
      reason: "process.env could leak sensitive environment variables",
      // Node.js internals and bundled dependencies read these env vars
      // during module loading, file watching, and I/O within the
      // AsyncLocalStorage context. None are user secrets.
      allowedKeys: /* @__PURE__ */ new Set([
        // Node.js core
        "NODE_V8_COVERAGE",
        "NODE_DEBUG",
        "NODE_DEBUG_NATIVE",
        "NODE_COMPILE_CACHE",
        "WATCH_REPORT_DEPENDENCIES",
        // Dependencies
        "FORCE_COLOR",
        // chalk/supports-color
        "DEBUG",
        // debug package
        "UNDICI_NO_FG",
        // undici (Node.js fetch)
        "JEST_WORKER_ID",
        // jest/vitest worker detection
        "__MINIMATCH_TESTING_PLATFORM__",
        // minimatch
        "LOG_TOKENS",
        // query engine debug logging
        "LOG_STREAM"
        // query engine debug logging
      ])
    },
    {
      prop: "binding",
      target: process,
      violationType: "process_binding",
      strategy: "throw",
      reason: "process.binding provides access to native Node.js modules"
    },
    {
      prop: "_linkedBinding",
      target: process,
      violationType: "process_binding",
      strategy: "throw",
      reason: "process._linkedBinding provides access to native Node.js modules"
    },
    {
      prop: "dlopen",
      target: process,
      violationType: "process_dlopen",
      strategy: "throw",
      reason: "process.dlopen allows loading native addons"
    },
    {
      prop: "getBuiltinModule",
      target: process,
      violationType: "process_get_builtin_module",
      strategy: "throw",
      reason: "process.getBuiltinModule allows loading native Node.js modules (fs, child_process, vm)"
    },
    // Note: process.mainModule is handled specially in defense-in-depth-box.ts
    // and worker-defense-in-depth.ts because it may be undefined in ESM contexts
    // but we still want to block both reading and setting it.
    // Process control vectors
    {
      prop: "exit",
      target: process,
      violationType: "process_exit",
      strategy: "throw",
      reason: "process.exit could terminate the interpreter"
    },
    {
      prop: "abort",
      target: process,
      violationType: "process_exit",
      strategy: "throw",
      reason: "process.abort could crash the interpreter"
    },
    {
      prop: "kill",
      target: process,
      violationType: "process_kill",
      strategy: "throw",
      reason: "process.kill could signal other processes"
    },
    // Privilege escalation vectors
    {
      prop: "setuid",
      target: process,
      violationType: "process_setuid",
      strategy: "throw",
      reason: "process.setuid could escalate privileges"
    },
    {
      prop: "setgid",
      target: process,
      violationType: "process_setuid",
      strategy: "throw",
      reason: "process.setgid could escalate privileges"
    },
    {
      prop: "seteuid",
      target: process,
      violationType: "process_setuid",
      strategy: "throw",
      reason: "process.seteuid could escalate effective user privileges"
    },
    {
      prop: "setegid",
      target: process,
      violationType: "process_setuid",
      strategy: "throw",
      reason: "process.setegid could escalate effective group privileges"
    },
    {
      prop: "initgroups",
      target: process,
      violationType: "process_setuid",
      strategy: "throw",
      reason: "process.initgroups could modify supplementary group IDs"
    },
    {
      prop: "setgroups",
      target: process,
      violationType: "process_setuid",
      strategy: "throw",
      reason: "process.setgroups could modify supplementary group IDs"
    },
    // File permission manipulation
    {
      prop: "umask",
      target: process,
      violationType: "process_umask",
      strategy: "throw",
      reason: "process.umask could modify file creation permissions"
    },
    // Information disclosure vectors
    // Note: process.argv is an array (object) so gets an object proxy
    {
      prop: "argv",
      target: process,
      violationType: "process_argv",
      strategy: "throw",
      reason: "process.argv may contain secrets in CLI arguments"
    },
    // Note: process.execPath is a string primitive, handled specially
    // in defense-in-depth-box.ts and worker-defense-in-depth.ts
    // Note: process.connected is a boolean primitive, handled specially
    // in defense-in-depth-box.ts and worker-defense-in-depth.ts
    // Working directory access/manipulation
    {
      prop: "cwd",
      target: process,
      violationType: "process_chdir",
      strategy: "throw",
      reason: "process.cwd could disclose real host working directory path"
    },
    {
      prop: "chdir",
      target: process,
      violationType: "process_chdir",
      strategy: "throw",
      reason: "process.chdir could confuse the interpreter's CWD tracking"
    },
    // Diagnostic report (leaks full environment, host paths, system info)
    {
      prop: "report",
      target: process,
      violationType: "process_report",
      strategy: "throw",
      reason: "process.report could disclose full environment, host paths, and system info"
    },
    // Environment file loading (Node 21.7+)
    {
      prop: "loadEnvFile",
      target: process,
      violationType: "process_env",
      strategy: "throw",
      reason: "process.loadEnvFile could load env files bypassing env proxy"
    },
    // Exception handler manipulation
    {
      prop: "setUncaughtExceptionCaptureCallback",
      target: process,
      violationType: "process_exception_handler",
      strategy: "throw",
      reason: "setUncaughtExceptionCaptureCallback could intercept security errors"
    },
    // IPC communication vectors (may be undefined in non-IPC contexts)
    {
      prop: "send",
      target: process,
      violationType: "process_send",
      strategy: "throw",
      reason: "process.send could communicate with parent process in IPC contexts"
    },
    {
      prop: "channel",
      target: process,
      violationType: "process_channel",
      strategy: "throw",
      reason: "process.channel could access IPC channel to parent process"
    },
    // Timing side-channel vectors
    {
      prop: "cpuUsage",
      target: process,
      violationType: "process_timing",
      strategy: "throw",
      reason: "process.cpuUsage could enable timing side-channel attacks"
    },
    {
      prop: "memoryUsage",
      target: process,
      violationType: "process_timing",
      strategy: "throw",
      reason: "process.memoryUsage could enable timing side-channel attacks"
    },
    {
      prop: "hrtime",
      target: process,
      violationType: "process_timing",
      strategy: "throw",
      reason: "process.hrtime could enable timing side-channel attacks"
    },
    // We also don't block `require` because:
    // 1. It may not exist in all environments (ESM)
    // 2. import() is the modern escape vector and can't be blocked this way
    // Reference leak vectors
    {
      prop: "WeakRef",
      target: globalThis,
      violationType: "weak_ref",
      strategy: "throw",
      reason: "WeakRef could be used to leak references outside sandbox"
    },
    {
      prop: "FinalizationRegistry",
      target: globalThis,
      violationType: "finalization_registry",
      strategy: "throw",
      reason: "FinalizationRegistry could be used to leak references outside sandbox"
    },
    // Introspection/interception vectors (freeze instead of throw)
    // SECURITY RATIONALE: Reflect is frozen (not blocked) because:
    // 1. Defense infrastructure uses Reflect.apply/get/set/construct internally
    // 2. Frozen Reflect cannot be mutated but remains fully functional
    // 3. Reflect.construct(Function, ['code']) IS safe because globalThis.Function
    //    is replaced with a blocking proxy — Reflect.construct receives the proxy
    // 4. Security depends on NEVER leaking original Function/eval references.
    //    If an unpatched Function ref leaked, Reflect.construct would bypass defense.
    {
      prop: "Reflect",
      target: globalThis,
      violationType: "reflect",
      strategy: "freeze",
      reason: "Reflect provides introspection capabilities"
    },
    {
      prop: "Proxy",
      target: globalThis,
      violationType: "proxy",
      strategy: "throw",
      reason: "Proxy allows intercepting and modifying object behavior"
    },
    // WebAssembly allows arbitrary code execution
    {
      prop: "WebAssembly",
      target: globalThis,
      violationType: "webassembly",
      strategy: "throw",
      reason: "WebAssembly allows executing arbitrary compiled code"
    },
    // SharedArrayBuffer and Atomics can enable side-channel attacks
    {
      prop: "SharedArrayBuffer",
      target: globalThis,
      violationType: "shared_array_buffer",
      strategy: "throw",
      reason: "SharedArrayBuffer could enable side-channel communication or timing attacks"
    },
    {
      prop: "Atomics",
      target: globalThis,
      violationType: "atomics",
      strategy: "throw",
      reason: "Atomics could enable side-channel communication or timing attacks"
    },
    // Note: Error.prepareStackTrace is handled specially in defense-in-depth-box.ts
    // because we only want to block SETTING it, not reading (V8 reads it internally)
    // Timing side-channel: performance.now() provides sub-millisecond resolution
    // Note: Date.now() is intentionally NOT blocked — it's used for $SECONDS,
    // date command, and has only ~1ms resolution (vs process.hrtime at ns).
    {
      prop: "performance",
      target: globalThis,
      violationType: "performance_timing",
      strategy: "throw",
      reason: "performance.now() provides sub-millisecond timing for side-channel attacks"
    },
    // Block direct access to process.stdout and process.stderr to prevent
    // writing to the host's actual stdout/stderr, bypassing the interpreter's
    // output accumulation.
    {
      prop: "stdout",
      target: process,
      violationType: "process_stdout",
      strategy: "throw",
      reason: "process.stdout could bypass interpreter output to write to host stdout"
    },
    {
      prop: "stderr",
      target: process,
      violationType: "process_stderr",
      strategy: "throw",
      reason: "process.stderr could bypass interpreter output to write to host stderr"
    },
    // Prototype pollution vectors
    {
      prop: "__defineGetter__",
      target: Object.prototype,
      violationType: "prototype_mutation",
      strategy: "throw",
      reason: "__defineGetter__ allows prototype pollution via getter injection"
    },
    {
      prop: "__defineSetter__",
      target: Object.prototype,
      violationType: "prototype_mutation",
      strategy: "throw",
      reason: "__defineSetter__ allows prototype pollution via setter injection"
    },
    {
      prop: "__lookupGetter__",
      target: Object.prototype,
      violationType: "prototype_mutation",
      strategy: "throw",
      reason: "__lookupGetter__ enables introspection for prototype pollution attacks"
    },
    {
      prop: "__lookupSetter__",
      target: Object.prototype,
      violationType: "prototype_mutation",
      strategy: "throw",
      reason: "__lookupSetter__ enables introspection for prototype pollution attacks"
    },
    // Freeze JSON and Math to prevent mutation of built-in utility objects
    {
      prop: "JSON",
      target: globalThis,
      violationType: "json_mutation",
      strategy: "freeze",
      reason: "Freeze JSON to prevent mutation of parsing/serialization"
    },
    {
      prop: "Math",
      target: globalThis,
      violationType: "math_mutation",
      strategy: "freeze",
      reason: "Freeze Math to prevent mutation of math utilities"
    }
  ];
  try {
    const AsyncFunction = Object.getPrototypeOf(async () => {
    }).constructor;
    if (AsyncFunction && AsyncFunction !== Function) {
      globals.push({
        prop: "constructor",
        target: Object.getPrototypeOf(async () => {
        }),
        violationType: "async_function_constructor",
        strategy: "throw",
        reason: "AsyncFunction constructor allows arbitrary async code execution"
      });
    }
  } catch {
  }
  try {
    const GeneratorFunction = Object.getPrototypeOf(
      function* () {
      }
    ).constructor;
    if (GeneratorFunction && GeneratorFunction !== Function) {
      globals.push({
        prop: "constructor",
        target: Object.getPrototypeOf(function* () {
        }),
        violationType: "generator_function_constructor",
        strategy: "throw",
        reason: "GeneratorFunction constructor allows arbitrary generator code execution"
      });
    }
  } catch {
  }
  try {
    const AsyncGeneratorFunction = Object.getPrototypeOf(
      async function* () {
      }
    ).constructor;
    if (AsyncGeneratorFunction && AsyncGeneratorFunction !== Function && AsyncGeneratorFunction !== Object.getPrototypeOf(async () => {
    }).constructor) {
      globals.push({
        prop: "constructor",
        target: Object.getPrototypeOf(async function* () {
        }),
        violationType: "async_generator_function_constructor",
        strategy: "throw",
        reason: "AsyncGeneratorFunction constructor allows arbitrary async generator code execution"
      });
    }
  } catch {
  }
  return globals.filter((g) => {
    try {
      return g.target[g.prop] !== void 0;
    } catch {
      return false;
    }
  });
}

// src/security/defense-in-depth-box.ts
var IS_BROWSER = typeof __BROWSER__ !== "undefined" && __BROWSER__;
var AsyncLocalStorageClass = null;
if (!IS_BROWSER) {
  try {
    const { AsyncLocalStorage } = __require("node:async_hooks");
    AsyncLocalStorageClass = AsyncLocalStorage;
  } catch {
  }
}
var executionContext = !IS_BROWSER && AsyncLocalStorageClass ? new AsyncLocalStorageClass() : null;

// src/security/worker-defense-in-depth.ts
var DEFENSE_IN_DEPTH_NOTICE = "\n\nThis is a defense-in-depth measure and indicates a bug in just-bash. Please report this at security@vercel.com";
var WorkerSecurityViolationError = class extends Error {
  constructor(message, violation) {
    super(message + DEFENSE_IN_DEPTH_NOTICE);
    this.violation = violation;
    this.name = "WorkerSecurityViolationError";
  }
};
var MAX_STORED_VIOLATIONS = 1e3;
function generateExecutionId() {
  if (typeof crypto !== "undefined" && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, (c) => {
    const r = Math.random() * 16 | 0;
    const v = c === "x" ? r : r & 3 | 8;
    return v.toString(16);
  });
}
var WorkerDefenseInDepth = class {
  config;
  isActivated = false;
  originalDescriptors = [];
  violations = [];
  executionId;
  /**
   * Original Proxy constructor, captured before patching.
   * This is captured at instance creation time to ensure we get the unpatched version.
   */
  originalProxy;
  /**
   * Recursion guard to prevent infinite loops when proxy traps trigger
   * code that accesses the same proxied object (e.g., process.env).
   */
  inTrap = false;
  /**
   * Create and activate the worker defense layer.
   *
   * @param config - Configuration for the defense layer
   */
  constructor(config) {
    this.originalProxy = Proxy;
    this.config = config;
    this.executionId = generateExecutionId();
    if (config.enabled !== false) {
      this.activate();
    }
  }
  /**
   * Get statistics about the defense layer.
   */
  getStats() {
    return {
      violationsBlocked: this.violations.length,
      violations: [...this.violations],
      isActive: this.isActivated
    };
  }
  /**
   * Clear stored violations. Useful for testing.
   */
  clearViolations() {
    this.violations = [];
  }
  /**
   * Get the execution ID for this worker.
   */
  getExecutionId() {
    return this.executionId;
  }
  /**
   * Deactivate the defense layer and restore original globals.
   * Typically only needed for testing.
   */
  deactivate() {
    if (!this.isActivated) {
      return;
    }
    this.restorePatches();
    this.isActivated = false;
  }
  /**
   * Activate the defense layer by applying patches.
   */
  activate() {
    if (this.isActivated) {
      return;
    }
    this.applyPatches();
    this.isActivated = true;
  }
  /**
   * Get a human-readable path for a target object and property.
   */
  getPathForTarget(target, prop) {
    if (target === globalThis) {
      return `globalThis.${prop}`;
    }
    if (typeof process !== "undefined" && target === process) {
      return `process.${prop}`;
    }
    if (target === Error) {
      return `Error.${prop}`;
    }
    if (target === Function.prototype) {
      return `Function.prototype.${prop}`;
    }
    if (target === Object.prototype) {
      return `Object.prototype.${prop}`;
    }
    return `<object>.${prop}`;
  }
  /**
   * Record a violation and invoke the callback.
   * In worker context, blocking always happens (no audit mode context check).
   */
  recordViolation(type, path, message) {
    const violation = {
      timestamp: Date.now(),
      type,
      message,
      path,
      stack: new Error().stack,
      executionId: this.executionId
    };
    if (this.violations.length < MAX_STORED_VIOLATIONS) {
      this.violations.push(violation);
    }
    if (this.config.onViolation) {
      try {
        this.config.onViolation(violation);
      } catch (e) {
        console.debug(
          "[WorkerDefenseInDepth] onViolation callback threw:",
          e instanceof Error ? e.message : e
        );
      }
    }
    return violation;
  }
  /**
   * Create a blocking proxy for a function.
   * In worker context, always blocks (no context check needed).
   */
  createBlockingProxy(original, path, violationType) {
    const self = this;
    const auditMode = this.config.auditMode;
    return new this.originalProxy(original, {
      apply(target, thisArg, args) {
        const message = `${path} is blocked in worker context`;
        const violation = self.recordViolation(violationType, path, message);
        if (!auditMode) {
          throw new WorkerSecurityViolationError(message, violation);
        }
        return Reflect.apply(target, thisArg, args);
      },
      construct(target, args, newTarget) {
        const message = `${path} constructor is blocked in worker context`;
        const violation = self.recordViolation(violationType, path, message);
        if (!auditMode) {
          throw new WorkerSecurityViolationError(message, violation);
        }
        return Reflect.construct(target, args, newTarget);
      }
    });
  }
  /**
   * Create a blocking proxy for an object (blocks all property access).
   */
  createBlockingObjectProxy(original, path, violationType, allowedKeys) {
    const self = this;
    const auditMode = this.config.auditMode;
    return new this.originalProxy(original, {
      get(target, prop, receiver) {
        if (self.inTrap) {
          return Reflect.get(target, prop, receiver);
        }
        if (allowedKeys && typeof prop === "string" && allowedKeys.has(prop)) {
          return Reflect.get(target, prop, receiver);
        }
        self.inTrap = true;
        try {
          const fullPath = `${path}.${String(prop)}`;
          const message = `${fullPath} is blocked in worker context`;
          const violation = self.recordViolation(
            violationType,
            fullPath,
            message
          );
          if (!auditMode) {
            throw new WorkerSecurityViolationError(message, violation);
          }
          return Reflect.get(target, prop, receiver);
        } finally {
          self.inTrap = false;
        }
      },
      set(target, prop, value, receiver) {
        if (self.inTrap) {
          return Reflect.set(target, prop, value, receiver);
        }
        self.inTrap = true;
        try {
          const fullPath = `${path}.${String(prop)}`;
          const message = `${fullPath} modification is blocked in worker context`;
          const violation = self.recordViolation(
            violationType,
            fullPath,
            message
          );
          if (!auditMode) {
            throw new WorkerSecurityViolationError(message, violation);
          }
          return Reflect.set(target, prop, value, receiver);
        } finally {
          self.inTrap = false;
        }
      },
      ownKeys(target) {
        if (self.inTrap) {
          return Reflect.ownKeys(target);
        }
        self.inTrap = true;
        try {
          const message = `${path} enumeration is blocked in worker context`;
          const violation = self.recordViolation(violationType, path, message);
          if (!auditMode) {
            throw new WorkerSecurityViolationError(message, violation);
          }
          return Reflect.ownKeys(target);
        } finally {
          self.inTrap = false;
        }
      },
      getOwnPropertyDescriptor(target, prop) {
        if (self.inTrap) {
          return Reflect.getOwnPropertyDescriptor(target, prop);
        }
        self.inTrap = true;
        try {
          const fullPath = `${path}.${String(prop)}`;
          const message = `${fullPath} descriptor access is blocked in worker context`;
          const violation = self.recordViolation(
            violationType,
            fullPath,
            message
          );
          if (!auditMode) {
            throw new WorkerSecurityViolationError(message, violation);
          }
          return Reflect.getOwnPropertyDescriptor(target, prop);
        } finally {
          self.inTrap = false;
        }
      },
      has(target, prop) {
        if (self.inTrap) {
          return Reflect.has(target, prop);
        }
        self.inTrap = true;
        try {
          const fullPath = `${path}.${String(prop)}`;
          const message = `${fullPath} existence check is blocked in worker context`;
          const violation = self.recordViolation(
            violationType,
            fullPath,
            message
          );
          if (!auditMode) {
            throw new WorkerSecurityViolationError(message, violation);
          }
          return Reflect.has(target, prop);
        } finally {
          self.inTrap = false;
        }
      },
      deleteProperty(target, prop) {
        if (self.inTrap) {
          return Reflect.deleteProperty(target, prop);
        }
        self.inTrap = true;
        try {
          const fullPath = `${path}.${String(prop)}`;
          const message = `${fullPath} deletion is blocked in worker context`;
          const violation = self.recordViolation(
            violationType,
            fullPath,
            message
          );
          if (!auditMode) {
            throw new WorkerSecurityViolationError(message, violation);
          }
          return Reflect.deleteProperty(target, prop);
        } finally {
          self.inTrap = false;
        }
      },
      setPrototypeOf(target, proto) {
        if (self.inTrap) {
          return Reflect.setPrototypeOf(target, proto);
        }
        self.inTrap = true;
        try {
          const message = `${path} setPrototypeOf is blocked in worker context`;
          const violation = self.recordViolation(violationType, path, message);
          if (!auditMode) {
            throw new WorkerSecurityViolationError(message, violation);
          }
          return Reflect.setPrototypeOf(target, proto);
        } finally {
          self.inTrap = false;
        }
      },
      defineProperty(target, prop, descriptor) {
        if (self.inTrap) {
          return Reflect.defineProperty(target, prop, descriptor);
        }
        self.inTrap = true;
        try {
          const fullPath = `${path}.${String(prop)}`;
          const message = `${fullPath} defineProperty is blocked in worker context`;
          const violation = self.recordViolation(
            violationType,
            fullPath,
            message
          );
          if (!auditMode) {
            throw new WorkerSecurityViolationError(message, violation);
          }
          return Reflect.defineProperty(target, prop, descriptor);
        } finally {
          self.inTrap = false;
        }
      }
    });
  }
  /**
   * Apply security patches to dangerous globals.
   */
  applyPatches() {
    const blockedGlobals = getBlockedGlobals();
    const excludeTypes = new Set(this.config.excludeViolationTypes ?? []);
    for (const blocked of blockedGlobals) {
      if (excludeTypes.has(blocked.violationType)) {
        continue;
      }
      this.applyPatch(blocked);
    }
    if (!excludeTypes.has("function_constructor")) {
      this.protectConstructorChain(excludeTypes);
    }
    if (!excludeTypes.has("error_prepare_stack_trace")) {
      this.protectErrorPrepareStackTrace();
    }
    if (!excludeTypes.has("module_load")) {
      this.protectModuleLoad();
    }
    if (!excludeTypes.has("module_resolve_filename")) {
      this.protectModuleResolveFilename();
    }
    if (!excludeTypes.has("process_main_module")) {
      this.protectProcessMainModule();
    }
    if (!excludeTypes.has("process_exec_path")) {
      this.protectProcessExecPath();
    }
    if (!excludeTypes.has("process_connected")) {
      this.protectProcessConnected();
    }
    this.lockWellKnownSymbols();
    if (!excludeTypes.has("proxy")) {
      this.protectProxyRevocable();
    }
  }
  /**
   * Lock well-known Symbol properties on built-in constructors/prototypes.
   */
  lockWellKnownSymbols() {
    const lock = (obj, sym) => {
      try {
        const desc = Object.getOwnPropertyDescriptor(obj, sym);
        if (desc?.configurable) {
          if ("value" in desc) {
            Object.defineProperty(obj, sym, {
              ...desc,
              configurable: false,
              writable: false
            });
            return;
          }
          Object.defineProperty(obj, sym, { ...desc, configurable: false });
        }
      } catch {
      }
    };
    for (const ctor of [Array, Map, Set, RegExp, Promise]) {
      lock(ctor, Symbol.species);
    }
    for (const proto of [
      Array.prototype,
      String.prototype,
      Map.prototype,
      Set.prototype
    ]) {
      lock(proto, Symbol.iterator);
    }
    lock(Symbol.prototype, Symbol.toPrimitive);
    lock(Date.prototype, Symbol.toPrimitive);
    for (const sym of [
      Symbol.match,
      Symbol.matchAll,
      Symbol.replace,
      Symbol.search,
      Symbol.split
    ]) {
      lock(RegExp.prototype, sym);
    }
    lock(Function.prototype, Symbol.hasInstance);
    lock(Array.prototype, Symbol.unscopables);
    for (const proto of [
      Map.prototype,
      Set.prototype,
      Promise.prototype,
      ArrayBuffer.prototype
    ]) {
      lock(proto, Symbol.toStringTag);
    }
    try {
      const stackDesc = Object.getOwnPropertyDescriptor(
        Error,
        "stackTraceLimit"
      );
      this.originalDescriptors.push({
        target: Error,
        prop: "stackTraceLimit",
        descriptor: stackDesc
      });
      Object.defineProperty(Error, "stackTraceLimit", {
        value: Error.stackTraceLimit,
        writable: false,
        configurable: true
      });
    } catch {
    }
  }
  /**
   * Block Proxy.revocable to prevent bypassing Proxy constructor blocking.
   *
   * Proxy.revocable internally uses the real Proxy constructor, so it bypasses
   * our blocking proxy on globalThis.Proxy. We replace it with a wrapper that
   * always blocks in worker context.
   */
  protectProxyRevocable() {
    const self = this;
    const auditMode = this.config.auditMode;
    try {
      const originalRevocable = this.originalProxy.revocable;
      if (typeof originalRevocable !== "function") return;
      const descriptor = Object.getOwnPropertyDescriptor(
        this.originalProxy,
        "revocable"
      );
      this.originalDescriptors.push({
        target: this.originalProxy,
        prop: "revocable",
        descriptor
      });
      Object.defineProperty(this.originalProxy, "revocable", {
        value: function revocable(_target, _handler) {
          const message = "Proxy.revocable is blocked in worker context";
          const violation = self.recordViolation(
            "proxy",
            "Proxy.revocable",
            message
          );
          if (!auditMode) {
            throw new WorkerSecurityViolationError(message, violation);
          }
          return originalRevocable(_target, _handler);
        },
        writable: false,
        configurable: true
        // Must be configurable for restoration
      });
    } catch {
    }
  }
  /**
   * Protect against .constructor.constructor escape vector.
   * @param excludeTypes - Set of violation types to skip
   */
  protectConstructorChain(excludeTypes) {
    let AsyncFunction = null;
    let GeneratorFunction = null;
    let AsyncGeneratorFunction = null;
    try {
      AsyncFunction = Object.getPrototypeOf(async () => {
      }).constructor;
    } catch {
    }
    try {
      GeneratorFunction = Object.getPrototypeOf(function* () {
      }).constructor;
    } catch {
    }
    try {
      AsyncGeneratorFunction = Object.getPrototypeOf(
        async function* () {
        }
      ).constructor;
    } catch {
    }
    this.patchPrototypeConstructor(
      Function.prototype,
      "Function.prototype.constructor",
      "function_constructor"
    );
    if (!excludeTypes.has("async_function_constructor") && AsyncFunction && AsyncFunction !== Function) {
      this.patchPrototypeConstructor(
        AsyncFunction.prototype,
        "AsyncFunction.prototype.constructor",
        "async_function_constructor"
      );
    }
    if (!excludeTypes.has("generator_function_constructor") && GeneratorFunction && GeneratorFunction !== Function) {
      this.patchPrototypeConstructor(
        GeneratorFunction.prototype,
        "GeneratorFunction.prototype.constructor",
        "generator_function_constructor"
      );
    }
    if (!excludeTypes.has("async_generator_function_constructor") && AsyncGeneratorFunction && AsyncGeneratorFunction !== Function && AsyncGeneratorFunction !== AsyncFunction) {
      this.patchPrototypeConstructor(
        AsyncGeneratorFunction.prototype,
        "AsyncGeneratorFunction.prototype.constructor",
        "async_generator_function_constructor"
      );
    }
  }
  /**
   * Protect Error.prepareStackTrace from being set.
   */
  protectErrorPrepareStackTrace() {
    const self = this;
    const auditMode = this.config.auditMode;
    try {
      const originalDescriptor = Object.getOwnPropertyDescriptor(
        Error,
        "prepareStackTrace"
      );
      this.originalDescriptors.push({
        target: Error,
        prop: "prepareStackTrace",
        descriptor: originalDescriptor
      });
      let currentValue = originalDescriptor?.value;
      Object.defineProperty(Error, "prepareStackTrace", {
        get() {
          return currentValue;
        },
        set(value) {
          const message = "Error.prepareStackTrace modification is blocked in worker context";
          const violation = self.recordViolation(
            "error_prepare_stack_trace",
            "Error.prepareStackTrace",
            message
          );
          if (!auditMode) {
            throw new WorkerSecurityViolationError(message, violation);
          }
          currentValue = value;
        },
        configurable: true
      });
    } catch {
    }
  }
  /**
   * Patch a prototype's constructor property.
   *
   * Returns a proxy that allows reading properties (like .name) but blocks
   * calling the constructor as a function (which would allow code execution).
   */
  patchPrototypeConstructor(prototype, path, violationType) {
    const self = this;
    const auditMode = this.config.auditMode;
    try {
      const originalDescriptor = Object.getOwnPropertyDescriptor(
        prototype,
        "constructor"
      );
      this.originalDescriptors.push({
        target: prototype,
        prop: "constructor",
        descriptor: originalDescriptor
      });
      const originalValue = originalDescriptor?.value;
      const constructorProxy = originalValue && typeof originalValue === "function" ? new this.originalProxy(originalValue, {
        apply(_target, _thisArg, _args) {
          const message = `${path} invocation is blocked in worker context`;
          const violation = self.recordViolation(
            violationType,
            path,
            message
          );
          if (!auditMode) {
            throw new WorkerSecurityViolationError(message, violation);
          }
          return void 0;
        },
        construct(_target, _args, _newTarget) {
          const message = `${path} construction is blocked in worker context`;
          const violation = self.recordViolation(
            violationType,
            path,
            message
          );
          if (!auditMode) {
            throw new WorkerSecurityViolationError(message, violation);
          }
          return {};
        },
        // Allow all property access (like .name, .prototype, etc.)
        get(target, prop, receiver) {
          return Reflect.get(target, prop, receiver);
        },
        getPrototypeOf(target) {
          return Reflect.getPrototypeOf(target);
        },
        has(target, prop) {
          return Reflect.has(target, prop);
        },
        ownKeys(target) {
          return Reflect.ownKeys(target);
        },
        getOwnPropertyDescriptor(target, prop) {
          return Reflect.getOwnPropertyDescriptor(target, prop);
        }
      }) : originalValue;
      Object.defineProperty(prototype, "constructor", {
        get() {
          return constructorProxy;
        },
        set(value) {
          const message = `${path} modification is blocked in worker context`;
          const violation = self.recordViolation(violationType, path, message);
          if (!auditMode) {
            throw new WorkerSecurityViolationError(message, violation);
          }
          Object.defineProperty(this, "constructor", {
            value,
            writable: true,
            configurable: true
          });
        },
        configurable: true
      });
    } catch {
    }
  }
  /**
   * Protect process.mainModule from being accessed or set.
   *
   * The attack vector is:
   * ```
   * process.mainModule.require('child_process').execSync('whoami')
   * process.mainModule.constructor._load('vm')
   * ```
   *
   * process.mainModule may be undefined in ESM contexts but could exist in
   * CommonJS workers. We block both reading and setting.
   */
  protectProcessMainModule() {
    if (typeof process === "undefined") return;
    const self = this;
    const auditMode = this.config.auditMode;
    try {
      const originalDescriptor = Object.getOwnPropertyDescriptor(
        process,
        "mainModule"
      );
      this.originalDescriptors.push({
        target: process,
        prop: "mainModule",
        descriptor: originalDescriptor
      });
      const currentValue = originalDescriptor?.value;
      if (currentValue !== void 0) {
        Object.defineProperty(process, "mainModule", {
          get() {
            const message = "process.mainModule access is blocked in worker context";
            const violation = self.recordViolation(
              "process_main_module",
              "process.mainModule",
              message
            );
            if (!auditMode) {
              throw new WorkerSecurityViolationError(message, violation);
            }
            return currentValue;
          },
          set(value) {
            const message = "process.mainModule modification is blocked in worker context";
            const violation = self.recordViolation(
              "process_main_module",
              "process.mainModule",
              message
            );
            if (!auditMode) {
              throw new WorkerSecurityViolationError(message, violation);
            }
            Object.defineProperty(process, "mainModule", {
              value,
              writable: true,
              configurable: true
            });
          },
          configurable: true
        });
      }
    } catch {
    }
  }
  /**
   * Protect process.execPath from being read or set in worker context.
   *
   * process.execPath is a string primitive (not an object), so it cannot be
   * proxied via the normal blocked globals mechanism. We use Object.defineProperty
   * with getter/setter (same pattern as protectProcessMainModule).
   */
  protectProcessExecPath() {
    if (typeof process === "undefined") return;
    const self = this;
    const auditMode = this.config.auditMode;
    try {
      const originalDescriptor = Object.getOwnPropertyDescriptor(
        process,
        "execPath"
      );
      this.originalDescriptors.push({
        target: process,
        prop: "execPath",
        descriptor: originalDescriptor
      });
      const currentValue = originalDescriptor?.value ?? process.execPath;
      Object.defineProperty(process, "execPath", {
        get() {
          const message = "process.execPath access is blocked in worker context";
          const violation = self.recordViolation(
            "process_exec_path",
            "process.execPath",
            message
          );
          if (!auditMode) {
            throw new WorkerSecurityViolationError(message, violation);
          }
          return currentValue;
        },
        set(value) {
          const message = "process.execPath modification is blocked in worker context";
          const violation = self.recordViolation(
            "process_exec_path",
            "process.execPath",
            message
          );
          if (!auditMode) {
            throw new WorkerSecurityViolationError(message, violation);
          }
          Object.defineProperty(process, "execPath", {
            value,
            writable: true,
            configurable: true
          });
        },
        configurable: true
      });
    } catch {
    }
  }
  /**
   * Protect process.connected from being read or set in worker context.
   *
   * process.connected is a boolean primitive (not an object), so it cannot be
   * proxied via the normal blocked globals mechanism. We use Object.defineProperty
   * with getter/setter (same pattern as protectProcessExecPath).
   *
   * Only protects if process.connected exists (IPC contexts).
   */
  protectProcessConnected() {
    if (typeof process === "undefined") return;
    if (process.connected === void 0) return;
    const self = this;
    const auditMode = this.config.auditMode;
    try {
      const originalDescriptor = Object.getOwnPropertyDescriptor(
        process,
        "connected"
      );
      this.originalDescriptors.push({
        target: process,
        prop: "connected",
        descriptor: originalDescriptor
      });
      const currentValue = originalDescriptor?.value ?? process.connected;
      Object.defineProperty(process, "connected", {
        get() {
          const message = "process.connected access is blocked in worker context";
          const violation = self.recordViolation(
            "process_connected",
            "process.connected",
            message
          );
          if (!auditMode) {
            throw new WorkerSecurityViolationError(message, violation);
          }
          return currentValue;
        },
        set(value) {
          const message = "process.connected modification is blocked in worker context";
          const violation = self.recordViolation(
            "process_connected",
            "process.connected",
            message
          );
          if (!auditMode) {
            throw new WorkerSecurityViolationError(message, violation);
          }
          Object.defineProperty(process, "connected", {
            value,
            writable: true,
            configurable: true
          });
        },
        configurable: true
      });
    } catch {
    }
  }
  /**
   * Protect Module._load from being called.
   *
   * The attack vector is:
   * ```
   * module.constructor._load('child_process')
   * require.main.constructor._load('vm')
   * ```
   *
   * We access the Module class and replace _load with a blocking proxy.
   */
  protectModuleLoad() {
    const self = this;
    const auditMode = this.config.auditMode;
    try {
      let ModuleClass = null;
      if (typeof process !== "undefined") {
        const mainModule = process.mainModule;
        if (mainModule && typeof mainModule === "object") {
          ModuleClass = mainModule.constructor;
        }
      }
      if (!ModuleClass && typeof __require !== "undefined" && typeof __require.main !== "undefined") {
        ModuleClass = __require.main.constructor;
      }
      if (!ModuleClass || typeof ModuleClass._load !== "function") {
        return;
      }
      const original = ModuleClass._load;
      const descriptor = Object.getOwnPropertyDescriptor(ModuleClass, "_load");
      this.originalDescriptors.push({
        target: ModuleClass,
        prop: "_load",
        descriptor
      });
      const path = "Module._load";
      const proxy = new this.originalProxy(original, {
        apply(_target, _thisArg, _args) {
          const message = `${path} is blocked in worker context`;
          const violation = self.recordViolation("module_load", path, message);
          if (!auditMode) {
            throw new WorkerSecurityViolationError(message, violation);
          }
          return Reflect.apply(_target, _thisArg, _args);
        }
      });
      Object.defineProperty(ModuleClass, "_load", {
        value: proxy,
        writable: true,
        configurable: true
      });
    } catch {
    }
  }
  /**
   * Protect Module._resolveFilename from being called in worker context.
   *
   * Module._resolveFilename is called for both require() and import() resolution.
   * Blocking it catches file-based import() specifiers.
   *
   * data: and blob: URLs are handled by ESM loader hooks registered
   * in the main thread (DefenseInDepthBox.protectDynamicImport).
   */
  protectModuleResolveFilename() {
    const self = this;
    const auditMode = this.config.auditMode;
    try {
      let ModuleClass = null;
      if (typeof process !== "undefined") {
        const mainModule = process.mainModule;
        if (mainModule && typeof mainModule === "object") {
          ModuleClass = mainModule.constructor;
        }
      }
      if (!ModuleClass && typeof __require !== "undefined" && typeof __require.main !== "undefined") {
        ModuleClass = __require.main.constructor;
      }
      if (!ModuleClass || typeof ModuleClass._resolveFilename !== "function") {
        return;
      }
      const original = ModuleClass._resolveFilename;
      const descriptor = Object.getOwnPropertyDescriptor(
        ModuleClass,
        "_resolveFilename"
      );
      this.originalDescriptors.push({
        target: ModuleClass,
        prop: "_resolveFilename",
        descriptor
      });
      const path = "Module._resolveFilename";
      const proxy = new this.originalProxy(original, {
        apply(_target, _thisArg, _args) {
          const message = `${path} is blocked in worker context`;
          const violation = self.recordViolation(
            "module_resolve_filename",
            path,
            message
          );
          if (!auditMode) {
            throw new WorkerSecurityViolationError(message, violation);
          }
          return Reflect.apply(_target, _thisArg, _args);
        }
      });
      Object.defineProperty(ModuleClass, "_resolveFilename", {
        value: proxy,
        writable: true,
        configurable: true
      });
    } catch {
    }
  }
  /**
   * Apply a single patch to a blocked global.
   */
  applyPatch(blocked) {
    const { target, prop, violationType, strategy } = blocked;
    try {
      const original = target[prop];
      if (original === void 0) {
        return;
      }
      const descriptor = Object.getOwnPropertyDescriptor(target, prop);
      this.originalDescriptors.push({ target, prop, descriptor });
      if (strategy === "freeze") {
        if (typeof original === "object" && original !== null) {
          Object.freeze(original);
        }
      } else {
        const path = this.getPathForTarget(target, prop);
        const proxy = typeof original === "function" ? this.createBlockingProxy(
          original,
          path,
          violationType
        ) : this.createBlockingObjectProxy(
          original,
          path,
          violationType,
          blocked.allowedKeys
        );
        Object.defineProperty(target, prop, {
          value: proxy,
          writable: true,
          configurable: true
        });
      }
    } catch {
    }
  }
  /**
   * Restore all original values.
   */
  restorePatches() {
    for (let i = this.originalDescriptors.length - 1; i >= 0; i--) {
      const { target, prop, descriptor } = this.originalDescriptors[i];
      try {
        if (descriptor) {
          Object.defineProperty(target, prop, descriptor);
        } else {
          delete target[prop];
        }
      } catch {
      }
    }
    this.originalDescriptors = [];
  }
};

// src/security/trusted-globals.ts
var _SharedArrayBuffer = globalThis.SharedArrayBuffer;
var _Atomics = globalThis.Atomics;
var _performanceNow = performance.now.bind(performance);
var _Headers = globalThis.Headers;

// src/commands/worker-bridge/protocol.ts
var OpCode = {
  NOOP: 0,
  READ_FILE: 1,
  WRITE_FILE: 2,
  STAT: 3,
  READDIR: 4,
  MKDIR: 5,
  RM: 6,
  EXISTS: 7,
  APPEND_FILE: 8,
  SYMLINK: 9,
  READLINK: 10,
  LSTAT: 11,
  CHMOD: 12,
  REALPATH: 13,
  RENAME: 14,
  COPY_FILE: 15,
  // Special operations for I/O
  WRITE_STDOUT: 100,
  WRITE_STDERR: 101,
  EXIT: 102,
  // HTTP operations
  HTTP_REQUEST: 200,
  // Sub-shell execution
  EXEC_COMMAND: 300
};
var Status = {
  PENDING: 0,
  READY: 1,
  SUCCESS: 2,
  ERROR: 3
};
var ErrorCode = {
  NONE: 0,
  NOT_FOUND: 1,
  IS_DIRECTORY: 2,
  NOT_DIRECTORY: 3,
  EXISTS: 4,
  PERMISSION_DENIED: 5,
  INVALID_PATH: 6,
  IO_ERROR: 7,
  TIMEOUT: 8,
  NETWORK_ERROR: 9,
  NETWORK_NOT_CONFIGURED: 10
};
var Offset = {
  OP_CODE: 0,
  STATUS: 4,
  PATH_LENGTH: 8,
  DATA_LENGTH: 12,
  RESULT_LENGTH: 16,
  ERROR_CODE: 20,
  FLAGS: 24,
  MODE: 28,
  PATH_BUFFER: 32,
  DATA_BUFFER: 4128
  // 32 + 4096
};
var Size = {
  CONTROL_REGION: 32,
  PATH_BUFFER: 4096,
  // 1MB limit applies to all FS read/write operations through the bridge.
  // Files larger than this will be truncated. This is tight — consider
  // increasing if real workloads hit the cap. Reduced from 16MB for faster tests.
  DATA_BUFFER: 1048576,
  TOTAL: 1052704
  // 32 + 4096 + 1MB
};
var Flags = {
  NONE: 0,
  RECURSIVE: 1,
  FORCE: 2,
  MKDIR_RECURSIVE: 1
};
var StatLayout = {
  IS_FILE: 0,
  IS_DIRECTORY: 1,
  IS_SYMLINK: 2,
  MODE: 4,
  SIZE: 8,
  MTIME: 16,
  TOTAL: 24
};
var ProtocolBuffer = class {
  int32View;
  uint8View;
  dataView;
  constructor(buffer) {
    this.int32View = new Int32Array(buffer);
    this.uint8View = new Uint8Array(buffer);
    this.dataView = new DataView(buffer);
  }
  getOpCode() {
    return _Atomics.load(this.int32View, Offset.OP_CODE / 4);
  }
  setOpCode(code) {
    _Atomics.store(this.int32View, Offset.OP_CODE / 4, code);
  }
  getStatus() {
    return _Atomics.load(this.int32View, Offset.STATUS / 4);
  }
  setStatus(status) {
    _Atomics.store(this.int32View, Offset.STATUS / 4, status);
  }
  getPathLength() {
    return _Atomics.load(this.int32View, Offset.PATH_LENGTH / 4);
  }
  setPathLength(length) {
    _Atomics.store(this.int32View, Offset.PATH_LENGTH / 4, length);
  }
  getDataLength() {
    return _Atomics.load(this.int32View, Offset.DATA_LENGTH / 4);
  }
  setDataLength(length) {
    _Atomics.store(this.int32View, Offset.DATA_LENGTH / 4, length);
  }
  getResultLength() {
    return _Atomics.load(this.int32View, Offset.RESULT_LENGTH / 4);
  }
  setResultLength(length) {
    _Atomics.store(this.int32View, Offset.RESULT_LENGTH / 4, length);
  }
  getErrorCode() {
    return _Atomics.load(
      this.int32View,
      Offset.ERROR_CODE / 4
    );
  }
  setErrorCode(code) {
    _Atomics.store(this.int32View, Offset.ERROR_CODE / 4, code);
  }
  getFlags() {
    return _Atomics.load(this.int32View, Offset.FLAGS / 4);
  }
  setFlags(flags) {
    _Atomics.store(this.int32View, Offset.FLAGS / 4, flags);
  }
  getMode() {
    return _Atomics.load(this.int32View, Offset.MODE / 4);
  }
  setMode(mode) {
    _Atomics.store(this.int32View, Offset.MODE / 4, mode);
  }
  getPath() {
    const length = this.getPathLength();
    const bytes = this.uint8View.slice(
      Offset.PATH_BUFFER,
      Offset.PATH_BUFFER + length
    );
    return new TextDecoder().decode(bytes);
  }
  setPath(path) {
    const encoded = new TextEncoder().encode(path);
    if (encoded.length > Size.PATH_BUFFER) {
      throw new Error(`Path too long: ${encoded.length} > ${Size.PATH_BUFFER}`);
    }
    this.uint8View.set(encoded, Offset.PATH_BUFFER);
    this.setPathLength(encoded.length);
  }
  getData() {
    const length = this.getDataLength();
    return this.uint8View.slice(
      Offset.DATA_BUFFER,
      Offset.DATA_BUFFER + length
    );
  }
  setData(data) {
    if (data.length > Size.DATA_BUFFER) {
      throw new Error(`Data too large: ${data.length} > ${Size.DATA_BUFFER}`);
    }
    this.uint8View.set(data, Offset.DATA_BUFFER);
    this.setDataLength(data.length);
  }
  getDataAsString() {
    const data = this.getData();
    return new TextDecoder().decode(data);
  }
  setDataFromString(str) {
    const encoded = new TextEncoder().encode(str);
    this.setData(encoded);
  }
  getResult() {
    const length = this.getResultLength();
    return this.uint8View.slice(
      Offset.DATA_BUFFER,
      Offset.DATA_BUFFER + length
    );
  }
  setResult(data) {
    if (data.length > Size.DATA_BUFFER) {
      throw new Error(`Result too large: ${data.length} > ${Size.DATA_BUFFER}`);
    }
    this.uint8View.set(data, Offset.DATA_BUFFER);
    this.setResultLength(data.length);
  }
  getResultAsString() {
    const result = this.getResult();
    return new TextDecoder().decode(result);
  }
  setResultFromString(str) {
    const encoded = new TextEncoder().encode(str);
    this.setResult(encoded);
  }
  encodeStat(stat) {
    this.uint8View[Offset.DATA_BUFFER + StatLayout.IS_FILE] = stat.isFile ? 1 : 0;
    this.uint8View[Offset.DATA_BUFFER + StatLayout.IS_DIRECTORY] = stat.isDirectory ? 1 : 0;
    this.uint8View[Offset.DATA_BUFFER + StatLayout.IS_SYMLINK] = stat.isSymbolicLink ? 1 : 0;
    this.dataView.setInt32(
      Offset.DATA_BUFFER + StatLayout.MODE,
      stat.mode,
      true
    );
    const size = Math.min(stat.size, Number.MAX_SAFE_INTEGER);
    this.dataView.setFloat64(Offset.DATA_BUFFER + StatLayout.SIZE, size, true);
    this.dataView.setFloat64(
      Offset.DATA_BUFFER + StatLayout.MTIME,
      stat.mtime.getTime(),
      true
    );
    this.setResultLength(StatLayout.TOTAL);
  }
  decodeStat() {
    return {
      isFile: this.uint8View[Offset.DATA_BUFFER + StatLayout.IS_FILE] === 1,
      isDirectory: this.uint8View[Offset.DATA_BUFFER + StatLayout.IS_DIRECTORY] === 1,
      isSymbolicLink: this.uint8View[Offset.DATA_BUFFER + StatLayout.IS_SYMLINK] === 1,
      mode: this.dataView.getInt32(Offset.DATA_BUFFER + StatLayout.MODE, true),
      size: this.dataView.getFloat64(
        Offset.DATA_BUFFER + StatLayout.SIZE,
        true
      ),
      mtime: new Date(
        this.dataView.getFloat64(Offset.DATA_BUFFER + StatLayout.MTIME, true)
      )
    };
  }
  waitForReady(timeout) {
    return _Atomics.wait(
      this.int32View,
      Offset.STATUS / 4,
      Status.PENDING,
      timeout
    );
  }
  waitForReadyAsync(timeout) {
    return _Atomics.waitAsync(
      this.int32View,
      Offset.STATUS / 4,
      Status.PENDING,
      timeout
    );
  }
  /**
   * Wait for status to become READY.
   * Returns immediately if status is already READY, or waits until it changes.
   */
  async waitUntilReady(timeout) {
    const startTime = Date.now();
    while (true) {
      const status = this.getStatus();
      if (status === Status.READY) {
        return true;
      }
      const elapsed = Date.now() - startTime;
      if (elapsed >= timeout) {
        return false;
      }
      const remainingMs = timeout - elapsed;
      const result = _Atomics.waitAsync(
        this.int32View,
        Offset.STATUS / 4,
        status,
        remainingMs
      );
      if (result.async) {
        const waitResult = await result.value;
        if (waitResult === "timed-out") {
          return false;
        }
      }
    }
  }
  waitForResult(timeout) {
    return _Atomics.wait(
      this.int32View,
      Offset.STATUS / 4,
      Status.READY,
      timeout
    );
  }
  notify() {
    return _Atomics.notify(this.int32View, Offset.STATUS / 4);
  }
  reset() {
    this.setOpCode(OpCode.NOOP);
    this.setStatus(Status.PENDING);
    this.setPathLength(0);
    this.setDataLength(0);
    this.setResultLength(0);
    this.setErrorCode(ErrorCode.NONE);
    this.setFlags(Flags.NONE);
    this.setMode(0);
  }
};

// src/commands/worker-bridge/sync-backend.ts
var SyncBackend = class {
  protocol;
  operationTimeoutMs;
  constructor(sharedBuffer, operationTimeoutMs = 3e4) {
    this.protocol = new ProtocolBuffer(sharedBuffer);
    this.operationTimeoutMs = operationTimeoutMs;
  }
  execSync(opCode, path, data, flags = 0, mode = 0) {
    this.protocol.reset();
    this.protocol.setOpCode(opCode);
    this.protocol.setPath(path);
    this.protocol.setFlags(flags);
    this.protocol.setMode(mode);
    if (data) {
      this.protocol.setData(data);
    }
    this.protocol.setStatus(Status.READY);
    this.protocol.notify();
    const waitResult = this.protocol.waitForResult(this.operationTimeoutMs);
    if (waitResult === "timed-out") {
      return { success: false, error: "Operation timed out" };
    }
    const status = this.protocol.getStatus();
    if (status === Status.SUCCESS) {
      return { success: true, result: this.protocol.getResult() };
    }
    return {
      success: false,
      error: this.protocol.getResultAsString() || `Error code: ${this.protocol.getErrorCode()}`
    };
  }
  readFile(path) {
    const result = this.execSync(OpCode.READ_FILE, path);
    if (!result.success) {
      throw new Error(result.error || "Failed to read file");
    }
    return result.result ?? new Uint8Array(0);
  }
  writeFile(path, data) {
    const result = this.execSync(OpCode.WRITE_FILE, path, data);
    if (!result.success) {
      throw new Error(result.error || "Failed to write file");
    }
  }
  stat(path) {
    const result = this.execSync(OpCode.STAT, path);
    if (!result.success) {
      throw new Error(result.error || "Failed to stat");
    }
    return this.protocol.decodeStat();
  }
  lstat(path) {
    const result = this.execSync(OpCode.LSTAT, path);
    if (!result.success) {
      throw new Error(result.error || "Failed to lstat");
    }
    return this.protocol.decodeStat();
  }
  readdir(path) {
    const result = this.execSync(OpCode.READDIR, path);
    if (!result.success) {
      throw new Error(result.error || "Failed to readdir");
    }
    return JSON.parse(this.protocol.getResultAsString());
  }
  mkdir(path, recursive = false) {
    const flags = recursive ? Flags.MKDIR_RECURSIVE : 0;
    const result = this.execSync(OpCode.MKDIR, path, void 0, flags);
    if (!result.success) {
      throw new Error(result.error || "Failed to mkdir");
    }
  }
  rm(path, recursive = false, force = false) {
    let flags = 0;
    if (recursive) flags |= Flags.RECURSIVE;
    if (force) flags |= Flags.FORCE;
    const result = this.execSync(OpCode.RM, path, void 0, flags);
    if (!result.success) {
      throw new Error(result.error || "Failed to rm");
    }
  }
  exists(path) {
    const result = this.execSync(OpCode.EXISTS, path);
    if (!result.success) {
      return false;
    }
    return result.result?.[0] === 1;
  }
  appendFile(path, data) {
    const result = this.execSync(OpCode.APPEND_FILE, path, data);
    if (!result.success) {
      throw new Error(result.error || "Failed to append file");
    }
  }
  symlink(target, linkPath) {
    const targetData = new TextEncoder().encode(target);
    const result = this.execSync(OpCode.SYMLINK, linkPath, targetData);
    if (!result.success) {
      throw new Error(result.error || "Failed to symlink");
    }
  }
  readlink(path) {
    const result = this.execSync(OpCode.READLINK, path);
    if (!result.success) {
      throw new Error(result.error || "Failed to readlink");
    }
    return this.protocol.getResultAsString();
  }
  chmod(path, mode) {
    const result = this.execSync(OpCode.CHMOD, path, void 0, 0, mode);
    if (!result.success) {
      throw new Error(result.error || "Failed to chmod");
    }
  }
  realpath(path) {
    const result = this.execSync(OpCode.REALPATH, path);
    if (!result.success) {
      throw new Error(result.error || "Failed to realpath");
    }
    return this.protocol.getResultAsString();
  }
  rename(oldPath, newPath) {
    const newPathData = new TextEncoder().encode(newPath);
    const result = this.execSync(OpCode.RENAME, oldPath, newPathData);
    if (!result.success) {
      throw new Error(result.error || "Failed to rename");
    }
  }
  copyFile(src, dest) {
    const destData = new TextEncoder().encode(dest);
    const result = this.execSync(OpCode.COPY_FILE, src, destData);
    if (!result.success) {
      throw new Error(result.error || "Failed to copyFile");
    }
  }
  writeStdout(data) {
    const encoded = new TextEncoder().encode(data);
    const result = this.execSync(OpCode.WRITE_STDOUT, "", encoded);
    if (!result.success) {
      throw new Error(result.error || "Failed to write stdout");
    }
  }
  writeStderr(data) {
    const encoded = new TextEncoder().encode(data);
    const result = this.execSync(OpCode.WRITE_STDERR, "", encoded);
    if (!result.success) {
      throw new Error(result.error || "Failed to write stderr");
    }
  }
  exit(code) {
    this.execSync(OpCode.EXIT, "", void 0, code);
  }
  /**
   * Make an HTTP request through the main thread's secureFetch.
   * Returns the response as a parsed object.
   */
  httpRequest(url, options) {
    const requestData = options ? new TextEncoder().encode(JSON.stringify(options)) : void 0;
    const result = this.execSync(OpCode.HTTP_REQUEST, url, requestData);
    if (!result.success) {
      throw new Error(result.error || "HTTP request failed");
    }
    const responseJson = new TextDecoder().decode(result.result);
    return JSON.parse(responseJson);
  }
  /**
   * Execute a shell command through the main thread's exec function.
   * Returns the result as { stdout, stderr, exitCode }.
   */
  execCommand(command, stdin) {
    const requestData = stdin ? new TextEncoder().encode(JSON.stringify({ stdin })) : void 0;
    const result = this.execSync(OpCode.EXEC_COMMAND, command, requestData);
    if (!result.success) {
      throw new Error(result.error || "Command execution failed");
    }
    const responseJson = new TextDecoder().decode(result.result);
    return JSON.parse(responseJson);
  }
  /**
   * Execute a shell command with structured args (shell-escaped on the main thread).
   * Prevents command injection from unsanitized args.
   */
  execCommandArgs(command, args) {
    const requestData = new TextEncoder().encode(JSON.stringify({ args }));
    const result = this.execSync(OpCode.EXEC_COMMAND, command, requestData);
    if (!result.success) {
      throw new Error(result.error || "Command execution failed");
    }
    const responseJson = new TextDecoder().decode(result.result);
    return JSON.parse(responseJson);
  }
};

// src/commands/js-exec/fetch-polyfill.ts
var FETCH_POLYFILL_SOURCE = `
(function() {
  // --- URLSearchParams ---
  function URLSearchParams(init) {
    this._entries = [];
    if (!init) return;
    if (typeof init === 'string') {
      var s = init;
      if (s.charAt(0) === '?') s = s.slice(1);
      var pairs = s.split('&');
      for (var i = 0; i < pairs.length; i++) {
        var pair = pairs[i];
        if (pair === '') continue;
        var eq = pair.indexOf('=');
        if (eq === -1) {
          this._entries.push([decodeURIComponent(pair), '']);
        } else {
          this._entries.push([
            decodeURIComponent(pair.slice(0, eq)),
            decodeURIComponent(pair.slice(eq + 1))
          ]);
        }
      }
    } else if (typeof init === 'object' && init !== null) {
      if (init instanceof URLSearchParams) {
        this._entries = init._entries.slice();
      } else {
        var keys = Object.keys(init);
        for (var i = 0; i < keys.length; i++) {
          this._entries.push([keys[i], String(init[keys[i]])]);
        }
      }
    }
  }

  URLSearchParams.prototype.append = function(name, value) {
    this._entries.push([String(name), String(value)]);
  };

  URLSearchParams.prototype.delete = function(name) {
    var n = String(name);
    this._entries = this._entries.filter(function(e) { return e[0] !== n; });
  };

  URLSearchParams.prototype.get = function(name) {
    var n = String(name);
    for (var i = 0; i < this._entries.length; i++) {
      if (this._entries[i][0] === n) return this._entries[i][1];
    }
    return null;
  };

  URLSearchParams.prototype.getAll = function(name) {
    var n = String(name);
    var result = [];
    for (var i = 0; i < this._entries.length; i++) {
      if (this._entries[i][0] === n) result.push(this._entries[i][1]);
    }
    return result;
  };

  URLSearchParams.prototype.has = function(name) {
    var n = String(name);
    for (var i = 0; i < this._entries.length; i++) {
      if (this._entries[i][0] === n) return true;
    }
    return false;
  };

  URLSearchParams.prototype.set = function(name, value) {
    var n = String(name);
    var v = String(value);
    var found = false;
    var newEntries = [];
    for (var i = 0; i < this._entries.length; i++) {
      if (this._entries[i][0] === n) {
        if (!found) {
          newEntries.push([n, v]);
          found = true;
        }
      } else {
        newEntries.push(this._entries[i]);
      }
    }
    if (!found) newEntries.push([n, v]);
    this._entries = newEntries;
  };

  URLSearchParams.prototype.sort = function() {
    this._entries.sort(function(a, b) {
      if (a[0] < b[0]) return -1;
      if (a[0] > b[0]) return 1;
      return 0;
    });
  };

  URLSearchParams.prototype.toString = function() {
    return this._entries.map(function(e) {
      return encodeURIComponent(e[0]) + '=' + encodeURIComponent(e[1]);
    }).join('&');
  };

  URLSearchParams.prototype.forEach = function(callback, thisArg) {
    for (var i = 0; i < this._entries.length; i++) {
      callback.call(thisArg, this._entries[i][1], this._entries[i][0], this);
    }
  };

  URLSearchParams.prototype.entries = function() {
    var idx = 0;
    var entries = this._entries;
    return {
      next: function() {
        if (idx >= entries.length) return { done: true, value: undefined };
        return { done: false, value: entries[idx++].slice() };
      },
      [Symbol.iterator]: function() { return this; }
    };
  };

  URLSearchParams.prototype.keys = function() {
    var idx = 0;
    var entries = this._entries;
    return {
      next: function() {
        if (idx >= entries.length) return { done: true, value: undefined };
        return { done: false, value: entries[idx++][0] };
      },
      [Symbol.iterator]: function() { return this; }
    };
  };

  URLSearchParams.prototype.values = function() {
    var idx = 0;
    var entries = this._entries;
    return {
      next: function() {
        if (idx >= entries.length) return { done: true, value: undefined };
        return { done: false, value: entries[idx++][1] };
      },
      [Symbol.iterator]: function() { return this; }
    };
  };

  URLSearchParams.prototype[Symbol.iterator] = URLSearchParams.prototype.entries;

  Object.defineProperty(URLSearchParams.prototype, 'size', {
    get: function() { return this._entries.length; }
  });

  // --- URL ---
  var urlRegex = /^([a-zA-Z][a-zA-Z0-9+.-]*):(?:\\/\\/(?:([^:@/?#]*)(?::([^@/?#]*))?@)?([^:/?#]*)(?::([0-9]+))?)?(\\/[^?#]*)?(?:\\?([^#]*))?(?:#(.*))?$/;

  function URL(url, base) {
    var input = String(url);

    if (base !== undefined) {
      var baseUrl = (base instanceof URL) ? base : new URL(String(base));
      // Resolve relative URL against base
      if (/^[a-zA-Z][a-zA-Z0-9+.-]*:/.test(input)) {
        // Absolute URL - parse as-is
      } else if (input.charAt(0) === '/' && input.charAt(1) === '/') {
        // Protocol-relative
        input = baseUrl.protocol + input;
      } else if (input.charAt(0) === '/') {
        // Absolute path
        input = baseUrl.origin + input;
      } else if (input.charAt(0) === '?' || input.charAt(0) === '#') {
        // Query or hash only
        var basePath = baseUrl.protocol + '//' + baseUrl.host + baseUrl.pathname;
        if (input.charAt(0) === '#') {
          input = basePath + baseUrl.search + input;
        } else {
          input = basePath + input;
        }
      } else {
        // Relative path
        var basePath = baseUrl.protocol + '//' + baseUrl.host;
        var dirPath = baseUrl.pathname;
        var lastSlash = dirPath.lastIndexOf('/');
        if (lastSlash >= 0) dirPath = dirPath.slice(0, lastSlash + 1);
        else dirPath = '/';
        input = basePath + dirPath + input;
      }
    }

    var m = urlRegex.exec(input);
    if (!m) throw new TypeError("Invalid URL: " + String(url));

    this.protocol = m[1].toLowerCase() + ':';
    this.username = m[2] ? decodeURIComponent(m[2]) : '';
    this.password = m[3] ? decodeURIComponent(m[3]) : '';
    this.hostname = m[4] || '';
    this.port = m[5] || '';
    this.pathname = m[6] || '/';
    this.hash = m[8] ? '#' + m[8] : '';

    // Normalize pathname (resolve . and ..)
    var parts = this.pathname.split('/');
    var resolved = [];
    for (var i = 0; i < parts.length; i++) {
      if (parts[i] === '..') { if (resolved.length > 1) resolved.pop(); }
      else if (parts[i] !== '.') resolved.push(parts[i]);
    }
    this.pathname = resolved.join('/') || '/';

    // searchParams is live
    this._searchParamsStr = m[7] || '';
    this.searchParams = new URLSearchParams(this._searchParamsStr);
  }

  Object.defineProperty(URL.prototype, 'search', {
    get: function() {
      var s = this.searchParams.toString();
      return s ? '?' + s : '';
    },
    set: function(v) {
      this.searchParams = new URLSearchParams(String(v));
    }
  });

  Object.defineProperty(URL.prototype, 'host', {
    get: function() {
      return this.port ? this.hostname + ':' + this.port : this.hostname;
    }
  });

  Object.defineProperty(URL.prototype, 'origin', {
    get: function() {
      return this.protocol + '//' + this.host;
    }
  });

  Object.defineProperty(URL.prototype, 'href', {
    get: function() {
      var auth = '';
      if (this.username) {
        auth = this.username;
        if (this.password) auth += ':' + this.password;
        auth += '@';
      }
      return this.protocol + '//' + auth + this.host + this.pathname + this.search + this.hash;
    },
    set: function(v) {
      var parsed = new URL(String(v));
      this.protocol = parsed.protocol;
      this.username = parsed.username;
      this.password = parsed.password;
      this.hostname = parsed.hostname;
      this.port = parsed.port;
      this.pathname = parsed.pathname;
      this.searchParams = parsed.searchParams;
      this.hash = parsed.hash;
    }
  });

  URL.prototype.toString = function() { return this.href; };
  URL.prototype.toJSON = function() { return this.href; };

  // --- Headers ---
  function Headers(init) {
    this._map = {};
    if (!init) return;
    if (init instanceof Headers) {
      var keys = Object.keys(init._map);
      for (var i = 0; i < keys.length; i++) {
        this._map[keys[i]] = init._map[keys[i]].slice();
      }
    } else if (typeof init === 'object') {
      var keys = Object.keys(init);
      for (var i = 0; i < keys.length; i++) {
        this._map[keys[i].toLowerCase()] = [String(init[keys[i]])];
      }
    }
  }

  Headers.prototype.append = function(name, value) {
    var key = String(name).toLowerCase();
    if (!this._map[key]) this._map[key] = [];
    this._map[key].push(String(value));
  };

  Headers.prototype.delete = function(name) {
    delete this._map[String(name).toLowerCase()];
  };

  Headers.prototype.get = function(name) {
    var vals = this._map[String(name).toLowerCase()];
    return vals ? vals.join(', ') : null;
  };

  Headers.prototype.has = function(name) {
    return String(name).toLowerCase() in this._map;
  };

  Headers.prototype.set = function(name, value) {
    this._map[String(name).toLowerCase()] = [String(value)];
  };

  Headers.prototype.forEach = function(callback, thisArg) {
    var keys = Object.keys(this._map).sort();
    for (var i = 0; i < keys.length; i++) {
      callback.call(thisArg, this._map[keys[i]].join(', '), keys[i], this);
    }
  };

  Headers.prototype.entries = function() {
    var keys = Object.keys(this._map).sort();
    var map = this._map;
    var idx = 0;
    return {
      next: function() {
        if (idx >= keys.length) return { done: true, value: undefined };
        var k = keys[idx++];
        return { done: false, value: [k, map[k].join(', ')] };
      },
      [Symbol.iterator]: function() { return this; }
    };
  };

  Headers.prototype.keys = function() {
    var keys = Object.keys(this._map).sort();
    var idx = 0;
    return {
      next: function() {
        if (idx >= keys.length) return { done: true, value: undefined };
        return { done: false, value: keys[idx++] };
      },
      [Symbol.iterator]: function() { return this; }
    };
  };

  Headers.prototype.values = function() {
    var keys = Object.keys(this._map).sort();
    var map = this._map;
    var idx = 0;
    return {
      next: function() {
        if (idx >= keys.length) return { done: true, value: undefined };
        return { done: false, value: map[keys[idx++]].join(', ') };
      },
      [Symbol.iterator]: function() { return this; }
    };
  };

  Headers.prototype[Symbol.iterator] = Headers.prototype.entries;

  // --- Response ---
  function Response(body, init) {
    if (init === undefined) init = {};
    this.status = init.status !== undefined ? init.status : 200;
    this.statusText = init.statusText !== undefined ? init.statusText : '';
    this.headers = init.headers instanceof Headers ? init.headers : new Headers(init.headers);
    this.body = body !== undefined && body !== null ? String(body) : '';
    this.ok = this.status >= 200 && this.status <= 299;
    this.url = '';
    this.redirected = false;
    this.type = 'basic';
    this.bodyUsed = false;
  }

  Response.prototype.text = function() {
    this.bodyUsed = true;
    return Promise.resolve(this.body);
  };

  Response.prototype.json = function() {
    this.bodyUsed = true;
    try {
      return Promise.resolve(JSON.parse(this.body));
    } catch (e) {
      return Promise.reject(e);
    }
  };

  Response.prototype.clone = function() {
    var r = new Response(this.body, {
      status: this.status,
      statusText: this.statusText,
      headers: new Headers(this.headers)
    });
    r.url = this.url;
    r.redirected = this.redirected;
    r.type = this.type;
    return r;
  };

  Response.json = function(data, init) {
    if (init === undefined) init = {};
    var headers = init.headers instanceof Headers ? init.headers : new Headers(init.headers);
    if (!headers.has('content-type')) {
      headers.set('content-type', 'application/json');
    }
    return new Response(JSON.stringify(data), {
      status: init.status !== undefined ? init.status : 200,
      statusText: init.statusText || '',
      headers: headers
    });
  };

  Response.error = function() {
    var r = new Response(null, { status: 0, statusText: '' });
    r.type = 'error';
    r.ok = false;
    return r;
  };

  Response.redirect = function(url, status) {
    if (status === undefined) status = 302;
    var r = new Response(null, {
      status: status,
      statusText: '',
      headers: new Headers({ location: String(url) })
    });
    r.redirected = true;
    return r;
  };

  // --- Request ---
  function Request(input, init) {
    if (init === undefined) init = {};
    if (input instanceof Request) {
      this.url = input.url;
      this.method = input.method;
      this.headers = new Headers(input.headers);
      this.body = input.body;
    } else {
      this.url = String(input);
      this.method = 'GET';
      this.headers = new Headers();
      this.body = null;
    }
    if (init.method !== undefined) this.method = String(init.method).toUpperCase();
    if (init.headers !== undefined) this.headers = init.headers instanceof Headers ? init.headers : new Headers(init.headers);
    if (init.body !== undefined) this.body = init.body !== null ? String(init.body) : null;
  }

  Request.prototype.clone = function() {
    return new Request(this);
  };

  // --- Assign to globalThis ---
  globalThis.URLSearchParams = URLSearchParams;
  globalThis.URL = URL;
  globalThis.Headers = Headers;
  globalThis.Response = Response;
  globalThis.Request = Request;

  // --- Wrap native fetch ---
  var _nativeFetch = globalThis[Symbol.for('jb:fetch')];
  globalThis.fetch = function fetch(input, init) {
    try {
      var url, method, headers, body;

      if (input instanceof Request) {
        url = input.url;
        method = input.method;
        headers = {};
        input.headers.forEach(function(v, k) { headers[k] = v; });
        body = input.body;
      } else {
        url = String(input);
        method = undefined;
        headers = undefined;
        body = undefined;
      }

      if (init) {
        if (init.method !== undefined) method = String(init.method).toUpperCase();
        if (init.headers !== undefined) {
          var h = init.headers instanceof Headers ? init.headers : new Headers(init.headers);
          headers = {};
          h.forEach(function(v, k) { headers[k] = v; });
        }
        if (init.body !== undefined) body = init.body !== null ? String(init.body) : undefined;
      }

      var opts = Object.create(null);
      if (method) opts.method = method;
      if (headers) opts.headers = headers;
      if (body) opts.body = body;

      var raw = _nativeFetch(url, opts);

      var respHeaders = new Headers(raw.headers || {});
      var response = new Response(raw.body, {
        status: raw.status,
        statusText: raw.statusText || '',
        headers: respHeaders
      });
      response.url = raw.url || url;

      return Promise.resolve(response);
    } catch (e) {
      return Promise.reject(new TypeError(e.message || 'fetch failed'));
    }
  };
})();
`;

// src/commands/js-exec/module-shims.ts
var EVENTS_MODULE_SOURCE = `
var EventEmitter = (function() {
  function EE() {
    this._events = {};
    this._maxListeners = 10;
  }
  EE.prototype.on = function(event, listener) {
    if (!this._events[event]) this._events[event] = [];
    this._events[event].push(listener);
    return this;
  };
  EE.prototype.addListener = EE.prototype.on;
  EE.prototype.once = function(event, listener) {
    var self = this;
    function wrapper() {
      self.removeListener(event, wrapper);
      listener.apply(this, arguments);
    }
    wrapper._original = listener;
    return this.on(event, wrapper);
  };
  EE.prototype.off = function(event, listener) {
    return this.removeListener(event, listener);
  };
  EE.prototype.removeListener = function(event, listener) {
    var list = this._events[event];
    if (list) {
      this._events[event] = list.filter(function(fn) {
        return fn !== listener && fn._original !== listener;
      });
    }
    return this;
  };
  EE.prototype.removeAllListeners = function(event) {
    if (event) delete this._events[event];
    else this._events = {};
    return this;
  };
  EE.prototype.emit = function(event) {
    var list = this._events[event];
    if (!list || list.length === 0) return false;
    var args = Array.prototype.slice.call(arguments, 1);
    var fns = list.slice();
    for (var i = 0; i < fns.length; i++) fns[i].apply(this, args);
    return true;
  };
  EE.prototype.listeners = function(event) {
    return (this._events[event] || []).slice();
  };
  EE.prototype.listenerCount = function(event) {
    return (this._events[event] || []).length;
  };
  EE.prototype.setMaxListeners = function(n) {
    this._maxListeners = n;
    return this;
  };
  EE.prototype.eventNames = function() {
    return Object.keys(this._events);
  };
  EE.prototype.prependListener = function(event, listener) {
    if (!this._events[event]) this._events[event] = [];
    this._events[event].unshift(listener);
    return this;
  };
  return EE;
})();
globalThis[Symbol.for('jb:events')] = { EventEmitter: EventEmitter };
`;
var OS_MODULE_SOURCE = `
var _os = {
  platform: function() { return globalThis.process.platform; },
  arch: function() { return globalThis.process.arch; },
  homedir: function() { return '/home/user'; },
  tmpdir: function() { return '/tmp'; },
  type: function() { return 'Linux'; },
  hostname: function() { return 'sandbox'; },
  EOL: '\\n',
  cpus: function() { return []; },
  totalmem: function() { return 0; },
  freemem: function() { return 0; },
  endianness: function() { return 'LE'; }
};
globalThis[Symbol.for('jb:os')] = _os;
`;
var URL_MODULE_SOURCE = `
var _urlMod = {
  URL: globalThis.URL,
  URLSearchParams: globalThis.URLSearchParams,
  parse: function(urlStr) {
    try {
      var u = new URL(urlStr);
      return {
        protocol: u.protocol, host: u.host, hostname: u.hostname,
        port: u.port, pathname: u.pathname, search: u.search,
        hash: u.hash, href: u.href, path: u.pathname + u.search
      };
    } catch(e) {
      return {
        protocol: null, host: null, hostname: null, port: null,
        pathname: urlStr, search: '', hash: '', href: urlStr, path: urlStr
      };
    }
  },
  format: function(obj) {
    if (typeof obj === 'string') return obj;
    if (obj instanceof URL) return obj.href;
    var auth = obj.auth ? obj.auth + '@' : '';
    var host = obj.host || ((obj.hostname || '') + (obj.port ? ':' + obj.port : ''));
    return (obj.protocol ? obj.protocol + '//' : '') + auth + host +
      (obj.pathname || '/') + (obj.search || '') + (obj.hash || '');
  }
};
globalThis[Symbol.for('jb:url')] = _urlMod;
`;
var ASSERT_MODULE_SOURCE = `
var _deepEqual = function(a, b) {
  if (a === b) return true;
  if (a === null || b === null || typeof a !== 'object' || typeof b !== 'object') return false;
  if (Array.isArray(a) !== Array.isArray(b)) return false;
  var ka = Object.keys(a), kb = Object.keys(b);
  if (ka.length !== kb.length) return false;
  for (var i = 0; i < ka.length; i++) {
    if (!_deepEqual(a[ka[i]], b[ka[i]])) return false;
  }
  return true;
};
var _assert = function(val, msg) {
  if (!val) throw new Error(msg || 'AssertionError: expected truthy value');
};
_assert.ok = _assert;
_assert.equal = function(a, b, msg) {
  if (a != b) throw new Error(msg || 'AssertionError: ' + a + ' != ' + b);
};
_assert.notEqual = function(a, b, msg) {
  if (a == b) throw new Error(msg || 'AssertionError: ' + a + ' == ' + b);
};
_assert.strictEqual = function(a, b, msg) {
  if (a !== b) throw new Error(msg || 'AssertionError: ' + a + ' !== ' + b);
};
_assert.notStrictEqual = function(a, b, msg) {
  if (a === b) throw new Error(msg || 'AssertionError: ' + a + ' === ' + b);
};
_assert.deepEqual = function(a, b, msg) {
  if (!_deepEqual(a, b)) throw new Error(msg || 'AssertionError: objects not deep equal');
};
_assert.deepStrictEqual = _assert.deepEqual;
_assert.notDeepEqual = function(a, b, msg) {
  if (_deepEqual(a, b)) throw new Error(msg || 'AssertionError: objects are deep equal');
};
_assert.throws = function(fn, expected, msg) {
  var threw = false;
  try { fn(); } catch(e) {
    threw = true;
    if (expected instanceof RegExp && !expected.test(e.message))
      throw new Error(msg || 'AssertionError: error message did not match');
  }
  if (!threw) throw new Error(msg || 'AssertionError: function did not throw');
};
_assert.doesNotThrow = function(fn, msg) {
  // @banned-pattern-ignore: sandbox-internal assertion helper; e.message is from user code inside QuickJS, not host details
  try { fn(); } catch(e) {
    throw new Error(msg || 'AssertionError: function threw: ' + e.message);
  }
};
_assert.fail = function(msg) {
  throw new Error(msg || 'AssertionError: assert.fail()');
};
globalThis[Symbol.for('jb:assert')] = _assert;
`;
var UTIL_MODULE_SOURCE = `
var _util = {
  format: function() {
    var args = Array.prototype.slice.call(arguments);
    if (args.length === 0) return '';
    var fmt = args[0];
    if (typeof fmt !== 'string') {
      return args.map(function(a) {
        return typeof a === 'string' ? a : JSON.stringify(a);
      }).join(' ');
    }
    var i = 1;
    var str = fmt.replace(/%[sdjifoO%]/g, function(m) {
      if (m === '%%') return '%';
      if (i >= args.length) return m;
      var v = args[i++];
      if (m === '%s') return String(v);
      if (m === '%d') return Number(v).toString();
      if (m === '%i') { var n = Number(v); return (isNaN(n) ? 'NaN' : Math.trunc(n)).toString(); }
      if (m === '%j') return JSON.stringify(v);
      if (m === '%f') return parseFloat(v).toString();
      if (m === '%o' || m === '%O') return JSON.stringify(v);
      return m;
    });
    while (i < args.length) {
      str += ' ' + (typeof args[i] === 'string' ? args[i] : JSON.stringify(args[i]));
      i++;
    }
    return str;
  },
  inspect: function(obj, opts) {
    if (obj === null) return 'null';
    if (obj === undefined) return 'undefined';
    if (typeof obj === 'string') return "'" + obj + "'";
    if (typeof obj === 'function') return '[Function: ' + (obj.name || 'anonymous') + ']';
    var seen = [];
    try {
      return JSON.stringify(obj, function(key, val) {
        if (typeof val === 'object' && val !== null) {
          if (seen.indexOf(val) !== -1) return '[Circular]';
          seen.push(val);
        }
        return val;
      });
    } catch(e) { return String(obj); }
  },
  promisify: function(fn) {
    return function() {
      var args = Array.prototype.slice.call(arguments);
      return new Promise(function(resolve, reject) {
        args.push(function(err, val) { if (err) reject(err); else resolve(val); });
        fn.apply(null, args);
      });
    };
  },
  types: {
    isDate: function(v) { return v instanceof Date; },
    isRegExp: function(v) { return v instanceof RegExp; },
    isArray: function(v) { return Array.isArray(v); },
    isMap: function(v) { return typeof Map !== 'undefined' && v instanceof Map; },
    isSet: function(v) { return typeof Set !== 'undefined' && v instanceof Set; }
  },
  inherits: function(ctor, superCtor) {
    ctor.prototype = Object.create(superCtor.prototype);
    ctor.prototype.constructor = ctor;
  }
};
globalThis[Symbol.for('jb:util')] = _util;
`;
var BUFFER_MODULE_SOURCE = `
function _utf8Encode(str) {
  var bytes = [];
  for (var i = 0; i < str.length; i++) {
    var c = str.charCodeAt(i);
    if (c < 0x80) {
      bytes.push(c);
    } else if (c < 0x800) {
      bytes.push(0xC0 | (c >> 6), 0x80 | (c & 0x3F));
    } else if (c >= 0xD800 && c <= 0xDBFF && i + 1 < str.length) {
      var lo = str.charCodeAt(++i);
      var cp = ((c - 0xD800) * 0x400) + (lo - 0xDC00) + 0x10000;
      bytes.push(0xF0 | (cp >> 18), 0x80 | ((cp >> 12) & 0x3F), 0x80 | ((cp >> 6) & 0x3F), 0x80 | (cp & 0x3F));
    } else {
      bytes.push(0xE0 | (c >> 12), 0x80 | ((c >> 6) & 0x3F), 0x80 | (c & 0x3F));
    }
  }
  return bytes;
}
function _utf8Decode(bytes) {
  var str = '';
  var i = 0;
  while (i < bytes.length) {
    var b = bytes[i];
    if (b < 0x80) { str += String.fromCharCode(b); i++; }
    else if ((b & 0xE0) === 0xC0) { str += String.fromCharCode(((b & 0x1F) << 6) | (bytes[i+1] & 0x3F)); i += 2; }
    else if ((b & 0xF0) === 0xE0) { str += String.fromCharCode(((b & 0x0F) << 12) | ((bytes[i+1] & 0x3F) << 6) | (bytes[i+2] & 0x3F)); i += 3; }
    else if ((b & 0xF8) === 0xF0) { var cp = ((b & 0x07) << 18) | ((bytes[i+1] & 0x3F) << 12) | ((bytes[i+2] & 0x3F) << 6) | (bytes[i+3] & 0x3F); cp -= 0x10000; str += String.fromCharCode((cp >> 10) + 0xD800, (cp & 0x3FF) + 0xDC00); i += 4; }
    else { i++; }
  }
  return str;
}
// _utf8Encode/_utf8Decode are IIFE-local vars, available to all module shims

function Buffer(arg) {
  if (typeof arg === 'number') {
    this._data = new Uint8Array(arg);
  } else if (arg instanceof ArrayBuffer) {
    this._data = new Uint8Array(arg);
  } else if (arg instanceof Uint8Array) {
    this._data = new Uint8Array(arg);
  } else if (Array.isArray(arg)) {
    this._data = new Uint8Array(arg);
  } else {
    this._data = new Uint8Array(0);
  }
  this.length = this._data.length;
}
Buffer.from = function(data, encoding) {
  if (typeof data === 'string') {
    return new Buffer(_utf8Encode(data));
  }
  if (data instanceof ArrayBuffer) return new Buffer(data);
  if (data instanceof Uint8Array) return new Buffer(data);
  if (Array.isArray(data)) return new Buffer(data);
  if (data && data._data) return new Buffer(data._data.slice());
  return new Buffer(0);
};
Buffer.alloc = function(size, fill) {
  var buf = new Buffer(size);
  if (fill !== undefined) {
    var fillByte = typeof fill === 'number' ? fill : 0;
    buf._data.fill(fillByte);
  }
  return buf;
};
Buffer.allocUnsafe = Buffer.alloc;
Buffer.isBuffer = function(obj) { return obj instanceof Buffer; };
Buffer.concat = function(list, totalLength) {
  if (!totalLength) {
    totalLength = 0;
    for (var i = 0; i < list.length; i++) totalLength += list[i].length;
  }
  var result = new Uint8Array(totalLength);
  var offset = 0;
  for (var i = 0; i < list.length; i++) {
    result.set(list[i]._data, offset);
    offset += list[i].length;
  }
  return new Buffer(result);
};
Buffer.byteLength = function(str) {
  return _utf8Encode(str).length;
};
Buffer.prototype.toString = function(encoding) {
  return _utf8Decode(this._data);
};
Buffer.prototype.toJSON = function() {
  return { type: 'Buffer', data: Array.from(this._data) };
};
Buffer.prototype.slice = function(start, end) {
  return new Buffer(this._data.slice(start, end));
};
Buffer.prototype.copy = function(target, targetStart, sourceStart, sourceEnd) {
  targetStart = targetStart || 0;
  sourceStart = sourceStart || 0;
  sourceEnd = sourceEnd || this.length;
  var sub = this._data.subarray(sourceStart, sourceEnd);
  target._data.set(sub, targetStart);
  return sub.length;
};
Buffer.prototype.write = function(str, offset) {
  var bytes = _utf8Encode(str);
  offset = offset || 0;
  this._data.set(bytes, offset);
  return bytes.length;
};
Buffer.prototype.fill = function(val, offset, end) {
  this._data.fill(typeof val === 'number' ? val : 0, offset, end);
  return this;
};
Buffer.prototype.equals = function(other) {
  if (this.length !== other.length) return false;
  for (var i = 0; i < this.length; i++) {
    if (this._data[i] !== other._data[i]) return false;
  }
  return true;
};
Buffer.prototype.readUInt8 = function(offset) { return this._data[offset]; };
Buffer.prototype.writeUInt8 = function(value, offset) { this._data[offset] = value; return offset + 1; };
globalThis[Symbol.for('jb:buffer')] = { Buffer: Buffer };
globalThis.Buffer = Buffer;
`;
var STREAM_MODULE_SOURCE = `
var _EE = globalThis[Symbol.for('jb:events')].EventEmitter;

function Stream() { _EE.call(this); }
Stream.prototype = Object.create(_EE.prototype);
Stream.prototype.constructor = Stream;
Stream.prototype.pipe = function(dest) {
  this.on('data', function(chunk) { dest.write(chunk); });
  this.on('end', function() { if (dest.end) dest.end(); });
  return dest;
};

function Readable(opts) {
  Stream.call(this);
  this.readable = true;
  this._readableState = { ended: false, buffer: [] };
}
Readable.prototype = Object.create(Stream.prototype);
Readable.prototype.constructor = Readable;
Readable.prototype.read = function() { return null; };
Readable.prototype.push = function(chunk) {
  if (chunk === null) { this._readableState.ended = true; this.emit('end'); return false; }
  this.emit('data', chunk);
  return true;
};
Readable.prototype.destroy = function() { this.emit('close'); return this; };

function Writable(opts) {
  Stream.call(this);
  this.writable = true;
  this._writableState = { ended: false };
}
Writable.prototype = Object.create(Stream.prototype);
Writable.prototype.constructor = Writable;
Writable.prototype.write = function(chunk) { return true; };
Writable.prototype.end = function(chunk) {
  if (chunk) this.write(chunk);
  this._writableState.ended = true;
  this.emit('finish');
  return this;
};
Writable.prototype.destroy = function() { this.emit('close'); return this; };

function Duplex(opts) {
  Readable.call(this, opts);
  Writable.call(this, opts);
}
Duplex.prototype = Object.create(Readable.prototype);
var _wKeys = Object.keys(Writable.prototype);
for (var _wi = 0; _wi < _wKeys.length; _wi++) {
  if (!Duplex.prototype[_wKeys[_wi]]) Duplex.prototype[_wKeys[_wi]] = Writable.prototype[_wKeys[_wi]];
}
Duplex.prototype.constructor = Duplex;

function Transform(opts) { Duplex.call(this, opts); }
Transform.prototype = Object.create(Duplex.prototype);
Transform.prototype.constructor = Transform;
Transform.prototype._transform = function(chunk, encoding, cb) { if (cb) cb(null, chunk); };

function PassThrough(opts) { Transform.call(this, opts); }
PassThrough.prototype = Object.create(Transform.prototype);
PassThrough.prototype.constructor = PassThrough;

function pipeline() {
  var streams = Array.prototype.slice.call(arguments);
  var cb = typeof streams[streams.length - 1] === 'function' ? streams.pop() : null;
  for (var i = 0; i < streams.length - 1; i++) streams[i].pipe(streams[i + 1]);
  if (cb) {
    var last = streams[streams.length - 1];
    last.on('finish', function() { cb(null); });
    last.on('error', function(e) { cb(e); });
  }
  return streams[streams.length - 1];
}

globalThis[Symbol.for('jb:stream')] = {
  Stream: Stream, Readable: Readable, Writable: Writable,
  Duplex: Duplex, Transform: Transform, PassThrough: PassThrough,
  pipeline: pipeline
};
`;
var STRING_DECODER_MODULE_SOURCE = `
function StringDecoder(encoding) {
  this.encoding = (encoding || 'utf-8').toLowerCase();
  if (this.encoding === 'utf8') this.encoding = 'utf-8';
}
StringDecoder.prototype.write = function(buf) {
  if (typeof buf === 'string') return buf;
  var data = buf instanceof Uint8Array ? buf : (buf && buf._data ? buf._data : new Uint8Array(0));
  return _utf8Decode(data);
};
StringDecoder.prototype.end = function(buf) {
  if (buf) return this.write(buf);
  return '';
};
globalThis[Symbol.for('jb:string_decoder')] = { StringDecoder: StringDecoder };
`;
var QUERYSTRING_MODULE_SOURCE = `
var _qs = {
  parse: function(str, sep, eq) {
    sep = sep || '&'; eq = eq || '=';
    var result = Object.create(null);
    if (!str || typeof str !== 'string') return result;
    var pairs = str.split(sep);
    for (var i = 0; i < pairs.length; i++) {
      var idx = pairs[i].indexOf(eq);
      var key, val;
      if (idx >= 0) {
        key = decodeURIComponent(pairs[i].slice(0, idx).replace(/\\+/g, ' '));
        val = decodeURIComponent(pairs[i].slice(idx + 1).replace(/\\+/g, ' '));
      } else {
        key = decodeURIComponent(pairs[i].replace(/\\+/g, ' '));
        val = '';
      }
      if (result[key] !== undefined) {
        if (Array.isArray(result[key])) result[key].push(val);
        else result[key] = [result[key], val];
      } else {
        result[key] = val;
      }
    }
    return result;
  },
  stringify: function(obj, sep, eq) {
    sep = sep || '&'; eq = eq || '=';
    var pairs = [];
    var keys = Object.keys(obj);
    for (var i = 0; i < keys.length; i++) {
      var key = keys[i];
      var val = obj[key];
      if (Array.isArray(val)) {
        for (var j = 0; j < val.length; j++) {
          pairs.push(encodeURIComponent(key) + eq + encodeURIComponent(val[j]));
        }
      } else {
        pairs.push(encodeURIComponent(key) + eq + encodeURIComponent(val));
      }
    }
    return pairs.join(sep);
  },
  escape: function(str) { return encodeURIComponent(str); },
  unescape: function(str) { return decodeURIComponent(str); }
};
_qs.decode = _qs.parse;
_qs.encode = _qs.stringify;
globalThis[Symbol.for('jb:querystring')] = _qs;
`;
var UNSUPPORTED_MODULES = Object.assign(
  /* @__PURE__ */ Object.create(null),
  {
    http: "Use fetch() for HTTP requests.",
    https: "Use fetch() for HTTP requests.",
    http2: "Use fetch() for HTTP requests.",
    net: "Network socket APIs are not supported.",
    tls: "Network socket APIs are not supported.",
    dgram: "Network socket APIs are not supported.",
    dns: "DNS APIs are not supported.",
    cluster: "Cluster APIs are not supported.",
    worker_threads: "Worker thread APIs are not supported.",
    vm: "VM APIs are not supported.",
    v8: "V8 APIs are not supported.",
    inspector: "Inspector APIs are not supported.",
    readline: "Readline APIs are not supported.",
    repl: "REPL APIs are not supported.",
    module: "Module APIs are not supported.",
    perf_hooks: "Performance hooks are not supported.",
    async_hooks: "Async hooks are not supported.",
    diagnostics_channel: "Diagnostics channel is not supported.",
    trace_events: "Trace events are not supported.",
    crypto: "Crypto APIs are not available in this sandbox.",
    zlib: "Compression APIs are not supported.",
    tty: "TTY APIs are not supported.",
    domain: "Domain APIs are not supported."
  }
);

// src/commands/js-exec/path-polyfill.ts
var PATH_MODULE_SOURCE = `
(function() {
  var sep = '/';
  var delimiter = ':';

  function normalize(p) {
    if (p === '') return '.';
    var isAbs = p.charCodeAt(0) === 47;
    var trailingSlash = p.charCodeAt(p.length - 1) === 47;
    var parts = p.split('/');
    var out = [];
    for (var i = 0; i < parts.length; i++) {
      var seg = parts[i];
      if (seg === '' || seg === '.') continue;
      if (seg === '..') {
        if (out.length > 0 && out[out.length - 1] !== '..') out.pop();
        else if (!isAbs) out.push('..');
      } else {
        out.push(seg);
      }
    }
    var result = out.join('/');
    if (isAbs) result = '/' + result;
    if (trailingSlash && result[result.length - 1] !== '/') result += '/';
    return result || (isAbs ? '/' : '.');
  }

  function join() {
    var joined = '';
    for (var i = 0; i < arguments.length; i++) {
      var arg = arguments[i];
      if (typeof arg !== 'string') throw new TypeError('Path must be a string');
      if (arg.length > 0) {
        if (joined.length > 0) joined += '/' + arg;
        else joined = arg;
      }
    }
    if (joined.length === 0) return '.';
    return normalize(joined);
  }

  function resolve() {
    var resolved = '';
    var resolvedAbsolute = false;
    for (var i = arguments.length - 1; i >= -1 && !resolvedAbsolute; i--) {
      var path = i >= 0 ? arguments[i] : globalThis.process.cwd();
      if (typeof path !== 'string') throw new TypeError('Path must be a string');
      if (path.length === 0) continue;
      if (resolved.length > 0) resolved = path + '/' + resolved;
      else resolved = path;
      resolvedAbsolute = path.charCodeAt(0) === 47;
    }
    resolved = normalize(resolved);
    if (resolvedAbsolute) return '/' + resolved.replace(/^\\/+/, '');
    return resolved.length > 0 ? resolved : '.';
  }

  function isAbsolute(p) {
    return typeof p === 'string' && p.length > 0 && p.charCodeAt(0) === 47;
  }

  function dirname(p) {
    if (p.length === 0) return '.';
    var hasRoot = p.charCodeAt(0) === 47;
    var end = -1;
    for (var i = p.length - 1; i >= 1; i--) {
      if (p.charCodeAt(i) === 47) { end = i; break; }
    }
    if (end === -1) return hasRoot ? '/' : '.';
    if (hasRoot && end === 0) return '/';
    return p.slice(0, end);
  }

  function basename(p, ext) {
    var start = 0;
    for (var i = p.length - 1; i >= 0; i--) {
      if (p.charCodeAt(i) === 47) { start = i + 1; break; }
    }
    var base = p.slice(start);
    if (ext && base.endsWith(ext)) {
      base = base.slice(0, base.length - ext.length);
    }
    return base;
  }

  function extname(p) {
    var startDot = -1;
    var startPart = 0;
    for (var i = p.length - 1; i >= 0; i--) {
      var code = p.charCodeAt(i);
      if (code === 47) { startPart = i + 1; break; }
      if (code === 46 && startDot === -1) startDot = i;
    }
    if (startDot === -1 || startDot === startPart ||
        (startDot === startPart + 1 && p.charCodeAt(startPart) === 46)) {
      return '';
    }
    return p.slice(startDot);
  }

  function relative(from, to) {
    if (from === to) return '';
    from = resolve(from);
    to = resolve(to);
    if (from === to) return '';
    var fromParts = from.split('/').filter(Boolean);
    var toParts = to.split('/').filter(Boolean);
    var common = 0;
    var length = Math.min(fromParts.length, toParts.length);
    for (var i = 0; i < length; i++) {
      if (fromParts[i] !== toParts[i]) break;
      common++;
    }
    var ups = [];
    for (var i = common; i < fromParts.length; i++) ups.push('..');
    return ups.concat(toParts.slice(common)).join('/') || '.';
  }

  function parse(p) {
    var root = p.charCodeAt(0) === 47 ? '/' : '';
    var dir = dirname(p);
    var base = basename(p);
    var ext = extname(p);
    var name = ext ? base.slice(0, base.length - ext.length) : base;
    return { root: root, dir: dir, base: base, ext: ext, name: name };
  }

  function format(obj) {
    var dir = obj.dir || obj.root || '';
    var base = obj.base || ((obj.name || '') + (obj.ext || ''));
    if (!dir) return base;
    if (dir === obj.root) return dir + base;
    return dir + '/' + base;
  }

  var posix = { sep: sep, delimiter: delimiter, join: join, resolve: resolve, normalize: normalize, isAbsolute: isAbsolute, dirname: dirname, basename: basename, extname: extname, relative: relative, parse: parse, format: format };
  posix.posix = posix;

  globalThis[Symbol.for('jb:path')] = posix;
})();
`;

// src/commands/js-exec/worker.ts
var quickjsModule = null;
var quickjsLoading = null;
async function getQuickJSModule() {
  if (quickjsModule) {
    return quickjsModule;
  }
  if (quickjsLoading) {
    return quickjsLoading;
  }
  quickjsLoading = getQuickJS();
  quickjsModule = await quickjsLoading;
  return quickjsModule;
}
var MEMORY_LIMIT = 64 * 1024 * 1024;
var INTERRUPT_CYCLES = 1e5;
function formatError(errorVal) {
  if (typeof errorVal === "object" && errorVal !== null && "message" in errorVal) {
    const err = errorVal;
    const msg = err.message;
    if (err.stack) {
      const lines = err.stack.split("\n");
      for (const line of lines) {
        const trimmed = line.trim();
        if (trimmed.startsWith("at ")) {
          const cleaned = trimmed.replace(/^at <eval> \((\/.+)\)$/, "at $1");
          return `${cleaned}: ${msg}`;
        }
      }
    }
    return msg;
  }
  return String(errorVal);
}
function throwError(context, message) {
  return { error: context.newError(message) };
}
function jsToHandle(context, value) {
  if (value === null || value === void 0) {
    return context.undefined;
  }
  if (typeof value === "string") {
    return context.newString(value);
  }
  if (typeof value === "number") {
    return context.newNumber(value);
  }
  if (typeof value === "boolean") {
    return value ? context.true : context.false;
  }
  if (Array.isArray(value)) {
    const arr = context.newArray();
    for (let i = 0; i < value.length; i++) {
      const elemHandle = jsToHandle(context, value[i]);
      context.setProp(arr, i, elemHandle);
      elemHandle.dispose();
    }
    return arr;
  }
  if (typeof value === "object") {
    const obj = context.newObject();
    for (const [k, v] of Object.entries(value)) {
      const valHandle = jsToHandle(context, v);
      context.setProp(obj, k, valHandle);
      valHandle.dispose();
    }
    return obj;
  }
  return context.undefined;
}
function resolveModulePath(name, fromFile, cwd) {
  if (name.startsWith("/")) return name;
  const base = fromFile ? fromFile.substring(0, fromFile.lastIndexOf("/")) || "/" : cwd;
  const parts = `${base}/${name}`.split("/").filter(Boolean);
  const resolved = [];
  for (const p of parts) {
    if (p === "..") resolved.pop();
    else if (p !== ".") resolved.push(p);
  }
  return `/${resolved.join("/")}`;
}
var VIRTUAL_MODULES = Object.assign(
  /* @__PURE__ */ Object.create(null),
  {
    fs: `
    const _fs = globalThis.fs;
    export const readFile = _fs.readFile;
    export const readFileSync = function(path, opts) { return _fs.readFileSync(path, opts); };
    export const readFileBuffer = _fs.readFileBuffer;
    export const writeFile = _fs.writeFile;
    export const writeFileSync = _fs.writeFileSync;
    export const stat = _fs.stat;
    export const statSync = _fs.statSync;
    export const lstat = _fs.lstat;
    export const lstatSync = _fs.lstatSync;
    export const readdir = _fs.readdir;
    export const readdirSync = _fs.readdirSync;
    export const mkdir = _fs.mkdir;
    export const mkdirSync = _fs.mkdirSync;
    export const rm = _fs.rm;
    export const rmSync = _fs.rmSync;
    export const exists = _fs.exists;
    export const existsSync = _fs.existsSync;
    export const appendFile = _fs.appendFile;
    export const appendFileSync = _fs.appendFileSync;
    export const symlink = _fs.symlink;
    export const symlinkSync = _fs.symlinkSync;
    export const readlink = _fs.readlink;
    export const readlinkSync = _fs.readlinkSync;
    export const chmod = _fs.chmod;
    export const chmodSync = _fs.chmodSync;
    export const realpath = _fs.realpath;
    export const realpathSync = _fs.realpathSync;
    export const rename = _fs.rename;
    export const renameSync = _fs.renameSync;
    export const copyFile = _fs.copyFile;
    export const copyFileSync = _fs.copyFileSync;
    export const unlinkSync = _fs.unlinkSync;
    export const unlink = _fs.unlink;
    export const rmdirSync = _fs.rmdirSync;
    export const rmdir = _fs.rmdir;
    export const promises = _fs.promises;
    export default _fs;
  `,
    path: `${PATH_MODULE_SOURCE}
    const _path = globalThis[Symbol.for('jb:path')];
    export const join = _path.join;
    export const resolve = _path.resolve;
    export const normalize = _path.normalize;
    export const isAbsolute = _path.isAbsolute;
    export const dirname = _path.dirname;
    export const basename = _path.basename;
    export const extname = _path.extname;
    export const relative = _path.relative;
    export const parse = _path.parse;
    export const format = _path.format;
    export const sep = _path.sep;
    export const delimiter = _path.delimiter;
    export const posix = _path.posix;
    export default _path;
  `,
    process: `
    const _process = globalThis.process;
    export const argv = _process.argv;
    export const cwd = _process.cwd;
    export const exit = _process.exit;
    export const env = _process.env;
    export const platform = _process.platform;
    export const arch = _process.arch;
    export const versions = _process.versions;
    export const version = _process.version;
    export default _process;
  `,
    child_process: `
    const _exec = globalThis[Symbol.for('jb:exec')];
    const _execArgs = globalThis[Symbol.for('jb:execArgs')];
    export function execSync(cmd, opts) {
      var r = _exec(cmd, opts);
      if (r.exitCode !== 0) {
        var e = new Error('Command failed: ' + cmd);
        e.status = r.exitCode;
        e.stderr = r.stderr;
        e.stdout = r.stdout;
        throw e;
      }
      return r.stdout;
    }
    export function exec(cmd, opts) { return _exec(cmd, opts); }
    export function spawnSync(cmd, args, opts) {
      var r = _execArgs(cmd, args || []);
      return { stdout: r.stdout, stderr: r.stderr, status: r.exitCode };
    }
    export default { exec: exec, execSync: execSync, spawnSync: spawnSync };
  `,
    os: `
    const _os = globalThis[Symbol.for('jb:os')];
    export const platform = _os.platform;
    export const arch = _os.arch;
    export const homedir = _os.homedir;
    export const tmpdir = _os.tmpdir;
    export const type = _os.type;
    export const hostname = _os.hostname;
    export const EOL = _os.EOL;
    export const cpus = _os.cpus;
    export const totalmem = _os.totalmem;
    export const freemem = _os.freemem;
    export const endianness = _os.endianness;
    export default _os;
  `,
    url: `
    const _url = globalThis[Symbol.for('jb:url')];
    export const URL = _url.URL;
    export const URLSearchParams = _url.URLSearchParams;
    export const parse = _url.parse;
    export const format = _url.format;
    export default _url;
  `,
    assert: `
    const _assert = globalThis[Symbol.for('jb:assert')];
    export const ok = _assert.ok;
    export const equal = _assert.equal;
    export const notEqual = _assert.notEqual;
    export const strictEqual = _assert.strictEqual;
    export const notStrictEqual = _assert.notStrictEqual;
    export const deepEqual = _assert.deepEqual;
    export const deepStrictEqual = _assert.deepStrictEqual;
    export const notDeepEqual = _assert.notDeepEqual;
    export const throws = _assert.throws;
    export const doesNotThrow = _assert.doesNotThrow;
    export const fail = _assert.fail;
    export default _assert;
  `,
    util: `
    const _util = globalThis[Symbol.for('jb:util')];
    export const format = _util.format;
    export const inspect = _util.inspect;
    export const promisify = _util.promisify;
    export const types = _util.types;
    export const inherits = _util.inherits;
    export default _util;
  `,
    events: `
    const _events = globalThis[Symbol.for('jb:events')];
    export const EventEmitter = _events.EventEmitter;
    export default _events;
  `,
    buffer: `
    const _buffer = globalThis[Symbol.for('jb:buffer')];
    export const Buffer = _buffer.Buffer;
    export default _buffer;
  `,
    stream: `
    const _stream = globalThis[Symbol.for('jb:stream')];
    export const Stream = _stream.Stream;
    export const Readable = _stream.Readable;
    export const Writable = _stream.Writable;
    export const Duplex = _stream.Duplex;
    export const Transform = _stream.Transform;
    export const PassThrough = _stream.PassThrough;
    export const pipeline = _stream.pipeline;
    export default _stream;
  `,
    string_decoder: `
    const _sd = globalThis[Symbol.for('jb:string_decoder')];
    export const StringDecoder = _sd.StringDecoder;
    export default _sd;
  `,
    querystring: `
    const _qs = globalThis[Symbol.for('jb:querystring')];
    export const parse = _qs.parse;
    export const stringify = _qs.stringify;
    export const escape = _qs.escape;
    export const unescape = _qs.unescape;
    export const decode = _qs.decode;
    export const encode = _qs.encode;
    export default _qs;
  `
  }
);
for (const [name, hint] of Object.entries(UNSUPPORTED_MODULES)) {
  VIRTUAL_MODULES[name] = `throw new Error("Module '${name}' is not available in the js-exec sandbox. ${hint} Run 'js-exec --help' for available modules.");`;
}
function setupContext(context, backend, input) {
  const consoleObj = context.newObject();
  const logFn = context.newFunction("log", (...args) => {
    const parts = args.map((a) => {
      const val = context.dump(a);
      return typeof val === "string" ? val : JSON.stringify(val);
    });
    try {
      backend.writeStdout(`${parts.join(" ")}
`);
    } catch (e) {
      return throwError(context, e.message || "write failed");
    }
    return context.undefined;
  });
  context.setProp(consoleObj, "log", logFn);
  logFn.dispose();
  const errorFn = context.newFunction("error", (...args) => {
    const parts = args.map((a) => {
      const val = context.dump(a);
      return typeof val === "string" ? val : JSON.stringify(val);
    });
    try {
      backend.writeStderr(`${parts.join(" ")}
`);
    } catch (e) {
      return throwError(context, e.message || "write failed");
    }
    return context.undefined;
  });
  context.setProp(consoleObj, "error", errorFn);
  errorFn.dispose();
  const warnFn = context.newFunction("warn", (...args) => {
    const parts = args.map((a) => {
      const val = context.dump(a);
      return typeof val === "string" ? val : JSON.stringify(val);
    });
    try {
      backend.writeStderr(`${parts.join(" ")}
`);
    } catch (e) {
      return throwError(context, e.message || "write failed");
    }
    return context.undefined;
  });
  context.setProp(consoleObj, "warn", warnFn);
  warnFn.dispose();
  context.setProp(context.global, "console", consoleObj);
  consoleObj.dispose();
  const fsObj = context.newObject();
  const readFileFn = context.newFunction(
    "readFile",
    (pathHandle) => {
      const path = context.getString(pathHandle);
      try {
        const data = backend.readFile(path);
        return context.newString(new TextDecoder().decode(data));
      } catch (e) {
        return throwError(context, e.message || "readFile failed");
      }
    }
  );
  context.setProp(fsObj, "readFile", readFileFn);
  readFileFn.dispose();
  const readFileBufferFn = context.newFunction(
    "readFileBuffer",
    (pathHandle) => {
      const path = context.getString(pathHandle);
      try {
        const data = backend.readFile(path);
        return context.newArrayBuffer(
          data.buffer.slice(data.byteOffset, data.byteOffset + data.byteLength)
        );
      } catch (e) {
        return throwError(
          context,
          e.message || "readFileBuffer failed"
        );
      }
    }
  );
  context.setProp(fsObj, "readFileBuffer", readFileBufferFn);
  readFileBufferFn.dispose();
  const writeFileFn = context.newFunction(
    "writeFile",
    (pathHandle, dataHandle) => {
      const path = context.getString(pathHandle);
      const data = context.getString(dataHandle);
      try {
        backend.writeFile(path, new TextEncoder().encode(data));
        return context.undefined;
      } catch (e) {
        return throwError(context, e.message || "writeFile failed");
      }
    }
  );
  context.setProp(fsObj, "writeFile", writeFileFn);
  writeFileFn.dispose();
  const statFn = context.newFunction("stat", (pathHandle) => {
    const path = context.getString(pathHandle);
    try {
      const stat = backend.stat(path);
      return jsToHandle(context, {
        isFile: stat.isFile,
        isDirectory: stat.isDirectory,
        isSymbolicLink: stat.isSymbolicLink,
        mode: stat.mode,
        size: stat.size,
        mtime: stat.mtime.toISOString()
      });
    } catch (e) {
      return throwError(context, e.message || "stat failed");
    }
  });
  context.setProp(fsObj, "stat", statFn);
  statFn.dispose();
  const readdirFn = context.newFunction(
    "readdir",
    (pathHandle) => {
      const path = context.getString(pathHandle);
      try {
        const entries = backend.readdir(path);
        return jsToHandle(context, entries);
      } catch (e) {
        return throwError(context, e.message || "readdir failed");
      }
    }
  );
  context.setProp(fsObj, "readdir", readdirFn);
  readdirFn.dispose();
  const mkdirFn = context.newFunction(
    "mkdir",
    (pathHandle, optsHandle) => {
      const path = context.getString(pathHandle);
      let recursive = false;
      if (optsHandle) {
        const opts = context.dump(optsHandle);
        if (opts && typeof opts === "object" && "recursive" in opts) {
          recursive = Boolean(opts.recursive);
        }
      }
      try {
        backend.mkdir(path, recursive);
        return context.undefined;
      } catch (e) {
        return throwError(context, e.message || "mkdir failed");
      }
    }
  );
  context.setProp(fsObj, "mkdir", mkdirFn);
  mkdirFn.dispose();
  const rmFn = context.newFunction(
    "rm",
    (pathHandle, optsHandle) => {
      const path = context.getString(pathHandle);
      let recursive = false;
      let force = false;
      if (optsHandle) {
        const opts = context.dump(optsHandle);
        if (opts && typeof opts === "object") {
          if ("recursive" in opts) recursive = Boolean(opts.recursive);
          if ("force" in opts) force = Boolean(opts.force);
        }
      }
      try {
        backend.rm(path, recursive, force);
        return context.undefined;
      } catch (e) {
        return throwError(context, e.message || "rm failed");
      }
    }
  );
  context.setProp(fsObj, "rm", rmFn);
  rmFn.dispose();
  const existsFn = context.newFunction(
    "exists",
    (pathHandle) => {
      const path = context.getString(pathHandle);
      return backend.exists(path) ? context.true : context.false;
    }
  );
  context.setProp(fsObj, "exists", existsFn);
  existsFn.dispose();
  const appendFileFn = context.newFunction(
    "appendFile",
    (pathHandle, dataHandle) => {
      const path = context.getString(pathHandle);
      const data = context.getString(dataHandle);
      try {
        backend.appendFile(path, new TextEncoder().encode(data));
        return context.undefined;
      } catch (e) {
        return throwError(context, e.message || "appendFile failed");
      }
    }
  );
  context.setProp(fsObj, "appendFile", appendFileFn);
  appendFileFn.dispose();
  const lstatFn = context.newFunction("lstat", (pathHandle) => {
    const path = context.getString(pathHandle);
    try {
      const s = backend.lstat(path);
      return jsToHandle(context, {
        isFile: s.isFile,
        isDirectory: s.isDirectory,
        isSymbolicLink: s.isSymbolicLink,
        mode: s.mode,
        size: s.size,
        mtime: s.mtime.toISOString()
      });
    } catch (e) {
      return throwError(context, e.message || "lstat failed");
    }
  });
  context.setProp(fsObj, "lstat", lstatFn);
  lstatFn.dispose();
  const symlinkFn = context.newFunction(
    "symlink",
    (targetHandle, pathHandle) => {
      const target = context.getString(targetHandle);
      const linkPath = context.getString(pathHandle);
      try {
        backend.symlink(target, linkPath);
        return context.undefined;
      } catch (e) {
        return throwError(context, e.message || "symlink failed");
      }
    }
  );
  context.setProp(fsObj, "symlink", symlinkFn);
  symlinkFn.dispose();
  const readlinkFn = context.newFunction(
    "readlink",
    (pathHandle) => {
      const path = context.getString(pathHandle);
      try {
        const target = backend.readlink(path);
        return context.newString(target);
      } catch (e) {
        return throwError(context, e.message || "readlink failed");
      }
    }
  );
  context.setProp(fsObj, "readlink", readlinkFn);
  readlinkFn.dispose();
  const chmodFn = context.newFunction(
    "chmod",
    (pathHandle, modeHandle) => {
      const path = context.getString(pathHandle);
      const mode = context.dump(modeHandle);
      try {
        backend.chmod(path, typeof mode === "number" ? mode : 0);
        return context.undefined;
      } catch (e) {
        return throwError(context, e.message || "chmod failed");
      }
    }
  );
  context.setProp(fsObj, "chmod", chmodFn);
  chmodFn.dispose();
  const realpathFn = context.newFunction(
    "realpath",
    (pathHandle) => {
      const path = context.getString(pathHandle);
      try {
        const resolved = backend.realpath(path);
        return context.newString(resolved);
      } catch (e) {
        return throwError(context, e.message || "realpath failed");
      }
    }
  );
  context.setProp(fsObj, "realpath", realpathFn);
  realpathFn.dispose();
  const renameFn = context.newFunction(
    "rename",
    (oldHandle, newHandle) => {
      const oldPath = context.getString(oldHandle);
      const newPath = context.getString(newHandle);
      try {
        backend.rename(oldPath, newPath);
        return context.undefined;
      } catch (e) {
        return throwError(context, e.message || "rename failed");
      }
    }
  );
  context.setProp(fsObj, "rename", renameFn);
  renameFn.dispose();
  const copyFileFn = context.newFunction(
    "copyFile",
    (srcHandle, destHandle) => {
      const src = context.getString(srcHandle);
      const dest = context.getString(destHandle);
      try {
        backend.copyFile(src, dest);
        return context.undefined;
      } catch (e) {
        return throwError(context, e.message || "copyFile failed");
      }
    }
  );
  context.setProp(fsObj, "copyFile", copyFileFn);
  copyFileFn.dispose();
  context.setProp(context.global, "fs", fsObj);
  fsObj.dispose();
  const fetchFn = context.newFunction(
    "fetch",
    (urlHandle, optsHandle) => {
      const url = context.getString(urlHandle);
      let options;
      if (optsHandle) {
        options = context.dump(optsHandle);
      }
      try {
        const result = backend.httpRequest(url, {
          method: options?.method,
          headers: options?.headers,
          body: options?.body
        });
        return jsToHandle(context, result);
      } catch (e) {
        return throwError(context, e.message || "fetch failed");
      }
    }
  );
  context.setProp(context.global, "__fetch", fetchFn);
  fetchFn.dispose();
  const execFn = context.newFunction(
    "exec",
    (cmdHandle, optsHandle) => {
      const command = context.getString(cmdHandle);
      let stdin;
      if (optsHandle) {
        const opts = context.dump(optsHandle);
        if (opts?.stdin) {
          stdin = String(opts.stdin);
        }
      }
      try {
        const result = backend.execCommand(command, stdin);
        return jsToHandle(context, result);
      } catch (e) {
        return throwError(context, e.message || "exec failed");
      }
    }
  );
  context.setProp(context.global, "__exec", execFn);
  execFn.dispose();
  const execArgsFn = context.newFunction(
    "execArgs",
    (cmdHandle, argsHandle) => {
      const command = context.getString(cmdHandle);
      const args = context.dump(argsHandle);
      try {
        const result = backend.execCommandArgs(command, args);
        return jsToHandle(context, result);
      } catch (e) {
        return throwError(context, e.message || "exec failed");
      }
    }
  );
  context.setProp(context.global, "__execArgs", execArgsFn);
  execArgsFn.dispose();
  const envObj = jsToHandle(context, input.env);
  context.setProp(context.global, "env", envObj);
  envObj.dispose();
  const processObj = context.newObject();
  const argv = [input.scriptPath || "js-exec", ...input.args];
  const argvHandle = jsToHandle(context, argv);
  context.setProp(processObj, "argv", argvHandle);
  argvHandle.dispose();
  const cwdFn = context.newFunction("cwd", () => {
    return context.newString(input.cwd);
  });
  context.setProp(processObj, "cwd", cwdFn);
  cwdFn.dispose();
  const exitFn = context.newFunction("exit", (codeHandle) => {
    let code = 0;
    if (codeHandle) {
      const val = context.dump(codeHandle);
      code = typeof val === "number" ? val : 0;
    }
    backend.exit(code);
    return throwError(context, "__EXIT__");
  });
  context.setProp(processObj, "exit", exitFn);
  exitFn.dispose();
  context.setProp(context.global, "process", processObj);
  processObj.dispose();
  const compatResult = context.evalCode(
    `(function() {
  // Bridge native handles from string keys (set by QuickJS setProp) to symbol keys
  globalThis[Symbol.for('jb:fetch')] = globalThis.__fetch;
  globalThis[Symbol.for('jb:exec')] = globalThis.__exec;
  globalThis[Symbol.for('jb:execArgs')] = globalThis.__execArgs;
  delete globalThis.__fetch;
  delete globalThis.__exec;
  delete globalThis.__execArgs;

  var _fs = globalThis.fs;
  // Save original native functions
  var orig = Object.create(null);
  var allNames = [
    'readFile', 'readFileBuffer', 'writeFile', 'stat', 'lstat', 'readdir',
    'mkdir', 'rm', 'exists', 'appendFile', 'symlink', 'readlink',
    'chmod', 'realpath', 'rename', 'copyFile'
  ];
  for (var i = 0; i < allNames.length; i++) {
    orig[allNames[i]] = _fs[allNames[i]];
  }

  // Wrap async-style methods to always throw (matching Node.js which requires a callback).
  // In Node.js, calling fs.readFile() without a callback throws TypeError.
  // We don't support callbacks, so the async form always errors.
  function wrapCb(fn, name) {
    return function() {
      throw new Error(
        "fs." + name + "() with callbacks is not supported. " +
        "Use fs." + name + "Sync() or fs.promises." + name + "() instead."
      );
    };
  }
  var cbNames = [
    'readFile', 'writeFile', 'stat', 'lstat', 'readdir', 'mkdir',
    'rm', 'appendFile', 'symlink', 'readlink', 'chmod', 'realpath',
    'rename', 'copyFile'
  ];
  for (var i = 0; i < cbNames.length; i++) {
    if (orig[cbNames[i]]) _fs[cbNames[i]] = wrapCb(orig[cbNames[i]], cbNames[i]);
  }
  // exists: callback is especially common in legacy Node.js
  _fs.exists = wrapCb(orig.exists, 'exists');

  // readFileSync: match Node.js behavior
  // - No encoding: return Buffer
  // - With encoding (e.g. 'utf8'): return string
  _fs.readFileSync = function(path, opts) {
    var encoding = typeof opts === 'string' ? opts : (opts && opts.encoding);
    if (encoding) return orig.readFile(path);
    return Buffer.from(orig.readFileBuffer(path));
  };
  _fs.writeFileSync = orig.writeFile;
  _fs.statSync = orig.stat;
  _fs.lstatSync = orig.lstat;
  _fs.readdirSync = orig.readdir;
  _fs.mkdirSync = orig.mkdir;
  _fs.rmSync = orig.rm;
  _fs.existsSync = orig.exists;
  _fs.appendFileSync = orig.appendFile;
  _fs.symlinkSync = orig.symlink;
  _fs.readlinkSync = orig.readlink;
  _fs.chmodSync = orig.chmod;
  _fs.realpathSync = orig.realpath;
  _fs.renameSync = orig.rename;
  _fs.copyFileSync = orig.copyFile;
  _fs.unlinkSync = orig.rm;
  _fs.rmdirSync = orig.rm;
  _fs.unlink = wrapCb(orig.rm, 'unlink');
  _fs.rmdir = wrapCb(orig.rm, 'rmdir');

  // promises namespace
  _fs.promises = {};
  for (var i = 0; i < allNames.length; i++) {
    var m = allNames[i];
    (function(fn) {
      _fs.promises[m] = function() {
        try { return Promise.resolve(fn.apply(null, arguments)); }
        catch(e) { return Promise.reject(e); }
      };
    })(orig[m]);
  }
  // Override promises.readFile to match Node.js behavior (Buffer vs string)
  _fs.promises.readFile = function(path, opts) {
    var encoding = typeof opts === 'string' ? opts : (opts && opts.encoding);
    try {
      if (encoding) return Promise.resolve(orig.readFile(path));
      return Promise.resolve(Buffer.from(orig.readFileBuffer(path)));
    } catch(e) { return Promise.reject(e); }
  };
  _fs.promises.unlink = _fs.promises.rm;
  _fs.promises.rmdir = _fs.promises.rm;
  _fs.promises.access = function(p) {
    return orig.exists(p) ? Promise.resolve() : Promise.reject(new Error('ENOENT: no such file or directory: ' + p));
  };

  // process enhancements
  var _p = globalThis.process;
  _p.env = globalThis.env;
  _p.platform = 'linux';
  _p.arch = 'x64';
  _p.versions = { node: '22.0.0', quickjs: '2024' };
  _p.version = 'v22.0.0';

  // Initialize path module on globalThis so require('path') works
  ${PATH_MODULE_SOURCE}

  // Initialize fetch polyfill (URL, Headers, Request, Response, fetch)
  ${FETCH_POLYFILL_SOURCE}

  // Initialize additional module shims
  ${EVENTS_MODULE_SOURCE}
  ${OS_MODULE_SOURCE}
  ${URL_MODULE_SOURCE}
  ${ASSERT_MODULE_SOURCE}
  ${UTIL_MODULE_SOURCE}
  ${BUFFER_MODULE_SOURCE}
  ${STREAM_MODULE_SOURCE}
  ${STRING_DECODER_MODULE_SOURCE}
  ${QUERYSTRING_MODULE_SOURCE}

  // Wrap console methods to auto-stringify Buffer arguments.
  // In Node.js, console.log(buffer) calls util.inspect \u2192 toString().
  (function() {
    var _cl = console.log;
    var _ce = console.error;
    var _cw = console.warn;
    function fix(a) { return a instanceof Buffer ? a.toString() : a; }
    function wrap(fn) {
      return function() {
        var a = [];
        for (var i = 0; i < arguments.length; i++) a.push(fix(arguments[i]));
        return fn.apply(console, a);
      };
    }
    console.log = wrap(_cl);
    console.error = wrap(_ce);
    console.warn = wrap(_cw);
  })();

  // require() shim for CommonJS compatibility
  var _execFn = globalThis[Symbol.for('jb:exec')];
  var _execArgsFn = globalThis[Symbol.for('jb:execArgs')];
  var _childProcess = {
    exec: function(cmd, opts) { return _execFn(cmd, opts); },
    execSync: function(cmd, opts) {
      var r = _execFn(cmd, opts);
      if (r.exitCode !== 0) {
        var e = new Error('Command failed: ' + cmd);
        e.status = r.exitCode;
        e.stderr = r.stderr;
        e.stdout = r.stdout;
        throw e;
      }
      return r.stdout;
    },
    spawnSync: function(cmd, args, opts) {
      var r = _execArgsFn(cmd, args || []);
      return { stdout: r.stdout, stderr: r.stderr, status: r.exitCode };
    }
  };

  var _modules = Object.create(null);
  _modules.fs = _fs;
  _modules.path = globalThis[Symbol.for('jb:path')];
  _modules.child_process = _childProcess;
  _modules.process = _p;
  _modules.console = globalThis.console;
  _modules.os = globalThis[Symbol.for('jb:os')];
  _modules.url = globalThis[Symbol.for('jb:url')];
  _modules.assert = globalThis[Symbol.for('jb:assert')];
  _modules.util = globalThis[Symbol.for('jb:util')];
  _modules.events = globalThis[Symbol.for('jb:events')];
  _modules.buffer = globalThis[Symbol.for('jb:buffer')];
  _modules.stream = globalThis[Symbol.for('jb:stream')];
  _modules.string_decoder = globalThis[Symbol.for('jb:string_decoder')];
  _modules.querystring = globalThis[Symbol.for('jb:querystring')];

  var _unsupported = Object.create(null);
  var _unsupportedRaw = ${JSON.stringify(UNSUPPORTED_MODULES)};
  Object.keys(_unsupportedRaw).forEach(function(_key) {
    _unsupported[_key] = _unsupportedRaw[_key];
  });

  globalThis.require = function(name) {
    if (name.startsWith('node:')) name = name.slice(5);
    if (Object.prototype.hasOwnProperty.call(_modules, name)) {
      return _modules[name];
    }
    if (Object.prototype.hasOwnProperty.call(_unsupported, name)) {
      var hint = _unsupported[name];
      throw new Error("Module '" + name + "' is not available in the js-exec sandbox. " + hint + " Run 'js-exec --help' for available modules.");
    }
    throw new Error("Cannot find module '" + name + "'. Run 'js-exec --help' for available modules.");
  };
  globalThis.require.resolve = function(name) { return name; };
})();`,
    "<compat>"
  );
  if (compatResult.error) {
    compatResult.error.dispose();
  } else {
    compatResult.value.dispose();
  }
}
var originalProcessExit = process.exit.bind(process);
process.on("uncaughtException", () => {
  originalProcessExit(1);
});
var defense = null;
async function initializeWithDefense() {
  await getQuickJSModule();
  try {
    stripTypeScriptTypes("const x = 1;");
  } catch {
  }
  await new Promise((r) => setTimeout(r, 0));
  defense = new WorkerDefenseInDepth({
    excludeViolationTypes: [
      // SharedArrayBuffer/Atomics: Used by sync-backend for synchronous
      // filesystem communication between the worker and main thread.
      "shared_array_buffer",
      "atomics",
      // process.stdout/stderr: Emscripten (quickjs-emscripten) routes WASM
      // stdout/stderr through Node.js console which uses process.stdout/stderr.
      // User code runs inside QuickJS with no access to Node.js process.
      "process_stdout",
      "process_stderr"
    ]
  });
}
async function executeCode(input) {
  const qjs = await getQuickJSModule();
  const backend = new SyncBackend(input.sharedBuffer, input.timeoutMs);
  let runtime;
  let context;
  try {
    runtime = qjs.newRuntime();
    runtime.setMemoryLimit(MEMORY_LIMIT);
    let interruptCount = 0;
    runtime.setInterruptHandler(() => {
      interruptCount++;
      return interruptCount > INTERRUPT_CYCLES;
    });
    context = runtime.newContext();
    setupContext(context, backend, input);
    {
      const initResult = context.evalCode(
        `{
          // --- Block dynamic code compilation ---
          // @banned-pattern-ignore: intentional sandbox hardening \u2014 removes eval/Function inside QuickJS guest, not the host
          Object.defineProperty(globalThis, 'eval', {
            value: undefined,
            writable: false,
            configurable: false,
          });
          const BlockedFunction = function () {
            throw new TypeError('Function constructor is not allowed');
          };
          const OrigFunction = Function;
          BlockedFunction.prototype = OrigFunction.prototype;

          // Capture function-type constructors before we patch them
          const AsyncFunction = (async function(){}).constructor;
          const GeneratorFunction = (function*(){}).constructor;
          const AsyncGeneratorFunction = (async function*(){}).constructor;

          // Patch .constructor on all function-type prototypes
          for (const proto of [
            OrigFunction.prototype,
            AsyncFunction.prototype,
            GeneratorFunction.prototype,
            AsyncGeneratorFunction.prototype,
          ]) {
            Object.defineProperty(proto, 'constructor', {
              value: BlockedFunction,
              writable: false,
              configurable: false,
            });
          }
          // @banned-pattern-ignore: intentional sandbox hardening \u2014 replaces Function constructor inside QuickJS guest
          Object.defineProperty(globalThis, 'Function', {
            value: BlockedFunction,
            writable: false,
            configurable: false,
          });

          // --- Freeze all intrinsic prototypes ---
          // Prevents prototype pollution (e.g. Array.prototype.x = ...).
          // Only language intrinsics \u2014 not sandbox-injected objects
          // (process, console, require) which need to stay mutable.
          // Error prototypes are excluded: freezing them makes the inherited
          // "message" property non-writable, which prevents new Error instances
          // from having their own "message" set (JS spec OrdinarySet step 4).
          const g = globalThis;
          const toFreeze = [
            Object, Object.prototype,
            OrigFunction, OrigFunction.prototype,
            AsyncFunction, AsyncFunction.prototype,
            GeneratorFunction, GeneratorFunction.prototype,
            AsyncGeneratorFunction, AsyncGeneratorFunction.prototype,
            Array, Array.prototype,
            String, String.prototype,
            Number, Number.prototype,
            Boolean, Boolean.prototype,
            g.Symbol, g.Symbol && g.Symbol.prototype,
            RegExp, RegExp.prototype,
            Date, Date.prototype,
            Map, Map.prototype,
            Set, Set.prototype,
            WeakMap, WeakMap.prototype,
            WeakSet, WeakSet.prototype,
            g.WeakRef, g.WeakRef && g.WeakRef.prototype,
            Promise, Promise.prototype,
            ArrayBuffer, ArrayBuffer.prototype,
            g.SharedArrayBuffer, g.SharedArrayBuffer && g.SharedArrayBuffer.prototype,
            g.DataView, g.DataView && g.DataView.prototype,
            JSON, Math, g.Reflect, g.Proxy, g.Atomics,
            g.BigInt, g.BigInt && g.BigInt.prototype,
            BlockedFunction,
          ];
          // TypedArrays (guard against missing globals in QuickJS)
          for (const name of [
            'Int8Array','Uint8Array','Uint8ClampedArray',
            'Int16Array','Uint16Array','Int32Array','Uint32Array',
            'Float32Array','Float64Array',
            'BigInt64Array','BigUint64Array',
          ]) {
            if (g[name]) {
              toFreeze.push(g[name], g[name].prototype);
            }
          }
          // %TypedArray% intrinsic (shared base)
          if (g.Uint8Array) {
            const taProto = Object.getPrototypeOf(g.Uint8Array.prototype);
            if (taProto && taProto !== Object.prototype) toFreeze.push(taProto);
            const taCtor = Object.getPrototypeOf(g.Uint8Array);
            if (taCtor && taCtor !== OrigFunction.prototype) toFreeze.push(taCtor);
          }
          // Iterator prototypes
          try {
            const arrIterProto = Object.getPrototypeOf(
              Object.getPrototypeOf([][Symbol.iterator]())
            );
            if (arrIterProto) {
              toFreeze.push(arrIterProto);
              const iterProto = Object.getPrototypeOf(arrIterProto);
              if (iterProto) toFreeze.push(iterProto);
            }
          } catch {}
          try {
            toFreeze.push(Object.getPrototypeOf(new Map()[Symbol.iterator]()));
          } catch {}
          try {
            toFreeze.push(Object.getPrototypeOf(new Set()[Symbol.iterator]()));
          } catch {}
          try {
            toFreeze.push(Object.getPrototypeOf(''[Symbol.iterator]()));
          } catch {}
          try {
            const genObj = (function*(){})();
            toFreeze.push(Object.getPrototypeOf(genObj));
            toFreeze.push(Object.getPrototypeOf(Object.getPrototypeOf(genObj)));
          } catch {}
          try {
            const asyncGenObj = (async function*(){})();
            toFreeze.push(Object.getPrototypeOf(asyncGenObj));
            toFreeze.push(Object.getPrototypeOf(Object.getPrototypeOf(asyncGenObj)));
          } catch {}

          for (const obj of toFreeze) {
            if (obj != null) {
              try { Object.freeze(obj); } catch {}
            }
          }
        }`,
        "<sandbox-init>"
      );
      if (initResult.error) {
        const errVal = context.dump(initResult.error);
        initResult.error.dispose();
        const msg = typeof errVal === "object" && errVal !== null && "message" in errVal ? errVal.message : String(errVal);
        backend.writeStderr(`js-exec: sandbox hardening failed: ${msg}
`);
        backend.exit(1);
        return { success: true };
      }
      initResult.value.dispose();
    }
    if (input.isModule) {
      runtime.setModuleLoader(
        (moduleName) => {
          if (Object.hasOwn(VIRTUAL_MODULES, moduleName)) {
            return VIRTUAL_MODULES[moduleName];
          }
          try {
            const data = backend.readFile(moduleName);
            let source = new TextDecoder().decode(data);
            if (moduleName.endsWith(".ts") || moduleName.endsWith(".mts")) {
              source = stripTypeScriptTypes(source);
            }
            return source;
          } catch (e) {
            return {
              error: new Error(
                `Cannot find module '${moduleName}': ${e.message}`
              )
            };
          }
        },
        (baseModuleName, requestedName) => {
          if (requestedName.startsWith("node:")) {
            requestedName = requestedName.slice(5);
          }
          if (!requestedName.startsWith("./") && !requestedName.startsWith("../") && !requestedName.startsWith("/")) {
            return requestedName;
          }
          const fromFile = baseModuleName === "<eval>" ? void 0 : baseModuleName;
          return resolveModulePath(requestedName, fromFile, input.cwd);
        }
      );
    }
    if (input.bootstrapCode) {
      const bootstrapResult = context.evalCode(
        input.bootstrapCode,
        "bootstrap.js"
      );
      if (bootstrapResult.error) {
        const errorVal = context.dump(bootstrapResult.error);
        bootstrapResult.error.dispose();
        const errorMsg = formatError(errorVal);
        backend.writeStderr(`js-exec: bootstrap error: ${errorMsg}
`);
        backend.exit(1);
        return { success: true };
      }
      bootstrapResult.value.dispose();
    }
    const filename = input.scriptPath || "<eval>";
    let jsCode = input.jsCode;
    if (input.stripTypes) {
      jsCode = stripTypeScriptTypes(jsCode);
    }
    const result = input.isModule ? context.evalCode(jsCode, filename, { type: "module" }) : context.evalCode(jsCode, filename);
    if (result.error) {
      const errorVal = context.dump(result.error);
      result.error.dispose();
      const rawMsg = typeof errorVal === "object" && errorVal !== null && "message" in errorVal ? errorVal.message : String(errorVal);
      if (rawMsg === "__EXIT__") {
        return { success: true };
      }
      const errorMsg = formatError(errorVal);
      try {
        backend.writeStderr(`${errorMsg}
`);
      } catch {
      }
      backend.exit(1);
      return { success: true };
    }
    {
      const pendingResult = runtime.executePendingJobs();
      if ("error" in pendingResult && pendingResult.error) {
        const errorVal = context.dump(pendingResult.error);
        pendingResult.error.dispose();
        const rawPendingMsg = typeof errorVal === "object" && errorVal !== null && "message" in errorVal ? errorVal.message : String(errorVal);
        if (rawPendingMsg !== "__EXIT__") {
          const errorMsg = formatError(errorVal);
          try {
            backend.writeStderr(`${errorMsg}
`);
          } catch {
          }
          backend.exit(1);
          return { success: true };
        }
        return { success: true };
      }
    }
    result.value.dispose();
    backend.exit(0);
    return {
      success: true,
      defenseStats: defense?.getStats()
    };
  } catch (e) {
    const message = e instanceof Error ? e.message : String(e);
    try {
      backend.writeStderr(`js-exec: ${message}
`);
    } catch {
    }
    try {
      backend.exit(1);
    } catch {
      return { success: false, error: message };
    }
    return { success: true };
  } finally {
    context?.dispose();
    runtime?.dispose();
  }
}
var initPromise = initializeWithDefense().catch((e) => {
  parentPort?.postMessage({
    success: false,
    // @banned-pattern-ignore: worker-internal init error; message stays within worker protocol, sanitized by js-exec.ts before user output
    error: e.message,
    defenseStats: defense?.getStats()
  });
});
parentPort?.on("message", async (input) => {
  try {
    await initPromise;
    const result = await executeCode(input);
    result.defenseStats = defense?.getStats();
    result.protocolToken = input.protocolToken;
    parentPort?.postMessage(result);
  } catch (e) {
    parentPort?.postMessage({
      protocolToken: input.protocolToken,
      success: false,
      // @banned-pattern-ignore: worker-internal error; message stays within worker protocol, sanitized by js-exec.ts before user output
      error: e.message,
      defenseStats: defense?.getStats()
    });
  }
});
