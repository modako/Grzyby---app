/**
 * 14-day IG chart with daily rain below (two panels on one date axis instead of a
 * dual y-axis, because IG 0-100 and rain in mm have different scales).
 */
import Svg, { G, Line, Polyline, Rect, Text as SvgText, Circle } from "react-native-svg";

import type { DayIndex } from "../model/forecast";
import { IG_PARAMS } from "../model/params";
import { shortDate } from "./format";
import { colors, igColor } from "./theme";

interface Props {
  width: number;
  series: DayIndex[];
  rain: number[];
  dates: string[];
  uncertainFrom: number;
}

export function IgChart({ width, series, rain, dates, uncertainFrom }: Props) {
  const left = 30;
  const right = 8;
  const igTop = 8;
  const igH = 130;
  const gap = 22;
  const rainH = 46;
  const height = igTop + igH + gap + rainH + 18;
  const n = series.length;
  const step = (width - left - right) / n;
  const x = (d: number) => left + step * d + step / 2;
  const y = (v: number) => igTop + igH - (v / 100) * igH;
  const rainMax = Math.max(5, ...rain);
  const rainTop = igTop + igH + gap;

  return (
    <Svg width={width} height={height} accessibilityLabel="Wykres indeksu na 14 dni i opadu">
      {/* uncertain days */}
      <Rect x={left + step * uncertainFrom} y={igTop} width={step * (n - uncertainFrom)} height={igH}
        fill={colors.surface} />
      <SvgText x={left + step * uncertainFrom + 4} y={igTop + 12} fontSize={11} fill={colors.ink2}>
        niepewne
      </SvgText>
      {/* thresholds */}
      {[IG_PARAMS.yellowMin, IG_PARAMS.greenMin, 100].map((v) => (
        <G key={v}>
          <Line x1={left} x2={width - right} y1={y(v)} y2={y(v)} stroke={colors.line}
            strokeDasharray={v === 100 ? undefined : "4 3"} />
          <SvgText x={left - 4} y={y(v) + 4} fontSize={11} fill={colors.ink2} textAnchor="end">{v}</SvgText>
        </G>
      ))}
      <Line x1={left} x2={width - right} y1={y(0)} y2={y(0)} stroke={colors.ink2} />
      {/* range of uncertain days */}
      {series.map((s, d) =>
        s.high > s.low ? (
          <Rect key={`r${d}`} x={x(d) - 3} y={y(s.high)} width={6} height={Math.max(2, y(s.low) - y(s.high))}
            rx={3} fill={colors.ink2} opacity={0.25} />
        ) : null,
      )}
      <Polyline points={series.map((s, d) => `${x(d)},${y(Math.max(0, s.ig))}`).join(" ")}
        fill="none" stroke={colors.ink} strokeWidth={2} />
      {series.map((s, d) => (
        <Circle key={`p${d}`} cx={x(d)} cy={y(Math.max(0, s.ig))} r={5} fill={igColor[s.color]}
          stroke="#fff" strokeWidth={1.5} />
      ))}
      {/* rain */}
      <SvgText x={left - 4} y={rainTop + 10} fontSize={11} fill={colors.ink2} textAnchor="end">mm</SvgText>
      {rain.map((r, d) => {
        const h = (r / rainMax) * rainH;
        return <Rect key={`b${d}`} x={x(d) - step * 0.3} y={rainTop + rainH - h} width={step * 0.6}
          height={Math.max(h, r > 0 ? 1 : 0)} rx={2} fill={colors.rain} />;
      })}
      <SvgText x={width - right} y={rainTop + 10} fontSize={11} fill={colors.ink2} textAnchor="end">
        {`max ${rainMax.toFixed(0)} mm`}
      </SvgText>
      <Line x1={left} x2={width - right} y1={rainTop + rainH} y2={rainTop + rainH} stroke={colors.ink2} />
      {dates.map((iso, d) =>
        d % 2 === 0 ? (
          <SvgText key={`t${d}`} x={x(d)} y={height - 4} fontSize={11} fill={colors.ink2} textAnchor="middle">
            {d === 0 ? "dziś" : shortDate(iso)}
          </SvgText>
        ) : null,
      )}
    </Svg>
  );
}
