#!/usr/bin/env python3
"""Build the Ubuntu lab and preserve raw evidence. Standard library only."""
import csv
import hashlib
import json
import os
from pathlib import Path
import platform
import shlex
import shutil
import subprocess
import sys
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
ASAN_OPTIONS = "halt_on_error=1:abort_on_error=0:detect_leaks=0:color=never"
COMMON = ["-std=c11", "-Wall", "-Wextra", "-g", "-O0",
          "-fno-omit-frame-pointer"]


def capture(command, directory, stem, env=None):
    (directory / (stem + ".command.txt")).write_text(
        shlex.join(command) + "\n", encoding="utf-8")
    try:
        result = subprocess.run(command, cwd=ROOT, env=env,
                                capture_output=True, timeout=30, check=False)
        code, out, err = result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired as exc:
        code, out, err = "TIMEOUT", exc.stdout or b"", exc.stderr or b""
    (directory / (stem + ".stdout.txt")).write_bytes(out)
    (directory / (stem + ".stderr.txt")).write_bytes(err)
    (directory / (stem + ".exitcode.txt")).write_text(str(code) + "\n")
    return code, err


def main():
    if platform.system() != "Linux" or not Path("/etc/os-release").exists():
        sys.exit("Run this lab inside the Ubuntu VM, not in Windows PowerShell.")
    os_release = Path("/etc/os-release").read_text()
    if 'ID=ubuntu\n' not in os_release and 'ID="ubuntu"\n' not in os_release:
        sys.exit("This Day 2 runner expects Ubuntu. Record other systems separately.")
    for tool in ("gcc", "gdb"):
        if shutil.which(tool) is None:
            sys.exit("Missing " + tool + "; install build-essential and gdb first.")

    cases = json.loads((ROOT / "tests/cases.json").read_text())
    for case in cases:
        data = (ROOT / "tests" / case["file"]).read_bytes().rstrip(b"\r\n")
        case["input"] = data.decode("ascii")
        if b"\0" in data or len(data) != case["bytes"]:
            sys.exit("Invalid test bytes: " + case["name"])
        if (len(data) + 1 > 8) != case["overflow"]:
            sys.exit("Invalid overflow expectation: " + case["name"])

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
    evidence = ROOT / "evidence/day2" / stamp
    evidence.mkdir(parents=True)
    build = evidence / "build"
    build.mkdir()
    (evidence / "os-release.txt").write_text(os_release)
    info = {"recorded_utc": stamp, "platform": platform.platform(),
            "architecture": platform.machine(), "python": sys.version,
            "project_path": str(ROOT), "ASAN_OPTIONS": ASAN_OPTIONS,
            "vm_product": "Fill in manually: VirtualBox/VMware/other",
            "note": "Linux metadata alone does not prove this is a VM."}
    (evidence / "environment.json").write_text(
        json.dumps(info, indent=2) + "\n", encoding="utf-8")
    for command, stem in [(["uname", "-a"], "uname"),
                          (["gcc", "--version"], "gcc-version"),
                          (["gdb", "--version"], "gdb-version"),
                          (["ldd", "--version"], "libc-version")]:
        capture(command, evidence, stem)
    aslr = Path("/proc/sys/kernel/randomize_va_space")
    if aslr.exists():
        (evidence / "aslr.txt").write_text(aslr.read_text())
    shutil.copy2(ROOT / "src/vulnerable.c", evidence / "vulnerable.c")
    shutil.copy2(ROOT / "tests/cases.json", evidence / "cases.json")
    hashes = {}
    for path in [ROOT / "src/vulnerable.c", Path(__file__).resolve(),
                 ROOT / "tests/cases.json"] + [ROOT / "tests" / c["file"] for c in cases]:
        hashes[str(path.relative_to(ROOT))] = hashlib.sha256(path.read_bytes()).hexdigest()
    (evidence / "sha256.json").write_text(json.dumps(hashes, indent=2) + "\n")

    for variant, extra in [("debug", []), ("asan", ["-fsanitize=address"])]:
        command = ["gcc"] + COMMON + extra + ["src/vulnerable.c", "-o",
                                              str(build / ("vulnerable_" + variant))]
        code, _ = capture(command, evidence, "build-" + variant)
        if code != 0:
            sys.exit("Build failed; inspect " + str(evidence))

    rows = []
    env = os.environ.copy()
    env["ASAN_OPTIONS"] = ASAN_OPTIONS
    for variant in ("debug", "asan"):
        for case in cases:
            stem = variant + "-" + case["name"]
            (evidence / (stem + ".input.txt")).write_bytes(case["input"].encode("ascii"))
            command = [str(build / ("vulnerable_" + variant)), case["input"]]
            code, stderr = capture(command, evidence, stem,
                                   env if variant == "asan" else None)
            detected = b"ERROR: AddressSanitizer: stack-buffer-overflow" in stderr
            if variant == "asan":
                matches = (isinstance(code, int) and code != 0 and detected
                           if case["overflow"] else code == 0 and not stderr)
                assessment = "EXPECTED" if matches else "INVESTIGATE"
            elif case["overflow"]:
                assessment = "UNDEFINED_BEHAVIOR; outcome is observation only"
            else:
                assessment = "EXPECTED" if code == 0 else "INVESTIGATE"
            rows.append({"variant": variant, "case": case["name"],
                         "input_bytes": case["bytes"], "required_bytes": case["bytes"] + 1,
                         "capacity": 8, "exitcode": code,
                         "asan_stack_overflow": detected, "assessment": assessment})

    with (evidence / "summary.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print("Evidence:", evidence)
    for row in rows:
        print(row["variant"], row["case"], "exit=" + str(row["exitcode"]), row["assessment"])
    if any(row["assessment"] == "INVESTIGATE" for row in rows):
        sys.exit(1)


if __name__ == "__main__":
    main()
