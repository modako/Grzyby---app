/**
 * Loads forest cells and the daily weather: cache first (offline), then refresh from
 * GitHub Pages when the cache is stale. Also holds the selected day and species.
 */
import { createContext, ReactNode, useCallback, useContext, useEffect, useMemo, useState } from "react";

import { CELLS_STALE_HOURS, CELLS_URL, DAILY_STALE_HOURS, DAILY_URL } from "../config";
import type { Species } from "../model/params";
import type { Cell, CellProps, Daily } from "../model/types";
import { CacheMeta, readMeta, readText, writeMeta, writeText } from "./cache";

type Status = "loading" | "ready" | "error";

interface DataState {
  status: Status;
  error: string | null;
  /** True when the last refresh failed and cached data is shown. */
  offline: boolean;
  refreshing: boolean;
  cells: Cell[];
  cellById: Map<string, Cell>;
  daily: Daily | null;
  dailyFetchedAt: number | null;
  refresh: (force?: boolean) => Promise<void>;
  day: number;
  setDay: (d: number) => void;
  species: Species | null;
  setSpecies: (s: Species | null) => void;
}

const DataContext = createContext<DataState | null>(null);

const HOUR = 3600 * 1000;

async function download(url: string): Promise<string> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 60000);
  try {
    const res = await fetch(url, { signal: controller.signal, headers: { "Cache-Control": "no-cache" } });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.text();
  } finally {
    clearTimeout(timer);
  }
}

export function parseCells(text: string): Cell[] {
  const fc = JSON.parse(text) as GeoJSON.FeatureCollection<GeoJSON.Polygon, CellProps>;
  return fc.features.map((f) => {
    const ring = f.geometry.coordinates[0] as [number, number][];
    const pts = ring.slice(0, -1);
    const center: [number, number] = [
      pts.reduce((s, p) => s + p[0], 0) / pts.length,
      pts.reduce((s, p) => s + p[1], 0) / pts.length,
    ];
    return { ...f.properties, ring, center };
  });
}

export function DataProvider({ children }: { children: ReactNode }) {
  const [status, setStatus] = useState<Status>("loading");
  const [error, setError] = useState<string | null>(null);
  const [offline, setOffline] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [cells, setCells] = useState<Cell[]>([]);
  const [daily, setDaily] = useState<Daily | null>(null);
  const [meta, setMeta] = useState<CacheMeta>({});
  const [day, setDay] = useState(0);
  const [species, setSpecies] = useState<Species | null>(null);

  const refresh = useCallback(async (force = false) => {
    setRefreshing(true);
    let current = await readMeta();
    const now = Date.now();
    let failed = false;
    try {
      if (force || !current.cellsFetchedAt || now - current.cellsFetchedAt > CELLS_STALE_HOURS * HOUR) {
        const text = await download(CELLS_URL);
        const parsed = parseCells(text);
        writeText("cells.geojson", text);
        current = { ...current, cellsFetchedAt: now };
        setCells(parsed);
      }
      if (force || !current.dailyFetchedAt || now - current.dailyFetchedAt > DAILY_STALE_HOURS * HOUR) {
        const text = await download(DAILY_URL);
        const parsed = JSON.parse(text) as Daily;
        writeText("daily.json", text);
        current = { ...current, dailyFetchedAt: now };
        setDaily(parsed);
      }
      writeMeta(current);
      setMeta(current);
    } catch (e) {
      failed = true;
      setError(e instanceof Error ? e.message : String(e));
    }
    setOffline(failed);
    setRefreshing(false);
    return;
  }, []);

  useEffect(() => {
    (async () => {
      // 1. Cached data first, so the map shows immediately and works without internet.
      const [cellsText, dailyText, cachedMeta] = await Promise.all([
        readText("cells.geojson"),
        readText("daily.json"),
        readMeta(),
      ]);
      let haveCache = false;
      try {
        if (cellsText && dailyText) {
          setCells(parseCells(cellsText));
          setDaily(JSON.parse(dailyText) as Daily);
          setMeta(cachedMeta);
          haveCache = true;
          setStatus("ready");
        }
      } catch {
        haveCache = false;
      }
      // 2. Refresh what is stale.
      await refresh(false);
      setStatus((s) => (s === "ready" || haveCache ? "ready" : "loading"));
    })();
  }, [refresh]);

  // Ready as soon as both datasets exist; error only when there is nothing to show.
  useEffect(() => {
    if (cells.length && daily) setStatus("ready");
    else if (!refreshing && error && !(cells.length && daily)) setStatus("error");
  }, [cells, daily, refreshing, error]);

  const cellById = useMemo(() => new Map(cells.map((c) => [c.id, c])), [cells]);

  const value: DataState = {
    status,
    error,
    offline,
    refreshing,
    cells,
    cellById,
    daily,
    dailyFetchedAt: meta.dailyFetchedAt ?? null,
    refresh,
    day,
    setDay,
    species,
    setSpecies,
  };
  return <DataContext.Provider value={value}>{children}</DataContext.Provider>;
}

export function useData(): DataState {
  const ctx = useContext(DataContext);
  if (!ctx) throw new Error("useData outside DataProvider");
  return ctx;
}
