# visualization_4d.py
import numpy as np
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401 (plt 3D projection)
import matplotlib.pyplot as plt
from matplotlib import animation
import os

def make_4d_animation(primary_times, primary_pos,
                      other_flights,   # list of dicts: {'id':..., 'times': np.array, 'pos': np.array Nx3}
                      conflicts,       # list of conflict dicts (time, primary_pos, other_pos, other_id)
                      out_file='4d_animation.mp4',
                      fps=10,
                      show_plot=False):
    """
    Create a 3D (x,y,z) animation over time. Time is represented by animation frames.
    - primary_times : 1D array of times (seconds)
    - primary_pos   : Nx3 array of positions (x,y,z). If your data is 2D, supply z=0 column.
    - other_flights : list of {'id', 'times' (1D), 'pos' (Mx3)}
    - conflicts     : list of {'time':epoch, 'primary_pos':(x,y,z), 'other_pos':(...), 'other_id':id}
    """

    # Ensure 3D arrays
    def ensure3(pos):
        pos = np.asarray(pos)
        if pos.ndim == 1:
            pos = pos.reshape(1, -1)
        if pos.shape[1] == 2:
            z = np.zeros((pos.shape[0], 1))
            pos = np.hstack([pos, z])
        return pos

    primary_pos = ensure3(primary_pos)
    for of in other_flights:
        of['pos'] = ensure3(of['pos'])

    frame_times = np.array(primary_times)
    n_frames = len(frame_times)

    # Precompute indices for other flights at each frame
    other_indices = []
    for of in other_flights:
        idxs = np.searchsorted(of['times'], frame_times, side='right') - 1
        idxs = np.clip(idxs, 0, len(of['times']) - 1)
        other_indices.append(idxs)

    # Map frame index -> list of conflicts
    conflict_by_frame = {}
    for c in conflicts:
        ct = c['time']
        idx = int(np.argmin(np.abs(frame_times - ct)))
        conflict_by_frame.setdefault(idx, []).append(c)

    # Setup figure
    fig = plt.figure(figsize=(9, 7))
    ax = fig.add_subplot(111, projection='3d')
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_zlabel('Z (altitude)')
    ax.set_title('4D Visualization: 3D space evolving over time')

    # Legend handles
    legend_handles = [
        ax.plot([], [], [], 'bo', markersize=6, label='Primary Drone')[0],
    ]

    for of in other_flights:
        legend_handles.append(
            ax.plot([], [], [], 'r--', label=f"Other: {of['id']}")[0]
        )

    legend_handles.append(
        ax.scatter([], [], [], s=120, c='yellow', edgecolors='black', label='Conflicts')
    )

    ax.legend(handles=legend_handles, loc='upper right')


    # Limits
    all_pos = [primary_pos] + [of['pos'] for of in other_flights]
    all_concat = np.vstack(all_pos)
    margin = 0.1 * (all_concat.max(axis=0) - all_concat.min(axis=0) + 1e-6)
    mins = all_concat.min(axis=0) - margin
    maxs = all_concat.max(axis=0) + margin
    ax.set_xlim(mins[0], maxs[0])
    ax.set_ylim(mins[1], maxs[1])
    ax.set_zlim(mins[2], maxs[2])

    # Static full paths
    ax.plot(primary_pos[:,0], primary_pos[:,1], primary_pos[:,2], color='blue', linewidth=1.0, alpha=0.25, label='Primary path')
    for of in other_flights:
        ax.plot(of['pos'][:,0], of['pos'][:,1], of['pos'][:,2], linestyle='--', alpha=0.15, label=f"Other {of['id']}")

    # Dynamic markers & trails
    prim_point, = ax.plot([], [], [], 'bo', markersize=6, label='Primary (current)')
    other_points = [ax.plot([], [], [], 'ro', markersize=5, label=f"Other {of['id']} (current)")[0] for of in other_flights]

    prim_trail, = ax.plot([], [], [], color='blue', linewidth=2.0, alpha=0.6)
    other_trails = [ax.plot([], [], [], color='red', linewidth=1.5, alpha=0.6)[0] for _ in other_flights]

    # Conflict scatter (empty at init)
    conflict_scats = ax.scatter([], [], [], s=120, c='yellow', edgecolors='black', zorder=10)

    # Time text
    time_text = ax.text2D(0.02, 0.95, "", transform=ax.transAxes)

    def init():
        prim_point.set_data([], [])
        prim_point.set_3d_properties([])
        for p in other_points:
            p.set_data([], [])
            p.set_3d_properties([])
        prim_trail.set_data([], [])
        prim_trail.set_3d_properties([])
        for t in other_trails:
            t.set_data([], [])
            t.set_3d_properties([])
        conflict_scats._offsets3d = ([], [], [])
        time_text.set_text("")
        return [prim_point, *other_points, prim_trail, *other_trails, conflict_scats, time_text]

    def update(frame):
        t = frame_times[frame]
        # Primary
        prim_curr = primary_pos[frame]
        prim_point.set_data([prim_curr[0]], [prim_curr[1]])
        prim_point.set_3d_properties([prim_curr[2]])
        prim_trail.set_data(primary_pos[:frame+1,0], primary_pos[:frame+1,1])
        prim_trail.set_3d_properties(primary_pos[:frame+1,2])

        # Others
        for i, of in enumerate(other_flights):
            idx = other_indices[i][frame]
            curr = of['pos'][idx]
            other_points[i].set_data([curr[0]], [curr[1]])
            other_points[i].set_3d_properties([curr[2]])
            other_trails[i].set_data(of['pos'][:idx+1,0], of['pos'][:idx+1,1])
            other_trails[i].set_3d_properties(of['pos'][:idx+1,2])

        # Conflicts at this frame
        confs = conflict_by_frame.get(frame, [])
        if confs:
            cxs = [c['primary_pos'][0] for c in confs]
            cys = [c['primary_pos'][1] for c in confs]
            czs = [c['primary_pos'][2] if len(c['primary_pos']) > 2 else 0.0 for c in confs]
            conflict_scats._offsets3d = (cxs, cys, czs)
        else:
            conflict_scats._offsets3d = ([], [], [])

        time_text.set_text(f"Time: {t:.1f} sec")
        return [prim_point, *other_points, prim_trail, *other_trails, conflict_scats, time_text]

    anim = animation.FuncAnimation(fig, update, init_func=init, frames=n_frames, interval=1000/fps, blit=False)

    if out_file and (not show_plot):
        d = os.path.dirname(out_file)
        if d and not os.path.exists(d):
            os.makedirs(d)
        try:
            Writer = animation.FFMpegWriter
            writer = Writer(fps=fps, metadata=dict(artist='uav-deconflict'), bitrate=1800)
            anim.save(out_file, writer=writer)
            print(f"Saved animation to {out_file}")
        except Exception as e:
            print("Failed to save mp4 (need ffmpeg). Error:", e)
            print("Showing plot instead.")
            plt.show()
    else:
        plt.show()
