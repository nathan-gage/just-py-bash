import {
  __require
} from "./chunk-KH45J4DC.js";

// dist/security/blocked-globals.js
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
    const GeneratorFunction = Object.getPrototypeOf(function* () {
    }).constructor;
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
    const AsyncGeneratorFunction = Object.getPrototypeOf(async function* () {
    }).constructor;
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

// dist/security/defense-in-depth-box.js
var IS_BROWSER = false;
function generateUUID() {
  if (typeof crypto !== "undefined" && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, (c) => {
    const r = Math.random() * 16 | 0;
    const v = c === "x" ? r : r & 3 | 8;
    return v.toString(16);
  });
}
var AsyncLocalStorageClass = null;
if (!IS_BROWSER) {
  try {
    const { AsyncLocalStorage } = __require("node:async_hooks");
    AsyncLocalStorageClass = AsyncLocalStorage;
  } catch {
  }
}
var DEFENSE_IN_DEPTH_NOTICE = "\n\nThis is a defense-in-depth measure and indicates a bug in just-bash. Please report this at security@vercel.com";
var SecurityViolationError = class extends Error {
  violation;
  constructor(message, violation) {
    super(message + DEFENSE_IN_DEPTH_NOTICE);
    this.violation = violation;
    this.name = "SecurityViolationError";
  }
};
var executionContext = !IS_BROWSER && AsyncLocalStorageClass ? new AsyncLocalStorageClass() : null;
var MAX_STORED_VIOLATIONS = 1e3;
function runInContext(captured, fn, ...args) {
  const als = executionContext;
  return als.run(captured, () => fn(...args));
}
var DEFAULT_CONFIG = {
  enabled: true,
  auditMode: false
};
function resolveConfig(config) {
  if (config === void 0) {
    return { ...DEFAULT_CONFIG, enabled: false };
  }
  if (typeof config === "boolean") {
    return { ...DEFAULT_CONFIG, enabled: config };
  }
  return {
    ...DEFAULT_CONFIG,
    ...config
  };
}
var DefenseInDepthBox = class _DefenseInDepthBox {
  static instance = null;
  static importHooksRegistered = false;
  /**
   * Tracks active trusted scopes per executionId.
   * Needed for async machinery that may not preserve `store.trusted` all the
   * way into Node.js internals (e.g. dynamic import resolution hooks).
   */
  static trustedExecutionDepth = /* @__PURE__ */ new Map();
  config;
  refCount = 0;
  patchFailures = [];
  activeExecutionIds = /* @__PURE__ */ new Set();
  /** Reusable DefenseContext objects keyed by executionId (avoids per-.then() allocation). */
  contextCache = /* @__PURE__ */ new Map();
  originalDescriptors = [];
  violations = [];
  activationTime = 0;
  totalActiveTimeMs = 0;
  constructor(config) {
    this.config = config;
  }
  /**
   * Get or create the singleton instance.
   *
   * @param config - Configuration for the defense box.
   * @throws Error if called with a config that conflicts with the existing instance's
   *         security-relevant settings (enabled, auditMode). This prevents a weaker
   *         first caller from silently downgrading protection for later callers.
   */
  static getInstance(config) {
    const resolved = resolveConfig(config);
    if (!_DefenseInDepthBox.instance) {
      _DefenseInDepthBox.instance = new _DefenseInDepthBox(resolved);
    } else {
      const active = _DefenseInDepthBox.instance.config;
      if (resolved.enabled !== active.enabled || resolved.auditMode !== active.auditMode) {
        throw new Error(`DefenseInDepthBox config conflict: requested {enabled: ${resolved.enabled}, auditMode: ${resolved.auditMode}} but singleton already has {enabled: ${active.enabled}, auditMode: ${active.auditMode}}. All Bash instances must use the same defense-in-depth security settings, or call DefenseInDepthBox.resetInstance() between incompatible configurations.`);
      }
    }
    return _DefenseInDepthBox.instance;
  }
  /**
   * Reset the singleton instance. Only use in tests.
   */
  static resetInstance() {
    if (_DefenseInDepthBox.instance) {
      _DefenseInDepthBox.instance.forceDeactivate();
      _DefenseInDepthBox.instance = null;
    }
    _DefenseInDepthBox.trustedExecutionDepth.clear();
  }
  /**
   * Check if the current async context is within sandboxed execution.
   */
  static isInSandboxedContext() {
    if (!executionContext)
      return false;
    return executionContext?.getStore()?.sandboxActive === true;
  }
  /**
   * Get the current execution ID if in a sandboxed context.
   */
  static getCurrentExecutionId() {
    if (!executionContext)
      return void 0;
    return executionContext?.getStore()?.executionId;
  }
  static enterTrustedScope(executionId) {
    const current = _DefenseInDepthBox.trustedExecutionDepth.get(executionId) ?? 0;
    _DefenseInDepthBox.trustedExecutionDepth.set(executionId, current + 1);
  }
  static leaveTrustedScope(executionId) {
    const current = _DefenseInDepthBox.trustedExecutionDepth.get(executionId);
    if (!current)
      return;
    if (current === 1) {
      _DefenseInDepthBox.trustedExecutionDepth.delete(executionId);
      return;
    }
    _DefenseInDepthBox.trustedExecutionDepth.set(executionId, current - 1);
  }
  static isTrustedScopeActive(executionId) {
    if (!executionId)
      return false;
    const depth = _DefenseInDepthBox.trustedExecutionDepth.get(executionId);
    return (depth ?? 0) > 0;
  }
  /**
   * Check if a defense execution ID is still live (its handle is not deactivated).
   */
  isExecutionIdActive(executionId) {
    return this.activeExecutionIds.has(executionId);
  }
  /**
   * Get or create a cached DefenseContext for an executionId.
   * Avoids allocating a new {sandboxActive, executionId} object on every
   * Promise.then / timer call.
   */
  getCachedContext(executionId) {
    let ctx = this.contextCache.get(executionId);
    if (!ctx) {
      ctx = { sandboxActive: true, executionId };
      this.contextCache.set(executionId, ctx);
    }
    return ctx;
  }
  /**
   * Return an active execution ID to bind callback context.
   * When multiple executions are active, this intentionally selects one
   * active ID so callback execution stays fail-closed.
   */
  getPreferredActiveExecutionId() {
    if (this.activeExecutionIds.size === 0)
      return void 0;
    for (const executionId of this.activeExecutionIds) {
      return executionId;
    }
    return void 0;
  }
  /**
   * Bind a callback to the current defense AsyncLocalStorage context.
   *
   * Useful for infrastructure callbacks that may execute later via pre-captured
   * timer references, while still needing executionId/trace continuity.
   *
   * Note: this intentionally does NOT preserve `trusted` mode. Trusted execution
   * is meant to stay tightly scoped to the immediate infrastructure operation.
   */
  static bindCurrentContext(fn) {
    if (!executionContext)
      return fn;
    const box = _DefenseInDepthBox.instance;
    const current = executionContext.getStore();
    const executionId = current?.sandboxActive === true ? current.executionId : box?.getPreferredActiveExecutionId();
    if (!executionId)
      return fn;
    const captured = box?.getCachedContext(executionId) ?? {
      sandboxActive: true,
      executionId
    };
    return ((...args) => {
      const activeBox = _DefenseInDepthBox.instance;
      if (activeBox && !activeBox.isExecutionIdActive(executionId)) {
        activeBox.recordViolation("bound_callback_after_deactivate", "bound callback", "Bound callback blocked after originating execution was deactivated");
        if (!activeBox.config.auditMode) {
          return void 0;
        }
      }
      return runInContext(captured, fn, ...args);
    });
  }
  /**
   * Check if defense-in-depth is enabled and functional.
   * Returns false if AsyncLocalStorage is unavailable or config.enabled is false.
   */
  isEnabled() {
    return this.config.enabled === true && executionContext !== null && !IS_BROWSER;
  }
  /**
   * Update configuration. Only affects future activations.
   */
  updateConfig(config) {
    this.config = { ...this.config, ...config };
  }
  /**
   * Activate the defense box. Returns a handle for scoped execution.
   *
   * Usage:
   * ```
   * const { run, deactivate } = box.activate();
   * try {
   *   await run(async () => {
   *     // Code here is protected
   *   });
   * } finally {
   *   deactivate();
   * }
   * ```
   */
  activate() {
    if (IS_BROWSER || !this.config.enabled || !executionContext) {
      const executionId2 = generateUUID();
      let deactivated2 = false;
      return {
        run: (fn) => {
          if (deactivated2) {
            return Promise.reject(new Error("DefenseInDepthBox handle is deactivated and cannot run new work"));
          }
          return fn();
        },
        deactivate: () => {
          deactivated2 = true;
        },
        executionId: executionId2
      };
    }
    this.refCount++;
    if (this.refCount === 1) {
      this.applyPatches();
      this.activationTime = Date.now();
    }
    const executionId = generateUUID();
    let deactivated = false;
    return {
      run: (fn) => {
        if (deactivated) {
          return Promise.reject(new Error("DefenseInDepthBox handle is deactivated and cannot run new work"));
        }
        this.activeExecutionIds.add(executionId);
        return executionContext.run({ sandboxActive: true, executionId }, fn);
      },
      deactivate: () => {
        if (deactivated)
          return;
        deactivated = true;
        this.activeExecutionIds.delete(executionId);
        this.contextCache.delete(executionId);
        this.refCount--;
        if (this.refCount === 0) {
          this.restorePatches();
          this.totalActiveTimeMs += Date.now() - this.activationTime;
        }
        if (this.refCount < 0) {
          this.refCount = 0;
        }
      },
      executionId
    };
  }
  /**
   * Force deactivation, restoring all patches regardless of ref count.
   * Use for error recovery only.
   */
  forceDeactivate() {
    if (this.refCount > 0) {
      this.restorePatches();
      this.totalActiveTimeMs += Date.now() - this.activationTime;
    }
    this.activeExecutionIds.clear();
    this.contextCache.clear();
    this.refCount = 0;
  }
  /**
   * Check if patches are currently applied.
   */
  isActive() {
    return this.refCount > 0;
  }
  /**
   * Get statistics about the defense box.
   */
  getStats() {
    return {
      violationsBlocked: this.violations.length,
      violations: [...this.violations],
      activeTimeMs: this.totalActiveTimeMs + (this.refCount > 0 ? Date.now() - this.activationTime : 0),
      refCount: this.refCount
    };
  }
  /**
   * Get the list of patch paths that failed during the last activation.
   */
  getPatchFailures() {
    return [...this.patchFailures];
  }
  /**
   * Clear stored violations. Useful for testing.
   */
  clearViolations() {
    this.violations = [];
  }
  /**
   * Get a human-readable path for a target object and property.
   */
  getPathForTarget(target, prop) {
    if (target === globalThis) {
      return `globalThis.${prop}`;
    }
    if (target === process) {
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
   * Run a function as trusted infrastructure code.
   * Blocking is suspended for the current async context only — other
   * concurrent exec() calls remain protected.
   *
   * Uses AsyncLocalStorage to scope the trust, so async operations
   * spawned inside the callback inherit the trusted state.
   */
  static runTrusted(fn) {
    if (!executionContext)
      return fn();
    const current = executionContext.getStore();
    if (!current)
      return fn();
    const { executionId } = current;
    return executionContext.run({ ...current, trusted: true }, () => {
      _DefenseInDepthBox.enterTrustedScope(executionId);
      try {
        const result = fn();
        if (typeof result === "object" && result !== null && "finally" in result && typeof result.finally === "function") {
          return result.finally(() => {
            _DefenseInDepthBox.leaveTrustedScope(executionId);
          });
        }
        _DefenseInDepthBox.leaveTrustedScope(executionId);
        return result;
      } catch (error) {
        _DefenseInDepthBox.leaveTrustedScope(executionId);
        throw error;
      }
    });
  }
  /**
   * Async version of runTrusted.
   */
  static async runTrustedAsync(fn) {
    if (!executionContext)
      return fn();
    const current = executionContext.getStore();
    if (!current)
      return fn();
    const { executionId } = current;
    return executionContext.run({ ...current, trusted: true }, async () => {
      _DefenseInDepthBox.enterTrustedScope(executionId);
      try {
        return await fn();
      } finally {
        _DefenseInDepthBox.leaveTrustedScope(executionId);
      }
    });
  }
  /**
   * Check if current context should be blocked.
   * Returns false in audit mode, browser environment, outside sandboxed context,
   * inside runTrusted(), or when the immediate caller is a Node.js bundled dep.
   */
  shouldBlock() {
    if (IS_BROWSER || this.config.auditMode || !executionContext) {
      return false;
    }
    const store = executionContext?.getStore();
    if (store?.sandboxActive !== true) {
      return false;
    }
    if (store.trusted || _DefenseInDepthBox.isTrustedScopeActive(store.executionId)) {
      return false;
    }
    return true;
  }
  /**
   * Record a violation and optionally invoke the callback.
   */
  recordViolation(type, path, message) {
    const violation = {
      timestamp: Date.now(),
      type,
      message,
      path,
      stack: new Error().stack,
      executionId: executionContext?.getStore()?.executionId
    };
    if (this.violations.length < MAX_STORED_VIOLATIONS) {
      this.violations.push(violation);
    }
    if (this.config.onViolation) {
      try {
        this.config.onViolation(violation);
      } catch (e) {
        console.debug("[DefenseInDepthBox] onViolation callback threw:", e instanceof Error ? e.message : e);
      }
    }
    return violation;
  }
  /**
   * Create a blocking proxy for a function.
   */
  // @banned-pattern-ignore: intentional use of Function type for security proxy
  createBlockingProxy(original, path, violationType) {
    const box = this;
    return new Proxy(original, {
      apply(target, thisArg, args) {
        if (box.shouldBlock()) {
          const message = `${path} is blocked during script execution`;
          const violation = box.recordViolation(violationType, path, message);
          throw new SecurityViolationError(message, violation);
        }
        if (box.config.auditMode && executionContext?.getStore()?.sandboxActive === true) {
          box.recordViolation(violationType, path, `${path} called (audit mode)`);
        }
        return Reflect.apply(target, thisArg, args);
      },
      construct(target, args, newTarget) {
        if (box.shouldBlock()) {
          const message = `${path} constructor is blocked during script execution`;
          const violation = box.recordViolation(violationType, path, message);
          throw new SecurityViolationError(message, violation);
        }
        if (box.config.auditMode && executionContext?.getStore()?.sandboxActive === true) {
          box.recordViolation(violationType, path, `${path} constructor called (audit mode)`);
        }
        return Reflect.construct(target, args, newTarget);
      }
    });
  }
  /**
   * Create a blocking proxy for an object (blocks all property access).
   */
  createBlockingObjectProxy(original, path, violationType, allowedKeys) {
    const box = this;
    return new Proxy(original, {
      get(target, prop, receiver) {
        if (box.shouldBlock()) {
          if (allowedKeys && typeof prop === "string" && allowedKeys.has(prop)) {
            return Reflect.get(target, prop, receiver);
          }
          const fullPath = `${path}.${String(prop)}`;
          const message = `${fullPath} is blocked during script execution`;
          const violation = box.recordViolation(violationType, fullPath, message);
          throw new SecurityViolationError(message, violation);
        }
        if (box.config.auditMode && executionContext?.getStore()?.sandboxActive === true) {
          const fullPath = `${path}.${String(prop)}`;
          box.recordViolation(violationType, fullPath, `${fullPath} accessed (audit mode)`);
        }
        return Reflect.get(target, prop, receiver);
      },
      set(target, prop, value, receiver) {
        if (box.shouldBlock()) {
          const fullPath = `${path}.${String(prop)}`;
          const message = `${fullPath} modification is blocked during script execution`;
          const violation = box.recordViolation(violationType, fullPath, message);
          throw new SecurityViolationError(message, violation);
        }
        return Reflect.set(target, prop, value, receiver);
      },
      // Block enumeration (Object.keys, Object.entries, for...in, etc.)
      ownKeys(target) {
        if (box.shouldBlock()) {
          const message = `${path} enumeration is blocked during script execution`;
          const violation = box.recordViolation(violationType, path, message);
          throw new SecurityViolationError(message, violation);
        }
        return Reflect.ownKeys(target);
      },
      // Block Object.getOwnPropertyDescriptor
      getOwnPropertyDescriptor(target, prop) {
        if (box.shouldBlock()) {
          const fullPath = `${path}.${String(prop)}`;
          const message = `${fullPath} descriptor access is blocked during script execution`;
          const violation = box.recordViolation(violationType, fullPath, message);
          throw new SecurityViolationError(message, violation);
        }
        return Reflect.getOwnPropertyDescriptor(target, prop);
      },
      // Block 'in' operator
      has(target, prop) {
        if (box.shouldBlock()) {
          const fullPath = `${path}.${String(prop)}`;
          const message = `${fullPath} existence check is blocked during script execution`;
          const violation = box.recordViolation(violationType, fullPath, message);
          throw new SecurityViolationError(message, violation);
        }
        return Reflect.has(target, prop);
      },
      // Block delete operator
      deleteProperty(target, prop) {
        if (box.shouldBlock()) {
          const fullPath = `${path}.${String(prop)}`;
          const message = `${fullPath} deletion is blocked during script execution`;
          const violation = box.recordViolation(violationType, fullPath, message);
          throw new SecurityViolationError(message, violation);
        }
        return Reflect.deleteProperty(target, prop);
      },
      // Block Object.setPrototypeOf
      setPrototypeOf(target, proto) {
        if (box.shouldBlock()) {
          const message = `${path} setPrototypeOf is blocked during script execution`;
          const violation = box.recordViolation(violationType, path, message);
          throw new SecurityViolationError(message, violation);
        }
        return Reflect.setPrototypeOf(target, proto);
      },
      // Block Object.defineProperty
      defineProperty(target, prop, descriptor) {
        if (box.shouldBlock()) {
          const fullPath = `${path}.${String(prop)}`;
          const message = `${fullPath} defineProperty is blocked during script execution`;
          const violation = box.recordViolation(violationType, fullPath, message);
          throw new SecurityViolationError(message, violation);
        }
        return Reflect.defineProperty(target, prop, descriptor);
      }
    });
  }
  /**
   * Apply security patches to dangerous globals.
   */
  applyPatches() {
    this.patchFailures = [];
    const blockedGlobals = getBlockedGlobals();
    const skipInMainThread = /* @__PURE__ */ new Set([
      "process_send",
      "process_channel",
      // process.stdout/stderr are used by console.log/debug/error internally.
      // Blocking them in the main thread breaks Node.js console output and
      // the defense layer's own diagnostic logging. They ARE blocked in
      // WorkerDefenseInDepth where the entire worker is sandboxed.
      "process_stdout",
      "process_stderr"
    ]);
    for (const blocked of blockedGlobals) {
      if (skipInMainThread.has(blocked.violationType))
        continue;
      this.applyPatch(blocked);
    }
    this.protectConstructorChain();
    this.protectErrorPrepareStackTrace();
    this.protectPromiseThen();
    this.protectDynamicImport();
    this.protectModuleLoad();
    this.protectModuleResolveFilename();
    this.protectProcessMainModule();
    this.protectProcessExecPath();
    this.lockWellKnownSymbols();
    this.protectProxyRevocable();
    const criticalPaths = ["Function.prototype.constructor", "Module._load"];
    const criticalFailures = this.patchFailures.filter((p) => criticalPaths.includes(p));
    if (criticalFailures.length > 0) {
      this.restorePatches();
      throw new Error(`DefenseInDepthBox: critical patches failed: ${criticalFailures.join(", ")}`);
    }
  }
  /**
   * Protect against .constructor.constructor escape vector.
   *
   * The pattern `{}.constructor.constructor` accesses Function via:
   * - {}.constructor → Object (via Object.prototype.constructor)
   * - Object.constructor → Function (via Function.prototype.constructor)
   *
   * By patching Function.prototype.constructor to return our blocked proxy,
   * we block the escape vector without breaking normal .constructor access.
   */
  protectConstructorChain() {
    this.patchPrototypeConstructor(Function.prototype, "Function.prototype.constructor", "function_constructor");
    try {
      const AsyncFunction = Object.getPrototypeOf(async () => {
      }).constructor;
      if (AsyncFunction && AsyncFunction !== Function) {
        this.patchPrototypeConstructor(AsyncFunction.prototype, "AsyncFunction.prototype.constructor", "async_function_constructor");
      }
    } catch (e) {
      this.patchFailures.push("AsyncFunction.prototype.constructor");
      console.debug("[DefenseInDepthBox] Could not patch AsyncFunction.prototype.constructor:", e instanceof Error ? e.message : e);
    }
    try {
      const GeneratorFunction = Object.getPrototypeOf(function* () {
      }).constructor;
      if (GeneratorFunction && GeneratorFunction !== Function) {
        this.patchPrototypeConstructor(GeneratorFunction.prototype, "GeneratorFunction.prototype.constructor", "generator_function_constructor");
      }
    } catch (e) {
      this.patchFailures.push("GeneratorFunction.prototype.constructor");
      console.debug("[DefenseInDepthBox] Could not patch GeneratorFunction.prototype.constructor:", e instanceof Error ? e.message : e);
    }
    try {
      const AsyncGeneratorFunction = Object.getPrototypeOf(async function* () {
      }).constructor;
      const AsyncFunction = Object.getPrototypeOf(async () => {
      }).constructor;
      if (AsyncGeneratorFunction && AsyncGeneratorFunction !== Function && AsyncGeneratorFunction !== AsyncFunction) {
        this.patchPrototypeConstructor(AsyncGeneratorFunction.prototype, "AsyncGeneratorFunction.prototype.constructor", "async_generator_function_constructor");
      }
    } catch (e) {
      this.patchFailures.push("AsyncGeneratorFunction.prototype.constructor");
      console.debug("[DefenseInDepthBox] Could not patch AsyncGeneratorFunction.prototype.constructor:", e instanceof Error ? e.message : e);
    }
  }
  /**
   * Protect Error.prepareStackTrace from being set in sandbox context.
   *
   * The attack vector is:
   * ```
   * Error.prepareStackTrace = (err, stack) => {
   *   return stack[0].getFunction().constructor; // Gets Function
   * };
   * const F = new Error().stack;
   * F("return process")();
   * ```
   *
   * We only block SETTING, not reading, because V8 reads it internally
   * when creating error stack traces.
   */
  protectErrorPrepareStackTrace() {
    const box = this;
    try {
      const originalDescriptor = Object.getOwnPropertyDescriptor(Error, "prepareStackTrace");
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
          if (box.shouldBlock()) {
            const message = "Error.prepareStackTrace modification is blocked during script execution";
            const violation = box.recordViolation("error_prepare_stack_trace", "Error.prepareStackTrace", message);
            throw new SecurityViolationError(message, violation);
          }
          if (box.config.auditMode && executionContext?.getStore()?.sandboxActive === true) {
            box.recordViolation("error_prepare_stack_trace", "Error.prepareStackTrace", "Error.prepareStackTrace set (audit mode)");
          }
          currentValue = value;
        },
        configurable: true
      });
    } catch (e) {
      this.patchFailures.push("Error.prepareStackTrace");
      console.debug("[DefenseInDepthBox] Could not protect Error.prepareStackTrace:", e instanceof Error ? e.message : e);
    }
  }
  /**
   * Protect Promise.then callback lifetime across deactivate boundaries.
   *
   * Callbacks registered in sandbox context are wrapped with an execution-id
   * liveness check. If they run after the originating handle is deactivated,
   * they are blocked even if global patches have already been restored.
   */
  protectPromiseThen() {
    const box = this;
    try {
      let runGuardedCallback2 = function(...args) {
        return executionContext.run(this.captured, () => {
          if (!this.box.isExecutionIdActive(this.executionId)) {
            const path = "Promise.then";
            const message = "Promise.then callback is blocked after defense deactivation";
            this.box.recordViolation("promise_then_after_deactivate", path, message);
            if (this.box.config.auditMode) {
              return Reflect.apply(this.cb, void 0, args);
            }
            if (this.kind === "fulfilled") {
              return args[0];
            }
            throw args[0];
          }
          return Reflect.apply(this.cb, void 0, args);
        });
      };
      var runGuardedCallback = runGuardedCallback2;
      const originalDescriptor = Object.getOwnPropertyDescriptor(Promise.prototype, "then");
      this.originalDescriptors.push({
        target: Promise.prototype,
        prop: "then",
        descriptor: originalDescriptor
      });
      const originalThen = originalDescriptor?.value;
      if (typeof originalThen !== "function")
        return;
      Object.defineProperty(Promise.prototype, "then", {
        value: function patchedThen(onFulfilled, onRejected) {
          if (!executionContext) {
            return Reflect.apply(originalThen, this, [onFulfilled, onRejected]);
          }
          const store = executionContext.getStore();
          const executionId = store?.sandboxActive === true && store.trusted !== true ? store.executionId : void 0;
          if (!executionId) {
            return Reflect.apply(originalThen, this, [onFulfilled, onRejected]);
          }
          const captured = box.getCachedContext(executionId);
          const wrapCallback = (cb, kind) => {
            if (typeof cb !== "function")
              return cb;
            return runGuardedCallback2.bind({
              box,
              executionId,
              captured,
              cb,
              kind
            });
          };
          return Reflect.apply(originalThen, this, [
            wrapCallback(onFulfilled, "fulfilled"),
            wrapCallback(onRejected, "rejected")
          ]);
        },
        writable: true,
        configurable: true
      });
    } catch (e) {
      this.patchFailures.push("Promise.prototype.then");
      console.debug("[DefenseInDepthBox] Could not protect Promise.prototype.then:", e instanceof Error ? e.message : e);
    }
  }
  /**
   * Patch a prototype's constructor property to block access in sandbox context.
   */
  patchPrototypeConstructor(prototype, path, violationType) {
    const box = this;
    try {
      const originalDescriptor = Object.getOwnPropertyDescriptor(prototype, "constructor");
      this.originalDescriptors.push({
        target: prototype,
        prop: "constructor",
        descriptor: originalDescriptor
      });
      const originalValue = originalDescriptor?.value;
      Object.defineProperty(prototype, "constructor", {
        get() {
          if (box.shouldBlock()) {
            const message = `${path} access is blocked during script execution`;
            const violation = box.recordViolation(violationType, path, message);
            throw new SecurityViolationError(message, violation);
          }
          if (box.config.auditMode && executionContext?.getStore()?.sandboxActive === true) {
            box.recordViolation(violationType, path, `${path} accessed (audit mode)`);
          }
          return originalValue;
        },
        set(value) {
          if (box.shouldBlock()) {
            const message = `${path} modification is blocked during script execution`;
            const violation = box.recordViolation(violationType, path, message);
            throw new SecurityViolationError(message, violation);
          }
          Object.defineProperty(this, "constructor", {
            value,
            writable: true,
            configurable: true
          });
        },
        configurable: true
      });
    } catch (e) {
      this.patchFailures.push(path);
      console.debug(`[DefenseInDepthBox] Could not patch ${path}:`, e instanceof Error ? e.message : e);
    }
  }
  /**
   * Protect process.mainModule from being accessed or set in sandbox context.
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
    if (typeof process === "undefined")
      return;
    const box = this;
    try {
      const originalDescriptor = Object.getOwnPropertyDescriptor(process, "mainModule");
      this.originalDescriptors.push({
        target: process,
        prop: "mainModule",
        descriptor: originalDescriptor
      });
      const currentValue = originalDescriptor?.value;
      if (currentValue !== void 0) {
        Object.defineProperty(process, "mainModule", {
          get() {
            if (box.shouldBlock()) {
              const message = "process.mainModule access is blocked during script execution";
              const violation = box.recordViolation("process_main_module", "process.mainModule", message);
              throw new SecurityViolationError(message, violation);
            }
            if (box.config.auditMode && executionContext?.getStore()?.sandboxActive === true) {
              box.recordViolation("process_main_module", "process.mainModule", "process.mainModule accessed (audit mode)");
            }
            return currentValue;
          },
          set(value) {
            if (box.shouldBlock()) {
              const message = "process.mainModule modification is blocked during script execution";
              const violation = box.recordViolation("process_main_module", "process.mainModule", message);
              throw new SecurityViolationError(message, violation);
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
    } catch (e) {
      this.patchFailures.push("process.mainModule");
      console.debug("[DefenseInDepthBox] Could not protect process.mainModule:", e instanceof Error ? e.message : e);
    }
  }
  /**
   * Protect process.execPath from being read or set in sandbox context.
   *
   * process.execPath is a string primitive (not an object), so it cannot be
   * proxied via the normal blocked globals mechanism. We use Object.defineProperty
   * with getter/setter (same pattern as protectProcessMainModule).
   */
  protectProcessExecPath() {
    if (typeof process === "undefined")
      return;
    const box = this;
    try {
      const originalDescriptor = Object.getOwnPropertyDescriptor(process, "execPath");
      this.originalDescriptors.push({
        target: process,
        prop: "execPath",
        descriptor: originalDescriptor
      });
      const currentValue = originalDescriptor?.value ?? process.execPath;
      Object.defineProperty(process, "execPath", {
        get() {
          if (box.shouldBlock()) {
            const message = "process.execPath access is blocked during script execution";
            const violation = box.recordViolation("process_exec_path", "process.execPath", message);
            throw new SecurityViolationError(message, violation);
          }
          if (box.config.auditMode && executionContext?.getStore()?.sandboxActive === true) {
            box.recordViolation("process_exec_path", "process.execPath", "process.execPath accessed (audit mode)");
          }
          return currentValue;
        },
        set(value) {
          if (box.shouldBlock()) {
            const message = "process.execPath modification is blocked during script execution";
            const violation = box.recordViolation("process_exec_path", "process.execPath", message);
            throw new SecurityViolationError(message, violation);
          }
          Object.defineProperty(process, "execPath", {
            value,
            writable: true,
            configurable: true
          });
        },
        configurable: true
      });
    } catch (e) {
      this.patchFailures.push("process.execPath");
      console.debug("[DefenseInDepthBox] Could not protect process.execPath:", e instanceof Error ? e.message : e);
    }
  }
  /**
   * Lock well-known Symbol properties on built-in constructors/prototypes.
   *
   * Instead of freezing entire prototypes (which breaks Node.js internals),
   * we make specific Symbol properties non-configurable so they can't be
   * replaced. This prevents:
   * - Symbol.species hijacking (controls .map/.filter/.slice return types)
   * - Symbol.iterator hijacking (controls for...of and spread)
   * - Symbol.toPrimitive hijacking (controls type coercion)
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
      const stackDesc = Object.getOwnPropertyDescriptor(Error, "stackTraceLimit");
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
   * checks the sandbox context before delegating to the original.
   */
  protectProxyRevocable() {
    const box = this;
    try {
      const originalRevocable = Proxy.revocable;
      if (typeof originalRevocable !== "function")
        return;
      const descriptor = Object.getOwnPropertyDescriptor(Proxy, "revocable");
      this.originalDescriptors.push({
        target: Proxy,
        prop: "revocable",
        descriptor
      });
      Object.defineProperty(Proxy, "revocable", {
        value: function revocable(target, handler) {
          if (box.shouldBlock()) {
            const message = "Proxy.revocable is blocked during script execution";
            const violation = box.recordViolation("proxy", "Proxy.revocable", message);
            throw new SecurityViolationError(message, violation);
          }
          if (box.config.auditMode && executionContext?.getStore()?.sandboxActive === true) {
            box.recordViolation("proxy", "Proxy.revocable", "Proxy.revocable called (audit mode)");
          }
          return originalRevocable(target, handler);
        },
        writable: false,
        configurable: true
        // Must be configurable for restoration
      });
    } catch (e) {
      this.patchFailures.push("Proxy.revocable");
      console.debug("[DefenseInDepthBox] Could not protect Proxy.revocable:", e instanceof Error ? e.message : e);
    }
  }
  /**
   * Block dynamic import() escape vectors via ESM loader hooks.
   *
   * Uses Node.js module.registerHooks() (23.5+, synchronous) or
   * module.register() (20.6+, async hooks in separate thread) to install
   * ESM loader hooks that reject dangerous specifiers.
   *
   * registerHooks() runs in-thread and can read AsyncLocalStorage. We use it
   * to block Node.js builtin specifiers (node:* and bare builtins) only in
   * untrusted sandbox context while still allowing trusted infrastructure
   * imports (runTrusted/runTrustedAsync).
   *
   * register() hooks run in a separate loader thread and cannot read
   * AsyncLocalStorage. In that fallback mode, only data:/blob: blocking is
   * enforced here.
   *
   * This is process-wide and permanent (hooks cannot be unregistered).
   * Only applied once per process regardless of how many DefenseInDepthBox
   * instances are created.
   *
   * Combined with Module._resolveFilename blocking (file-based specifiers),
   * this closes the import() escape vector except for specifiers that bypass
   * both the ESM loader and CJS resolution (none known).
   */
  protectDynamicImport() {
    if (IS_BROWSER || _DefenseInDepthBox.importHooksRegistered)
      return;
    try {
      const box = this;
      const mod = __require("node:module");
      const builtinModules = /* @__PURE__ */ new Set();
      for (const rawBuiltin of mod.builtinModules ?? []) {
        const normalized = rawBuiltin.startsWith("node:") ? rawBuiltin.slice("node:".length) : rawBuiltin;
        builtinModules.add(normalized);
        const slashIndex = normalized.indexOf("/");
        if (slashIndex > 0) {
          builtinModules.add(normalized.slice(0, slashIndex));
        }
      }
      const isNodeBuiltinSpecifier = (specifier) => {
        if (specifier.startsWith("./") || specifier.startsWith("../") || specifier.startsWith("/") || specifier.startsWith("file:") || specifier.startsWith("data:") || specifier.startsWith("blob:") || specifier.startsWith("http:") || specifier.startsWith("https:")) {
          return false;
        }
        const normalized = specifier.startsWith("node:") ? specifier.slice("node:".length) : specifier;
        if (!normalized)
          return false;
        if (typeof mod.isBuiltin === "function" && mod.isBuiltin(normalized)) {
          return true;
        }
        if (builtinModules.has(normalized)) {
          return true;
        }
        const slashIndex = normalized.indexOf("/");
        return slashIndex > 0 && builtinModules.has(normalized.slice(0, slashIndex));
      };
      const shouldRecordAuditViolation = () => {
        const store = executionContext?.getStore();
        return box.config.auditMode === true && store?.sandboxActive === true && store.trusted !== true && !_DefenseInDepthBox.isTrustedScopeActive(store.executionId);
      };
      if (typeof mod.registerHooks === "function") {
        mod.registerHooks({
          resolve(specifier, context, nextResolve) {
            if (specifier.startsWith("data:") || specifier.startsWith("blob:")) {
              throw new Error(`dynamic import of ${specifier.startsWith("data:") ? "data:" : "blob:"} URLs is blocked by defense-in-depth`);
            }
            if (isNodeBuiltinSpecifier(specifier)) {
              const path = `import(${specifier})`;
              const message = `dynamic import of Node.js builtin '${specifier}' is blocked during script execution`;
              if (box.shouldBlock()) {
                const violation = box.recordViolation("dynamic_import_builtin", path, message);
                throw new SecurityViolationError(message, violation);
              }
              if (shouldRecordAuditViolation()) {
                box.recordViolation("dynamic_import_builtin", path, `dynamic import of Node.js builtin '${specifier}' called (audit mode)`);
              }
            }
            return nextResolve(specifier, context);
          }
        });
        _DefenseInDepthBox.importHooksRegistered = true;
        return;
      }
      if (typeof mod.register === "function") {
        const hookCode = [
          "export async function resolve(specifier, context, nextResolve) {",
          '  if (specifier.startsWith("data:") || specifier.startsWith("blob:")) {',
          '    throw new Error("dynamic import of " + (specifier.startsWith("data:") ? "data:" : "blob:") + " URLs is blocked by defense-in-depth");',
          "  }",
          "  return nextResolve(specifier, context);",
          "}"
        ].join("\n");
        mod.register(`data:text/javascript,${encodeURIComponent(hookCode)}`);
        _DefenseInDepthBox.importHooksRegistered = true;
      }
    } catch (e) {
      console.debug("[DefenseInDepthBox] Could not register import() hooks:", e instanceof Error ? e.message : e);
    }
  }
  /**
   * Protect Module._load from being called in sandbox context.
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
    if (IS_BROWSER)
      return;
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
      const proxy = this.createBlockingProxy(original, path, "module_load");
      Object.defineProperty(ModuleClass, "_load", {
        value: proxy,
        writable: true,
        configurable: true
      });
    } catch (e) {
      this.patchFailures.push("Module._load");
      console.debug("[DefenseInDepthBox] Could not protect Module._load:", e instanceof Error ? e.message : e);
    }
  }
  /**
   * Protect Module._resolveFilename from being called in sandbox context.
   *
   * Module._resolveFilename is called for both require() and import() resolution.
   * Blocking it catches file-based import() specifiers:
   *   import('./malicious.js')  // _resolveFilename is called to resolve the path
   *
   * data: and blob: URLs are handled separately by protectDynamicImport()
   * via ESM loader hooks.
   */
  protectModuleResolveFilename() {
    if (IS_BROWSER)
      return;
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
      const descriptor = Object.getOwnPropertyDescriptor(ModuleClass, "_resolveFilename");
      this.originalDescriptors.push({
        target: ModuleClass,
        prop: "_resolveFilename",
        descriptor
      });
      const path = "Module._resolveFilename";
      const proxy = this.createBlockingProxy(original, path, "module_resolve_filename");
      Object.defineProperty(ModuleClass, "_resolveFilename", {
        value: proxy,
        writable: true,
        configurable: true
      });
    } catch (e) {
      this.patchFailures.push("Module._resolveFilename");
      console.debug("[DefenseInDepthBox] Could not protect Module._resolveFilename:", e instanceof Error ? e.message : e);
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
        const proxy = typeof original === "function" ? this.createBlockingProxy(original, path, violationType) : this.createBlockingObjectProxy(original, path, violationType, blocked.allowedKeys);
        Object.defineProperty(target, prop, {
          value: proxy,
          writable: true,
          // Keep writable so external code (vitest, etc.) can reassign if needed
          configurable: true
          // Must be configurable for restoration
        });
      }
    } catch (e) {
      const path = this.getPathForTarget(target, prop);
      this.patchFailures.push(path);
      console.debug(`[DefenseInDepthBox] Could not patch ${path}:`, e instanceof Error ? e.message : e);
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
      } catch (e) {
        const path = this.getPathForTarget(target, prop);
        console.debug(`[DefenseInDepthBox] Could not restore ${path}:`, e instanceof Error ? e.message : e);
      }
    }
    this.originalDescriptors = [];
  }
};

export {
  SecurityViolationError,
  DefenseInDepthBox
};
