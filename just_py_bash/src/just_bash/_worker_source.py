WORKER_SOURCE = """
import { readFile } from 'node:fs/promises';
import { createInterface } from 'node:readline';
import { pathToFileURL } from 'node:url';

const BYTE_TAG = '__just_bash_bytes__';

let BashClass = null;
let backendModule = null;
let bash = null;
let backendVersion = null;
let nextInvocationId = 1;
const pendingCustomCommands = new Map();
const pendingLazyFiles = new Map();

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

async function handleMessage(message) {
  switch (message.op) {
    case 'init': {
      const moduleUrl = pathToFileURL(message.jsEntry).href;
      const mod = await import(moduleUrl);
      backendModule = mod;
      BashClass = mod.Bash;
      bash = new BashClass(decodeInitOptions(message.options ?? {}));

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

    case 'exists': {
      ensureInitialized();
      return await bash.fs.exists(resolveSessionPath(message.path));
    }

    case 'stat': {
      ensureInitialized();
      return normalizeFsStat(await bash.fs.stat(resolveSessionPath(message.path)));
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

    case 'chmod': {
      ensureInitialized();
      await bash.fs.chmod(resolveSessionPath(message.path), message.mode);
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

    case 'get_env': {
      ensureInitialized();
      return bash.getEnv();
    }

    case 'get_cwd': {
      ensureInitialized();
      return bash.getCwd();
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
