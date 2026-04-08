// dist/helpers/env.js
function mapToRecord(env) {
  return Object.assign(/* @__PURE__ */ Object.create(null), Object.fromEntries(env));
}
function mapToRecordWithExtras(env, extra) {
  return Object.assign(/* @__PURE__ */ Object.create(null), Object.fromEntries(env), extra);
}
function mergeToNullPrototype(...objects) {
  return Object.assign(/* @__PURE__ */ Object.create(null), ...objects);
}

export {
  mapToRecord,
  mapToRecordWithExtras,
  mergeToNullPrototype
};
