"""Join pilot, forward cockpit, and touchdown captures into one shareable clip."""
import runtime
import subprocess
import imageio_ffmpeg

ROOT=runtime.ROOT
OUT=ROOT/'outputs'

def main():
    ffmpeg=imageio_ffmpeg.get_ffmpeg_exe()
    inputs=[]
    for name in ('captain','cockpit','touchdown'):
        path=OUT/f'{name}.mp4'
        if not path.exists():
            raise SystemExit(f'Capture {name}.mp4 first; see README.md')
        inputs += ['-i',str(path)]
    # Hard cuts intentionally skip uneventful approach time. Replay clocks
    # retain the source timestamps. Trim capture-start CSS transitions.
    filters='[0:v]trim=start=0:end=4,setpts=PTS-STARTPTS[a];[1:v]trim=start=0.5,setpts=PTS-STARTPTS[b];[2:v]trim=start=0.5,setpts=PTS-STARTPTS[c];[a][b][c]concat=n=3:v=1:a=0[v]'
    video=OUT/'fly-pilot-highlights.mp4'
    subprocess.run([ffmpeg,'-y','-loglevel','error',*inputs,'-filter_complex',filters,'-map','[v]',
                    '-an','-c:v','libx264','-crf','18','-preset','fast','-pix_fmt','yuv420p','-movflags','+faststart',str(video)],check=True)
    subprocess.run([ffmpeg,'-y','-loglevel','error','-i',str(video),'-filter_complex',
                    '[0:v]fps=12,scale=768:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=192[p];[b][p]paletteuse=dither=bayer',
                    '-loop','0',str(OUT/'fly-pilot-highlights.gif')],check=True)
    print('Saved fly-pilot-highlights.mp4 and fly-pilot-highlights.gif',flush=True)

if __name__=='__main__':
    main()
