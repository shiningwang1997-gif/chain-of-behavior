import json
import os
import csv

DATA_FILE = "data/sudoku/sudoku6x6_50.json"
RUN_FILE = "output/sudoku/sudoku.jsonl"
STANDARD_FILE = "output/sudoku/sudoku_standard.jsonl"
CSV_OUTPUT = "output/sudoku/verify_results.csv"


def load_jsonl(path):
    if not os.path.exists(path):
        return {}
    results = {}
    with open(path, "r") as f:
        for line in f:
            if line.strip():
                obj = json.loads(line)
                results[obj["id"]] = obj["solved"]
    return results


def load_ground_truth():
    with open(DATA_FILE, "r") as f:
        data = json.load(f)
    gt = {}
    for p in data["puzzles"]:
        gt[p["id"]] = p["solution"]
    return gt


def boards_equal(b1, b2):
    if b1 is None or b2 is None:
        return False
    if len(b1) != len(b2):
        return False
    return all(r1 == r2 for r1, r2 in zip(b1, b2))


def main():
    print("📘 Loading data...")

    gt = load_ground_truth()
    run_res = load_jsonl(RUN_FILE)
    std_res = load_jsonl(STANDARD_FILE)

    ids = sorted(gt.keys())

    run_correct = 0
    std_correct = 0

    rows_for_csv = []  # store rows for csv output

    print("\n================ Verification Report ================\n")
    print(f"{'ID':<4} {'Standard':<10} {'Run':<10} {'Correct?'}")
    print("-" * 45)

    for pid in ids:
        correct = gt[pid]
        std = std_res.get(pid)
        run = run_res.get(pid)

        std_ok = boards_equal(std, correct)
        run_ok = boards_equal(run, correct)

        if std_ok:
            std_correct += 1
        if run_ok:
            run_correct += 1

        print(f"{pid:<4} "
              f"{('✔' if std_ok else '✘'):<10} "
              f"{('✔' if run_ok else '✘'):<10} "
              f"{'✔' if (run_ok or std_ok) else '✘'}")

        # ================= CSV: use true/false =================
        rows_for_csv.append({
            "id": pid,
            "standard_correct": "true" if std_ok else "false",
            "run_correct": "true" if run_ok else "false"
        })

    print("\n================ Summary ================\n")
    print(f"Total puzzles: {len(ids)}")
    print(f"Standard correct: {std_correct}/{len(ids)}")
    print(f"Run correct:      {run_correct}/{len(ids)}")

    # ================= SAVE CSV =================
    os.makedirs(os.path.dirname(CSV_OUTPUT), exist_ok=True)
    with open(CSV_OUTPUT, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "standard_correct", "run_correct"])
        writer.writeheader()
        writer.writerows(rows_for_csv)

    print(f"\n📄 CSV 已保存到: {CSV_OUTPUT}\n")


if __name__ == "__main__":
    main()
