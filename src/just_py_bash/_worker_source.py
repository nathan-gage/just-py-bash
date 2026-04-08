WORKER_SOURCE = """
import { readFile } from 'node:fs/promises';
import { createInterface } from 'node:readline';
import { pathToFileURL } from 'node:url';

const BYTE_TAG = '__just_py_bash_bytes__';

let BashClass = null;
let bash = null;
let backendVersion = null;
let nextInvocationId = 1;
const pendingCustomCommands = new Map();

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

function decodeFiles(files) {
  if (!files) {
    return undefined;
  }

  const decoded = {};
  for (const [path, value] of Object.entries(files)) {
    decoded[path] = decodeFileContent(value);
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

function decodeInitOptions(options) {
  const decoded = {};

  if (options.files !== undefined) decoded.files = decodeFiles(options.files);
  if (options.env !== undefined) decoded.env = options.env;
  if (options.cwd !== undefined) decoded.cwd = options.cwd;
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

async function handleMessage(message) {
  switch (message.op) {
    case 'init': {
      const moduleUrl = pathToFileURL(message.jsEntry).href;
      const mod = await import(moduleUrl);
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

    case 'read_text': {
      ensureInitialized();
      return await bash.readFile(message.path);
    }

    case 'read_bytes': {
      ensureInitialized();
      const buffer = await bash.fs.readFileBuffer(
        bash.fs.resolvePath(bash.getCwd(), message.path),
      );
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
