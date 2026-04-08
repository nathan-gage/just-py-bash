import {
  require_papaparse
} from "./chunk-LSNHU7P5.js";
import {
  __toESM
} from "./chunk-KH45J4DC.js";

// dist/commands/xan/csv.js
var import_papaparse = __toESM(require_papaparse(), 1);
function createSafeRow() {
  return /* @__PURE__ */ Object.create(null);
}
function safeSetRow(row, key, value) {
  row[key] = value;
}
function toSafeRow(plainRow) {
  const safe = createSafeRow();
  for (const key of Object.keys(plainRow)) {
    const value = plainRow[key];
    if (typeof value === "string" || typeof value === "number" || typeof value === "boolean" || value === null) {
      safe[key] = value;
    }
  }
  return safe;
}
function parseCsv(input) {
  const result = import_papaparse.default.parse(input.trim(), {
    header: true,
    dynamicTyping: true,
    skipEmptyLines: true
  });
  const safeData = result.data.map((row) => toSafeRow(row));
  return {
    headers: result.meta.fields || [],
    data: safeData
  };
}
function formatCsv(headers, data) {
  if (data.length === 0) {
    return `${headers.join(",")}
`;
  }
  const csv = import_papaparse.default.unparse(data, { columns: headers });
  return `${csv.replace(/\r\n/g, "\n")}
`;
}
async function readCsvInput(args, ctx) {
  const file = args.find((a) => !a.startsWith("-"));
  let input;
  if (!file || file === "-") {
    input = ctx.stdin;
  } else {
    try {
      const path = ctx.fs.resolvePath(ctx.cwd, file);
      input = await ctx.fs.readFile(path);
    } catch {
      return {
        headers: [],
        data: [],
        error: {
          stdout: "",
          stderr: `xan: ${file}: No such file or directory
`,
          exitCode: 1
        }
      };
    }
  }
  const { headers, data } = parseCsv(input);
  return { headers, data };
}

// dist/commands/xan/xan-view.js
async function cmdFlatten(args, ctx) {
  let limit = 0;
  let selectCols = [];
  const fileArgs = [];
  for (let i = 0; i < args.length; i++) {
    const arg = args[i];
    if ((arg === "-l" || arg === "--limit") && i + 1 < args.length) {
      limit = Number.parseInt(args[++i], 10);
    } else if ((arg === "-s" || arg === "--select") && i + 1 < args.length) {
      selectCols = args[++i].split(",");
    } else if (!arg.startsWith("-")) {
      fileArgs.push(arg);
    }
  }
  const { headers, data, error } = await readCsvInput(fileArgs, ctx);
  if (error)
    return error;
  const displayHeaders = selectCols.length > 0 ? selectCols.filter((c) => headers.includes(c)) : headers;
  const rows = limit > 0 ? data.slice(0, limit) : data;
  const maxHeaderWidth = Math.max(...displayHeaders.map((h) => h.length));
  const lines = [];
  const separator = "\u2500".repeat(80);
  for (let i = 0; i < rows.length; i++) {
    const row = rows[i];
    lines.push(`Row n\xB0${i}`);
    lines.push(separator);
    for (const h of displayHeaders) {
      const val = row[h];
      const valStr = val === null || val === void 0 ? "" : String(val);
      lines.push(`${h.padEnd(maxHeaderWidth)} ${valStr}`);
    }
    if (i < rows.length - 1) {
      lines.push("");
    }
  }
  return { stdout: `${lines.join("\n")}
`, stderr: "", exitCode: 0 };
}
async function cmdView(args, ctx) {
  let n = 0;
  const fileArgs = [];
  for (let i = 0; i < args.length; i++) {
    const arg = args[i];
    if (arg === "-n" && i + 1 < args.length) {
      n = Number.parseInt(args[++i], 10);
    } else if (!arg.startsWith("-")) {
      fileArgs.push(arg);
    }
  }
  const { headers, data, error } = await readCsvInput(fileArgs, ctx);
  if (error)
    return error;
  const rows = n > 0 ? data.slice(0, n) : data;
  const widths = headers.map((h) => h.length);
  for (const row of rows) {
    for (let i = 0; i < headers.length; i++) {
      const val = String(row[headers[i]] ?? "");
      widths[i] = Math.max(widths[i], val.length);
    }
  }
  const lines = [];
  const border = "\u2500";
  const sep = "\u2502";
  lines.push(`\u250C${widths.map((w) => border.repeat(w + 2)).join("\u252C")}\u2510`);
  const headerRow = headers.map((h, i) => ` ${h.padEnd(widths[i])} `).join(sep);
  lines.push(`${sep}${headerRow}${sep}`);
  lines.push(`\u251C${widths.map((w) => border.repeat(w + 2)).join("\u253C")}\u2524`);
  for (const row of rows) {
    const dataRow = headers.map((h, i) => ` ${String(row[h] ?? "").padEnd(widths[i])} `).join(sep);
    lines.push(`${sep}${dataRow}${sep}`);
  }
  lines.push(`\u2514${widths.map((w) => border.repeat(w + 2)).join("\u2534")}\u2518`);
  return { stdout: `${lines.join("\n")}
`, stderr: "", exitCode: 0 };
}

export {
  createSafeRow,
  safeSetRow,
  toSafeRow,
  parseCsv,
  formatCsv,
  readCsvInput,
  cmdFlatten,
  cmdView
};
