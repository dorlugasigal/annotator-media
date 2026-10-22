# Annotator reel — design spec

Brand truth comes from the website (`website/src/styles/editorial.css`) and the
product's real ink colours sampled from the recordings.

## Palette

| Role | Hex | Use |
| --- | --- | --- |
| Night (brand stage) | `#0b101a` | Hook, end card, recording desktop behind the takes; frame 0 = last frame |
| Ink | `#f1f4fc` | Type on dark |
| Muted | `#b8c3d8` | Mono labels |
| Apricot (the pen) | `#ffb58c` | Every reel-drawn mark; Smart Draw caption slabs |
| Periwinkle | `#abc7ff` | Emphasised words ("any app."), one flood, focus caption slabs |
| Halo cyan | `#14ccd6` | The take's cursor halo, echoed on "pointer." |
| Teal ink | `#61919d` / light `#8fc3cc` | From the real rough ellipse |
| Arrow blue | `#5c71d7` | From the real curved arrow |
| Highlighter | `#edfa56` | From the site tokens / real highlighter |

Floods are solid fields (no full-screen linear gradients: they band in H.264).

## Type

- **Bricolage Grotesque** (self-hosted variable, weights 200–800): the gestural
  voice — huge, tight (-0.045em to -0.06em), weight contrast 300 vs 800.
- **JetBrains Mono** (bundled by the HyperFrames renderer): the end card's
  small caps tag, letter-spaced 0.16em.
- Captions: Bricolage 720, -0.04em, on slabs that change colour per take
  (night, apricot, periwinkle). Toolbar labels: Bricolage 640 under apricot
  brackets, pinned to the footage.

## Motion

- Grid: 130 BPM, beat 0.4615 s, bar 1.846 s, 64 beats = 29.5 s. Bars start on
  beats 2, 6, 10, ...: the second drop of the song lands on "Draw", the cuts on
  beats 30 and 42 and the end card on beat 58 fall on downbeats. Hits land on beats; secondary moves
  on the offbeat. Each native action is anchored to a beat in tools/shots.py.
- Marks draw with `power2.out` (a hand lifting), never bounce. Type slams with
  `power4.out` / `expo.out`; camera legs `power4.out` landings, `power2.inOut`
  repositioning. Blur envelopes ride their motion.
- Each caption does what it says, in step with the take underneath: "Circle
  it." gets circled, "Point at it." gets an arrow, "Bend it." gets a bending
  arrow, "Highlight it." gets a highlighter pass, "Draw it rough." gets a
  scribble that snaps into a clean box on "It snaps clean.", "Add a note."
  types itself, "pointer." gets a halo, "Spotlight it." is lit by a moving
  spotlight and "Blur" blurs inside a dragged selection.
- Hold each action: one camera move per action, then a slow push. Speed ramps
  stay near real time on the action and speed up only on pointer travel.
- When a tool is chosen, frame the toolbar until the click lands; the Effects
  choice also gets a hand-drawn ring pinned to the button.

## Sound

- Foley only, for actions you can see: a quiet mouse click, one real key per
  typed character, a soft pen stroke under hand-drawn ink. No whooshes, pops,
  risers or hits, and nothing for titles or cuts.

## Layout

- Desktop 1920x1080: caption slabs bottom-left or bottom-right, away from the
  action; end card headline left, wordmark bottom-right, arrow bridging them.
- Phone 1080x1350: caption slabs at the top (the toolbar is at the bottom of
  the portrait shots); end card stacked.
- Retina footage stays at or below 1.15 output px per capture px, except the
  toolbar close-up (1.35 desktop, 1.4 portrait, bicubic).

## Don't

- No fake UI, cursors or simulated product states.
- No claims beyond the site copy; blur is never called secure.
- No grain overlays (bitrate), no gradient text, no neon.
