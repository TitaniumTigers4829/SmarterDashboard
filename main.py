from networktables.util import ChooserControl
from networktables import NetworkTables
from networktables import NetworkTablesInstance
import dearpygui.dearpygui as dpg
import numpy as np
import threading
import logging
import time

# Initialization
dpg.create_context()
dpg.configure_app(docking=True, docking_space=True)
dpg.create_viewport(title="4829 SmarterDashboard", width=800, height=600)

# Create a global dictionary to store if windows are already open
open_widgets = {
    "field_view": None,
    "grid_view": None,
    "orientation": None,
    "auto_selector": None,
    "mode_indicator": None,
}
# Global variable to see if it's connected
connection_status = False
# Global chooser options
chooser_options = []
# Current path
current_path = [
    [9.5, 8, -38.8, 180],
    [5.3, 4.75, 180, 180],
    [2.5, 4.75, 180, 180],
    [1.5, 1.42, 180, 180]
]

alternate_path = [
    [9.5, 1, -38.8, 180],
    [5.3, 4.75, 180, 180],
    [2.5, 8.75, 180, 180],
    [1.5, 4.42, 180, 180],
    [1.5, 2.42, 180, 180],
    [9.5, 5.42, 180, 180],
]

# Global robot data
robot_odometry = {
    "field_x": 8.25,
    "field_y": 4,
    "pitch": 0, # 2d rotation
    "roll": 0,
    "yaw": 0,
}

# Fetch textures (should be a function)
logo_width, logo_height, logo_channels, logo_data = dpg.load_image('GUI/4829logo.png') # 0: width, 1: height, 2: channels, 3: data
field_width, field_height, field_channels, field_data = dpg.load_image('GUI/gamefield.png') # 0: width, 1: height, 2: channels, 3: data
robot_width, robot_height, robot_channels, robot_data = dpg.load_image('GUI/robot.png')

field_aspect = field_width / field_height

def field_to_canvas(x, y):
    field_meters_width = 16.54175
    field_meters_height = 8.0137 
    normalized_x = (x / field_meters_width) - 0.5
    normalized_y = (y / (field_aspect * field_meters_height)) - (1 / (2 * field_aspect))
    return normalized_x, normalized_y

def path_to_cubic_points(path):
    points = []
    for i in range(len(path) - 1):
        start = field_to_canvas(*path[i][0:2])
        end = field_to_canvas(*path[i+1][0:2])
        handle_length = np.sqrt((start[0] - end[0])**2 + (start[1] - end[1])**2) / 3
        start_handle = [
            start[0] + np.cos(np.deg2rad(path[i][3])) * handle_length, 
            start[1] + np.sin(np.deg2rad(path[i][3])) * handle_length
        ]
        end_handle = [
            end[0] - np.cos(np.deg2rad(path[i+1][3])) * handle_length, 
            end[1] - np.sin(np.deg2rad(path[i+1][3])) * handle_length
        ]

        points.extend([start, start_handle, end_handle, end])

    return points

# God function for networktables callbacks
def on_networktales_change(source, key, value, isNew):
    global robot_odometry

    # TODO: Figure out a way to stop it from erroring when closing the program when connected

    match (key):
        case "pitch":
            dpg.set_value(item="orientation_pitch_text", value=f"Pitch: {np.round(value, 1)} deg".rjust(18))
            dpg.set_value(item="orientation_pitch_bar", value=(180 + value)/360)
            robot_odometry["pitch"] = value
        case "roll":
            dpg.set_value(item="orientation_roll_text", value=f"Roll: {np.round(value, 1)} deg".rjust(18))
            dpg.set_value(item="orientation_roll_bar", value=(180 + value)/360)
            robot_odometry["roll"] = value
        case "yaw":
            dpg.set_value(item="orientation_yaw_text", value=f"Yaw: {np.round(value, 1)} deg".rjust(18))
            dpg.set_value(item="orientation_yaw_bar", value=(180 + value)/360)
            robot_odometry["yaw"] = value
        case "position":
            robot_odometry["field_x"] = value[0]
            robot_odometry["field_y"] = value[1]
        case "botPose":
            robot_odometry["field_x"] = value[0]
            robot_odometry["field_y"] = value[1]
        case "Cargo Mode":
            dpg.configure_item(item="indicator_cube", show=(value == "Cube"))
            dpg.configure_item(item="indicator_cone", show=(value == "Cone"))

# Load textures intro registry
with dpg.texture_registry():
    dpg.add_static_texture(logo_width, logo_height, logo_data, tag="logo")
    dpg.add_static_texture(field_width, field_height, field_data, tag="field")
    dpg.add_static_texture(robot_width, robot_height, robot_data, tag="robot")

# Set up theme
def set_theme():
    with dpg.theme() as global_theme:
        with dpg.theme_component(dpg.mvAll):
            dpg.add_theme_style(dpg.mvStyleVar_WindowTitleAlign, 0.5, 0.5, category=dpg.mvThemeCat_Core)
            dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 1, category=dpg.mvThemeCat_Core)
            dpg.add_theme_style(dpg.mvStyleVar_WindowRounding, 8, category=dpg.mvThemeCat_Core)
            dpg.add_theme_style(dpg.mvStyleVar_ScrollbarRounding, 16, category=dpg.mvThemeCat_Core)

            accent1 = (236, 151, 29, 103)
            accent2 = (200, 119, 0, 153)
            accent3 = (135, 86, 15, 255)

            dpg.add_theme_color(dpg.mvThemeCol_FrameBgHovered, accent1, category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_FrameBgActive, accent2, category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_TitleBgActive, accent3, category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_FrameBg, accent3, category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_FrameBgActive, accent3, category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_FrameBgHovered, accent3, category=dpg.mvThemeCat_Core)
            
            dpg.add_theme_color(dpg.mvThemeCol_CheckMark, accent2, category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_SliderGrab, accent1, category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_SliderGrabActive, accent2, category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, accent1, category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, accent2, category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_HeaderHovered, accent1, category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_HeaderActive, accent2, category=dpg.mvThemeCat_Core)

            dpg.add_theme_color(dpg.mvThemeCol_TabHovered, accent1, category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_TabActive, accent2, category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_TabUnfocusedActive, accent2, category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_DockingPreview, accent2, category=dpg.mvThemeCat_Core)

    dpg.bind_theme(global_theme)

# Makes the grid view
def make_grid_view():
    grid_aspect = 9 / 3
    margin = 0.015

    grid_values = [
        (-0.45 + margin, -0.15 + margin), (-0.15 - margin, 0.15 - margin),
        (-0.15 + margin, -0.15 + margin), ( 0.15 - margin, 0.15 - margin),
        ( 0.15 + margin, -0.15 + margin), ( 0.45 - margin, 0.15 - margin)
    ]

    global open_widgets
    if open_widgets["grid_view"] is not None:
        dpg.delete_item(open_widgets["grid_view"])
        dpg.delete_item(item="grid_drawlist")
        dpg.delete_item(item="grid_resize_handler")

    with dpg.window(label="Grid View", tag="grid_view", no_collapse=True, no_scrollbar=True, no_title_bar=False, width=300, height=400) as grid_view:
        # Attach grid_view to the global widgets
        open_widgets["grid_view"] = grid_view

        # Make the window menu
        with dpg.menu_bar(label="Grid Menu", tag="grid_menu"):
            with dpg.menu(label="Settings"):
                dpg.add_checkbox(label="Show Blocks", tag="s_show_blocks", default_value=True)

        with dpg.drawlist(width=100, height=100, tag="grid_drawlist"):
            with dpg.draw_layer(tag="grid_pass", depth_clipping=False, perspective_divide=True):
                # Grid blocks
                with dpg.draw_node(tag="grid_block_node"):
                    dpg.draw_rectangle(pmin=grid_values[0], pmax=grid_values[1])
                    dpg.draw_rectangle(pmin=grid_values[2], pmax=grid_values[3])
                    dpg.draw_rectangle(pmin=grid_values[4], pmax=grid_values[5])

                # Actual grid
                # todo figure out a way to make this not god awful
                with dpg.draw_node(tag="grid_node"):
                    x_difference = grid_values[1][0] - grid_values[0][0]
                    y_difference = grid_values[1][1] - grid_values[0][1]

                    for x in range(3):
                        for y in range(3):
                            x_pos = x * ((x_difference / 3) - margin)
                            y_pos = y * ((y_difference / 3) - margin)
                            center = (
                                grid_values[0][0] + margin + (x_difference / 6) + x_pos, 
                                grid_values[0][1] + margin + (y_difference / 6) + y_pos
                            )
                            dpg.draw_circle(
                                center=center, 
                                radius=4, 
                                thickness=1
                            )

                    for x in range(3):
                        for y in range(3):
                            x_pos = x * ((x_difference / 3) - margin)
                            y_pos = y * ((y_difference / 3) - margin)
                            center = (
                                grid_values[2][0] + margin + (x_difference / 6) + x_pos, 
                                grid_values[2][1] + margin + (y_difference / 6) + y_pos
                            )
                            dpg.draw_circle(
                                center=center, 
                                radius=4, 
                                thickness=1
                            )

                    for x in range(3):
                        for y in range(3):
                            x_pos = x * ((x_difference / 3) - margin)
                            y_pos = y * ((y_difference / 3) - margin)
                            center = (
                                grid_values[4][0] + margin + (x_difference / 6) + x_pos, 
                                grid_values[4][1] + margin + (y_difference / 6) + y_pos
                            )
                            dpg.draw_circle(
                                center=center, 
                                radius=4, 
                                thickness=1
                            )

        dpg.set_clip_space("grid_pass", 0, 0, 100, 100, -1.0, 1.0)
        grid_scale = dpg.create_scale_matrix([1, grid_aspect])
        dpg.apply_transform("grid_block_node", grid_scale)
        dpg.apply_transform("grid_node", grid_scale)

    # Make all necessary callback functions
    def drawlist_resize(sender, appdata):
        width, height = dpg.get_item_rect_size("grid_view")
        # Annoying hack to get things sizing properly
        width -= 2 * 8
        height -= 7 * 8
        dpg.configure_item("grid_drawlist", width=width, height=height)

        # Dynamic field image resizing and positioning
        new_field_width = width
        new_field_height = height
        if (new_field_width > new_field_height * grid_aspect):
            new_field_width = height * grid_aspect

        elif (new_field_width < new_field_height * grid_aspect):
            new_field_height = width * (1 / grid_aspect)

        # Configure the clip space for the robot
        dpg.set_clip_space(
            item="grid_pass", 
            top_left_x=((width - new_field_width) // 2), 
            top_left_y=((height - new_field_height) // 2), 
            width=new_field_width, 
            height=new_field_height,
            min_depth=-1.0,
            max_depth=1.0
        )

    # Resize handler
    with dpg.item_handler_registry(tag="grid_resize_handler"):
        dpg.add_item_resize_handler(callback=drawlist_resize)

    dpg.bind_item_handler_registry("grid_view", "grid_resize_handler")
    
# Makes the auto selector window
def make_auto_selector():
    global open_widgets, chooser_options

    def auto_selector_callback(item):
        control = ChooserControl("SendableChooser[0]", inst=NetworkTablesInstance.getDefault())
        control.setSelected(dpg.get_value(item=item))

    if open_widgets["auto_selector"] is not None:
        dpg.delete_item(open_widgets["auto_selector"])

    with dpg.window(label="Auto Path Selector") as auto_selector:
        # Attach auto selector to global widgets
        open_widgets["auto_selector"] = auto_selector

        # Add items
        dpg.add_text(default_value="Select Auto Path")
        dpg.add_combo(tag="auto_selector", items=chooser_options, width=-1)

    # Attach necessary callbacks
    dpg.set_item_callback(
        item="auto_selector",
        callback=auto_selector_callback
    )

# Makes the orientation window
def make_orientation():
    grid_size = 8
    grid_ticks = 4

    axis_length = 8

    width = 4
    length = 4
    height = 1
    robot_vertices = [
        # Shape
        [-width, -length, -height],
        [width, -length, -height],
        [-width, length, -height],
        [width, length, -height],
        [-width, -length, height],
        [width, -length, height],
        [-width, length, height],
        [width, length, height],
        # Arrow
        [-width, 0, 0],
        [width, 0, 0]
    ]

    global open_widgets, robot_odometry
    if open_widgets["orientation"] is not None:
        dpg.delete_item(open_widgets["orientation"])
        dpg.delete_item(item="orientation_drawlist")
        dpg.delete_item(item="orientation_resize_handler")

    with dpg.window(label="Robot Orientation", tag="orientation", no_collapse=True, no_scrollbar=True, no_title_bar=False, width=300, height=400) as orientation:
        # Attach orientation to the global widgets
        open_widgets["orientation"] = orientation

        # Make the window menu
        with dpg.menu_bar(label="Orientation Menu", tag="orientation_menu"):
            with dpg.menu(label="Settings"):
                dpg.add_checkbox(label="Show Grid", tag="s_show_grid", default_value=True)
                dpg.add_checkbox(label="Show Axis", tag="s_show_axis", default_value=True)

        # Create Items
        with dpg.group(horizontal=True):
            dpg.add_text(tag="orientation_pitch_text", default_value=f"Pitch: {robot_odometry['pitch']} deg".rjust(18))
            dpg.add_progress_bar(tag="orientation_pitch_bar", label="Pitch", width=-1, default_value=robot_odometry['pitch']/360)
        with dpg.group(horizontal=True):
            dpg.add_text(tag="orientation_roll_text", default_value=f"Roll: {robot_odometry['roll']} deg".rjust(18))
            dpg.add_progress_bar(tag="orientation_roll_bar", label="Roll", width=-1, default_value=robot_odometry['roll']/360)
        with dpg.group(horizontal=True):
            dpg.add_text(tag="orientation_yaw_text", default_value=f"Yaw: {robot_odometry['yaw']} deg".rjust(18))
            dpg.add_progress_bar(tag="orientation_yaw_bar", label="Yaw", width=-1, default_value=robot_odometry['yaw']/360)

        with dpg.drawlist(width=100, height=100, tag="orientation_drawlist"):
            with dpg.draw_layer(tag="robot_3d_pass", depth_clipping=False, perspective_divide=True):

                with dpg.draw_node(tag="grid_3d"):
                    for i in range(-grid_ticks, grid_ticks + 1):
                        step = i * (grid_size / grid_ticks)
                        dpg.draw_line([step, -grid_size, 0], [step, grid_size, 0], thickness=1, color=(255, 255, 255, 50))
                        dpg.draw_line([-grid_size, step, 0], [grid_size, step, 0], thickness=1, color=(255, 255, 255, 50))
                
                with dpg.draw_node(tag="axis_3d"):
                    dpg.draw_line([axis_length, 0, 0], [0, 0, 0], color=(255, 0, 0, 50), thickness=3)
                    dpg.draw_line([0, axis_length, 0], [0, 0, 0], color=(0, 255, 0, 50), thickness=3)
                    dpg.draw_line([0, 0, axis_length], [0, 0, 0], color=(0, 0, 255, 50), thickness=3)

                with dpg.draw_node(tag="robot_3d"):
                    # Bottom face
                    dpg.draw_line(robot_vertices[0], robot_vertices[1], thickness=2)
                    dpg.draw_line(robot_vertices[0], robot_vertices[2], thickness=2)
                    dpg.draw_line(robot_vertices[1], robot_vertices[3], thickness=2)
                    dpg.draw_line(robot_vertices[2], robot_vertices[3], thickness=2)
                    # Arrow to how which way is forward
                    dpg.draw_arrow(robot_vertices[9], robot_vertices[8], thickness=2, size=2, color=(255, 100, 0, 255))
                    # Connecting lines
                    dpg.draw_line(robot_vertices[0], robot_vertices[4], thickness=2)
                    dpg.draw_line(robot_vertices[1], robot_vertices[5], thickness=2)
                    dpg.draw_line(robot_vertices[2], robot_vertices[6], thickness=2)
                    dpg.draw_line(robot_vertices[3], robot_vertices[7], thickness=2)
                    # Top face
                    dpg.draw_line(robot_vertices[4], robot_vertices[5], thickness=2)
                    dpg.draw_line(robot_vertices[4], robot_vertices[6], thickness=2)
                    dpg.draw_line(robot_vertices[5], robot_vertices[7], thickness=2)
                    dpg.draw_line(robot_vertices[6], robot_vertices[7], thickness=2)
        
        dpg.set_clip_space("robot_3d_pass", 0, 0, 100, 100, -5.0, 5.0)
        
        # Make all necessary callback functions
        def drawlist_resize(sender, appdata):
            width, height = dpg.get_item_rect_size("orientation")
            width -= 2 * 8
            height -= 14 * 8
            dpg.configure_item("orientation_drawlist", width=width, height=height)

            # Drawing space
            drawing_size = min(width, height)
            dpg.set_clip_space(
                item="robot_3d_pass", 
                top_left_x=((width - drawing_size) // 2), 
                top_left_y=((height - drawing_size) // 2), 
                width=drawing_size, 
                height=drawing_size,
                min_depth=-5.0,
                max_depth=5.0
            )

        dpg.set_item_callback(
            "s_show_grid", 
            callback=lambda x: dpg.configure_item("grid_3d", show=dpg.get_value(x))
        )
        dpg.set_item_callback(
            "s_show_axis", 
            callback=lambda x: dpg.configure_item("axis_3d", show=dpg.get_value(x))
        )

        # Make all necessary connections for proper resizing
        with dpg.item_handler_registry(tag="orientation_resize_handler"):
            dpg.add_item_resize_handler(callback=drawlist_resize)

        dpg.bind_item_handler_registry("orientation", "orientation_resize_handler")

# Makes the mode indicator
def make_mode_indicator():
    global open_widgets, robot_odometry

    if open_widgets["mode_indicator"] is not None:
        dpg.delete_item(open_widgets["mode_indicator"])
        dpg.delete_item(item="indicator_drawlist")
        dpg.delete_item(item="indicator_resize_handler")

    with dpg.window(label="Robot Mode", tag="mode_indicator", no_collapse=True, no_scrollbar=True, no_title_bar=False, width=200, height=200) as indicator:
        # Attach orientation to the global widgets
        open_widgets["mode_indicator"] = indicator

        with dpg.drawlist(width=100, height=100, tag="indicator_drawlist"):
            with dpg.draw_layer(tag="mode_indicator_pass", depth_clipping=False, perspective_divide=True):
                with dpg.draw_node(tag="indicator_cube", show=True):
                    dpg.draw_polygon(
                        points=[[-0.4, -0.4], [-0.4, 0.4], [0.4, 0.4], [0.4, -0.4], [-0.4, -0.4], [-0.4, 0.4]],
                        fill=(255, 0, 255, 30),
                        color=(255, 0, 255),
                        thickness=5
                    )

                with dpg.draw_node(tag="indicator_cone", show=False):
                    dpg.draw_polygon(
                        points=[[-0.4, -0.4], [-0.4, -0.25], [0.4, -0.25], [0.4, -0.4], [-0.4, -0.4], [-0.4, -0.25]],
                        fill=(255, 255, 0, 30),
                        color=(255, 255, 0),
                        thickness=5
                    )
                    dpg.draw_polygon(
                        points=[[-0.25, -0.25], [-0.05, 0.4], [0.05, 0.4], [0.25, -0.25]],
                        fill=(255, 255, 0, 30),
                        color=(255, 255, 0),
                        thickness=5
                    )

            dpg.set_clip_space("robot_3d_pass", 0, 0, 100, 100, -5.0, 5.0)

    def drawlist_resize(sender, appdata):
        width, height = dpg.get_item_rect_size("mode_indicator")
        width -= 2 * 8
        height -= 5 * 8
        dpg.configure_item("indicator_drawlist", width=width, height=height)

        # Drawing space
        drawing_size = min(width, height)
        dpg.set_clip_space(
            item="mode_indicator_pass",
            top_left_x=((width - drawing_size) // 2),
            top_left_y=((height - drawing_size) // 2),
            width=drawing_size,
            height=drawing_size,
            min_depth=-5.0,
            max_depth=5.0
        )
    # Make all necessary connections for proper resizing
    with dpg.item_handler_registry(tag="indicator_resize_handler"):
        dpg.add_item_resize_handler(callback=drawlist_resize)

    dpg.bind_item_handler_registry("mode_indicator", "indicator_resize_handler")

# Draws the path and all such points
def draw_path():
    dpg.delete_item(item="robot_path")
    dpg.delete_item(item="robot_handles")
    dpg.delete_item(item="robot_points")

    with dpg.draw_node(tag="robot_path", parent="field_robot_pass", show=False):
        bezier_points = path_to_cubic_points(current_path)
        
        for i in range(int(len(bezier_points) / 4)):
            # dpg.draw_circle(center=bezier_points[i], radius=3, thickness=2)
            dpg.draw_bezier_cubic(
                p1=bezier_points[(i*4) + 0],
                p2=bezier_points[(i*4) + 1],
                p3=bezier_points[(i*4) + 2],
                p4=bezier_points[(i*4) + 3],
                thickness=5,
                color=(155, 155, 255, 200)
            )

    with dpg.draw_node(tag="robot_handles", parent="field_robot_pass", show=False):
        bezier_points = path_to_cubic_points(current_path)
        
        for i in range(int(len(bezier_points) / 4)):
            dpg.draw_circle(center=bezier_points[(i*4) + 1], radius=3, thickness=2)
            dpg.draw_circle(center=bezier_points[(i*4) + 2], radius=3, thickness=2)
            dpg.draw_line(p1=bezier_points[(i*4)], p2=bezier_points[(i*4) + 1])
            dpg.draw_line(p1=bezier_points[(i*4) + 3], p2=bezier_points[(i*4) + 2])

    with dpg.draw_node(tag="robot_points", parent="field_robot_pass", show=False):
        for node in current_path:
            dpg.draw_circle(
                center=field_to_canvas(*node[0:2]), 
                radius=5, 
                thickness=4,
                color=(0, 0, 0),
                fill=(255, 255, 255)
            )

# Makes the field layout window
def make_field_view():
    robot_width = 0.03
    robot_height = 0.03

    robot_vertices = [
        # Box
        [-robot_width, -robot_height],
        [ robot_width, -robot_height],
        [ robot_width,  robot_height],
        [-robot_width,  robot_height],
        [-robot_width, -robot_height],
    ]
    arrow_vertices = [
        # Arrow
        [0, -robot_height * 0.8],
        [0,  robot_height * 0.25],
        [-robot_width * 0.35, robot_height * 0.25],
        [0,  robot_height * 0.8],
        [robot_width * 0.35, robot_height * 0.25],
        [0,  robot_height * 0.25],
    ]

    global open_widgets, current_path

    if open_widgets["field_view"] is not None:
        dpg.delete_item(open_widgets["field_view"])
        dpg.delete_item(item="field_drawlist")
        dpg.delete_item(item="field_resize_handler")

    # Make the window
    with dpg.window(label="Field View", tag="field_view", no_collapse=True, no_scrollbar=True, no_title_bar=False, width=400, height=300) as field_view:
        # Attach field view to the global widgets
        open_widgets["field_view"] = field_view

        # Make the menu for the window
        with dpg.menu_bar(label="Field Menu", tag="field_menu"):
            with dpg.menu(label="Field Settings"):
                dpg.add_checkbox(label="Flip Field", tag="fs_flip_field")

            with dpg.menu(label="Robot Settings"):
                dpg.add_checkbox(label="Show Robot", tag="rs_show_robot", default_value=True)

            with dpg.menu(label="Path Settings"):
                dpg.add_checkbox(label="Show Path", tag="ps_show_path", default_value=False)
                dpg.add_checkbox(label="Show Waypoints", tag="ps_show_waypoints", default_value=False)
                dpg.add_checkbox(label="Show Handles", tag="ps_show_handles", default_value=False)
        
        # Create items
        with dpg.drawlist(width=100, height=100, tag="field_drawlist"):
            dpg.draw_image(texture_tag="field", tag="field_image", pmin=(0, 0), pmax=(field_width, field_height))

            with dpg.draw_layer(tag="field_robot_pass", depth_clipping=False, perspective_divide=True):
                with dpg.draw_node(tag="field_robot"):
                    dpg.draw_polygon(arrow_vertices, thickness=3, color=(255, 100, 0), fill=(255, 100, 0))
                    dpg.draw_polygon(robot_vertices, thickness=3, fill=(255, 255, 255, 10))
                    
            dpg.set_clip_space("field_robot_pass", 0, 0, 100, 100, -5.0, 5.0)

        draw_path()
    
    # Make all necessary callback functions
    def drawlist_resize(sender, appdata):
        width, height = dpg.get_item_rect_size("field_view")
        # Annoying hack to get things sizing properly
        width -= 2 * 8
        height -= 7 * 8
        dpg.configure_item("field_drawlist", width=width, height=height)

        # Dynamic field image resizing and positioning
        new_field_width = width
        new_field_height = height
        if (new_field_width > new_field_height * field_aspect):
            new_field_width = height * field_aspect

        elif (new_field_width < new_field_height * field_aspect):
            new_field_height = width * (1 / field_aspect)

        field_min = [(width - new_field_width) // 2, (height - new_field_height) // 2]
        field_max = [field_min[0] + new_field_width, field_min[1] + new_field_height]

        if (dpg.get_value("fs_flip_field")):
            tmp = field_min[0]
            field_min[0] = field_max[0]
            field_max[0] = tmp

        dpg.configure_item("field_image", pmin=field_min, pmax=field_max)

        # Configure the clip space for the robot
        dpg.set_clip_space(
            item="field_robot_pass", 
            top_left_x=((width - new_field_width) // 2), 
            top_left_y=((height - new_field_height) // 2), 
            width=new_field_width, 
            height=new_field_height,
            min_depth=-1.0,
            max_depth=1.0
        )

    # Make all necessary connections for settings to work
    dpg.set_item_callback("fs_flip_field", callback=drawlist_resize)
    dpg.set_item_callback(
        "rs_show_robot",
        callback=lambda x: dpg.configure_item("field_robot", show=dpg.get_value(x))
    )
    dpg.set_item_callback(
        "ps_show_path",
        callback=lambda x: dpg.configure_item("robot_path", show=dpg.get_value(x))
    )
    dpg.set_item_callback(
        "ps_show_waypoints",
        callback=lambda x: dpg.configure_item("robot_points", show=dpg.get_value(x))
    )
    dpg.set_item_callback(
        "ps_show_handles",
        callback=lambda x: dpg.configure_item("robot_handles", show=dpg.get_value(x))
    )

    # Make all necessary connections for proper resizing
    with dpg.item_handler_registry(tag="field_resize_handler"):
        dpg.add_item_resize_handler(callback=drawlist_resize)

    dpg.bind_item_handler_registry("field_view", "field_resize_handler")

# Update for whenever the frame is drawn
def draw_call_update():
    global robot_odometry
    pitch = robot_odometry["pitch"] * np.pi / 180
    roll = robot_odometry["roll"] * np.pi / 180
    yaw = robot_odometry["yaw"] * np.pi / 180

    x, y = field_to_canvas(robot_odometry["field_x"], robot_odometry["field_y"])

    # Orientation
    if open_widgets["orientation"] is not None:
        view = dpg.create_fps_matrix([0, 20, 10], pitch=(np.pi / 3), yaw=(np.pi))
        proj = dpg.create_perspective_matrix(90.0 * (np.pi / 180.0), 1.0, 0.1, 100)
        orientation_3d = dpg.create_rotation_matrix(-np.pi / 4, [0, 0, 1])

        # Always make sure Y is first otherwise there's gonna be some serious problems
        robot_rotation = dpg.create_rotation_matrix(pitch, [0, 0, 1]) * \
                            dpg.create_rotation_matrix(yaw, [0, 1, 0]) * \
                            dpg.create_rotation_matrix(roll, [1, 0, 0])
        dpg.apply_transform("robot_3d", proj*view*orientation_3d*robot_rotation)
        dpg.apply_transform("grid_3d", proj*view*orientation_3d)
        dpg.apply_transform("axis_3d", proj*view*orientation_3d)

    # Field View
    if open_widgets["field_view"] is not None:
        field_scale = dpg.create_scale_matrix([1, field_aspect])
        field_rotation = dpg.create_rotation_matrix(pitch, [0, 0, -1])
        field_position = dpg.create_translation_matrix([x, y])
        dpg.apply_transform("field_robot", field_scale*field_position*field_rotation)

# Target thread to make some connections
def connect_table_and_listeners(timeout=5):
    global table_instance, chooser_options

    NetworkTables.startClientTeam(4829)
    
    def connected_callback(connection, info):
        global connection_status
        connection_status = True
        dpg.set_value(item="connection_text", value="Connected")
        dpg.configure_item(item="connection_text", color=(0, 255, 0))

    NetworkTables.addConnectionListener(
        listener=connected_callback,
        immediateNotify=True
    )

    # Some kind of waiting routine
    start = time.time()
    while (time.time() - start < timeout) and not connection_status:
        pass
    
    if (not connection_status): 
        dpg.set_value(item="connection_text", value="Failed To Connect (Timeout)")
        dpg.configure_item(item="connection_text", color=(255, 0, 0))
        return


    table_instance = NetworkTables.getTable("SmartDashboard")
    chooser_options = ChooserControl("SendableChooser[0]", inst=NetworkTablesInstance.getDefault()).getChoices()
    dpg.configure_item(item="auto_selector", items=chooser_options)

    table_instance.addEntryListener(on_networktales_change)

def sample_path():
    global current_path
    current_path = alternate_path.copy()
    draw_path()
def main():
    # Create the menu bar
    with dpg.viewport_menu_bar(label="Menu", tag="menu"):
        with dpg.menu(label="Settings"):
            dpg.add_menu_item(label="Enable Something")
        with dpg.menu(label="Widgets"):
            dpg.add_menu_item(label="Field View", callback=make_field_view)
            dpg.add_menu_item(label="Grid View", callback=make_grid_view)
            dpg.add_menu_item(label="Orientation", callback=make_orientation)
            dpg.add_menu_item(label="Auto Selector", callback=make_auto_selector)
            dpg.add_menu_item(label="Mode Indicator", callback=make_mode_indicator)
        with dpg.menu(label="Override"):
            dpg.add_button(
                label="Attempt Reconnect", 
                callback=lambda _: threading.Thread(target=connect_table_and_listeners, daemon=True).start()
            )
            dpg.add_button(
                label="New Path",
                callback=sample_path
            )
            dpg.add_button(
                label="Manual Theme Edit",
                callback=dpg.show_style_editor
            )
        dpg.add_spacer(width=30)
        dpg.add_text(default_value="Status:", color=(255, 255, 255, 100))
        dpg.add_text(tag="connection_text", default_value="Not Connected", color=(255, 0, 0))

    # Networktables Setup
    logging.basicConfig(level=logging.DEBUG)
    threading.Thread(target=connect_table_and_listeners, daemon=True).start()
    
    # Make all the windows to start with
    make_grid_view()
    make_auto_selector()
    make_orientation()
    make_field_view()
    make_mode_indicator()

    # Setup
    dpg.setup_dearpygui()
    dpg.show_viewport()

    set_theme()
    # Update loop
    while dpg.is_dearpygui_running():
        draw_call_update()
        dpg.render_dearpygui_frame()

    dpg.start_dearpygui()
    dpg.destroy_context()

if __name__ == "__main__":
    main()