# C:\Users\munsikpark\data_generation.py
from pathlib import Path
import csv
import re
import sys

# ----- 기본 설정 -----
BASE_DIR = Path(r"C:\Users\munsikpark")  # 웨이퍼 csv들이 있는 폴더

VSOA_PREFIX = "VSOA_"
PGP_SUFFIX = "_PGP"

TEST_NAME_RE = re.compile(r"[A-Z0-9_]+$")
HEAD_SITE_XY_RE = re.compile(
    r'Head\((?P<head>-?\d+)\)\s+Site\((?P<site>-?\d+)\)\s+\(X,Y\)=\((?P<x>-?\d+),(?P<y>-?\d+)\)'
)


def parse_lot_wafer_from_filename(path: Path):
    """
    예: 4174991.081.4991-06.FPP.00.csv
      -> lot_id = 4174991.081.4991
      -> wafer_id = 06
    """
    name = path.name  # 4174991.081.4991-06.FPP.00.csv
    base = name[:-4]  # remove .csv
    before_fpp = base.split(".FPP", 1)[0]  # 4174991.081.4991-06
    lot_part, wafer_part = before_fpp.split("-")
    return lot_part, wafer_part


def is_valid_test_name(token: str) -> bool:
    return TEST_NAME_RE.fullmatch(token) is not None


def is_nan_value(v: str) -> bool:
    """
    'NaN', 'nan', 'NAN', '-nan', ... 모두 True
    """
    if v.startswith("-"):
        v = v[1:]

    if len(v) != 3:
        return False

    c0, c1, c2 = v[0], v[1], v[2]
    return (c0 in ("N", "n")) and (c1 in ("A", "a")) and (c2 in ("N", "n"))


def collect_meta_defs(raw_path: Path):
    """
    메타 영역에서 TREND_DEF / SERIES_DEF / time_profiler 수집
    """
    trend_names = set()
    series_names = set()
    time_profiler_lines = []

    with raw_path.open("r", encoding="utf-8", errors="ignore") as f:
        trend_add = trend_names.add
        series_add = series_names.add
        vsoa_prefix = VSOA_PREFIX
        pgp_suffix = PGP_SUFFIX

        for line in f:
            if '"Head(' in line:
                break

            if "print_memory_usage" in line:
                continue

            if "time_profiler" in line:
                time_profiler_lines.append(line.rstrip("\n"))

            if "TREND_DEF" not in line and "SERIES_DEF" not in line:
                continue

            tokens = line.strip().split()
            kind = None
            start_idx = 0

            for i, t in enumerate(tokens):
                if t == "TREND_DEF":
                    kind = "TREND"
                    start_idx = i + 1
                    break
                elif t == "SERIES_DEF":
                    kind = "SERIES"
                    start_idx = i + 1
                    break

            if kind is None:
                continue

            name_token = None
            for token in tokens[start_idx:]:
                if is_valid_test_name(token):
                    name_token = token
                    break

            if not name_token:
                continue

            if name_token.startswith(vsoa_prefix) or name_token.endswith(pgp_suffix):
                continue

            if kind == "TREND":
                trend_add(name_token)
            else:
                series_add(name_token)

    return trend_names, series_names, time_profiler_lines


def parse_head_site_xy(line: str):
    m = HEAD_SITE_XY_RE.search(line)
    if not m:
        return None, None, None, None
    return int(m.group("head")), int(m.group("site")), int(m.group("x")), int(m.group("y"))


def process_die_data(
    raw_path: Path,
    trend_names,
    series_names,
    timeprof_path: Path,
    trend_out_path: Path,
    series_out_path: Path,
    lot_id: str,
    wafer_id: str,
):
    vsoa_prefix = VSOA_PREFIX
    pgp_suffix = PGP_SUFFIX

    with raw_path.open("r", encoding="utf-8", errors="ignore") as fin, \
         trend_out_path.open("w", newline="", encoding="utf-8") as f_trend, \
         series_out_path.open("w", newline="", encoding="utf-8") as f_series, \
         timeprof_path.open("a", encoding="utf-8") as f_tprof:

        trend_writer = csv.writer(f_trend)
        series_writer = csv.writer(f_series)
        trow = trend_writer.writerow
        srow = series_writer.writerow
        tprof_write = f_tprof.write

        trend_set = trend_names
        series_set = series_names

        header = ["lot_id", "wafer_id", "head", "site", "x", "y", "test_name", "value_raw"]
        trow(header)
        srow(header)

        in_meta = True
        head = site = x = y = None

        for line in fin:
            s = line.rstrip("\n")

            if in_meta:
                if '"Head(' in s:
                    in_meta = False
                    head, site, x, y = parse_head_site_xy(s)
                else:
                    if "time_profiler" in s and "print_memory_usage" not in s:
                        if vsoa_prefix not in s and pgp_suffix not in s:
                            tprof_write(s + "\n")
                continue

            if '"Head(' in s:
                head, site, x, y = parse_head_site_xy(s)
                continue

            if "time_profiler" in s and "print_memory_usage" not in s:
                if vsoa_prefix not in s and pgp_suffix not in s:
                    tprof_write(s + "\n")

            if s == "}" or s.startswith("Bin Results"):
                continue

            if not s:
                continue

            if s[0].isspace():
                continue

            parts = s.split(maxsplit=1)
            if not parts:
                continue

            key = parts[0]
            value_raw = parts[1] if len(parts) > 1 else ""

            if key.startswith(vsoa_prefix) or key.endswith(pgp_suffix):
                continue
            if "print_memory_usage" in s:
                continue

            if key in trend_set:
                if not is_nan_value(value_raw):
                    trow([lot_id, wafer_id, head, site, x, y, key, value_raw])

            if key in series_set:
                srow([lot_id, wafer_id, head, site, x, y, key, value_raw])


def run_for_wafer(wafer_name: str):
    """
    wafer_name 예: '4174991.081.4991-06.FPP.00'
    입력 파일: BASE_DIR / (wafer_name + '.csv')
    출력 폴더: BASE_DIR / wafer_name / ...
    """
    raw_path = BASE_DIR / f"{wafer_name}.csv"
    if not raw_path.exists():
        print(f"[WARN] Raw file not found: {raw_path}")
        return {"wafer": wafer_name, "status": "missing"}

    out_dir = BASE_DIR / wafer_name
    out_dir.mkdir(exist_ok=True)

    trend_out = out_dir / "TREND_DATA.csv"
    series_out = out_dir / "SERIES_DATA.csv"
    timeprof_out = out_dir / "TIME_PROFILER.txt"

    lot_id, wafer_id = parse_lot_wafer_from_filename(raw_path)

    print(f"=== Processing {wafer_name} ===")
    print(f" Raw:   {raw_path}")
    print(f" Lot/Wafer: {lot_id} / {wafer_id}")
    print(f" Out dir:   {out_dir}")

    trend_names, series_names, timeprof_meta_lines = collect_meta_defs(raw_path)

    with timeprof_out.open("w", encoding="utf-8") as f:
        for line in timeprof_meta_lines:
            f.write(line + "\n")

    print(f"  TREND_DEF:  {len(trend_names)}")
    print(f"  SERIES_DEF: {len(series_names)}")

    process_die_data(
        raw_path,
        trend_names,
        series_names,
        timeprof_out,
        trend_out,
        series_out,
        lot_id,
        wafer_id,
    )

    print(f"=== Done {wafer_name} ===\n")
    return {"wafer": wafer_name, "status": "ok"}


def main():
    # 인자로 여러 wafer_name 을 받는다.
    wafer_names = [w.strip() for w in sys.argv[1:] if w.strip()]
    if not wafer_names:
        print("Usage: python data_generation.py <wafer_name1> [<wafer_name2> ...]")
        sys.exit(1)

    # 최대 10개만 처리
    wafer_names = wafer_names[:10]

    results = []
    for name in wafer_names:
        results.append(run_for_wafer(name))

    print("Summary:")
    for r in results:
        print(f"  {r['wafer']}: {r['status']}")


if __name__ == "__main__":
    main()
