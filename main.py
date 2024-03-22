from networktables.util import ChooserControl
from networktables import NetworkTables
from networktables import NetworkTablesInstance
import dearpygui.dearpygui as dpg
import numpy as np
from scipy.special import comb
import re
import threading
import logging
import time
from loadmatchdata import get_match_data
# Initialization
dpg.create_context()
dpg.configure_app(docking=True, docking_space=True)
dpg.create_viewport(title="4829 SmarterDashboard", width=1300, height=800)

# Create a global dictionary to store if windows are already open
open_widgets = {
    "field_view": None,
    "replay_view": None,
    "countdown": None,
    "orientation": None,
    "auto_selector": None,
    "mode_indicator": None,
    "note_loaded": None,
    "auto_note_selector": None,
}
# Global variable to see if it's connected
connection_status = False
# Global chooser options
chooser_options = []

upper_blue_waypoint = [4, 9.5, 0, 180]
lower_blue_waypoint = [4, -1, 0, 180]
upper_red_waypoint = [12.5, 9.5, 0, 0]
lower_red_waypoint = [12.5, -1, 0, 0]

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

def field_x_to_canvas_x(x):
    field_meters_width = 16.54175
    normalized_x = (x / field_meters_width) - 0.5
    return normalized_x

def field_y_to_canvas_y(y):
    field_meters_height = 8.0137 
    normalized_y = (y / (field_aspect * field_meters_height)) - (1 / (2 * field_aspect))
    return normalized_y





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

    points = [[start[0], start[1]],
              [start_handle[0], start_handle[1]],
              [end_handle[0], end_handle[1]],
              [end[0], end[1]]
              ]
    return points

#bernstein polynomial of nth degree, i as a function of t
def bernstein_poly(i, degree, listOfPointsAcrossCurve):
    # print(comb(degree, i))
    print(comb(degree, i))
    return comb(degree, i) * ( listOfPointsAcrossCurve**(degree-i) ) * (1 - listOfPointsAcrossCurve)**i

# returns a rough list of points along the bezier curve
def bezier_curve(points, nTimes=100):

    nPoints = len(points)
    # print(nPoints)
    xPoints = np.array([p[0] for p in points])
    yPoints = np.array([p[1] for p in points])
    # print(xPoints[0], yPoints[0], "xpoints, ypoints")
    listOfPointsAcrossCurve = np.linspace(0.0, 1.0, nTimes)
    polynomial_array = np.array([ bernstein_poly(i, nPoints-1, listOfPointsAcrossCurve) for i in range(0, nPoints)   ])
    # print(polynomial_array)
    xvals = np.dot(xPoints, polynomial_array)
    yvals = np.dot(yPoints, polynomial_array)
    print(xvals[0], yvals[0])
    return xvals, yvals



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
        case "screwed":
            dpg.configure_item(item="can_shoot", show=(value != "true"))
            dpg.configure_item(item="can_shoot", show=(value != "false"))
            dpg.configure_item(item="can_not_shoot", show=(value == "true"))
            dpg.configure_item(item="can_not_shoot", show=(value == "false"))
        # case "pathData[0]":
        #     dpg.configure_item(item="path_detected", show=(value == "true"))
        #     dpg.configure_item(item="path_detected", show=(value == "false"))
        # case "pathData[1]":
        #     dpg.configure_item(item="red_or_blue", show=(value == "red"))
        #     dpg.configure_item(item="red_or_blue", show=(value == "blue"))
        # case "pathData[2]":
        #     dpg.configure_item(item="speaker_or_amp", show=(value == "speaker"))
        #     dpg.configure_item(item="speaker_or_amp", show=(value == "amp"))
        case "limelight_pose":
            limelight_odometry["field_x"] = value[0]
            limelight_odometry["field_y"] = value[1]
            limelight_odometry["pitch"] = value[2]
        case "ampedTimeLeft":
            dpg.configure_item(item="countdown_progress_bar", value=(value/10))
        case "notePos":
            dpg.configure_item(item="note_in_robot", show=(value != "0"))
            dpg.configure_item(item="note_not_in_robot", show=(value != "0"))
            dpg.configure_item(item="note_partly_in_robot", show=(value == "0"))
            dpg.configure_item(item="note_in_robot", show=(value != "1"))
            dpg.configure_item(item="note_not_in_robot", show=(value == "1"))
            dpg.configure_item(item="note_partly_in_robot", show=(value != "1"))
            dpg.configure_item(item="note_in_robot", show=(value == "2"))
            dpg.configure_item(item="note_not_in_robot", show=(value != "2"))
            dpg.configure_item(item="note_partly_in_robot", show=(value != "2"))


            
            
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

    with dpg.window(label="Screwed", tag="mode_indicator", no_collapse=True, no_scrollbar=True, no_title_bar=False, width=200, height=150) as indicator:
        # Attach orientation to the global widgets
        open_widgets["mode_indicator"] = indicator
        dpg.set_item_pos(indicator, (dpg.get_viewport_width()-(dpg.get_item_width(indicator)+20),dpg.get_viewport_height()-(dpg.get_item_height(indicator)+230)))

        with dpg.drawlist(width=100, height=100, tag="indicator_drawlist"):
            with dpg.draw_layer(tag="mode_indicator_pass", depth_clipping=False, perspective_divide=True):
                with dpg.draw_node(tag="can_shoot", show=False):
                    dpg.draw_polygon(
                        points=[[-0.4, -0.4], [-0.4, 0.4], [0.4, 0.4], [0.4, -0.4], [-0.4, -0.4], [-0.4, 0.4]],
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


def make_note_in_robot():
    global open_widgets, robot_odometry

    if open_widgets["note_loaded"] is not None:
        dpg.delete_item(open_widgets["note_loaded"])
        dpg.delete_item(item="path_drawlist")
        dpg.delete_item(item="path_resize_handler")

    with dpg.window(label="Note in Robot", tag="note_loaded", no_collapse=True, no_scrollbar=True, no_title_bar=False, width=200, height=150) as detection:
        # Attach orientation to the global widgets
        open_widgets["note_loaded"] = detection
        dpg.set_item_pos(detection, (dpg.get_viewport_width()-(dpg.get_item_width(detection)+20),dpg.get_viewport_height()-(dpg.get_item_height(detection)+80)))

        with dpg.drawlist(width=200, height=150, tag="path_drawlist"):
            with dpg.draw_layer(tag="path_indicator_pass", depth_clipping=False, perspective_divide=True):

                with dpg.draw_node(tag="note_not_in_robot", show=True):
                    dpg.draw_circle(
                        center=(0,0), 
                        radius=(dpg.get_item_width(detection)/4), 
                        color=(186, 0, 0), 
                        fill=(186, 0, 0, 50),
                        thickness=5, 
                        )
                with dpg.draw_node(tag="note_partly_in_robot", show=False):
                    dpg.draw_circle(
                        center=(0,0), 
                        radius=(dpg.get_item_width(detection)/4), 
                        color=(252, 186, 3), 
                        fill=(252, 186, 3, 50),
                        thickness=5, 
                        )
                with dpg.draw_node(tag="note_in_robot", show=False):
                    dpg.draw_circle(
                        center=(0, 0), 
                        radius=(dpg.get_item_width(detection)/4), 
                        color=(5, 255, 5), 
                        thickness=5, 
                        fill=(144, 238, 144, 50)
                        )

            dpg.set_clip_space("path_indicator_pass", 0, 0, 100, 100, -5.0, 5.0)

    def drawlist_resize(sender, appdata):
        width, height = dpg.get_item_rect_size("note_loaded")
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
    with dpg.item_handler_registry(tag="note_in_robot_resize_handler"):
        dpg.add_item_resize_handler(callback=drawlist_resize)

    dpg.bind_item_handler_registry("note_loaded", "note_in_robot_resize_handler")

# Makes the countdown
def make_amp_countdown():
    global open_widgets, robot_odometry

    if open_widgets["countdown"] is not None:
        dpg.delete_item(open_widgets["countdown"])
        dpg.delete_item(item="countdown_drawlist")
        dpg.delete_item(item="countdown_resize_handler")

    with dpg.window(label="Countdown", tag="countdown", no_collapse=True, no_scrollbar=True, no_title_bar=False, width=1080, height=20) as amp_countdown:
        dpg.set_item_pos(amp_countdown, (0, 0))

        dpg.add_progress_bar(tag="countdown_progress_bar", label="Countdown", default_value=0.0, width=-1, height=-1)


        def drawlist_resize(sender, appdata):
            width, height = dpg.get_item_rect_size("amp_countdown")
            width -= 2 * 8
            height -= 5 * 8
            dpg.configure_item("countdown_drawlist", width=width, height=height)
            dpg.configure_item("amp_countdown_text", size=min(width / 2.3, height / 1.2))

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

        dpg.bind_item_handler_registry("countdown", "countdown_resize_handler")



# creates the path based on the robot pose and the stuff to fix it
def create_path(path_to_place):

    robot_pos = [robot_odometry["field_x"], robot_odometry["field_y"], 0, robot_odometry["yaw"]]
    print(robot_pos)

    if path_to_place[0] >= 10:
        
        if robot_odometry["field_x"] >= 12:
                middle_waypoint = []
        else:
            if robot_odometry["field_y"] <= 3:
                middle_waypoint = lower_red_waypoint
            else:
                middle_waypoint = upper_red_waypoint
    else:

        if robot_odometry["field_x"] <= 3:
                middle_waypoint = []
        else:
            if robot_odometry["field_y"] <= 3:
                middle_waypoint = lower_blue_waypoint      
            else:
                middle_waypoint = upper_blue_waypoint      

    # do this if no waypoint is needed
    if middle_waypoint == []:
        curve = np.stack((robot_pos, path_to_place))
        cubic_points = path_to_cubic_points(curve, 3)
        bezier_points = []
        for i in range(len(cubic_points)):
            bezier_points.append(cubic_points[i-1])
        xvals, yvals = bezier_curve(cubic_points, nTimes=100)
        return(xvals, yvals, [0], [0], bezier_points, [0])

    
    # do this if waypoint is needed
    first_part = np.stack((robot_pos, middle_waypoint))
    second_part = np.stack((middle_waypoint, path_to_place))
    first_spline_cubic_points = path_to_cubic_points(first_part, 3)
    second_spline_cubic_points = path_to_cubic_points(second_part, 3)
    bezier_points = []
    second_bezier_points = []

    for i in range(len(first_spline_cubic_points)):
         bezier_points.append(first_spline_cubic_points[i-1])

    for i in range(len(second_spline_cubic_points)):
         second_bezier_points.append(second_spline_cubic_points[i-1])

    xvals_second, yvals_second = bezier_curve(second_spline_cubic_points, nTimes=100)
    xvals, yvals = bezier_curve(first_spline_cubic_points, nTimes=100)
    # print(xvals[0], yvals[0])
    return(xvals, yvals, xvals_second, yvals_second, bezier_points, second_bezier_points)








# Draws the path and all such points

def draw_path(path_to_place):

    xvals, yvals, xvals_second, yvals_second, bezier_points, second_bezier_points = create_path(path_to_place)
    
    dpg.delete_item(item="robot_path")
    dpg.delete_item(item="robot_handles")
    dpg.delete_item(item="robot_bezier_points")

    with dpg.draw_node(tag="robot_path", parent="field_robot_pass", show=True):
        for i in range(len(xvals)):
            dpg.draw_circle((field_x_to_canvas_x(xvals[i-1]), field_y_to_canvas_y(yvals[i-1])), 4, color=(155, 155, 255), fill=(155, 155, 255, 200))
        if xvals_second[0] != 0:
            for i in range(len(xvals_second)):
                dpg.draw_circle((field_x_to_canvas_x(xvals_second[i-1]), field_y_to_canvas_y(yvals_second[i-1])), 4, color=(155, 155, 255), fill=(155, 155, 255, 200))
  
  

    with dpg.draw_node(tag="robot_bezier_points", parent="field_robot_pass", show=True):
        # draws the robot nodes
        dpg.draw_circle(center=field_to_canvas(bezier_points[3][0], bezier_points[3][1]), radius=5, thickness=4, color=(255, 255, 255), fill=(255, 255, 255))
        dpg.draw_circle(center=field_to_canvas(bezier_points[2][0], bezier_points[2][1]), radius=5, thickness=4, color=(255, 255, 255), fill=(255, 255, 255))
        dpg.draw_circle(center=field_to_canvas(bezier_points[1][0], bezier_points[1][1]), radius=5, thickness=4, color=(255, 255, 255), fill=(255, 255, 255))
        dpg.draw_circle(center=field_to_canvas(bezier_points[0][0], bezier_points[0][1]), radius=5, thickness=4, color=(255, 255, 255), fill=(255, 255, 255))
       
        # draws the lines between the handles
        dpg.draw_line(p1=field_to_canvas(bezier_points[0][0], bezier_points[0][1]), p2=field_to_canvas(bezier_points[3][0], bezier_points[3][1]), thickness=3, color=(255, 255, 255), label="bezier_stuff")
        dpg.draw_line(p1=field_to_canvas(bezier_points[3][0], bezier_points[3][1]), p2=field_to_canvas(bezier_points[2][0], bezier_points[2][1]), thickness=3, color=(255, 255, 255), label="bezier_stuff")
        dpg.draw_line(p1=field_to_canvas(bezier_points[2][0], bezier_points[2][1]), p2=field_to_canvas(bezier_points[1][0], bezier_points[1][1]), thickness=3, color=(255, 255, 255), label="bezier_stuff")
 
        if xvals_second[0] != 0:
            dpg.draw_circle(center=field_to_canvas(second_bezier_points[3][0], second_bezier_points[3][1]), radius=5, thickness=4, color=(255, 255, 255), fill=(255, 255, 255))
            dpg.draw_circle(center=field_to_canvas(second_bezier_points[2][0], second_bezier_points[2][1]), radius=5, thickness=4, color=(255, 255, 255), fill=(255, 255, 255))
            dpg.draw_circle(center=field_to_canvas(second_bezier_points[1][0], second_bezier_points[1][1]), radius=5, thickness=4, color=(255, 255, 255), fill=(255, 255, 255))
            dpg.draw_circle(center=field_to_canvas(second_bezier_points[0][0], second_bezier_points[0][1]), radius=5, thickness=4, color=(255, 255, 255), fill=(255, 255, 255))
       
            # draws the lines between the handles
            dpg.draw_line(p1=field_to_canvas(second_bezier_points[0][0], second_bezier_points[0][1]), p2=field_to_canvas(second_bezier_points[3][0], second_bezier_points[3][1]), thickness=3, color=(255, 255, 255), label="bezier_stuff")
            dpg.draw_line(p1=field_to_canvas(second_bezier_points[3][0], second_bezier_points[3][1]), p2=field_to_canvas(second_bezier_points[2][0], second_bezier_points[2][1]), thickness=3, color=(255, 255, 255), label="bezier_stuff")
            dpg.draw_line(p1=field_to_canvas(second_bezier_points[2][0], second_bezier_points[2][1]), p2=field_to_canvas(second_bezier_points[1][0], second_bezier_points[1][1]), thickness=3, color=(255, 255, 255), label="bezier_stuff")
       

# makes the auto note selector
def make_auto_note_selector():
    note_choices = []


    if open_widgets["auto_note_selector"] is not None:
        dpg.delete_item(open_widgets["auto_note_selector"])
        dpg.delete_item(item="field_drawlist")
        dpg.delete_item(item="field_resize_handler")

    with dpg.window(label="Auto Note Selector", tag="auto_note_selector", no_collapse=True, no_scrollbar=True, no_title_bar=False, width=1080, height=800) as auto_note_selector:
        # Attach field view to the global widgets
        open_widgets["auto_note_selector"] = auto_note_selector    
        dpg.set_item_pos("auto_note_selector", (0,0))
        # Make the menu for the window
        with dpg.menu_bar(label="Field Menu", tag="auto_note_selector"):
            with dpg.menu(label="Field Settings"):
                dpg.add_checkbox(label="Flip Field", tag="fs_flip_field")

        with dpg.drawlist(width=100, height=100, tag="auto_drawlist"):
            dpg.draw_image(texture_tag="field", tag="field_image", pmin=(0, 0), pmax=(field_width, field_height))
   
   
def load_match_data():
    global  pose_data
    pose_data = get_match_data()
    print(pose_data)
    return ( pose_data)

def make_replay_view():
    robot_width = 0.03
    robot_height = 0.03
    pose_data = load_match_data()
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

    global open_widgets, input_value
    
    if open_widgets["replay_view"] is not None:
        
        
        dpg.delete_item(open_widgets["replay_view"])
        dpg.delete_item(item="replay_drawlist")
        dpg.delete_item(item="replay_resize_handler")
        

    # Make the window
    with dpg.window(label="Replay View", tag="replay_view", no_collapse=True, no_scrollbar=True, no_title_bar=False, width=1080, height=800) as replay_view:
        # Attach replay view to the global widgets
        open_widgets["replay_view"] = replay_view
        dpg.set_item_pos("replay_view", (0,0))
        # Make the menu for the window
        with dpg.menu_bar(label="Replay Menu", tag="replay_menu"):
            with dpg.menu(label="Replay Settings"):
                dpg.add_checkbox(label="Flip Replay", tag="fs_flip_replay")
           

            with dpg.menu(label="Robot Settings"):
                dpg.add_checkbox(label="Show Robot", tag="rs_show_robot", default_value=True)
                dpg.add_checkbox(label="Show Limelight Estimate", tag="rs_show_limelight", default_value=False)
        input_value = dpg.add_slider_int(width=1065, height=10, max_value=len(pose_data), clamped=True)
        # Create items
        with dpg.drawlist(width=100, height=100, tag="replay_drawlist"):
            dpg.draw_image(texture_tag="field", tag="replay_image", pmin=(0, 0), pmax=(field_width, field_height))

            with dpg.draw_layer(tag="replay_robot_pass", depth_clipping=False, perspective_divide=True):
                with dpg.draw_node(tag="replay_robot", show=True):
                    dpg.draw_polygon(robot_vertices, thickness=3, color=(255, 94, 5), fill=(255, 94, 5, 10))
                    dpg.draw_polygon(arrow_vertices, thickness=3, color=(255, 94, 5), fill=(255, 94, 5))
               
            dpg.set_clip_space("replay_robot_pass", 0, 0, 100, 100, -5.0, 5.0)

    # Make all necessary callback functions
    def drawlist_resize(sender, appdata):
        width, height = dpg.get_item_rect_size("replay_view")
        # Annoying hack to get things sizing properly
        width -= 2 * 8
        height -= 7 * 8
        dpg.configure_item("replay_drawlist", width=width, height=height)

        # Dynamic replay image resizing and positioning
        new_replay_width = width
        new_replay_height = height
        if (new_replay_width > new_replay_height * field_aspect):
            new_replay_width = height * field_aspect

        elif (new_replay_width < new_replay_height * field_aspect):
            new_replay_height = width * (1 / field_aspect)

        replay_min = [(width - new_replay_width) // 2, (height - new_replay_height) // 2]
        replay_max = [replay_min[0] + new_replay_width, replay_min[1] + new_replay_height]

        if (dpg.get_value("fs_flip_replay")):
            tmp = replay_min[0]
            replay_min[0] = replay_max[0]
            replay_max[0] = tmp

        dpg.configure_item("replay_image", pmin=replay_min, pmax=replay_max)

        # Configure the clip space for the robot
        dpg.set_clip_space(
            item="replay_robot_pass", 
            top_left_x=((width - new_replay_width) // 2), 
            top_left_y=((height - new_replay_height) // 2), 
            width=new_replay_width, 
            height=new_replay_height,
            min_depth=-1.0,
            max_depth=1.0
        )

    # Make all necessary connections for settings to work
    dpg.set_item_callback("fs_flip_replay", callback=drawlist_resize)
    dpg.set_item_callback(
        "build_auto",
        callback=lambda x: dpg.configure_item("auto_builder", show=dpg.get_value(x))
    )
    dpg.set_item_callback(
        "rs_show_robot",
        callback=lambda x: dpg.configure_item("replay_robot", show=dpg.get_value(x))
    )
  



    # Make all necessary connections for proper resizing
    with dpg.item_handler_registry(tag="replay_resize_handler"):
        dpg.add_item_resize_handler(callback=drawlist_resize)

    dpg.bind_item_handler_registry("replay_view", "replay_resize_handler")
        



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

    global open_widgets

    if open_widgets["field_view"] is not None:
        dpg.delete_item(open_widgets["field_view"])
        dpg.delete_item(item="field_drawlist")
        dpg.delete_item(item="field_resize_handler")

    # Make the window
    with dpg.window(label="Field View", tag="field_view", no_collapse=True, no_scrollbar=True, no_title_bar=False, width=1080, height=600) as field_view:
        # Attach field view to the global widgets
        open_widgets["field_view"] = field_view
        dpg.set_item_pos("field_view", (0, 120))
        # Make the menu for the window
        with dpg.menu_bar(label="Field Menu", tag="field_menu"):
            with dpg.menu(label="Field Settings"):
                dpg.add_checkbox(label="Flip Field", tag="fs_flip_field")
           
            with dpg.menu(label="Auto Builder"):
                dpg.add_checkbox(label="Build Auto", tag="build_auto", default_value=False)

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
               
                with dpg.draw_node(tag="auto_builder", show=False):
                    dpg.draw_circle((field_x_to_canvas_x(2.89), field_y_to_canvas_y(4)), radius=10, thickness=2, color=(255, 255, 255), fill=(255, 255, 255, 100), tag="blue_note_1")
                    dpg.draw_circle((field_x_to_canvas_x(2.89), field_y_to_canvas_y(6.85)), radius=10, thickness=2, color=(255, 255, 255), fill=(255, 255, 255, 100), tag="blue_note_2")
                    dpg.draw_circle((field_x_to_canvas_x(2.89), field_y_to_canvas_y(9.7)), radius=10, thickness=2, color=(255, 255, 255), fill=(255, 255, 255, 100), tag="blue_note_3")
                    
                    dpg.draw_circle((field_x_to_canvas_x(13.66), field_y_to_canvas_y(4)), radius=10, thickness=2, color=(255, 255, 255), fill=(255, 255, 255, 100), tag="red_note_1")
                    dpg.draw_circle((field_x_to_canvas_x(13.66), field_y_to_canvas_y(6.85)), radius=10, thickness=2, color=(255, 255, 255), fill=(255, 255, 255, 100), tag="red_note_2")
                    dpg.draw_circle((field_x_to_canvas_x(13.66), field_y_to_canvas_y(9.7)), radius=10, thickness=2, color=(255, 255, 255), fill=(255, 255, 255, 100), tag="red_note_3")

                    dpg.draw_circle((field_x_to_canvas_x(8.28), field_y_to_canvas_y(10.55)), radius=10, thickness=2, color=(255, 255, 255), fill=(255, 255, 255, 100), tag="note_4")
                    dpg.draw_circle((field_x_to_canvas_x(8.28), field_y_to_canvas_y(7.3)), radius=10, thickness=2, color=(255, 255, 255), fill=(255, 255, 255, 100), tag="note_5")
                    dpg.draw_circle((field_x_to_canvas_x(8.28), field_y_to_canvas_y(4)), radius=10, thickness=2, color=(255, 255, 255), fill=(255, 255, 255, 100), tag="note_6")
                    dpg.draw_circle((field_x_to_canvas_x(8.28), field_y_to_canvas_y(0.7)), radius=10, thickness=2, color=(255, 255, 255), fill=(255, 255, 255, 100), tag="note_7")
                    dpg.draw_circle((field_x_to_canvas_x(8.28), field_y_to_canvas_y(-2.55)), radius=10, thickness=2, color=(255, 255, 255), fill=(255, 255, 255, 100), tag="note_8")

   
            dpg.set_clip_space("field_robot_pass", 0, 0, 100, 100, -5.0, 5.0)

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
        "build_auto",
        callback=lambda x: dpg.configure_item("auto_builder", show=dpg.get_value(x))
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
 
    if open_widgets["replay_view"] is not None:
       
        #I HATE STRING PARSING
        current_pose_entry = dpg.get_value(input_value)
        current_pose_x = pose_data.iat[(current_pose_entry -1), 2].strip("Pose2d(Translation2d(X: ").split(";", 1)
        current_pose_y = current_pose_x[1].strip("Y: ").split(");", 1)
        current_pose_rads = current_pose_y[1].strip("Rotation2d(Rads: ").split(";", 1) # i really hate string parsing this variable serves no purpose
        current_pose_degrees = current_pose_rads[1].strip("Deg: ").split("))", 1)
        
        replay_x, replay_y,  = field_to_canvas(float(current_pose_x[0]), float(current_pose_y[0]))
        replay_pitch = float(current_pose_degrees[0])
        replay_rotation = dpg.create_rotation_matrix(np.pi / 2 - replay_pitch, [0, 0, -1])
        replay_position = dpg.create_translation_matrix([replay_x, replay_y])
        replay_scale = dpg.create_scale_matrix([1, field_aspect])

        dpg.apply_transform("replay_robot", replay_scale*replay_position*replay_rotation)

    


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


def red_speaker_path():
    draw_path(red_speaker_cords)
def blue_speaker_path():
    draw_path(blue_speaker_cords)
def red_amp_path():
    draw_path(red_amp_cords)
def blue_amp_path():
    draw_path(blue_amp_cords)

def main():
    # Create the menu bar
    with dpg.viewport_menu_bar(label="Menu", tag="menu"):
        with dpg.menu(label="Settings"):
            dpg.add_menu_item(label="Enable Something")
        with dpg.menu(label="Widgets"):
            dpg.add_menu_item(label="Field View", callback=make_field_view)
            dpg.add_menu_item(label="Replay", callback=make_replay_view)
            dpg.add_menu_item(label="Orientation", callback=make_orientation)
            dpg.add_menu_item(label="Auto Selector", callback=make_auto_selector)
            dpg.add_menu_item(label="Mode Indicator", callback=make_mode_indicator)
            dpg.add_menu_item(label="Path Detection", callback=make_note_in_robot)
        with dpg.menu(label="Override"):
            dpg.add_button(
                label="Attempt Reconnect", 
                callback=lambda _: threading.Thread(target=connect_table_and_listeners, daemon=True).start()
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
    make_amp_countdown()
    make_mode_indicator()
    make_note_in_robot()
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



