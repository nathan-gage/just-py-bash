// dist/interpreter/helpers/errors.js
function getErrorMessage(error) {
  return error instanceof Error ? error.message : String(error);
}

export {
  getErrorMessage
};
