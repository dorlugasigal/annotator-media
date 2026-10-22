# Annotator media

The promo film and the reel for [Annotator](https://github.com/dorlugasigal/annotator),
as [HyperFrames](https://github.com/heygen-com/hyperframes) projects. They live
here so a clone of the app stays small.

| Folder | What it is |
| --- | --- |
| `annotator-native-promo/` | The product film, built from real recordings of the Mac app |
| `annotator-reel/` | The short reel on the website and in the README |

For demo work, clone this repository into `videos/` inside an Annotator
checkout. The app repository ignores that folder, and its demo tools
(`tools/demo/`) and recording tests read it there:

```sh
git clone https://github.com/dorlugasigal/annotator-media videos
```

## Licenses

The music, sound effects, fonts and vendored scripts keep their own licenses;
see each folder's `THIRD_PARTY_NOTICES.md` and the credits in the films.
Annotator's recordings, artwork and storyboards here may be used to talk about
Annotator. The Annotator name and icon follow the app repository's
[TRADEMARK.md](https://github.com/dorlugasigal/annotator/blob/main/TRADEMARK.md).
Don't reuse a music track on its own; get it from its source under its license.
