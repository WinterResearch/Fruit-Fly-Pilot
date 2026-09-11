"""Offline 3D projection of recorded graph activity, with depth and glow.

This data visualization needs no browser. All displayed edges are imported
connectome edges; schematic positions and camera motion are presentation.
"""
import runtime
import json
import math
import subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageChops
from neural_clips import font
import imageio_ffmpeg

ROOT=runtime.ROOT
OUT=ROOT/'outputs'
W,H=960,640

def render(data,t,angle):
    frames=data['frames']
    idx=min(range(len(frames)),key=lambda k:abs(frames[k]['t']-t))
    frame=frames[idx]
    positions=np.asarray(data['positions'])
    edges=np.asarray(data['edges'])
    activity=np.asarray(frame['activity'])
    # The brightness scale exposes weak rates but never adds synthetic events.
    level=np.minimum(1,np.log1p(np.abs(activity)*100)/np.log(101))
    c,s=np.cos(angle),np.sin(angle)
    rotation=np.array([[c,0,s],[s*.16,.987,-c*.16],[-s*.987,.16,c*.987]])
    p=positions@rotation.T
    depth=8-p[:,2]
    scale=1080/depth
    xy=np.column_stack((W/2+p[:,0]*scale,325-p[:,1]*scale))
    colors=np.array([(115,225,255) if is_input else (255,188,101) if is_output else (152,139,249)
                     for is_input,is_output in zip(data['input'],data['readout'])])
    image=Image.new('RGB',(W,H),'#020408')
    lines=Image.new('RGB',(W,H))
    d=ImageDraw.Draw(lines)
    for a,b in edges[np.argsort((p[edges[:,0],2]+p[edges[:,1],2])/2)]:
        strength=(level[a]+level[b])/2
        color=(colors[a]+colors[b])/2*(.028+.20*strength)
        d.line((tuple(xy[a]),tuple(xy[b])),fill=tuple(color.astype(int)),width=1)
    image=ImageChops.add(image,lines)
    glow=Image.new('RGB',(W,H))
    g=ImageDraw.Draw(glow)
    d=ImageDraw.Draw(image)
    for i in np.argsort(p[:,2]):
        x,y=xy[i]
        strength=level[i]
        brightness=(.16+.84*strength)*min(1,scale[i]/130)
        color=tuple(np.minimum(255,colors[i]*brightness).astype(int))
        r=(.7+strength*2.2)*scale[i]/135
        g.ellipse((x-r*2,y-r*2,x+r*2,y+r*2),fill=color)
        d.ellipse((x-r,y-r,x+r,y+r),fill=color)
        if strength>.3:
            core=tuple(np.minimum(255,colors[i]*(.65+strength)).astype(int))
            d.ellipse((x-.55,y-.55,x+.55,y+.55),fill=core)
    image=ImageChops.add(image,glow.filter(ImageFilter.GaussianBlur(4)))
    image=ImageChops.add(image,glow.filter(ImageFilter.GaussianBlur(11)))
    d=ImageDraw.Draw(image)
    d.text((34,25),'D R O S O P H I L A   A I R L I N E S',font=font(13,True),fill='#86c8d8')
    d.text((34,53),'Inside the cockpit. Inside the network.',font=font(26,True),fill='#e7edf2')
    d.text((34,93),f"{len(positions):,} displayed neurons / {len(edges):,} mapped connections",font=font(13),fill='#9aaebf')
    d.text((34,538),'VISUAL INPUT',font=font(11,True),fill='#73e1ff')
    d.text((193,538),'OUTPUT READOUT',font=font(11,True),fill='#ffbc65')
    d.text((385,538),'OTHER NETWORK CELLS',font=font(11,True),fill='#988bf9')
    d.line((34,566,926,566),fill='#29313d',width=1)
    control=frame['controls']
    d.text((34,579),f"AILERON {control[0]:+.3f}    ELEVATOR {control[1]:+.3f}",font=font(16),fill='#ecf0f4')
    d.text((735,579),f'SIM {t:04.1f}s / 1.5×',font=font(14),fill='#9aaebf')
    d.text((34,612),'Recorded rate activations · schematic 3D layout · fixed wiring + trained adapter · assisted flight',font=font(12),fill='#8a99ac')
    return image

def main():
    data=json.loads((OUT/'neural-scene.json').read_text())
    ffmpeg=imageio_ffmpeg.get_ffmpeg_exe()
    start=data['touchdown_time']-9
    path=OUT/'neural-3d.mp4'
    process=subprocess.Popen([ffmpeg,'-y','-loglevel','error','-f','rawvideo','-pixel_format','rgb24','-video_size',f'{W}x{H}',
                              '-framerate','20','-i','-','-an','-c:v','libx264','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',str(path)],stdin=subprocess.PIPE)
    try:
        for i in range(160):
            t=start+i/20*1.5
            im=render(data,t,-.26+i/160*.55)
            process.stdin.write(im.tobytes())
            if i==80:im.save(OUT/'neural-3d.png')
            if i%20==0:print(f'Rendering 3D neural view {i//20}/8s',flush=True)
    finally:
        process.stdin.close();process.wait()
    if process.returncode:raise RuntimeError('Encoding failed')
    subprocess.run([ffmpeg,'-y','-loglevel','error','-i',str(path),'-filter_complex',
                    '[0:v]fps=10,scale=768:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=192[p];[b][p]paletteuse=dither=bayer',
                    '-loop','0',str(OUT/'neural-3d.gif')],check=True)
    print('Saved neural-3d.mp4, neural-3d.gif, neural-3d.png',flush=True)

if __name__=='__main__':
    main()
