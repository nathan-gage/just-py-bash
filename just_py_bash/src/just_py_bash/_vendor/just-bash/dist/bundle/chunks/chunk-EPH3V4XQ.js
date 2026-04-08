import {
  parseArgs
} from "./chunk-AP27C34D.js";
import {
  hasHelpFlag,
  showHelp
} from "./chunk-GFRMOA7L.js";

// dist/commands/which/which.js
var whichHelp = {
  name: "which",
  summary: "locate a command",
  usage: "which [-as] program ...",
  options: [
    "-a         List all instances of executables found",
    "-s         No output, just return 0 if found, 1 if not",
    "--help     display this help and exit"
  ]
};
var argDefs = {
  showAll: { short: "a", type: "boolean" },
  silent: { short: "s", type: "boolean" }
};
var whichCommand = {
  name: "which",
  async execute(args, ctx) {
    if (hasHelpFlag(args)) {
      return showHelp(whichHelp);
    }
    const parsed = parseArgs("which", args, argDefs);
    if (!parsed.ok)
      return parsed.error;
    const showAll = parsed.result.flags.showAll;
    const silent = parsed.result.flags.silent;
    const names = parsed.result.positional;
    if (names.length === 0) {
      return { stdout: "", stderr: "", exitCode: 1 };
    }
    const pathEnv = ctx.env.get("PATH") || "/usr/bin:/bin";
    const pathDirs = pathEnv.split(":");
    let stdout = "";
    let allFound = true;
    for (const name of names) {
      let found = false;
      for (const dir of pathDirs) {
        if (!dir)
          continue;
        const fullPath = ctx.fs.resolvePath(dir, name);
        if (await ctx.fs.exists(fullPath)) {
          found = true;
          if (!silent) {
            stdout += `${fullPath}
`;
          }
          if (!showAll) {
            break;
          }
        }
      }
      if (!found) {
        allFound = false;
      }
    }
    return {
      stdout,
      stderr: "",
      exitCode: allFound ? 0 : 1
    };
  }
};
var flagsForFuzzing = {
  name: "which",
  flags: [
    { flag: "-a", type: "boolean" },
    { flag: "-s", type: "boolean" }
  ],
  needsArgs: true
};

export {
  whichCommand,
  flagsForFuzzing
};
