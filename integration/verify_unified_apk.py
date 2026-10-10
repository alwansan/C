#!/usr/bin/env python3
"""Refuse to call a standalone APK 'merged'. Inspect defined DEX classes, not loose strings."""
import json, re, struct, subprocess, sys, zipfile
def word(b,i): return struct.unpack_from('<I',b,i)[0]
def classes(b):
    if b[:4]!=b'dex\n': raise ValueError('invalid DEX')
    st,so=word(b,56),word(b,60)
    tt,to=word(b,64),word(b,68)
    ct,co=word(b,96),word(b,100)
    strs=[word(b,so+4*i) for i in range(st)]
    types=[word(b,to+4*i) for i in range(tt)]
    out=set()
    for i in range(ct):
        j=strs[types[word(b,co+32*i)]]
        for _ in range(5):
            c=b[j];j+=1
            if c<128:break
        out.add(b[j:b.index(0,j)].decode('utf-8','replace'))
    return out
def validate(path,aapt='aapt'):
    with zipfile.ZipFile(path) as z:
        if z.testzip(): raise ValueError('corrupt APK')
        names=z.namelist()
        if 'resources.arsc' not in names: raise ValueError('missing resources')
        declared=set()
        for name in names:
            if re.fullmatch(r'classes\d*\.dex',name): declared.update(classes(z.read(name)))
    pkg=next((x for x in subprocess.check_output([aapt,'dump','badging',path],text=True).splitlines() if x.startswith('package: ')),'')
    flags={
      'cinemana_application':'Lcom/shabakaty/cinemana/CinemanaApplication;' in declared,
      'cinemana_engine':'Lcom/shabakaty/cinemana/compat/nuvio/NuvioEngineProvider;' in declared,
      'cinemana_player':any(x.endswith('/VideoPlayerActivity;') for x in declared),
      'nuvio_main':'Lcom/nuvio/app/MainActivity;' in declared,
      'cinemana_package':"name='com.shabakaty.cinemana'" in pkg,
    }
    return {'checks':flags,'merged':all(flags.values()),'defined_classes':len(declared),'package':pkg}
if __name__=='__main__':
    try:
        aapt=sys.argv[2] if len(sys.argv)>2 else 'aapt'
        result=validate(sys.argv[1],aapt)
        print(json.dumps(result,indent=2))
        sys.exit(0 if result['merged'] else 2)
    except Exception as e:
        print(json.dumps({'merged':False,'error':str(e)}))
        sys.exit(3)
