// dist/commands/duration.js
function parseDuration(arg) {
  const match = arg.match(/^(\d+\.?\d*)(s|m|h|d)?$/);
  if (!match)
    return null;
  const value = parseFloat(match[1]);
  const suffix = match[2] || "s";
  switch (suffix) {
    case "s":
      return value * 1e3;
    case "m":
      return value * 60 * 1e3;
    case "h":
      return value * 60 * 60 * 1e3;
    case "d":
      return value * 24 * 60 * 60 * 1e3;
    default:
      return null;
  }
}

export {
  parseDuration
};
