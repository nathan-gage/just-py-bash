// dist/fs/path-utils.js
var MAX_SYMLINK_DEPTH = 40;
var DEFAULT_DIR_MODE = 493;
var DEFAULT_FILE_MODE = 420;
var SYMLINK_MODE = 511;
function normalizePath(path) {
  if (!path || path === "/")
    return "/";
  let normalized = path.endsWith("/") && path !== "/" ? path.slice(0, -1) : path;
  if (!normalized.startsWith("/")) {
    normalized = `/${normalized}`;
  }
  const parts = normalized.split("/").filter((p) => p && p !== ".");
  const resolved = [];
  for (const part of parts) {
    if (part === "..") {
      resolved.pop();
    } else {
      resolved.push(part);
    }
  }
  return `/${resolved.join("/")}` || "/";
}
function validatePath(path, operation) {
  if (path.includes("\0")) {
    throw new Error(`ENOENT: path contains null byte, ${operation} '${path}'`);
  }
}
function dirname(path) {
  const normalized = normalizePath(path);
  if (normalized === "/")
    return "/";
  const lastSlash = normalized.lastIndexOf("/");
  return lastSlash === 0 ? "/" : normalized.slice(0, lastSlash);
}
function resolvePath(base, path) {
  if (path.startsWith("/")) {
    return normalizePath(path);
  }
  const combined = base === "/" ? `/${path}` : `${base}/${path}`;
  return normalizePath(combined);
}
function joinPath(parent, child) {
  return parent === "/" ? `/${child}` : `${parent}/${child}`;
}
function resolveSymlinkTarget(symlinkPath, target) {
  if (target.startsWith("/")) {
    return normalizePath(target);
  }
  const dir = dirname(symlinkPath);
  return normalizePath(joinPath(dir, target));
}

// dist/fs/real-fs-utils.js
import * as fs from "node:fs";
import * as nodePath from "node:path";
function isPathWithinRoot(resolved, canonicalRoot) {
  return resolved === canonicalRoot || resolved.startsWith(`${canonicalRoot}/`);
}
function resolveCanonicalPath(realPath, canonicalRoot) {
  try {
    const resolved = fs.realpathSync(realPath);
    return isPathWithinRoot(resolved, canonicalRoot) ? resolved : null;
  } catch (e) {
    if (e.code === "ENOENT") {
      const parent = nodePath.dirname(realPath);
      if (parent === realPath)
        return null;
      const parentCanon = resolveCanonicalPath(parent, canonicalRoot);
      if (parentCanon === null)
        return null;
      try {
        const leafStat = fs.lstatSync(realPath);
        if (leafStat.isSymbolicLink()) {
          const target = fs.readlinkSync(realPath);
          const resolvedTarget = nodePath.isAbsolute(target) ? target : nodePath.resolve(nodePath.dirname(realPath), target);
          const validatedTarget = resolveCanonicalPath(resolvedTarget, canonicalRoot);
          if (validatedTarget === null) {
            return null;
          }
        }
      } catch {
      }
      return nodePath.join(parentCanon, nodePath.basename(realPath));
    }
    return null;
  }
}
function resolveCanonicalPathNoSymlinks(realPath, root, canonicalRoot) {
  const canonical = resolveCanonicalPath(realPath, canonicalRoot);
  if (canonical === null)
    return null;
  const resolvedReal = nodePath.resolve(realPath);
  const relFromRoot = resolvedReal.slice(root.length);
  const relFromCanonical = canonical.slice(canonicalRoot.length);
  if (relFromRoot !== relFromCanonical) {
    return null;
  }
  try {
    const stat = fs.lstatSync(resolvedReal);
    if (stat.isSymbolicLink()) {
      return null;
    }
  } catch {
  }
  return canonical;
}
function validateRootDirectory(root, fsName) {
  if (!fs.existsSync(root)) {
    throw new Error(`${fsName} root does not exist`);
  }
  const stat = fs.statSync(root);
  if (!stat.isDirectory()) {
    throw new Error(`${fsName} root is not a directory`);
  }
}
function sanitizeSymlinkTarget(rawTarget, canonicalRoot) {
  if (!nodePath.isAbsolute(rawTarget)) {
    return { withinRoot: true, relativePath: rawTarget };
  }
  let resolved;
  try {
    resolved = fs.realpathSync(rawTarget);
  } catch {
    resolved = nodePath.resolve(rawTarget);
  }
  if (isPathWithinRoot(resolved, canonicalRoot)) {
    const relativePath = resolved.slice(canonicalRoot.length) || "/";
    return { withinRoot: true, relativePath };
  }
  return { withinRoot: false, safeName: nodePath.basename(rawTarget) };
}
function sanitizeFsError(e, virtualPath, operation, passthroughPatterns) {
  const err = e;
  if (err.path === void 0) {
    for (const pat of passthroughPatterns) {
      if (err.message?.includes(pat)) {
        throw e;
      }
    }
  }
  const code = err.code || "EIO";
  throw new Error(`${code}: ${operation} '${virtualPath}'`);
}

export {
  MAX_SYMLINK_DEPTH,
  DEFAULT_DIR_MODE,
  DEFAULT_FILE_MODE,
  SYMLINK_MODE,
  normalizePath,
  validatePath,
  dirname,
  resolvePath,
  joinPath,
  resolveSymlinkTarget,
  isPathWithinRoot,
  resolveCanonicalPath,
  resolveCanonicalPathNoSymlinks,
  validateRootDirectory,
  sanitizeSymlinkTarget,
  sanitizeFsError
};
