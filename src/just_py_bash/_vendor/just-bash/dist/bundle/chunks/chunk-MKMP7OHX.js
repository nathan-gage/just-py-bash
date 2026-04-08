// dist/commands/whoami/whoami.js
async function whoamiExecute(_args, _ctx) {
  return { stdout: "user\n", stderr: "", exitCode: 0 };
}
var whoami = {
  name: "whoami",
  execute: whoamiExecute
};
var flagsForFuzzing = {
  name: "whoami",
  flags: []
};

export {
  whoami,
  flagsForFuzzing
};
