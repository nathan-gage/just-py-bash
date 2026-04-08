// dist/commands/format-mode.js
function formatMode(mode, isDirectory) {
  const typeChar = isDirectory ? "d" : "-";
  const perms = [
    mode & 256 ? "r" : "-",
    mode & 128 ? "w" : "-",
    mode & 64 ? "x" : "-",
    mode & 32 ? "r" : "-",
    mode & 16 ? "w" : "-",
    mode & 8 ? "x" : "-",
    mode & 4 ? "r" : "-",
    mode & 2 ? "w" : "-",
    mode & 1 ? "x" : "-"
  ];
  return typeChar + perms.join("");
}

export {
  formatMode
};
