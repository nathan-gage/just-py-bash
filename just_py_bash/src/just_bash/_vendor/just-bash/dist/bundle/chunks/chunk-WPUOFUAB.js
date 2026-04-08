import {
  formatMode
} from "./chunk-Z4P336UH.js";
import {
  parseArgs
} from "./chunk-AP27C34D.js";
import {
  hasHelpFlag,
  showHelp
} from "./chunk-GFRMOA7L.js";

// dist/commands/stat/stat.js
var statHelp = {
  name: "stat",
  summary: "display file or file system status",
  usage: "stat [OPTION]... FILE...",
  options: [
    "-c FORMAT   use the specified FORMAT instead of the default",
    "    --help  display this help and exit"
  ]
};
var argDefs = {
  format: { short: "c", type: "string" }
};
var statCommand = {
  name: "stat",
  async execute(args, ctx) {
    if (hasHelpFlag(args)) {
      return showHelp(statHelp);
    }
    const parsed = parseArgs("stat", args, argDefs);
    if (!parsed.ok)
      return parsed.error;
    const format = parsed.result.flags.format ?? null;
    const files = parsed.result.positional;
    if (files.length === 0) {
      return {
        stdout: "",
        stderr: "stat: missing operand\n",
        exitCode: 1
      };
    }
    let stdout = "";
    let stderr = "";
    let hasError = false;
    for (const file of files) {
      const fullPath = ctx.fs.resolvePath(ctx.cwd, file);
      try {
        const stat = await ctx.fs.stat(fullPath);
        if (format) {
          let output = format;
          const modeOctal = stat.mode.toString(8);
          const modeStr = formatMode(stat.mode, stat.isDirectory);
          output = output.replace(/%n/g, file);
          output = output.replace(/%N/g, `'${file}'`);
          output = output.replace(/%s/g, String(stat.size));
          output = output.replace(/%F/g, stat.isDirectory ? "directory" : "regular file");
          output = output.replace(/%a/g, modeOctal);
          output = output.replace(/%A/g, modeStr);
          output = output.replace(/%u/g, "1000");
          output = output.replace(/%U/g, "user");
          output = output.replace(/%g/g, "1000");
          output = output.replace(/%G/g, "group");
          stdout += `${output}
`;
        } else {
          const modeOctal = stat.mode.toString(8).padStart(4, "0");
          const modeStr = formatMode(stat.mode, stat.isDirectory);
          stdout += `  File: ${file}
`;
          stdout += `  Size: ${stat.size}		Blocks: ${Math.ceil(stat.size / 512)}
`;
          stdout += `Access: (${modeOctal}/${modeStr})
`;
          stdout += `Modify: ${stat.mtime.toISOString()}
`;
        }
      } catch {
        stderr += `stat: cannot stat '${file}': No such file or directory
`;
        hasError = true;
      }
    }
    return { stdout, stderr, exitCode: hasError ? 1 : 0 };
  }
};
var flagsForFuzzing = {
  name: "stat",
  flags: [
    { flag: "-c", type: "value", valueHint: "format" },
    { flag: "-L", type: "boolean" }
  ],
  needsArgs: true
};

export {
  statCommand,
  flagsForFuzzing
};
