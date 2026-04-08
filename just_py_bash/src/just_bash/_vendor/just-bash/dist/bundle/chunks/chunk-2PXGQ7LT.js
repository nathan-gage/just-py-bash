// dist/helpers/shell-quote.js
function shellQuoteArg(arg) {
  return `'${arg.replace(/'/g, "'\\''")}'`;
}
function shellJoinArgs(args) {
  return args.map(shellQuoteArg).join(" ");
}

export {
  shellJoinArgs
};
