import bpy
from bpy.types import Menu

# spawn an edit mode selection pie (run while object is in edit mode to get a valid output)

bl_info = {
    "name": "Bear's Pies",
    "author": "Bjørnar Frøyse",
    "version": (0, 0, 1),
    "blender": (2, 72, 0),
    "description": "Mmmm... Pie.",
    "category": "User Interface",
}

class VIEW3D_PIE_bear_transform(Menu):
    bl_label = "Bear Transform Pies"

    def draw(self, context):
        layout = self.layout

        pie = layout.menu_pie()

        if(bpy.context.mode == 'EDIT_MESH'):
            pie.menu("VIEW3D_MT_edit_mesh_vertices")
            pie.menu("VIEW3D_MT_edit_mesh_faces")
            pie.operator("bear.checker_delete_edges")
            pie.menu("VIEW3D_MT_edit_mesh_edges")
            pie.operator("mesh.sort_elements")
            pie.operator("mesh.intersect")

        if(bpy.context.mode == 'OBJECT'):
            pie.operator("bear.align_transform")
            pie.operator("object.randomize_transform")
            pie.operator("transform.mirror")
            pie.operator("object.align")
            pie.operator("object.to_sphere")

        if(bpy.context.mode == 'EDIT_CURVE'):
            pie.operator("curve.spline_type_set")

class VIEW3D_PIE_bear_select(Menu):
    bl_label = "Bear Select Pies"

    def draw(self, context):
        layout = self.layout

        pie = layout.menu_pie()

        if(bpy.context.mode == 'EDIT_MESH'):
            pie.operator("mesh.select_mirror")
            pie.operator("mesh.select_face_by_sides")
            pie.operator("mesh.select_nth")
            pie.operator("mesh.select_random")
            pie.operator("mesh.inset")

        if(bpy.context.mode == 'OBJECT'):
            pie.operator("object.select_mirror")
            pie.operator("object.select_by_type")
            pie.operator("object.select_camera")
            pie.operator("object.select_random")

class HELPER_transform_align(bpy.types.Operator):
    bl_idname = "bear.align_transform"
    bl_label = "Align Transform To Orientation"

    def execute(self, context):
        bpy.ops.transform.transform(mode='ALIGN')
        return {'FINISHED'}

class CheckerThenDeleteEdges(bpy.types.Operator):
    bl_idname = "bear.checker_delete_edges"
    bl_label = "Delete Every 2nd Edge"

    def execute(self, context):
        bpy.ops.mesh.select_nth()
        bpy.ops.mesh.edge_collapse()
        return {'FINISHED'}

#class HELPER_inset_outset(bpy.types.Operator):
#    bl_idname = "bear.outset"
#    bl_label = "Outset Faces"
#
#    def execute(self, context):
#        bpy.ops.mesh.inset(use_boundary=True, use_even_offset=True, use_edge_rail=True, use_outset=True, use_select_inset=False, use_interpolate=True)
#        return {'FINISHED'}


script_classes = [
    VIEW3D_PIE_bear_select,
    VIEW3D_PIE_bear_transform,
    HELPER_transform_align,
    CheckerThenDeleteEdges,
    ]

def register():
    for c in script_classes:
        bpy.utils.register_class(c)


def unregister():
    for c in script_classes:
        bpy.utils.unregister_class(c)


if __name__ == "__main__":
    register()

    bpy.ops.wm.call_menu_pie(name="VIEW3D_PIE_bear_select")
