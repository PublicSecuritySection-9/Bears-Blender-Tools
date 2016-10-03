import bpy

bl_info = {
    "name": "Bear's Menu",
    "description": "",
    "author": "Bjørnar Frøyse",
    "version": (0, 0, 1),
    "blender": (2, 7, 1),
    "location": "Tool Shelf",
    "warning": "",  # used for warning icon and text in addons panel
    "wiki_url": "",
    "tracker_url": "",
    "category": "3D View"
    }

class BearMenu(bpy.types.Menu):
    bl_label = "Bear Menu"
    bl_idname = "OBJECT_MT_bear_menu"

    def draw(self, context):
        layout = self.layout

        layout.operator("wm.open_mainfile")
        layout.operator("wm.save_as_mainfile").copy = True

        layout.operator("object.shade_smooth")

        layout.label(text="Hello world!", icon='WORLD_DATA')

        # use an operator enum property to populate a sub-menu
        layout.operator_menu_enum("object.select_by_type",
                                  property="type",
                                  text="Select All by Type...",
                                  )

        # call another menu
        layout.operator("wm.call_menu", text="Unwrap").name = "VIEW3D_MT_uv_map"


def draw_item(self, context):
    layout = self.layout
    layout.menu(BearMenu.bl_idname)


def register():
    bpy.utils.register_class(BearMenu)

    # lets add ourselves to the main header
    bpy.types.INFO_HT_header.append(draw_item)


def unregister():
    bpy.utils.unregister_class(BearMenu)

    bpy.types.INFO_HT_header.remove(draw_item)

if __name__ == "__main__":
    register()

    # The menu can also be called from scripts
    #bpy.ops.wm.call_menu(name=BearMenu.bl_idname)
