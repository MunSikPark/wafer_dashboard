// src/routes/api/corr/+server.ts
import type { RequestHandler } from '@sveltejs/kit';
import fs from 'node:fs/promises';
import path from 'node:path';

const BASE_DIR = 'C:/Users/munsikpark';

// 간단 CSV 파서
function parseCsv(text: string) {
  const lines = text.split(/\r?\n/).filter((l) => l.trim().length > 0);
  if (lines.length === 0) return { header: [], rows: [] as any[] };

  const header = lines[0].split(',').map((h) => h.trim());
  const rows = lines.slice(1).map((line) => {
    const cols = line.split(',');
    const obj: any = {};
    header.forEach((h, i) => {
      obj[h] = cols[i]?.trim();
    });
    return obj;
  });

  return { header, rows };
}

// Pearson r
function pearson(xArr: number[], yArr: number[]): number {
  if (xArr.length !== yArr.length) return NaN;
  const n = xArr.length;
  if (n === 0) return NaN;

  let sumX = 0;
  let sumY = 0;
  for (let i = 0; i < n; i++) {
    sumX += xArr[i];
    sumY += yArr[i];
  }
  const mx = sumX / n;
  const my = sumY / n;

  let num = 0;
  let dx = 0;
  let dy = 0;

  for (let i = 0; i < n; i++) {
    const ax = xArr[i] - mx;
    const ay = yArr[i] - my;
    num += ax * ay;
    dx += ax * ax;
    dy += ay * ay;
  }

  const denom = Math.sqrt(dx * dy);
  if (denom === 0) return NaN;

  return num / denom;
}

export const POST: RequestHandler = async ({ request }) => {
  const body = await request.json();
  const waferId = body.waferId?.trim();
  const target = body.target?.trim();
  const kind = (body.kind ?? 'trend').trim(); // 'trend' | 'series'

  if (!waferId || !target) {
    return new Response(
      JSON.stringify({ error: 'waferId, target 둘 다 필요합니다.' }),
      { status: 400 }
    );
  }

  const dataFile =
    kind === 'series' ? 'SERIES_DATA.csv' : 'TREND_DATA.csv';

  const trendPath = path.join(BASE_DIR, waferId, dataFile);

  let csvText: string;
  try {
    csvText = await fs.readFile(trendPath, 'utf-8');
  } catch (err) {
    return new Response(
      JSON.stringify({
        error: `${dataFile} 를 읽을 수 없습니다: ${trendPath}`
      }),
      { status: 500 }
    );
  }

  const { rows } = parseCsv(csvText);
  if (rows.length === 0) {
    return new Response(
      JSON.stringify({ error: '데이터 행이 없습니다.' }),
      { status: 500 }
    );
  }

  // 1) 한 번만 돌면서 test_name -> number[] 맵을 만든다
  const seriesMap = new Map<string, number[]>();

  for (const r of rows as any[]) {
    const name = r.test_name;
    if (!name) continue;

    const v = Number(r.value_raw);
    if (Number.isNaN(v)) continue;

    let arr = seriesMap.get(name);
    if (!arr) {
      arr = [];
      seriesMap.set(name, arr);
    }
    arr.push(v);
  }

  const testNames = Array.from(seriesMap.keys());

  // target 존재 여부 체크
  if (!seriesMap.has(target)) {
    return new Response(
      JSON.stringify({
        error: `target '${target}' 이 ${dataFile} 에 존재하지 않습니다.`
      }),
      { status: 400 }
    );
  }

  const targetVals = seriesMap.get(target)!;
  const results: { name: string; r: number }[] = [];

  // 2) 맵에서 바로 꺼내서 코릴레이션 계산
  for (const [name, vals] of seriesMap.entries()) {
    if (name === target) continue;

    // 길이가 다르면 스킵 (alignment 를 안 맞추고 단순 비교)
    if (vals.length !== targetVals.length) continue;

    const r = pearson(targetVals, vals);
    if (!Number.isNaN(r)) {
      results.push({ name, r });
    }
  }

  // 절댓값 기준으로 정렬
  results.sort((a, b) => Math.abs(b.r) - Math.abs(a.r));

  return new Response(
    JSON.stringify({
      waferId,
      kind,
      target,
      top: results.slice(0, 30)
    }),
    { status: 200 }
  );
};
