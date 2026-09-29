export function displayValue(value: string | number | null | undefined): string {
  return value === null || value === undefined || value === "" ? "Not reported" : String(value);
}

export function formatResolution(value: number | null): string {
  return value === null ? "Not reported" : `${value.toLocaleString()} Å`;
}

export function formatDate(value: string | null): string {
  if (!value) return "Not reported";
  const date = new Date(value);
  return Number.isNaN(date.getTime())
    ? value
    : new Intl.DateTimeFormat("en", { dateStyle: "medium" }).format(date);
}

export function joinOrUnavailable(values: string[]): string {
  return values.length > 0 ? values.join(", ") : "Not reported";
}
