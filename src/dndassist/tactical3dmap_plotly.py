import plotly.graph_objects as go
import numpy as np
import textwrap

def _normalize_color_raster(arr):
    """Accepts numpy array either 0..1 or 0..255, returns 0..255 ints."""
    arr = np.asarray(arr)
    if arr.max() <= 1.0:
        arr = (arr * 255).astype(int)
    else:
        arr = arr.astype(int)
    return arr

def _rgba_str(r, g, b, a):
    """Return an 'rgba(r,g,b,a)' string where r,g,b are ints 0..255 and a is 0..1 float."""
    return f"rgba({int(r)},{int(g)},{int(b)},{float(a)})"

def render_tactical_map_plotly(
    height, R, G, B, A,
    obstacle_height,
    annotations,
    delta_x=1.5,
    #elevation_unit=0.5,
    camera_position=dict(x=1.8, y=1.8, z=1.2)
):
    """
    Plotly 3D map using per-tile RGBA for ground and obstacles.

    height : 2D array (ny, nx) -- ground elevation units
    R,G,B,A : 2D arrays same shape, color channels for ground (R,G,B either 0..1 or 0..255; A in 0..1)
    obstacle_height, oR,oG,oB,oA : 2D arrays for obstacles (same shape as height)
    annotations : list of (x_tile, y_tile, height_units, hex_color, name, desc)
    delta_x : meters per tile horizontally
    elevation_unit : meters per elevation unit (vertical scale)
    """
    elevation_unit = 1
    # Normalize inputs
    H0 = np.asarray(height)
    nx, ny = H0.shape
    delta_y = -delta_x
    R = _normalize_color_raster(R)
    G = _normalize_color_raster(G)
    B = _normalize_color_raster(B)
    A = np.asarray(A).astype(float)  # should be 0..1


    # Expand ground so that tiles (nx x ny) align with quads (we want one quad per original tile)
    # We'll compute corner heights by taking H0 and duplicating right/bottom edges
    H = np.zeros((nx + 1, ny + 1), dtype=float)
    H[:-1, :-1] = H0 * elevation_unit
    H[-1, :-1] = H0[-1, :] * elevation_unit
    H[:-1, -1] = H0[:, -1] * elevation_unit
    H[-1, -1] = H0[-1, -1] * elevation_unit

    # Prepare tile corner coordinates
    xs = np.arange(nx + 1) * delta_x
    ys = np.arange(ny + 1) * delta_y

    # We'll build plotly traces: a list starting with nothing, then many Mesh3d traces
    traces = []

    # --- Ground: build one thin mesh per tile (two triangles) colored with tile RGBA ---
    for iy in range(ny):
        for ix in range(nx):
            # corner coords of this tile (four corners)
            x0 = ix * delta_x
            y0 = iy * delta_y
            # vertices order: (0)bl, (1)br, (2)tr, (3)tl  (bl = bottom-left in XY)
            vert_x = [x0, x0 + delta_x, x0 + delta_x, x0]
            vert_y = [y0, y0, y0 + delta_y, y0 + delta_y]
            vert_z = [
                H[ix, iy],
                H[ix + 1, iy],
                H[ix + 1, iy + 1],
                H[ix, iy + 1],
            ]

            # color for this tile from R,G,B,A arrays (take the tile center color)
            rr = R[ix, iy]
            gg = G[ix, iy]
            bb = B[ix, iy]
            aa = float(A[ix, iy])
            color_str = _rgba_str(rr, gg, bb, aa)

            # two triangles: (0,1,2) and (0,2,3)
            traces.append(go.Mesh3d(
                x=vert_x + [ ], y=vert_y + [ ], z=vert_z + [ ],
                i=[0, 0], j=[1, 2], k=[2, 3],
                color=color_str,
                opacity=aa,
                flatshading=True,
                showscale=False
            ))

    # --- Obstacles: one thin column (prism sides) per tile where obstacle_height>0
    for iy in range(ny):
        for ix in range(nx):
            h_units = obstacle_height[ix, iy]
            if h_units <= 0:
                continue
            h_m = float(h_units) * elevation_unit
            base = H0[ix, iy] * elevation_unit  # base height at that tile

            # thin column centered in tile, width fraction
            cx = ix * delta_x + delta_x * 0.5
            cy = iy * delta_y + delta_y * 0.5
            w = delta_x * 0.5

            # 8 vertices of the column (we'll create side faces only = 4 quads => 8 triangles)
            # order: bottom 0..3, top 4..7
            vx = [cx - w, cx + w, cx + w, cx - w, cx - w, cx + w, cx + w, cx - w]
            vy = [cy - w, cy - w, cy + w, cy + w, cy - w, cy - w, cy + w, cy + w]
            vz = [base, base, base, base, base + h_m, base + h_m, base + h_m, base + h_m]

            rr = R[ix, iy]
            gg = G[ix, iy]
            bb = B[ix, iy]
            aa = float(A[ix, iy])
            color_str = _rgba_str(rr, gg, bb, aa)

            # faces indices for Mesh3d (we'll define triangular faces)
            # four side quads, each split into 2 triangles:
            i = [0,4,2,5,3,3,3,4]
            j = [1,0,1,2,2,6,0,0]
            k = [5,5,5,6,6,7,7,7]
            # Note: top/bottom faces omitted (thin column no top/bottom)

            traces.append(go.Mesh3d(
                x=vx, y=vy, z=vz,
                i=i, j=j, k=k,
                color=color_str,
                opacity=aa,
                flatshading=True,
                showscale=False
            ))

    # --- Annotations: circle marker at ground center, grey line up, and text 30m higher ---
    for (tx, ty, h_units, color_hex, name, desc) in annotations:
        z = float(h_units) #* elevation_unit
        txt = "<br>".join(textwrap.wrap(f"{name}: {desc}", width=40))
        # marker
        traces.append(go.Scatter3d(
            x=[tx * delta_x + delta_x*0.5],
            y=[ty * delta_y + delta_y*0.5],
            z=[z],
            mode='markers',
            text=[txt],
            marker=dict(color=color_hex, size=6),
            showlegend=False
        ))

    # Build figure
    layout = go.Layout(
        scene=dict(
            xaxis=dict(showbackground=False, color='grey', showgrid=False),
            yaxis=dict(showbackground=False, color='grey', showgrid=False),
            zaxis=dict(showbackground=False, color='grey', showgrid=False),
            aspectmode='data',
            camera=dict(eye=camera_position)
        ),
        paper_bgcolor='black',
        plot_bgcolor='black',
        margin=dict(l=0, r=0, t=0, b=0)
    )

    fig = go.Figure(data=traces, layout=layout)
    fig.show()
