# Native Camera partial-reset isolation experiment

Status: Completed; cross-row buffer overwrite reproduced. User explicitly asked
to test the native Camera claim. No production behavior changed, no commit/push.

## Setup

Installed IsaacLab346c74fe722ad371a6c663e3b384b3d172966d11, native Newton/Warp,
two environments, headless,150s timeout. Approximately17GiB available RAM and
7793MiB free VRAM checked before each run. Actual sensor class is exactly native
isaaclab.sensors.camera.Camera (asserted); supports_batch_update=True. Reused
current camera optics/pose/RGB+depth configuration, replaced only class_type.
Disabled target/metadata observation groups because they require project-only
read_sample; other environment machinery retained. Two box terrain rows, seed7.
No HeldDepthCamera instance supplies the tested buffers.

## Procedure

1. Reset/capture both rows; frame=[1,1], last_update=[0,0].
2. Advance two20ms steps and read: environment1 depth is still exactly held at
   t=.04s before its .1s capture is due.
3. Only reset camera row0 (or separately the entire environment0), inspect raw
   row1 WITHOUT lazy capture, then request camera.data to capture outdated row0.
4. Separate write-detection control: fill row1 raw depth with NaN. A clean
   camera.data read leaves all76800 markers intact. Resetting row0 still leaves
   them intact; requesting row0 capture overwrites all76800 markers.
5. Controlled actual scene change: after step2 move robot1 +.5m in world X and
   call sim.forward, without advancing the sensor clock or resetting row1.
   Its old buffer remains unchanged until row0 is reset and captured. This makes
   a changed rendered scene available while row1 is still logically held.

## Results

| Case | Changed row1 pixels after row0 capture | Row1 frame/last_update |
|---|---:|---|
| Camera-only partial reset, ordinary scene | 0 | unchanged:1 /0s |
| Environment partial reset, ordinary scene | 0 | unchanged:1 /0s |
| Camera-only partial reset after controlled scene change | 40645 /76800 | unchanged:1 /0s |

Maximum finite depth difference in the controlled case:4.591831684112549m.
In all three cases, ordinary reads and reset itself preserved the NaN marker;
only capture removed it. Thus the overwrite belongs to the capture/render path,
not merely a reset clearing memory. The scene-change case establishes actual
numeric image changes, beyond the separate artificial-marker write test.

Conclusion: native Camera data.output rows can be overwritten by another row's
capture while their own frame and last-update metadata remain unchanged. A simple
partial reset does not necessarily change pixels if the rendered scene is the
same; the original claim must not be read as every reset always changing images.
This supports a row-isolated snapshot for the approved training contract. It does
not prove a subclass is the only way to provide it, nor does it generalize to
other renderer backends or all camera update paths.

The direct camera.data read exercises native scalar capture; native batch
eligibility was confirmed, but this experiment does not separately characterize
scheduled multi-camera batch capture. RGB output was enabled; the measured
cross-row data in this report is image-plane depth.

## Retained evidence

Latest full diagnostic run exited 0; structured results are retained in
native-camera-isolation.json. A post-run invariant check confirmed held
before-capture values, marker preservation/removal, unchanged row1 metadata and
nonzero controlled-scene pixel changes. The one-off probe and verbose launch log
were removed during the user-requested cleanup after this investigation completed.
The setup and procedure above document the experiment; no executable reproduction
script is retained. Production code was not modified by this experiment.
