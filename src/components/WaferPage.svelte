<script lang="ts">
  import { onMount } from "svelte";
  import WaferMapPanel from "./WaferMapPanel.svelte";
  import WaferInputBar from "./WaferInputBar.svelte";

  const DATA_URL = "/wafer_bin.json";

  let wafers: any[] = [];
  let currentIndex = 0;
  let loading = true;
  let error = "";
  let generating = false;
  let generateMessage = "";

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

  // WaferInputBar → submit 이벤트 처리
  async function handleInputSubmit(event: CustomEvent<{ waferIds: string[] }>) {
    const { waferIds } = event.detail;
    console.log("Requested waferIds:", waferIds);

    if (!waferIds.length) {
      generateMessage = "웨이퍼 ID를 하나 이상 입력해주세요.";
      return;
    }

    generating = true;
    generateMessage = "데이터 생성 중...";

    try {
      const res = await fetch("/api/generate-data", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ waferIds })
      });

      const json = await res.json();
      if (!res.ok) {
        console.error(json);
        generateMessage = `에러: ${json.error ?? "서버 오류"}`;
        return;
      }

      console.log("generate-data results:", json);
      generateMessage = `데이터 생성 완료: ${json.waferIds.join(", ")}`;
    } catch (e) {
      console.error(e);
      generateMessage = "요청 중 오류가 발생했습니다.";
    } finally {
      generating = false;
    }
  }
</script>

<div class="min-h-[480px] bg-white flex flex-col">
  <!-- 상단 인풋 바 (한 번만!) -->
  <WaferInputBar on:submit={handleInputSubmit} />

  <!-- 상태 메시지 -->
  {#if generateMessage}
    <div style="padding: 4px 20px; font-size: 12px; color: #4b5563;">
      {generateMessage}
    </div>
  {/if}

  <!-- 아래 메인 컨텐츠 -->
  <div class="px-8 pt-4 pb-10">
    {#if loading}
      <div class="text-slate-400">Loading wafer data...</div>
    {:else if error}
      <div class="text-red-500">Error: {error}</div>
    {:else if !currentWafer}
      <div class="text-slate-400">No wafer data.</div>
    {:else}
      <header class="flex items-center justify-between mb-4">
        <div class="text-lg font-semibold text-slate-800">
          Wafer Map Viewer
        </div>

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
      </header>

      <main class="flex items-start justify-start">
        <WaferMapPanel {currentWafer} wafer={currentWafer} />
      </main>
    {/if}
  </div>
</div>
