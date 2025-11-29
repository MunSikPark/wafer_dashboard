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
  <header class="flex items-center justify-between mb-4">
    <div class="text-lg font-semibold text-slate-800">
      Wafer Map Viewer
    </div>

    {#if currentWafer}
      <div class="flex items-center gap-2 text-sm text-slate-700">
        <button
          class="px-2 py-1 rounded border border-slate-300 bg-white hover:bg-slate-100"
          on:click={prev}
        >
          &lt;
        </button>

        <div>
          Wafer {currentWafer.wafer}
          <span class="text-slate-500 ml-1">(Lot {currentWafer.lot})</span>
          <span class="ml-2 text-xs text-slate-400">
            {currentIndex + 1} / {wafers.length}
          </span>
        </div>

        <button
          class="px-2 py-1 rounded border border-slate-300 bg-white hover:bg-slate-100"
          on:click={next}
        >
          &gt;
        </button>
      </div>
    {/if}
  </header>

  <!-- 핵심: 두 컬럼 레이아웃 -->
  <main class="flex items-start gap-6">

    <!-- 왼쪽: 웨이퍼맵 고정 폭 -->
    <div class="shrink-0 w-[900px]">
      <WaferMapPanel {currentWafer} wafer={currentWafer} />
    </div>

    <!-- 오른쪽: 트렌드 코릴레이션 패널 -->
    <div class="flex-1 min-w-[420px]">
      <TrendCorrelationPanel {trendNames} />
    </div>

  </main>
</div>
