<script lang="ts">
  import WaferLegend from "./WaferLegend.svelte";
  import {
    BACKGROUND_COLOR,
    buildBinStats,
    normalizeBin,
    type Die
  } from "../lib/binColors";

  export let wafer: any;

  const PANEL_SIZE = 640;

  // Legend 인터랙션 상태
  let hoverBin: string | null = null;
  let activeBin: string | null = null;          // ★ 추가
  let sortOrder: "asc" | "desc" = "desc";

  // row/col 정보
  $: rowMin = wafer ? wafer.row_min : 0;
  $: rowMax = wafer ? wafer.row_max : -1;
  $: colMin = wafer ? wafer.col_min : 0;
  $: colMax = wafer ? wafer.col_max : -1;

  $: rowCount = rowMax - rowMin + 1;
  $: colCount = colMax - colMin + 1;

  // 셀 크기(px)
  $: cellW = PANEL_SIZE / (colCount || 1);
  $: cellH = PANEL_SIZE / (rowCount || 1);

  const centerX = PANEL_SIZE / 2;
  const centerY = PANEL_SIZE / 2;

  // 원 반지름
  $: radius = PANEL_SIZE / 2 - Math.max(cellW, cellH) * 0.7;

  // 원 안에 들어오는 다이
  $: visibleDies =
    wafer && wafer.dies
      ? (wafer.dies as Die[]).filter((die) => {
          const col = die.col;
          const row = die.row;

          const xCenter = (col - colMin + 0.5) * cellW;
          const yCenter = (rowMax - row + 0.5) * cellH;

          const dx = xCenter - centerX;
          const dy = yCenter - centerY;

          return dx * dx + dy * dy <= radius * radius;
        })
      : [];

  // bin 통계 / 색 계산
  $: binStats = buildBinStats(wafer?.dies as Die[] | undefined);
  $: legendItems = binStats.items;
  $: backgroundCount = binStats.backgroundCount;
  $: binColorMap = binStats.colorMap;

  function getBinBaseColor(key: string): string {
    return binColorMap[key] ?? BACKGROUND_COLOR;
  }

  function getRenderColor(
    die: Die,
    active: string | null,
    hover: string | null
  ): string {
    const key = normalizeBin(die?.fail_bin);

    // 1) activeBin 이 설정돼 있으면: 그 bin만 색, 나머지 전부 background
    if (active) {
      return key === active ? getBinBaseColor(key) : BACKGROUND_COLOR;
    }

    // 2) activeBin 없고 hoverBin만 있을 때: hover된 bin만 색
    if (hover) {
      return key === hover ? getBinBaseColor(key) : BACKGROUND_COLOR;
    }

    // 3) 아무것도 없으면 전체 기본 색
    return getBinBaseColor(key);
  }


  function getRenderOpacity(die: Die): number {
    // 지금은 색으로만 구분하니 모두 1 유지
    return 1;
  }
</script>

{#if !wafer}
  <div class="no-wafer">No wafer data.</div>
{:else}
  <div class="wafer-page-root">
    <div
      class="stack-card"
      style={`width: ${PANEL_SIZE + 230}px;`}
    >
      <div class="card-title">
        Wafer {wafer.wafer}
        <span class="card-title-sep">·</span>
        Lot {wafer.lot}
      </div>

      <div class="card-body-row">
        <!-- 웨이퍼 SVG -->
        <div
          class="wafer-svg-wrapper"
          style={`width:${PANEL_SIZE + 40}px; height:${PANEL_SIZE + 40}px;`}
        >
          <svg
            width={PANEL_SIZE + 40}
            height={PANEL_SIZE + 40}
            viewBox={`0 0 ${PANEL_SIZE + 40} ${PANEL_SIZE + 40}`}
          >
            <rect
              x="0"
              y="0"
              width={PANEL_SIZE + 40}
              height={PANEL_SIZE + 40}
              fill="#ffffff"
            />

            <circle
              cx={(PANEL_SIZE + 40) / 2}
              cy={(PANEL_SIZE + 40) / 2}
              r={(PANEL_SIZE / 2) + 10}
              fill="#ffffff"
              stroke="#e5e7eb"
            />

            <circle
              cx={(PANEL_SIZE + 40) / 2}
              cy={(PANEL_SIZE + 40) / 2}
              r={PANEL_SIZE / 2}
              fill="#f9fafb"
            />

            <g transform="translate(20,20)">
              {#each visibleDies as die (die.row + '-' + die.col)}
                <rect
                  x={(die.col - colMin) * cellW}
                  y={(rowMax - die.row) * cellH}
                  width={cellW}
                  height={cellH}
                  fill={getRenderColor(die, activeBin, hoverBin)}
                  fill-opacity={getRenderOpacity(die)}
                />
              {/each}
            </g>
          </svg>
        </div>

        <!-- 범례 컴포넌트 -->
        <WaferLegend
          bind:hoverBin
          bind:activeBin
          bind:sortOrder
          items={legendItems}
          backgroundColor={BACKGROUND_COLOR}
          backgroundCount={backgroundCount}
        />
      </div>
    </div>
  </div>
{/if}

<style>
  .no-wafer {
    color: #6b7280;
    font-size: 0.875rem;
  }

  .wafer-page-root {
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    width: 100%;
  }

  .stack-card {
    position: relative;
    background-color: #ffffff;
    border-radius: 24px;
    padding: 18px 24px 24px;
    box-shadow: 0 24px 50px rgba(15, 23, 42, 0.18);
    overflow: visible;
  }

  .stack-card::before,
  .stack-card::after {
    content: "";
    position: absolute;
    inset: 8px;
    border-radius: 24px;
    background: #f3f4f6;
    z-index: -1;
  }

  .stack-card::before {
    transform: translate(8px, 8px);
    box-shadow: 0 18px 40px rgba(15, 23, 42, 0.12);
    opacity: 0.9;
  }

  .stack-card::after {
    transform: translate(16px, 16px);
    box-shadow: 0 14px 30px rgba(15, 23, 42, 0.09);
    opacity: 0.7;
  }

  .card-title {
    text-align: center;
    font-size: 0.95rem;
    font-weight: 600;
    color: #111827;
    margin-bottom: 0.75rem;
  }

  .card-title-sep {
    color: #9ca3af;
    margin: 0 0.25rem;
  }

  .card-body-row {
    display: flex;
    flex-direction: row;
    align-items: flex-start;
    justify-content: flex-start;
    gap: 24px;
  }

  .wafer-svg-wrapper {
    display: block;
  }
</style>
