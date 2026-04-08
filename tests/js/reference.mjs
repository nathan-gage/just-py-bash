import { readFile } from 'node:fs/promises';
import { pathToFileURL } from 'node:url';

const BYTE_TAG = '__just_py_bash_bytes__';

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

async function readStdin() {
  const chunks = [];
  for await (const chunk of process.stdin) {
    chunks.push(chunk);
  }
  return chunks.join('');
}

const request = JSON.parse(await readStdin());
const mod = await import(pathToFileURL(request.jsEntry).href);
const bash = new mod.Bash(decodeInitOptions(request.initOptions ?? {}));
const packageJson = JSON.parse(await readFile(request.packageJson, 'utf8'));

const results = [];
for (const operation of request.operations) {
  switch (operation.op) {
    case 'exec':
      results.push(
        await execWithTimeout(
          bash,
          operation.script,
          decodeExecOptions(operation.options ?? {}),
        ),
      );
      break;
    case 'read_text':
      results.push(await bash.readFile(operation.path));
      break;
    case 'read_bytes':
      results.push(
        encodeBytes(
          await bash.fs.readFileBuffer(
            bash.fs.resolvePath(bash.getCwd(), operation.path),
          ),
        ),
      );
      break;
    case 'write_text':
      await bash.writeFile(operation.path, operation.content);
      results.push(null);
      break;
    case 'write_bytes':
      await bash.writeFile(operation.path, decodeBytes(operation.content));
      results.push(null);
      break;
    case 'get_env':
      results.push(bash.getEnv());
      break;
    case 'get_cwd':
      results.push(bash.getCwd());
      break;
    default:
      throw new Error(`Unknown operation: ${operation.op}`);
  }
}

process.stdout.write(
  JSON.stringify({
    backendVersion: packageJson.version ?? null,
    results,
  }),
);
