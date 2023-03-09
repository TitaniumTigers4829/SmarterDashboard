from networktables import NetworkTables
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
}
# Global variable to see if it's connected
connection_status = False

# Fetch textures (should be a function)
logo_width, logo_height, logo_channels, logo_data = dpg.load_image('GUI/4829logo.png') # 0: width, 1: height, 2: channels, 3: data
field_width, field_height, field_channels, field_data = dpg.load_image('GUI/gamefield.png') # 0: width, 1: height, 2: channels, 3: data
robot_width, robot_height, robot_channels, robot_data = dpg.load_image('GUI/robot.png')

field_aspect = field_width / field_height

# Load textures intro registry
with dpg.texture_registry():
    dpg.add_static_texture(logo_width, logo_height, logo_data, tag="logo")
    dpg.add_static_texture(field_width, field_height, field_data, tag="field")
    dpg.add_static_texture(robot_width, robot_height, robot_data, tag="robot")

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
    options = ["Auto Path 1", "Auto Path 2", "Auto Path 3"]

    global open_widgets
    if open_widgets["auto_selector"] is not None:
        dpg.delete_item(open_widgets["auto_selector"])

    with dpg.window(label="Auto Path Selector") as auto_selector:
        # Attach auto selector to global widgets
        open_widgets["auto_selector"] = auto_selector

        # Add items
        dpg.add_text(default_value="Select Auto Path")
        dpg.add_combo(tag="auto_selector", items=options, width=-1)

    # Attach necessary callbacks
    dpg.set_item_callback("auto_selector", lambda _: print("Something here about sending the path and showing it on the field view"))

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

    global open_widgets
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
            dpg.add_text(default_value="Pitch: {} deg")
            dpg.add_progress_bar(label="Pitch", width=-1, default_value=0.5)
        with dpg.group(horizontal=True):
            dpg.add_text(default_value="Roll:  {} deg")
            dpg.add_progress_bar(label="Roll", width=-1, default_value=0.5)
        with dpg.group(horizontal=True):
            dpg.add_text(default_value="Yaw:   {} deg")
            dpg.add_progress_bar(label="Yaw", width=-1, default_value=0.5)

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
                dpg.add_checkbox(label="Show Path", default_value=True)
                dpg.add_checkbox(label="Show Waypoints", default_value=True)
                dpg.add_checkbox(label="Show Handles", default_value=False)
                dpg.add_slider_double(label="Path Opacity", default_value=1, min_value=0, max_value=1, width=50)
        
        # Create items
        with dpg.drawlist(width=100, height=100, tag="field_drawlist"):
            dpg.draw_image(texture_tag="field", tag="field_image", pmin=(0, 0), pmax=(field_width, field_height))

            with dpg.draw_layer(tag="field_robot_pass", depth_clipping=False, perspective_divide=True):
                with dpg.draw_node(tag="field_robot"):
                    dpg.draw_polygon(arrow_vertices, thickness=3, color=(255, 100, 0), fill=(255, 100, 0))
                    dpg.draw_polygon(robot_vertices, thickness=3, fill=(255, 255, 255, 10))

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
        "rs_show_robot",
        callback=lambda x: dpg.configure_item("field_robot", show=dpg.get_value(x))
    )

    # Make all necessary connections for proper resizing
    with dpg.item_handler_registry(tag="field_resize_handler"):
        dpg.add_item_resize_handler(callback=drawlist_resize)

    dpg.bind_item_handler_registry("field_view", "field_resize_handler")

# Update for whenever the frame is drawn
def draw_call_update():
    # Orientation
    if open_widgets["orientation"] is not None:
        view = dpg.create_fps_matrix([0, 20, 10], pitch=(np.pi / 3), yaw=(np.pi))
        proj = dpg.create_perspective_matrix(90.0 * (np.pi / 180.0), 1.0, 0.1, 100)
        orientation_3d = dpg.create_rotation_matrix(-np.pi / 4, [0, 0, 1])

        test_pitch = (time.time()) % (2 * np.pi)
        test_roll = np.sin(time.time() * 3) / 5
        # Always make sure Y is first otherwise there's gonna be some serious problems
        robot_rotation = dpg.create_rotation_matrix(test_pitch, [0, 0, 1]) * \
                            dpg.create_rotation_matrix(test_roll, [0, 1, 0])
        dpg.apply_transform("robot_3d", proj*view*orientation_3d*robot_rotation)
        dpg.apply_transform("grid_3d", proj*view*orientation_3d)
        dpg.apply_transform("axis_3d", proj*view*orientation_3d)

    # Field View
    if open_widgets["field_view"] is not None:
        field_scale = dpg.create_scale_matrix([1, field_aspect])
        test_field_rotation = dpg.create_rotation_matrix((time.time()) % (2 * np.pi), [0, 0, -1])
        test_field_position = dpg.create_translation_matrix([np.cos(time.time()) * 0.1, np.sin(time.time()) * 0.1])
        dpg.apply_transform("field_robot", field_scale*test_field_position*test_field_rotation)

# Target thread to make some connections
def connect_table_and_listeners(timeout=5):
    connected = False

    NetworkTables.addConnectionListener(
        listener=lambda connected, info: print(f"Connected: {connected}\nInfo: {info}"),
        immediateNotify=True
    )

    # Some kind of waiting routine
    start = time.time()
    while (not connected) and ((time.time() - start) < timeout):
        pass

    # Add a bunch of these to the right values assuming they exist
    # NetworkTables.addEntryListener()

def main():
    # Networktables Setup
    logging.basicConfig(level=logging.DEBUG)
    NetworkTables.startClientTeam(4829)


    # Create the menu bar
    with dpg.viewport_menu_bar(label="Menu", tag="menu"):
        with dpg.menu(label="Settings"):
            dpg.add_menu_item(label="Enable Something")
        with dpg.menu(label="Widgets"):
            dpg.add_menu_item(label="Field View", callback=make_field_view)
            dpg.add_menu_item(label="Grid View", callback=make_grid_view)
            dpg.add_menu_item(label="Orientation", callback=make_orientation)
            dpg.add_menu_item(label="Auto Selector", callback=make_auto_selector)
        with dpg.menu(label="Override"):
            dpg.add_text(default_value="Nothing here yet.")
        dpg.add_spacer(width=30)
        dpg.add_text(default_value="Status:", color=(255, 255, 255, 100))
        dpg.add_text(default_value="Not Connected", color=(255, 0, 0))

    # Make all the windows to start with
    make_orientation()
    make_grid_view()
    make_field_view()
    make_auto_selector()

    # Setup
    dpg.setup_dearpygui()
    dpg.show_viewport()

    # Update loop
    while dpg.is_dearpygui_running():
        draw_call_update()
        dpg.render_dearpygui_frame()

    dpg.start_dearpygui()
    dpg.destroy_context()

if __name__ == "__main__":
    main()