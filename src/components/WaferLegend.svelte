<script lang="ts">
  import type { BinLegendItem } from "../lib/binColors";

  export let items: BinLegendItem[] = [];
  export let backgroundColor: string;
  export let backgroundCount: number;

  // 부모와 바인딩할 값들
  export let hoverBin: string | null = null;
  export let activeBin: string | null = null;     // ★ 추가
  export let sortOrder: "asc" | "desc" = "desc";

  // 정렬 적용
  $: sortedItems = items
    .slice()
    .sort((a, b) =>
      sortOrder === "desc" ? b.count - a.count : a.count - b.count
    );

  function toggleSortOrder() {
    sortOrder = sortOrder === "desc" ? "asc" : "desc";
  }

  function handleClick(code: string) {
    // 같은 bin을 한 번 더 클릭하면 필터 해제
    activeBin = activeBin === code ? null : code;
  }
</script>

<div class="legend-panel">
  <div class="legend-header">
    <div class="legend-title">Legend</div>
    <button
      class="legend-sort-btn"
      type="button"
      on:click={toggleSortOrder}
    >
      Count {sortOrder === "desc" ? "↓" : "↑"}
    </button>
  </div>

  <div class="legend-scroll">
    {#each sortedItems as item}
      <div
        class="legend-row"
        class:active={activeBin === item.code}
        on:mouseenter={() => (hoverBin = item.code)}
        on:mouseleave={() => (hoverBin = null)}
        on:click={() => handleClick(item.code)}
      >
        <span
          class="legend-color"
          style={`background-color:${item.color};`}
        ></span>
        <span>{item.label} ({item.count})</span>
      </div>
    {/each}
  </div>

  <div class="legend-footer">
    <div class="legend-row">
      <span
        class="legend-color"
        style={`background-color:${backgroundColor};`}
      ></span>
      <span>def ({backgroundCount})</span>
    </div>
  </div>
</div>

<style>
  .legend-panel {
    min-width: 130px;
    max-height: 600px;
    padding: 8px 10px;
    border-radius: 16px;
    background-color: #ffffff;
    border: 1px solid #e5e7eb;
    color: #111827;
    font-size: 0.8rem;
    display: flex;
    flex-direction: column;
    box-shadow: 0 12px 30px rgba(15, 23, 42, 0.12);
  }

  .legend-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
    margin-bottom: 4px;
  }

  .legend-title {
    font-weight: 600;
    flex: 0 0 auto;
  }

  .legend-sort-btn {
    border: none;
    background: #f3f4f6;
    border-radius: 999px;
    padding: 2px 8px;
    font-size: 0.7rem;
    color: #374151;
    cursor: pointer;
  }

  .legend-sort-btn:hover {
    background: #e5e7eb;
  }

  .legend-scroll {
    flex: 1 1 auto;
    overflow-y: auto;
    padding-right: 4px;
    margin-bottom: 6px;
  }

  .legend-footer {
    border-top: 1px solid #e5e7eb;
    padding-top: 6px;
    flex: 0 0 auto;
  }

  .legend-row {
    display: flex;
    align-items: center;
    margin-bottom: 4px;
    cursor: pointer;
    border-radius: 6px;
    padding: 2px 4px;
  }

  .legend-row:hover span:last-child {
    font-weight: 600;
  }

  .legend-row.active {
    background-color: #eef2ff; /* 선택된 bin 하이라이트 */
    font-weight: 600;
  }

  .legend-color {
    width: 14px;
    height: 14px;
    border-radius: 3px;
    margin-right: 6px;
  }
</style>
