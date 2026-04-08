import {
  createChecksumCommand
} from "./chunk-T4LD3Q5U.js";

// dist/commands/md5sum/sha256sum.js
var sha256sumCommand = createChecksumCommand("sha256sum", "sha256", "compute SHA256 message digest");
var flagsForFuzzing = {
  name: "sha256sum",
  flags: [{ flag: "-c", type: "boolean" }],
  needsFiles: true
};

export {
  sha256sumCommand,
  flagsForFuzzing
};
