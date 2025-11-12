import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401
from matplotlib.colors import Normalize

def plot_terrain_with_obstacles(
    ground_height, ground_r, ground_g, ground_b, ground_a,
    obst_height, obst_r, obst_g, obst_b, obst_a,
    delta_x=1.5,
    annotations=None
):
    """
    Plot a 3D terrain surface with colored ground, semi-transparent obstacles, and annotations.

    Parameters
    ----------
    ground_height : 2D np.array
        Elevation of the terrain (meters)
    ground_r,g,b,a : 2D np.array
        RGB + alpha components of ground (0–1 range)
    obst_height : 2D np.array
        Additional obstacle elevation over terrain (meters)
    obst_r,g,b,a : 2D np.array
        RGB + alpha components of obstacles (0–1 range)
    delta_x : float
        Tile width in meters (for both X and Y spacing)
    annotations : list of tuples
        Each (x, y, height, color, name, description)
    """

    ny, nx = ground_height.shape
    X = (np.arange(nx)) * delta_x
    Y = (np.arange(ny)) * delta_x
    X, Y = np.meshgrid(X, Y)

    # --- Build RGBA for ground ---
    ground_colors = np.dstack([ground_r, ground_g, ground_b, ground_a])

    # --- Plot setup ---
    fig = plt.figure(figsize=(10, 7))
    ax = fig.add_subplot(111, projection='3d')

    # --- Ground surface ---
    ax.plot_surface(
        X, Y, ground_height,
        facecolors=ground_colors,
        linewidth=0.2, antialiased=False, shade=True, edgecolor="black"
    )

    # --- Obstacles (sparse 3D histogram) ---
    # Plot only where obstacle height > 0
    nz = obst_height > 0
    ox, oy = np.where(nz)

    if len(ox) > 0:
        ox_vals = ox * delta_x
        oy_vals = oy * delta_x
        dz_vals = obst_height[nz]
        colors = np.array([
            [obst_r[i, j], obst_g[i, j], obst_b[i, j], obst_a[i, j]]
            for i, j in zip(ox, oy)
        ])
        ax.bar3d(
            oy_vals, ox_vals, ground_height[nz],
            delta_x, delta_x, dz_vals,
            color=colors,
            shade=False,
            linewidth=0.1,
            edgecolor="black"
            
        )

    # --- Annotations ---
    if annotations:
        for x, y, h, hex_color, name, desc in annotations:
            ax.text(
                y * delta_x, x * delta_x, h + 10.0,
                f"{name}\n{desc}",
                color=hex_color, fontsize=8,
                ha='center', va='bottom'
            )
            # ajouter une line verticale pour voir qui est qui
            # utiliser MPL cursor?
            ax.lines(
                y * delta_x, x * delta_x, h + 0.0,
                y * delta_x, x * delta_x, h + 10.0,
            )

    # --- Equal aspect ratio ---
    max_range = np.array([
        X.max()-X.min(),
        Y.max()-Y.min(),
        obst_height.max() - ground_height.min()
    ]).max() / 2.0
    print(max_range)
    mid_x = (X.max()+X.min()) / 2
    mid_y = (Y.max()+Y.min()) / 2
    mid_z = (obst_height.max()+ground_height.min()) / 2

    ax.set_xlim(mid_x - max_range, mid_x + max_range)
    ax.set_ylim(mid_y - max_range, mid_y + max_range)
    ax.set_zlim(mid_z - max_range, mid_z + max_range)

    ax.set_xlabel("X (m)")
    ax.set_ylabel("Y (m)")
    ax.set_zlabel("Elevation (m)")
    ax.view_init(elev=50, azim=-60)

    plt.tight_layout()
    plt.show()
