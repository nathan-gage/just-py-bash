import {
  createChecksumCommand
} from "./chunk-T4LD3Q5U.js";

// dist/commands/md5sum/md5sum.js
var md5sumCommand = createChecksumCommand("md5sum", "md5", "compute MD5 message digest");
var flagsForFuzzing = {
  name: "md5sum",
  flags: [{ flag: "-c", type: "boolean" }],
  needsFiles: true
};

export {
  md5sumCommand,
  flagsForFuzzing
};
