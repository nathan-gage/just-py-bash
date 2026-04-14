import { readFile } from 'node:fs/promises';
import { dirname, join } from 'node:path';
import { createInterface } from 'node:readline';
import { pathToFileURL } from 'node:url';

const BYTE_TAG = '__just_bash_bytes__';

let nextInvocationId = 1;
const pendingLazyFiles = new Map();
const pendingFetches = new Map();

function respond(id, ok, payload) {
  const body = ok
    ? { id, ok: true, result: payload }
    : { id, ok: false, error: payload };
  process.stdout.write(`${JSON.stringify(body)}\n`);
}

function emitLazyFileInvocation(providerName) {
  process.stdout.write(
    `${JSON.stringify({
      type: 'lazy_file',
      invocationId: nextInvocationId,
      providerName,
    })}\n`,
  );
  return nextInvocationId++;
}

function emitFetchInvocation(url, options) {
  process.stdout.write(
    `${JSON.stringify({
      type: 'fetch',
      invocationId: nextInvocationId,
      url,
      options,
    })}\n`,
  );
  return nextInvocationId++;
}

function emitLoggerEvent(level, message, data) {
  process.stdout.write(
    `${JSON.stringify({
      type: 'logger',
      level,
      message,
      data: data ?? null,
    })}\n`,
  );
}

function emitTraceEvent(event) {
  process.stdout.write(`${JSON.stringify({ type: 'trace', event })}\n`);
}

function emitCoverageEvent(feature) {
  process.stdout.write(`${JSON.stringify({ type: 'coverage', feature })}\n`);
}

function emitDefenseViolationEvent(violation) {
  process.stdout.write(`${JSON.stringify({ type: 'defense_violation', violation })}\n`);
}

function errorPayload(error) {
  return {
    type: error?.name ?? 'Error',
    message: error?.message ?? String(error),
    stack: error?.stack ?? null,
  };
}

function wrapSuccess(value) {
  return { kind: 'ok', value };
}

function normalizeError(error) {
  return {
    kind: 'error',
    type: error?.name ?? 'Error',
    message: error?.message ?? String(error),
  };
}

function isBytes(value) {
  return Boolean(
    value &&
      typeof value === 'object' &&
      !Array.isArray(value) &&
      Object.prototype.hasOwnProperty.call(value, BYTE_TAG),
  );
}

function decodeBytes(value) {
  return Buffer.from(value[BYTE_TAG], 'base64');
}

function encodeBytes(value) {
  return { [BYTE_TAG]: Buffer.from(value).toString('base64') };
}

function decodeFileContent(value) {
  if (typeof value === 'string') {
    return value;
  }
  if (isBytes(value)) {
    return decodeBytes(value);
  }
  throw new Error('Unsupported file content payload');
}

function decodeInitialFileValue(value) {
  if (
    value &&
    typeof value === 'object' &&
    !Array.isArray(value) &&
    typeof value.kind === 'string'
  ) {
    switch (value.kind) {
      case 'file_init': {
        const decoded = {
          content: decodeFileContent(value.content),
        };
        if (value.mode !== undefined) decoded.mode = value.mode;
        if (value.mtimeMs !== undefined) decoded.mtime = new Date(value.mtimeMs);
        return decoded;
      }
      case 'lazy_static':
        return async () => decodeFileContent(value.content);
      case 'lazy_callback':
        return async () => {
          const invocationId = emitLazyFileInvocation(value.providerName);
          return await new Promise((resolve, reject) => {
            pendingLazyFiles.set(invocationId, { resolve, reject });
          });
        };
      default:
        throw new Error(`Unsupported initial file payload kind: ${String(value.kind)}`);
    }
  }

  return decodeFileContent(value);
}

function decodeFiles(files) {
  if (!files) {
    return undefined;
  }

  const decoded = {};
  for (const [path, value] of Object.entries(files)) {
    decoded[path] = decodeInitialFileValue(value);
  }
  return decoded;
}

function normalizeFetchOptions(options) {
  const normalized = {};
  if (options?.method !== undefined) normalized.method = options.method;
  if (options?.headers !== undefined) {
    normalized.headers =
      options.headers instanceof Headers
        ? Object.fromEntries(options.headers.entries())
        : options.headers;
  }
  if (options?.body !== undefined) normalized.body = options.body;
  if (options?.followRedirects !== undefined) {
    normalized.followRedirects = options.followRedirects;
  }
  if (options?.timeoutMs !== undefined) normalized.timeoutMs = options.timeoutMs;
  return normalized;
}

function normalizeTraceEvent(event) {
  const normalized = {
    category: typeof event?.category === 'string' ? event.category : '',
    name: typeof event?.name === 'string' ? event.name : '',
    durationMs: Number(event?.durationMs ?? 0),
  };
  if (
    event?.details &&
    typeof event.details === 'object' &&
    !Array.isArray(event.details)
  ) {
    normalized.details = event.details;
  }
  return normalized;
}

function normalizeSecurityViolation(violation) {
  const normalized = {
    timestamp: Number(violation?.timestamp ?? 0),
    type: typeof violation?.type === 'string' ? violation.type : '',
    message: typeof violation?.message === 'string' ? violation.message : '',
    path: typeof violation?.path === 'string' ? violation.path : '',
  };
  if (typeof violation?.stack === 'string') normalized.stack = violation.stack;
  if (typeof violation?.executionId === 'string') {
    normalized.executionId = violation.executionId;
  }
  return normalized;
}

function decodeDefenseInDepth(spec) {
  if (typeof spec === 'boolean') {
    return spec;
  }
  if (!spec || typeof spec !== 'object' || Array.isArray(spec)) {
    throw new Error('Unsupported defenseInDepth payload');
  }

  const decoded = {};
  if (spec.enabled !== undefined) decoded.enabled = spec.enabled;
  if (spec.auditMode !== undefined) decoded.auditMode = spec.auditMode;
  if (Array.isArray(spec.excludeViolationTypes)) {
    decoded.excludeViolationTypes = spec.excludeViolationTypes;
  }
  if (spec.onViolationEnabled) {
    decoded.onViolation = (violation) => {
      emitDefenseViolationEvent(normalizeSecurityViolation(violation));
    };
  }
  return decoded;
}

async function runDefenseViolationProbe(mod, packageJsonPath, kind) {
  if (kind === 'main') {
    const violations = [];
    const box = mod.DefenseInDepthBox.getInstance({
      enabled: true,
      auditMode: true,
      onViolation: (violation) => {
        violations.push(violation);
        emitDefenseViolationEvent(normalizeSecurityViolation(violation));
      },
    });
    const handle = box.activate();
    try {
      const returnValue = await handle.run(async () => {
        const fn = new Function('return 42');
        return fn();
      });
      return { kind, returnValue, violationCount: violations.length };
    } finally {
      handle.deactivate();
      mod.DefenseInDepthBox.resetInstance();
    }
  }

  if (kind === 'worker') {
    const securityModuleUrl = pathToFileURL(
      join(dirname(packageJsonPath), 'dist', 'security', 'index.js'),
    ).href;
    const securityModule = await import(securityModuleUrl);
    const violations = [];
    const defense = new securityModule.WorkerDefenseInDepth({
      auditMode: true,
      excludeViolationTypes: ['process_stdout', 'process_stderr'],
      onViolation: (violation) => {
        violations.push(violation);
        emitDefenseViolationEvent(normalizeSecurityViolation(violation));
      },
    });
    try {
      const fn = new Function('return 42');
      return { kind, returnValue: fn(), violationCount: violations.length };
    } finally {
      defense.deactivate();
    }
  }

  throw new Error(`Unknown defense probe kind: ${String(kind)}`);
}

function decodeFs(mod, spec) {
  if (!spec || typeof spec !== 'object' || Array.isArray(spec)) {
    throw new Error('Unsupported fs config payload');
  }

  switch (spec.kind) {
    case 'in_memory':
      return new mod.InMemoryFs(decodeFiles(spec.files));
    case 'overlay':
      return new mod.OverlayFs({
        root: spec.root,
        mountPoint: spec.mountPoint,
        readOnly: spec.readOnly,
        maxFileReadSize: spec.maxFileReadSize,
        allowSymlinks: spec.allowSymlinks,
      });
    case 'read_write':
      return new mod.ReadWriteFs({
        root: spec.root,
        maxFileReadSize: spec.maxFileReadSize,
        allowSymlinks: spec.allowSymlinks,
      });
    case 'mountable':
      return new mod.MountableFs({
        base: spec.base ? decodeFs(mod, spec.base) : undefined,
        mounts: Array.isArray(spec.mounts)
          ? spec.mounts.map((mount) => ({
              mountPoint: mount.mountPoint,
              filesystem: decodeFs(mod, mount.filesystem),
            }))
          : undefined,
      });
    default:
      throw new Error(`Unknown fs config kind: ${String(spec.kind)}`);
  }
}

function decodeInitOptions(mod, options) {
  const decoded = {};
  if (options.files !== undefined) decoded.files = decodeFiles(options.files);
  if (options.env !== undefined) decoded.env = options.env;
  if (options.cwd !== undefined) decoded.cwd = options.cwd;
  if (options.fs !== undefined) decoded.fs = decodeFs(mod, options.fs);
  if (options.commands !== undefined) decoded.commands = options.commands;
  if (options.python !== undefined) decoded.python = options.python;
  if (options.javascript !== undefined) decoded.javascript = options.javascript;
  if (options.executionLimits !== undefined) {
    decoded.executionLimits = options.executionLimits;
  }
  if (options.fetchEnabled) {
    decoded.fetch = async (url, fetchOptions) => {
      const invocationId = emitFetchInvocation(url, normalizeFetchOptions(fetchOptions));
      return await new Promise((resolve, reject) => {
        pendingFetches.set(invocationId, { resolve, reject });
      });
    };
  }
  if (options.loggerEnabled) {
    decoded.logger = {
      info(message, data) {
        emitLoggerEvent('info', message, data);
      },
      debug(message, data) {
        emitLoggerEvent('debug', message, data);
      },
    };
  }
  if (options.traceEnabled) {
    decoded.trace = (event) => {
      emitTraceEvent(normalizeTraceEvent(event));
    };
  }
  if (options.coverageEnabled) {
    decoded.coverage = {
      hit(feature) {
        emitCoverageEvent(feature);
      },
    };
  }
  if (options.defenseInDepth !== undefined) {
    decoded.defenseInDepth = decodeDefenseInDepth(options.defenseInDepth);
  }
  if (options.network !== undefined) decoded.network = options.network;
  if (options.processInfo !== undefined) decoded.processInfo = options.processInfo;
  return decoded;
}

function decodeExecOptions(options) {
  const decoded = {};
  if (options.env !== undefined) decoded.env = options.env;
  if (options.cwd !== undefined) decoded.cwd = options.cwd;
  if (options.stdin !== undefined) decoded.stdin = options.stdin;
  if (options.args !== undefined) decoded.args = options.args;
  if (options.replaceEnv !== undefined) decoded.replaceEnv = options.replaceEnv;
  if (options.rawScript !== undefined) decoded.rawScript = options.rawScript;
  if (options.timeoutMs !== undefined) decoded.timeoutMs = options.timeoutMs;
  return decoded;
}

function normalizeFsStat(stat) {
  return {
    isFile: Boolean(stat?.isFile),
    isDirectory: Boolean(stat?.isDirectory),
    isSymbolicLink: Boolean(stat?.isSymbolicLink),
    mode: Number.isInteger(stat?.mode) ? stat.mode : 0,
    size: Number.isInteger(stat?.size) ? stat.size : 0,
    mtimeMs:
      stat?.mtime instanceof Date
        ? stat.mtime.getTime()
        : Number.isFinite(stat?.mtime?.valueOf?.())
          ? Number(stat.mtime.valueOf())
          : 0,
  };
}

function normalizeDirentEntry(entry) {
  return {
    name: typeof entry?.name === 'string' ? entry.name : '',
    isFile: Boolean(entry?.isFile),
    isDirectory: Boolean(entry?.isDirectory),
    isSymbolicLink: Boolean(entry?.isSymbolicLink),
  };
}

async function execWithTimeout(bash, script, options) {
  const timeoutMs = options?.timeoutMs;
  const execOptions = { ...options };
  delete execOptions.timeoutMs;

  if (timeoutMs === undefined) {
    return await bash.exec(script, execOptions);
  }

  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    return await bash.exec(script, {
      ...execOptions,
      signal: controller.signal,
    });
  } finally {
    clearTimeout(timer);
  }
}

function resolveSessionPath(bash, path) {
  return bash.fs.resolvePath(bash.getCwd(), path);
}

function handleLazyFileComplete(message) {
  const pending = pendingLazyFiles.get(message.invocationId);
  if (!pending) {
    throw new Error(`Unknown lazy file invocation: ${message.invocationId}`);
  }

  pendingLazyFiles.delete(message.invocationId);
  if (message.error) {
    const error = new Error(message.error.message ?? 'Lazy file provider failed');
    if (typeof message.error.type === 'string' && message.error.type) {
      error.name = message.error.type;
    }
    pending.reject(error);
    return;
  }

  pending.resolve(decodeFileContent(message.content));
}

function handleFetchComplete(message) {
  const pending = pendingFetches.get(message.invocationId);
  if (!pending) {
    throw new Error(`Unknown fetch invocation: ${message.invocationId}`);
  }

  pendingFetches.delete(message.invocationId);
  if (message.error) {
    const error = new Error(message.error.message ?? 'Fetch callback failed');
    if (typeof message.error.type === 'string' && message.error.type) {
      error.name = message.error.type;
    }
    pending.reject(error);
    return;
  }

  pending.resolve(message.result ?? {});
}

async function runScenario(message) {
  const mod = await import(pathToFileURL(message.jsEntry).href);
  const bash = new mod.Bash(decodeInitOptions(mod, message.initOptions ?? {}));
  const packageJson = JSON.parse(await readFile(message.packageJson, 'utf8'));

  const results = [];
  for (const operation of message.operations ?? []) {
    try {
      switch (operation.op) {
        case 'exec':
          results.push(
            wrapSuccess(
              await execWithTimeout(
                bash,
                operation.script,
                decodeExecOptions(operation.options ?? {}),
              ),
            ),
          );
          break;
        case 'read_text':
          results.push(wrapSuccess(await bash.readFile(operation.path)));
          break;
        case 'read_bytes':
          results.push(
            wrapSuccess(
              encodeBytes(
                await bash.fs.readFileBuffer(resolveSessionPath(bash, operation.path)),
              ),
            ),
          );
          break;
        case 'write_text':
          await bash.writeFile(operation.path, operation.content);
          results.push(wrapSuccess(null));
          break;
        case 'write_bytes':
          await bash.writeFile(operation.path, decodeBytes(operation.content));
          results.push(wrapSuccess(null));
          break;
        case 'append_text':
          await bash.fs.appendFile(resolveSessionPath(bash, operation.path), operation.content);
          results.push(wrapSuccess(null));
          break;
        case 'append_bytes':
          await bash.fs.appendFile(
            resolveSessionPath(bash, operation.path),
            decodeBytes(operation.content),
          );
          results.push(wrapSuccess(null));
          break;
        case 'exists':
          results.push(wrapSuccess(await bash.fs.exists(resolveSessionPath(bash, operation.path))));
          break;
        case 'stat':
          results.push(
            wrapSuccess(normalizeFsStat(await bash.fs.stat(resolveSessionPath(bash, operation.path)))),
          );
          break;
        case 'lstat':
          results.push(
            wrapSuccess(normalizeFsStat(await bash.fs.lstat(resolveSessionPath(bash, operation.path)))),
          );
          break;
        case 'mkdir':
          await bash.fs.mkdir(resolveSessionPath(bash, operation.path), {
            recursive: operation.recursive,
          });
          results.push(wrapSuccess(null));
          break;
        case 'readdir':
          results.push(wrapSuccess(await bash.fs.readdir(resolveSessionPath(bash, operation.path))));
          break;
        case 'readdir_with_file_types': {
          if (typeof bash.fs.readdirWithFileTypes !== 'function') {
            throw new Error('readdirWithFileTypes is not available for this session filesystem');
          }
          results.push(
            wrapSuccess(
              (await bash.fs.readdirWithFileTypes(resolveSessionPath(bash, operation.path))).map(
                normalizeDirentEntry,
              ),
            ),
          );
          break;
        }
        case 'rm':
          await bash.fs.rm(resolveSessionPath(bash, operation.path), {
            recursive: operation.recursive,
            force: operation.force,
          });
          results.push(wrapSuccess(null));
          break;
        case 'cp':
          await bash.fs.cp(
            resolveSessionPath(bash, operation.src),
            resolveSessionPath(bash, operation.dest),
            { recursive: operation.recursive },
          );
          results.push(wrapSuccess(null));
          break;
        case 'mv':
          await bash.fs.mv(
            resolveSessionPath(bash, operation.src),
            resolveSessionPath(bash, operation.dest),
          );
          results.push(wrapSuccess(null));
          break;
        case 'resolve_path': {
          const base =
            typeof operation.base === 'string'
              ? resolveSessionPath(bash, operation.base)
              : bash.getCwd();
          results.push(wrapSuccess(bash.fs.resolvePath(base, operation.path)));
          break;
        }
        case 'get_all_paths':
          results.push(wrapSuccess(bash.fs.getAllPaths()));
          break;
        case 'chmod':
          await bash.fs.chmod(resolveSessionPath(bash, operation.path), operation.mode);
          results.push(wrapSuccess(null));
          break;
        case 'symlink':
          await bash.fs.symlink(operation.target, resolveSessionPath(bash, operation.linkPath));
          results.push(wrapSuccess(null));
          break;
        case 'link':
          await bash.fs.link(
            resolveSessionPath(bash, operation.existingPath),
            resolveSessionPath(bash, operation.newPath),
          );
          results.push(wrapSuccess(null));
          break;
        case 'readlink':
          results.push(wrapSuccess(await bash.fs.readlink(resolveSessionPath(bash, operation.path))));
          break;
        case 'realpath':
          results.push(wrapSuccess(await bash.fs.realpath(resolveSessionPath(bash, operation.path))));
          break;
        case 'utimes':
          await bash.fs.utimes(
            resolveSessionPath(bash, operation.path),
            new Date(operation.atimeMs),
            new Date(operation.mtimeMs),
          );
          results.push(wrapSuccess(null));
          break;
        case 'get_env':
          results.push(wrapSuccess(bash.getEnv()));
          break;
        case 'get_cwd':
          results.push(wrapSuccess(bash.getCwd()));
          break;
        case 'probe_defense_violation':
          results.push(
            wrapSuccess(await runDefenseViolationProbe(mod, message.packageJson, operation.kind)),
          );
          break;
        default:
          throw new Error(`Unknown operation: ${operation.op}`);
      }
    } catch (error) {
      results.push(normalizeError(error));
    }
  }

  return {
    backendVersion: packageJson.version ?? null,
    results,
  };
}

const rl = createInterface({
  input: process.stdin,
  crlfDelay: Infinity,
});

rl.on('line', (line) => {
  let message;

  try {
    message = JSON.parse(line);
  } catch (error) {
    process.stderr.write(`Protocol error: ${String(error)}\n`);
    process.exitCode = 1;
    return;
  }

  if (message.op === 'lazy_file_complete') {
    Promise.resolve()
      .then(() => handleLazyFileComplete(message))
      .catch((error) => {
        process.stderr.write(`Lazy file completion error: ${String(error)}\n`);
        process.exitCode = 1;
      });
    return;
  }

  if (message.op === 'fetch_complete') {
    Promise.resolve()
      .then(() => handleFetchComplete(message))
      .catch((error) => {
        process.stderr.write(`Fetch completion error: ${String(error)}\n`);
        process.exitCode = 1;
      });
    return;
  }

  if (message.op !== 'run') {
    respond(message.id ?? 0, false, {
      type: 'Error',
      message: `Unknown operation: ${String(message.op)}`,
      stack: null,
    });
    return;
  }

  runScenario(message)
    .then((result) => {
      respond(message.id, true, result);
    })
    .catch((error) => {
      respond(message.id, false, errorPayload(error));
    });
});
