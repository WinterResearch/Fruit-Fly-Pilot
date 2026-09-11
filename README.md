

https://github.com/user-attachments/assets/a10171c7-0bf0-4354-bd90-74d48265fa29

# Fly Pilot

A fruit fly connectome drives roll and pitch controls in a JSBSim aircraft,
presented with a procedural 3D fly pilot, cockpit camera, and landing replay.

**Experimental, assisted control.** This is a fixed, signed rate network on
FlyWire-derived connectivity with an imitation-trained linear output adapter.
It is not a living fly, a faithful biological emulation, reinforcement learning,
or evidence that a natural fruit fly understands airplanes.

## What is real, and what is engineered?

| Component | Implementation |
|---|---|
| Wiring | FlyWire FAFB v783-derived graph distributed by snedea/flybrain. The imported node and edge counts are recorded with each rollout. This is the older female brain dataset, not MaleCNS. |
| Dynamics | Our signed, incoming-weight-normalized recurrent tanh rate model. All imported nodes and edges participate; the dataset itself is filtered. No claim of Shiu-model numerical equivalence. |
| Inputs | Ten instrument/guidance channels encoded by artificial electrodes in the upstream visual population. These assignments are not anatomical retinotopy. |
| Outputs | A small linear adapter reads non-injected neurons connected to the visual population, and drives aileron/elevator commands. No raw-state skip connection. |
| Learning | Ridge-regression imitation of an engineered attitude controller. The connectome weights remain fixed. |
| Assistance | Geometric approach director supplies desired bank/pitch. Separate throttle speed hold and post-touchdown braking. The fly network tracks those guidance cues. |
| Physics | JSBSim c172p aircraft model. Visual geometry is stylized and not an exact C172 cockpit or airframe. |
| Fly body | Procedural visual animation tied to commanded controls; no insect biomechanics simulation. |
| Neural inset | Recorded rate activations on a schematic layout, not spikes, dopamine, reconstructed anatomical coordinates, or emotion. |
| Video | A replay of saved physics/controller states. Playback speed is displayed. Camera direction and tower subtitles are scripted presentation. |

## Run

Python 3.10+ and a recent browser are recommended. A normal networked machine can use:

```sh
python -m venv .venv
# Linux/macOS:
source .venv/bin/activate
# Windows instead: .venv\Scripts\activate
pip install -r requirements.txt
python -m playwright install chromium
python fetch_data.py
python simulate.py --train
python record.py
```

Open `web/index.html` to play the recorded 3D flight, change camera, pause, or
scrub. The scene uses local scripts and needs no web server or API key.

For this workspace, Windows `download-deps.ps1` downloads the data and Linux
wheels without installing packages globally. Then, inside WSL:

```sh
python3 bootstrap_offline.py
python3 simulate.py --train
python3 record.py
```

The offline dependency path is `.deps/`; system Python remains untouched.
Chromium may need system libraries installed on minimal Linux distributions.

Short showcase segments (start times are displayed replay seconds):

```sh
python record.py --camera pilot --start 0 --seconds 5 --name captain
python record.py --camera cockpit --start 8 --seconds 6 --name cockpit
python record.py --camera chase --start 28 --seconds 8 --name touchdown
python neural_clips.py
python assemble_showcase.py
```

The first three commands write matching MP4/GIF files. `neural_clips.py` needs
no browser and produces 6-second approach and 8-second touchdown neural GIFs,
plus PNG stills, directly from the saved rollout. The 384 sampled values are
signed model rates, not biological spike measurements. Their positions are a
sample grid, not anatomical coordinates. Display brightness saturates at an
absolute rate of 0.125; command plots use separate scales for visibility.
The browser's stylized landing gear has a visual ground-contact correction;
this changes no recorded physics states, touchdown detection, or metrics.

`assemble_showcase.py` creates `outputs/fly-pilot-highlights.mp4` and `.gif`:
one edited sequence that switches from pilot close-up to forward cockpit to
exterior landing. Cuts skip parts of the approach; the source replay clocks
remain visible. These are real physics/controller recordings, not a continuous
real-time capture.

For the black-background 3D neural visualization:

```sh
python export_neural_scene.py
python render_neural_3d.py
```

These commands produce `outputs/neural-3d.mp4`, `.gif`, and `.png`. The
visualization displays 2,945 selected cells and 5,941 actual connections from
the imported graph. Neurons are grouped in schematic 3D clouds, not positioned
using anatomical coordinates. Glow is a logarithmic display of recorded rate
magnitude, not simulated action-potential flashes. Connections brighten based
on endpoint activity; no propagating spikes are claimed. The export checks
that recording this larger subset leaves every aircraft command unchanged.

## Outputs

- `outputs/fly-pilot.mp4`: H.264, 1280×720, 24 fps, no third-party music.
- `outputs/fly-pilot.gif`: smaller looping preview.
- `outputs/flight.json`: actual state/action/neural recording and provenance.
- `outputs/training.json`: training settings and fit diagnostics.
- `web/replay.js`: the browser's generated replay data.

Videos should be described as **an assisted aircraft controller using a
fly-connectome rate network**, not an unaided biological fly learning aviation.
A chosen successful clip does not establish general landing success.

## Checks and controls

```sh
python -m unittest test_brain.py
python simulate.py --mode teacher --name teacher
python simulate.py --mode disconnected --name disconnected
```

The disconnected control removes recurrent transmission while retaining the
same sensory encoding and output adapter. Comparing held-out initial conditions
with intact and disconnected networks tests whether neural signal transmission
matters for this demonstration. It does not establish that biological wiring is
superior to a random network; that would require retraining matched controls.

## Sources and licenses

Original code and procedural artwork: MIT, see `LICENSE`.

- [FlyWire](https://flywire.ai/), Dorkenwald et al., *Neuronal wiring diagram of an adult brain*, Nature (2024), DOI: [10.1038/s41586-024-07558-y](https://doi.org/10.1038/s41586-024-07558-y).
- [snedea/flybrain](https://github.com/snedea/flybrain): upstream packed data and metadata; its pinned source commit is stored in `third_party/flybrain/source.json`. Its MIT license is downloaded alongside the reference parser. Underlying scientific data retain their own terms.
- [JSBSim](https://github.com/JSBSim-Team/jsbsim): flight dynamics, LGPL-2.1. Loaded as a dependency; no JSBSim source is copied into this project's own code.
- [Three.js](https://threejs.org/): MIT. Its vendored license is in `web/vendor/THREE-LICENSE.txt`.
- [Playwright](https://playwright.dev/): Apache-2.0; development capture tool.
- FFmpeg: used through imageio-ffmpeg for local encoding; not included in the source release.

There are no game assets, airline logos, celebrity voices, or commercial songs.
The project does not claim endorsement by the research teams or tools above.
