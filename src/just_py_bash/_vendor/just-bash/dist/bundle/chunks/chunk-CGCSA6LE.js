// dist/commands/true/true.js
var trueCommand = {
  name: "true",
  async execute() {
    return { stdout: "", stderr: "", exitCode: 0 };
  }
};
var falseCommand = {
  name: "false",
  async execute() {
    return { stdout: "", stderr: "", exitCode: 1 };
  }
};
var flagsForFuzzing = {
  name: "true",
  flags: []
};
var falseFlagsForFuzzing = {
  name: "false",
  flags: []
};

export {
  trueCommand,
  falseCommand,
  flagsForFuzzing,
  falseFlagsForFuzzing
};
