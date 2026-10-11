#!/usr/bin/env python3
"""Check build output is a genuine Nuvio APK, NOT a merged Cinemana build."""
import json
import pathlib
import subprocess
import sys
import zipfile

root = pathlib.Path(sys.argv[1])
apks = sorted(root.rglob("*.apk"))
if not apks:
    raise SystemExit("FAIL: no Nuvio APK was produced")
records = []
for apk in apks:
    with zipfile.ZipFile(apk) as z:
        bad = z.testzip()
        if bad:
            raise SystemExit(f"FAIL: corrupt zip member {bad}")
        files = set(z.namelist())
        if "resources.arsc" not in files or not any(f.startswith("classes") and f.endswith(".dex") for f in files):
            raise SystemExit(f"FAIL: missing Android resources/DEX in {apk}")
    proc = subprocess.run(["aapt", "dump", "badging", str(apk)], text=True, capture_output=True, check=True)
    package_line = next((l for l in proc.stdout.splitlines() if l.startswith("package: ")), "")
    if "com.nuvio.app" not in package_line and "com.nuviodebug.com" not in package_line:
        raise SystemExit(f"FAIL: unexpected package identity: {package_line}")
    records.append({"filename": str(apk), "package": package_line, "classification": "NUVIO_COMPONENT_NOT_MERGED"})
print(json.dumps({"status": "component_build_only", "apk_count": len(apks), "apks": records}, indent=2))
