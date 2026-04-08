import {
  parseDuration
} from "./chunk-I5QVGVQT.js";
import {
  _clearTimeout,
  _setTimeout
} from "./chunk-4HTZXI76.js";
import {
  shellJoinArgs
} from "./chunk-2PXGQ7LT.js";
import {
  hasHelpFlag,
  showHelp,
  unknownOption
} from "./chunk-GFRMOA7L.js";

// dist/commands/timeout/timeout.js
var timeoutHelp = {
  name: "timeout",
  summary: "run a command with a time limit",
  usage: "timeout [OPTION] DURATION COMMAND [ARG]...",
  description: `Start COMMAND, and kill it if still running after DURATION.

DURATION is a number with optional suffix:
  s - seconds (default)
  m - minutes
  h - hours
  d - days`,
  options: [
    "-k, --kill-after=DURATION  send KILL signal after DURATION if still running",
    "-s, --signal=SIGNAL        specify signal to send (default: TERM)",
    "    --preserve-status      exit with same status as COMMAND, even on timeout",
    "    --foreground           run command in foreground",
    "    --help                 display this help and exit"
  ]
};
var timeoutCommand = {
  name: "timeout",
  async execute(args, ctx) {
    if (hasHelpFlag(args)) {
      return showHelp(timeoutHelp);
    }
    let commandStart = 0;
    for (let i = 0; i < args.length; i++) {
      const arg = args[i];
      if (arg === "--preserve-status") {
        commandStart = i + 1;
      } else if (arg === "--foreground") {
        commandStart = i + 1;
      } else if (arg === "-k" || arg === "--kill-after") {
        i++;
        commandStart = i + 1;
      } else if (arg.startsWith("--kill-after=")) {
        commandStart = i + 1;
      } else if (arg === "-s" || arg === "--signal") {
        i++;
        commandStart = i + 1;
      } else if (arg.startsWith("--signal=")) {
        commandStart = i + 1;
      } else if (arg.startsWith("--") && arg !== "--") {
        return unknownOption("timeout", arg);
      } else if (arg.startsWith("-") && arg.length > 1 && arg !== "--") {
        if (arg.startsWith("-k")) {
          commandStart = i + 1;
        } else if (arg.startsWith("-s")) {
          commandStart = i + 1;
        } else {
          return unknownOption("timeout", arg);
        }
      } else {
        commandStart = i;
        break;
      }
    }
    const remainingArgs = args.slice(commandStart);
    if (remainingArgs.length === 0) {
      return {
        stdout: "",
        stderr: "timeout: missing operand\n",
        exitCode: 1
      };
    }
    const durationStr = remainingArgs[0];
    const durationMs = parseDuration(durationStr);
    if (durationMs === null) {
      return {
        stdout: "",
        stderr: `timeout: invalid time interval '${durationStr}'
`,
        exitCode: 1
      };
    }
    const commandArgs = remainingArgs.slice(1);
    if (commandArgs.length === 0) {
      return {
        stdout: "",
        stderr: "timeout: missing operand\n",
        exitCode: 1
      };
    }
    if (!ctx.exec) {
      return {
        stdout: "",
        stderr: "timeout: exec not available\n",
        exitCode: 1
      };
    }
    const controller = new AbortController();
    let timerId;
    try {
      const timeoutPromise = new Promise((resolve) => {
        timerId = _setTimeout(() => {
          controller.abort();
          resolve({ timedOut: true });
        }, durationMs);
      });
      const execPromise = ctx.exec(shellJoinArgs([commandArgs[0]]), {
        cwd: ctx.cwd,
        signal: controller.signal,
        stdin: ctx.stdin,
        args: commandArgs.slice(1)
      }).then((result) => ({ timedOut: false, result }));
      const outcome = await Promise.race([timeoutPromise, execPromise]);
      if (outcome.timedOut) {
        return {
          stdout: "",
          stderr: "",
          exitCode: 124
        };
      }
      return outcome.result;
    } finally {
      if (timerId !== void 0) {
        _clearTimeout(timerId);
      }
    }
  }
};
var flagsForFuzzing = {
  name: "timeout",
  flags: [
    { flag: "-k", type: "value", valueHint: "string" },
    { flag: "-s", type: "value", valueHint: "string" },
    { flag: "--preserve-status", type: "boolean" },
    { flag: "--foreground", type: "boolean" }
  ],
  needsArgs: true,
  minArgs: 2
};

export {
  timeoutCommand,
  flagsForFuzzing
};
