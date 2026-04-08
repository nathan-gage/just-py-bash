import {
  _Atomics,
  _SharedArrayBuffer
} from "./chunk-FRLCLFVF.js";
import {
  _clearTimeout,
  _setTimeout
} from "./chunk-4HTZXI76.js";
import {
  shellJoinArgs
} from "./chunk-2PXGQ7LT.js";
import {
  sanitizeErrorMessage
} from "./chunk-A6TBX6EJ.js";

// dist/commands/worker-bridge/protocol.js
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
function createSharedBuffer() {
  return new _SharedArrayBuffer(Size.TOTAL);
}
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
    return _Atomics.load(this.int32View, Offset.ERROR_CODE / 4);
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
    const bytes = this.uint8View.slice(Offset.PATH_BUFFER, Offset.PATH_BUFFER + length);
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
    return this.uint8View.slice(Offset.DATA_BUFFER, Offset.DATA_BUFFER + length);
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
    return this.uint8View.slice(Offset.DATA_BUFFER, Offset.DATA_BUFFER + length);
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
    this.dataView.setInt32(Offset.DATA_BUFFER + StatLayout.MODE, stat.mode, true);
    const size = Math.min(stat.size, Number.MAX_SAFE_INTEGER);
    this.dataView.setFloat64(Offset.DATA_BUFFER + StatLayout.SIZE, size, true);
    this.dataView.setFloat64(Offset.DATA_BUFFER + StatLayout.MTIME, stat.mtime.getTime(), true);
    this.setResultLength(StatLayout.TOTAL);
  }
  decodeStat() {
    return {
      isFile: this.uint8View[Offset.DATA_BUFFER + StatLayout.IS_FILE] === 1,
      isDirectory: this.uint8View[Offset.DATA_BUFFER + StatLayout.IS_DIRECTORY] === 1,
      isSymbolicLink: this.uint8View[Offset.DATA_BUFFER + StatLayout.IS_SYMLINK] === 1,
      mode: this.dataView.getInt32(Offset.DATA_BUFFER + StatLayout.MODE, true),
      size: this.dataView.getFloat64(Offset.DATA_BUFFER + StatLayout.SIZE, true),
      mtime: new Date(this.dataView.getFloat64(Offset.DATA_BUFFER + StatLayout.MTIME, true))
    };
  }
  waitForReady(timeout) {
    return _Atomics.wait(this.int32View, Offset.STATUS / 4, Status.PENDING, timeout);
  }
  waitForReadyAsync(timeout) {
    return _Atomics.waitAsync(this.int32View, Offset.STATUS / 4, Status.PENDING, timeout);
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
      const result = _Atomics.waitAsync(this.int32View, Offset.STATUS / 4, status, remainingMs);
      if (result.async) {
        const waitResult = await result.value;
        if (waitResult === "timed-out") {
          return false;
        }
      }
    }
  }
  waitForResult(timeout) {
    return _Atomics.wait(this.int32View, Offset.STATUS / 4, Status.READY, timeout);
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

// dist/commands/worker-bridge/bridge-handler.js
var BridgeHandler = class {
  fs;
  cwd;
  commandName;
  secureFetch;
  maxOutputSize;
  exec;
  protocol;
  running = false;
  output = { stdout: "", stderr: "", exitCode: 0 };
  outputLimitExceeded = false;
  startTime = 0;
  timeoutMs = 0;
  constructor(sharedBuffer, fs, cwd, commandName, secureFetch = void 0, maxOutputSize = 0, exec = void 0) {
    this.fs = fs;
    this.cwd = cwd;
    this.commandName = commandName;
    this.secureFetch = secureFetch;
    this.maxOutputSize = maxOutputSize;
    this.exec = exec;
    this.protocol = new ProtocolBuffer(sharedBuffer);
  }
  /**
   * Returns remaining milliseconds before the overall execution deadline.
   */
  remainingMs() {
    return Math.max(0, this.timeoutMs - (Date.now() - this.startTime));
  }
  /**
   * Races a promise against the remaining execution deadline.
   * If the deadline expires first, sets `this.running = false` and rejects.
   */
  raceDeadline(fn) {
    const remaining = this.remainingMs();
    if (remaining <= 0) {
      this.running = false;
      this.output.exitCode = 124;
      this.output.stderr += `
${this.commandName}: execution timeout exceeded
`;
      return Promise.reject(new Error("Operation timed out"));
    }
    const promise = fn();
    return new Promise((resolve, reject) => {
      const timer = _setTimeout(() => {
        this.running = false;
        this.output.exitCode = 124;
        this.output.stderr += `
${this.commandName}: execution timeout exceeded
`;
        reject(new Error("Operation timed out"));
      }, remaining);
      promise.then((v) => {
        _clearTimeout(timer);
        resolve(v);
      }, (e) => {
        _clearTimeout(timer);
        reject(e);
      });
    });
  }
  /**
   * Run the handler loop until EXIT operation or timeout.
   */
  async run(timeoutMs) {
    this.running = true;
    this.startTime = Date.now();
    this.timeoutMs = timeoutMs;
    while (this.running) {
      const elapsed = Date.now() - this.startTime;
      if (elapsed >= timeoutMs) {
        this.output.stderr += `
${this.commandName}: execution timeout exceeded
`;
        this.output.exitCode = 124;
        break;
      }
      const remainingMs = this.remainingMs();
      const ready = await this.protocol.waitUntilReady(remainingMs);
      if (!ready) {
        this.output.stderr += `
${this.commandName}: execution timeout exceeded
`;
        this.output.exitCode = 124;
        break;
      }
      const opCode = this.protocol.getOpCode();
      await this.handleOperation(opCode);
      this.protocol.notify();
    }
    return this.output;
  }
  stop() {
    this.running = false;
  }
  async handleOperation(opCode) {
    try {
      switch (opCode) {
        case OpCode.READ_FILE:
          await this.handleReadFile();
          break;
        case OpCode.WRITE_FILE:
          await this.handleWriteFile();
          break;
        case OpCode.STAT:
          await this.handleStat();
          break;
        case OpCode.LSTAT:
          await this.handleLstat();
          break;
        case OpCode.READDIR:
          await this.handleReaddir();
          break;
        case OpCode.MKDIR:
          await this.handleMkdir();
          break;
        case OpCode.RM:
          await this.handleRm();
          break;
        case OpCode.EXISTS:
          await this.handleExists();
          break;
        case OpCode.APPEND_FILE:
          await this.handleAppendFile();
          break;
        case OpCode.SYMLINK:
          await this.handleSymlink();
          break;
        case OpCode.READLINK:
          await this.handleReadlink();
          break;
        case OpCode.CHMOD:
          await this.handleChmod();
          break;
        case OpCode.REALPATH:
          await this.handleRealpath();
          break;
        case OpCode.RENAME:
          await this.handleRename();
          break;
        case OpCode.COPY_FILE:
          await this.handleCopyFile();
          break;
        case OpCode.WRITE_STDOUT:
          this.handleWriteStdout();
          break;
        case OpCode.WRITE_STDERR:
          this.handleWriteStderr();
          break;
        case OpCode.EXIT:
          this.handleExit();
          break;
        case OpCode.HTTP_REQUEST:
          await this.handleHttpRequest();
          break;
        case OpCode.EXEC_COMMAND:
          await this.handleExecCommand();
          break;
        default:
          this.protocol.setErrorCode(ErrorCode.IO_ERROR);
          this.protocol.setStatus(Status.ERROR);
      }
    } catch (e) {
      this.setErrorFromException(e);
    }
  }
  resolvePath(path) {
    return this.fs.resolvePath(this.cwd, path);
  }
  async handleReadFile() {
    const path = this.resolvePath(this.protocol.getPath());
    try {
      const content = await this.fs.readFileBuffer(path);
      this.protocol.setResult(content);
      this.protocol.setStatus(Status.SUCCESS);
    } catch (e) {
      this.setErrorFromException(e);
    }
  }
  async handleWriteFile() {
    const path = this.resolvePath(this.protocol.getPath());
    const data = this.protocol.getData();
    try {
      await this.fs.writeFile(path, data);
      this.protocol.setStatus(Status.SUCCESS);
    } catch (e) {
      this.setErrorFromException(e);
    }
  }
  async handleStat() {
    const path = this.resolvePath(this.protocol.getPath());
    try {
      const stat = await this.fs.stat(path);
      this.protocol.encodeStat(stat);
      this.protocol.setStatus(Status.SUCCESS);
    } catch (e) {
      this.setErrorFromException(e);
    }
  }
  async handleLstat() {
    const path = this.resolvePath(this.protocol.getPath());
    try {
      const stat = await this.fs.lstat(path);
      this.protocol.encodeStat(stat);
      this.protocol.setStatus(Status.SUCCESS);
    } catch (e) {
      this.setErrorFromException(e);
    }
  }
  async handleReaddir() {
    const path = this.resolvePath(this.protocol.getPath());
    try {
      const entries = await this.fs.readdir(path);
      this.protocol.setResultFromString(JSON.stringify(entries));
      this.protocol.setStatus(Status.SUCCESS);
    } catch (e) {
      this.setErrorFromException(e);
    }
  }
  async handleMkdir() {
    const path = this.resolvePath(this.protocol.getPath());
    const flags = this.protocol.getFlags();
    const recursive = (flags & Flags.MKDIR_RECURSIVE) !== 0;
    try {
      await this.fs.mkdir(path, { recursive });
      this.protocol.setStatus(Status.SUCCESS);
    } catch (e) {
      this.setErrorFromException(e);
    }
  }
  async handleRm() {
    const path = this.resolvePath(this.protocol.getPath());
    const flags = this.protocol.getFlags();
    const recursive = (flags & Flags.RECURSIVE) !== 0;
    const force = (flags & Flags.FORCE) !== 0;
    try {
      await this.fs.rm(path, { recursive, force });
      this.protocol.setStatus(Status.SUCCESS);
    } catch (e) {
      this.setErrorFromException(e);
    }
  }
  async handleExists() {
    const path = this.resolvePath(this.protocol.getPath());
    try {
      const exists = await this.fs.exists(path);
      this.protocol.setResult(new Uint8Array([exists ? 1 : 0]));
      this.protocol.setStatus(Status.SUCCESS);
    } catch (e) {
      this.setErrorFromException(e);
    }
  }
  async handleAppendFile() {
    const path = this.resolvePath(this.protocol.getPath());
    const data = this.protocol.getData();
    try {
      await this.fs.appendFile(path, data);
      this.protocol.setStatus(Status.SUCCESS);
    } catch (e) {
      this.setErrorFromException(e);
    }
  }
  async handleSymlink() {
    const path = this.protocol.getPath();
    const data = this.protocol.getDataAsString();
    const linkPath = this.resolvePath(path);
    try {
      await this.fs.symlink(data, linkPath);
      this.protocol.setStatus(Status.SUCCESS);
    } catch (e) {
      this.setErrorFromException(e);
    }
  }
  async handleReadlink() {
    const path = this.resolvePath(this.protocol.getPath());
    try {
      const target = await this.fs.readlink(path);
      this.protocol.setResultFromString(target);
      this.protocol.setStatus(Status.SUCCESS);
    } catch (e) {
      this.setErrorFromException(e);
    }
  }
  async handleChmod() {
    const path = this.resolvePath(this.protocol.getPath());
    const mode = this.protocol.getMode();
    try {
      await this.fs.chmod(path, mode);
      this.protocol.setStatus(Status.SUCCESS);
    } catch (e) {
      this.setErrorFromException(e);
    }
  }
  async handleRealpath() {
    const path = this.resolvePath(this.protocol.getPath());
    try {
      const realpath = await this.fs.realpath(path);
      this.protocol.setResultFromString(realpath);
      this.protocol.setStatus(Status.SUCCESS);
    } catch (e) {
      this.setErrorFromException(e);
    }
  }
  async handleRename() {
    const oldPath = this.resolvePath(this.protocol.getPath());
    const newPath = this.resolvePath(this.protocol.getDataAsString());
    try {
      await this.fs.mv(oldPath, newPath);
      this.protocol.setStatus(Status.SUCCESS);
    } catch (e) {
      this.setErrorFromException(e);
    }
  }
  async handleCopyFile() {
    const src = this.resolvePath(this.protocol.getPath());
    const dest = this.resolvePath(this.protocol.getDataAsString());
    try {
      await this.fs.cp(src, dest);
      this.protocol.setStatus(Status.SUCCESS);
    } catch (e) {
      this.setErrorFromException(e);
    }
  }
  handleWriteStdout() {
    const data = this.protocol.getDataAsString();
    if (!this.tryAppendOutput("stdout", data)) {
      this.outputLimitExceeded = true;
      this.output.exitCode = 1;
      this.appendOutputLimitError();
      this.protocol.setErrorCode(ErrorCode.IO_ERROR);
      this.protocol.setResultFromString("Output size limit exceeded");
      this.protocol.setStatus(Status.ERROR);
      return;
    }
    this.protocol.setStatus(Status.SUCCESS);
  }
  handleWriteStderr() {
    const data = this.protocol.getDataAsString();
    if (!this.tryAppendOutput("stderr", data)) {
      this.outputLimitExceeded = true;
      this.output.exitCode = 1;
      this.appendOutputLimitError();
      this.protocol.setErrorCode(ErrorCode.IO_ERROR);
      this.protocol.setResultFromString("Output size limit exceeded");
      this.protocol.setStatus(Status.ERROR);
      return;
    }
    this.protocol.setStatus(Status.SUCCESS);
  }
  handleExit() {
    const exitCode = this.protocol.getFlags();
    if (!this.outputLimitExceeded) {
      this.output.exitCode = exitCode;
    } else if (this.output.exitCode === 0) {
      this.output.exitCode = 1;
    }
    this.protocol.setStatus(Status.SUCCESS);
    this.running = false;
  }
  tryAppendOutput(stream, data) {
    if (this.outputLimitExceeded) {
      return false;
    }
    if (this.maxOutputSize <= 0) {
      if (stream === "stdout") {
        this.output.stdout += data;
      } else {
        this.output.stderr += data;
      }
      return true;
    }
    const total = this.output.stdout.length + this.output.stderr.length;
    if (total + data.length > this.maxOutputSize) {
      return false;
    }
    if (stream === "stdout") {
      this.output.stdout += data;
    } else {
      this.output.stderr += data;
    }
    return true;
  }
  appendOutputLimitError() {
    if (this.maxOutputSize <= 0) {
      return;
    }
    const fullMsg = `${this.commandName}: total output size exceeded (>${this.maxOutputSize} bytes), increase executionLimits.maxOutputSize
`;
    const msg = fullMsg.length > this.maxOutputSize ? fullMsg.slice(0, this.maxOutputSize) : fullMsg;
    if (this.output.stderr.includes("total output size exceeded")) {
      return;
    }
    const currentTotal = this.output.stdout.length + this.output.stderr.length;
    const needed = currentTotal + msg.length - this.maxOutputSize;
    if (needed > 0) {
      if (this.output.stdout.length >= needed) {
        this.output.stdout = this.output.stdout.slice(0, this.output.stdout.length - needed);
      } else {
        const remainingNeeded = needed - this.output.stdout.length;
        this.output.stdout = "";
        if (remainingNeeded >= this.output.stderr.length) {
          this.output.stderr = "";
        } else {
          this.output.stderr = this.output.stderr.slice(0, this.output.stderr.length - remainingNeeded);
        }
      }
    }
    this.output.stderr += msg;
  }
  async handleHttpRequest() {
    const fetchFn = this.secureFetch;
    if (!fetchFn) {
      this.protocol.setErrorCode(ErrorCode.NETWORK_NOT_CONFIGURED);
      this.protocol.setResultFromString("Network access not configured. Enable network in Bash options.");
      this.protocol.setStatus(Status.ERROR);
      return;
    }
    const url = this.protocol.getPath();
    const requestJson = this.protocol.getDataAsString();
    try {
      const request = requestJson ? JSON.parse(requestJson) : {};
      const remaining = this.remainingMs();
      const result = await this.raceDeadline(() => fetchFn(url, {
        method: request.method,
        headers: request.headers,
        body: request.body,
        timeoutMs: remaining
      }));
      const response = JSON.stringify({
        status: result.status,
        statusText: result.statusText,
        headers: result.headers,
        body: result.body,
        url: result.url
      });
      this.protocol.setResultFromString(response);
      this.protocol.setStatus(Status.SUCCESS);
    } catch (e) {
      const message = sanitizeErrorMessage(e instanceof Error ? e.message : String(e));
      this.protocol.setErrorCode(ErrorCode.NETWORK_ERROR);
      this.protocol.setResultFromString(message);
      this.protocol.setStatus(Status.ERROR);
    }
  }
  async handleExecCommand() {
    const execFn = this.exec;
    if (!execFn) {
      this.protocol.setErrorCode(ErrorCode.IO_ERROR);
      this.protocol.setResultFromString("Command execution not available in this context.");
      this.protocol.setStatus(Status.ERROR);
      return;
    }
    let command = this.protocol.getPath();
    const dataStr = this.protocol.getDataAsString();
    const controller = new AbortController();
    try {
      const options = {
        cwd: this.cwd,
        signal: controller.signal
      };
      if (dataStr) {
        const parsed = JSON.parse(dataStr);
        if (parsed.stdin) {
          options.stdin = parsed.stdin;
        }
        if (parsed.args && Array.isArray(parsed.args)) {
          options.args = parsed.args.map((a) => String(a));
          command = shellJoinArgs([command]);
        }
      }
      const result = await this.raceDeadline(() => execFn(command, options));
      const response = JSON.stringify({
        stdout: result.stdout,
        stderr: result.stderr,
        exitCode: result.exitCode
      });
      this.protocol.setResultFromString(response);
      this.protocol.setStatus(Status.SUCCESS);
    } catch (e) {
      controller.abort();
      const message = e instanceof Error ? e.message : String(e);
      this.protocol.setErrorCode(ErrorCode.IO_ERROR);
      this.protocol.setResultFromString(message);
      this.protocol.setStatus(Status.ERROR);
    }
  }
  setErrorFromException(e) {
    const rawMessage = e instanceof Error ? e.message : String(e);
    const message = sanitizeErrorMessage(rawMessage);
    let errorCode = ErrorCode.IO_ERROR;
    const lowerMsg = rawMessage.toLowerCase();
    if (lowerMsg.includes("no such file") || lowerMsg.includes("not found") || lowerMsg.includes("enoent")) {
      errorCode = ErrorCode.NOT_FOUND;
    } else if (lowerMsg.includes("is a directory") || lowerMsg.includes("eisdir")) {
      errorCode = ErrorCode.IS_DIRECTORY;
    } else if (lowerMsg.includes("not a directory") || lowerMsg.includes("enotdir")) {
      errorCode = ErrorCode.NOT_DIRECTORY;
    } else if (lowerMsg.includes("already exists") || lowerMsg.includes("eexist")) {
      errorCode = ErrorCode.EXISTS;
    } else if (lowerMsg.includes("permission") || lowerMsg.includes("eperm") || lowerMsg.includes("eacces")) {
      errorCode = ErrorCode.PERMISSION_DENIED;
    }
    this.protocol.setErrorCode(errorCode);
    this.protocol.setResultFromString(message);
    this.protocol.setStatus(Status.ERROR);
  }
};

export {
  createSharedBuffer,
  BridgeHandler
};
