WORKER_SOURCE = """
import { readFile } from 'node:fs/promises';
import { dirname, join } from 'node:path';
import { createInterface } from 'node:readline';
import { pathToFileURL } from 'node:url';

const BYTE_TAG = '__just_bash_bytes__';

let BashClass = null;
let backendModule = null;
let bash = null;
let backendVersion = null;
let packageJsonPath = null;
let nextInvocationId = 1;
let nextSandboxId = 1;
let nextSandboxCommandId = 1;
const pendingCustomCommands = new Map();
const pendingLazyFiles = new Map();
const pendingFetches = new Map();
const sandboxes = new Map();
const sandboxCommands = new Map();

function respond(id, ok, payload) {
  const body = ok
    ? { id, ok: true, result: payload }
    : { id, ok: false, error: payload };
  process.stdout.write(`${JSON.stringify(body)}\n`);
}

function emitCustomCommandInvocation(name, args, ctx) {
  process.stdout.write(
    `${JSON.stringify({
      type: 'custom_command',
      invocationId: nextInvocationId,
      name,
      args,
      context: {
        cwd: ctx.cwd,
        env: Object.fromEntries(ctx.env),
        stdin: ctx.stdin,
      },
    })}\n`,
  );
  return nextInvocationId++;
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
  process.stdout.write(
    `${JSON.stringify({
      type: 'trace',
      event,
    })}\n`,
  );
}

function emitCoverageEvent(feature) {
  process.stdout.write(
    `${JSON.stringify({
      type: 'coverage',
      feature,
    })}\n`,
  );
}

function emitDefenseViolationEvent(violation) {
  process.stdout.write(
    `${JSON.stringify({
      type: 'defense_violation',
      violation,
    })}\n`,
  );
}

function errorPayload(error) {
  return {
    type: error?.name ?? 'Error',
    message: error?.message ?? String(error),
    stack: error?.stack ?? null,
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

function createPythonCustomCommand(name) {
  return {
    name,
    trusted: true,
    async execute(args, ctx) {
      const invocationId = emitCustomCommandInvocation(name, args, ctx);
      return await new Promise((resolve) => {
        pendingCustomCommands.set(invocationId, { ctx, resolve });
      });
    },
  };
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

async function runDefenseViolationProbe(kind) {
  if (!backendModule) {
    throw new Error('Backend module is not loaded');
  }

  if (kind === 'main') {
    const violations = [];
    const box = backendModule.DefenseInDepthBox.getInstance({
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
      backendModule.DefenseInDepthBox.resetInstance();
    }
  }

  if (kind === 'worker') {
    if (!packageJsonPath) {
      throw new Error('package.json path is not configured');
    }
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

function decodeFs(spec) {
  if (!spec || typeof spec !== 'object' || Array.isArray(spec)) {
    throw new Error('Unsupported fs config payload');
  }
  if (!backendModule) {
    throw new Error('Backend module is not loaded');
  }

  switch (spec.kind) {
    case 'in_memory':
      return new backendModule.InMemoryFs(decodeFiles(spec.files));
    case 'overlay':
      return new backendModule.OverlayFs({
        root: spec.root,
        mountPoint: spec.mountPoint,
        readOnly: spec.readOnly,
        maxFileReadSize: spec.maxFileReadSize,
        allowSymlinks: spec.allowSymlinks,
      });
    case 'read_write':
      return new backendModule.ReadWriteFs({
        root: spec.root,
        maxFileReadSize: spec.maxFileReadSize,
        allowSymlinks: spec.allowSymlinks,
      });
    case 'mountable':
      return new backendModule.MountableFs({
        base: spec.base ? decodeFs(spec.base) : undefined,
        mounts: Array.isArray(spec.mounts)
          ? spec.mounts.map((mount) => ({
              mountPoint: mount.mountPoint,
              filesystem: decodeFs(mount.filesystem),
            }))
          : undefined,
      });
    default:
      throw new Error(`Unknown fs config kind: ${String(spec.kind)}`);
  }
}

function decodeInitOptions(options) {
  const decoded = {};

  if (options.files !== undefined) decoded.files = decodeFiles(options.files);
  if (options.env !== undefined) decoded.env = options.env;
  if (options.cwd !== undefined) decoded.cwd = options.cwd;
  if (options.fs !== undefined) decoded.fs = decodeFs(options.fs);
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

  const customCommandNames = Array.isArray(options.customCommandNames)
    ? options.customCommandNames.filter((name) => typeof name === 'string')
    : [];
  if (customCommandNames.length > 0) {
    decoded.customCommands = customCommandNames.map(createPythonCustomCommand);
  }

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

function decodeParseOptions(options) {
  const decoded = {};
  if (options?.maxHeredocSize !== undefined) {
    decoded.maxHeredocSize = options.maxHeredocSize;
  }
  return decoded;
}

function decodeTransformPlugin(spec) {
  if (!backendModule) {
    throw new Error('Backend module is not loaded');
  }
  if (!spec || typeof spec !== 'object' || Array.isArray(spec)) {
    throw new Error('Unsupported transform plugin payload');
  }

  switch (spec.kind) {
    case 'command_collector':
      return new backendModule.CommandCollectorPlugin();
    case 'tee': {
      const options = {
        outputDir: spec.outputDir,
      };
      if (typeof spec.targetCommandPatternSource === 'string') {
        options.targetCommandPattern = new RegExp(
          spec.targetCommandPatternSource,
          typeof spec.targetCommandPatternFlags === 'string'
            ? spec.targetCommandPatternFlags
            : '',
        );
      }
      if (spec.timestampMs !== undefined) {
        options.timestamp = new Date(spec.timestampMs);
      }
      return new backendModule.TeePlugin(options);
    }
    default:
      throw new Error(`Unsupported transform plugin kind: ${String(spec.kind)}`);
  }
}

function decodeTransformPlugins(specs) {
  if (!Array.isArray(specs)) {
    return [];
  }
  return specs.map((spec) => decodeTransformPlugin(spec));
}

function decodeSandboxOptions(options) {
  const decoded = {};
  if (options.cwd !== undefined) decoded.cwd = options.cwd;
  if (options.env !== undefined) decoded.env = options.env;
  if (options.timeoutMs !== undefined) decoded.timeoutMs = options.timeoutMs;
  if (options.fs !== undefined) decoded.fs = decodeFs(options.fs);
  if (options.overlayRoot !== undefined) decoded.overlayRoot = options.overlayRoot;
  if (options.maxCallDepth !== undefined) decoded.maxCallDepth = options.maxCallDepth;
  if (options.maxCommandCount !== undefined) decoded.maxCommandCount = options.maxCommandCount;
  if (options.maxLoopIterations !== undefined) decoded.maxLoopIterations = options.maxLoopIterations;
  if (options.network !== undefined) decoded.network = options.network;
  if (options.defenseInDepth !== undefined) {
    decoded.defenseInDepth = decodeDefenseInDepth(options.defenseInDepth);
  }
  return decoded;
}

function ensureInitialized() {
  if (!bash) {
    throw new Error('Worker is not initialized');
  }
}

function resolveSessionPath(path) {
  return bash.fs.resolvePath(bash.getCwd(), path);
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

function getSandbox(sandboxId) {
  const sandbox = sandboxes.get(sandboxId);
  if (!sandbox) {
    throw new Error(`Unknown sandbox: ${String(sandboxId)}`);
  }
  return sandbox;
}

function storeSandboxCommand(command) {
  const commandId = nextSandboxCommandId++;
  sandboxCommands.set(commandId, command);
  return commandId;
}

function getSandboxCommand(commandId) {
  const command = sandboxCommands.get(commandId);
  if (!command) {
    throw new Error(`Unknown sandbox command: ${String(commandId)}`);
  }
  return command;
}

async function describeSandboxCommand(command, commandId, includeOutput = false) {
  const payload = {
    commandId,
    cmdId: typeof command?.cmdId === 'string' ? command.cmdId : '',
    cwd: typeof command?.cwd === 'string' ? command.cwd : '',
    startedAtMs:
      command?.startedAt instanceof Date ? command.startedAt.getTime() : Date.now(),
    exitCode:
      command?.exitCode === undefined || Number.isInteger(command?.exitCode)
        ? command.exitCode ?? null
        : null,
  };

  if (includeOutput) {
    const finished = await command.wait();
    payload.exitCode = Number.isInteger(finished?.exitCode)
      ? finished.exitCode
      : payload.exitCode;
    payload.stdout = await command.stdout();
    payload.stderr = await command.stderr();
  }

  return payload;
}

async function collectSandboxLogs(command) {
  const messages = [];
  for await (const message of command.logs()) {
    messages.push({
      type: message?.type === 'stderr' ? 'stderr' : 'stdout',
      data: typeof message?.data === 'string' ? message.data : '',
      timestampMs:
        message?.timestamp instanceof Date ? message.timestamp.getTime() : Date.now(),
    });
  }
  return messages;
}

async function handleSandboxRunCommand(message) {
  const sandbox = getSandbox(message.sandboxId);
  const detached = Boolean(message.detached);

  let command;
  if (Array.isArray(message.args)) {
    if (message.cwd !== undefined || message.env !== undefined || detached || message.sudo) {
      command = await sandbox.runCommand({
        cmd: message.command,
        args: message.args,
        cwd: message.cwd,
        env: message.env,
        sudo: Boolean(message.sudo),
        detached,
      });
    } else {
      command = await sandbox.runCommand(message.command, message.args);
    }
  } else {
    if (detached || message.sudo) {
      command = await sandbox.runCommand({
        cmd: message.commandLine,
        cwd: message.cwd,
        env: message.env,
        sudo: Boolean(message.sudo),
        detached,
      });
    } else {
      command = await sandbox.runCommand(message.commandLine, {
        cwd: message.cwd,
        env: message.env,
      });
    }
  }

  const commandId = storeSandboxCommand(command);
  return await describeSandboxCommand(command, commandId, !detached);
}

async function runExec(executor, script, options) {
  const timeoutMs = options?.timeoutMs;
  const execOptions = { ...options };
  delete execOptions.timeoutMs;

  if (timeoutMs === undefined) {
    return await executor(script, execOptions);
  }

  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);

  try {
    return await executor(script, {
      ...execOptions,
      signal: controller.signal,
    });
  } finally {
    clearTimeout(timer);
  }
}

function normalizeCommandResult(result) {
  return {
    stdout: typeof result?.stdout === 'string' ? result.stdout : '',
    stderr: typeof result?.stderr === 'string' ? result.stderr : '',
    exitCode: Number.isInteger(result?.exitCode) ? result.exitCode : 0,
  };
}

async function handleCustomCommandExec(message) {
  const pending = pendingCustomCommands.get(message.invocationId);
  if (!pending) {
    throw new Error(`Unknown custom command invocation: ${message.invocationId}`);
  }
  if (typeof pending.ctx.exec !== 'function') {
    throw new Error('Custom command context does not support nested exec');
  }

  const execOptions = decodeExecOptions(message.options ?? {});
  if (execOptions.cwd === undefined) {
    execOptions.cwd = pending.ctx.cwd;
  }

  return await runExec(
    pending.ctx.exec.bind(pending.ctx),
    message.script,
    execOptions,
  );
}

function handleCustomCommandComplete(message) {
  const pending = pendingCustomCommands.get(message.invocationId);
  if (!pending) {
    throw new Error(`Unknown custom command invocation: ${message.invocationId}`);
  }

  pendingCustomCommands.delete(message.invocationId);
  pending.resolve(normalizeCommandResult(message.result));
  return null;
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
    return null;
  }

  pending.resolve(decodeFileContent(message.content));
  return null;
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
    return null;
  }

  pending.resolve(message.result ?? {});
  return null;
}

async function handleMessage(message) {
  switch (message.op) {
    case 'init': {
      const moduleUrl = pathToFileURL(message.jsEntry).href;
      const mod = await import(moduleUrl);
      backendModule = mod;
      BashClass = mod.Bash;
      bash = new BashClass(decodeInitOptions(message.options ?? {}));

      packageJsonPath = message.packageJson ?? null;
      if (message.packageJson) {
        const packageJson = JSON.parse(
          await readFile(message.packageJson, 'utf8'),
        );
        backendVersion = packageJson.version ?? null;
      }

      return { backendVersion };
    }

    case 'info': {
      ensureInitialized();
      return {
        backendVersion,
        cwd: bash.getCwd(),
        env: bash.getEnv(),
      };
    }

    case 'exec': {
      ensureInitialized();
      return await runExec(
        bash.exec.bind(bash),
        message.script,
        decodeExecOptions(message.options ?? {}),
      );
    }

    case 'get_command_names': {
      ensureInitialized();
      switch (message.kind) {
        case 'network':
          return backendModule.getNetworkCommandNames();
        case 'python':
          return backendModule.getPythonCommandNames();
        case 'javascript':
          return backendModule.getJavaScriptCommandNames();
        case 'all':
        default:
          return backendModule.getCommandNames();
      }
    }

    case 'parse': {
      ensureInitialized();
      return backendModule.parse(message.script, decodeParseOptions(message.options ?? {}));
    }

    case 'serialize': {
      ensureInitialized();
      return backendModule.serialize(message.ast);
    }

    case 'transform_script': {
      ensureInitialized();
      const pipeline = new backendModule.BashTransformPipeline();
      for (const plugin of decodeTransformPlugins(message.plugins)) {
        pipeline.use(plugin);
      }
      return pipeline.transform(message.script);
    }

    case 'register_transform_plugin': {
      ensureInitialized();
      bash.registerTransformPlugin(decodeTransformPlugin(message.plugin));
      return null;
    }

    case 'transform': {
      ensureInitialized();
      return bash.transform(message.script);
    }

    case 'sandbox_create': {
      ensureInitialized();
      const sandbox = await backendModule.Sandbox.create(
        decodeSandboxOptions(message.options ?? {}),
      );
      const sandboxId = nextSandboxId++;
      sandboxes.set(sandboxId, sandbox);
      return { sandboxId, domain: sandbox.domain ?? null };
    }

    case 'sandbox_run_command': {
      ensureInitialized();
      return await handleSandboxRunCommand(message);
    }

    case 'sandbox_write_files': {
      ensureInitialized();
      const sandbox = getSandbox(message.sandboxId);
      await sandbox.writeFiles(message.files ?? {});
      return null;
    }

    case 'sandbox_read_file': {
      ensureInitialized();
      const sandbox = getSandbox(message.sandboxId);
      return await sandbox.readFile(message.path, message.encoding);
    }

    case 'sandbox_mkdir': {
      ensureInitialized();
      const sandbox = getSandbox(message.sandboxId);
      await sandbox.mkDir(message.path, { recursive: Boolean(message.recursive) });
      return null;
    }

    case 'sandbox_extend_timeout': {
      ensureInitialized();
      const sandbox = getSandbox(message.sandboxId);
      await sandbox.extendTimeout(message.timeoutMs);
      return null;
    }

    case 'sandbox_stop': {
      ensureInitialized();
      const sandbox = getSandbox(message.sandboxId);
      await sandbox.stop();
      sandboxes.delete(message.sandboxId);
      return null;
    }

    case 'sandbox_command_wait': {
      ensureInitialized();
      const command = getSandboxCommand(message.commandId);
      return await describeSandboxCommand(command, message.commandId, true);
    }

    case 'sandbox_command_stdout': {
      ensureInitialized();
      const command = getSandboxCommand(message.commandId);
      return await command.stdout();
    }

    case 'sandbox_command_stderr': {
      ensureInitialized();
      const command = getSandboxCommand(message.commandId);
      return await command.stderr();
    }

    case 'sandbox_command_output': {
      ensureInitialized();
      const command = getSandboxCommand(message.commandId);
      return await command.output();
    }

    case 'sandbox_command_logs': {
      ensureInitialized();
      const command = getSandboxCommand(message.commandId);
      return await collectSandboxLogs(command);
    }

    case 'sandbox_command_kill': {
      ensureInitialized();
      const command = getSandboxCommand(message.commandId);
      await command.kill();
      return null;
    }

    case 'custom_command_exec': {
      ensureInitialized();
      return await handleCustomCommandExec(message);
    }

    case 'custom_command_complete': {
      ensureInitialized();
      return handleCustomCommandComplete(message);
    }

    case 'lazy_file_complete': {
      ensureInitialized();
      return handleLazyFileComplete(message);
    }

    case 'fetch_complete': {
      ensureInitialized();
      return handleFetchComplete(message);
    }

    case 'read_text': {
      ensureInitialized();
      return await bash.readFile(message.path);
    }

    case 'read_bytes': {
      ensureInitialized();
      const buffer = await bash.fs.readFileBuffer(resolveSessionPath(message.path));
      return encodeBytes(buffer);
    }

    case 'write_text': {
      ensureInitialized();
      await bash.writeFile(message.path, message.content);
      return null;
    }

    case 'write_bytes': {
      ensureInitialized();
      await bash.writeFile(message.path, decodeBytes(message.content));
      return null;
    }

    case 'append_text': {
      ensureInitialized();
      await bash.fs.appendFile(resolveSessionPath(message.path), message.content);
      return null;
    }

    case 'append_bytes': {
      ensureInitialized();
      await bash.fs.appendFile(resolveSessionPath(message.path), decodeBytes(message.content));
      return null;
    }

    case 'exists': {
      ensureInitialized();
      return await bash.fs.exists(resolveSessionPath(message.path));
    }

    case 'stat': {
      ensureInitialized();
      return normalizeFsStat(await bash.fs.stat(resolveSessionPath(message.path)));
    }

    case 'lstat': {
      ensureInitialized();
      return normalizeFsStat(await bash.fs.lstat(resolveSessionPath(message.path)));
    }

    case 'mkdir': {
      ensureInitialized();
      await bash.fs.mkdir(resolveSessionPath(message.path), {
        recursive: message.recursive,
      });
      return null;
    }

    case 'readdir': {
      ensureInitialized();
      return await bash.fs.readdir(resolveSessionPath(message.path));
    }

    case 'readdir_with_file_types': {
      ensureInitialized();
      if (typeof bash.fs.readdirWithFileTypes !== 'function') {
        throw new Error('readdirWithFileTypes is not available for this session filesystem');
      }
      return (await bash.fs.readdirWithFileTypes(resolveSessionPath(message.path))).map(
        normalizeDirentEntry,
      );
    }

    case 'rm': {
      ensureInitialized();
      await bash.fs.rm(resolveSessionPath(message.path), {
        recursive: message.recursive,
        force: message.force,
      });
      return null;
    }

    case 'cp': {
      ensureInitialized();
      await bash.fs.cp(resolveSessionPath(message.src), resolveSessionPath(message.dest), {
        recursive: message.recursive,
      });
      return null;
    }

    case 'mv': {
      ensureInitialized();
      await bash.fs.mv(resolveSessionPath(message.src), resolveSessionPath(message.dest));
      return null;
    }

    case 'resolve_path': {
      ensureInitialized();
      const base =
        typeof message.base === 'string' ? resolveSessionPath(message.base) : bash.getCwd();
      return bash.fs.resolvePath(base, message.path);
    }

    case 'get_all_paths': {
      ensureInitialized();
      return bash.fs.getAllPaths();
    }

    case 'chmod': {
      ensureInitialized();
      await bash.fs.chmod(resolveSessionPath(message.path), message.mode);
      return null;
    }

    case 'symlink': {
      ensureInitialized();
      await bash.fs.symlink(message.target, resolveSessionPath(message.linkPath));
      return null;
    }

    case 'link': {
      ensureInitialized();
      await bash.fs.link(
        resolveSessionPath(message.existingPath),
        resolveSessionPath(message.newPath),
      );
      return null;
    }

    case 'readlink': {
      ensureInitialized();
      return await bash.fs.readlink(resolveSessionPath(message.path));
    }

    case 'realpath': {
      ensureInitialized();
      return await bash.fs.realpath(resolveSessionPath(message.path));
    }

    case 'utimes': {
      ensureInitialized();
      await bash.fs.utimes(
        resolveSessionPath(message.path),
        new Date(message.atimeMs),
        new Date(message.mtimeMs),
      );
      return null;
    }

    case 'get_env': {
      ensureInitialized();
      return bash.getEnv();
    }

    case 'get_cwd': {
      ensureInitialized();
      return bash.getCwd();
    }

    case 'probe_defense_violation': {
      ensureInitialized();
      return await runDefenseViolationProbe(message.kind);
    }

    default:
      throw new Error(`Unknown operation: ${message.op}`);
  }
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

  handleMessage(message)
    .then((result) => {
      respond(message.id, true, result);
    })
    .catch((error) => {
      respond(message.id, false, errorPayload(error));
    });
});
"""
