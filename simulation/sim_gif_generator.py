# gif_generator.py
import json
import glob
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from PIL import Image
from scipy.ndimage import rotate

# --- Configuration ---
DPI = 96
FPS = 15

# --- Visual Improvements Config ---
# --- NEW: Configuration for adaptive plot sizing ---
PLOT_PADDING_FACTOR = 1.2 # Use 20% padding around the action space
ABSOLUTE_MIN_PLOT_SIZE = 60.0 # Smallest possible plot dimension in meters
POINTER_IMAGE_PATH = 'pointer.webp' 
# NEW: Define pointer size in plot data units (meters)
POINTER_SIZE_METERS = 12.0 
POINTER_ROTATION_OFFSET = 225.0 # (This is 45 + 180)
SKYBEACON_COLOR = '#0077BE' # Blue
INTRUDER_COLOR = '#D95319' # Orange

SCENARIO_TITLES = {
    "HeadOn_Collision": "Head-On Collision Scenario",
    "Crossing_Collision": "Crossing Paths Scenario",
    "Overtake_From_Behind": "Overtake Scenario",
    "Stationary_Collision": "Stationary Drone with Approaching Intruder",
    "Converging_Paths": "Converging Paths (Shallow Angle)",
    "Parallel_Near_Miss": "Parallel Paths (Near Miss)",
    "Perpendicular_Intersection": "Perpendicular Intersection"
}

def create_colorized_image(image_path, color_hex):
    """Loads an image and applies a color tint."""
    img = Image.open(image_path).convert("LA")
    img_data = np.array(img)
    rgba_img = np.zeros((img_data.shape[0], img_data.shape[1], 4), dtype=np.uint8)
    rgb_color = tuple(int(color_hex.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
    rgba_img[:, :, 0] = rgb_color[0]
    rgba_img[:, :, 1] = rgb_color[1]
    rgba_img[:, :, 2] = rgb_color[2]
    rgba_img[:, :, 3] = img_data[:, :, 1]
    return rgba_img

def generate_web_animation(data_filepath, sb_img_base, in_img_base):
    """Loads data from a JSON file and generates an improved, web-friendly GIF."""
    
    print(f"\n--- Loading data from: {data_filepath} ---")
    try:
        with open(data_filepath, 'r') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error loading file: {e}")
        return

    scenario_name = data["scenario_name"]
    goal_pos = np.array(data["goal_position_ned"])
    sb_path = np.array(data["skybeacon_path"])
    in_path = np.array(data["intruder_path"])
    
    plt.style.use('seaborn-v0_8-whitegrid')
    fig, ax = plt.subplots(figsize=(10, 10))
    
# --- FINAL: Per-Scenario or Adaptive plot sizing ---
    all_x = np.concatenate((sb_path[:, 1], in_path[:, 1], [goal_pos[1]]))
    all_y = np.concatenate((sb_path[:, 0], in_path[:, 0], [goal_pos[0]]))
    
    data_center_x = (all_x.max() + all_x.min()) / 2
    data_center_y = (all_y.max() + all_y.min()) / 2

    # Check if a specific plot size was provided in the data file
    manual_plot_size = data.get("plot_size")
    if manual_plot_size:
        final_plot_dim = manual_plot_size
        print(f"  Using manual plot size from scenario: {final_plot_dim}m")
    else:
        # Fallback to adaptive logic if no size is specified
        data_range = max(all_x.max() - all_x.min(), all_y.max() - all_y.min())
        plot_base_size = max(data_range, ABSOLUTE_MIN_PLOT_SIZE)
        final_plot_dim = plot_base_size * PLOT_PADDING_FACTOR
    
    # Set limits centered on the data
    ax.set_xlim(data_center_x - final_plot_dim / 2, data_center_x + final_plot_dim / 2)
    ax.set_ylim(data_center_y - final_plot_dim / 2, data_center_y + final_plot_dim / 2)
    ax.set_aspect('equal', adjustable='box')
    display_title = SCENARIO_TITLES.get(scenario_name, scenario_name.replace('_', ' '))
    ax.set_title(f"SkyBeacon Collision Avoidance\n{display_title}", fontsize=16)
    ax.set_xlabel("East (m)", fontsize=12)
    ax.set_ylabel("North (m)", fontsize=12)

    # Static plot elements
    ax.plot(sb_path[0, 1], sb_path[0, 0], 'o', color='green', markersize=10, label='SkyBeacon Start')
    ax.plot(in_path[0, 1], in_path[0, 0], 'X', color='darkred', markersize=10, markeredgewidth=2.5, label='Intruder Start')
    ax.plot(goal_pos[1], goal_pos[0], '*', color='gold', markersize=20, markeredgecolor='black', label='Goal')

    # Dynamic plot elements
    skybeacon_path_line, = ax.plot([], [], '-', color=SKYBEACON_COLOR, linewidth=1.5, alpha=0.8, label='SkyBeacon Path')
    intruder_path_line, = ax.plot([], [], '-', color=INTRUDER_COLOR, linewidth=1.5, alpha=0.8, label='Intruder Path')
    
    # --- NEW METHOD: Using ax.imshow for drone symbols ---
    # Create the initial image artists. They will be updated in each frame.
    sb_artist = ax.imshow(sb_img_base, extent=[0,1,0,1], zorder=10)
    in_artist = ax.imshow(in_img_base, extent=[0,1,0,1], zorder=10)

    time_text = ax.text(0.02, 0.95, '', transform=ax.transAxes, fontsize=12, bbox=dict(facecolor='white', alpha=0.7))
    ax.legend(loc='upper right')

    def get_heading(path, index):
        if index < 1: # Use frames 0 and 1 for the first frame's heading
            dx = path[1, 1] - path[0, 1]
            dy = path[1, 0] - path[0, 0]
        else:
            dx = path[index, 1] - path[index-1, 1]
            dy = path[index, 0] - path[index-1, 0]
        if abs(dx) < 1e-6 and abs(dy) < 1e-6: return None # No movement
        return np.rad2deg(np.arctan2(dy, dx)) + POINTER_ROTATION_OFFSET

    # Store last known heading in case of no movement
    last_headings = {'sb': 0, 'in': 0} 

    def animate(i):
        # Update path trails
        skybeacon_path_line.set_data(sb_path[:i+1, 1], sb_path[:i+1, 0])
        intruder_path_line.set_data(in_path[:i+1, 1], in_path[:i+1, 0])
        
        # --- Update SkyBeacon Symbol ---
        x, y = sb_path[i, 1], sb_path[i, 0]
        heading = get_heading(sb_path, i)
        if heading is not None: last_headings['sb'] = heading
        rotated_img = rotate(sb_img_base, last_headings['sb'], reshape=False, mode='constant', cval=0)
        
        size = POINTER_SIZE_METERS
        extent = [x - size/2, x + size/2, y - size/2, y + size/2]
        
        sb_artist.set_data(rotated_img)
        sb_artist.set_extent(extent)

        # --- Update Intruder Symbol ---
        x, y = in_path[i, 1], in_path[i, 0]
        heading = get_heading(in_path, i)
        if heading is not None: last_headings['in'] = heading
        rotated_img = rotate(in_img_base, last_headings['in'], reshape=False, mode='constant', cval=0)

        extent = [x - size/2, x + size/2, y - size/2, y + size/2]

        in_artist.set_data(rotated_img)
        in_artist.set_extent(extent)
        
        time_text.set_text(f'Time: {i / data["sim_frequency_hz"]:.1f}s')
        
        # Return all artists that change
        return skybeacon_path_line, intruder_path_line, sb_artist, in_artist, time_text

    num_frames = min(len(sb_path), len(in_path))
    ani = animation.FuncAnimation(fig, animate, frames=num_frames, blit=False, interval=1000/FPS)

    output_filename = f"web_animation_{scenario_name.lower().replace(' ', '_')}.gif"
    print(f"  Generating GIF: {output_filename} ...")
    ani.save(output_filename, writer='pillow', fps=FPS, dpi=DPI)
    print(f"  Successfully saved animation!")
    plt.close(fig)

if __name__ == "__main__":
    try:
        sb_img = create_colorized_image(POINTER_IMAGE_PATH, SKYBEACON_COLOR)
        in_img = create_colorized_image(POINTER_IMAGE_PATH, INTRUDER_COLOR)
    except FileNotFoundError:
        print(f"Error: Custom pointer image not found at '{POINTER_IMAGE_PATH}'")
        exit()

    data_files = glob.glob("sim_data_scenario_*.json")
    if not data_files:
        print("No simulation data files found. Please run the simulation script first.")
    else:
        for filepath in sorted(data_files):
            generate_web_animation(filepath, sb_img, in_img)
    
    print("\nAll GIFs generated.")