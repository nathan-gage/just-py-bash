// dist/fs/sanitize-error.js
function sanitizeWithUnixPrefixes(message, includeHostRuntimePrefixes, includeFileUrls) {
  if (!message)
    return message;
  let sanitized = message.replace(/\n\s+at\s.*/g, "");
  if (includeFileUrls) {
    sanitized = sanitized.replace(/\bfile:\/\/\/?[^\s'",)}\]:]+/g, "<path>");
  }
  sanitized = sanitized.replace(includeHostRuntimePrefixes ? /(?:\/(?:Users|home|private|var|opt|Library|System|usr|etc|tmp|nix|snap|workspace|root|srv|mnt|app))\b[^\s'",)}\]:]*/g : /(?:\/(?:Users|home|private|var|opt|Library|System|usr|etc|tmp|nix|snap))\b[^\s'",)}\]:]*/g, "<path>");
  sanitized = sanitized.replace(/node:internal\/[^\s'",)}\]:]+/g, "<internal>");
  sanitized = sanitized.replace(/[A-Z]:\\[^\s'",)}\]:]+/g, "<path>");
  if (includeFileUrls) {
    sanitized = sanitized.replace(/\\\\[^\s\\]+\\[^\s'",)}\]:]+/g, "<path>");
  }
  return sanitized;
}
function sanitizeErrorMessage(message) {
  return sanitizeWithUnixPrefixes(message, false, false);
}
function sanitizeHostErrorMessage(message) {
  return sanitizeWithUnixPrefixes(message, true, true);
}

export {
  sanitizeErrorMessage,
  sanitizeHostErrorMessage
};
