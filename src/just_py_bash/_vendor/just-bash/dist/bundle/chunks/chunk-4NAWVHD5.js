import {
  mapToRecord
} from "./chunk-7I2WJAI4.js";
import {
  hasHelpFlag,
  showHelp,
  unknownOption
} from "./chunk-GFRMOA7L.js";

// dist/commands/env/env.js
var envHelp = {
  name: "env",
  summary: "run a program in a modified environment",
  usage: "env [OPTION]... [NAME=VALUE]... [COMMAND [ARG]...]",
  options: [
    "-i, --ignore-environment  start with an empty environment",
    "-u NAME, --unset=NAME     remove NAME from the environment",
    "    --help                display this help and exit"
  ]
};
var envCommand = {
  name: "env",
  async execute(args, ctx) {
    if (hasHelpFlag(args)) {
      return showHelp(envHelp);
    }
    let ignoreEnv = false;
    const unsetVars = [];
    const setVars = /* @__PURE__ */ new Map();
    let commandStart = -1;
    for (let i = 0; i < args.length; i++) {
      const arg = args[i];
      if (arg === "-i" || arg === "--ignore-environment") {
        ignoreEnv = true;
      } else if (arg === "-u" && i + 1 < args.length) {
        unsetVars.push(args[++i]);
      } else if (arg.startsWith("-u")) {
        unsetVars.push(arg.slice(2));
      } else if (arg.startsWith("--unset=")) {
        unsetVars.push(arg.slice(8));
      } else if (arg.startsWith("--") && arg !== "--") {
        return unknownOption("env", arg);
      } else if (arg.startsWith("-") && arg !== "-") {
        for (const c of arg.slice(1)) {
          if (c !== "i" && c !== "u") {
            return unknownOption("env", `-${c}`);
          }
        }
        if (arg.includes("i"))
          ignoreEnv = true;
      } else if (arg.includes("=") && commandStart === -1) {
        const eqIdx = arg.indexOf("=");
        const name = arg.slice(0, eqIdx);
        const value = arg.slice(eqIdx + 1);
        setVars.set(name, value);
      } else {
        commandStart = i;
        break;
      }
    }
    let newEnv;
    if (ignoreEnv) {
      newEnv = new Map(setVars);
    } else {
      newEnv = new Map(ctx.env);
      for (const name of unsetVars) {
        newEnv.delete(name);
      }
      for (const [name, value] of setVars) {
        newEnv.set(name, value);
      }
    }
    if (commandStart === -1) {
      const lines = [];
      for (const [key, value] of newEnv) {
        lines.push(`${key}=${value}`);
      }
      return {
        stdout: lines.join("\n") + (lines.length > 0 ? "\n" : ""),
        stderr: "",
        exitCode: 0
      };
    }
    if (!ctx.exec) {
      return {
        stdout: "",
        stderr: "env: command execution not supported in this context\n",
        exitCode: 1
      };
    }
    const cmdArgs = args.slice(commandStart);
    return ctx.exec("command", {
      cwd: ctx.cwd,
      env: mapToRecord(newEnv),
      replaceEnv: true,
      stdin: ctx.stdin,
      signal: ctx.signal,
      args: cmdArgs
    });
  }
};
var printenvHelp = {
  name: "printenv",
  summary: "print all or part of environment",
  usage: "printenv [OPTION]... [VARIABLE]...",
  options: ["    --help       display this help and exit"]
};
var printenvCommand = {
  name: "printenv",
  async execute(args, ctx) {
    if (hasHelpFlag(args)) {
      return showHelp(printenvHelp);
    }
    const vars = args.filter((arg) => !arg.startsWith("-"));
    if (vars.length === 0) {
      const lines2 = [];
      for (const [key, value] of ctx.env) {
        lines2.push(`${key}=${value}`);
      }
      return {
        stdout: lines2.join("\n") + (lines2.length > 0 ? "\n" : ""),
        stderr: "",
        exitCode: 0
      };
    }
    const lines = [];
    let exitCode = 0;
    for (const varName of vars) {
      const value = ctx.env.get(varName);
      if (value !== void 0) {
        lines.push(value);
      } else {
        exitCode = 1;
      }
    }
    return {
      stdout: lines.join("\n") + (lines.length > 0 ? "\n" : ""),
      stderr: "",
      exitCode
    };
  }
};
var flagsForFuzzing = {
  name: "env",
  flags: [
    { flag: "-i", type: "boolean" },
    { flag: "-u", type: "value", valueHint: "string" }
  ]
};
var printenvFlagsForFuzzing = {
  name: "printenv",
  flags: []
};

export {
  envCommand,
  printenvCommand,
  flagsForFuzzing,
  printenvFlagsForFuzzing
};
