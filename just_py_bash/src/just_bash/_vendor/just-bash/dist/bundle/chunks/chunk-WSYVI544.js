import {
  parseDuration
} from "./chunk-I5QVGVQT.js";
import {
  _clearTimeout,
  _setTimeout
} from "./chunk-4HTZXI76.js";
import {
  hasHelpFlag,
  showHelp
} from "./chunk-GFRMOA7L.js";

// dist/commands/sleep/sleep.js
var sleepHelp = {
  name: "sleep",
  summary: "delay for a specified amount of time",
  usage: "sleep NUMBER[SUFFIX]",
  description: `Pause for NUMBER seconds. SUFFIX may be:
  s - seconds (default)
  m - minutes
  h - hours
  d - days

NUMBER may be a decimal number.`,
  options: ["    --help display this help and exit"]
};
var MAX_SLEEP_MS = 36e5;
var sleepCommand = {
  name: "sleep",
  async execute(args, ctx) {
    if (hasHelpFlag(args)) {
      return showHelp(sleepHelp);
    }
    if (args.length === 0) {
      return {
        stdout: "",
        stderr: "sleep: missing operand\n",
        exitCode: 1
      };
    }
    let totalMs = 0;
    for (const arg of args) {
      const ms = parseDuration(arg);
      if (ms === null) {
        return {
          stdout: "",
          stderr: `sleep: invalid time interval '${arg}'
`,
          exitCode: 1
        };
      }
      totalMs += ms;
    }
    if (totalMs > MAX_SLEEP_MS) {
      totalMs = MAX_SLEEP_MS;
    }
    if (ctx.signal?.aborted) {
      return { stdout: "", stderr: "", exitCode: 0 };
    }
    if (ctx.sleep) {
      await ctx.sleep(totalMs);
    } else if (ctx.signal) {
      await new Promise((resolve) => {
        const onAbort = () => {
          _clearTimeout(timer);
          resolve();
        };
        const timer = _setTimeout(() => {
          ctx.signal?.removeEventListener("abort", onAbort);
          resolve();
        }, totalMs);
        ctx.signal?.addEventListener("abort", onAbort, { once: true });
      });
    } else {
      await new Promise((resolve) => _setTimeout(resolve, totalMs));
    }
    return { stdout: "", stderr: "", exitCode: 0 };
  }
};
var flagsForFuzzing = {
  name: "sleep",
  flags: [],
  needsArgs: true
};

export {
  sleepCommand,
  flagsForFuzzing
};
