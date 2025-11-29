import type { RequestHandler } from '@sveltejs/kit';
import { execFile } from 'node:child_process';
import { promisify } from 'node:util';

const execFileAsync = promisify(execFile);

// 필요하면 'py' 로 바꿔도 됨 (윈도우에서 어떤 명령이 되는지에 따라)
const PYTHON_CMD = 'python';

// 실제 data_generation.py 위치로 수정
const SCRIPT_PATH = 'C:/Users/munsikpark/wafer_dashboard/src/python/data_generation.py';

export const POST: RequestHandler = async ({ request }) => {
  const body = await request.json();
  const waferIdsInput = (body.waferIds ?? []) as string[];

  // 공백 제거 + 중복 제거 + 최대 10개
  const waferIds = [...new Set(
    waferIdsInput
      .map((s) => (s ?? '').trim())
      .filter(Boolean)
  )].slice(0, 10);

  if (waferIds.length === 0) {
    return new Response(
      JSON.stringify({ error: 'waferIds 가 비어 있습니다.' }),
      { status: 400 }
    );
  }

  try {
    const { stdout, stderr } = await execFileAsync(
      PYTHON_CMD,
      [SCRIPT_PATH, ...waferIds],
      { windowsHide: true }
    );

    return new Response(
      JSON.stringify({
        ok: true,
        waferIds,
        stdout,
        stderr
      }),
      { status: 200 }
    );
  } catch (err: any) {
    console.error('generate-data error:', err);
    return new Response(
      JSON.stringify({
        error: String(err?.message ?? err),
      }),
      { status: 500 }
    );
  }
};
