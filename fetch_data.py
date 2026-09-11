"""Fetch public inputs and pinned renderer on a normally networked machine."""
from pathlib import Path
import hashlib
import json
import re
import urllib.request

ROOT=Path(__file__).resolve().parent

def fetch(url,path):
    path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists() and path.stat().st_size:
        print('Present:',path.relative_to(ROOT));return
    print('Downloading:',url,flush=True)
    req=urllib.request.Request(url,headers={'User-Agent':'fly-pilot-open-source-demo'})
    part=path.with_suffix(path.suffix+'.partial')
    with urllib.request.urlopen(req,timeout=180) as src,part.open('wb') as dst:
        while chunk:=src.read(1024*1024):dst.write(chunk)
    part.replace(path)

def main():
    upstream=ROOT/'third_party/flybrain';upstream.mkdir(parents=True,exist_ok=True)
    lock=upstream/'source.json'
    if lock.exists():commit=json.loads(lock.read_text(encoding='utf-8-sig'))['commit']
    else:
        req=urllib.request.Request('https://api.github.com/repos/snedea/flybrain/commits/main',headers={'User-Agent':'fly-pilot'})
        with urllib.request.urlopen(req,timeout=30) as response:commit=json.load(response)['sha']
        lock.write_text(json.dumps({'repository':'https://github.com/snedea/flybrain','commit':commit},indent=2))
    base=f'https://raw.githubusercontent.com/snedea/flybrain/{commit}'
    for name in ['connectome.bin.gz','neuron_meta.json']:fetch(base+'/data/'+name,ROOT/'data'/name)
    fetch(base+'/js/sim-worker.js',upstream/'sim-worker.js')
    fetch(base+'/license.md',upstream/'LICENSE.md')
    fetch('https://cdn.jsdelivr.net/npm/three@0.160.1/build/three.module.js',ROOT/'web/vendor/three.module.js')
    fetch('https://raw.githubusercontent.com/mrdoob/three.js/r160/LICENSE',ROOT/'web/vendor/THREE-LICENSE.txt')
    # Only invokes our own local bundler, not any downloaded script.
    import bootstrap_offline
    hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'data').iterdir() if p.is_file()}
    (upstream/'data-hashes.json').write_text(json.dumps(hashes,indent=2))
    print('Data and renderer ready.')

if __name__=='__main__':main()
