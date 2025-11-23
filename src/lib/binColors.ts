// binColors.ts
export const BACKGROUND_COLOR = "#e5e7eb"; // bin 0
export const PASS_DOT_COLOR = "#32ff7e";   // fail_bin = "."
export const PASS_N_COLOR = "#0dd9ff";     // fail_bin = "N"

export type Die = {
  fail_bin: any;
  row: number;
  col: number;
};

export type BinLegendItem = {
  code: string;
  label: string;
  count: number;
  color: string;
};

// bin 값을 문자열로 정규화
export function normalizeBin(raw: any): string {
  if (
    raw === null ||
    raw === undefined ||
    raw === "" ||
    raw === 0 ||
    raw === "0"
  ) {
    return "0";
  }
  return String(raw);
}

// 문자열을 기반으로 "랜덤하지만 항상 같은" 색
// 초록 계열(H ≈ 90~160)은 피함
export function generateColorForBin(bin: string): string {
  let hash = 0;
  for (let i = 0; i < bin.length; i++) {
    hash = (hash * 31 + bin.charCodeAt(i)) | 0;
  }
  let hue = ((hash % 360) + 360) % 360;

  if (hue >= 90 && hue <= 160) {
    hue = (hue + 100) % 360;
  }

  return `hsl(${hue}, 80%, 55%)`;
}

// dies에서 legend/색 정보를 한 번에 계산
export function buildBinStats(dies: Die[] | undefined | null): {
  items: BinLegendItem[];
  backgroundCount: number;
  colorMap: Record<string, string>;
} {
  const counts: Record<string, number> = {};
  const colorMap: Record<string, string> = {};

  if (!dies) {
    return { items: [], backgroundCount: 0, colorMap };
  }

  // 카운트 계산
  for (const d of dies) {
    const key = normalizeBin(d?.fail_bin);
    counts[key] = (counts[key] ?? 0) + 1;
  }

  const backgroundCount = counts["0"] ?? 0;

  // 0을 제외한 bin 리스트
  const uniqueBins = Array.from(
    new Set(
      Object.keys(counts).filter((k) => k !== "0")
    )
  );

  const items: BinLegendItem[] = [];

  for (const key of uniqueBins) {
    let color: string;
    if (key === ".") {
      color = PASS_DOT_COLOR;
    } else if (key === "N") {
      color = PASS_N_COLOR;
    } else {
      color = generateColorForBin(key);
    }

    colorMap[key] = color;

    const label =
      key === "."
        ? "PASS (.)"
        : key === "N"
        ? "PASS (N)"
        : key;

    items.push({
      code: key,
      label,
      count: counts[key] ?? 0,
      color
    });
  }

  // 0번 bin 색
  colorMap["0"] = BACKGROUND_COLOR;

  return { items, backgroundCount, colorMap };
}
