#!/usr/bin/env python3
"""Gate Android library artifacts. AAR is an input, NEVER a merged Cinemana APK."""
from pathlib import Path
from zipfile import ZipFile
import json, sys
root=Path(sys.argv[1])
paths=list(root.rglob("*.aar"))
if not paths: raise SystemExit("FAIL: Compose Android .aar not generated")
out=[]
for p in paths:
    with ZipFile(p) as z:
        if z.testzip(): raise SystemExit(f"FAIL: corrupt AAR: {p}")
        files=z.namelist()
        if "AndroidManifest.xml" not in files or "classes.jar" not in files:
            raise SystemExit(f"FAIL: missing library manifest or classes.jar: {p}")
        classblob=z.read("classes.jar")
        from io import BytesIO
        with ZipFile(BytesIO(classblob)) as classes:
            members=classes.namelist()
            nuvio=sum(x.startswith("com/nuvio/") and x.endswith(".class") for x in members)
            if nuvio == 0: raise SystemExit(f"FAIL: empty Nuvio class archive: {p}")
        out.append({"path":str(p),"size":p.stat().st_size,"nuvio_classes":nuvio,"files":len(files),"classification":"LIBRARY_NOT_MERGED","has_resources":any(x.startswith("res/") for x in files)})
print(json.dumps({"classification":"NOT_A_CINEMANA_APK","aars":out},indent=2))
