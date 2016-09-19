bl_info = {
    "name": "Bear's Bag of Tricks",
    "description": "",
    "author": "Bjørnar Frøyse",
    "version": (0,2,7),
    "blender": (2, 7, 3),
    "location": "Tool Shelf",
    "warning": '', # used for warning icon and text in addons panel
    "wiki_url": "",
    "tracker_url": "",
    "category": "3D View"}

import bpy
#from bpy import *
import time
import glob
import os
import bpy_extras
import mathutils
import math
import bmesh
import subprocess

class class_bbotaddonprefs(bpy.types.AddonPreferences):
    bl_idname = __name__
    obj_import_path = bpy.props.StringProperty(
            name = "OBJ Import Folder",
            description = "Folder to import most recent OBJ file from.",
            default = "")

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "obj_import_path")
  
##############################################################
#               COPY/PASTE TRANSFORMS
##############################################################

global copiedLocation
global copiedRotation
global copiedScale

def copy_full_transform(context):
    
    global copiedLocation
    global copiedRotation
    global copiedScale
    
    ob = context.active_object

    copiedLocation = ob.location.copy()
    copiedRotation = ob.rotation_euler.copy()
    copiedScale = ob.scale.copy()

def paste_full_transform(context):
    
    global copiedLocation
    global copiedRotation
    global copiedScale


    if (bpy.context.mode == 'OBJECT'):
        for ob in context.selected_objects:
            ob.location = copiedLocation
            ob.rotation_euler = copiedRotation
            ob.scale = copiedScale
    if (bpy.context.mode == 'POSE'):
        return None
        

class class_copy_full_transform(bpy.types.Operator):
    """Copy Full Transform"""
    bl_idname = "object.copy_full_transform"
    bl_label = "Copy Full Transform"

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        
        copy_full_transform(context)
        return {'FINISHED'}
    
class class_paste_full_transform(bpy.types.Operator):
    """Paste Full Transform"""
    bl_idname = "object.paste_full_transform"
    bl_label = "Paste Full Transform"

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        paste_full_transform(context)
        return {'FINISHED'}

class class_buffer_print(bpy.types.Operator):
    bl_idname = "object.debug_print_buffers"
    bl_label = "DEBUG: Print Buffers"

    def execute(self, context):
        print("")
        print("Current transform buffer:")
        print("Location:", copiedLocation)
        print("Rotation:", "X",copiedRotation[0],"Y", copiedRotation[1],"Z", copiedRotation[2])
        print("Scale:", copiedScale)
        return {'FINISHED'}

##############################################################
#               ONE KEY TOGGLE WIRES
##############################################################

def toggle_wires(context, inputstring):
    
    show_wire = context.active_object.show_wire
    show_bounds = context.active_object.show_bounds

    if (inputstring == 'WIREFRAME'):
        for ob in context.selected_objects:
            ob.show_wire = not show_wire
            ob.show_all_edges = True

    if (inputstring == 'BOUNDS'):
        for ob in context.selected_objects:
            ob.show_bounds = not show_bounds

class class_toggle_stuff(bpy.types.Operator):
    """Toggle Wireframe & Draw All Edges"""
    bl_idname = "bear.toggle_wires"
    bl_label = "Toggle Wireframe"

    what_to_toggle = bpy.props.StringProperty(
            name="What To Toggle")

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        
        toggle_wires(context, self.what_to_toggle)
        return {'FINISHED'}

##############################################################
#               CAMERA SETUP ORTHO
##############################################################

def camera_setup_ortho(context):

    C = bpy.context
    C.scene.camera.location = (0.0, 0.0, 10.0)
    C.scene.camera.rotation_euler = (0.0, 0.0, 0.0)
    C.scene.camera.data.type = 'ORTHO'

    C.scene.render.resolution_x = 1024.0
    C.scene.render.resolution_y = 1024.0

    C.scene.camera.data.ortho_scale = max(C.active_object.dimensions.x, C.active_object.dimensions.y)

class class_camera_setup_ortho(bpy.types.Operator):
    """Setup camera for rendering textures"""
    bl_idname = "bear.camera_setup_ortho"
    bl_label = "Setup Cam Ortho"

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        camera_setup_ortho(context)
        return {'FINISHED'}

##############################################################
#             APPLY SCALE ON LINKED OBJECTS
##############################################################

def apply_linked_transform(context, reset_rot, reset_scl):

    print("\n\n")

    active_obj = context.active_object

    original_selection = bpy.context.selected_objects

    bpy.ops.object.select_linked(type='OBDATA')
    linked = bpy.context.selected_objects
    linked.remove(active_obj)

    print(linked)
    active_obj.select = True

    for linked_object in linked:
        linked_object.select = False

    data_name = active_obj.data.name
    bpy.ops.object.make_single_user(type='SELECTED_OBJECTS', object=False, obdata=True, material=False, texture=False, animation=False)

    active_obj.data.name = data_name

    bpy.ops.object.transform_apply(location=False, rotation=reset_rot, scale=reset_scl)

    for linked_object in linked:
        linked_object.select = True

    bpy.ops.object.make_links_data(type='OBDATA')

    for linked_object in linked:
        linked_object.select = False

    for obj in original_selection:
        obj.select = True
        if(reset_rot):
            bpy.ops.object.rotation_clear()
        if(reset_scl):
            bpy.ops.object.scale_clear()

    active_obj.select = True

class class_apply_linked_scale(bpy.types.Operator):
    """Apply Scale (Linked)"""
    bl_idname = "object.apply_linked_scale"
    bl_label = "Apply Scale To Linked"

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        apply_linked_transform(context, False, True)
        return {'FINISHED'}

class class_apply_linked_rotation(bpy.types.Operator):
    """Apply Rotation (Linked)"""
    bl_idname = "object.apply_linked_rotation"
    bl_label = "Apply Rotation To Linked"

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        apply_linked_transform(context, True, False)
        return {'FINISHED'}

class class_apply_linked_transform(bpy.types.Operator):
    """Apply Transform (Linked)"""
    bl_idname = "object.apply_linked_transform"
    bl_label = "Apply Scale To Linked"

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        apply_linked_transform(context, True, True)
        return {'FINISHED'}

##############################################################
#            CREATE BRANCHES FROM GPENCIL
##############################################################


def bear_branches(context):
    branch_radius = 0.25
    scn = bpy.context.scene
    gps = bpy.context.blend_data.grease_pencil[-1].layers.active.active_frame
    cu = bpy.data.curves.new("GpencilBranch", 'CURVE')
    cu.dimensions = '3D'
    cu.bevel_depth = branch_radius
    cu.fill_mode = 'FULL'
    cu.bevel_resolution = 2
    cu.use_uv_as_generated = True

    for stroke in gps.strokes:
        i = 0
        numpoints = len(stroke.points)
        spline = cu.splines.new(type='NURBS')
        spline.resolution_u = 1
        spline.points.add(numpoints-1)
        spline.use_endpoint_u = True
        for point in spline.points:
            spline.points[i].co = (stroke.points[i].co[0], stroke.points[i].co[1], stroke.points[i].co[2], 1.0)
            point.radius = 1 - ((1/len(spline.points)) * i)
            i += 1
            if (i == numpoints):
                point.radius = 0.0
    gps.clear()

    ob = bpy.data.objects.new("GPencil Branch.000", cu)
    scn.objects.link(ob)
    scn.objects.active = ob
    bpy.ops.object.select_all(action='DESELECT')
    ob.select = True

    cursorBuffer = bpy.context.scene.cursor_location.copy()

    bpy.context.scene.cursor_location = cu.splines[0].points[0].co.xyz
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
    bpy.context.scene.cursor_location = cursorBuffer


class class_bear_branches(bpy.types.Operator):
    """Create Branches From Grease Pencil"""
    bl_idname = "bear.branches"
    bl_label = "GPencil Branch"

    @classmethod
    def poll(cls, context):
        if bpy.context.mode != 'OBJECT':
            return False
        elif len(bpy.data.grease_pencil) is 0:
            return False
        elif len(bpy.data.grease_pencil[-1].layers) is 0:
            return False
        elif bpy.data.grease_pencil[-1].layers.active.active_frame is None:
            return False
        elif len(bpy.data.grease_pencil[-1].layers.active.active_frame.strokes) is 0:
            return False
        else:
            return True

    def execute(self, context):
        bear_branches(context)
        return {'FINISHED'}

##############################################################
#            TAPER CURVE POINT SCALE
##############################################################

def bear_taper_curve_scale(context):
    i = 0
    obj = context.active_object
    branch_radius = 0.25
    scn = bpy.context.scene
    spline = obj.data.splines[0]
    for point in spline.points:
        point.radius = 1 - ((1/len(spline.points)) * i)
        i += 1
        if (i == len(spline.points)):
            point.radius = 0.0

class class_bear_taper_curve_scale(bpy.types.Operator):
    """Taper an already existing curve"""
    bl_idname = "bear.taper_curve_scale"
    bl_label = "Taper Curve"

    @classmethod
    def poll(cls, context):
        return len(context.selected_objects) is not 0

    def execute(self, context):
        bear_taper_curve_scale(context)
        return {'FINISHED'}


##############################################################
#            RENAME OBJECT
##############################################################

def rename_object(context, namestring):
    string = "New Name"


class class_bear_rename_object(bpy.types.Operator):
    """Renames seleted objects"""
    bl_idname = "bear.rename_object"
    bl_label = "Rename Object"

    namestring = bpy.props.StringProperty(name="Name")

    @classmethod
    def poll(cls, context):
        return len(context.selected_objects) is not 0

    def execute(self, context):
        rename_object(context)
        return {'FINISHED'}


##############################################################
#            SIERPINSKY CUBE
##############################################################

def sierpinsky_cube(context):
    bpy.ops.mesh.subdivide(number_cuts = 2)
   #obj = bpy.context.edit_object
   #me = obj.data
   #bm = bmesh.from_edit_mesh(me)

   #bmesh.ops.subdivide_edges(bm, edges = bm.edges, 
   #    use_only_quads = False,
   #    smooth = 1,
   #    cuts = 2)
   #    # smooth_falloff = 0,
   #    # fractal = 0,
   #    # along_normal = 0,
   #    #seed = 1,
   #    #edge_percents = KEY,
   #    #quad_corner_type = KEY,
   #    #use_grid_fill = KEY,
   #    #use_single_edge = KEY,
   #    #use_sphere = KEY,
   #    #use_smooth_even = KEY,
   #    #)

   #bmesh.update_edit_mesh(me, True)

class class_bear_sierpinsky_cube(bpy.types.Operator):
    """Create a sierpinsky cube with n iterations"""
    bl_idname = "bear.sierpinsky_cube"
    bl_label = "[WIP] Sierpinsky Cube"

    namestring = bpy.props.StringProperty(name="Name")

    @classmethod
    def poll(cls, context):
        return len(context.selected_objects) is not 0

    def execute(self, context):
        sierpinsky_cube(context)
        return {'FINISHED'}

##############################################################
#            ARRAY SETUP
##############################################################

def array_setup(context):

    deg2rad = 0.0174532925


    ob = bpy.context.active_object

    array1 = ob.modifiers.new("Array", type='ARRAY')
    bpy.ops.object.empty_add()
    array_control = bpy.context.scene.objects[0]
    array_control.name = "Array Control 1"

    array1.use_relative_offset = False
    array1.use_object_offset = True
    array1.offset_object = array_control

    bpy.context.scene.update()

    array_control.select = False
    ob.select = True
    bpy.context.scene.objects.active = array_control

class class_bear_array_setup(bpy.types.Operator):
    """Initialize a regular array modifier"""
    bl_idname = "bear.array_setup"
    bl_label = "Setup Array"

    @classmethod
    def poll(cls, context):
        return len(context.selected_objects) is not 0

    def execute(self, context):
        array_setup(context)
        return {'FINISHED'}
##############################################################
#            FANCY ARRAY SETUP
##############################################################

def fancy_array_setup(context):

    deg2rad = 0.0174532925

    ob = bpy.context.active_object
    ob.name = "Array Object"

    array1_count = 5
    array2_count = 5
    array3_count = 5

    array1 = ob.modifiers.new("array1", type='ARRAY')
    bpy.ops.object.empty_add()
    array_control_1 = bpy.context.scene.objects[0]
    array_control_1.name = "Array Control 1"

    array_control_1.location.x = 1.0
    array_control_1.scale.x = 0.8
    array_control_1.scale.y = 0.8
    array_control_1.scale.z = 0.8
    array_control_1.rotation_euler.y = -15.0 * deg2rad

    array1.use_relative_offset = False
    array1.use_object_offset = True
    array1.offset_object = array_control_1
    array1.count = array1_count

    array2 = ob.modifiers.new("array2", type='ARRAY')
    bpy.ops.object.empty_add()
    array_control_2 = bpy.context.scene.objects[0]
    array_control_2.name = "Array Control 2"

    array_control_2.location.z = 1.0
    array_control_2.scale.x = 0.8
    array_control_2.scale.y = 0.8
    array_control_2.scale.z = 0.8
    array_control_2.rotation_euler.z = -15.0 * deg2rad

    array2.use_relative_offset = False
    array2.use_object_offset = True
    array2.offset_object = array_control_2
    array2.count = array2_count

    array3 = ob.modifiers.new("array3", type='ARRAY')
    bpy.ops.object.empty_add()
    array_control_3 = bpy.context.scene.objects[0]
    array_control_3.name = "Array Control 3"
    array3.use_relative_offset = False
    array3.use_object_offset = True
    array3.offset_object = array_control_3
    array3.count = array3_count

    d = array_control_3.driver_add('rotation_euler', 2)
    d.modifiers.remove(d.modifiers[0])

    var = d.driver.variables.new()
    var.type = 'SINGLE_PROP'
    var.targets[0].id = ob
    var.targets[0].data_path = 'modifiers["array3"].count'
    d.driver.expression =  "360/var*0.0174532925"

    bpy.context.scene.update()

    #ob.select = False
    array_control_3.select = False
    array_control_1.select = True
    bpy.context.scene.objects.active = array_control_1

    context.scene.camera.location = (0,0,10)
    context.scene.camera.rotation_euler = (0,0,0)
    context.scene.render.resolution_x = 2048
    context.scene.render.resolution_y = 2048
    context.scene.cycles.caustics_reflective = False
    context.scene.cycles.caustics_refractive = False


class class_bear_fancy_array_setup(bpy.types.Operator):
    """Initialize a fancy smancy array!"""
    bl_idname = "bear.fancy_array_setup"
    bl_label = "Setup Fancy Array"

    @classmethod
    def poll(cls, context):
        return len(context.selected_objects) is not 0

    def execute(self, context):
        fancy_array_setup(context)
        return {'FINISHED'}

##############################################################
#            DOUBLE SIDED SOLIDIFY SETUP
##############################################################

def double_sided_solidify_setup(context):

    modifier_name = "Auto Setup Double Sided"

    original_active_object = bpy.context.active_object
    original_selection = bpy.context.selected_objects

    for ob in original_selection:
        ob.select = False

    for ob in original_selection:
        ob.select = True
        if(len(ob.modifiers) > 0):
            for mod in ob.modifiers:
                if(mod.name == modifier_name):
                    ob.modifiers.remove(mod)

        solidify_modifier = ob.modifiers.new(modifier_name, type='SOLIDIFY')
        

        solidify_modifier.thickness = 0
        solidify_modifier.offset = 0
        solidify_modifier.use_rim = False

        ob.data.use_auto_smooth = True

    for ob in original_selection:
        ob.select = True

    bpy.context.scene.objects.active = original_active_object

class class_bear_double_sided_solidify_setup(bpy.types.Operator):
    """Initialize a fancy edit double sided solidify modifier!"""
    bl_idname = "bear.double_sided_solidify_setup"
    bl_label = "Setup Double Sided Solidify"

    @classmethod
    def poll(cls, context):
        return len(context.selected_objects) is not 0

    def execute(self, context):
        double_sided_solidify_setup(context)
        return {'FINISHED'}

##############################################################
#            NORMAL EDIT SETUP
##############################################################

def edit_normals_setup(context):

    modifier_name = "Auto Setup Split Normals"

    original_active_object = bpy.context.active_object
    original_selection = bpy.context.selected_objects

    for ob in original_selection:
        ob.select = False

    for ob in original_selection:
        ob.select = True
        if(len(ob.modifiers) > 0):
            for mod in ob.modifiers:
                if(mod.name == modifier_name):
                    ob.modifiers.remove(mod)

        edit_normal = ob.modifiers.new(modifier_name, type='NORMAL_EDIT')
        
        normal_edit_target = None

        for obj in bpy.context.scene.objects:
            if(obj.name == ob.name + " Normal Target"):
                normal_edit_target = obj

        if (normal_edit_target is None):
            bpy.ops.object.empty_add()
            normal_edit_target = bpy.context.scene.objects[0]
            normal_edit_target.name = ob.name + " Normal Target" 

        normal_edit_target.location = mathutils.Vector((ob.location.x, ob.location.y, ob.location.z + 1))

        edit_normal.target = normal_edit_target
        #edit_normal.mode = 'DIRECTIONAL'
        edit_normal.mode = 'RADIAL'

        ob.data.use_auto_smooth = True

    for ob in original_selection:
        ob.select = True

    bpy.context.scene.objects.active = original_active_object

class class_bear_edit_normals_setup(bpy.types.Operator):
    """Initialize a fancy edit normals modifier!"""
    bl_idname = "bear.edit_normals_setup"
    bl_label = "Setup Edit Normals"

    @classmethod
    def poll(cls, context):
        return len(context.selected_objects) is not 0

    def execute(self, context):
        edit_normals_setup(context)
        return {'FINISHED'}
##############################################################
#            SET VERTEX COLORS FROM EDIT MODE
##############################################################

def set_vertex_colors_from_edit_mode(context):
    obj = bpy.context.edit_object

    materials = bpy.context.edit_object.data.materials

    material_id = bpy.context.edit_object.active_material_index

    color = materials[material_id].diffuse_color

    original_use_paint_mask = obj.data.use_paint_mask

    bpy.ops.object.mode_set(mode='VERTEX_PAINT', toggle=False)
    original_brush_color = bpy.data.brushes['Add'].color

    obj.data.use_paint_mask = True
    bpy.data.brushes['Add'].color = color
    bpy.ops.paint.vertex_color_set()

    bpy.data.brushes['Add'].color = original_brush_color

    bpy.ops.object.mode_set(mode='EDIT', toggle=False)   

    obj.data.use_paint_mask = original_use_paint_mask


class class_bear_set_vertex_colors_from_edit_mode(bpy.types.Operator):
    """Set vertex colors on selected faces from edit mode"""
    bl_idname = "bear.set_vertex_colors_from_edit_mode"
    bl_label = "Set Vertex Colors"

    @classmethod
    def poll(cls, context):
        return bpy.context.edit_object is not None

    def execute(self, context):
        set_vertex_colors_from_edit_mode(context)
        return {'FINISHED'}

##############################################################
#            BEND SETUP
##############################################################

def bend_setup(context):

    ob = bpy.context.active_object

    bend = ob.modifiers.new("Bend", type='SIMPLE_DEFORM')
    
    bpy.ops.object.empty_add()
    bend_control_object = bpy.context.scene.objects[0]
    bend_control_object.name = "Bend Control" 

    bend.deform_method = 'BEND'
    bend.origin = bend_control_object
    bend.angle = 360*deg2rad

    bpy.context.scene.objects.active = ob

class class_bear_bend_setup(bpy.types.Operator):
    """Initialize a fancy bend modifier!"""
    bl_idname = "bear.bend_setup"
    bl_label = "Setup Bend"

    @classmethod
    def poll(cls, context):
        return len(context.selected_objects) is not 0

    def execute(self, context):
        bend_setup(context)
        return {'FINISHED'}

##############################################################
#            MIRROR SETUP
##############################################################

def mirror_setup(context):

    ob = bpy.context.active_object

    mirror = ob.modifiers.new("Mirror", type='MIRROR')
    
    bpy.ops.object.empty_add()
    mirror_control_object = bpy.context.scene.objects[0]
    mirror_control_object.name = "Mirror Control" 
    mirror_control_object.select = False

    mirror.mirror_object = mirror_control_object

    ob.select = True
    bpy.context.scene.objects.active = ob

class class_bear_mirror_setup(bpy.types.Operator):
    """Initialize a fancy mirror modifier!"""
    bl_idname = "bear.mirror_setup"
    bl_label = "Setup Mirror"

    @classmethod
    def poll(cls, context):
        return len(context.selected_objects) is not 0

    def execute(self, context):
        mirror_setup(context)
        return {'FINISHED'}

##############################################################
#            RESET MESH ROTATION
##############################################################

def reset_mesh_rotation(context):
    ob = bpy.context.edit_object
    mat = ob.matrix_world
    me = ob.data

    zero = mathutils.Vector((0.0,0.0,0.0))

    verts = me.vertices
    polygons = me.polygons
    edges = me.edges

    selected_vert = 0
    selected_edge = 0
    selected_poly = 0

    s_pos = 0
    s_rot = 0

    vert_selection = bpy.context.tool_settings.mesh_select_mode[0] 
    edge_selection = bpy.context.tool_settings.mesh_select_mode[1]
    face_selection = bpy.context.tool_settings.mesh_select_mode[2]

    bpy.ops.object.mode_set(mode='OBJECT', toggle=True)   
    bpy.ops.object.mode_set(mode='EDIT', toggle=True)

    if(vert_selection):
        for v in verts:
            if v.select:
                selected_vert = v
                break

        s_rot = selected_vert.normal
        s_pos = selected_vert.co

    if(face_selection):
        for p in polygons:
            if p.select:
                selected_poly = p
                break

        s_rot = array_to_vector(selected_poly.normal)
        s_pos = array_to_vector(selected_poly.center)
        vec = mathutils.Vector((0.0, 0.0, 1.0))
        bpy.ops.transform.create_orientation(name="RESET_ROT_ORIENTATION", use_view=False, use=True, overwrite=True)

    # Probably need bmesh stuff to get proper edge info
    # if(edge_selection):
    #     for e in edges:
    #         if e.select:
    #             selected_edge = e
    #             break

    #     #s_rot = selected_edge.normal
    #     s_pos = selected_edge.center


    bpy.ops.object.mode_set(mode='OBJECT', toggle=True)   

    bpy.ops.object.empty_add()
    empty = bpy.context.scene.objects[0]
    empty.name = "Temp Empty"
    empty.location = mat * s_pos

    bpy.context.scene.objects.active = empty

    bpy.ops.transform.transform(mode='ALIGN', value=(0, 0, 0, 0), axis=(0, 0, 0), constraint_axis=(False, False, False), constraint_orientation='RESET_ROT_ORIENTATION', mirror=False, proportional='DISABLED', proportional_edit_falloff='SMOOTH')
    bpy.ops.transform.delete_orientation()

    ob.select = True

    bpy.ops.object.parent_set(type='OBJECT', xmirror=False, keep_transform=True)

    ob.select = False

    bpy.ops.object.rotation_clear()

    ob.select = True
    bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
    ob.select = False

    bpy.ops.object.delete(use_global=False)

    bpy.context.scene.objects.active = ob
    bpy.ops.object.mode_set(mode='EDIT', toggle=True)

    print("\n")

def array_to_vector(a):
    return mathutils.Vector((a[0],a[1],a[2]))

def euler_to_vector(e):
    return mathutils.Vector((e.x,e.y,e.z))

class class_reset_mesh_rotation(bpy.types.Operator):
    """Reset rotation of a mesh ..."""
    bl_idname = "bear.reset_mesh_rotation"
    bl_label = "[WIP] Reset Mesh Rotation"

    #@classmethod
    #def poll(cls, context):
    #    return len(context.selected_objects) is not 0

    def execute(self, context):
        reset_mesh_rotation(context)
        return {'FINISHED'}

##############################################################
#            EDGE SLIDE "SPECIAL"
##############################################################

def catmull_edge_slide(context):
    ob = bpy.context.edit_object
    bpy.ops.transform.edge_slide(value=0.14285)
    bpy.ops.transform.edge_slide(value=-0.12501)

class class_catmull_edge_slide(bpy.types.Operator):
    """Catmull edge slide"""
    bl_idname = "bear.catmull_edge_slide"
    bl_label = "'Catmull' Special"

    #@classmethod
    #def poll(cls, context):
    #    return len(context.selected_objects) is not 0

    def execute(self, context):
        catmull_edge_slide(context)
        return {'FINISHED'}


##############################################################
#            EDGE SLIDE TO CENTER
##############################################################

def edge_slide_to_center(context):
    ob = bpy.context.edit_object
    bpy.ops.transform.edge_slide(value=1.0)
    bpy.ops.transform.edge_slide(value=0.5)

class class_edge_slide_to_center(bpy.types.Operator):
    """Edge Slide To Center"""
    bl_idname = "bear.edge_slide_to_center"
    bl_label = "Edge Slide To Center"

    #@classmethod
    #def poll(cls, context):
    #    return len(context.selected_objects) is not 0

    def execute(self, context):
        edge_slide_to_center(context)
        return {'FINISHED'}

##############################################################
#            BEVEL PERFECT ROUND
##############################################################

from bpy.props import FloatProperty, IntProperty

def bevel_perfect_round(context, bevel_width, bevel_segments):
    ob = bpy.context.edit_object
    bpy.ops.mesh.bevel(offset_type='PERCENT', offset=bevel_width, segments=bevel_segments)
    bpy.ops.mesh.remove_doubles(threshold=0.0001)

class class_bevel_perfect_round(bpy.types.Operator):
    """Cutmull edge slide"""
    bl_idname = "bear.bevel_perfect_round"
    bl_label = "Bevel Perfect Round"
    bl_options = {'REGISTER', 'UNDO'}

    bevel_width = FloatProperty(
            name="Width",
            description="Width",
            min=0.0, max=100.0,
            default=50.0,
            )

    bevel_segments = IntProperty(
            name="Segments",
            description="Width",
            min=1, max=8,
            default=4,
            )

    #@classmethod
    #def poll(cls, context):
    #    return len(context.selected_objects) is not 0

    def execute(self, context):
        bevel_perfect_round(context, self.bevel_width, self.bevel_segments)
        return {'FINISHED'}

##############################################################
#           NICE MESH SPIN
##############################################################

def nice_mesh_spin(context, spin_steps, spin_angle):
    ob = bpy.context.edit_object

    # Get view axis rotation. Turns out it's the third row of the matrix.
    view_mat = bpy.context.region_data.view_matrix
    view_axis = (view_mat[2][0], view_mat[2][1], view_mat[2][2])

    # Spin uses radians, input uses degrees. Convert nao!
    spin_angle = math.radians(spin_angle)

    # Calculate proper rotation so the object doesn't need to be deleted after spinning.
    actual_spin_steps = spin_steps - 1
    actual_spin_angle = spin_angle - (spin_angle / spin_steps)

    # Spin!
    bpy.ops.mesh.spin(steps=actual_spin_steps, dupli=True, angle=actual_spin_angle, center=bpy.context.scene.cursor_location, axis=view_axis)

class class_nice_mesh_spin(bpy.types.Operator):
    """Nice Mesh Spin"""
    bl_idname = "bear.nice_mesh_spin"
    bl_label = "Nice Mesh Spin"
    bl_options = {'REGISTER', 'UNDO'}

    spin_angle = FloatProperty(
            name="Angle",
            description="Width",
            min=0.0, max=360.0,
            default=360.0,
            )

    spin_steps = IntProperty(   
            name="Steps",
            description="Width",
            min=1, max=64,
            default=8,
            )

    @classmethod
    def poll(cls, context):
       return bpy.context.edit_object

    def execute(self, context):
        nice_mesh_spin(context, self.spin_steps, self.spin_angle)
        return {'FINISHED'}


##############################################################
#                  UNWRAP MANY TUBES 
##############################################################

def bear_unwrap_tubes(context):
    scn = bpy.context.scene
    uvop = bpy.ops.uv
    gp = bpy.ops.gpencil
    m = bpy.data.meshes


class class_bear_unwrap_tubes(bpy.types.Operator):
    """Unwrap Many Tubes"""
    bl_idname = "bear.unwrap_tubes"
    bl_label = "Unwrap Tubes"

    def execute(self, context):
        bear_unwrap_tubes(context)
        return {'FINISHED'}


##############################################################
#             ONE CLICK AO BAKE FROM OBJ
##############################################################

def one_click_ao_bake_from_obj(context):
    pass


class class_one_click_ao_bake_from_obj(bpy.types.Operator):
    """One Click AO Bake"""
    bl_idname = "object.one_click_ao_bake_from_obj"
    bl_label = "One Click AO Bake"

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        one_click_ao_bake_from_obj(context)
        return {'FINISHED'}

##############################################################
#                   SAVE INCREMENTAL
##############################################################


class class_save_incremental(bpy.types.Operator):

    bl_idname = "bear.save_incremental"
    bl_label = "Save Incremental"

    def execute(self, context):
        print(bpy.path.abspath('//'))
        print(bpy.data.filepath)
        print(bpy.data.is_saved)
        print(bpy.path.basename(bpy.context.blend_data.filepath))

        bpy.ops.wm.save_as_mainfile(copy=True)
        return {'FINISHED'}

##############################################################
#       SAVE TRANSPARENT IMAGE TO TEMP FOLDER (FOR PHOTOSHOP IMPORT)
##############################################################


class class_copy_image_to_temp_with_alpha(bpy.types.Operator):

    bl_idname = "image.save_copy_to_temp_with_alpha"
    bl_label = "Copy transparent image to Temp"

    def execute(self, context):
        original_render_format = bpy.context.scene.render.image_settings.file_format
        original_color_mode = bpy.context.scene.render.image_settings.color_mode

        bpy.context.scene.render.image_settings.file_format = 'PNG'
        bpy.context.scene.render.image_settings.color_mode = 'RGBA'
        bpy.ops.image.save_as(copy=True, filepath="C:/tmp/clip/clip.png")

        bpy.context.scene.render.image_settings.file_format = original_render_format
        bpy.context.scene.render.image_settings.color_mode = original_color_mode

        subprocess.call([bpy.context.user_preferences.filepaths.image_editor, 'C:\\tmp\\clip\\clip.png'])
        return {'FINISHED'}

##############################################################
#       SAVE IMAGE TO TEMP FOLDER (FOR PHOTOSHOP IMPORT)
##############################################################


class class_copy_image_to_temp(bpy.types.Operator):

    bl_idname = "image.save_copy_to_temp"
    bl_label = "Copy image to Temp"

    def execute(self, context):
        original_render_format = bpy.context.scene.render.image_settings.file_format

        bpy.context.scene.render.image_settings.file_format = 'TARGA_RAW'
        bpy.ops.image.save_as(copy=True, filepath="C:/tmp/clip/clip.tga")

        bpy.context.scene.render.image_settings.file_format = original_render_format
        return {'FINISHED'}

##############################################################
#             MAKE UV LAYOUT PNG FROM OBJ
##############################################################


class class_uv_layout_from_obj(bpy.types.Operator):

    bl_idname = "uv.uv_layout_from_obj"
    bl_label = "UV Layout From OBJ"

    filepath = bpy.props.StringProperty(subtype="FILE_PATH")
    filename = bpy.props.StringProperty(subtype="FILE_NAME")

    filter_glob = bpy.props.StringProperty(
            default="*.obj",
            options={'HIDDEN'},
            )

    export_size = bpy.props.EnumProperty(
        name="Image Size",
        description="Exported Image Size In Pixels",
        items=(('64', "64", "64x64"),
               ('128', "128", "128x128"),
               ('256', "256", "256x256"),
               ('512', "512", "512x512"),
               ('1024', "1024", "1024x1024"),
               ('2048', "2048", "2048x2048"),
               ('4096', "4096", "4096x4096")
               ),
        default="2048"
        )

    def execute(self, context):
        time_start = time.time()
        size = int(self.export_size)
        bpy.ops.import_scene.obj(filepath=self.filepath)
        obj = bpy.context.scene.objects[0]
        bpy.context.scene.objects.active = obj
        bpy.ops.object.join()
        bpy.ops.object.mode_set(mode='EDIT', toggle=True)   
        bpy.ops.uv.export_layout(filepath=self.filepath, check_existing=True, export_all=True, modified=False, mode='PNG', size=(size, size), opacity=0.25, tessellated=False)
        bpy.ops.object.mode_set(mode='OBJECT', toggle=True)
        bpy.ops.object.delete(use_global=False)

        print("Time taken:")
        print(time.time() - time_start)
        print("Image size:")
        print(size)

        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

##############################################################
#            IMPORT NEWEST OBJ FROM UNITY FOLDER
##############################################################


class class_import_latest_unity_exported_obj(bpy.types.Operator):

    bl_idname = "object.import_latest_unity_exported_obj"
    bl_label = "Import Latest OBJ Exported From Unity"

    filepath = bpy.props.StringProperty(subtype="FILE_PATH")
    filename = bpy.props.StringProperty(subtype="FILE_NAME")

    def execute(self, context):
        #folder = "D:\\ATS\\ExportedObj\\"
        folder = context.user_preferences.addons[__name__].preferences.obj_import_path
        if (len(folder) == 0):
            folder = "D:\\Projects\\Mosaic\\ExportedObj"
        filepath = max(glob.iglob(folder+'\\*.[Oo][Bb][Jj]'), key=os.path.getmtime)
        bpy.ops.import_scene.obj(filepath=filepath)
        bpy.context.scene.objects.active = bpy.context.scene.objects[0]
        bpy.ops.object.shade_smooth()
        return {'FINISHED'}


##############################################################
#                   AVERAGE EDGE LENGTHS
##############################################################

class class_average_edge_length(bpy.types.Operator):

    bl_idname = "bear.average_edge_length"
    bl_label = "Average Edge Length"

    filepath = bpy.props.StringProperty(subtype="FILE_PATH")
    filename = bpy.props.StringProperty(subtype="FILE_NAME")

    def execute(self, context):
        #folder = "D:\\ATS\\ExportedObj\\"

        obj = bpy.context.edit_object
        me = obj.data

        bm = bmesh.from_edit_mesh(me)

        bm.faces.active = None
        selected_edges = [e for e in bm.edges if e.select is True]

        avg_length = 0

        for edge in selected_edges:
            avg_length += edge.calc_length()

        avg_length /= len(selected_edges)

        for edge in selected_edges:

            diff_from_avg = avg_length - edge.calc_length()
            v0 = edge.verts[0]
            v1 = edge.verts[1]

            direction = v0.co - v1.co
            direction.normalize()

            v0.co += direction * (diff_from_avg * 0.5)
            v1.co -= direction * (diff_from_avg * 0.5)


        bmesh.update_edit_mesh(me, True)

        return {'FINISHED'}


##############################################################
#           COPY MODIFIERS TO LINKED COPIES
##############################################################

class class_copy_modifiers_to_linked_copies(bpy.types.Operator):

    bl_idname = "bear.copy_modifiers_to_linked_copies"
    bl_label = "Modifiers To Linked"

    def execute(self, context):

        original_selection = bpy.context.selected_objects

        bpy.ops.object.select_linked()
        bpy.ops.object.make_links_data(type='MODIFIERS')

        for obj in bpy.context.selected_objects:
            if(obj not in original_selection):
                obj.select = False

        for obj in original_selection:
            obj.select = True

        return {'FINISHED'}

    @classmethod
    def poll(cls, context):
        if(context.active_object is not None and bpy.context.mode == 'OBJECT'):
            return True

##############################################################
#          LINK SELECTED TO ACTIVE AND COPY MODIFIERS
##############################################################

class class_link_and_copy_modifiers(bpy.types.Operator):

    bl_idname = "bear.link_and_copy_modifiers"
    bl_label = "Link & Copy Modifiers"

    def execute(self, context):

        selection = bpy.context.selected_objects
        source = bpy.context.active_object


        for obj in selection:
            obj.data = source.data

        bpy.ops.object.make_links_data(type='MODIFIERS')

        return {'FINISHED'}

    @classmethod
    def poll(cls, context):
        if(context.active_object is not None and bpy.context.mode == 'OBJECT'):
            return True

##############################################################
#          SCALE UVS TO BOUNDS
##############################################################

class class_scale_uvs_to_bounds(bpy.types.Operator):

    bl_idname = "bear.scale_uvs_to_bounds"
    bl_label = "Scale UVs To Bounds"

    def execute(self, context):
        editor = bpy.context.area.spaces[0]
        obj = context.active_object
        me = obj.data
        bm = bmesh.from_edit_mesh(me)

        uv_layer = bm.loops.layers.uv.verify()
        bm.faces.layers.tex.verify()  # currently blender needs both layers.
        
        v_coords = []
        v_coord = None
        
        # adjust UVs


        for f in bm.faces:
            for l in f.loops:
                luv = l[uv_layer]
                if luv.select:
                    if(v_coord is None):
                        v_coord = luv.uv[1]
                    elif(luv.uv[1] > v_coord):
                        if (luv.uv[1] > v_coord):
                            v_coord = luv.uv[1]
        print(v_coord)
        
        editor.cursor_location = [0.0, 0.0]

        v_scale_value = 1 / v_coord

        bpy.ops.transform.resize(value=(1, v_scale_value, 1))

                    # apply the location of the vertex as a UV
                    #luv.uv = l.vert.co.xy

        bmesh.update_edit_mesh(me)

        return {'FINISHED'}

    #@classmethod
    #def poll(cls, context):
    #    if(context.active_object is not None and bpy.context.mode == 'OBJECT'):
    #        return True

##############################################################
#                       FLIP CORNER
##############################################################

class class_flip_corner(bpy.types.Operator):

    bl_idname = "bear.flip_corner"
    bl_label = "Flip Corner"

    def execute(self, context):

        C = bpy.context
        D = bpy.data

        obj = C.edit_object

        bm = bmesh.from_edit_mesh(obj.data)  

        selected_verts = []
        dont_do_these = []

        # Get selected verts
        for vert in bm.verts:
            if(vert.select):
                selected_verts.append(vert)
            
                    
        for vert in selected_verts:
            
            connected_verts = []
            
            bpy.ops.transform.shrink_fatten(value=inset_value, mirror=False, proportional='DISABLED', proportional_edit_falloff='SMOOTH', proportional_size=0.31863)

            for edge in vert.link_edges:
                for v in edge.verts:
                    if v is not vert:
                        connected_verts.append(v)
                        print(v)

        bmesh.update_edit_mesh(obj.data, True)

        return {'FINISHED'}

    @classmethod
    def poll(cls, context):
        if(context.active_object is not None and bpy.context.mode == 'OBJECT'):
            return True

##############################################################
#                      VERTS TO SELECTED
##############################################################

class class_verts_to_selected(bpy.types.Operator):

    bl_idname = "bear.verts_to_selected"
    bl_label = "Verts To Selected"

    def execute(self, context):

        C = bpy.context
        D = bpy.data

        obj = C.edit_object

        original_pivot_mode = bpy.context.space_data.pivot_point

        bpy.ops.wm.context_set_enum(data_path="space_data.pivot_point", value="ACTIVE_ELEMENT")
        
        bpy.ops.transform.resize(value=(0, 0, 0))

        bpy.ops.wm.context_set_enum(data_path="space_data.pivot_point", value=original_pivot_mode)

        return {'FINISHED'}

    @classmethod
    def poll(cls, context):
        if(context.active_object is not None and bpy.context.mode == 'EDIT_MESH'):
            return True

##############################################################
#                  SLICE AT SELECTED VERTICES
##############################################################

class class_slice_at_verts(bpy.types.Operator):
    """Tooltip Exxxxtravaganza!"""
    bl_idname = "bear.slice_at_verts"
    bl_label = "Slice At Verts"

    bisect_direction = bpy.props.EnumProperty(
        name="Direction",
        description="Bisect Direction",
        items=(('X', "X", "X"),
               ('Y', "Y", "Y"),
               ('Z', "Z", "Z"),
               ),
        default="X"
        )

    @classmethod
    def poll(cls, context):
        if(context.active_object is not None and bpy.context.mode == 'EDIT_MESH'):
            return True

    def execute(self, context):
        bisect_mesh(context, self.bisect_direction)
        return {'FINISHED'}


def bisect_mesh(context, direction):
    C = bpy.context
    D = bpy.data

    obj = C.edit_object

    bm = bmesh.from_edit_mesh(obj.data)  

    selected_verts_locations = []
    dont_do_these = []
    # Get selected verts
    for vert in bm.verts:
        if(vert.select):
            selected_verts_locations.append(vert.co)

    b_dir = (1.0, 0.0, 0.0)
    if(direction == 'X'):
        b_dir = (1.0, 0.0, 0.0)
    elif(direction == 'Y'):
        b_dir = (0.0, 1.0, 0.0)
    elif(direction == 'Z'):
        b_dir = (0.0, 0.0, 1.0)
    #else:
    #    return {'FINISHED'}

    for loc in selected_verts_locations:
        loc = obj.matrix_world * loc
        bpy.ops.mesh.select_all(action='SELECT')    
        bpy.ops.mesh.bisect(plane_co=loc, plane_no=(0.0, 1.0, 0.0), use_fill=False)
        bpy.ops.mesh.select_all(action='SELECT')    
        bpy.ops.mesh.bisect(plane_co=loc, plane_no=(1.0, 0.0, 0.0), use_fill=False)
        bpy.ops.mesh.select_all(action='SELECT')    
        bpy.ops.mesh.bisect(plane_co=loc, plane_no=(0.0, 0.0, 1.0), use_fill=False)
        bpy.ops.mesh.select_all(action='DESELECT')

    bmesh.update_edit_mesh(obj.data, True)

        
##############################################################
#            TOGGLE USE NODES BOOL ON MATERIALS
##############################################################

class class_material_toggle_use_nodes(bpy.types.Operator):
    """Material Color To Vertex Color!"""
    bl_idname = "bear.material_toggle_use_nodes"
    bl_label = "Toggle \"Use Nodes\""

    #@classmethod
    #def poll(cls, context):
    #    if(context.active_object is not None and bpy.context.mode == 'EDIT_MESH'):
    #        return True

    def execute(self, context):

        obj = bpy.context.active_object

        for mat in obj.data.materials:
            mat.use_nodes = not mat.use_nodes

        #material_color_to_vertex_color(context, mix_type='COLOR_ONLY')
        return {'FINISHED'}

##############################################################
#                  MATERIAL COLOR TO VERTEX COLOR
##############################################################

class class_material_color_to_vertex_color(bpy.types.Operator):
    """Material Color To Vertex Color!"""
    bl_idname = "bear.material_color_to_vertex_color"
    bl_label = "Material to Vcol"

    #@classmethod
    #def poll(cls, context):
    #    if(context.active_object is not None and bpy.context.mode == 'EDIT_MESH'):
    #        return True

    def execute(self, context):
        print("\nExecuting material_color_to_vertex_color")
        material_color_to_vertex_color(context, mix_type='COLOR_ONLY')
        return {'FINISHED'}

class class_ao_to_vertex_color(bpy.types.Operator):
    """AO To Vertex Color!"""
    bl_idname = "bear.ao_to_vertex_color"
    bl_label = "AO to Vcol"

    #@classmethod
    #def poll(cls, context):
    #    if(context.active_object is not None and bpy.context.mode == 'EDIT_MESH'):
    #        return True

    def execute(self, context):
        print("\nExecuting ao_to_vertex_color")
        material_color_to_vertex_color(context, mix_type='AO_ONLY')
        return {'FINISHED'}

class class_color_ao_mix_color_to_vertex_color(bpy.types.Operator):
    """AO To Vertex Color!"""
    bl_idname = "bear.color_ao_mix_to_vertex_color"
    bl_label = "AO*Color to Vcol"

    #@classmethod
    #def poll(cls, context):
    #    if(context.active_object is not None and bpy.context.mode == 'EDIT_MESH'):
    #        return True

    def execute(self, context):
        print("\nExecuting color_ao_mix_to_vertex_color")
        material_color_to_vertex_color(context, mix_type='COLOR_AO_MIX')
        return {'FINISHED'}

class class_vertex_normals_to_vertex_color(bpy.types.Operator):
    """AO To Vertex Color!"""
    bl_idname = "bear.color_ao_mix_to_vertex_color"
    bl_label = "AO*Color to Vcol"

    #@classmethod
    #def poll(cls, context):
    #    if(context.active_object is not None and bpy.context.mode == 'EDIT_MESH'):
    #        return True

    def execute(self, context):
        print("\nExecuting color_ao_mix_to_vertex_color")
        material_color_to_vertex_color(context, mix_type='COLOR_AO_MIX')
        return {'FINISHED'}


def material_color_to_vertex_color(context, mix_type='COLOR_ONLY', mix_strength=1.0):

    valid_mix_types = ['COLOR_ONLY', 'AO_ONLY', 'COLOR_AO_MIX', 'NORMAL_DIR']

    if(mix_type not in valid_mix_types):
        print("Material color to vertex color: Invalid mix type...")
        return

    C = bpy.context
    S = bpy.context.scene

    print(S.render.engine)

    objects = C.selected_objects
    bpy.ops.object.select_all(action='DESELECT')

    original_render_engine = S.render.engine
    original_bake_type = S.render.bake_type
    original_vcol_bake = S.render.use_bake_to_vertex_color

    S.render.engine = 'BLENDER_RENDER'
    S.render.bake_type = 'TEXTURE'
    S.render.use_bake_to_vertex_color = True

    print("engine =", S.render.engine)
    print("bake_type =", S.render.bake_type)
    print("use_bake_to_vertex_color =", S.render.use_bake_to_vertex_color)

    print("mix_type =", mix_type)
    if(mix_type == 'COLOR_ONLY'):
        print("REGULAR COLOR PLEASE BYE")
        for obj in objects:
            if (obj.type != 'MESH'):
                print(obj.type)
                continue
            obj.select = True

            if(len(obj.data.vertex_colors) > 0):
                for l in obj.data.vertex_colors:
                    print("LAYER NAME:", l.name)
                    if(l.name == "NGon Face-Vertex"):
                        continue
                    obj.data.vertex_colors.remove(l)
            else:
                print("len, " + str(len(obj.data.vertex_colors)))

            print("\nShould be empty:")

            for layer in obj.data.vertex_colors:
                print(layer)

            print("_______")
            
            obj.data.vertex_colors.new("Col")
            obj.data.vertex_colors["Col"].active_render = True
            bpy.ops.object.bake_image()

            obj.select = False

    elif(mix_type == 'AO_ONLY'):
        print("AO ONLY OKAAYYY")
        for obj in objects:
            if (obj.type != 'MESH'):
                continue
            obj.select = True

            if(len(obj.data.vertex_colors) > 0):
                for l in obj.data.vertex_colors:
                    obj.data.vertex_colors.remove(l)

            layers = obj.data.vertex_colors
            
            layers.new("AO")
            layers["AO"].active_render = True
            S.render.bake_type = 'AO'
            
            bpy.ops.object.bake_image()

            obj.select = False
    elif(mix_type == 'NORMAL_DIR'):
        for obj in objects:
            if (obj.type != 'MESH'):
                continue
            obj.select = True
            layers = obj.data.vertex_colors

            if(len(layers) > 0):
                for l in layers:
                    layers.remove(l)
            
            layers.new("Col")
            layers["Col"].active_render = True
            bpy.ops.object.bake_image()

            layers.new("AO")
            layers["AO"].active_render = True
            S.render.bake_type = 'AO'
            
            bpy.ops.object.bake_image()

            layers.new("NRM")

            for i, vert in enumerate(layers["NRM"].data):
                layers["NRM"].data[i].color = obj.data.vertices[i].normal

            layers.remove(layers["Col"])
            layers.remove(layers["AO"])
            layers["NRM"].name = "Col"

            bpy.ops.object.mode_set(mode='VERTEX_PAINT', toggle=True)   
            bpy.ops.paint.vertex_color_smooth()
            bpy.ops.object.mode_set(mode='OBJECT', toggle=True)   
            obj.select = False

    elif(mix_type == 'COLOR_AO_MIX'):
        print("\nCOLOR AO MIX AYYYYY")
        for obj in objects:
            if (obj.type != 'MESH'):
                continue
            obj.select = True
            layers = obj.data.vertex_colors

            if(len(layers) > 0):
                for l in layers:
                    layers.remove(l)
            
            layers.new("Col")
            layers["Col"].active_render = True
            bpy.ops.object.bake_image()

            layers.new("AO")
            layers["AO"].active_render = True
            S.render.bake_type = 'AO'
            
            bpy.ops.object.bake_image()

            layers.new("MIX")

            for i, vert in enumerate(layers["MIX"].data):
                layers["MIX"].data[i].color = (layers["Col"].data[i].color[0] * layers["AO"].data[i].color[0], layers["Col"].data[i].color[1] * layers["AO"].data[i].color[1], layers["Col"].data[i].color[2] * layers["AO"].data[i].color[2])

            layers.remove(layers["Col"])
            layers.remove(layers["AO"])
            layers["MIX"].name = "Col"

            bpy.ops.object.mode_set(mode='VERTEX_PAINT', toggle=True)   
            bpy.ops.paint.vertex_color_smooth()
            bpy.ops.object.mode_set(mode='OBJECT', toggle=True)   
            obj.select = False
    else:
        print("NOOOOOOOOOOOOOOOO")


    S.render.engine = original_render_engine
    S.render.bake_type = original_bake_type
    S.render.use_bake_to_vertex_color = original_vcol_bake

    for obj in objects:
        obj.select = True

def multiply_colors(col1, col2):
    return (col1[0] * col2[0], col1[1] * col2[1], col1[2] * col2[2])


###############################################################
##             VIEWPORT COLOR TO DIFFUSE COLOR
###############################################################
#
#class class_viewport_color_to_diffuse(bpy.types.Operator):
#    """Viewport Color To Diffuse Color!"""
#    bl_idname = "bear.viewport_color_to_diffuse"
#    bl_label = "Viewport color to diffuse"
#
#    #@classmethod
#    #def poll(cls, context):
#    #    if(context.active_object is not None and bpy.context.mode == 'EDIT_MESH'):
#    #        return True
#
#    def execute(self, context):
#        material_color_to_vertex_color(context)
#        return {'FINISHED'}
#
#
#def material_color_to_vertex_color(context):
#    C = bpy.context
#    S = bpy.context.scene
#
#    print(S.render.engine)
#
#    objects = C.selected_objects
#    bpy.ops.object.select_all(action='DESELECT')
#
#    original_render_engine = S.render.engine
#    original_bake_type = S.render.bake_type
#    original_vcol_bake = S.render.use_bake_to_vertex_color
#
#    S.render.engine = 'BLENDER_RENDER'
#    S.render.bake_type = 'TEXTURE'
#    S.render.use_bake_to_vertex_color = True
#
#    print("engine =", S.render.engine)
#    print("bake_type =", S.render.bake_type)
#    print("use_bake_to_vertex_color =", S.render.use_bake_to_vertex_color)
#
#    for obj in objects:
#        obj.select = True
#        if(len(obj.data.vertex_colors) == 0):
#            obj.data.vertex_colors.new()
#        bpy.ops.object.bake_image()
#        obj.select = False
#
#    S.render.engine = original_render_engine
#    S.render.bake_type = original_bake_type
#    S.render.use_bake_to_vertex_color = original_vcol_bake
#
#    for obj in objects:
#        obj.select = True
#

##############################################################
#             VIEWPORT COLOR TO DIFFUSE COLOR
##############################################################

class class_edit_shape_keys(bpy.types.Operator):
    """Viewport Color To Diffuse Color!"""
    bl_idname = "bear.edit_shape_keys"
    bl_label = "Edit Shape Keys"

    #@classmethod
    #def poll(cls, context):
    #    if(context.active_object is not None and bpy.context.mode == 'EDIT_MESH'):
    #        return True

    def execute(self, context):
        edit_shape_keys(context)
        return {'FINISHED'}


def edit_shape_keys(context):
    C = bpy.context
    S = bpy.context.scene

    obj = C.edit_object
    keys = obj.data.shape_keys.key_blocks

    #for i in len(obj.data.shape_keys):
    #    print(obj.data.shape_keys[i])



##############################################################
#             TOOL SHELF BUTTONS
##############################################################
#class property_holder(bpy.types.Scene):

#
# Image editor buttons
#
class class_bbot_uv_buttons(bpy.types.Panel):
    bl_category = "Tools"
    bl_label = "Bear's Bag of Tricks"
    bl_space_type = "IMAGE_EDITOR"
    bl_region_type = "TOOLS"

    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)
        row = col.row()
        row.operator("bear.scale_uvs_to_bounds", text="Scale UVs To Bounds")


#
# Material buttons
#
class class_bbot_material_buttons(bpy.types.Panel):
    bl_label = "Bear's Material Utils"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "material"
 
    def draw(self, context):
        self.layout.operator("bear.material_color_to_vertex_color", text="Material Colors To Vertex Colors")
        self.layout.operator("bear.material_toggle_use_nodes", text="Toggle use_nodes")

#
# Modifier buttons
#
class class_bbot_modifier_buttons(bpy.types.Panel):
    bl_label = "Bear's Material Utils"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "modifiers"
 
    def draw(self, context):
        self.layout.operator("bear.fancy_array_setup")
        self.layout.operator("bear.array_setup")
        self.layout.operator("bear.mirror_setup")
        self.layout.operator("bear.bend_setup")
        self.layout.operator("bear.edit_normals_setup")
        self.layout.operator("bear.double_sided_solidify_setup")

#
# Main buttons
#
class class_bbot_buttons(bpy.types.Panel):
    bl_category = "Custom"
    bl_label = "Bear's Bag of Tricks"
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"


    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)
        col.operator("bear.save_incremental")
        col = layout.column(align=True)
        col.label(text="Transform")
        row = col.row()
        row.operator("object.copy_full_transform", text="Copy")
        row.operator("object.paste_full_transform", text="Paste")
        col = layout.column(align=True)
        col.label(text="Apply Linked Transforms")
        col.operator("object.apply_linked_scale", text="Scale")
        col.operator("object.apply_linked_rotation", text="Rotation")
        col.operator("object.apply_linked_transform", text="Both")
        col = layout.column(align=True)
        col.label(text="Various")
        row = col.row()
        col.operator("uv.uv_layout_from_obj")
        col.operator("object.import_latest_unity_exported_obj")
        col.operator("bear.branches")
        col.operator("bear.unwrap_tubes")
        col.operator("bear.taper_curve_scale")
        col.operator("bear.rename_object")
        #col.operator("bear.sierpinsky_cube")

        col.operator("bear.reset_mesh_rotation")
        col.operator("bear.catmull_edge_slide")
        col.operator("bear.edge_slide_to_center")
        col.operator("bear.bevel_perfect_round")
        col.operator("bear.nice_mesh_spin")
        col.operator("bear.average_edge_length")
        col.operator("bear.copy_modifiers_to_linked_copies")
        col.operator("bear.link_and_copy_modifiers")
        col.operator("bear.camera_setup_ortho")
        col.operator("bear.slice_at_verts")
        col.operator("bear.verts_to_selected")
        col.operator("bear.material_color_to_vertex_color")
        col.operator("bear.ao_to_vertex_color")
        col.operator("bear.color_ao_mix_to_vertex_color")
        #col.prop(bpy.context.active_object, "edit_mode_vertex_color", text="Text???")
        col.operator("bear.set_vertex_colors_from_edit_mode")

        col = layout.column(align=True)
        col.label(text="Modifiers")
        row = col.row()
        col.operator("bear.array_setup")
        col.operator("bear.fancy_array_setup")
        col.operator("bear.mirror_setup")
        col.operator("bear.bend_setup")
        col.operator("bear.edit_normals_setup")
        col.operator("bear.double_sided_solidify_setup")

class class_bbot_menu(bpy.types.Menu):
    bl_label = "Bear class_menu"
    bl_idname = "OBJECT_MT_bear_menu"
    bl_context = "object"

    def draw(self, context):
        layout = self.layout

        layout.operator("bear.edit_shape_keys")
        #layout.operator("wm.open_mainfile")
        #layout.operator("wm.save_as_mainfile").copy = True
#
        #layout.operator("object.modifier_add")
#
        #layout.label(text="Hello world!", icon='WORLD_DATA')

script_classes = [
    class_apply_linked_scale,
    class_apply_linked_rotation,
    class_apply_linked_transform,
    class_average_edge_length,
    class_bbot_buttons,
    class_bbot_menu,
    class_bbot_uv_buttons,
    class_bbot_material_buttons,
    class_bbotaddonprefs,
    class_bear_array_setup,
    class_bear_bend_setup,
    class_bear_branches,
    class_bear_double_sided_solidify_setup,
    class_bear_edit_normals_setup,
    class_bear_fancy_array_setup,
    class_bear_mirror_setup,
    class_bear_rename_object,
    class_bear_sierpinsky_cube,
    class_bear_taper_curve_scale,
    class_bear_unwrap_tubes,
    class_bevel_perfect_round,
    class_buffer_print,
    class_camera_setup_ortho,
    class_catmull_edge_slide,
    class_copy_full_transform,
    class_copy_image_to_temp,
    class_copy_image_to_temp_with_alpha,
    class_copy_modifiers_to_linked_copies,
    class_edge_slide_to_center,
    class_flip_corner,
    class_import_latest_unity_exported_obj,
    class_link_and_copy_modifiers,
    class_nice_mesh_spin,
    class_one_click_ao_bake_from_obj,
    class_paste_full_transform,
    class_reset_mesh_rotation,
    class_save_incremental,
    class_scale_uvs_to_bounds,
    class_slice_at_verts,
    class_toggle_stuff,
    class_verts_to_selected,
    class_uv_layout_from_obj,
    class_material_color_to_vertex_color,
    class_material_toggle_use_nodes,
    class_color_ao_mix_color_to_vertex_color,
    class_ao_to_vertex_color,
    class_bear_set_vertex_colors_from_edit_mode,
    class_bbot_modifier_buttons,
    class_edit_shape_keys,
    #property_holder,
]

def register():
    for c in script_classes:
        bpy.utils.register_class(c)

def unregister():
    for c in script_classes:
        bpy.utils.unregister_class(c)

if __name__ == "__main__":
    register()
