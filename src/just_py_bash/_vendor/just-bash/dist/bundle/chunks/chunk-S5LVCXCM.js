import {
  createChecksumCommand
} from "./chunk-T4LD3Q5U.js";

// dist/commands/md5sum/sha1sum.js
var sha1sumCommand = createChecksumCommand("sha1sum", "sha1", "compute SHA1 message digest");
var flagsForFuzzing = {
  name: "sha1sum",
  flags: [{ flag: "-c", type: "boolean" }],
  needsFiles: true
};

export {
  sha1sumCommand,
  flagsForFuzzing
};
