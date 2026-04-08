// dist/commands/query-engine/safe-object.js
var DANGEROUS_KEYS = /* @__PURE__ */ new Set(["__proto__", "constructor", "prototype"]);
var EXTENDED_DANGEROUS_KEYS = /* @__PURE__ */ new Set([
  ...DANGEROUS_KEYS,
  // Additional properties that could cause issues in specific contexts
  "__defineGetter__",
  "__defineSetter__",
  "__lookupGetter__",
  "__lookupSetter__",
  "hasOwnProperty",
  "isPrototypeOf",
  "propertyIsEnumerable",
  "toLocaleString",
  "toString",
  "valueOf"
]);
function assertSafeObject(obj, caller) {
  if (Array.isArray(obj)) {
    throw new TypeError(`${caller}: expected object, got array`);
  }
  if (Object.getPrototypeOf(obj) !== null) {
    throw new TypeError(`${caller}: expected null-prototype object, got prototypal object`);
  }
}
function isSafeKey(key) {
  return !DANGEROUS_KEYS.has(key);
}
function safeSet(obj, key, value) {
  assertSafeObject(obj, "safeSet");
  if (isSafeKey(key)) {
    obj[key] = value;
  }
}
function safeHasOwn(obj, key) {
  assertSafeObject(obj, "safeHasOwn");
  return Object.hasOwn(obj, key);
}
function sanitizeParsedData(value) {
  const seen = /* @__PURE__ */ new WeakMap();
  const sanitize = (current) => {
    if (current === null || typeof current !== "object")
      return current;
    if (current instanceof Date)
      return current;
    const cached = seen.get(current);
    if (cached !== void 0) {
      return cached;
    }
    if (Array.isArray(current)) {
      const sanitizedArray = [];
      seen.set(current, sanitizedArray);
      for (const item of current) {
        sanitizedArray.push(sanitize(item));
      }
      return sanitizedArray;
    }
    const result = /* @__PURE__ */ Object.create(null);
    seen.set(current, result);
    for (const key of Object.keys(current)) {
      result[key] = sanitize(current[key]);
    }
    return result;
  };
  return sanitize(value);
}
function asQueryRecord(value) {
  if (value !== null && typeof value === "object" && !Array.isArray(value)) {
    return value;
  }
  return null;
}
function nullPrototype(obj) {
  return Object.assign(/* @__PURE__ */ Object.create(null), obj);
}
function nullPrototypeCopy(obj) {
  return Object.assign(/* @__PURE__ */ Object.create(null), obj);
}
function nullPrototypeMerge(...objs) {
  return Object.assign(/* @__PURE__ */ Object.create(null), ...objs);
}

export {
  isSafeKey,
  safeSet,
  safeHasOwn,
  sanitizeParsedData,
  asQueryRecord,
  nullPrototype,
  nullPrototypeCopy,
  nullPrototypeMerge
};
