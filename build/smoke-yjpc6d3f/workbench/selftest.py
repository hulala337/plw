from __future__ import annotations

from . import runtime


def self_test() -> int:
    from . import application, database, desktop, services, tracking

    "Offline + hook smoke test used by the Windows release pipeline."
    try:
        database.init_db()
        database.recover_stale_sessions()
        database.ensure_today()
        if not (runtime.WEB / "index.html").is_file():
            raise RuntimeError("web/index.html missing")
        if not (runtime.WEB / "assets").is_dir():
            raise RuntimeError("web/assets missing")
        paths = {getattr(route, "path", "") for route in runtime.api.routes}
        required_paths = {
            "/",
            "/api/dashboard",
            "/api/world",
            "/api/health",
            "/api/display-info",
            "/api/settings",
            "/api/growth",
            "/api/todos",
            "/api/forget-today",
            "/api/replay",
            "/api/export/csv",
            "/api/export/xlsx",
            "/api/equipment",
        }
        missing = required_paths - paths
        if missing:
            raise RuntimeError(
                "required API routes missing: " + ", ".join(sorted(missing))
            )
        html = (runtime.WEB / "index.html").read_text(encoding="utf-8")
        js = (runtime.WEB / "assets" / "app.js").read_text(encoding="utf-8")
        if 'data-view="growth"' not in html or 'id="view-growth"' not in html:
            raise RuntimeError("Growth UI navigation/view missing")
        import re

        html_ids = set(re.findall('id="([^"]+)"', html))
        js_ids = set(re.findall("\\$\\('([^']+)'\\)", js))
        missing_dom = sorted(js_ids - html_ids)
        if missing_dom:
            raise RuntimeError(
                "frontend DOM contract missing IDs: " + ", ".join(missing_dom)
            )
        for view in ("home", "replay", "timeline", "stats", "growth", "settings"):
            if f'id="view-{view}"' not in html:
                raise RuntimeError("frontend view missing: " + view)
        services.seed_progression_catalog()
        conn = database.db()
        required_tables = {
            "progress_profile",
            "progress_events",
            "unlocks",
            "achievements",
            "equipment",
            "scenes",
            "pelicans",
            "outfits",
            "accessories",
            "decorations",
            "effects",
        }
        actual_tables = {
            r["name"]
            for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        if required_tables - actual_tables:
            conn.close()
            raise RuntimeError(
                "P1 tables missing: "
                + ", ".join(sorted(required_tables - actual_tables))
            )
        conn.close()
        gp = services.growth_payload()
        if not {
            "profile",
            "collection",
            "equipment",
            "scenes",
            "pelicans",
            "unlock_catalog",
            "achievement_catalog",
        }.issubset(gp):
            raise RuntimeError("P1 growth payload incomplete")
        if set(gp["collection"]) != {
            "pelicans",
            "outfits",
            "accessories",
            "scenes",
            "decorations",
            "effects",
        }:
            raise RuntimeError("P1 collection categories incomplete")
        xp_before = gp["profile"]["xp"]
        xp_after = services.growth_payload()["profile"]["xp"]
        if xp_before != xp_after:
            raise RuntimeError("P1 progression is not idempotent")
        if not any((x["id"] == "office" and x["unlocked"] for x in gp["scenes"])):
            raise RuntimeError("default scene not unlocked")
        if not any((x["id"] == "classic" and x["unlocked"] for x in gp["pelicans"])):
            raise RuntimeError("default pelican not unlocked")
        equipment_by_slot = {
            x["slot"]: x
            for x in gp["equipment"]
            if not x["slot"].startswith("decoration:")
        }
        for slot, item_id in (
            ("scene", "office"),
            ("pelican", "classic"),
            ("outfit", "default"),
        ):
            if equipment_by_slot.get(slot, {}).get("item_id") != item_id:
                raise RuntimeError("default equipment missing: " + slot)
        world = services.world_payload()
        required_world = {
            "scene",
            "selected_scene",
            "pelican",
            "outfit",
            "decorations",
            "display_count",
            "work_state",
            "pelican_state",
            "time_phase",
            "weather_enabled",
        }
        if not required_world.issubset(world):
            raise RuntimeError("world projection incomplete")
        info = desktop.display_info()
        if not isinstance(info.get("count"), int):
            raise RuntimeError("display detection returned invalid data")
        if not tracking.listeners_start():
            raise RuntimeError(
                f"input listeners failed to start: {runtime.listener_error}"
            )
        runtime.time.sleep(0.35)
        if not tracking.listeners_healthy():
            raise RuntimeError(
                f"input listeners stopped immediately: {runtime.listener_error}"
            )
        day = services.today_key()
        conn = database.db()
        before_row = conn.execute("SELECT * FROM daily WHERE day=?", (day,)).fetchone()
        if before_row is None:
            conn.close()
            raise RuntimeError("daily row missing")
        before = dict(before_row)
        conn.close()
        self_test_slice = "__self_test__"
        tracking.queue_input(
            keys=1, text_chars=1, cursor_distance_px=123.0, monitor_switches=1
        )
        tracking.persist_tracker_tick(day, self_test_slice, self_test_slice, 0.0, 1)
        conn = database.db()
        after = dict(conn.execute("SELECT * FROM daily WHERE day=?", (day,)).fetchone())
        expected = {
            "keys": 1,
            "text_chars": 1,
            "cursor_distance_px": 123.0,
            "activity_events": 1,
            "monitor_switches": 1,
        }
        for key, delta in expected.items():
            if (after.get(key) or 0) != (before.get(key) or 0) + delta:
                raise RuntimeError("input pipeline persistence check failed: " + key)
        columns = [key for key in before if key != "day"]
        assignments = ", ".join(("%s=?" % key for key in columns))
        conn.execute(
            "UPDATE daily SET %s WHERE day=?" % assignments,
            [before[key] for key in columns] + [day],
        )
        conn.commit()
        conn.close()
        before_pending = before
        original_db = database.db
        failure = {"armed": True}

        def fail_once_db():
            if failure["armed"]:
                failure["armed"] = False
                raise RuntimeError("self-test simulated database outage")
            return original_db()

        tracking.queue_input(keys=1)
        database.db = fail_once_db
        try:
            try:
                tracking.persist_tracker_tick(
                    day, self_test_slice, self_test_slice, 0.0, 1
                )
            except RuntimeError:
                pass
            else:
                raise RuntimeError("pending recovery failure was not simulated")
        finally:
            database.db = original_db
        with runtime.pending_lock:
            if runtime.pending["keys"] != 1:
                raise RuntimeError("pending input was lost during database failure")
        tracking.persist_tracker_tick(day, self_test_slice, self_test_slice, 0.0, 1)
        with runtime.pending_lock:
            if runtime.pending["keys"] != 0:
                raise RuntimeError("pending input was not cleared after recovery")
        conn = database.db()
        recovered = dict(
            conn.execute("SELECT * FROM daily WHERE day=?", (day,)).fetchone()
        )
        conn.execute(
            "DELETE FROM activity_slices WHERE slice_start=? AND category=?",
            (self_test_slice, self_test_slice),
        )
        conn.execute(
            "DELETE FROM app_usage WHERE day=? AND category=?", (day, self_test_slice)
        )
        columns = [key for key in before_pending if key != "day"]
        assignments = ", ".join(("%s=?" % key for key in columns))
        conn.execute(
            "UPDATE daily SET %s WHERE day=?" % assignments,
            [before_pending[key] for key in columns] + [day],
        )
        conn.commit()
        conn.close()
        conn = database.db()
        cur = conn.execute(
            "INSERT INTO focus_sessions(started_at) VALUES(?)",
            (
                (runtime.datetime.now() - runtime.timedelta(hours=1)).isoformat(
                    timespec="seconds"
                ),
            ),
        )
        stale_id = cur.lastrowid
        conn.commit()
        conn.close()
        database.recover_stale_sessions()
        conn = database.db()
        stale = conn.execute(
            "SELECT ended_at,ended_reason FROM focus_sessions WHERE id=?", (stale_id,)
        ).fetchone()
        conn.execute("DELETE FROM focus_sessions WHERE id=?", (stale_id,))
        conn.commit()
        conn.close()
        if not stale or not stale["ended_at"] or stale["ended_reason"] != "recovered":
            raise RuntimeError("stale Session recovery failed")
        runtime.threading.Thread(
            target=tracking.tracker, daemon=True, name="tracker"
        ).start()
        application.run_server()
        if not application.wait_for_server():
            raise RuntimeError("local API server failed to start during self-test")
        import urllib.request

        def http_json(path, method="GET", body=None):
            req = urllib.request.Request(
                f"http://127.0.0.1:{runtime.PORT}{path}",
                data=runtime.json.dumps(body).encode("utf-8")
                if body is not None
                else None,
                headers={"Content-Type": "application/json"},
                method=method,
            )
            with urllib.request.urlopen(req, timeout=3) as response:
                return (
                    response.status,
                    runtime.json.loads(response.read().decode("utf-8")),
                )

        status, health = http_json("/api/health")
        if (
            status != 200
            or health.get("database") is not True
            or health.get("tracker") is not True
            or (health.get("keyboard_listener") is not True)
            or (health.get("mouse_listener") is not True)
        ):
            raise RuntimeError("HTTP health contract failed")
        for path in (
            "/api/dashboard?range=today",
            "/api/growth",
            "/api/world",
            "/api/display-info",
            "/api/settings",
            "/api/replay",
        ):
            status, payload = http_json(path)
            if status != 200 or not isinstance(payload, dict):
                raise RuntimeError("HTTP API contract failed: " + path)
        for path, method, body, expected in (
            ("/api/replay?day=2026-02-30", "GET", None, 400),
            ("/api/replay?day=20261002", "GET", None, 400),
            ("/api/export/csv?range=invalid", "GET", None, 400),
            ("/api/export/xlsx?range=invalid", "GET", None, 400),
            ("/api/todos", "POST", {"title": "   "}, 422),
            ("/api/settings", "PATCH", {"idle_seconds": 901}, 422),
        ):
            try:
                http_json(path, method, body)
            except urllib.error.HTTPError as exc:
                error_payload = runtime.json.loads(exc.read().decode("utf-8"))
                if "detail" not in error_payload or "code" not in error_payload:
                    raise RuntimeError("Error response contract missing")
                if exc.code != expected:
                    raise RuntimeError(
                        f"Invalid request returned {exc.code}, expected {expected}: {path}"
                    )
            else:
                raise RuntimeError("Invalid request was accepted: " + path)
        conn = database.db()
        original_equipment = [
            dict(x) for x in conn.execute("SELECT * FROM equipment").fetchall()
        ]
        conn.execute(
            "INSERT OR REPLACE INTO scenes(id,name,required_level,base_id,weather,time_mode,monitor_mode) VALUES(?,?,?,?,?,?,?)",
            (
                "__self_test_locked__",
                "Self Test Locked",
                999,
                "office",
                "clear",
                "auto",
                "auto",
            ),
        )
        conn.execute(
            "INSERT OR REPLACE INTO decorations(id,name,required_level,slot) VALUES(?,?,?,?)",
            ("__self_test_dec_a__", "Self Test A", 1, "room"),
        )
        conn.execute(
            "INSERT OR REPLACE INTO decorations(id,name,required_level,slot) VALUES(?,?,?,?)",
            ("__self_test_dec_b__", "Self Test B", 1, "room"),
        )
        conn.commit()
        conn.close()
        try:
            import urllib.error

            def expect_http_error(path, expected_status, body):
                try:
                    http_json(path, "PATCH", body)
                except urllib.error.HTTPError as exc:
                    if exc.code != expected_status:
                        raise RuntimeError(
                            "unexpected equipment error status: " + str(exc.code)
                        )
                    return
                raise RuntimeError("expected equipment HTTP error was not raised")

            expect_http_error(
                "/api/equipment",
                404,
                {"slot": "scene", "item_id": "__self_test_missing__"},
            )
            expect_http_error(
                "/api/equipment",
                403,
                {"slot": "scene", "item_id": "__self_test_locked__"},
            )
            http_json(
                "/api/equipment",
                "PATCH",
                {"slot": "decoration", "item_id": "__self_test_dec_a__"},
            )
            http_json(
                "/api/equipment",
                "PATCH",
                {"slot": "decoration", "item_id": "__self_test_dec_b__"},
            )
            status, equip = http_json(
                "/api/equipment",
                "PATCH",
                {"slot": "decoration", "item_id": "__self_test_dec_a__"},
            )
            if (
                status != 200
                or not any(
                    (
                        x["slot"] == "decoration:__self_test_dec_a__"
                        for x in equip["equipment"]
                    )
                )
                or (
                    not any(
                        (
                            x["slot"] == "decoration:__self_test_dec_b__"
                            for x in equip["equipment"]
                        )
                    )
                )
            ):
                raise RuntimeError("multiple decoration equipment did not coexist")
        finally:
            conn = database.db()
            conn.execute(
                "DELETE FROM equipment WHERE slot LIKE 'decoration:__self_test_%'"
            )
            conn.execute("DELETE FROM scenes WHERE id='__self_test_locked__'")
            conn.execute(
                "DELETE FROM decorations WHERE id IN ('__self_test_dec_a__','__self_test_dec_b__')"
            )
            for row in original_equipment:
                conn.execute(
                    "INSERT INTO equipment(slot,item_type,item_id,updated_at) VALUES(?,?,?,?) ON CONFLICT(slot) DO UPDATE SET item_type=excluded.item_type,item_id=excluded.item_id,updated_at=excluded.updated_at",
                    (row["slot"], row["item_type"], row["item_id"], row["updated_at"]),
                )
            conn.commit()
            conn.close()
        status, todo = http_json(
            "/api/todos", "POST", {"title": "__self_test_todo__\u9e48\u9e55\U0001f426"}
        )
        if status != 200 or "id" not in todo:
            raise RuntimeError("Todo create API failed")
        tid = todo["id"]
        try:
            xp0 = services.growth_payload()["profile"]["xp"]
            first = http_json(f"/api/todos/{tid}", "PATCH", {"done": True})[1]
            xp1 = services.growth_payload()["profile"]["xp"]
            if first.get("completion_count") != 1 or xp1 < xp0 + 20:
                raise RuntimeError("Todo first-completion reward failed")
            http_json(f"/api/todos/{tid}", "PATCH", {"done": True})
            xp2 = services.growth_payload()["profile"]["xp"]
            if xp2 != xp1:
                raise RuntimeError("Todo completion reward is not idempotent")
            http_json(f"/api/todos/{tid}", "PATCH", {"done": False})
            second = http_json(f"/api/todos/{tid}", "PATCH", {"done": True})[1]
            xp3 = services.growth_payload()["profile"]["xp"]
            if second.get("completion_count") != 2 or xp3 < xp2 + 20:
                raise RuntimeError("Todo re-completion reward failed")
        finally:
            with runtime.suppress(Exception):
                http_json(f"/api/todos/{tid}", "DELETE")
        print(
            "Pelican Workbench self-test: PASS (DB + real hooks + display + HTTP API + frontend contract)"
        )
        return 0
    except Exception as exc:
        runtime.logger.exception("Self-test failed")
        print(f"Pelican Workbench self-test: FAIL: {exc}")
        return 1
    finally:
        application.shutdown_runtime()
        if runtime._SELF_TEST_DIR:
            import logging

            logging.shutdown()
            runtime._SELF_TEST_DIR.cleanup()
