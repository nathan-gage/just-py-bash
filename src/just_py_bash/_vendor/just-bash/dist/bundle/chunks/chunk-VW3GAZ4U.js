import {
  createUserRegex
} from "./chunk-PXYGJXWK.js";

// dist/utils/glob.js
var GLOB_CACHE_MAX = 2048;
var globRegexCache = /* @__PURE__ */ new Map();
function matchGlob(name, pattern, options) {
  const opts = typeof options === "boolean" ? { ignoreCase: options } : options ?? {};
  let cleanPattern = pattern;
  if (opts.stripQuotes) {
    if (cleanPattern.startsWith('"') && cleanPattern.endsWith('"') || cleanPattern.startsWith("'") && cleanPattern.endsWith("'")) {
      cleanPattern = cleanPattern.slice(1, -1);
    }
  }
  const cacheKey = opts.ignoreCase ? `i:${cleanPattern}` : cleanPattern;
  let re = globRegexCache.get(cacheKey);
  if (!re) {
    re = globToRegex(cleanPattern, opts.ignoreCase);
    if (globRegexCache.size >= GLOB_CACHE_MAX) {
      const oldest = globRegexCache.keys().next().value;
      if (oldest !== void 0)
        globRegexCache.delete(oldest);
    }
    globRegexCache.set(cacheKey, re);
  }
  return re.test(name);
}
function globToRegex(pattern, ignoreCase) {
  let regex = "^";
  for (let i = 0; i < pattern.length; i++) {
    const c = pattern[i];
    if (c === "*") {
      regex += ".*";
    } else if (c === "?") {
      regex += ".";
    } else if (c === "[") {
      let j = i + 1;
      while (j < pattern.length && pattern[j] !== "]")
        j++;
      regex += pattern.slice(i, j + 1);
      i = j;
    } else if (c === "." || c === "+" || c === "^" || c === "$" || c === "{" || c === "}" || c === "(" || c === ")" || c === "|" || c === "\\") {
      regex += `\\${c}`;
    } else {
      regex += c;
    }
  }
  regex += "$";
  return createUserRegex(regex, ignoreCase ? "i" : "");
}

export {
  matchGlob
};
