import json
import hashlib
import math
import sys
import os

# --- Layout Algorithm (Grand Cross) ---
def generate_city_slots(limit):
    slots = []
    facing_dir = []
    
    # 0. Central House (e.g. First Entry or Today)
    slots.append((0, 0))
    facing_dir.append("down")
    
    # If limit is 1, we are done
    if limit <= 1:
        return slots, facing_dir, []
        
    # Generate remaining slots
    limit_remaining = limit - 1
    
    # "Grand Cross" Layout
    HOUSE_GAP = 2
    STREET_GAP = 2 
    MAIN_AVENUE_WIDTH = 6
    
    CLUSTER_ROWS = 4
    CLUSTER_COLS = 4
    HOUSES_PER_BLOCK = CLUSTER_ROWS * CLUSTER_COLS
    
    # Calculate Block Size
    BLOCK_WIDTH = (CLUSTER_COLS - 1) * HOUSE_GAP
    BLOCK_HEIGHT = (CLUSTER_ROWS - 1) * HOUSE_GAP
    
    # Stride
    BLOCK_STRIDE_X = BLOCK_WIDTH + STREET_GAP
    BLOCK_STRIDE_Y = BLOCK_HEIGHT + STREET_GAP
    
    # Number of houses needed
    total_blocks = math.ceil(limit / HOUSES_PER_BLOCK)
    
    # We distribute blocks into 4 Quadrants symmetrically
    # 0: NE (+x, -y), 1: NW (-x, -y), 2: SW (-x, +y), 3: SE (+x, +y)
    quadrants = [
        (1, -1),  # NE
        (-1, -1), # NW
        (-1, 1),  # SW
        (1, 1)    # SE
    ]
    
    abstract_block_positions = []
    layer = 0
    while len(abstract_block_positions) * 4 < total_blocks + 4: # +4 buffer
        for x in range(layer + 1):
            y = layer - x
            abstract_block_positions.append((x, y))
        layer += 1
        
    # Generate Houses
    houses_placed = 0
    road_tiles = set()
    
    for bx, by in abstract_block_positions:
        for q_idx in range(4):
            if houses_placed >= limit: break
            
            qx, qy = quadrants[q_idx]
            
            # Base (Start of Cluster near center)
            base_x = (MAIN_AVENUE_WIDTH / 2) * qx
            base_y = (MAIN_AVENUE_WIDTH / 2) * qy
            
            # Add block strides
            block_start_x = base_x + (bx * BLOCK_STRIDE_X * qx)
            block_start_y = base_y + (by * BLOCK_STRIDE_Y * qy)
            
            # Fill the block
            for i in range(HOUSES_PER_BLOCK):
                if houses_placed >= limit_remaining: break
                
                # Inner Grid
                ix = i % CLUSTER_COLS
                iy = i // CLUSTER_COLS
                
                house_x = block_start_x + (ix * HOUSE_GAP * qx)
                house_y = block_start_y + (iy * HOUSE_GAP * qy)
                
                slots.append((house_x, house_y))
                
                # Facing Logic
                if house_x > 0:
                    facing_dir.append("left")
                else:
                    facing_dir.append("right")
                
                houses_placed += 1
            
            # --- Road Generation ---
            def get_r_coord(idx):
                if idx == 0: return 0
                return 2 + idx * 8
            
            rx_in = get_r_coord(bx) * qx
            rx_out = get_r_coord(bx + 1) * qx
            ry_in = get_r_coord(by) * qy
            ry_out = get_r_coord(by + 1) * qy
            
            sx = int(min(rx_in, rx_out))
            ex = int(max(rx_in, rx_out))
            sy = int(min(ry_in, ry_out))
            ey = int(max(ry_in, ry_out))
            
            for x in range(sx, ex + 1):
                road_tiles.add((x, int(ry_in)))
                road_tiles.add((x, int(ry_out)))
            for y in range(sy, ey + 1):
                road_tiles.add((int(rx_in), y))
                road_tiles.add((int(rx_out), y))
                
    # --- Central House Adjustment ---
    # Clear roads under center
    for i in range(-2, 3):
         if (0, i) in road_tiles: road_tiles.remove((0, i))
         if (i, 0) in road_tiles: road_tiles.remove((i, 0))
         
    # Ring Road
    ring_min = -2
    ring_max = 2
    for x in range(ring_min, ring_max + 1):
        road_tiles.add((x, ring_min))
        road_tiles.add((x, ring_max))
    for y in range(ring_min, ring_max + 1):
        road_tiles.add((ring_min, y))
        road_tiles.add((ring_max, y))
                
    return slots, facing_dir, list(road_tiles)

# --- Helpers ---
def string_to_color(s):
    hash_object = hashlib.md5(s.encode())
    hex_dig = hash_object.hexdigest()
    return "#" + hex_dig[:6]

def string_to_pseudo_random(s):
    hash_object = hashlib.md5(s.encode())
    hex_dig = hash_object.hexdigest()
    nums = [int(hex_dig[i], 16) % 4 for i in range(5)]
    return nums

# --- Main Logic ---
# --- Main Logic ---
def generate(diary_path, output_dir):
    if not os.path.exists(diary_path):
        print(f"diary_data.json not found at {diary_path}")
        return

    with open(diary_path, "r") as f:
        try:
            data = json.load(f)
        except:
            data = {}
            
    # Filter valid entries (non-empty)
    # The user manual said "if i entry anything"
    valid_dates = []
    for date_str, entries in data.items():
        # Check if there's any non-empty answer
        if any(v.strip() for v in entries.values()):
            valid_dates.append(date_str)
            
    # Sort dates (Oldest first? Or Newest? Grand Cross usually centers the "first" or "main" one)
    # Let's sort oldest first so the city grows outwards as time passes.
    valid_dates.sort()
    
    # Generate Layout
    limit = len(valid_dates)
    
    slots, facings, roads = generate_city_slots(limit) if limit > 0 else ([], [], [])
    
    houses_output = []
    
    for i, date_str in enumerate(valid_dates):
        slot_x, slot_y = slots[i]
        
        # Generate attributes
        attrs = string_to_pseudo_random(date_str)
        facing = facings[i]
        
        house = {
            "x": slot_x,
            "y": slot_y,
            "color": string_to_color(date_str),
            "roofStyle": attrs[0],
            "doorStyle": attrs[1],
            "windowStyle": attrs[2],
            "chimneyStyle": attrs[3],
            "wallStyle": attrs[4],
            "username": date_str, # Using Date as Username
            "facing": facing,
            "has_terrace": False,
            "obstacle": None 
        }
        houses_output.append(house)
        
    # Write Output
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    houses_path = os.path.join(output_dir, "houses.json")
    roads_path = os.path.join(output_dir, "roads.json")
    
    with open(houses_path, "w") as f:
        json.dump(houses_output, f, indent=4)
        
    road_data = [{"x": int(r[0]), "y": int(r[1])} for r in roads]
    with open(roads_path, "w") as f:
        json.dump(road_data, f, indent=4)
        
    print(f"Generated {len(houses_output)} houses from diary entries.")


def main():
    # Helper for running standalone
    base_dir = os.path.dirname(os.path.abspath(__file__))
    diary_path = os.path.join(base_dir, "..", "diary_data.json")
    generate(diary_path, base_dir)

if __name__ == "__main__":
    main()
