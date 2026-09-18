# Pelican Workbench V3.6-C — Office Environment Art Asset Rebuild

## Scope
This pass changes presentation/art assets only. Business logic, API/database access, TODO CRUD, statistics, replay controls, and existing state classes are not intentionally changed.

## New environment assets
- `office-room-base-v36.svg` — room/wall/floor base
- `office-window-day-v36.svg` — daytime window, skyline, sun and glass highlights
- `office-window-night-v36.svg` — nighttime window and city lights
- `office-window-cloud-v36.svg` — cloudy/mist window atmosphere
- `office-window-rain-v36.svg` — window glass rain drops
- `office-decor-v36.svg` — shelf, plant, wall art and clock
- `office-monitors-v36.svg` — dual-monitor workstation asset
- `office-desk-v36.svg` — physical desk surface, drawers and edge highlights
- `office-board-v36.svg` — physical board backing/frame behind the interactive TODO DOM
- `office-lamp-v36.svg` — desk lamp and warm light pool

## Integration
`index.html` now composes the scene from independent environment layers. The existing interactive `.board` DOM remains the data/UI source for TODO items; the new board illustration is only its physical backing.

`visual-v36c.css/js` only observes existing `scene` classes and `data-time` / `data-weather` attributes to present the art layers.

## Verification
- New SVG assets parsed successfully with Python XML parser.
- V3.6 visual JavaScript files pass `node --check`.
- Environment layers were rendered and composited for visual inspection.

## Known package limitation
This is an art/presentation package. The current source tree still does not contain `assets/app.js`; therefore it should not be treated as a complete business-logic release unless the corresponding application runtime package is merged separately.
