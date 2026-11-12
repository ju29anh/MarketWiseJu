/** Escape quotes/newlines and neutralize spreadsheet formula injection on export. */
export function csvCell(value: unknown): string {
  let text = String(value ?? '');
  if (!(typeof value === 'number' && Number.isFinite(value)) && /^[\s]*[=+@-]/.test(text)) text = `'${text}`;
  return `"${text.replace(/"/g, '""')}"`;
}
