import dearpygui.dearpygui as dpg
import numpy as np
import time

dpg.create_context()
dpg.configure_app(docking=True, docking_space=True)
dpg.create_viewport(title="4829 SmarterDashboard", width=800, height=600)

# Fetch textures (should be a function)
logowidth, logoheight, logochannels, logodata = dpg.load_image('GUI/4829logo.png') # 0: width, 1: height, 2: channels, 3: data
fieldwidth, fieldheight, fieldchannels, fielddata = dpg.load_image('GUI/gamefield.png') # 0: width, 1: height, 2: channels, 3: data
trackingwidth, trackingheight, trackingchannels, trackingdata = dpg.load_image('GUI/robot.png')

# Load textures intro registry
with dpg.texture_registry():
    dpg.add_static_texture(logowidth, logoheight, logodata, tag="logo")
    dpg.add_static_texture(fieldwidth, fieldheight, fielddata, tag="field")
    dpg.add_static_texture(trackingwidth, trackingheight, trackingdata, tag="robot")

def make_dummy_window():
    with dpg.window(label="dummy", tag="dummy"):
        dpg.add_text(default_value="Dummy text")
        dpg.add_button(label="Dummy button")

# Create the menu bar
with dpg.viewport_menu_bar(label="Menu", tag="menu"):
    with dpg.menu(label="Settings"):
        dpg.add_menu_item(label="Enable Something")
        dpg.add_slider_double(label="Path opacity")
    with dpg.menu(label="Widgets"):
        dpg.add_menu_item(label="Field View", callback=make_dummy_window)
        dpg.add_menu_item(label="Grid View", callback=make_dummy_window)
        dpg.add_menu_item(label="Orientation", callback=make_dummy_window)
    with dpg.menu(label="Override"):
        dpg.add_text(default_value="Nothing here yet.")

# Create each component of the gui
with dpg.window(label="main", tag="main"):
    dpg.add_button(label="Thing number one")

with dpg.window(label="sub", tag="sub"):
    dpg.add_button(label="Thing number two")

dpg.setup_dearpygui()
dpg.show_viewport()

while dpg.is_dearpygui_running():
    # update code start



    # update code end

    dpg.render_dearpygui_frame()

dpg.start_dearpygui()
dpg.destroy_context()

