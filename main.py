# main.py
from core_deconflict import check_mission, plan_primary_mission, sample_trajectory, resolve_conflict
from visualization_4d import make_4d_animation
from other_flights_data import other_flights
import os

def run_demo():
    # --- Define Primary Mission ---
    primary_waypoints = [
        {'x': 0, 'y': 0, 'z': 0},
        {'x': 100, 'y': 0, 'z': 20},
        {'x': 200, 'y': 50, 'z': 50}
    ]
    T_start = "2025-08-10 10:00:00"
    T_end   = "2025-08-10 10:03:00"

    # --- Conflict Check ---
    result = check_mission(primary_waypoints, T_start, T_end, other_flights, safety_radius=10.0, dt=1.0)
    print("Status:", result['status'])
    if result['conflicts']:
        print("Conflicts found:")
        for c in result['conflicts'][:5]:
            print(c)

        # Step 2 — Try to resolve
        result, T_start, T_end = resolve_conflict(
            primary_waypoints, T_start, T_end, other_flights,
            safety_radius=10.0, dt=1.0, delay_step=60
        )
        print(f"📅 Updated Mission Window: {T_start} → {T_end}")

    # --- Prepare for Visualization ---
    primary_timed = plan_primary_mission(primary_waypoints, T_start, T_end)
    p_times, p_pos = sample_trajectory(primary_timed, dt=1.0)

    other_timed_list = []
    other_flights_4d = []
    for other in other_flights:
        timed_wp = plan_primary_mission(other['waypoints'], other['T_start'], other['T_end'])
        other_timed_list.append({'id': other['id'], 'waypoints': timed_wp})
        o_times, o_pos = sample_trajectory(timed_wp, dt=1.0)
        other_flights_4d.append({'id': other['id'], 'times': o_times, 'pos': o_pos})

    # --- Show & Save 4D Animation ---
    os.makedirs("outputs", exist_ok=True)
    make_4d_animation(
        primary_times=p_times,
        primary_pos=p_pos,
        other_flights=other_flights_4d,
        conflicts=result['conflicts'],
        out_file="4d_demo.mp4",
        fps=12,
        show_plot=True  # set to True to display interactively instead of saving
    )

if __name__ == '__main__':
    run_demo()
