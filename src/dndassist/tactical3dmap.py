import numpy as np
import matplotlib.pyplot as plt

# def plot_terrain_with_obstacles(
#     ground_height, ground_r, ground_g, ground_b, ground_a,
#     obst_height, obst_r, obst_g, obst_b, obst_a,
#     delta_x=1.5,
#     annotations=None
# ):
#     """
#     Plot a 3D terrain surface with colored ground, semi-transparent obstacles, and annotations.

#     Parameters
#     ----------
#     ground_height : 2D np.array
#         Elevation of the terrain (meters)
#     ground_r,g,b,a : 2D np.array
#         RGB + alpha components of ground (0–1 range)
#     obst_height : 2D np.array
#         Additional obstacle elevation over terrain (meters)
#     obst_r,g,b,a : 2D np.array
#         RGB + alpha components of obstacles (0–1 range)
#     delta_x : float
#         Tile width in meters (for both X and Y spacing)
#     annotations : list of tuples
#         Each (x, y, height, color, name, description)
#     """

#     ny, nx = ground_height.shape
#     X = (np.arange(nx)) * delta_x
#     Y = (np.arange(ny)) * delta_x
#     X, Y = np.meshgrid(X, Y)

#     # --- Build RGBA for ground ---
#     ground_colors = np.dstack([ground_r, ground_g, ground_b, ground_a])

#     # --- Plot setup ---
#     fig = plt.figure(figsize=(10, 7))
#     ax = fig.add_subplot(111, projection='3d')

#     # --- Ground surface ---
#     ax.plot_surface(
#         X, Y, ground_height,
#         facecolors=ground_colors,
#         linewidth=0.2, antialiased=False, shade=True, edgecolor="black"
#     )

#     # --- Obstacles (sparse 3D histogram) ---
#     # Plot only where obstacle height > 0
#     nz = obst_height > 0
#     ox, oy = np.where(nz)

#     if len(ox) > 0:
#         ox_vals = ox * delta_x
#         oy_vals = oy * delta_x
#         dz_vals = obst_height[nz]
#         colors = np.array([
#             [obst_r[i, j], obst_g[i, j], obst_b[i, j], obst_a[i, j]]
#             for i, j in zip(ox, oy)
#         ])
#         ax.bar3d(
#             oy_vals, ox_vals, ground_height[nz],
#             delta_x, delta_x, dz_vals,
#             color=colors,
#             shade=False,
#             linewidth=0.1,
#             edgecolor="black"
            
#         )

#     # --- Annotations ---
#     if annotations:
#         for x, y, h, hex_color, name, desc in annotations:
#             ax.text(
#                 y * delta_x, x * delta_x, h + 10.0,
#                 f"{name}\n{desc}",
#                 color=hex_color, fontsize=8,
#                 ha='center', va='bottom'
#             )
#             # ajouter une line verticale pour voir qui est qui
#             # utiliser MPL cursor?
#             ax.lines(
#                 y * delta_x, x * delta_x, h + 0.0,
#                 y * delta_x, x * delta_x, h + 10.0,
#             )

#     # --- Equal aspect ratio ---
#     max_range = np.array([
#         X.max()-X.min(),
#         Y.max()-Y.min(),
#         obst_height.max() - ground_height.min()
#     ]).max() / 2.0
#     print(max_range)
#     mid_x = (X.max()+X.min()) / 2
#     mid_y = (Y.max()+Y.min()) / 2
#     mid_z = (obst_height.max()+ground_height.min()) / 2

#     ax.set_xlim(mid_x - max_range, mid_x + max_range)
#     ax.set_ylim(mid_y - max_range, mid_y + max_range)
#     ax.set_zlim(mid_z - max_range, mid_z + max_range)

#     ax.set_xlabel("X (m)")
#     ax.set_ylabel("Y (m)")
#     ax.set_zlabel("Elevation (m)")
#     ax.view_init(elev=50, azim=-60)

#     plt.tight_layout()
#     plt.show()


import numpy as np
import matplotlib.pyplot as plt
#from mpl_toolkits.mplot3d import Axes3D  # noqa
from textwrap import fill

def plot_terrain_with_obstacles(
    ground_height, ground_r, ground_g, ground_b, ground_a,
    obst_height,
    delta_x=1.5,
    annotations=None
):
    """
    Plot a 3D terrain surface with colored ground, semi-transparent obstacles, and annotations.

    Improvements:
    - Black background, grey axes labels, no grid
    - Fancy font for text
    - Annotations with small colored marker + vertical line + wrapped grey text
    - Surface mesh extended to align with histogram bars
    """

    # --- Helper to expand arrays by one cell in both axes (copy edge values) ---
    def expand(arr):
        arr = np.asarray(arr)
        out = np.zeros((arr.shape[0]+1, arr.shape[1]+1), dtype=arr.dtype)
        out[:-1, :-1] = arr
        out[-1, :-1] = arr[-1, :]
        out[:-1, -1] = arr[:, -1]
        out[-1, -1] = arr[-1, -1]
        return out

    # --- Expand ground rasters so surface aligns with histogram ---
    ground_height = expand(ground_height)
    ground_rp1 = expand(ground_r)
    ground_gp1 = expand(ground_g)
    ground_bp1 = expand(ground_b)
    ground_ap1 = expand(ground_a)

    ny, nx = ground_height.shape
    X = np.arange(nx) * delta_x
    Y = np.arange(ny) * delta_x
    X, Y = np.meshgrid(X, Y)

    ground_colors = np.dstack([ground_rp1, ground_gp1, ground_bp1, ground_ap1])

    # --- Setup figure ---
    fig = plt.figure(figsize=(10, 7))
    ax = fig.add_subplot(111, projection='3d')

    # Black background
    fig.patch.set_facecolor("black")
    ax.set_facecolor("black")

    # --- Ground surface ---
    ax.plot_surface(
        X, Y, ground_height,
        facecolors=ground_colors,
        linewidth=0.2, antialiased=False, shade=True, edgecolor="black"
    )

    # --- Obstacles (3D histogram) ---
    nz = obst_height > 0
    ox, oy = np.where(nz)

    if len(ox) > 0:
        ox_vals = ox * delta_x
        oy_vals = oy * delta_x
        dz_vals = obst_height[nz]
        colors = np.array([
            [ground_r[i, j], ground_g[i, j], ground_b[i, j], ground_a[i, j]]
            for i, j in zip(ox, oy)
        ])
        ax.bar3d(
            oy_vals, ox_vals, ground_height[:-1, :-1][nz],
            delta_x, delta_x, dz_vals,
            color=colors,
            shade=False,
            linewidth=0.1,
            edgecolor="black"
        )

    # --- Annotations ---
    if annotations:
        for x, y, h, hex_color, name, desc in annotations:
            # Ground coordinates
            gx, gy = (y +0.5)* delta_x, (x+0.5) * delta_x
            gz = h#ground_height[min(int(x), ny-1), min(int(y), nx-1)] + h
            text_height = gz + 30.0
            
            # Marker at ground
            ax.scatter(
                gx, gy, gz,
                color=hex_color, s=60, depthshade=False
            )

            # Vertical line up to text level
            ax.plot(
                [gx, gx], [gy, gy], [gz, text_height],
                color="grey", linestyle="--", linewidth=0.8
            )

            # Wrapped grey annotation text above line
            text_str = fill(f"{name}: {desc}", width=40)
            ax.text(
                gx, gy, text_height,
                text_str,
                color="lightgrey", fontsize=8,
                ha='center', va='bottom', family='serif'
            )

    # --- Visual polish ---
    ax.xaxis.pane.fill = False
    ax.yaxis.pane.fill = False
    ax.zaxis.pane.fill = False

    ax.grid(False)
    ax.xaxis._axinfo["grid"]["linewidth"] = 0
    ax.yaxis._axinfo["grid"]["linewidth"] = 0
    ax.zaxis._axinfo["grid"]["linewidth"] = 0

    for axis in [ax.xaxis, ax.yaxis, ax.zaxis]:
        axis.set_tick_params(colors='grey', labelcolor='grey')

    ax.set_xlabel("Y (m)", color='grey', fontfamily='serif')
    ax.set_ylabel("X (m)", color='grey', fontfamily='serif')
    ax.set_zlabel("Elevation (m)", color='grey', fontfamily='serif')

    # Major ticks only
    ax.xaxis.set_major_locator(plt.MaxNLocator(6))
    ax.yaxis.set_major_locator(plt.MaxNLocator(6))
    ax.zaxis.set_major_locator(plt.MaxNLocator(4))

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
    ax.set_proj_type('persp', focal_length=0.2) 
    ax.view_init(elev=50, azim=-60)
    plt.tight_layout()
    plt.show()
