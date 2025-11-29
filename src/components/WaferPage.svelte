<script lang="ts">
  import { onMount } from "svelte";
  import WaferMapPanel from "./WaferMapPanel.svelte";
  import TrendCorrelationPanel from "./TrendCorrelationPanel.svelte";

  const DATA_URL = "/wafer_bin.json";

  let wafers: any[] = [];
  let currentIndex = 0;
  let loading = true;
  let error = "";

  // 더미 트렌드 리스트
  let trendNames: string[] = [
    "GROSSICC",
    "GROSSICC_PMUPS",
    "VCC_PMU",
    "OPENS_PMON",
    "OPENS_VNEG",
    "PTRES_PMON_PMU"
  ];

  $: currentWafer = wafers.length ? wafers[currentIndex] : null;

  onMount(async () => {
    try {
      const res = await fetch(DATA_URL);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      wafers = data;
      currentIndex = 0;
    } catch (e) {
      console.error(e);
      error = String(e);
    } finally {
      loading = false;
    }
  });

  function next() {
    if (!wafers.length) return;
    currentIndex = (currentIndex + 1) % wafers.length;
  }

  function prev() {
    if (!wafers.length) return;
    currentIndex = (currentIndex - 1 + wafers.length) % wafers.length;
  }
</script>

<div class="min-h-[480px] px-8 pt-6 pb-10 bg-white">
  <!-- 헤더 영역 -->
  <header class="mb-4">
    <div class="flex items-center gap-4">
      <!-- 제목 -->
      <div class="text-lg font-semibold text-slate-800">
        Wafer Map Viewer
      </div>

      <!-- 제목 오른쪽에 바로 붙는 웨이퍼 선택 영역 -->
      {#if currentWafer}
        <div
          class="flex items-center gap-2 text-xs text-slate-700
                 bg-slate-100 px-3 py-1 rounded-full border border-slate-200"
        >
          <button
            class="px-1.5 py-0.5 rounded-full border border-slate-300 bg-white hover:bg-slate-100"
            type="button"
            on:click={prev}
          >
            &lt;
          </button>

          <div class="flex items-center gap-1">
            <span class="font-medium">
              Wafer {currentWafer.wafer}
            </span>
            <span class="text-slate-500">
              (Lot {currentWafer.lot})
            </span>
            <span class="ml-1 text-[10px] text-slate-400">
              {currentIndex + 1} / {wafers.length}
            </span>
          </div>

          <button
            class="px-1.5 py-0.5 rounded-full border border-slate-300 bg-white hover:bg-slate-100"
            type="button"
            on:click={next}
          >
            &gt;
          </button>
        </div>
      {/if}
    </div>
  </header>

  <!-- 이하 나머지 main 부분은 그대로 유지 -->
  <main class="flex items-start justify-start gap-6">
    {#if loading}
      <div class="text-slate-400">Loading wafer data...</div>
    {:else if error}
      <div class="text-red-500">Error: {error}</div>
    {:else if !currentWafer}
      <div class="text-slate-400">No wafer data.</div>
    {:else}
      <div class="flex-shrink-0">
        <WaferMapPanel {currentWafer} wafer={currentWafer} />
      </div>

      <div class="flex-1 min-w-[420px]">
        <TrendCorrelationPanel {trendNames} />
      </div>
    {/if}
  </main>
</div>

