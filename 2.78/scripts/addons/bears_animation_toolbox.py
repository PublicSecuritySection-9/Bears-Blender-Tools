bl_info = {
    "name": "Bear's Animation Toolbox",
    "description": "",
    "author": "Bjørnar Frøyse",
    "version": (0,0,2),
    "blender": (2, 7, 7),
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
from mathutils import Vector
import math
import bmesh
import subprocess
from bpy_extras.io_utils import (ExportHelper,
                                path_reference_mode,
                                )
from datetime import datetime

##############################################################
#             EXPORT FUNCTIONS
##############################################################
def export_single_action(context, filepath):

    armature = bpy.context.active_object
    action = armature.animation_data.action
    scene = bpy.context.scene

    export_action_internal(context, armature, action, scene, filepath)

def export_all_actions(context, filepath):
    start_time = time.clock()
    armature = bpy.context.active_object
    scene = bpy.context.scene

    original_action = armature.animation_data.action
    exported_actions = []
    # Loop through all actions in blend file and export all with fake user flag on
    for action in bpy.data.actions:
        if(action.use_fake_user != True):
            continue
        export_action_internal(context, armature, action, scene, filepath)
        exported_actions.append(action.name)


    armature.animation_data.action = original_action
    print("\nEXPORTED ACTIONS:")
    for action in exported_actions:
        print(action)

    print("--- %s seconds ---" % (time.clock() - start_time))


def export_action_internal(context, armature, action, scene, filepath):
    # Store original values
    original_frame_start = scene.frame_start
    original_frame_end = scene.frame_end

    # Set frame range to action max min
    scene.frame_start = action.frame_range[0]
    scene.frame_end = action.frame_range[1]

    # Prep filename
    filename = filepath + "@" + action.name + ".fbx"

    # Add dummy object
    # This is done to have control over the final hierarchy in Unity.
    bpy.ops.object.empty_add(type='PLAIN_AXES')
    empty = bpy.context.scene.objects[-1]
    empty.name = "_DUMMY"

    # Prep selection for export
    empty.select = True
    armature.select = True

    armature.animation_data.action = action

    export_selected(filename)

    # Restore original values
    scene.frame_start = int(original_frame_start)
    scene.frame_end = int(original_frame_end)

    # Delete dummy object
    armature.select = False
    bpy.ops.object.delete()

    armature.select = True
    bpy.context.scene.objects.active = armature


class class_export_single_action(bpy.types.Operator, ExportHelper):
    """Toggle deform status for bones not required by mecanim"""
    bl_idname = "bear.export_single_action"
    bl_label = "Export Current Action"
    filename_ext = ""

    filepath = ""

    @classmethod
    def poll(cls, context):
        return len(context.selected_objects) is not 0

    def execute(self, context):
        export_single_action(context, self.filepath)
        return {'FINISHED'}

class class_export_all_actions(bpy.types.Operator, ExportHelper):
    """Toggle deform status for bones not required by mecanim"""
    bl_idname = "bear.export_all_actions"
    bl_label = "Export All Actions"
    filename_ext = ""

    filepath = ""

    @classmethod
    def poll(cls, context):
        return len(context.selected_objects) is not 0

    def execute(self, context):
        export_all_actions(context, self.filepath)
        return {'FINISHED'}

def export_rigged_character(context, filepath):
    armature = None
    characterMesh = None
    C = bpy.context

    original_selected_objects = C.selected_objects

    activeObject = C.active_object

    for obj in C.selected_objects:
        obj.select = False

    if (activeObject.type == 'MESH'):
        characterMesh = activeObject
        for modifier in activeObject.modifiers:
            if (modifier.type == 'ARMATURE'):
                armature = modifier.object
    elif (activeObject.type == 'ARMATURE'):
        armature = activeObject
        bpy.ops.object.select_grouped(extend=False, type='CHILDREN')
        for obj in C.selected_objects:
            for modifier in obj.modifiers:
                if(modifier.type == 'ARMATURE' and modifier.object == armature):
                    characterMesh = obj

    print("CHAR MESH", type(characterMesh.data))
    print("ARMATURE", type(armature.data))

    original_pose_position = armature.data.pose_position
    armature.data.pose_position = 'REST'

    characterMesh.select = True

    #bpy.ops.bear.material_color_to_vertex_color()

    old_materials = [mat for mat in characterMesh.data.materials]
    characterMesh.data.materials.clear()

    armature.select = True

    filename = filepath.replace(".fbx", "").replace(".FBX", "") + ".fbx"
    export_selected(filename, False)

    armature.data.pose_position = original_pose_position
    armature.select = False

    for mat in old_materials:
        characterMesh.data.materials.append(mat)

    characterMesh.select = False

    for obj in original_selected_objects:
        obj.select = True

    bpy.context.scene.objects.active = activeObject

class class_export_rigged_character(bpy.types.Operator, ExportHelper):
    """Toggle deform status for bones not required by mecanim"""
    bl_idname = "bear.export_rigged_character"
    bl_label = "Export Rigged Character"
    filename_ext = ""

    filepath = ""

    @classmethod
    def poll(cls, context):
        return len(context.selected_objects) is not 0

    def execute(self, context):
        export_rigged_character(context, self.filepath)
        return {'FINISHED'}

def export_selected(filename, include_animation=True, override_bake_anim_step=1.0):
    bpy.ops.export_scene.fbx(
    filepath=filename,
    check_existing=True,
    axis_forward='-Z',
    axis_up='Y',
    filter_glob="*.fbx",
    version='BIN7400',
    ui_tab='MAIN',
    use_selection=True,
    global_scale=1.0,
    apply_unit_scale=False, #Set to false to avoid rig being scaled to 100 in Unity
    bake_space_transform=True,
    object_types={'ARMATURE',
    #'CAMERA',
    'EMPTY',
    #'LAMP',
    'MESH',
    #'OTHER'
    },
    use_mesh_modifiers=True,
    mesh_smooth_type='OFF',
    use_mesh_edges=False,
    use_tspace=False,
    use_custom_props=False,
    add_leaf_bones=False, #Disabledee
    primary_bone_axis='Y',
    secondary_bone_axis='X',
    use_armature_deform_only=True,
    armature_nodetype='NULL',
    bake_anim=True,
    bake_anim_use_all_bones=True,
    bake_anim_use_nla_strips=False,
    bake_anim_use_all_actions=False,
    bake_anim_force_startend_keying=True,
    bake_anim_step=override_bake_anim_step,
    bake_anim_simplify_factor=0.0,
    use_anim=include_animation,
    use_anim_action_all=False,
    use_default_take=False,
    use_anim_optimize=False,
    anim_optimize_precision=1.0,
    path_mode='AUTO',
    embed_textures=False,
    batch_mode='OFF',
    use_batch_own_dir=True,
    use_metadata=True)

##############################################################
#            RIG SETUP FUNCTIONS
##############################################################

def setup_deformable_bones(context):

    obj = bpy.context.active_object
    
    bones_to_un_deform = ["DEF-chest", "DEF-f_index.01.L.01", "DEF-f_index.01.L.02", "DEF-f_index.01.R.01",
    "DEF-f_index.01.R.02", "DEF-f_index.02.L", "DEF-f_index.02.R", "DEF-f_index.03.L", "DEF-f_index.03.R",
    "DEF-f_middle.01.L.01", "DEF-f_middle.01.L.02", "DEF-f_middle.01.R.01", "DEF-f_middle.01.R.02", "DEF-f_middle.02.L",
    "DEF-f_middle.02.R", "DEF-f_middle.03.L", "DEF-f_middle.03.R", "DEF-f_pinky.01.L.01", "DEF-f_pinky.01.L.02",
    "DEF-f_pinky.01.R.01", "DEF-f_pinky.01.R.02", "DEF-f_pinky.02.L", "DEF-f_pinky.02.R", "DEF-f_pinky.03.L",
    "DEF-f_pinky.03.R", "DEF-f_ring.01.L.01", "DEF-f_ring.01.L.02", "DEF-f_ring.01.R.01", "DEF-f_ring.01.R.02",
    "DEF-f_ring.02.L", "DEF-f_ring.02.R", "DEF-f_ring.03.L", "DEF-f_ring.03.R", "DEF-foot.L", "DEF-foot.R",
    "DEF-forearm.01.L", "DEF-forearm.01.R", "DEF-forearm.02.L", "DEF-forearm.02.R", "DEF-hand.L", "DEF-hand.R",
    "DEF-head", "DEF-hips", "DEF-neck", "DEF-palm.01.L", "DEF-palm.01.R", "DEF-palm.02.L", "DEF-palm.02.R",
    "DEF-palm.03.L", "DEF-palm.03.R", "DEF-palm.04.L", "DEF-palm.04.R", "DEF-shin.01.L", "DEF-shin.01.R",
    "DEF-shin.02.L", "DEF-shin.02.R", "DEF-shoulder.L", "DEF-shoulder.R", "DEF-spine", "DEF-thigh.01.L",
    "DEF-thigh.01.R", "DEF-thigh.02.L", "DEF-thigh.02.R", "DEF-thumb.01.L.01", "DEF-thumb.01.L.02", "DEF-thumb.01.R.01",
    "DEF-thumb.01.R.02", "DEF-thumb.02.L", "DEF-thumb.02.R", "DEF-thumb.03.L", "DEF-thumb.03.R", "DEF-tie.00",
    "DEF-tie.01", "DEF-tie.02", "DEF-toe.L", "DEF-toe.R", "DEF-upper_arm.01.L", "DEF-upper_arm.01.R", "DEF-upper_arm.02.L",
    "DEF-upper_arm.02.R", "ORG-heel.02.L", "ORG-heel.02.R", "ORG-heel.L", "ORG-heel.R", "ORG-palm.01.L", "ORG-palm.01.R",
    "ORG-palm.02.L", "ORG-palm.02.R", "ORG-palm.03.L", "ORG-palm.03.R", "ORG-palm.04.L", "ORG-palm.04.R"
    ]

    bones_to_deform = ["ORG-chest", "ORG-f_index.01.L", "ORG-f_index.01.R", "ORG-f_index.02.L", "ORG-f_index.02.R",
    "ORG-f_index.03.L", "ORG-f_index.03.R", "ORG-f_middle.01.L", "ORG-f_middle.01.R", "ORG-f_middle.02.L",
    "ORG-f_middle.02.R", "ORG-f_middle.03.L", "ORG-f_middle.03.R", "ORG-f_pinky.01.L", "ORG-f_pinky.01.R",
    "ORG-f_pinky.02.L", "ORG-f_pinky.02.R", "ORG-f_pinky.03.L", "ORG-f_pinky.03.R", "ORG-f_ring.01.L",
    "ORG-f_ring.01.R", "ORG-f_ring.02.L", "ORG-f_ring.02.R", "ORG-f_ring.03.L", "ORG-f_ring.03.R", "ORG-foot.L",
    "ORG-foot.R", "ORG-forearm.L", "ORG-forearm.R", "ORG-hand.L", "ORG-hand.R", "ORG-head", "ORG-hips", "ORG-neck",
    "ORG-shin.L", "ORG-shin.R", "ORG-shoulder.L", "ORG-shoulder.R", "ORG-spine", "ORG-thigh.L", "ORG-thigh.R",
    "ORG-thumb.01.L", "ORG-thumb.01.R", "ORG-thumb.02.L", "ORG-thumb.02.R", "ORG-thumb.03.L", "ORG-thumb.03.R",
    "ORG-toe.L", "ORG-toe.R", "ORG-upper_arm.L", "ORG-upper_arm.R", "EXT-jaw", "EXT-eye.R", "EXT-eye.L",
    "EXT-tie.01", "EXT-tie.02", "EXT-tie.03"
    ]

    print("Disabling deformation for bones...")
    for bone in bones_to_un_deform:
        try:
            obj.data.bones[bone].use_deform = False
            print(bone, "...OK!")
        except:
            print("Could not find bone", bone)
            pass
    
    print("Enabling deformation for bones...")
    for bone in bones_to_deform:
        try:
            obj.data.bones[bone].use_deform = True
            print(bone, "...OK!")
        except:
            print("Could not find bone", bone)
            pass

class class_setup_deformable_bones(bpy.types.Operator):
    """Toggle deform status for bones not required by mecanim"""
    bl_idname = "bear.setup_deformable_bones"
    bl_label = "Toggle Non-mecanim Deform"

    @classmethod
    def poll(cls, context):
        return len(context.selected_objects) is not 0

    def execute(self, context):
        setup_deformable_bones(context)
        return {'FINISHED'}

##############################################################
#            HIDE/UNHIDE UNINTERESTING BONES
##############################################################

def hide_unused_bones(context):

    obj = bpy.context.active_object
    
    bones_to_hide = ["DEF-chest", "DEF-f_index.01.L.01", "DEF-f_index.01.L.02", "DEF-f_index.01.R.01", "DEF-f_index.01.R.02",
    "DEF-f_index.02.L", "DEF-f_index.02.R", "DEF-f_index.03.L", "DEF-f_index.03.R", "DEF-f_middle.01.L.01", "DEF-f_middle.01.L.02",
    "DEF-f_middle.01.R.01", "DEF-f_middle.01.R.02", "DEF-f_middle.02.L", "DEF-f_middle.02.R", "DEF-f_middle.03.L", "DEF-f_middle.03.R",
    "DEF-f_pinky.01.L.01", "DEF-f_pinky.01.L.02", "DEF-f_pinky.01.R.01", "DEF-f_pinky.01.R.02", "DEF-f_pinky.02.L", "DEF-f_pinky.02.R",
    "DEF-f_pinky.03.L", "DEF-f_pinky.03.R", "DEF-f_ring.01.L.01", "DEF-f_ring.01.L.02", "DEF-f_ring.01.R.01", "DEF-f_ring.01.R.02",
    "DEF-f_ring.02.L", "DEF-f_ring.02.R", "DEF-f_ring.03.L", "DEF-f_ring.03.R", "DEF-foot.L", "DEF-foot.R", "DEF-forearm.01.L", "DEF-forearm.01.R",
    "DEF-forearm.02.L", "DEF-forearm.02.R", "DEF-hand.L", "DEF-hand.R", "DEF-head", "DEF-hips", "DEF-neck", "DEF-palm.01.L", "DEF-palm.01.R",
    "DEF-palm.02.L", "DEF-palm.02.R", "DEF-palm.03.L", "DEF-palm.03.R", "DEF-palm.04.L", "DEF-palm.04.R", "DEF-shin.01.L", "DEF-shin.01.R", "DEF-shin.02.L",
    "DEF-shin.02.R", "DEF-shoulder.L", "DEF-shoulder.R", "DEF-spine", "DEF-thigh.01.L", "DEF-thigh.01.R", "DEF-thigh.02.L", "DEF-thigh.02.R",
    "DEF-thumb.01.L.01", "DEF-thumb.01.L.02", "DEF-thumb.01.R.01", "DEF-thumb.01.R.02", "DEF-thumb.02.L", "DEF-thumb.02.R", "DEF-thumb.03.L",
    "DEF-thumb.03.R", "DEF-tie.00", "DEF-tie.01", "DEF-tie.02", "DEF-toe.L", "DEF-toe.R", "DEF-upper_arm.01.L", "DEF-upper_arm.01.R", "DEF-upper_arm.02.L",
    "DEF-upper_arm.02.R", "ORG-heel.02.L", "ORG-heel.02.R", "ORG-heel.L", "ORG-heel.R", "ORG-palm.01.L", "ORG-palm.01.R", "ORG-palm.02.L",
    "ORG-palm.02.R", "ORG-palm.03.L", "ORG-palm.03.R", "ORG-palm.04.L", "ORG-palm.04.R", "MCH-elbow_hose_p.R", "elbow_hose.R", "MCH-forearm_hose_p.R",
    "forearm_hose.R", "MCH-forearm_hose_end_p.R", "forearm_hose_end.R", "MCH-upper_arm_hose_end_p.R", "upper_arm_hose_end.R", "MCH-upper_arm_hose_p.R",
    "upper_arm_hose.R", "MCH-elbow_hose_p.L", "elbow_hose.L", "MCH-forearm_hose_p.L", "forearm_hose.L", "MCH-forearm_hose_end_p.L", "forearm_hose_end.L",
    "MCH-upper_arm_hose_end_p.L", "upper_arm_hose_end.L", "MCH-upper_arm_hose_p.L", "upper_arm_hose.L", "MCH-knee_hose_p.L", "knee_hose.L", "MCH-shin_hose_p.L",
    "shin_hose.L", "MCH-shin_hose_end_p.L", "shin_hose_end.L", "MCH-thigh_hose_end_p.L", "thigh_hose_end.L", "MCH-thigh_hose_p.L", "thigh_hose.L",
    "MCH-knee_hose_p.R", "knee_hose.R", "MCH-shin_hose_p.R", "shin_hose.R", "MCH-shin_hose_end_p.R", "shin_hose_end.R", "MCH-thigh_hose_end_p.R",
    "thigh_hose_end.R", "MCH-thigh_hose_p.R", "thigh_hose.R"]

    bones_to_unhide = ["ORG-chest", "ORG-f_index.01.L", "ORG-f_index.01.R", "ORG-f_index.02.L", "ORG-f_index.02.R", "ORG-f_index.03.L",
    "ORG-f_index.03.R", "ORG-f_middle.01.L", "ORG-f_middle.01.R", "ORG-f_middle.02.L", "ORG-f_middle.02.R", "ORG-f_middle.03.L",
    "ORG-f_middle.03.R", "ORG-f_pinky.01.L", "ORG-f_pinky.01.R", "ORG-f_pinky.02.L", "ORG-f_pinky.02.R", "ORG-f_pinky.03.L", "ORG-f_pinky.03.R",
    "ORG-f_ring.01.L", "ORG-f_ring.01.R", "ORG-f_ring.02.L", "ORG-f_ring.02.R", "ORG-f_ring.03.L", "ORG-f_ring.03.R", "ORG-foot.L", "ORG-foot.R",
    "ORG-forearm.L", "ORG-forearm.R", "ORG-hand.L", "ORG-hand.R", "ORG-head", "ORG-hips", "ORG-neck", "ORG-shin.L", "ORG-shin.R", "ORG-shoulder.L",
    "ORG-shoulder.R", "ORG-spine", "ORG-thigh.L", "ORG-thigh.R", "ORG-thumb.01.L", "ORG-thumb.01.R", "ORG-thumb.02.L", "ORG-thumb.02.R",
    "ORG-thumb.03.L", "ORG-thumb.03.R", "ORG-toe.L", "ORG-toe.R", "ORG-upper_arm.L", "ORG-upper_arm.R", "EXT-jaw", "EXT-eye.R", "EXT-eye.L",
    "EXT-tie.01", "EXT-tie.02", "EXT-tie.03"]

    for bone in bones_to_hide:
        try:
            obj.data.bones[bone].hide = True
        except:
            pass

    for bone in bones_to_unhide:
        try:
            obj.data.bones[bone].hide = False
        except:
            pass

class class_hide_unused_bones(bpy.types.Operator):
    """Hide/unhide bones that aren't used when using mecanim"""
    bl_idname = "bear.hide_unused_bones"
    bl_label = "Hide Bones"

    @classmethod
    def poll(cls, context):
        return len(context.selected_objects) is not 0

    def execute(self, context):
        hide_unused_bones(context)
        return {'FINISHED'}

##############################################################
#                  ADD EXTRA BONES
##############################################################

def add_extra_bones(context):

    obj = bpy.context.active_object

    ext = "EXT"
    att = "ATTACH"
    aim = "AIM"

    head = obj.data.edit_bones["ORG-head"]
    neck = obj.data.edit_bones["ORG-head"]
    root = obj.data.edit_bones["root"]
    handR = obj.data.edit_bones["ORG-hand.R"]
    handL = obj.data.edit_bones["ORG-hand.L"]

    jaw = add_bone(context, obj,            head.head + Vector((0, -0.1, 0)),       head.head + Vector((0, -0.15, 0)),          0,          ext, "jaw", head, False)
    eyeR = add_bone(context, obj,           head.head + Vector((-0.036, -0.1, 0.1)),head.head + Vector((-0.036, -0.15, 0.1)),   0,          ext, "eye.R", head, False)
    eyeL = add_bone(context, obj,           head.head + Vector((0.036, -0.1, 0.1)), head.head + Vector((0.036, -0.15, 0.1)),    0,          ext, "eye.L", head, False)
  
    interactionR = add_bone(context, obj,   root.head + Vector((-1, 0, 1)),         root.head + Vector((-1, -0.1, 1)),          0,          ext, "interaction.R", root, False)
    interactionL = add_bone(context, obj,   root.head + Vector((1, 0, 1)),          root.head + Vector((1, -0.1, 1)),           0,          ext, "interaction.L", root, False)
   
    aimR = add_bone(context, obj,           root.head + Vector((-1, 0, 1.5)),       root.head + Vector((-1, -0.1, 1.5)),        0,          aim, "hand.R", root, True)
    aimL = add_bone(context, obj,           root.head + Vector((1, 0, 1.5)),        root.head + Vector((1, -0.1, 1.5)),         0,          aim, "hand.L", root, True)
   
    attachHandR = add_bone(context, obj,    handR.tail,                             handR.vector * 0.3 + handR.tail,            handR.roll, att, "hand.R", handR, True)
    attachHandL = add_bone(context, obj,    handL.tail,                             handL.vector * 0.3 + handL.tail,            handL.roll, att, "hand.L", handL, True)
    attachHead =  add_bone(context, obj,    head.tail,                              head.vector * 0.3 + head.tail,              head.roll,  att, "head",   head, True)
    
def add_bone(context, obj, head, tail, roll, prefix, bone_name, parent, overwrite):
   
    name = "{0}-{1}".format(prefix, bone_name)
    bone = None
    newBone = False

    try:
        bone = obj.data.edit_bones[name]
    except KeyError as e:
        bone = obj.data.edit_bones.new(name)
        newBone = True
        print("Added new bone:", bone)
    else:
        print("Found existing bone:", bone)

    if(newBone or overwrite):
        bone.head = Vector(head)
        bone.tail = Vector(tail)
        bone.parent = parent
        bone.roll = roll
        bone.layers[23] = True
        bone.layers[31] = True

    bone.select = True
    bone.select_head = True
    bone.select_tail = True
    return bone


class class_add_extra_bones(bpy.types.Operator):
    """Add extra bones (eyes, jaw)"""
    bl_idname = "bear.add_extra_bones"
    bl_label = "Add Extra Bones"

    @classmethod
    def poll(cls, context):
        return bpy.context.mode == 'EDIT_ARMATURE'

    def execute(self, context):
        add_extra_bones(context)
        return {'FINISHED'}


##############################################################
#               MAKE PLAYBLAST
##############################################################

def make_playblast(context, scene, action, output_folder):
    
    # ORIGINAL SETTINGS
    original_output_path = scene.render.filepath

    original_image_settings_file_format = scene.render.image_settings.file_format
    original_ffmpeg_format = scene.render.ffmpeg.format

    original_frame_start = scene.frame_start
    original_frame_end = scene.frame_end

    original_stamp_note_text = scene.render.stamp_note_text
    original_use_stamp = scene.render.use_stamp

    # NEW DATA
    blend_name = bpy.path.basename(bpy.context.blend_data.filepath).split(".")[0]
    timestamp = datetime.today().strftime('%y%m%d_%H%M%S')

    final_path = output_folder + blend_name + "_" + action.name + "_" + timestamp + "_.mp4"

    # APPLY SETTINGS
    scene.render.filepath = final_path
    
    scene.render.image_settings.file_format = 'H264'
    scene.render.ffmpeg.format = 'MPEG4'
    scene.render.ffmpeg.codec = 'H264'
    scene.render.ffmpeg.audio_codec = 'AAC'

    scene.render.use_stamp = True

    scene.render.use_stamp_note = True
    scene.render.use_stamp_time = False
    scene.render.use_stamp_render_time = False
    scene.render.use_stamp_camera = False
    scene.render.use_stamp_scene = False

    scene.render.stamp_note_text = blend_name + "@" + action.name

    scene.frame_start = action.frame_range[0]
    scene.frame_end = action.frame_range[1]

    print("Rendering playblast.\n"+
        "Output: " + final_path + "\n" +
        "Frame range: " + str(action.frame_range)
        )

    # DO THE THINGS
    bpy.ops.render.opengl(animation=True)

    # RESTORE ORIGINAL SETTINGS
    scene.render.filepath = original_output_path
    
    scene.render.image_settings.file_format = original_image_settings_file_format
    scene.render.ffmpeg.format = original_ffmpeg_format

    scene.frame_start = int(original_frame_start)
    scene.frame_end = int(original_frame_end)

    scene.render.stamp_note_text = original_stamp_note_text
    scene.render.use_stamp = original_use_stamp


class class_make_playblast(bpy.types.Operator):
    """Render playblast to folder beside blend file"""
    bl_idname = "bear.render_playblast"
    bl_label = "Export Playblast"

    @classmethod
    def poll(cls, context):
        return context.active_object.type == 'ARMATURE'

    def execute(self, context):
        output_folder = bpy.path.abspath("//") + "Playblast\\"
 
        scene = bpy.context.scene

        armature = bpy.context.active_object
        action = armature.animation_data.action

        make_playblast(context, scene, action, output_folder)

        subprocess.Popen('explorer ' + output_folder)

        return {'FINISHED'}

class class_make_playblast_from_all_actions(bpy.types.Operator):
    """Render playblast to folder beside blend file"""
    bl_idname = "bear.render_playblast_all"
    bl_label = "Export Playblast (ALL, VERY SLOW)"

    @classmethod
    def poll(cls, context):
        return context.active_object.type == 'ARMATURE'

    def execute(self, context):
        bpy.ops.wm.save_mainfile()

        start_time = time.clock()

        timestamp = datetime.today().strftime('%y%m%d_%H%M%S')

        output_folder = bpy.path.abspath("//") + "Playblast\\export_all_" + timestamp + "\\"

        subprocess.Popen('explorer ' + output_folder)
        armature = bpy.context.active_object
        scene = bpy.context.scene

        original_action = armature.animation_data.action
        exported_actions = []
        # Loop through all actions in blend file and export all with fake user flag on
        for action in bpy.data.actions:
            if(action.use_fake_user != True):
                continue
            armature.animation_data.action = action;
            make_playblast(context, scene, action, output_folder)
            exported_actions.append(action.name)

        armature.animation_data.action = original_action
        print("\nEXPORTED PLAYBLASTS:")
        for action in exported_actions:
            print(action)

        print("--- %s seconds ---" % (time.clock() - start_time))
        return {'FINISHED'}

def set_frame_range_from_action(action):
    scene = bpy.context.scene

    scene.frame_start = action.frame_range[0]
    scene.frame_end = action.frame_range[1]


##############################################################
#               VERIFY RIG COMPATIBILITY
##############################################################

def verify_rig_integrity(context):

    print("Not implemented yet")

class class_verify_rig_compatibility(bpy.types.Operator):
    """Verify rig compatibility with mecanim"""
    bl_idname = "bear.verify_rig_integrity"
    bl_label = "Verify"

    @classmethod
    def poll(cls, context):
        return len(context.selected_objects) is not 0

    def execute(self, context):
        verify_rig_integrity(context)
        return {'FINISHED'}

##############################################################
#               ALIGN FUNCTIONS
##############################################################


class class_align_objects(bpy.types.Operator):
    bl_idname = "bear.align_objects"
    bl_label = "Align Objects"

    @classmethod
    def poll(cls, context):
        return len(context.selected_objects) is not 0

    def execute(self, context):
        align_objects(context)

        return {'FINISHED'}


def align_objects(context):
    print("Aligning objects")
    C = bpy.context
    activeObject = C.active_object
    activePoseBone = C.active_pose_bone

    alignTarget = None

    mode = ""

    if(activePoseBone is not None):
        mode = "TO_POSE_BONE"
        alignTarget = activePoseBone
    elif activeObject is not None:
        mode = "TO_OBJECT"
        alignTarget = activeObject

    objectsToAlign = [obj for obj in C.selected_objects if obj != C.active_object]

    poseBonesToAlign = []
    if(activePoseBone is not None):
        poseBonesToAlign = [bone for bone in C.selected_pose_bones if bone != activePoseBone]

    if(alignTarget is activePoseBone):
        for obj in objectsToAlign:
            obj.matrix_world = alignTarget.matrix

        for bone in poseBonesToAlign:
            bone.matrix = alignTarget.matrix

    elif(alignTarget is activeObject):
        for obj in objectsToAlign:
            obj.matrix_world = alignTarget.matrix_world


class class_align_pose_bones(bpy.types.Operator):
    bl_idname = "bear.align_pose_bones"
    bl_label = "Align Pose Bones To Object"

    @classmethod
    def poll(cls, context):
        if (bpy.context.active_pose_bone is not None and len(bpy.context.selected_objects) == 2):
            return True
        elif (bpy.context.active_pose_bone is not None and len(bpy.context.selected_pose_bones) > 1):
            return True
        else:
            return False

    def execute(self, context):
        align_pose_bones(context)

        return {'FINISHED'}


def align_pose_bones(context):
    print("Aligning pose bones")
    C = bpy.context
    activeObject = C.active_object
    activePoseBone = C.active_pose_bone

    alignTarget = None

    mode = ""

    sel = len(C.selected_objects)

    otherObject = None
    print(sel)
    if (sel == 2):
        otherObject = [obj for obj in C.selected_objects if obj != activeObject][0]
        alignTarget = otherObject
    elif (sel <= 1 and activePoseBone is not None):
        alignTarget = activePoseBone
    else:
        print("Dunno what to do... Please select only ONE other object. You have currently selected", len(C.selected_objects) - 1)


    if(alignTarget == otherObject and otherObject is not None):
        poseBonesToAlign = [bone for bone in C.selected_pose_bones]

        for bone in poseBonesToAlign:
            bone.matrix = alignTarget.matrix_world


    elif(alignTarget == activePoseBone):
        poseBonesToAlign = [bone for bone in C.selected_pose_bones if bone != activePoseBone]

        for bone in poseBonesToAlign:
            scl = bone.scale
            bone.matrix = alignTarget.matrix
            bone.scale = scl

##############################################################
#             TOOL SHELF BUTTONS
##############################################################


class class_bear_rig_buttons(bpy.types.Panel):
    bl_category = "Custom"
    bl_label = "Animation Toolbox"
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"

    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)
        col.label(text="Align")
        col.operator("bear.align_objects")
        col.operator("bear.align_pose_bones")

        col = layout.column(align=True)
        col.label(text="Export")
        col.operator("bear.export_single_action")
        col.operator("bear.export_all_actions")
        col.separator()
        col.operator("bear.export_rigged_character")
        col.label(text="Render")
        col.operator("bear.render_playblast")
        col.operator("bear.render_playblast_all")
        col.label(text="Setup")
        row = col.row()
        col.operator("bear.setup_deformable_bones")
        col.operator("bear.hide_unused_bones")
        col.operator("bear.add_extra_bones")
        #col.operator("bear.verify_rig_integrity")

script_classes = [
    class_bear_rig_buttons,
    class_verify_rig_compatibility,
    class_setup_deformable_bones,
    class_hide_unused_bones,
    class_add_extra_bones,
    class_export_single_action,
    class_export_all_actions,
    class_export_rigged_character,
    class_align_objects,
    class_align_pose_bones,
    class_make_playblast,
    class_make_playblast_from_all_actions,
]

def register():
    for c in script_classes:
        bpy.utils.register_class(c)

def unregister():
    for c in script_classes:
        bpy.utils.unregister_class(c)

if __name__ == "__main__":
    register()
