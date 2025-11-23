import json
from collections import defaultdict
from pathlib import Path

# 1) raw 데이터가 있는 디렉터리
#   -> 여기에 wafer_bin.csv, wafer_bin_second2.csv, wafer_bin_03.csv ... 이런 식으로 놓으면 됨
DATA_DIR = Path(r"C:\Users\munsikpark")

# 2) 어떤 파일을 읽을지 패턴 지정
#   wafer_bin.csv, wafer_bin_second2.csv, wafer_bin_03.csv ... 전부 포함
INPUT_GLOB = "wafer_bin*.csv"

# 3) 출력 JSON 경로 (Svelte 프로젝트 static 폴더)
OUTPUT_PATH = Path(
    r"C:\Users\munsikpark\wafer_dashboard\static\wafer_bin.json"
)


def parse_line(line: str):
    """
    한 줄을 파싱해서 die 정보 dict를 반환.
    사용하지 않는/헤더 줄이면 None 반환.
    """
    line = line.strip()
    if not line:
        return None

    lower = line.lower()

    # 헤더/설명 줄 스킵 (필요하다면 패턴을 더 추가)
    if lower.startswith("lot") or lower.startswith("c0=") or lower.startswith("~"):
        return None

    # 콤마가 섞여 있어도 동작하도록 콤마를 공백으로 치환
    line = line.replace(",", " ")
    parts = line.split()

    # 우리가 필요한 컬럼 9개보다 적으면 데이터 라인이 아니라고 판단
    if len(parts) < 9:
        return None

    lot, wafer, row, col, wafsize, proc, fail_bin, err_bin, group = parts[:9]

    try:
        row_i = int(row)
        col_i = int(col)
        waf_i = int(wafsize)
        wafer_i = int(wafer)
    except ValueError:
        # 숫자 변환 안 되는 줄은 스킵
        return None

    return {
        "lot": lot,
        "wafer": wafer_i,
        "row": row_i,
        "col": col_i,
        "wafsize": waf_i,
        "process": proc,
        "fail_bin": fail_bin,
        "error_bin": err_bin,
        "group": group,
    }


def build_wafer_json(records):
    """
    die 레코드 리스트 -> wafer 단위 JSON 구조로 변환
    [
      {
        "wafer": 24,
        "lot": "4175341",
        "wafsize": 12,
        "row_min": ...,
        "row_max": ...,
        "col_min": ...,
        "col_max": ...,
        "dies": [ {die...}, ... ]
      },
      ...
    ]
    """
    wafers = defaultdict(
        lambda: {
            "wafer": None,
            "lot": None,
            "wafsize": None,
            "row_min": None,
            "row_max": None,
            "col_min": None,
            "col_max": None,
            "dies": [],
        }
    )

    for rec in records:
        key = (rec["lot"], rec["wafer"])
        w = wafers[key]

        # 기본 정보 세팅
        if w["wafer"] is None:
            w["wafer"] = rec["wafer"]
        if w["lot"] is None:
            w["lot"] = rec["lot"]
        if w["wafsize"] is None:
            w["wafsize"] = rec["wafsize"]

        r = rec["row"]
        c = rec["col"]

        # row/col 최소/최대 갱신
        if w["row_min"] is None or r < w["row_min"]:
            w["row_min"] = r
        if w["row_max"] is None or r > w["row_max"]:
            w["row_max"] = r
        if w["col_min"] is None or c < w["col_min"]:
            w["col_min"] = c
        if w["col_max"] is None or c > w["col_max"]:
            w["col_max"] = c

        # die 자체는 dies 배열에 추가
        w["dies"].append(rec)

    # dict -> list 로 변환
    return list(wafers.values())


def main():
    # 1) 읽어올 CSV 파일들 찾기
    input_files = sorted(DATA_DIR.glob(INPUT_GLOB))

    if not input_files:
        raise FileNotFoundError(
            f"'{DATA_DIR}' 아래에 패턴 '{INPUT_GLOB}'에 맞는 CSV 파일이 없습니다."
        )

    print("다음 파일들을 읽습니다:")
    for p in input_files:
        print("  -", p)

    # 2) 모든 파일에서 레코드 모으기
    all_records = []

    for path in input_files:
        print(f"\n[파일 처리 중] {path}")
        cnt_before = len(all_records)

        with path.open(encoding="utf-8", errors="ignore") as f:
            for line in f:
                rec = parse_line(line)
                if rec is not None:
                    all_records.append(rec)

        cnt_after = len(all_records)
        print(f"  이 파일에서 추가된 die 레코드: {cnt_after - cnt_before} 개")

    if not all_records:
        print("경고: 유효한 데이터가 0개입니다. parse_line 조건을 확인해 보세요.")
        return

    print(f"\n총 유효한 die 레코드: {len(all_records)} 개")

    # 3) wafer 단위로 묶어서 JSON 구조 생성
    wafer_list = build_wafer_json(all_records)
    print(f"wafer 개수: {len(wafer_list)} 개")

    # 4) 출력 폴더가 없으면 생성
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    with OUTPUT_PATH.open("w", encoding="utf-8") as f:
        json.dump(wafer_list, f, indent=2, ensure_ascii=False)

    print(f"\nJSON 저장 완료: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
