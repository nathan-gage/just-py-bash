import {
  shellJoinArgs
} from "./chunk-2PXGQ7LT.js";

// dist/commands/help/help.js
var CATEGORIES = /* @__PURE__ */ new Map([
  [
    "File operations",
    [
      "ls",
      "cat",
      "head",
      "tail",
      "wc",
      "touch",
      "mkdir",
      "rm",
      "cp",
      "mv",
      "ln",
      "chmod",
      "stat",
      "readlink"
    ]
  ],
  [
    "Text processing",
    ["grep", "sed", "awk", "sort", "uniq", "cut", "tr", "tee", "diff"]
  ],
  ["Search", ["find"]],
  ["Navigation & paths", ["pwd", "basename", "dirname", "tree", "du"]],
  [
    "Environment & shell",
    [
      "echo",
      "printf",
      "env",
      "printenv",
      "export",
      "alias",
      "unalias",
      "history",
      "clear",
      "true",
      "false",
      "bash",
      "sh"
    ]
  ],
  ["Data processing", ["xargs", "jq", "base64", "date"]],
  ["Network", ["curl", "html-to-markdown"]]
]);
function formatHelp(commands) {
  const lines = [];
  const commandSet = new Set(commands);
  lines.push("Available commands:\n");
  const uncategorized = [];
  for (const [category, cmds] of CATEGORIES) {
    const available = cmds.filter((c) => commandSet.has(c));
    if (available.length > 0) {
      lines.push(`  ${category}:`);
      lines.push(`    ${available.join(", ")}
`);
      for (const c of available) {
        commandSet.delete(c);
      }
    }
  }
  for (const cmd of commandSet) {
    uncategorized.push(cmd);
  }
  if (uncategorized.length > 0) {
    lines.push("  Other:");
    lines.push(`    ${uncategorized.sort().join(", ")}
`);
  }
  lines.push("Use '<command> --help' for details on a specific command.");
  return `${lines.join("\n")}
`;
}
var helpCommand = {
  name: "help",
  async execute(args, ctx) {
    if (args.includes("--help") || args.includes("-h")) {
      return {
        stdout: `help - display available commands

Usage: help [command]

Options:
  -h, --help    Show this help message

If a command name is provided, shows help for that command.
Otherwise, lists all available commands.
`,
        stderr: "",
        exitCode: 0
      };
    }
    if (args.length > 0 && ctx.exec) {
      const cmdName = args[0];
      return ctx.exec(shellJoinArgs([cmdName]), {
        cwd: ctx.cwd,
        signal: ctx.signal,
        args: ["--help"]
      });
    }
    const commands = ctx.getRegisteredCommands?.() ?? [];
    return {
      stdout: formatHelp(commands),
      stderr: "",
      exitCode: 0
    };
  }
};
var flagsForFuzzing = {
  name: "help",
  flags: []
};

export {
  helpCommand,
  flagsForFuzzing
};
