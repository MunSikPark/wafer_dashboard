<script lang="ts">
  export type CorrItem = {
    name: string;
    corr: number; // -1 ~ 1
  };

  export let targetName: string;
  export let correlations: CorrItem[] = [];

  // 상위 N개만 (예: 40)
  const TOP_N = 40;

  $: sortedCorr = [...correlations]
    .sort((a, b) => Math.abs(b.corr) - Math.abs(a.corr))
    .slice(0, TOP_N);

  // 막대 길이용: 0 ~ 1 로 정규화
  function corrToWidth(c: number) {
    return `${Math.abs(c) * 100}%`;
  }

  // 색상: 양/음에 따라
  function corrToColor(c: number) {
    if (c > 0) {
      return "bg-red-500";  // 양의 상관
    } else if (c < 0) {
      return "bg-blue-500"; // 음의 상관
    } else {
      return "bg-gray-300";
    }
  }

  // 텍스트 색상 (강한 상관이면 흰색, 아니면 회색)
  function corrTextColor(c: number) {
    return Math.abs(c) > 0.7 ? "text-white" : "text-gray-700";
  }
</script>

<div class="flex flex-col gap-4 h-full">
  <!-- 상단: 선택된 트렌드 헤더 -->
  <div class="rounded-2xl border border-slate-700 bg-slate-900/60 px-4 py-3">
    <div class="text-xs uppercase tracking-widest text-slate-400">
      Selected trend
    </div>
    <div class="mt-1 text-lg font-semibold text-slate-50">
      {targetName}
    </div>
    <div class="mt-1 text-xs text-slate-400">
      Showing Pearson correlation with {correlations.length} trends
    </div>
  </div>

  <!-- 중간: 1D heatstrip (optional 간단 버전) -->
  <div class="rounded-2xl border border-slate-800 bg-slate-900/50 px-3 py-2">
    <div class="text-xs mb-1 text-slate-400 flex justify-between">
      <span>Correlation overview</span>
      <span>|corr| sorted (top {TOP_N})</span>
    </div>
    <div class="flex gap-0.5 overflow-x-auto">
      {#each sortedCorr as item}
        <div
          class="h-6 w-2 rounded-sm"
          class:bg-red-500={item.corr > 0}
          class:bg-blue-500={item.corr < 0}
          class:bg-slate-600={item.corr === 0}
          title={`${item.name}: ${item.corr.toFixed(3)}`}
        />
      {/each}
    </div>
  </div>

  <!-- 리스트: 상관 랭킹 -->
  <div class="flex-1 rounded-2xl border border-slate-800 bg-slate-950/60 px-3 py-2 overflow-y-auto">
    <div class="text-xs mb-2 text-slate-400 flex justify-between">
      <span>Top correlated trends</span>
      <span>Pearson r</span>
    </div>

    <div class="flex flex-col gap-1.5">
      {#each sortedCorr as item}
        <div
          class="group flex items-center gap-2 rounded-xl px-2 py-1.5 hover:bg-slate-800/60 cursor-pointer"
          on:click={() => {
            // TODO: 여기서 item.name 을 상위 레벨로 emit해서
            //       "비교 대상 트렌드"로 선택하게 만들면 됨
          }}
        >
          <!-- 이름 -->
          <div class="flex-1 min-w-0">
            <div class="text-xs font-medium text-slate-100 truncate">
              {item.name}
            </div>
          </div>

          <!-- 막대 + 숫자 -->
          <div class="flex items-center gap-2 w-40">
            <div class="relative h-3 flex-1 rounded-full bg-slate-800 overflow-hidden">
              <div
                class={`h-full ${corrToColor(item.corr)} transition-all duration-300`}
                style={`width: ${corrToWidth(item.corr)};`}
              />
            </div>
            <div class={`w-12 text-right text-xs tabular-nums ${corrTextColor(item.corr)}`}>
              {item.corr.toFixed(2)}
            </div>
          </div>
        </div>
      {/each}
    </div>
  </div>
</div>
