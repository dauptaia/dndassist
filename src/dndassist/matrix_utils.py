from typing import Tuple, List
import string,math
from collections import deque
import numpy as np
import matplotlib.pyplot as plt

def plot_elevation_2d(elevation: np.ndarray, dx=1.5, cmap="gist_ncar"):
    """
    Display a 2D heatmap of the elevation map.
    
    Args:
        elevation: 2D numpy array of elevation units
        dx, dy: horizontal resolution per tile (meters)
        dz: vertical scale (meters per elevation unit)
        cmap: any matplotlib sequential colormap ("Greys", "terrain", "viridis", ...)
    """
    dy=dx
    w,h = elevation.shape
    extent = [0, w*dx, h*dy, 0, ]  # ensures correct scaling and orientation
    elev_m = elevation.T     # convert units to meters

    fig, ax = plt.subplots(figsize=(8, 6))
    im = ax.imshow(
        elev_m,
        cmap=cmap,
        extent=extent,
        origin="upper",
        aspect=dx/dy
    )

    # Add a colorbar for elevation
    cbar = plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label("Elevation (m)", rotation=270, labelpad=15)

    ax.set_xlabel("X (m)")
    ax.set_ylabel("Y (m)")
    ax.set_title("Elevation Map (2D View)")
    plt.tight_layout()
    plt.show()




def char_to_elev(ch: str) -> float | None:
    """Convert elevation control char to numeric value."""
    if ch in string.digits:
        return float(int(ch))
    elif ch in "abcdef":
        return 10.0 + float(ord(ch) - ord("a"))
    elif ch == " ":
        return None
    else:
        raise ValueError(f"Invalid elevation char: {ch!r}")

def build_elevation_map(elev_ascii: list[list[str]], smoothing_passes: int = 1, dh=0.5) -> np.ndarray:
    """
    Convert ASCII elevation map into numeric elevation grid.
    - Each control tile ('0'-'9','a'-'f') sets an elevation level.
    - Empty tiles inherit the elevation of the nearest control tile.
    - Optional smoothing to soften slopes (control tiles remain fixed).
    """
    h, w = len(elev_ascii), len(elev_ascii[0])
    elevation = np.full((w, h), np.nan)
    fixed_mask = np.zeros((w, h), dtype=bool)

    # Step 1: Decode control tiles
    for y in range(h):
        for x in range(w):
            val = char_to_elev(elev_ascii[y][x])
            if val is not None:
                elevation[x, y] = val
                fixed_mask[x, y] = True

    # Step 2: Fill free tiles via BFS (nearest control)
    q = deque()
    for y in range(h):
        for x in range(w):
            if fixed_mask[x, y]:
                q.append((x, y))

    directions = [(-1,0), (1,0), (0,-1), (0,1), (-1,-1),(1,-1),(-1,1),(1,1)]

    while q:
        x, y = q.popleft()
        for dx, dy in directions:
            nx, ny = x+dx, y+dy
            if 0 <= nx < w and 0 <= ny < h and np.isnan(elevation[nx, ny]):
                elevation[nx, ny] = elevation[x, y]
                q.append((nx, ny))

    # Step 3: Optional smoothing
    for _ in range(smoothing_passes):
        new_elev = elevation.copy()
        for y in range(h):
            for x in range(w):
                if fixed_mask[x,y]:
                    continue  # keep control points unchanged
                vals = []
                for dx, dy in directions:
                    nx, ny = x+dx, y+dy
                    if 0 <= nx < w and 0 <= ny < h:
                        vals.append(elevation[nx, ny])
                if vals:
                    new_elev[x, y] = np.mean(vals)
        elevation = new_elev
    elevation *= dh
    return elevation


def get_crown_pos(
    pos_in: Tuple[int, int], width: int, height: int, radius: int
) -> List[Tuple[int, int]]:
    """Return the list of position for each crown around a position"""

    def _is_valid(pos):
        if pos[0] < 0:
            return False
        if pos[0] > width-1:
            return False
        if pos[1] < 0:
            return False
        if pos[1] > height-1:
            return False
        return True

    crown = []
    for i in range(-radius+1, radius+1):
        crown.append((pos_in[0] + i, pos_in[1] + radius))
    for j in range(radius-1, -radius-1, -1):
        crown.append((pos_in[0] + radius, pos_in[1] + j))
    for i in range(radius-1, -radius-1, -1):
        crown.append((pos_in[0] + i, pos_in[1] - radius))
    for j in range(-radius+1, radius+1):
        crown.append((pos_in[0] - radius, pos_in[1] + j))

    return [pos for pos in crown if _is_valid(pos)]

def get_upstream_pos(
        pos_0: Tuple[int, int],
        pos_in: Tuple[int, int],    
    )->Tuple[int, int]:
    """return the last tile btw 0 and in"""
    x0,y0 = pos_0
    xi,yi = pos_in
    dx = xi-x0
    dy = yi-y0
    u=dx/max(abs(dx),abs(dy))
    v=dy/max(abs(dx),abs(dy))

    if u > 0.5:
        du=-1
    elif u < -0.5:
        du=1
    else:
        du=0
    if v > 0.5:
        dv=-1
    elif v < -0.5:
        dv=1
    else:
        dv=0

    return xi+du, yi+dv




def compute_transparency(fog_map:np.ndarray, pos_0:Tuple[int,int], dx=1.5,)->np.ndarray:
    """Fog map : opacity map in % / m 
        a fog value of 0.5 mean 50% of view los after 1 m" 
     """
    width,height=fog_map.shape
    trsp_map=np.ones_like(fog_map)

    crwn_idx=0
    while True:
        crwn_idx+=1
        tiles = get_crown_pos(pos_0,width,height,crwn_idx)
        if not tiles:
            break
        for pos in tiles:
            pos_m1 = get_upstream_pos(pos_0,pos)
            x=(pos_m1[0]-pos[0])*dx
            y=(pos_m1[1]-pos[1])*dx
            dist = math.hypot(x,y)
            trsp_map[pos] = trsp_map[pos_m1] * max(1. - fog_map[pos]*dist, 0)

    return trsp_map



def compute_nap_of_earth(elev_map:np.ndarray, pos_0:Tuple[int,int], h0=1., dx=1.5,)->np.ndarray:
    width,height=elev_map.shape
    noe_map=np.zeros_like( elev_map)
    max_angle_map=np.zeros_like(elev_map)
    noe0, a0= eval_noe(0, 0, h0)
    noe_map[pos_0] = noe0
    max_angle_map[pos_0] = a0

    crwn_idx=0
    while True:
        crwn_idx+=1
        tiles = get_crown_pos(pos_0,width,height,crwn_idx)
        if not tiles:
            break
        for pos in tiles:
            x=(pos_0[0]-pos[0])*dx
            y=(pos_0[1]-pos[1])*dx

            pos_m1 = get_upstream_pos(pos_0,pos)

            noe, max_angle = eval_noe(
                math.hypot(x,y),
                elev_map[pos]-elev_map[pos_0],
                h0,
                max_angle_map[pos_m1])
            
            max_angle_map[pos]=max_angle
            noe_map[pos]=noe
            
            

    return noe_map



def eval_noe(x:float,h:float,h0:float,max_angle_m1:float=-math.pi):
    """Evaluate Nap Of the Earth
    
                                   X
                            XXXXXXXX
                      ..XXXXXXXXXXXX
    v       XXXXXXX...XXXXXXXXXXXXXX
    XXXXXXXXXXXXXXX...XXXXXXXXXXXXXXX

    the . are places hidden by ground X elevation
    from the viewer POV

    Evaluate for a position the height hidden on top of this tile
    
    x : distance form the viewer
    h : elevation gap btw this tile and the viewer tile
    h0 : viewer height
    max_angle_m1: max_angle of view from this tile (radians)
        -pi/2 is looking right below the viewer
        0 is looking horizontally
        +pi/2 is looking vertically up

        Should be the maximum angle blocking among all tile btw viewed and target

    returns:
    noe : height hidden on this tile
    max_angle: the maximum blocking angle after this tile
        
    """
    angle=math.atan2( 
        h-h0 ,
        x
    ) #*180/math.pi
    max_angle = max(angle,max_angle_m1) 
    noe = math.tan(max_angle)*x+h0 - h

    noe = noe>0.01
    return noe,max_angle

def return_relative_pos(pos_0:Tuple[int, int], pos_in:Tuple[int, int],delta_x:float)-> Tuple[int, str]:
    """return relative position info"""
    if pos_0 == pos_in:
        return 0, "same place"
    
    dx = pos_in[0]-pos_0[0]
    dy = pos_in[1]-pos_0[1]
    
    azimuth=math.atan2(-dx,-dy)/math.pi*180

    dir=""
    mini=400
    for key,desc in {
        -180 : "South",
        -135 : "SouthEast",
        -90 : "East",
        -45 : "NorthEast",
        0 : "North",
        45 : "NorthWest",
        90 : "West",
        135 : "SouthWest",
        180 :"South"
    }.items():
        if abs(azimuth-key) < mini:
            mini = abs(azimuth-key)
            dir =desc

    return round(np.hypot(dx,dy)*delta_x), dir
 


# ascii_map = [
    
#     list("000000000000000000000000"),
#     list("000000000000000000000000"),
#     list("000000000000000000000000"),
#     list("000000000000000000000000"),
#     list("000000000000000000000000"),
#     list("000000000000000000000000"),
#     list("000050000050000050000000"),
#     list("000000000000000000000000"),
#     list("000000000000000000000000"),
#     list("0000000000000     000000"),
#     list("0000500000000  5  000000"),
#     list("0000000000000     000000"),
#     list("000000000000000000000000"),
#     list("000000000000000000000000"),
#     list("000000000000000000000000"),
#     list("000050000050000050000000"),
#     list("000000000000000000000000"),
#     list("000000000000000000000000"),
#     list("000000000000000000000000"),
#     list("000000000000000000000000"),
#     list("000000000000000000000000"),
#     # list("                    "),
#     # list("            0       "),
#     # list("                    "),
#     # list("    5               "),
#     # list("               5    "),
#     # list("          0         "),
#     # list("                    "),
#     # list("                    "),
#     # list("              4     "),
#     # list("     3    0         "),
#     # list("                    "),
#     # list("                    "),
#     # list("                    "),
#     # list("       0      5     "),
#     # list("   5                "),
#     # list("                    "),
#     # list("                    "),
#     # list("   5      0         "),
#     # list("                 4  "),
#     # list("                    "),
    
# ]
# elev_map = build_elevation_map(ascii_map, dh=1.5, smoothing_passes=1)
# #ang_,noe_ = compute_lowest_vertical_los(elev_map,(7,14),h0=2)

# fog_map = np.ones_like(elev_map)*0.01
# trsp_map = compute_transparency(fog_map, (10,10))
# plot_elevation_2d(fog_map, dx=1.5)


# plot_elevation_2d(trsp_map, dx=1.5)

# plot_elevation_2d(noe_, dx=1.5)


# profile = [0, 1, 2, 3, -3, -5, -6, 5, 6, 8, 13]



# def test_compute_noe(profile, h0, dx=1.5):
#     # a0 = math.atan2( 
#     #         -h0 ,
#     #         0
#     #     ) #*180/math.pi
#     # #max_angle_list = [a0]
    
#     noe0, a0= eval_noe(0, 0, h0)
#     noe_list = [noe0]
#     max_angle = a0
#     for i,h in enumerate(profile[1:]):
#         x = (i+1)*dx
#         noe, max_angle = eval_noe(x,h,h0,max_angle)
#        # max_angle_list.append(max_angle)
#         noe_list.append(noe)
        
#     return(profile, noe_list)


# angle_list, max_angle_list = test_compute_noe(profile,2)
# plt.plot(angle_list)
# plt.plot(max_angle_list)

# plt.show()