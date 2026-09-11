"""Deterministically render a real rollout to H.264 MP4 and a smaller GIF.

No web server is required. Chromium opens the local, self-contained showcase.
Rendering can be slower than real time without changing the flight trajectory.
"""
import runtime
import argparse
import asyncio
import io
from pathlib import Path
import subprocess
import numpy as np
from PIL import Image

ROOT=runtime.ROOT

async def main(args):
    from playwright.async_api import async_playwright
    import imageio_ffmpeg
    out=ROOT/'outputs';out.mkdir(exist_ok=True)
    ffmpeg=imageio_ffmpeg.get_ffmpeg_exe()
    chromium=ROOT/'.deps/chrome-linux/headless_shell'
    if not chromium.exists():
        candidates=list((ROOT/'.deps').rglob('headless_shell'))
        if candidates:chromium=candidates[0]
    async with async_playwright() as p:
        browser=await p.chromium.launch(executable_path=str(chromium) if chromium.exists() else None,
            headless=True,args=['--no-sandbox','--disable-dev-shm-usage','--allow-file-access-from-files',
                '--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
        page=await browser.new_page(viewport={'width':1280,'height':720},device_scale_factor=1)
        errors=[]
        page.on('pageerror',lambda error:errors.append(str(error)))
        await page.goto((ROOT/'web'/('preview.html' if args.preview else 'index.html')).as_uri()+'?capture=1')
        await page.wait_for_function('window.__ready === true',timeout=60000)
        if args.camera != 'auto':
            await page.evaluate('(name)=>window.setCamera(name)', args.camera)
        if errors:raise RuntimeError('\n'.join(errors))
        duration=await page.evaluate('window.clipDuration')
        if args.still is not None:
            await page.evaluate('(t)=>window.seekTime(t)',args.still)
            await page.screenshot(path=str(out/'preview.png'))
            print('Saved outputs/preview.png',flush=True)
            await browser.close();return
        duration=max(0,duration-args.start)
        duration=min(duration,args.seconds) if args.seconds else duration
        if duration <= 0:raise ValueError('Clip start must be before the end of the replay')
        path=out/f'{args.name}.mp4'
        encoder=subprocess.Popen([ffmpeg,'-y','-loglevel','error','-f','image2pipe','-vcodec','mjpeg',
            '-r',str(args.fps),'-i','-','-an','-c:v','libx264','-preset','fast','-crf','19',
            '-pix_fmt','yuv420p','-movflags','+faststart',str(path)],stdin=subprocess.PIPE)
        try:
            count=int(duration*args.fps)
            for i in range(count):
                await page.evaluate('(t)=>window.seekTime(t)',args.start+i/args.fps)
                frame=await page.screenshot(type='jpeg',quality=94)
                encoder.stdin.write(frame)
                if i%args.fps==0:print(f'Rendering {i/args.fps:.0f}/{duration:.0f}s',flush=True)
                if i in (0,int(count*.3),int(count*.65),count-1):
                    (out/f'{args.name}-frame-{i:04d}.jpg').write_bytes(frame)
        finally:
            encoder.stdin.close();encoder.wait();await browser.close()
        if encoder.returncode:raise RuntimeError('Video encoding failed')
        if errors:raise RuntimeError('Browser errors: '+'; '.join(errors))
        subprocess.run([ffmpeg,'-y','-loglevel','error','-i',str(path),'-filter_complex',
            '[0:v]fps=12,scale=640:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=128[p];[b][p]paletteuse=dither=bayer',
            '-loop','0',str(out/f'{args.name}.gif')],check=True)
        print(f'Saved outputs/{args.name}.mp4 and outputs/{args.name}.gif',flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--fps',type=int,default=24);parser.add_argument('--seconds',type=float);parser.add_argument('--still',type=float);parser.add_argument('--preview',action='store_true')
    parser.add_argument('--start',type=float,default=0,help='Start time in displayed replay seconds')
    parser.add_argument('--camera',choices=['auto','pilot','cockpit','chase'],default='auto')
    parser.add_argument('--name',default='fly-pilot',help='Output filename stem')
    args=parser.parse_args()
    if args.start < 0 or args.fps <= 0 or (args.seconds is not None and args.seconds <= 0):
        parser.error('Use nonnegative start and positive fps/duration')
    if not args.name or Path(args.name).name != args.name or args.name in ('.','..'):
        parser.error('Name must be a filename stem')
    asyncio.run(main(args))
