# Cursor-led native demonstration

The first two seconds introduce the product. The main recording then runs
continuously at 2x, retaining control choices, cursor travel and results.
The toolbar stays in view; restrained pan/zoom uses captured coordinates.
The native picture is downsampled to 1280x960, never enlarged.

| Section | Visual role |
| --- | --- |
| Make your point | Large warm-white/copper type on navy |
| Start with the question | Type the title; toolbar and color choice visible |
| Draw it. Name it. | Smart Draw API/cache with centered owner labels |
| Pick the right shape | Resizable Tools and current Database/Person artwork |
| Connect the parts | Native line construction and arrowhead choices |
| Make the path clear | Label the cache-miss route |
| Point out what matters | Highlight and a short pen underline |
| Move it. Keep the label. | Owner label stays attached through move/Undo |
| Keep the focus | Native Blur over a real controlled browser window |
| Annotator | Free/private-preview status and CC BY music credit |

`website/src/data/native-demo.json` is generated from the exact source chapter
times. `native-quality-source.json` records cursor/control geometry and
`assets/cursor-tracked.mp4` is the preprocessed camera master.
The composed total is 51.816667 seconds at 60 fps.

Two-frame temporal blending is enabled only during camera movement.
An earlier aggressive camera/three-frame blend smeared text and was rejected
before delivery. All recorded control presses must remain visible, and
upscaling is prohibited by the camera test.

The soundtrack is Punch Deck's "Chrome Funk" under CC BY 4.0.
This is a new candidate; owner listening/creative approval remains open.
