<script lang="ts">
  import { onMount } from "svelte";
  import WaferMapPanel from "./WaferMapPanel.svelte";

  const DATA_URL = "/wafer_bin.json";

  let wafers: any[] = [];
  let currentIndex = 0;

  let loading = true;     // ← 에러 원인: 이게 빠져 있었음
  let error = "";

  $: currentWafer = wafers.length ? wafers[currentIndex] : null;

  onMount(async () => {
    try {
      const res = await fetch(DATA_URL);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      wafers = await res.json();
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

<section class="flex flex-col flex-1 bg-slate-50">
  <!-- 제목 + 좌우 네비, 전체는 좌측 정렬 -->
  <header class="flex items-center justify-between px-8 pt-6 pb-2">
    <h2 class="text-lg font-semibold text-slate-800">
      Wafer Map Viewer
    </h2>

    {#if currentWafer}
      <div class="flex items-center gap-4 text-sm text-slate-700">
        <button
          class="h-8 w-8 flex items-center justify-center rounded-full border border-slate-300 bg-white hover:bg-slate-100"
          on:click={prev}
        >
          ‹
        </button>

        <span class="whitespace-nowrap">
          Wafer {currentWafer.wafer}
          <span class="text-slate-400 mx-1">·</span>
          Lot {currentWafer.lot}
          <span class="text-slate-400 ml-2">
            {currentIndex + 1} / {wafers.length}
          </span>
        </span>

        <button
          class="h-8 w-8 flex items-center justify-center rounded-full border border-slate-300 bg-white hover:bg-slate-100"
          on:click={next}
        >
          ›
        </button>
      </div>
    {/if}
  </header>

  <!-- 본문: 왼쪽에 카드 붙이기 -->
  <main class="flex-1 px-8 pb-10">
    {#if loading}
      <div class="mt-10 text-slate-500 text-sm">Loading wafer data…</div>
    {:else if error}
      <div class="mt-10 text-sm text-red-500">Error: {error}</div>
    {:else if !currentWafer}
      <div class="mt-10 text-slate-500 text-sm">No wafer data.</div>
    {:else}
      <div class="w-full flex justify-start">
        <!-- 카드 크기: 한 화면의 일부만 차지 (대시보드용) -->
        <WaferMapPanel wafer={currentWafer} />
      </div>
    {/if}
  </main>
</section>
