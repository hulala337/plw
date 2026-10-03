from __future__ import annotations

from . import runtime


def mark_event() -> None:
    runtime.last_input_ts = runtime.time.time()
    with runtime.LOCK:
        runtime.state["event_seq"] += 1


def queue_input(**kwargs) -> None:
    """Fast, exception-safe input hook path. SQLite is flushed by tracker()."""
    now = runtime.time.time()
    runtime.last_input_ts = now
    with runtime.LOCK:
        runtime.state["event_seq"] += 1
    with runtime.pending_lock:
        for key, value in kwargs.items():
            if key in runtime.pending:
                runtime.pending[key] += value
        runtime.pending["activity_events"] += 1


def flush_pending() -> None:
    from . import database, services

    database.ensure_today()
    with runtime.pending_lock:
        batch = {k: v for k, v in runtime.pending.items() if v}
    if not batch:
        return
    with runtime.LOCK:
        conn = database.db()
        try:
            sets = ", ".join(("%s=%s+?" % (k, k) for k in batch))
            conn.execute(
                "UPDATE daily SET %s WHERE day=?" % sets,
                [*batch.values(), services.today_key()],
            )
            conn.commit()
        except Exception:
            with runtime.suppress(Exception):
                conn.rollback()
            raise
        finally:
            conn.close()
    with runtime.pending_lock:
        for key, value in batch.items():
            runtime.pending[key] = max(0, runtime.pending[key] - value)


def persist_tracker_tick(
    day: str, slice_key: str, category: str, dt: float, events: int = 0
) -> None:
    from . import database

    "Atomically persist one tracker tick and all queued input counters."
    with runtime.LOCK:
        with runtime.pending_lock:
            batch = {k: v for k, v in runtime.pending.items() if v}
        conn = database.db()
        try:
            conn.execute("INSERT OR IGNORE INTO daily(day) VALUES(?)", (day,))
            conn.execute(
                "INSERT OR IGNORE INTO progress_profile(id,xp,total_active_seconds,level,updated_at) VALUES(1,0,0,1,?)",
                (runtime.datetime.now().isoformat(timespec="seconds"),),
            )
            updates = dict(batch)
            time_field = "active_seconds" if category != "idle" else "idle_seconds"
            updates[time_field] = updates.get(time_field, 0) + dt
            sets = ", ".join((f"{k}={k}+?" for k in updates))
            conn.execute(
                f"UPDATE daily SET {sets} WHERE day=?", [*updates.values(), day]
            )
            if time_field == "active_seconds" and dt > 0:
                conn.execute(
                    "UPDATE progress_profile SET total_active_seconds=total_active_seconds+?,updated_at=? WHERE id=1",
                    (dt, runtime.datetime.now().isoformat(timespec="seconds")),
                )
            conn.execute(
                "INSERT INTO activity_slices(slice_start,category,seconds,events)\n                   VALUES(?,?,?,?)\n                   ON CONFLICT(slice_start,category) DO UPDATE\n                   SET seconds=seconds+excluded.seconds,events=events+excluded.events",
                (slice_key, category, int(round(dt)), events),
            )
            conn.execute(
                "INSERT INTO app_usage(day,category,seconds) VALUES(?,?,?)\n                   ON CONFLICT(day,category) DO UPDATE SET seconds=seconds+excluded.seconds",
                (day, category, dt),
            )
            conn.commit()
        except Exception:
            with runtime.suppress(Exception):
                conn.rollback()
            raise
        finally:
            conn.close()
    if batch:
        with runtime.pending_lock:
            for key, value in batch.items():
                runtime.pending[key] = max(0, runtime.pending[key] - value)

    from . import key_counts
    key_counts.flush(database.db)


def incr(**kwargs) -> None:
    from . import database, services

    database.ensure_today()
    if not kwargs:
        return
    with runtime.LOCK:
        conn = database.db()
        sets = ", ".join((f"{k}={k}+?" for k in kwargs))
        conn.execute(
            f"UPDATE daily SET {sets} WHERE day=?",
            [*kwargs.values(), services.today_key()],
        )
        conn.commit()
        conn.close()


def key_is_text(key) -> bool:
    with runtime.suppress(Exception):
        ch = key.char
        return bool(ch) and (ch.isprintable() or ch == "\t")
    return False


def on_press(key) -> None:
    from . import tracking

    try:
        runtime.listener_last_keyboard_event = runtime.time.time()
        payload = {"keys": 1}
        if key == runtime.keyboard.Key.backspace:
            payload["backspace"] = 1
        elif key == runtime.keyboard.Key.delete:
            payload["delete_count"] = 1
        elif key == runtime.keyboard.Key.enter:
            payload["enter_count"] = 1
        elif key == runtime.keyboard.Key.space:
            payload["space_count"] = 1
        elif tracking.key_is_text(key):
            payload["text_chars"] = 1
        tracking.queue_input(**payload)
        from . import key_counts
        key_counts.record(key)
    except Exception:
        return


def on_click(x, y, button, pressed) -> None:
    from . import tracking

    if not pressed:
        return
    try:
        runtime.listener_last_mouse_event = runtime.time.time()
        if button == runtime.mouse.Button.left:
            tracking.queue_input(left_click=1)
        elif button == runtime.mouse.Button.right:
            tracking.queue_input(right_click=1)
        elif button == runtime.mouse.Button.middle:
            tracking.queue_input(middle_click=1)
    except Exception:
        return


def on_scroll(x, y, dx, dy) -> None:
    from . import tracking

    try:
        runtime.listener_last_mouse_event = runtime.time.time()
        tracking.queue_input(scroll_events=1, scroll_distance_px=abs(dy) * 120)
    except Exception:
        return


def refresh_monitor_layout(force: bool = False) -> list[dict]:
    if not force and runtime.time.time() - runtime.monitor_layout_ts < 5:
        return runtime.monitor_layout
    monitors = []
    try:
        import win32api as _wapi

        for index, (_handle, _hdc, rect) in enumerate(_wapi.EnumDisplayMonitors()):
            left, top, right, bottom = map(int, rect)
            monitors.append(
                {
                    "index": index,
                    "left": left,
                    "top": top,
                    "right": right,
                    "bottom": bottom,
                    "width": right - left,
                    "height": bottom - top,
                }
            )
    except Exception:
        monitors = []
    signature = tuple(
        sorted(((m["left"], m["top"], m["right"], m["bottom"]) for m in monitors))
    )
    if (
        runtime.monitor_layout_signature
        and signature != runtime.monitor_layout_signature
    ):
        runtime.last_xy = None
        runtime.last_monitor_index = None
    runtime.monitor_layout = monitors
    runtime.monitor_layout_signature = signature
    runtime.monitor_layout_ts = runtime.time.time()
    return runtime.monitor_layout


def monitor_at(x: int, y: int) -> tuple[int, int, int, int] | None:
    from . import tracking

    layout = tracking.refresh_monitor_layout()
    for m in layout:
        if m["left"] <= x < m["right"] and m["top"] <= y < m["bottom"]:
            return (m["left"], m["top"], m["right"], m["bottom"])
    layout = tracking.refresh_monitor_layout(force=True)
    for m in layout:
        if m["left"] <= x < m["right"] and m["top"] <= y < m["bottom"]:
            return (m["left"], m["top"], m["right"], m["bottom"])
    return None


def on_move(x, y) -> None:
    from . import tracking

    try:
        runtime.listener_last_mouse_event = runtime.time.time()
        xi, yi = (int(x), int(y))
        current_monitor = tracking.monitor_at(xi, yi)
        if runtime.last_xy is not None:
            dist = runtime.math.hypot(xi - runtime.last_xy[0], yi - runtime.last_xy[1])
            if runtime.math.isfinite(dist) and dist >= 0:
                payload = {"cursor_distance_px": dist}
                if (
                    runtime.last_monitor_index is not None
                    and current_monitor is not None
                    and (current_monitor != runtime.last_monitor_index)
                ):
                    payload["monitor_switches"] = 1
                tracking.queue_input(**payload)
        runtime.last_xy = (xi, yi)
        runtime.last_monitor_index = current_monitor
    except Exception:
        return


def foreground_context() -> tuple[str, str]:
    if runtime.win32gui and runtime.win32process:
        with runtime.suppress(Exception):
            hwnd = runtime.win32gui.GetForegroundWindow()
            _, pid = runtime.win32process.GetWindowThreadProcessId(hwnd)
            proc = runtime.psutil.Process(pid)
            return (
                (proc.name() or "").lower(),
                runtime.win32gui.GetWindowText(hwnd) or "",
            )
    return ("", "")


def _close_focus_session(
    session_id,
    session_started,
    session_active,
    session_last_active,
    session_events,
    categories,
    reason,
):
    from . import database

    if not session_id or not session_started:
        return
    end_dt = runtime.datetime.fromtimestamp(
        session_last_active or runtime.time.time()
    ).isoformat(timespec="seconds")
    conn = database.db()
    conn.execute(
        "UPDATE focus_sessions SET ended_at=?,active_seconds=?,break_seconds=?,event_count=?,categories=?,ended_reason=? WHERE id=?",
        (
            end_dt,
            round(session_active),
            max(
                0,
                round(
                    runtime.time.time() - (session_last_active or runtime.time.time())
                ),
            ),
            session_events,
            ",".join(categories),
            reason,
            session_id,
        ),
    )
    conn.commit()
    conn.close()


def tracker() -> None:
    from . import database, services, tracking

    prev = runtime.time.time()
    session_id = None
    session_started = None
    session_active = 0.0
    session_last_active = None
    last_seq = runtime.state["event_seq"]
    session_events = 0
    categories = []
    local_reset_seq = runtime.tracker_reset_seq
    while not runtime.STOP.is_set():
        now = runtime.time.time()
        dt = min(now - prev, 5.0)
        active = runtime.last_input_ts > 0 and now - runtime.last_input_ts <= int(
            database.setting_get("idle_seconds", str(runtime.IDLE_SECONDS))
        )
        if local_reset_seq != runtime.tracker_reset_seq:
            session_id = None
            session_started = None
            session_active = 0.0
            session_last_active = None
            session_events = 0
            categories = []
            local_reset_seq = runtime.tracker_reset_seq
        name, title = tracking.foreground_context()
        category = services.classify_activity(name, title, active)
        with runtime.LOCK:
            current_seq = runtime.state["event_seq"]
        new_events = max(0, current_seq - last_seq)
        last_seq = current_seq
        time_field = "active_seconds" if active else "idle_seconds"
        with runtime.pending_lock:
            elapsed_to_persist = dt + runtime.pending_time[time_field]
        try:
            slice_key = (
                runtime.datetime.now()
                .replace(second=0, microsecond=0)
                .isoformat(timespec="minutes")
            )
            tracking.persist_tracker_tick(
                services.today_key(),
                slice_key,
                category,
                elapsed_to_persist,
                new_events,
            )
            with runtime.pending_lock:
                runtime.pending_time[time_field] = 0.0
        except Exception:
            runtime.logger.warning(
                "Tracker persistence failed; queued counters retained", exc_info=True
            )
            with runtime.pending_lock:
                runtime.pending_time[time_field] += dt
            prev = now
            runtime.STOP.wait(runtime.TRACK_INTERVAL)
            continue
        try:
            active_credit = 0.0
            with runtime.pending_lock:
                active_credit = runtime.pending_time["active_seconds"]
            if active:
                if session_id is None:
                    conn = database.db()
                    cur = conn.execute(
                        "INSERT INTO focus_sessions(started_at) VALUES(?)",
                        (
                            runtime.datetime.fromtimestamp(
                                runtime.last_input_ts
                            ).isoformat(timespec="seconds"),
                        ),
                    )
                    session_id = cur.lastrowid
                    conn.commit()
                    conn.close()
                    session_started = runtime.last_input_ts
                    session_active = 0
                    session_last_active = runtime.last_input_ts
                    session_events = 0
                    categories = []
                session_active += elapsed_to_persist
                session_last_active = runtime.last_input_ts
                session_events += new_events
                if category not in categories:
                    categories.append(category)
                with runtime.suppress(Exception):
                    conn = database.db()
                    conn.execute(
                        "UPDATE focus_sessions SET active_seconds=?,event_count=?,categories=? WHERE id=? AND ended_at IS NULL",
                        (
                            session_active,
                            session_events,
                            ",".join(categories),
                            session_id,
                        ),
                    )
                    conn.commit()
                    conn.close()
            elif (
                session_id
                and session_last_active
                and (now - session_last_active > runtime.FOCUS_BREAK_SECONDS)
            ):
                session_active += active_credit
                tracking._close_focus_session(
                    session_id,
                    session_started,
                    session_active,
                    session_last_active,
                    session_events,
                    categories,
                    "idle",
                )
                with runtime.pending_lock:
                    runtime.pending_time["active_seconds"] = 0.0
                session_id = session_started = session_last_active = None
                session_active = 0
                session_events = 0
                categories = []
        except Exception:
            runtime.logger.warning("Focus session update failed", exc_info=True)
            prev = now
            runtime.STOP.wait(runtime.TRACK_INTERVAL)
            continue
        prev = now
        runtime.STOP.wait(runtime.TRACK_INTERVAL)
    if session_id:
        tracking._close_focus_session(
            session_id,
            session_started,
            session_active,
            session_last_active,
            session_events,
            categories,
            "shutdown",
        )


def listeners_start() -> bool:
    from . import tracking

    new_refs = []
    try:
        k = runtime.keyboard.Listener(on_press=tracking.on_press)
        m = runtime.mouse.Listener(
            on_click=tracking.on_click,
            on_scroll=tracking.on_scroll,
            on_move=tracking.on_move,
        )
        new_refs = [k, m]
        k.start()
        m.start()
        runtime.listener_refs = new_refs
        runtime.listener_last_ok = runtime.time.time()
        runtime.listener_error = ""
        return True
    except Exception as exc:
        runtime.listener_error = f"{type(exc).__name__}: {exc}"
        for listener in new_refs:
            with runtime.suppress(Exception):
                listener.stop()
        runtime.listener_refs = []
        return False


def listeners_healthy() -> bool:
    return len(runtime.listener_refs) == 2 and all(
        (
            bool(getattr(listener, "is_alive", lambda: False)())
            for listener in runtime.listener_refs
        )
    )


def listener_watchdog() -> None:
    from . import tracking

    while not runtime.STOP.wait(5):
        if tracking.listeners_healthy():
            runtime.listener_last_ok = runtime.time.time()
            continue
        with runtime.listener_restart_lock:
            if tracking.listeners_healthy():
                continue
            if tracking.listeners_start():
                runtime.listener_restart_count += 1
