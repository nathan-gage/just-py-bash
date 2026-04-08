import {
  parseArgs
} from "./chunk-AP27C34D.js";
import {
  hasHelpFlag,
  showHelp
} from "./chunk-GFRMOA7L.js";

// dist/commands/gzip/gzip.js
import { constants, gunzipSync, gzipSync } from "node:zlib";
var gzipHelp = {
  name: "gzip",
  summary: "compress or expand files",
  usage: "gzip [OPTION]... [FILE]...",
  description: `Compress FILEs (by default, in-place).

When no FILE is given, or when FILE is -, read from standard input.

With -d, decompress instead.`,
  options: [
    "-c, --stdout      write to standard output, keep original files",
    "-d, --decompress  decompress",
    "-f, --force       force overwrite of output file",
    "-k, --keep        keep (don't delete) input files",
    "-l, --list        list compressed file contents",
    "-n, --no-name     do not save or restore the original name and timestamp",
    "-N, --name        save or restore the original file name and timestamp",
    "-q, --quiet       suppress all warnings",
    "-r, --recursive   operate recursively on directories",
    "-S, --suffix=SUF  use suffix SUF on compressed files (default: .gz)",
    "-t, --test        test compressed file integrity",
    "-v, --verbose     verbose mode",
    "-1, --fast        compress faster",
    "-9, --best        compress better",
    "    --help        display this help and exit"
  ]
};
var gunzipHelp = {
  name: "gunzip",
  summary: "decompress files",
  usage: "gunzip [OPTION]... [FILE]...",
  description: `Decompress FILEs (by default, in-place).

When no FILE is given, or when FILE is -, read from standard input.`,
  options: [
    "-c, --stdout      write to standard output, keep original files",
    "-f, --force       force overwrite of output file",
    "-k, --keep        keep (don't delete) input files",
    "-l, --list        list compressed file contents",
    "-n, --no-name     do not restore the original name and timestamp",
    "-N, --name        restore the original file name and timestamp",
    "-q, --quiet       suppress all warnings",
    "-r, --recursive   operate recursively on directories",
    "-S, --suffix=SUF  use suffix SUF on compressed files (default: .gz)",
    "-t, --test        test compressed file integrity",
    "-v, --verbose     verbose mode",
    "    --help        display this help and exit"
  ]
};
var zcatHelp = {
  name: "zcat",
  summary: "decompress files to stdout",
  usage: "zcat [OPTION]... [FILE]...",
  description: `Decompress FILEs to standard output.

When no FILE is given, or when FILE is -, read from standard input.`,
  options: [
    "-f, --force       force; read compressed data even from a terminal",
    "-l, --list        list compressed file contents",
    "-q, --quiet       suppress all warnings",
    "-S, --suffix=SUF  use suffix SUF on compressed files (default: .gz)",
    "-t, --test        test compressed file integrity",
    "-v, --verbose     verbose mode",
    "    --help        display this help and exit"
  ]
};
var argDefs = {
  stdout: { short: "c", long: "stdout", type: "boolean" },
  toStdout: { long: "to-stdout", type: "boolean" },
  // alias
  decompress: { short: "d", long: "decompress", type: "boolean" },
  uncompress: { long: "uncompress", type: "boolean" },
  // alias
  force: { short: "f", long: "force", type: "boolean" },
  keep: { short: "k", long: "keep", type: "boolean" },
  list: { short: "l", long: "list", type: "boolean" },
  noName: { short: "n", long: "no-name", type: "boolean" },
  name: { short: "N", long: "name", type: "boolean" },
  quiet: { short: "q", long: "quiet", type: "boolean" },
  recursive: { short: "r", long: "recursive", type: "boolean" },
  suffix: {
    short: "S",
    long: "suffix",
    type: "string",
    default: ".gz"
  },
  test: { short: "t", long: "test", type: "boolean" },
  verbose: { short: "v", long: "verbose", type: "boolean" },
  // Compression levels
  fast: { short: "1", long: "fast", type: "boolean" },
  level2: { short: "2", type: "boolean" },
  level3: { short: "3", type: "boolean" },
  level4: { short: "4", type: "boolean" },
  level5: { short: "5", type: "boolean" },
  level6: { short: "6", type: "boolean" },
  level7: { short: "7", type: "boolean" },
  level8: { short: "8", type: "boolean" },
  best: { short: "9", long: "best", type: "boolean" }
};
function getCompressionLevel(flags) {
  if (flags.best)
    return constants.Z_BEST_COMPRESSION;
  if (flags.level8)
    return 8;
  if (flags.level7)
    return 7;
  if (flags.level6)
    return 6;
  if (flags.level5)
    return 5;
  if (flags.level4)
    return 4;
  if (flags.level3)
    return 3;
  if (flags.level2)
    return 2;
  if (flags.fast)
    return constants.Z_BEST_SPEED;
  return constants.Z_DEFAULT_COMPRESSION;
}
function parseGzipHeader(data) {
  if (data.length < 10) {
    return { originalName: null, mtime: null, headerSize: 0 };
  }
  if (data[0] !== 31 || data[1] !== 139) {
    return { originalName: null, mtime: null, headerSize: 0 };
  }
  const flags = data[3];
  const mtime = data[4] | data[5] << 8 | data[6] << 16 | data[7] << 24;
  let offset = 10;
  if (flags & 4) {
    if (offset + 2 > data.length)
      return { originalName: null, mtime: null, headerSize: 0 };
    const xlen = data[offset] | data[offset + 1] << 8;
    offset += 2 + xlen;
  }
  let originalName = null;
  if (flags & 8) {
    const nameStart = offset;
    while (offset < data.length && data[offset] !== 0) {
      offset++;
    }
    if (offset < data.length) {
      originalName = new TextDecoder().decode(data.slice(nameStart, offset));
      offset++;
    }
  }
  if (flags & 16) {
    while (offset < data.length && data[offset] !== 0) {
      offset++;
    }
    offset++;
  }
  if (flags & 2) {
    offset += 2;
  }
  return {
    originalName,
    mtime: mtime > 0 ? new Date(mtime * 1e3) : null,
    headerSize: offset
  };
}
function getUncompressedSize(data) {
  if (data.length < 4)
    return 0;
  const len = data.length;
  return data[len - 4] | data[len - 3] << 8 | data[len - 2] << 16 | data[len - 1] << 24;
}
function isGzip(data) {
  return data.length >= 2 && data[0] === 31 && data[1] === 139;
}
function toBinaryString(data) {
  return Buffer.from(data).toString("latin1");
}
function getMaxDecompressedSize(ctx) {
  return ctx.limits?.maxOutputSize ?? 0;
}
function gunzipWithLimit(inputData, maxDecompressedSize) {
  if (maxDecompressedSize > 0) {
    const advertisedSize = getUncompressedSize(inputData);
    if (advertisedSize > maxDecompressedSize) {
      throw new Error(`decompressed data exceeds limit (${maxDecompressedSize} bytes)`);
    }
    return gunzipSync(inputData, {
      maxOutputLength: maxDecompressedSize
    });
  }
  return gunzipSync(inputData);
}
async function processFile(ctx, file, flags, cmdName, decompress, toStdout) {
  const suffix = flags.suffix;
  let inputPath;
  let outputPath;
  let inputData;
  const maxDecompressedSize = getMaxDecompressedSize(ctx);
  if (file === "-" || file === "") {
    inputData = Uint8Array.from(ctx.stdin, (c) => c.charCodeAt(0));
    if (decompress) {
      if (!isGzip(inputData)) {
        if (!flags.quiet) {
          return {
            stdout: "",
            stderr: `${cmdName}: stdin: not in gzip format
`,
            exitCode: 1
          };
        }
        return { stdout: "", stderr: "", exitCode: 1 };
      }
      try {
        const decompressed = gunzipWithLimit(inputData, maxDecompressedSize);
        return {
          stdout: toBinaryString(decompressed),
          stderr: "",
          exitCode: 0
        };
      } catch (e) {
        const msg = e instanceof Error ? e.message : "unknown error";
        return {
          stdout: "",
          stderr: `${cmdName}: stdin: ${msg}
`,
          exitCode: 1
        };
      }
    } else {
      const level = getCompressionLevel(flags);
      const compressed = gzipSync(inputData, { level });
      return {
        stdout: toBinaryString(compressed),
        stderr: "",
        exitCode: 0
      };
    }
  }
  inputPath = ctx.fs.resolvePath(ctx.cwd, file);
  try {
    const stat = await ctx.fs.stat(inputPath);
    if (stat.isDirectory) {
      if (flags.recursive) {
        return await processDirectory(ctx, inputPath, flags, cmdName, decompress, toStdout);
      }
      if (!flags.quiet) {
        return {
          stdout: "",
          stderr: `${cmdName}: ${file}: is a directory -- ignored
`,
          exitCode: 1
        };
      }
      return { stdout: "", stderr: "", exitCode: 1 };
    }
  } catch {
    return {
      stdout: "",
      stderr: `${cmdName}: ${file}: No such file or directory
`,
      exitCode: 1
    };
  }
  try {
    inputData = await ctx.fs.readFileBuffer(inputPath);
  } catch {
    return {
      stdout: "",
      stderr: `${cmdName}: ${file}: No such file or directory
`,
      exitCode: 1
    };
  }
  if (decompress) {
    if (!file.endsWith(suffix)) {
      if (!flags.quiet) {
        return {
          stdout: "",
          stderr: `${cmdName}: ${file}: unknown suffix -- ignored
`,
          exitCode: 1
        };
      }
      return { stdout: "", stderr: "", exitCode: 1 };
    }
    if (!isGzip(inputData)) {
      if (!flags.quiet) {
        return {
          stdout: "",
          stderr: `${cmdName}: ${file}: not in gzip format
`,
          exitCode: 1
        };
      }
      return { stdout: "", stderr: "", exitCode: 1 };
    }
    let decompressed;
    try {
      decompressed = gunzipWithLimit(inputData, maxDecompressedSize);
    } catch (e) {
      const msg = e instanceof Error ? e.message : "unknown error";
      return {
        stdout: "",
        stderr: `${cmdName}: ${file}: ${msg}
`,
        exitCode: 1
      };
    }
    if (toStdout) {
      return {
        stdout: toBinaryString(decompressed),
        stderr: "",
        exitCode: 0
      };
    }
    if (flags.name) {
      const header = parseGzipHeader(inputData);
      if (header.originalName) {
        outputPath = ctx.fs.resolvePath(ctx.cwd, header.originalName);
      } else {
        outputPath = inputPath.slice(0, -suffix.length);
      }
    } else {
      outputPath = inputPath.slice(0, -suffix.length);
    }
    if (!flags.force) {
      try {
        await ctx.fs.stat(outputPath);
        return {
          stdout: "",
          stderr: `${cmdName}: ${outputPath} already exists; not overwritten
`,
          exitCode: 1
        };
      } catch {
      }
    }
    await ctx.fs.writeFile(outputPath, decompressed);
    if (!flags.keep && !toStdout) {
      await ctx.fs.rm(inputPath);
    }
    if (flags.verbose) {
      const ratio = inputData.length > 0 ? ((1 - inputData.length / decompressed.length) * 100).toFixed(1) : "0.0";
      return {
        stdout: "",
        stderr: `${file}:	${ratio}% -- replaced with ${outputPath.split("/").pop()}
`,
        exitCode: 0
      };
    }
    return { stdout: "", stderr: "", exitCode: 0 };
  } else {
    if (file.endsWith(suffix)) {
      if (!flags.quiet) {
        return {
          stdout: "",
          stderr: `${cmdName}: ${file} already has ${suffix} suffix -- unchanged
`,
          exitCode: 1
        };
      }
      return { stdout: "", stderr: "", exitCode: 1 };
    }
    const level = getCompressionLevel(flags);
    let compressed;
    try {
      compressed = gzipSync(inputData, { level });
    } catch (e) {
      const msg = e instanceof Error ? e.message : "unknown error";
      return {
        stdout: "",
        stderr: `${cmdName}: ${file}: ${msg}
`,
        exitCode: 1
      };
    }
    if (toStdout) {
      return {
        stdout: toBinaryString(compressed),
        stderr: "",
        exitCode: 0
      };
    }
    outputPath = inputPath + suffix;
    if (!flags.force) {
      try {
        await ctx.fs.stat(outputPath);
        return {
          stdout: "",
          stderr: `${cmdName}: ${outputPath} already exists; not overwritten
`,
          exitCode: 1
        };
      } catch {
      }
    }
    await ctx.fs.writeFile(outputPath, compressed);
    if (!flags.keep && !toStdout) {
      await ctx.fs.rm(inputPath);
    }
    if (flags.verbose) {
      const ratio = inputData.length > 0 ? ((1 - compressed.length / inputData.length) * 100).toFixed(1) : "0.0";
      return {
        stdout: "",
        stderr: `${file}:	${ratio}% -- replaced with ${outputPath.split("/").pop()}
`,
        exitCode: 0
      };
    }
    return { stdout: "", stderr: "", exitCode: 0 };
  }
}
async function processDirectory(ctx, dirPath, flags, cmdName, decompress, toStdout) {
  const entries = await ctx.fs.readdir(dirPath);
  let stdout = "";
  let stderr = "";
  let exitCode = 0;
  for (const entry of entries) {
    const entryPath = ctx.fs.resolvePath(dirPath, entry);
    const stat = await ctx.fs.stat(entryPath);
    if (stat.isDirectory) {
      const result = await processDirectory(ctx, entryPath, flags, cmdName, decompress, toStdout);
      stdout += result.stdout;
      stderr += result.stderr;
      if (result.exitCode !== 0)
        exitCode = result.exitCode;
    } else if (stat.isFile) {
      const suffix = flags.suffix;
      if (decompress && !entry.endsWith(suffix))
        continue;
      if (!decompress && entry.endsWith(suffix))
        continue;
      const relativePath = entryPath.startsWith(`${ctx.cwd}/`) ? entryPath.slice(ctx.cwd.length + 1) : entryPath;
      const result = await processFile(ctx, relativePath, flags, cmdName, decompress, toStdout);
      stdout += result.stdout;
      stderr += result.stderr;
      if (result.exitCode !== 0)
        exitCode = result.exitCode;
    }
  }
  return { stdout, stderr, exitCode };
}
async function listFile(ctx, file, flags, cmdName) {
  let inputData;
  if (file === "-" || file === "") {
    inputData = Uint8Array.from(ctx.stdin, (c) => c.charCodeAt(0));
  } else {
    const inputPath = ctx.fs.resolvePath(ctx.cwd, file);
    try {
      inputData = await ctx.fs.readFileBuffer(inputPath);
    } catch {
      return {
        stdout: "",
        stderr: `${cmdName}: ${file}: No such file or directory
`,
        exitCode: 1
      };
    }
  }
  if (!isGzip(inputData)) {
    if (!flags.quiet) {
      return {
        stdout: "",
        stderr: `${cmdName}: ${file}: not in gzip format
`,
        exitCode: 1
      };
    }
    return { stdout: "", stderr: "", exitCode: 1 };
  }
  const compressed = inputData.length;
  const uncompressed = getUncompressedSize(inputData);
  const ratio = uncompressed > 0 ? ((1 - compressed / uncompressed) * 100).toFixed(1) : "0.0";
  const header = parseGzipHeader(inputData);
  const name = header.originalName || (file === "-" ? "" : file.replace(/\.gz$/, ""));
  const line = `${compressed.toString().padStart(10)} ${uncompressed.toString().padStart(10)} ${ratio.padStart(5)}% ${name}
`;
  return { stdout: line, stderr: "", exitCode: 0 };
}
async function testFile(ctx, file, flags, cmdName) {
  let inputData;
  if (file === "-" || file === "") {
    inputData = Uint8Array.from(ctx.stdin, (c) => c.charCodeAt(0));
  } else {
    const inputPath = ctx.fs.resolvePath(ctx.cwd, file);
    try {
      inputData = await ctx.fs.readFileBuffer(inputPath);
    } catch {
      return {
        stdout: "",
        stderr: `${cmdName}: ${file}: No such file or directory
`,
        exitCode: 1
      };
    }
  }
  if (!isGzip(inputData)) {
    if (!flags.quiet) {
      return {
        stdout: "",
        stderr: `${cmdName}: ${file}: not in gzip format
`,
        exitCode: 1
      };
    }
    return { stdout: "", stderr: "", exitCode: 1 };
  }
  try {
    gunzipWithLimit(inputData, getMaxDecompressedSize(ctx));
    if (flags.verbose) {
      return { stdout: "", stderr: `${file}:	OK
`, exitCode: 0 };
    }
    return { stdout: "", stderr: "", exitCode: 0 };
  } catch (e) {
    const msg = e instanceof Error ? e.message : "invalid";
    return {
      stdout: "",
      stderr: `${cmdName}: ${file}: ${msg}
`,
      exitCode: 1
    };
  }
}
async function executeGzip(args, ctx, cmdName) {
  const help = cmdName === "zcat" ? zcatHelp : cmdName === "gunzip" ? gunzipHelp : gzipHelp;
  if (hasHelpFlag(args)) {
    return showHelp(help);
  }
  const parsed = parseArgs(cmdName, args, argDefs);
  if (!parsed.ok) {
    if (parsed.error.stderr.includes("unrecognized option")) {
      return parsed.error;
    }
    return parsed.error;
  }
  const flags = parsed.result.flags;
  let files = parsed.result.positional;
  const decompress = cmdName === "gunzip" || cmdName === "zcat" || flags.decompress || flags.uncompress;
  const toStdout = cmdName === "zcat" || flags.stdout || flags.toStdout;
  if (flags.list) {
    if (files.length === 0)
      files = ["-"];
    let stdout2 = "  compressed uncompressed  ratio uncompressed_name\n";
    let stderr2 = "";
    let exitCode2 = 0;
    for (const file of files) {
      const result = await listFile(ctx, file, flags, cmdName);
      stdout2 += result.stdout;
      stderr2 += result.stderr;
      if (result.exitCode !== 0)
        exitCode2 = result.exitCode;
    }
    return { stdout: stdout2, stderr: stderr2, exitCode: exitCode2 };
  }
  if (flags.test) {
    if (files.length === 0)
      files = ["-"];
    let stdout2 = "";
    let stderr2 = "";
    let exitCode2 = 0;
    for (const file of files) {
      const result = await testFile(ctx, file, flags, cmdName);
      stdout2 += result.stdout;
      stderr2 += result.stderr;
      if (result.exitCode !== 0)
        exitCode2 = result.exitCode;
    }
    return { stdout: stdout2, stderr: stderr2, exitCode: exitCode2 };
  }
  if (files.length === 0) {
    files = ["-"];
  }
  let stdout = "";
  let stderr = "";
  let exitCode = 0;
  for (const file of files) {
    const result = await processFile(ctx, file, flags, cmdName, decompress, toStdout);
    stdout += result.stdout;
    stderr += result.stderr;
    if (result.exitCode !== 0)
      exitCode = result.exitCode;
  }
  return { stdout, stderr, exitCode };
}
var gzipCommand = {
  name: "gzip",
  async execute(args, ctx) {
    const result = await executeGzip(args, ctx, "gzip");
    return { ...result, stdoutEncoding: "binary" };
  }
};
var gunzipCommand = {
  name: "gunzip",
  async execute(args, ctx) {
    const result = await executeGzip(args, ctx, "gunzip");
    return { ...result, stdoutEncoding: "binary" };
  }
};
var zcatCommand = {
  name: "zcat",
  async execute(args, ctx) {
    const result = await executeGzip(args, ctx, "zcat");
    return { ...result, stdoutEncoding: "binary" };
  }
};
var flagsForFuzzing = {
  name: "gzip",
  flags: [
    { flag: "-c", type: "boolean" },
    { flag: "-d", type: "boolean" },
    { flag: "-f", type: "boolean" },
    { flag: "-k", type: "boolean" },
    { flag: "-l", type: "boolean" },
    { flag: "-n", type: "boolean" },
    { flag: "-q", type: "boolean" },
    { flag: "-r", type: "boolean" },
    { flag: "-t", type: "boolean" },
    { flag: "-v", type: "boolean" },
    { flag: "-1", type: "boolean" },
    { flag: "-9", type: "boolean" }
  ],
  stdinType: "binary",
  needsFiles: true
};
var gunzipFlagsForFuzzing = {
  name: "gunzip",
  flags: [
    { flag: "-c", type: "boolean" },
    { flag: "-f", type: "boolean" },
    { flag: "-k", type: "boolean" },
    { flag: "-q", type: "boolean" },
    { flag: "-v", type: "boolean" }
  ],
  stdinType: "binary",
  needsFiles: true
};
var zcatFlagsForFuzzing = {
  name: "zcat",
  flags: [
    { flag: "-f", type: "boolean" },
    { flag: "-q", type: "boolean" },
    { flag: "-v", type: "boolean" }
  ],
  stdinType: "binary",
  needsFiles: true
};

export {
  gzipCommand,
  gunzipCommand,
  zcatCommand,
  flagsForFuzzing,
  gunzipFlagsForFuzzing,
  zcatFlagsForFuzzing
};
