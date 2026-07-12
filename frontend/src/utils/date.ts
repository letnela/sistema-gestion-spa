/**
 * Fecha calendario local en formato YYYY-MM-DD.
 *
 * OJO: `new Date().toISOString().slice(0,10)` usa UTC, no la hora local del
 * navegador. En Perú (UTC-5), pasadas las 7:00 p. m. la fecha en UTC ya es el
 * día siguiente, así que la agenda/formularios podían "saltar" a mañana antes
 * de tiempo. Esta función arma la fecha a partir de los componentes locales
 * del objeto Date en vez de convertir a UTC.
 */
export function localToday(): string {
  const d = new Date();
  const yyyy = d.getFullYear();
  const mm = String(d.getMonth() + 1).padStart(2, '0');
  const dd = String(d.getDate()).padStart(2, '0');
  return `${yyyy}-${mm}-${dd}`;
}

/** Igual que localToday() pero retrocediendo `days` días en el calendario local. */
export function localDaysAgo(days: number): string {
  const d = new Date();
  d.setDate(d.getDate() - days);
  const yyyy = d.getFullYear();
  const mm = String(d.getMonth() + 1).padStart(2, '0');
  const dd = String(d.getDate()).padStart(2, '0');
  return `${yyyy}-${mm}-${dd}`;
}
