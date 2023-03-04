import dearpygui.dearpygui as dpg





if __name__ == '__main__':
    dpg.create_context()
    dpg.create_viewport(title='Smarter Dashboard', width=500, height=500)


    with dpg.window(tag='Smarter Dashboard'):
        with dpg.drawlist(width=100.0, height=100.0, tag='drawlist', parent='Smarter Dashboard'):
            dpg.draw_rectangle(pmin=[0.00, 0.0], pmax=[100.0, 100.0])
        dpg.add_text('Display stuff here')



    dpg.setup_dearpygui()
    dpg.show_viewport()
    dpg.set_primary_window('Smarter Dashboard', True)
    dpg.start_dearpygui()
    dpg.destroy_context()