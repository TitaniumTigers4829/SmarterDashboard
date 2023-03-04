import dearpygui.dearpygui as dpg
import array

dpg.create_context()

logowidth, logoheight, logochannels, logodata = dpg.load_image('GUI/4829logo.png') # 0: width, 1: height, 2: channels, 3: data
fieldwidth, fieldheight, fieldchannels, fielddata = dpg.load_image('GUI/gamefield.png') # 0: width, 1: height, 2: channels, 3: data
trackingwidth, trackingheight, trackingchannels, trackingdata = dpg.load_image('GUI/robot.png')

with dpg.texture_registry():
    dpg.add_static_texture(logowidth, logoheight, logodata, tag="4829logo")
    dpg.add_static_texture(fieldwidth, fieldheight, fielddata, tag="Gamefield")
    dpg.add_static_texture(trackingwidth, trackingheight, trackingdata, tag="robot")
robotx = (175, 300)
roboty = (250, 375)
with dpg.window(tag="Main"):
    #displays images
    with dpg.drawlist(width=2000, height=2000):
        dpg.draw_image("4829logo", (0, 0), (50, 50), uv_min=(0, 0), uv_max=(1, 1))
        dpg.draw_image("Gamefield", (100,100), (1000, 500), uv_min=(0, 0), uv_max=(1, 1))
        dpg.draw_image("robot", robotx, roboty, uv_min=(0, 0), uv_max=(1, 1))

       

with dpg.viewport_drawlist():
        #draws a line from a to b
        dpg.draw_line((100, 50), (1000, 50), thickness=5)


dpg.create_viewport(title='Smarter Dashboard', width=1500, height=1500)
dpg.setup_dearpygui()

dpg.show_viewport()
while dpg.is_dearpygui_running():
    dpg.render_dearpygui_frame()
dpg.set_primary_window("Main", True)
dpg.start_dearpygui()
dpg.destroy_context()

