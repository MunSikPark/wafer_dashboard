// src/routes/api/trends/+server.ts
import type { RequestHandler } from '@sveltejs/kit';
import fs from 'node:fs/promises';
import path from 'node:path';

// data_generation.py 와 동일한 기본 경로
const BASE_DIR = 'C:/Users/munsikpark';

// UNIQUE_* CSV 는 첫 컬럼이 test_name 이라고 가정
function parseUniqueList(csv: string): string[] {
  const lines = csv.split(/\r?\n/).filter((l) => l.trim().length > 0);
  if (lines.length <= 1) return [];
  // 첫 줄은 header (test_name)
  return lines
    .slice(1)
    .map((line) => line.split(',')[0]?.trim())
    .filter((name) => !!name);
}

export const GET: RequestHandler = async ({ url }) => {
  const waferId = url.searchParams.get('waferId')?.trim();
  const kind = (url.searchParams.get('kind') ?? 'trend').trim(); // 'trend' | 'series'

  if (!waferId) {
    return new Response(JSON.stringify({ error: 'waferId 가 필요합니다.' }), {
      status: 400
    });
  }

  const fileName =
    kind === 'series' ? 'UNIQUE_SERIES.csv' : 'UNIQUE_TREND.csv';

  const fullPath = path.join(BASE_DIR, waferId, fileName);

  try {
    const text = await fs.readFile(fullPath, 'utf-8');
    const tests = parseUniqueList(text);
    return new Response(
      JSON.stringify({
        waferId,
        kind,
        tests
      }),
      { status: 200 }
    );
  } catch (err: any) {
    console.error('trends API error:', err);
    return new Response(
      JSON.stringify({
        error: `파일을 읽을 수 없습니다: ${fullPath}`
      }),
      { status: 500 }
    );
  }
};
