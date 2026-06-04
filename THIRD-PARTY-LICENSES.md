# Third-party licenses

This repository vendors third-party assets so it runs fully offline. Each is
redistributed under its own license, reproduced below / alongside the asset.

## Plotly.js v2.27.0 — MIT License
- File: `apps/vendor/plotly-2.27.0.min.js`
- Copyright (c) 2012-2023 Plotly, Inc.
- The MIT license header is retained at the top of the minified file.

## Web fonts — SIL Open Font License 1.1

Full license texts are bundled next to the fonts in `assets/fonts/`:

| Font | Copyright | License file |
|------|-----------|--------------|
| JetBrains Mono | Copyright 2020 The JetBrains Mono Project Authors | `assets/fonts/OFL-JetBrainsMono.txt` |
| Plus Jakarta Sans | Copyright 2020 The Plus Jakarta Sans Project Authors | `assets/fonts/OFL-PlusJakartaSans.txt` |
| Inter | Copyright (c) 2016 The Inter Project Authors | `assets/fonts/OFL-Inter.txt` |

The woff2 files in `assets/fonts/` are subsets served by Google Fonts and are
covered by the same OFL 1.1 texts above. The OFL permits bundling and
redistribution provided the copyright notice and license accompany the fonts
(satisfied here) and the fonts are not sold by themselves.

## Embedded analysis engines

The HTML engines under `apps/` are vendored verbatim from their own source
repositories (under `github.com/mahmood726-cyber`) and retain whatever license
those repositories declare. This hub adds no claim over them.
