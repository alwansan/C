#!/usr/bin/env python3
"""CI-only Maven wrapper for Nuvio's bundled local Android AAR dependencies."""
import hashlib
import json
import re
import shutil
import sys
from pathlib import Path

GROUP = "com.nuvio.localaar"
VERSION = "0.5.8-local"

def run(root):
    root = Path(root).resolve()
    build = root / "composeApp/build.gradle.kts"
    settings = root / "settings.gradle.kts"
    libs = root / "composeApp/libs"
    repo = root / "nuvio-local-aar-maven"
    if not build.is_file() or not settings.is_file() or not libs.is_dir():
        raise RuntimeError("Not a Nuvio project root")
    local = sorted(libs.glob("lib-*.aar"))
    quickjs = libs / "quickjs-kt-android-1.0.5-nuvio.aar"
    if len(local) != 11 or not quickjs.is_file():
        raise RuntimeError("Unexpected upstream AAR set: refusing to mutate Gradle files")
    result = []
    for source in local + [quickjs]:
        artifact = source.stem.lower()
        if not re.fullmatch(r"[a-z0-9][a-z0-9_.-]*", artifact):
            raise RuntimeError("Unsafe AAR name")
        folder = repo / "com/nuvio/localaar" / artifact / VERSION
        folder.mkdir(parents=True, exist_ok=True)
        prefix = f"{artifact}-{VERSION}"
        shutil.copy2(source, folder / f"{prefix}.aar")
        (folder / f"{prefix}.pom").write_text(
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<project xmlns="http://maven.apache.org/POM/4.0.0"><modelVersion>4.0.0</modelVersion>'
            f'<groupId>{GROUP}</groupId><artifactId>{artifact}</artifactId>'
            f'<version>{VERSION}</version><packaging>aar</packaging></project>\n'
        )
        result.append({"name": source.name, "coordinate": f"{GROUP}:{artifact}:{VERSION}",
                       "sha256": hashlib.sha256(source.read_bytes()).hexdigest()})
    b = build.read_text()
    needle = 'implementation(fileTree(mapOf("dir" to "libs", "include" to listOf("lib-*.aar"))))'
    if b.count(needle) != 1:
        raise RuntimeError("Upstream fileTree declaration changed")
    replacement = "\n                ".join('implementation("' + x["coordinate"] + '")' for x in result[:-1])
    b = b.replace(needle, replacement)
    needle = 'implementation(files("libs/quickjs-kt-android-1.0.5-nuvio.aar"))'
    if b.count(needle) != 1:
        raise RuntimeError("Upstream QuickJS declaration changed")
    b = b.replace(needle, 'implementation("' + result[-1]["coordinate"] + '")')
    build.write_text(b)
    s = settings.read_text()
    needle = "dependencyResolutionManagement {\n    repositories {"
    if s.count(needle) != 1:
        raise RuntimeError("Upstream repositories changed")
    settings.write_text(s.replace(needle, needle + '\n        maven { url = uri(file("nuvio-local-aar-maven")) }'))
    print(json.dumps({"local_aar_count": len(result), "local_maven_repo": str(repo), "files": result}, indent=2))

if __name__ == "__main__":
    run(sys.argv[1])
