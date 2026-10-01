# Generated Art Sync Register — 2026-10-01

Repository: https://github.com/hulala337/plw
Canonical state: art-production-spec/ART_PRODUCTION_STATE.json
Style anchor: B01

## Production progress resynced

The repository state has been resynced through **F08**.

Generated in the production conversation and registered as pending binary persistence:
- C01 C02 C03
- E01 E02 E03 E04 E05 E06
- F01 F02 F03
- F06 F07 F08

B07 remains **SKIPPED BY USER**.

## Binary availability

The current GitHub connector can create UTF-8 text files and Git blobs when binary content is supplied as base64, but the recent ChatGPT-generated image outputs are not exposed to this connector as binary file references. Therefore this commit deliberately does **not** invent or substitute image binaries.

Known image files currently available in the ChatGPT Library include:
- B02_pelican_working.png
- B02_pelican_working_v2.png
- B02_pelican_working_v3.png
- B03_pelican_typing.png

Recent Pelican Workbench generated images are also present in the Library under descriptive filenames, but their exact asset-ID mapping must be confirmed before placing them under canonical asset folders.

## Required persistence layout

For each generated asset:
- art-assets/<ID>/candidates/<ID>_vNN.png
- art-assets/<ID>/review.json
- after human approval: art-assets/<ID>/approved/<ID>_vNN.png

No binary is marked APPROVED merely because a generation occurred.

## Next

When the actual image binaries are available through a local workspace or binary-capable upload route, run the existing intake/check pipeline and persist the files before advancing beyond F08.
