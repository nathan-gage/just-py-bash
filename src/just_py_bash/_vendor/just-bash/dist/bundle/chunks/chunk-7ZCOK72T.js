// dist/commands/hostname/hostname.js
async function hostnameExecute(_args, _ctx) {
  return { stdout: "localhost\n", stderr: "", exitCode: 0 };
}
var hostname = {
  name: "hostname",
  execute: hostnameExecute
};
var flagsForFuzzing = {
  name: "hostname",
  flags: []
};

export {
  hostname,
  flagsForFuzzing
};
