import {
  DefenseInDepthBox
} from "./chunk-R3ZPC4XR.js";

// dist/timers.js
var nativeSetTimeout = globalThis.setTimeout.bind(globalThis);
var nativeClearTimeout = globalThis.clearTimeout.bind(globalThis);
var nativeSetInterval = globalThis.setInterval.bind(globalThis);
var nativeClearInterval = globalThis.clearInterval.bind(globalThis);
function bindTimerCallback(callback) {
  if (typeof callback !== "function")
    return callback;
  return DefenseInDepthBox.bindCurrentContext(callback);
}
var _setTimeout = ((callback, delay, ...args) => {
  return nativeSetTimeout(bindTimerCallback(callback), delay, ...args);
});
var _clearTimeout = nativeClearTimeout;

export {
  _setTimeout,
  _clearTimeout
};
