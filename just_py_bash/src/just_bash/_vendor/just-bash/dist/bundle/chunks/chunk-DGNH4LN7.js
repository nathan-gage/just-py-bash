import {
  readFiles
} from "./chunk-JBW3RTLA.js";
import {
  parseArgs
} from "./chunk-AP27C34D.js";
import {
  hasHelpFlag,
  showHelp
} from "./chunk-GFRMOA7L.js";

// dist/commands/cat/cat.js
var catHelp = {
  name: "cat",
  summary: "concatenate files and print on the standard output",
  usage: "cat [OPTION]... [FILE]...",
  options: [
    "-n, --number           number all output lines",
    "    --help             display this help and exit"
  ]
};
var argDefs = {
  number: { short: "n", long: "number", type: "boolean" }
};
var catCommand = {
  name: "cat",
  async execute(args, ctx) {
    if (hasHelpFlag(args)) {
      return showHelp(catHelp);
    }
    const parsed = parseArgs("cat", args, argDefs);
    if (!parsed.ok)
      return parsed.error;
    const showLineNumbers = parsed.result.flags.number;
    const files = parsed.result.positional;
    const readResult = await readFiles(ctx, files, {
      cmdName: "cat",
      allowStdinMarker: true,
      stopOnError: false
    });
    let stdout = "";
    let lineNumber = 1;
    for (const { content } of readResult.files) {
      if (showLineNumbers) {
        const result = addLineNumbers(content, lineNumber);
        stdout += result.content;
        lineNumber = result.nextLineNumber;
      } else {
        stdout += content;
      }
    }
    const isReadingFiles = files.length > 0 && files.some((f) => f !== "-");
    return {
      stdout,
      stderr: readResult.stderr,
      exitCode: readResult.exitCode,
      // @banned-pattern-ignore: spread into static result keys, no user-controlled properties
      ...isReadingFiles ? { stdoutEncoding: "binary" } : {}
    };
  }
};
function addLineNumbers(content, startLine) {
  const lines = content.split("\n");
  const hasTrailingNewline = content.endsWith("\n");
  const linesToNumber = hasTrailingNewline ? lines.slice(0, -1) : lines;
  const numbered = linesToNumber.map((line, i) => {
    const num = String(startLine + i).padStart(6, " ");
    return `${num}	${line}`;
  });
  return {
    content: numbered.join("\n") + (hasTrailingNewline ? "\n" : ""),
    nextLineNumber: startLine + linesToNumber.length
  };
}
var flagsForFuzzing = {
  name: "cat",
  flags: [
    { flag: "-n", type: "boolean" },
    { flag: "-A", type: "boolean" },
    { flag: "-b", type: "boolean" },
    { flag: "-s", type: "boolean" },
    { flag: "-v", type: "boolean" },
    { flag: "-e", type: "boolean" },
    { flag: "-t", type: "boolean" }
  ],
  stdinType: "text",
  needsFiles: true
};

export {
  catCommand,
  flagsForFuzzing
};
