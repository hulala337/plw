# P1 Acceptance Matrix

P1 is accepted only when Growth, Collection, Equipment and Today World form one idempotent chain.

## Progression
- Effective active time produces time XP; idle time never does.
- Todo completion grants XP once per completion event.
- Achievement rewards grant XP once.
- Refresh/restart never duplicates rewards.
- Forget Today does not erase lifetime Growth progress.

## Level / Unlock
- Level and XP progress persist in SQLite.
- Unlock catalog is typed and idempotent.
- Locked content cannot be equipped.

## Collection
- Pelicans, Outfits, Accessories, Scenes, Decorations, Effects are separate categories.
- Collection exposes locked/unlocked state.
- Default Scene/Pelican/Outfit exist on a fresh database.
- Multiple decorations can coexist.

## Equipment
- Scene/Pelican/Outfit/Accessory/Decoration/Effect selections persist.
- Unknown or locked items are rejected.
- Decoration equipment does not overwrite another decoration.

## World binding
- Dashboard exposes a normalized World projection.
- Today consumes equipped Scene/Pelican state.
- Multi-monitor adaptation only selects an unlocked Scene.
- Work state is available to World/Pelican without storing content.

## Self Test
- All P1 tables exist.
- Growth payload contains profile, collection, unlocks, achievements and equipment.
- Catalog seeding is idempotent.
- Default equipment exists.
- Frontend DOM contract remains valid.

Windows runtime acceptance remains required for final product acceptance.
