#!/usr/bin/env python3
"""Validate native Cinemana <-> Nuvio Kotlin ContentProvider contract.

Accepts paths to locally supplied PATCH215 native bridge and PATCH216 Kotlin bridge.
Only static checks: successful execution does not establish Android runtime compatibility.
"""
import argparse
import json
import re
from pathlib import Path

EXPECTED = {
    "cinemanaHome", "cinemanaGroup", "cinemanaSearch",
    "cinemanaDetails", "cinemanaEpisodes", "animercoCatalog",
    "animercoSearch", "animercoDetails", "animercoEpisodes",
    "preparePlayback",
}

def verify(provider, bridge, kotlin, manifest):
    native_methods = set(re.findall(r'"(\w+)"\.equals\(method\)', bridge + provider))
    calls = set(re.findall(r'\bcall\("(\w+)"', kotlin))
    calls.update(re.findall(r'contentResolver\.call\(uri, "(\w+)"', kotlin))
    calls.update(re.findall(r'"(cinemanaEpisodes|animercoEpisodes|cinemanaDetails|animercoDetails)"', kotlin))
    checks = {
        "native_methods_implemented": EXPECTED <= native_methods,
        "kotlin_methods_used": EXPECTED <= calls,
        "no_unknown_calls": calls <= native_methods,
        "native_source_tags": all(('"source", "' + v + '"') in bridge for v in ("cinemana:original", "cinemana:animerco")),
        "episode_work_identity_check": 'response.optString("workId") != id' in kotlin,
        "detail_identity_check": 'it.id == id' in kotlin,
        "internal_package_bound": 'HOST_PACKAGE = "com.shabakaty.cinemana"' in kotlin,
        "provider_not_exported": bool(re.search(r'<provider\b[^>]*android:name="com\.shabakaty\.cinemana\.compat\.nuvio\.NuvioEngineProvider"[^>]*android:exported="false"', manifest)),
    }
    return {"passed": all(checks.values()), "checks": checks,
            "expected_methods": sorted(EXPECTED),
            "missing_kotlin_calls": sorted(EXPECTED - calls),
            "missing_native_methods": sorted(EXPECTED - native_methods)}

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    for name in ("provider", "bridge", "kotlin", "manifest"):
        ap.add_argument("--" + name, type=Path, required=True)
    args = ap.parse_args()
    result = verify(*(getattr(args, name).read_text() for name in ("provider", "bridge", "kotlin", "manifest")))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(0 if result["passed"] else 1)
