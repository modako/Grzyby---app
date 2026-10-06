/** Small file cache in the app's document directory (survives restarts, works offline). */
import { File, Paths } from "expo-file-system";

export interface CacheMeta {
  dailyFetchedAt?: number;
  cellsFetchedAt?: number;
}

const file = (name: string) => new File(Paths.document, name);

export async function readText(name: string): Promise<string | null> {
  const f = file(name);
  return f.exists ? f.text() : null;
}

export function writeText(name: string, text: string): void {
  const f = file(name);
  if (!f.exists) f.create();
  f.write(text);
}

export async function readMeta(): Promise<CacheMeta> {
  const text = await readText("meta.json");
  try {
    return text ? (JSON.parse(text) as CacheMeta) : {};
  } catch {
    return {};
  }
}

export function writeMeta(meta: CacheMeta): void {
  writeText("meta.json", JSON.stringify(meta));
}
