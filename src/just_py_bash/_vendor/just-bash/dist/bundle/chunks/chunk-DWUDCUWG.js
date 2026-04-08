import {
  DefenseInDepthBox,
  SecurityViolationError
} from "./chunk-R3ZPC4XR.js";

// dist/security/defense-context.js
function assertDefenseContext(requireDefenseContext, component, phase) {
  if (!requireDefenseContext)
    return;
  if (DefenseInDepthBox.isInSandboxedContext())
    return;
  const message = `${component} ${phase} attempted outside defense context`;
  throw new SecurityViolationError(message, {
    timestamp: Date.now(),
    type: "missing_defense_context",
    message,
    path: "DefenseInDepthBox.context",
    stack: new Error().stack,
    executionId: DefenseInDepthBox.getCurrentExecutionId()
  });
}
async function awaitWithDefenseContext(requireDefenseContext, component, phase, op) {
  assertDefenseContext(requireDefenseContext, component, `${phase} (pre-await)`);
  const result = await op();
  assertDefenseContext(requireDefenseContext, component, `${phase} (post-await)`);
  return result;
}
function bindDefenseContextCallback(requireDefenseContext, component, phase, callback) {
  const guarded = ((...args) => {
    assertDefenseContext(requireDefenseContext, component, phase);
    return callback(...args);
  });
  if (!requireDefenseContext) {
    return guarded;
  }
  return DefenseInDepthBox.bindCurrentContext(guarded);
}

export {
  assertDefenseContext,
  awaitWithDefenseContext,
  bindDefenseContextCallback
};
