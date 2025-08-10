import math
import numpy as np
from datetime import datetime, timedelta

def to_seconds(t):
    if isinstance(t, (int, float)):
        return float(t)
    if isinstance(t, datetime):
        return t.timestamp()
    if isinstance(t, str):
        try:
            return datetime.fromisoformat(t).timestamp()
        except Exception:
            return datetime.strptime(t, "%Y-%m-%d %H:%M:%S").timestamp()

def plan_primary_mission(waypoints, t_start, t_end):
    dims = 3 if any('z' in wp for wp in waypoints) else 2
    pos = np.array([[wp['x'], wp['y']] + ([wp.get('z', 0.0)] if dims == 3 else []) for wp in waypoints], dtype=float)
    t0 = to_seconds(t_start)
    t1 = to_seconds(t_end)

    if len(pos) < 2:
        times = np.array([t0])
    else:
        seg_d = np.linalg.norm(pos[1:] - pos[:-1], axis=1)
        total = seg_d.sum()
        if total <= 0:
            times = np.linspace(t0, t1, len(pos))
        else:
            cum = np.concatenate(([0.0], np.cumsum(seg_d)))
            times = t0 + (cum / cum[-1]) * (t1 - t0)

    out = []
    for i, p in enumerate(pos):
        entry = {'x': float(p[0]), 'y': float(p[1]), 't': float(times[i])}
        if dims == 3:
            entry['z'] = float(p[2])
        out.append(entry)
    return out

def sample_trajectory(waypoints_with_t, dt=1.0):
    times = np.array([wp['t'] for wp in waypoints_with_t], dtype=float)
    order = np.argsort(times)
    times = times[order]
    dims = 3 if any('z' in wp for wp in waypoints_with_t) else 2
    positions = np.array([[waypoints_with_t[i]['x'], waypoints_with_t[i]['y']] + ([waypoints_with_t[i].get('z',0.0)] if dims==3 else []) for i in order], dtype=float)

    if len(times) == 1:
        return np.array([times[0]]), positions.copy()

    sample_times = np.arange(times[0], times[-1] + 1e-9, dt)
    sampled = np.column_stack([np.interp(sample_times, times, positions[:, i]) for i in range(positions.shape[1])])
    return sample_times, sampled

def resample_positions(src_times, src_pos, target_times):
    return np.column_stack([np.interp(target_times, src_times, src_pos[:, i]) for i in range(src_pos.shape[1])])

def detect_conflicts(primary_pos, primary_times, other_times, other_pos, safety_radius):
    conflicts = []
    overlap_mask = (primary_times >= other_times[0]) & (primary_times <= other_times[-1])
    if not overlap_mask.any():
        return conflicts

    other_resampled = resample_positions(other_times, other_pos, primary_times[overlap_mask])
    prim_overlap = primary_pos[overlap_mask]
    dists = np.linalg.norm(prim_overlap - other_resampled, axis=1)
    hits = np.where(dists < safety_radius)[0]

    idxs = np.nonzero(overlap_mask)[0]
    for i in hits:
        global_idx = idxs[i]
        conflicts.append({
            'time': float(primary_times[global_idx]),
            'primary_pos': tuple(prim_overlap[i]),
            'other_pos': tuple(other_resampled[i]),
            'distance': float(dists[i])
        })
    return conflicts

def check_mission(primary_waypoints, T_start, T_end, other_flights, safety_radius=5.0, dt=1.0):
    primary_timed = plan_primary_mission(primary_waypoints, T_start, T_end)
    p_times, p_pos = sample_trajectory(primary_timed, dt=dt)

    all_conflicts = []
    for other in other_flights:
        oid = other.get('id', 'other')
        wps = other['waypoints']
        if any('t' in wp for wp in wps):
            other_timed = wps
        else:
            if 'T_start' in other and 'T_end' in other:
                other_timed = plan_primary_mission(wps, other['T_start'], other['T_end'])
            else:
                raise ValueError(f"Other flight '{oid}' missing timing info")
        o_times, o_pos = sample_trajectory(other_timed, dt=dt)
        confs = detect_conflicts(p_pos, p_times, o_times, o_pos, safety_radius)
        for c in confs:
            c['other_id'] = oid
        all_conflicts.extend(confs)

    status = 'clear' if len(all_conflicts) == 0 else 'conflict detected'
    return {'status': status, 'conflicts': all_conflicts}

def resolve_conflict(primary_waypoints, T_start, T_end, other_flights, safety_radius=5.0, dt=1.0, delay_step=60, max_attempts=10):
    """
    Attempt to resolve conflicts by delaying the mission start/end times.
    - delay_step: seconds to delay per attempt
    - max_attempts: how many delays to try before giving up
    """ 

    def str_to_dt(s): return datetime.strptime(s, "%Y-%m-%d %H:%M:%S")
    def dt_to_str(d): return d.strftime("%Y-%m-%d %H:%M:%S")

    attempts = 0
    result = check_mission(primary_waypoints, T_start, T_end, other_flights, safety_radius, dt)

    while result['status'] != 'clear' and attempts < max_attempts:
        attempts += 1
        print(f"⚠️ Conflict detected — delaying mission by {delay_step} seconds (attempt {attempts})")

        # Delay start/end times
        T_start_dt = str_to_dt(T_start) + timedelta(seconds=delay_step)
        T_end_dt = str_to_dt(T_end) + timedelta(seconds=delay_step)
        T_start, T_end = dt_to_str(T_start_dt), dt_to_str(T_end_dt)

        # Re-check mission
        result = check_mission(primary_waypoints, T_start, T_end, other_flights, safety_radius, dt)

    if result['status'] == 'clear':
        print("✅ Conflict resolved. New schedule is safe.")
    else:
        print("❌ Could not resolve conflict within max attempts.")

    return result, T_start, T_end
