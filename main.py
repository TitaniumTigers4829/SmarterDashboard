from networktables.util import ChooserControl
from networktables import NetworkTables
from networktables import NetworkTablesInstance
import dearpygui.dearpygui as dpg
from shapely import Point, Polygon, overlaps, LineString
import numpy as np
import threading
import logging
import time

# Initialization
dpg.create_context()
dpg.configure_app(docking=True, docking_space=True)
dpg.create_viewport(title="4829 SmarterDashboard", width=1300, height=800)

# Create a global dictionary to store if windows are already open
open_widgets = {
    "field_view": None,
    "orientation": None,
    "auto_selector": None,
    "mode_indicator": None,
    "path_detection": None,
}
# Global variable to see if it's connected
connection_status = False
# Global chooser options
chooser_options = []

# Global robot data
robot_odometry = {
    "field_x": 8.25,
    "field_y": 4,
    "pitch": 0, # 2d rotation
    "roll": 0,
    "yaw": 0,
}

limelight_odometry = {
    "field_x": 8.25,
    "field_y": 4,
    "pitch": 0, # 2d rotation
}

# coordinates for field places
red_amp_cords = [13.75, 10, True, 90]
blue_amp_cords = [2.5, 10, True, 90]
red_speaker_cords = [15.25, 7.25, True, 0]
blue_speaker_cords = [1.25, 7, True, 180]

# waypoints for object avoidance

red_upper_waypoint_x = 690
red_upper_waypoint_y = 265
red_middle_waypoint_x = 877
red_middle_waypoint_y = 372
red_lower_waypoint_x = 690
red_lower_waypoint_y = 478

blue_upper_waypoint_x = 375
blue_upper_waypoint_y = 265
blue_middle_waypoint_x = 190
blue_middle_waypoint_y = 372
blue_lower_waypoint_x = 375
blue_lower_waypoint_y = 475 

blue_stage_triangle = Polygon([(blue_upper_waypoint_x, blue_upper_waypoint_y), (blue_lower_waypoint_x, blue_lower_waypoint_y), (blue_middle_waypoint_x, blue_middle_waypoint_y)])
red_stage_triangle = Polygon([(red_upper_waypoint_x, red_upper_waypoint_y), (red_lower_waypoint_x, red_lower_waypoint_y), (red_middle_waypoint_x, red_middle_waypoint_y)])
# Fetch textures (should be a function)
logo_width, logo_height, logo_channels, logo_data = dpg.load_image('GUI/4829logo.png') # 0: width, 1: height, 2: channels, 3: data
field_width, field_height, field_channels, field_data = dpg.load_image('GUI/field24.png') # 0: width, 1: height, 2: channels, 3: data
robot_width, robot_height, robot_channels, robot_data = dpg.load_image('GUI/robot.png')

field_aspect = field_width / field_height

# Make fonts
with dpg.font_registry():
    default_font = dpg.add_font(file='GUI\ArialCEMTBlack.ttf', size=16)
    clock_font = dpg.add_font(file='GUI\ArialCEMTBlack.ttf', size=150)

    # dpg.bind_font(default_font)

# Load textures intro registry
with dpg.texture_registry():
    dpg.add_static_texture(logo_width, logo_height, logo_data, tag="logo")
    dpg.add_static_texture(field_width, field_height, field_data, tag="field")
    dpg.add_static_texture(robot_width, robot_height, robot_data, tag="robot")


def field_to_canvas(x, y):
    field_meters_width = 16.54175
    field_meters_height = 8.0137 
    normalized_x = (x / field_meters_width) - 0.5
    normalized_y = (y / (field_aspect * field_meters_height)) - (1 / (2 * field_aspect))
    return normalized_x, normalized_y


def path_to_cubic_points(path, curvieness):
    points = []
    for i in range(len(path) - 1):
        start = path[i][0:2]
        end = path[i+1][0:2]
        handle_length = np.sqrt((start[0] - end[0])**2 + (start[1] - end[1])**2) / curvieness
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
def on_networktables_change(source, key, value, isNew):
    global robot_odometry

    # TODO: Figure out a way to stop it from erroring when closing the program when connected

    match (key):
        case "pitch":
            if (open_widgets["orientation"] != None):
                dpg.set_value(item="orientation_pitch_text", value=f"Pitch: {np.round(value, 1)} deg".rjust(18))
                dpg.set_value(item="orientation_pitch_bar", value=(180 + value)/360)
            robot_odometry["pitch"] = value
        case "roll":
            if (open_widgets["orientation"] != None): 
                dpg.set_value(item="orientation_roll_text", value=f"Roll: {np.round(value, 1)} deg".rjust(18))
                dpg.set_value(item="orientation_roll_bar", value=(180 + value)/360)
            robot_odometry["roll"] = value
        case "yaw":
            if (open_widgets["orientation"] != None):
                dpg.set_value(item="orientation_yaw_text", value=f"Yaw: {np.round(value, 1)} deg".rjust(18))
                dpg.set_value(item="orientation_yaw_bar", value=(180 + value)/360)
            robot_odometry["yaw"] = value
        case "position":
            robot_odometry["field_x"] = value[0]
            robot_odometry["field_y"] = value[1]
        case "botPose":
            robot_odometry["field_x"] = value[0]
            robot_odometry["field_y"] = value[1]
        case "canShoot":
            dpg.configure_item(item="can_shoot", show=(value == "true"))
            dpg.configure_item(item="can_shoot", show=(value == "false"))
        case "pathData[0]":
            dpg.configure_item(item="path_detected", show=(value == "true"))
            dpg.configure_item(item="path_detected", show=(value == "false"))
        case "pathData[1]":
            dpg.configure_item(item="red_or_blue", show=(value == "red"))
            dpg.configure_item(item="red_or_blue", show=(value == "blue"))
        case "pathData[2]":
            dpg.configure_item(item="speaker_or_amp", show=(value == "speaker"))
            dpg.configure_item(item="speaker_or_amp", show=(value == "amp"))
        case "limelight_pose":
            limelight_odometry["field_x"] = value[0]
            limelight_odometry["field_y"] = value[1]
            limelight_odometry["pitch"] = value[2]

# Set up theme
def set_theme():
    with dpg.theme() as global_theme:
        with dpg.theme_component(dpg.mvAll):
            dpg.add_theme_style(dpg.mvStyleVar_WindowTitleAlign, 0.5, 0.5, category=dpg.mvThemeCat_Core)
            dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 1, category=dpg.mvThemeCat_Core)
            dpg.add_theme_style(dpg.mvStyleVar_WindowRounding, 8, category=dpg.mvThemeCat_Core)
            dpg.add_theme_style(dpg.mvStyleVar_ScrollbarRounding, 16, category=dpg.mvThemeCat_Core)

            accent1 = (236, 151, 29, 103)
            accent2 = (200, 119, 0, 255)
            accent3 = (135, 86, 15, 255)

            dpg.add_theme_color(dpg.mvThemeCol_FrameBgHovered, accent1, category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_FrameBgActive, accent2, category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_TitleBgActive, accent3, category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_FrameBgActive, accent3, category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_FrameBgHovered, accent3, category=dpg.mvThemeCat_Core)
            
            dpg.add_theme_color(dpg.mvThemeCol_CheckMark, accent2, category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_PlotHistogram, accent2, category=dpg.mvThemeCat_Core)
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

# Makes the auto selector window
def make_auto_selector():
    global open_widgets, chooser_options

    def auto_selector_callback(item):
        control = ChooserControl("SendableChooser[0]", inst=NetworkTablesInstance.getDefault())
        control.setSelected(dpg.get_value(item=item))

    if open_widgets["auto_selector"] is not None:
        dpg.delete_item(open_widgets["auto_selector"])

    with dpg.window(label="Auto Path Selector", no_collapse=True, no_scrollbar=True, width=200, height=100) as auto_selector:
        # Attach auto selector to global widgets

        open_widgets["auto_selector"] = auto_selector
        dpg.add_combo(tag="auto_selector", items=chooser_options, width=-10)

        dpg.set_item_pos(auto_selector, (dpg.get_viewport_width()-(dpg.get_item_width(auto_selector)+20),dpg.get_viewport_height()-(dpg.get_item_height(auto_selector)+380)))

        # Add items
        dpg.add_text(default_value="Select Auto Path")


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

    with dpg.window(label="Robot Orientation", tag="orientation", no_collapse=True, no_scrollbar=True, no_title_bar=False, width=200, height=300) as orientation:
        # Attach orientation to the global widgets
        open_widgets["orientation"] = orientation
        dpg.set_item_pos("orientation", (dpg.get_viewport_width()-(dpg.get_item_width(orientation)+20),0))

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

    with dpg.window(label="Can Shooter Shoot", tag="mode_indicator", no_collapse=True, no_scrollbar=True, no_title_bar=False, width=200, height=100) as indicator:
        # Attach orientation to the global widgets
        open_widgets["mode_indicator"] = indicator
        dpg.set_item_pos(indicator, (dpg.get_viewport_width()-(dpg.get_item_width(indicator)+20),dpg.get_viewport_height()-(dpg.get_item_height(indicator)+180)))

        with dpg.drawlist(width=100, height=100, tag="indicator_drawlist"):
            with dpg.draw_layer(tag="mode_indicator_pass", depth_clipping=False, perspective_divide=True):
                with dpg.draw_node(tag="can_shoot", show=False):
                    dpg.draw_circle(
                        center=(0,0), 
                        radius=(dpg.get_item_height(indicator)/4), 
                        color=(5, 255, 5), 
                        thickness=5, 
                        fill=(5, 94, 5, 50)
                        )
                    
                with dpg.draw_node(tag="can_not_shoot", show=True):
                    dpg.draw_polygon(
                        points=[[-0.4, -0.4], [-0.4, 0.4], [0.4, 0.4], [0.4, -0.4], [-0.4, -0.4], [-0.4, 0.4]],
                        color=(186, 0, 0),
                        fill=(186, 0, 0, 10),
                        thickness=5
                        )

            dpg.set_clip_space("mode_indicator_pass", 0, 0, 100, 100, -5.0, 5.0)

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


def make_path_detection():
    global open_widgets, robot_odometry

    if open_widgets["path_detection"] is not None:
        dpg.delete_item(open_widgets["path_detection"])
        dpg.delete_item(item="path_drawlist")
        dpg.delete_item(item="path_resize_handler")

    with dpg.window(label="Auto Path Detection", tag="path_detection", no_collapse=True, no_scrollbar=True, no_title_bar=False, width=200, height=100) as detection:
        # Attach orientation to the global widgets
        open_widgets["path_detection"] = detection
        dpg.set_item_pos(detection, (dpg.get_viewport_width()-(dpg.get_item_width(detection)+20),dpg.get_viewport_height()-(dpg.get_item_height(detection)+80)))

        with dpg.drawlist(width=100, height=100, tag="path_drawlist"):
            with dpg.draw_layer(tag="path_indicator_pass", depth_clipping=False, perspective_divide=True):
                with dpg.draw_node(tag="path_detected", show=False):
                    dpg.draw_circle(
                        center=(0,0), 
                        radius=25, 
                        color=(5, 255, 5), 
                        thickness=5, 
                        fill=(144, 238, 144, 10)
                        )

                with dpg.draw_node(tag="path_not_detected", show=True):
                    dpg.draw_circle(
                        center=(0,0), 
                        radius=25, 
                        color=(186, 0, 0), 
                        fill=(186, 0, 0, 50),
                        thickness=5, 
                        )

            dpg.set_clip_space("path_indicator_pass", 0, 0, 100, 100, -5.0, 5.0)

    def drawlist_resize(sender, appdata):
        width, height = dpg.get_item_rect_size("path_detection")
        width -= 2 * 8
        height -= 5 * 8
        dpg.configure_item("path_drawlist", width=width, height=height)

        # Drawing space
        drawing_size = min(width, height)
        dpg.set_clip_space(
            item="path_indicator_pass",
            top_left_x=((width - drawing_size) // 2),
            top_left_y=((height - drawing_size) // 2),
            width=drawing_size,
            height=drawing_size,
            min_depth=-5.0,
            max_depth=5.0
        )
    # Make all necessary connections for proper resizing
    with dpg.item_handler_registry(tag="path_detection_resize_handler"):
        dpg.add_item_resize_handler(callback=drawlist_resize)

    dpg.bind_item_handler_registry("path_detection", "path_detection_resize_handler")

# Makes the countdown
def make_round_countdown():
    global open_widgets

    with dpg.window(label="Round Countdown", tag="round_countdown", no_collapse=True, no_scrollbar=True, no_title_bar=False, width=200, height=100) as round_countdown:
        dpg.set_item_pos(round_countdown, (dpg.get_viewport_width()-(dpg.get_item_width(round_countdown)+20),dpg.get_viewport_height()-(dpg.get_item_height(round_countdown)+280)))

        with dpg.drawlist(width=100, height=100, tag="countdown_drawlist"):
            with dpg.draw_layer(tag="countdown_pass", depth_clipping=False, perspective_divide=True):
                dpg.draw_text(pos=(-0.6, 0.5), text="2:45", size=200, tag="round_countdown_text")

        dpg.bind_item_font("round_countdown_text", clock_font)

        dpg.set_clip_space("countdown_pass", 0, 0, 100, 100, -5.0, 5.0)

        def drawlist_resize(sender, appdata):
            width, height = dpg.get_item_rect_size("round_countdown")
            width -= 2 * 8
            height -= 5 * 8
            dpg.configure_item("countdown_drawlist", width=width, height=height)
            dpg.configure_item("round_countdown_text", size=min(width / 2.3, height / 1.2))

            # Drawing space
            drawing_size = min(width, height)
            dpg.set_clip_space(
                item="countdown_pass",
                top_left_x=((width - drawing_size) // 2),
                top_left_y=((height - drawing_size) // 2),
                width=drawing_size,
                height=drawing_size,
                min_depth=-5.0,
                max_depth=5.0
            )

        # Make all necessary connections for proper resizing
        with dpg.item_handler_registry(tag="countdown_resize_handler"):
            dpg.add_item_resize_handler(callback=drawlist_resize)

        dpg.bind_item_handler_registry("round_countdown", "countdown_resize_handler")

# Draws the path and all such points
def draw_path(path_to_place):
    robot_pos = [robot_odometry["field_x"], robot_odometry["field_y"], 0, robot_odometry["yaw"]]

    path_with_current_pos = np.stack((robot_pos, path_to_place))
    
    dpg.delete_item(item="robot_path")
    dpg.delete_item(item="robot_handles")
    dpg.delete_item(item="robot_points")
    bezier_points = path_to_cubic_points(path_with_current_pos, 3)
    with dpg.draw_node(tag="robot_path", parent="field_robot_pass", show=True):
        
        for i in range(int(len(bezier_points) / 4)):
            dpg.draw_bezier_cubic(
                p1=field_to_canvas(bezier_points[(i*4) + 0][0], bezier_points[(i*4) + 0][1]),
                p2=field_to_canvas(bezier_points[(i*4) + 1][0], bezier_points[(i*4) + 1][1]),
                p3=field_to_canvas(bezier_points[(i*4) + 2][0], bezier_points[(i*4) + 2][1]),
                p4=field_to_canvas(bezier_points[(i*4) + 3][0], bezier_points[(i*4) + 3][1]),
                thickness=5,
                color=(155, 155, 255, 200)
            )
            print((bezier_points[(i*4) + 0][0], bezier_points[(i*4) + 0][1]))


            
  
    with dpg.draw_node(tag="robot_handles", parent="field_robot_pass", show=True):
        
        for i in range(int(len(bezier_points) / 4)):
            dpg.draw_circle(center=field_to_canvas(bezier_points[(i*4) + 1][0], bezier_points[(i*4) + 1][1]), radius=5, thickness=4, color=(255, 255, 255), fill=(255, 255, 255))
            dpg.draw_circle(center=field_to_canvas(bezier_points[(i*4) + 2][0], bezier_points[(i*4) + 2][1]), radius=5, thickness=4, color=(255, 255, 255), fill=(255, 255, 255))
            dpg.draw_line(p1=field_to_canvas(bezier_points[(i*4)+0][0], bezier_points[(i*4)+0][1]), p2=field_to_canvas(bezier_points[(i*4)+1][0], bezier_points[(i*4)+1][1]), thickness=3, label="bezier_stuff")
            dpg.draw_line(p1=field_to_canvas(bezier_points[(i*4)+0][0], bezier_points[(i*4)+0][1]), p2=field_to_canvas(bezier_points[(i*4)+3][0], bezier_points[(i*4)+3][1]), thickness=3, label="bezier_stuff")
            dpg.draw_line(p1=field_to_canvas(bezier_points[(i*4)+1][0], bezier_points[(i*4)+1][1]), p2=field_to_canvas(bezier_points[(i*4)+2][0], bezier_points[(i*4)+2][1]), thickness=3, label="bezier_stuff")
            dpg.draw_line(p1=field_to_canvas(bezier_points[(i*4)+2][0], bezier_points[(i*4)+2][1]), p2=field_to_canvas(bezier_points[(i*4)+3][0], bezier_points[(i*4)+3][1]), thickness=3, label="bezier_stuff")
      
        path1 = LineString([[bezier_points[0][0], bezier_points[0][1]], [bezier_points[1][0], bezier_points[1][1]]])
        path2 = LineString([[bezier_points[0][0], bezier_points[0][1]], [bezier_points[2][0], bezier_points[2][1]]])
        path3 = LineString([[bezier_points[0][0], bezier_points[0][1]], [bezier_points[3][0], bezier_points[3][1]]])
        path4 = LineString([[bezier_points[3][0], bezier_points[3][1]], [bezier_points[1][0], bezier_points[1][1]]])
        path5 = LineString([[bezier_points[3][0], bezier_points[3][1]], [bezier_points[2][0], bezier_points[2][1]]])
        path6 = LineString([[bezier_points[2][0], bezier_points[2][1]], [bezier_points[1][0], bezier_points[1][1]]])
        if red_stage_triangle.intersects(path1) == True:
            print('it looks like its working')
        elif red_stage_triangle.intersects(path2) == True:
            print("it looks like its working")
        elif red_stage_triangle.intersects(path3) == True:
            print("it looks like its working")
        elif red_stage_triangle.intersects(path4) == True:
            print("it looks like its working")
        elif red_stage_triangle.intersects(path5) == True:
            print("it looks like its working")
        elif red_stage_triangle.intersects(path6) == True:
            print("it looks like its working")
        else:
            print("Something isn't working, keep trying stuff lol")


    with dpg.draw_node(tag="robot_points", parent="field_robot_pass", show=True):
        for node in path_with_current_pos:
            dpg.draw_circle(
                center=field_to_canvas(*node[0:2]), 
                radius=5, 
                thickness=4,
                color=(255, 255, 255),
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

    global open_widgets, red_amp_cords

    if open_widgets["field_view"] is not None:
        dpg.delete_item(open_widgets["field_view"])
        dpg.delete_item(item="field_drawlist")
        dpg.delete_item(item="field_resize_handler")

    # Make the window
    with dpg.window(label="Field View", tag="field_view", no_collapse=True, no_scrollbar=True, no_title_bar=False, width=1080, height=800) as field_view:
        # Attach field view to the global widgets
        open_widgets["field_view"] = field_view
        dpg.set_item_pos("field_view", (0,0))
        # Make the menu for the window
        with dpg.menu_bar(label="Field Menu", tag="field_menu"):
            with dpg.menu(label="Field Settings"):
                dpg.add_checkbox(label="Flip Field", tag="fs_flip_field")

            with dpg.menu(label="Robot Settings"):
                dpg.add_checkbox(label="Show Robot", tag="rs_show_robot", default_value=True)
                dpg.add_checkbox(label="Show Limelight Estimate", tag="rs_show_limelight", default_value=False)

            with dpg.menu(label="Path Settings"):
                dpg.add_checkbox(label="Show Path", tag="ps_show_path", default_value=False)
                dpg.add_checkbox(label="Show Waypoints", tag="ps_show_waypoints", default_value=False)
                dpg.add_checkbox(label="Show Handles", tag="ps_show_handles", default_value=False)
        
        # Create items
        with dpg.drawlist(width=100, height=100, tag="field_drawlist"):
            dpg.draw_image(texture_tag="field", tag="field_image", pmin=(0, 0), pmax=(field_width, field_height))

            with dpg.draw_layer(tag="field_robot_pass", depth_clipping=False, perspective_divide=True):
                with dpg.draw_node(tag="limelight_robot", show=False):
                    dpg.draw_polygon(robot_vertices, thickness=3, color=(14, 200, 14, 50), fill=(200, 255, 200, 10))
                    dpg.draw_polygon(arrow_vertices, thickness=3, color=(14, 255, 14, 50), fill=(15, 200, 15, 50))

                with dpg.draw_node(tag="field_robot", show=True):
                    dpg.draw_polygon(robot_vertices, thickness=3, color=(255, 94, 5), fill=(255, 94, 5, 10))
                    dpg.draw_polygon(arrow_vertices, thickness=3, color=(255, 94, 5), fill=(255, 94, 5))
            dpg.set_clip_space("field_robot_pass", 0, 0, 100, 100, -5.0, 5.0)
            dpg.draw_triangle((blue_middle_waypoint_x, blue_middle_waypoint_y), (blue_upper_waypoint_x, blue_upper_waypoint_y),(blue_lower_waypoint_x, blue_lower_waypoint_y), tag="blue_stage", thickness=2, color=(255, 255, 255))
            dpg.draw_triangle((red_middle_waypoint_x, red_middle_waypoint_y), (red_upper_waypoint_x, red_upper_waypoint_y),(red_lower_waypoint_x, red_lower_waypoint_y), tag="red_stage", thickness=2, color=(255, 255, 255))
  
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
        "rs_show_limelight",
        callback=lambda x: dpg.configure_item("limelight_robot", show=dpg.get_value(x))
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

    limelight_pitch = limelight_odometry["pitch"] * np.pi / 180
    limelight_x, limelight_y = field_to_canvas(limelight_odometry["field_x"], limelight_odometry["field_y"])

    # Orientation
    if open_widgets["orientation"] is not None:
        view = dpg.create_fps_matrix([0, 20, 10], pitch=(np.pi / 3), yaw=(np.pi))
        proj = dpg.create_perspective_matrix(90.0 * (np.pi / 180.0), 1.0, 0.1, 100)
        orientation_3d = dpg.create_rotation_matrix(-np.pi / 4, [0, 0, 1])

        # Always make sure Y is first otherwise there's gonna be some serious problems
        robot_rotation = dpg.create_rotation_matrix(np.pi / 2 - pitch, [0, 0, 1]) * \
                            dpg.create_rotation_matrix(yaw, [0, 1, 0]) * \
                            dpg.create_rotation_matrix(roll, [1, 0, 0])
        dpg.apply_transform("robot_3d", proj*view*orientation_3d*robot_rotation)
        dpg.apply_transform("grid_3d", proj*view*orientation_3d)
        dpg.apply_transform("axis_3d", proj*view*orientation_3d)

    # Field View
    if open_widgets["field_view"] is not None:
        field_scale = dpg.create_scale_matrix([1, field_aspect])
        field_rotation = dpg.create_rotation_matrix(np.pi / 2 - pitch, [0, 0, -1])
        field_position = dpg.create_translation_matrix([x, y])

        limelight_scale = dpg.create_scale_matrix([1, field_aspect])
        limelight_rotation = dpg.create_rotation_matrix(np.pi / 2 - limelight_pitch, [0, 0, -1])
        limelight_position = dpg.create_translation_matrix([limelight_x, limelight_y])
        
        dpg.apply_transform("field_robot", field_scale*field_position*field_rotation)
        dpg.apply_transform("limelight_robot", limelight_scale*limelight_position*limelight_rotation)

        if("path_detected" == "true"):
            if ("red_or_blue" == "red") & ("speaker_or_amp" == "speaker"):
                draw_path(red_speaker_cords)
            elif("red_or_blue" == "red") & ("speaker_or_amp" == "speaker"):
                draw_path(red_amp_cords)
            if ("red_or_blue" == "blue") & ("speaker_or_amp" == "amp"):
                draw_path(blue_speaker_cords)
            elif("red_or_blue" == "blue") & ("speaker_or_amp" == "amp"):
                draw_path(blue_amp_cords)

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

    table_instance.addEntryListener(on_networktables_change)

def sample_path():
    draw_path(blue_amp_cords)

def main():
    # Create the menu bar
    with dpg.viewport_menu_bar(label="Menu", tag="menu"):
        with dpg.menu(label="Settings"):
            dpg.add_menu_item(label="Enable Something")
        with dpg.menu(label="Widgets"):
            dpg.add_menu_item(label="Field View", callback=make_field_view)
            dpg.add_menu_item(label="Orientation", callback=make_orientation)
            dpg.add_menu_item(label="Auto Selector", callback=make_auto_selector)
            dpg.add_menu_item(label="Mode Indicator", callback=make_mode_indicator)
            dpg.add_menu_item(label="Path Detection", callback=make_path_detection)
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
    make_auto_selector()
    make_field_view()
    make_round_countdown()
    make_mode_indicator()
    make_path_detection()
    make_orientation()


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
