from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSS = ROOT / "web" / "assets" / "style.css"
MARKER = "/* PELICAN_WORKBENCH_VISUAL_POLISH_V2 */"

PATCH = r'''
/* PELICAN_WORKBENCH_VISUAL_POLISH_V2 */
:root{
  --pw-cream:#fffaf0;
  --pw-wood:#9b6848;
  --pw-wood-dark:#714b38;
  --pw-glass:rgba(255,255,255,.88);
  --pw-line:rgba(78,110,119,.15);
  --pw-focus:0 0 0 3px rgba(63,143,216,.14);
}

/* Shared interaction language: softer, more tactile, less admin-dashboard-like. */
.panel,.card,.stat-card,.metric-card,.timeline-card,.replay-card,.settings-card{
  transition:transform .22s ease,box-shadow .22s ease,border-color .22s ease,background .22s ease;
}
.panel:hover,.card:hover,.stat-card:hover,.metric-card:hover,.timeline-card:hover,.replay-card:hover,.settings-card:hover{
  transform:translateY(-2px);
  box-shadow:0 18px 42px rgba(31,65,78,.12);
  border-color:rgba(63,143,216,.18);
}
button:focus-visible,input:focus-visible,select:focus-visible,a:focus-visible{outline:none;box-shadow:var(--pw-focus)}

/* Home scene: make the office feel like one persistent place. */
.office-scene{background:#d6ecf6;box-shadow:0 20px 48px rgba(39,76,91,.14)}
.office-scene .window{box-shadow:0 18px 30px rgba(0,0,0,.08) inset,0 8px 15px rgba(20,52,69,.10),0 0 0 1px rgba(255,255,255,.18)}
.office-scene .monitor-screen{position:relative;overflow:hidden}
.office-scene .monitor-screen:after{content:"";position:absolute;inset:0;background:linear-gradient(115deg,rgba(255,255,255,.30),transparent 35%,rgba(80,160,190,.08));pointer-events:none}
.office-scene.working .monitor{box-shadow:0 0 0 2px rgba(117,184,232,.12),0 14px 20px rgba(20,43,58,.20)}
.office-scene.working .keyboard{box-shadow:0 5px 8px rgba(31,54,69,.15),0 0 18px rgba(117,184,232,.10)}
.office-scene.working .keyboard i:nth-child(3),.office-scene.working .keyboard i:nth-child(7){animation:key .55s infinite}
.office-scene.working .coffee em{opacity:.7}
.office-scene.resting .coffee em{animation-duration:3s}

/* Weather becomes a scene layer instead of a text-only status. */
.office-scene.raining:before{content:"";position:absolute;inset:0;z-index:6;pointer-events:none;background:repeating-linear-gradient(110deg,transparent 0 13px,rgba(91,153,185,.22) 14px 15px,transparent 16px 27px);opacity:.55;animation:pwRain .75s linear infinite}
.office-scene.raining .scene-sky{filter:saturate(.78) brightness(.94)}
.office-scene.snowing:before{content:"";position:absolute;inset:0;z-index:6;pointer-events:none;background-image:radial-gradient(circle,rgba(255,255,255,.92) 0 2px,transparent 2.5px),radial-gradient(circle,rgba(255,255,255,.72) 0 1.5px,transparent 2px);background-size:31px 31px,47px 47px;background-position:8px 0,19px 11px;animation:pwSnow 7s linear infinite}
.office-scene.snowing .scene-sky{filter:saturate(.62) brightness(1.03)}
.office-scene.overcast .sun{opacity:.25;box-shadow:none}
.office-scene.overcast .scene-sky{filter:saturate(.70) brightness(.96)}
.office-scene.thunderstorm:after{animation:pwFlash 5s infinite}
.office-scene.night.working .window:after{box-shadow:0 0 35px rgba(117,184,232,.10) inset}

/* Night + working are deliberately composable: do not hide the work state. */
.office-scene.night.working .pelican{animation:work .9s ease-in-out infinite}
.office-scene.night.working .monitor-screen{background:linear-gradient(130deg,#d9edf5,#8fbfd4)}

/* Growth/unlocks: keep the scene visually alive even when the DOM uses simple text tokens. */
.office-scene .growth-item,.office-scene .unlock-item,.office-scene .decor-item{filter:drop-shadow(0 4px 4px rgba(34,65,47,.16));animation:pwDecorIn .45s ease both}
.office-scene .growth-item:nth-child(2),.office-scene .unlock-item:nth-child(2){animation-delay:.08s}
.office-scene .growth-item:nth-child(3),.office-scene .unlock-item:nth-child(3){animation-delay:.16s}
.office-scene .growth-item:nth-child(4),.office-scene .unlock-item:nth-child(4){animation-delay:.24s}

/* Single / dual / multi-display states. JS can opt in with data-display-count without changing layout code. */
.office-scene[data-display-count="2"] .monitor{left:34%;width:205px}
.office-scene[data-display-count="2"] .monitor:after{content:"";position:absolute;left:calc(100% + 10px);top:0;width:205px;height:115px;background:#1c3244;border:8px solid #28485e;border-radius:13px;box-shadow:0 14px 18px rgba(20,43,58,.16)}
.office-scene[data-display-count="3"] .monitor{left:28%;width:190px}
.office-scene[data-display-count="3"] .monitor:after{content:"";position:absolute;left:calc(100% + 9px);top:0;width:190px;height:115px;background:#1c3244;border:8px solid #28485e;border-radius:13px;box-shadow:0 14px 18px rgba(20,43,58,.16)}

/* Keyboard and mouse feedback stays subtle; the numbers remain the source of truth. */
.office-scene.activity-keyboard .keyboard{animation:pwKeyPulse .65s ease}
.office-scene.activity-mouse .mouse,.office-scene.activity-mouse .mouse-cursor{animation:pwMousePulse .55s ease}
.office-scene .mouse-cursor{position:absolute;z-index:6;width:13px;height:18px;border:2px solid #35566a;border-radius:8px 8px 9px 4px;opacity:0;pointer-events:none;transform:rotate(-18deg)}
.office-scene.activity-mouse .mouse-cursor{opacity:.72;left:61%;bottom:22%}

/* Replay should look like the same office, not a second product. */
.replay-scene,.day-replay-scene,.replay-card .scene{border-radius:22px;overflow:hidden;background:linear-gradient(180deg,#d9f1f6,#d7d5bd 60%,#9d8864);box-shadow:inset 0 0 0 1px rgba(49,85,109,.10),0 16px 36px rgba(39,76,91,.10)}
.replay-scene .pelican,.day-replay-scene .pelican{filter:drop-shadow(0 11px 8px rgba(20,53,66,.18))}
.replay-scene .scene-bubble,.day-replay-scene .scene-bubble{background:rgba(255,255,255,.92);backdrop-filter:blur(6px)}

/* Timeline: stronger hierarchy and clearer active moments. */
.timeline-item,.timeline-row{transition:background .18s ease,transform .18s ease}
.timeline-item:hover,.timeline-row:hover{background:rgba(63,143,216,.055);transform:translateX(2px)}
.timeline-item.active,.timeline-row.active{box-shadow:inset 3px 0 0 var(--blue);background:rgba(63,143,216,.075)}

/* Stats keep the same data, but visually belong to the workbench. */
.stats-page .stat-card,.trends-page .stat-card{background:linear-gradient(145deg,rgba(255,255,255,.96),rgba(255,250,240,.90))}
.stats-page .chart,.trends-page .chart{border-radius:18px;background:rgba(255,255,255,.72);border:1px solid var(--pw-line);box-shadow:inset 0 1px 0 rgba(255,255,255,.8)}

/* Empty/loading/error states should feel intentional rather than broken. */
.empty,.empty-state,.loading,.loading-state,.error,.error-state{border:1px dashed rgba(63,143,216,.22);border-radius:18px;background:rgba(255,253,248,.70);padding:22px;text-align:center}
.empty:before,.empty-state:before{content:"🪶";display:block;font-size:25px;margin-bottom:6px;opacity:.72}

/* Responsive scene scaling. */
@media (max-width:1100px){
  main{padding:24px 22px 20px}
  .grid-hero{grid-template-columns:minmax(0,1fr) 290px}
  .office-scene{height:390px}
  .board{transform:scale(.88);transform-origin:top right}
  .monitor{transform:scale(.9);transform-origin:top center}
}
@media (max-width:860px){
  .app-shell{grid-template-columns:78px minmax(0,1fr)}
  .sidebar{padding:18px 9px}
  .brand strong,.brand span,.brand-signature,.nav em,.side-pet div,.side-foot{display:none}
  .brand{justify-content:center;padding:0 0 16px}
  .nav{justify-content:center;padding:12px 8px}
  .nav span{width:auto}
  .side-pet{justify-content:center;padding:10px}
  .grid-hero{grid-template-columns:1fr}
}
@media (max-width:620px){
  main{padding:18px 14px}
  .topbar{gap:12px}
  .topbar h1{font-size:23px}
  .clock{min-width:116px}
  .office-scene{height:350px}
  .window{width:62%;height:49%}
  .board{display:none}
  .monitor{left:37%;width:175px;height:96px}
  .keyboard{left:39%;width:155px;bottom:13%}
  .pelican{left:12%;transform:scale(.86);transform-origin:bottom left}
  .coffee{left:70%;transform:scale(.82);transform-origin:bottom left}
}

@media (prefers-reduced-motion:reduce){
  *,*:before,*:after{scroll-behavior:auto!important;animation-duration:.001ms!important;animation-iteration-count:1!important;transition-duration:.001ms!important}
}

@keyframes pwRain{from{transform:translateY(-18px)}to{transform:translateY(18px)}}
@keyframes pwSnow{from{transform:translateY(-24px)}to{transform:translateY(70px)}}
@keyframes pwFlash{0%,92%,100%{opacity:1}93%{opacity:.72}94%{opacity:1}}
@keyframes pwDecorIn{from{opacity:0;transform:translateY(5px) scale(.96)}to{opacity:1;transform:none}}
@keyframes pwKeyPulse{0%,100%{filter:none}45%{filter:brightness(1.08) drop-shadow(0 0 6px rgba(117,184,232,.22))}}
@keyframes pwMousePulse{0%,100%{transform:translate(0,0) rotate(-18deg)}45%{transform:translate(7px,-4px) rotate(-18deg)}}
'''.strip() + "\n"


def main() -> int:
    if not CSS.exists():
        raise SystemExit(f"style.css not found: {CSS}")
    current = CSS.read_text(encoding="utf-8")
    if MARKER in current:
        print("[VISUAL] V2 polish already applied.")
        return 0
    CSS.write_text(current.rstrip() + "\n\n" + PATCH, encoding="utf-8")
    print("[VISUAL] Applied Pelican Workbench V2 visual polish.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
