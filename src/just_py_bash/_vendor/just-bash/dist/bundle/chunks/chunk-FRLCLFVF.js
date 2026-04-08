// dist/security/trusted-globals.js
var _SharedArrayBuffer = globalThis.SharedArrayBuffer;
var _Atomics = globalThis.Atomics;
var _performanceNow = performance.now.bind(performance);
var _Headers = globalThis.Headers;

export {
  _SharedArrayBuffer,
  _Atomics,
  _performanceNow,
  _Headers
};
