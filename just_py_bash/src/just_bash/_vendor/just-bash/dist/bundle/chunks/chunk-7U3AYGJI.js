// dist/interpreter/errors.js
var ControlFlowError = class extends Error {
  stdout;
  stderr;
  constructor(message, stdout = "", stderr = "") {
    super(message);
    this.stdout = stdout;
    this.stderr = stderr;
  }
  /**
   * Prepend output from the current context before re-throwing.
   */
  prependOutput(stdout, stderr) {
    this.stdout = stdout + this.stdout;
    this.stderr = stderr + this.stderr;
  }
};
var BreakError = class extends ControlFlowError {
  levels;
  name = "BreakError";
  constructor(levels = 1, stdout = "", stderr = "") {
    super("break", stdout, stderr);
    this.levels = levels;
  }
};
var ContinueError = class extends ControlFlowError {
  levels;
  name = "ContinueError";
  constructor(levels = 1, stdout = "", stderr = "") {
    super("continue", stdout, stderr);
    this.levels = levels;
  }
};
var ReturnError = class extends ControlFlowError {
  exitCode;
  name = "ReturnError";
  constructor(exitCode = 0, stdout = "", stderr = "") {
    super("return", stdout, stderr);
    this.exitCode = exitCode;
  }
};
var ErrexitError = class extends ControlFlowError {
  exitCode;
  name = "ErrexitError";
  constructor(exitCode, stdout = "", stderr = "") {
    super(`errexit: command exited with status ${exitCode}`, stdout, stderr);
    this.exitCode = exitCode;
  }
};
var NounsetError = class extends ControlFlowError {
  varName;
  name = "NounsetError";
  constructor(varName, stdout = "") {
    super(`${varName}: unbound variable`, stdout, `bash: ${varName}: unbound variable
`);
    this.varName = varName;
  }
};
var ExitError = class extends ControlFlowError {
  exitCode;
  name = "ExitError";
  constructor(exitCode, stdout = "", stderr = "") {
    super(`exit`, stdout, stderr);
    this.exitCode = exitCode;
  }
};
var ArithmeticError = class extends ControlFlowError {
  name = "ArithmeticError";
  /**
   * If true, this error should abort script execution (like missing operand after binary operator).
   * If false, the error is recoverable and execution can continue.
   */
  fatal;
  constructor(message, stdout = "", stderr = "", fatal = false) {
    super(message, stdout, stderr);
    this.stderr = stderr || `bash: ${message}
`;
    this.fatal = fatal;
  }
};
var BadSubstitutionError = class extends ControlFlowError {
  name = "BadSubstitutionError";
  constructor(message, stdout = "", stderr = "") {
    super(message, stdout, stderr);
    this.stderr = stderr || `bash: ${message}: bad substitution
`;
  }
};
var GlobError = class extends ControlFlowError {
  name = "GlobError";
  constructor(pattern, stdout = "", stderr = "") {
    super(`no match: ${pattern}`, stdout, stderr);
    this.stderr = stderr || `bash: no match: ${pattern}
`;
  }
};
var BraceExpansionError = class extends ControlFlowError {
  name = "BraceExpansionError";
  constructor(message, stdout = "", stderr = "") {
    super(message, stdout, stderr);
    this.stderr = stderr || `bash: ${message}
`;
  }
};
var ExecutionLimitError = class extends ControlFlowError {
  limitType;
  name = "ExecutionLimitError";
  static EXIT_CODE = 126;
  constructor(message, limitType, stdout = "", stderr = "") {
    super(message, stdout, stderr);
    this.limitType = limitType;
    this.stderr = stderr || `bash: ${message}
`;
  }
};
var ExecutionAbortedError = class extends ControlFlowError {
  name = "ExecutionAbortedError";
  constructor(stdout = "", stderr = "") {
    super("execution aborted", stdout, stderr);
  }
};
var SubshellExitError = class extends ControlFlowError {
  name = "SubshellExitError";
  constructor(stdout = "", stderr = "") {
    super("subshell exit", stdout, stderr);
  }
};
function isScopeExitError(error) {
  return error instanceof BreakError || error instanceof ContinueError || error instanceof ReturnError;
}
var PosixFatalError = class extends ControlFlowError {
  exitCode;
  name = "PosixFatalError";
  constructor(exitCode, stdout = "", stderr = "") {
    super("posix fatal error", stdout, stderr);
    this.exitCode = exitCode;
  }
};

export {
  BreakError,
  ContinueError,
  ReturnError,
  ErrexitError,
  NounsetError,
  ExitError,
  ArithmeticError,
  BadSubstitutionError,
  GlobError,
  BraceExpansionError,
  ExecutionLimitError,
  ExecutionAbortedError,
  SubshellExitError,
  isScopeExitError,
  PosixFatalError
};
