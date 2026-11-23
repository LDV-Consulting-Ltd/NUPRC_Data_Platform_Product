export function errorMessage(error: unknown) {
  if (error instanceof Error && error.message) return error.message;
  return "The request failed.";
}

export function permissionDenied(error: unknown) {
  return /401|403|forbidden|unauthorized/i.test(errorMessage(error));
}
