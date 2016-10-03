bl_info = {
    "name": "Bear's Cleanup Tools",
    "description": "",
    "author": "Bjørnar Frøyse",
    "version": (0,0,1),
    "blender": (2, 7, 2),
    "location": "Tool Shelf",
    "warning": '', # used for warning icon and text in addons panel
    "wiki_url": "",
    "tracker_url": "",
    "category": "3D View"}

import bpy
#from bpy import *
import time
#from cursor_utils import *
import glob
import os
import bpy_extras
import mathutils
import math


class class_bear_cleanup_prefs(bpy.types.AddonPreferences):
    bl_idname = __name__
    obj_import_path = bpy.props.StringProperty(
            name = "OBJ Import Folder",
            description = "Folder to import most recent OBJ file from.",
            default = "")

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "obj_import_path")


##############################################################
#            DECIMATE SETUP
##############################################################

def setup_decimation(context):

    for ob in context.selected_objects:
        decimate = ob.modifiers.new("Decimation", type='DECIMATE')
        decimate.ratio = 0.1

class class_setup_decimation(bpy.types.Operator):
    """Init decimation"""
    bl_idname = "bear.setup_decimation"
    bl_label = "Setup Decimation"

    @classmethod
    def poll(cls, context):
        return len(context.selected_objects) is not 0

    def execute(self, context):
        setup_decimation(context)
        return {'FINISHED'}


##############################################################
#             REMOVE DOUBLES IN SELECTED
##############################################################

def remove_doubles_in_selected(context):

    b = bpy.ops

    initial_active_object = context.active_object
    initial_selection = context.selected_objects

    bpy.ops.object.select_all(action='DESELECT')

    for ob in initial_selection:
        if(type(ob.data) != bpy.types.Mesh):
            continue

        ob.select = True
        bpy.context.scene.objects.active = ob
    
        b.object.mode_set(mode='EDIT', toggle=True)
        bpy.ops.mesh.select_all(action='SELECT')
        b.mesh.remove_doubles(threshold=0.0001)
        b.object.mode_set(mode='OBJECT', toggle=True)

    bpy.context.scene.objects.active = initial_active_object

class class_remove_doubles_in_selected(bpy.types.Operator):
    """Remove Doubles In Selected Objects"""
    bl_idname = "object.remove_doubles_in_selected"
    bl_label = "Remove Doubles In Selected"

    @classmethod
    def poll(cls, context):
        return len(context.selected_objects) > 0

    def execute(self, context):
        
        remove_doubles_in_selected(context)
        return {'FINISHED'}

##############################################################
#             FLIP NORMALS IN SELECTED
##############################################################

def flip_normals_in_selected(context):

    print("wahat")
    b = bpy.ops

    initial_active_object = context.active_object
    initial_selection = context.selected_objects

    bpy.ops.object.select_all(action='DESELECT')

    for ob in initial_selection:
        if(type(ob.data) != bpy.types.Mesh):
            continue
            
        ob.select = True
        bpy.context.scene.objects.active = ob

        b.object.mode_set(mode='EDIT', toggle=True)
        bpy.ops.mesh.select_all(action='SELECT')
        b.mesh.flip_normals()
        b.object.mode_set(mode='OBJECT', toggle=True)
        
    bpy.context.scene.objects.active = initial_active_object

class class_flip_normals_in_selected(bpy.types.Operator):
    """Flip Normals In Selected Objects"""
    bl_idname = "object.flip_normals_in_selected"
    bl_label = "Flip Normals In Selected"

    @classmethod
    def poll(cls, context):
        return len(context.selected_objects) > 0

    def execute(self, context):
        flip_normals_in_selected(context)
        return {'FINISHED'}

##############################################################
#             FIND HIGH POLY MESHES
##############################################################

def find_high_poly_meshes(context):

    high_poly_objects = []
    for ob in context.selected_objects:
        #print(ob.dm_info('FINAL'))
        if(type(ob.data) != bpy.types.Mesh):
            continue
        polycount = len(ob.data.polygons)
        if polycount >= 2000:
            high_poly_objects.append(ob)
            print(ob.name, polycount)
           # print(ob.name, len(ob.data.tessfaces))


    bpy.ops.object.select_all(action='DESELECT')

    for ob in high_poly_objects:
        ob.select = True

class class_find_high_poly_meshes(bpy.types.Operator):
    """Find High Poly Meshes"""
    bl_idname = "object.find_high_poly_meshes"
    bl_label = "Find High Poly Meshes"

    @classmethod
    def poll(cls, context):
        return len(context.selected_objects) > 0

    def execute(self, context):
        
        find_high_poly_meshes(context)
        return {'FINISHED'}

##############################################################
#             ADJUST MATERIAL DIFFUSE BRIGHTNESS
##############################################################

def brighten_all_materials(context):
    for ob in context.selected_objects:
        if(type(ob.data) != bpy.types.Mesh):
            continue

        for mat in ob.data.materials:
            if mat is not None:
                    mat.diffuse_color.hsv = [mat.diffuse_color.hsv[0], mat.diffuse_color.hsv[1], mat.diffuse_color.hsv[2] + 0.01]

class class_brighten_all_materials(bpy.types.Operator):
    """brighten_all_materials"""
    bl_idname = "object.brighten_all_materials"
    bl_label = "Brighten"

    @classmethod
    def poll(cls, context):
        return len(context.selected_objects) > 0

    def execute(self, context):
        
        brighten_all_materials(context)
        return {'FINISHED'}


def darken_all_materials(context):
    for ob in context.selected_objects:
        if(type(ob.data) != bpy.types.Mesh):
            continue

        for mat in ob.data.materials:
            if mat is not None:
                    mat.diffuse_color.hsv = [mat.diffuse_color.hsv[0], mat.diffuse_color.hsv[1], mat.diffuse_color.hsv[2] - 0.01]

class class_darken_all_materials(bpy.types.Operator):
    """darken_all_materials"""
    bl_idname = "object.darken_all_materials"
    bl_label = "Darken"

    @classmethod
    def poll(cls, context):
        return len(context.selected_objects) > 0

    def execute(self, context):
        
        darken_all_materials(context)
        return {'FINISHED'}


##############################################################
#             TOOL SHELF BUTTONS
##############################################################

class class_bear_cleanup_buttons(bpy.types.Panel):

    bl_category = "Custom"
    bl_label = "Bear's Cleanup Tools"
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"

    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)
        col.operator("object.brighten_all_materials")
        col.operator("object.darken_all_materials")
        col.operator("object.remove_doubles_in_selected")
        col.operator("object.flip_normals_in_selected")
        col.operator("object.find_high_poly_meshes")
        col.label("Modifiers")
        col.operator("bear.setup_decimation")

script_classes = [
    class_remove_doubles_in_selected,
    class_flip_normals_in_selected,
    class_brighten_all_materials,
    class_darken_all_materials,
    class_setup_decimation,
    class_find_high_poly_meshes,
    class_bear_cleanup_buttons,
    class_bear_cleanup_prefs,
]

def register():
    for c in script_classes:
        bpy.utils.register_class(c)

def unregister():
    for c in script_classes:
        bpy.utils.unregister_class(c)

if __name__ == "__main__":
    register()
