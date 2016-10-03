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
    armature = bpy.context.active_object
    scene = bpy.context.scene

    original_action = armature.animation_data.action

    # Loop through all actions in blend file and export all with fake user flag on
    for action in bpy.data.actions:
        if(action.use_fake_user != True):
            continue
        export_action_internal(context, armature, action, scene, filepath)

    armature.animation_data.action = original_action

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

    armature.data.pose_position = 'POSE'
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
    
    bones_to_un_deform = ["DEF-chest", "DEF-f_index.01.L.01", "DEF-f_index.01.L.02", "DEF-f_index.01.R.01", "DEF-f_index.01.R.02", "DEF-f_index.02.L", "DEF-f_index.02.R", "DEF-f_index.03.L", "DEF-f_index.03.R", "DEF-f_middle.01.L.01", "DEF-f_middle.01.L.02", "DEF-f_middle.01.R.01", "DEF-f_middle.01.R.02", "DEF-f_middle.02.L", "DEF-f_middle.02.R", "DEF-f_middle.03.L", "DEF-f_middle.03.R", "DEF-f_pinky.01.L.01", "DEF-f_pinky.01.L.02", "DEF-f_pinky.01.R.01", "DEF-f_pinky.01.R.02", "DEF-f_pinky.02.L", "DEF-f_pinky.02.R", "DEF-f_pinky.03.L", "DEF-f_pinky.03.R", "DEF-f_ring.01.L.01", "DEF-f_ring.01.L.02", "DEF-f_ring.01.R.01", "DEF-f_ring.01.R.02", "DEF-f_ring.02.L", "DEF-f_ring.02.R", "DEF-f_ring.03.L", "DEF-f_ring.03.R", "DEF-foot.L", "DEF-foot.R", "DEF-forearm.01.L", "DEF-forearm.01.R", "DEF-forearm.02.L", "DEF-forearm.02.R", "DEF-hand.L", "DEF-hand.R", "DEF-head", "DEF-hips", "DEF-neck", "DEF-palm.01.L", "DEF-palm.01.R", "DEF-palm.02.L", "DEF-palm.02.R", "DEF-palm.03.L", "DEF-palm.03.R", "DEF-palm.04.L", "DEF-palm.04.R", "DEF-shin.01.L", "DEF-shin.01.R", "DEF-shin.02.L", "DEF-shin.02.R", "DEF-shoulder.L", "DEF-shoulder.R", "DEF-spine", "DEF-thigh.01.L", "DEF-thigh.01.R", "DEF-thigh.02.L", "DEF-thigh.02.R", "DEF-thumb.01.L.01", "DEF-thumb.01.L.02", "DEF-thumb.01.R.01", "DEF-thumb.01.R.02", "DEF-thumb.02.L", "DEF-thumb.02.R", "DEF-thumb.03.L", "DEF-thumb.03.R", "DEF-tie.00", "DEF-tie.01", "DEF-tie.02", "DEF-toe.L", "DEF-toe.R", "DEF-upper_arm.01.L", "DEF-upper_arm.01.R", "DEF-upper_arm.02.L", "DEF-upper_arm.02.R", "ORG-heel.02.L", "ORG-heel.02.R", "ORG-heel.L", "ORG-heel.R", "ORG-palm.01.L", "ORG-palm.01.R", "ORG-palm.02.L", "ORG-palm.02.R", "ORG-palm.03.L", "ORG-palm.03.R", "ORG-palm.04.L", "ORG-palm.04.R"]
    bones_to_deform = ["ORG-chest", "ORG-f_index.01.L", "ORG-f_index.01.R", "ORG-f_index.02.L", "ORG-f_index.02.R", "ORG-f_index.03.L", "ORG-f_index.03.R", "ORG-f_middle.01.L", "ORG-f_middle.01.R", "ORG-f_middle.02.L", "ORG-f_middle.02.R", "ORG-f_middle.03.L", "ORG-f_middle.03.R", "ORG-f_pinky.01.L", "ORG-f_pinky.01.R", "ORG-f_pinky.02.L", "ORG-f_pinky.02.R", "ORG-f_pinky.03.L", "ORG-f_pinky.03.R", "ORG-f_ring.01.L", "ORG-f_ring.01.R", "ORG-f_ring.02.L", "ORG-f_ring.02.R", "ORG-f_ring.03.L", "ORG-f_ring.03.R", "ORG-foot.L", "ORG-foot.R", "ORG-forearm.L", "ORG-forearm.R", "ORG-hand.L", "ORG-hand.R", "ORG-head", "ORG-hips", "ORG-neck", "ORG-shin.L", "ORG-shin.R", "ORG-shoulder.L", "ORG-shoulder.R", "ORG-spine", "ORG-thigh.L", "ORG-thigh.R", "ORG-thumb.01.L", "ORG-thumb.01.R", "ORG-thumb.02.L", "ORG-thumb.02.R", "ORG-thumb.03.L", "ORG-thumb.03.R", "ORG-toe.L", "ORG-toe.R", "ORG-upper_arm.L", "ORG-upper_arm.R", "EXTRA-jaw", "EXTRA-eye.R", "EXTRA-eye.L", "OlavChest", "OlavLeftIndex1", "OlavRightIndex1", "OlavLeftIndex2", "OlavRightIndex2", "OlavLeftIndex3", "OlavRightIndex3", "OlavLeftMiddle1", "OlavRightMiddle1", "OlavLeftMiddle2", "OlavRightMiddle2", "OlavLeftMiddle3", "OlavRightMiddle3", "OlavLeftPinkie1", "OlavRightPinkie1", "OlavLeftPinkie2", "OlavRightPinkie2", "OlavLeftPinkie3", "OlavRightPinkie3", "OlavLeftRing1", "OlavRightRing1", "OlavLeftRing2", "OlavRightRing2", "OlavLeftRing3", "OlavRightRing3", "OlavLeftFoot", "OlavRightFoot", "OlavLeftLowerArm", "OlavRightLowerArm", "OlavLeftHand", "OlavRightHand", "OlavHead", "OlavHips", "OlavNeck", "OlavLeftLowerLeg", "OlavRightLowerLeg", "OlavLeftShoulder", "OlavRightShoulder", "OlavSpine", "OlavLeftUpperLeg", "OlavRightUpperLeg", "OlavLeftThumb1", "OlavRightThumb1", "OlavLeftThumb2", "OlavRightThumb2", "OlavLeftThumb3", "OlavRightThumb3", "OlavLeftToes", "OlavRightToes", "OlavLeftUpperArm", "OlavRightUpperArm", "OlavJaw", "OlavRightEye", "OlavLeftEye", "EXTRA-tie.01", "OlavTieBone001", "EXTRA-tie.02", "OlavTieBone002", "EXTRA-tie.03", "OlavTieBone003"]

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
#            DELETE UNUSED BONES
##############################################################

def delete_unused_bones(context):

    obj = bpy.context.active_object
    
    bones_to_delete = ["DEF-chest", "DEF-f_index.01.L.01", "DEF-f_index.01.L.02", "DEF-f_index.01.R.01", "DEF-f_index.01.R.02", "DEF-f_index.02.L", "DEF-f_index.02.R", "DEF-f_index.03.L", "DEF-f_index.03.R", "DEF-f_middle.01.L.01", "DEF-f_middle.01.L.02", "DEF-f_middle.01.R.01", "DEF-f_middle.01.R.02", "DEF-f_middle.02.L", "DEF-f_middle.02.R", "DEF-f_middle.03.L", "DEF-f_middle.03.R", "DEF-f_pinky.01.L.01", "DEF-f_pinky.01.L.02", "DEF-f_pinky.01.R.01", "DEF-f_pinky.01.R.02", "DEF-f_pinky.02.L", "DEF-f_pinky.02.R", "DEF-f_pinky.03.L", "DEF-f_pinky.03.R", "DEF-f_ring.01.L.01", "DEF-f_ring.01.L.02", "DEF-f_ring.01.R.01", "DEF-f_ring.01.R.02", "DEF-f_ring.02.L", "DEF-f_ring.02.R", "DEF-f_ring.03.L", "DEF-f_ring.03.R", "DEF-foot.L", "DEF-foot.R", "DEF-forearm.01.L", "DEF-forearm.01.R", "DEF-forearm.02.L", "DEF-forearm.02.R", "DEF-hand.L", "DEF-hand.R", "DEF-head", "DEF-hips", "DEF-neck", "DEF-palm.01.L", "DEF-palm.01.R", "DEF-palm.02.L", "DEF-palm.02.R", "DEF-palm.03.L", "DEF-palm.03.R", "DEF-palm.04.L", "DEF-palm.04.R", "DEF-shin.01.L", "DEF-shin.01.R", "DEF-shin.02.L", "DEF-shin.02.R", "DEF-shoulder.L", "DEF-shoulder.R", "DEF-spine", "DEF-thigh.01.L", "DEF-thigh.01.R", "DEF-thigh.02.L", "DEF-thigh.02.R", "DEF-thumb.01.L.01", "DEF-thumb.01.L.02", "DEF-thumb.01.R.01", "DEF-thumb.01.R.02", "DEF-thumb.02.L", "DEF-thumb.02.R", "DEF-thumb.03.L", "DEF-thumb.03.R", "DEF-tie.00", "DEF-tie.01", "DEF-tie.02", "DEF-toe.L", "DEF-toe.R", "DEF-upper_arm.01.L", "DEF-upper_arm.01.R", "DEF-upper_arm.02.L", "DEF-upper_arm.02.R", "ORG-heel.02.L", "ORG-heel.02.R", "ORG-heel.L", "ORG-heel.R", "ORG-palm.01.L", "ORG-palm.01.R", "ORG-palm.02.L", "ORG-palm.02.R", "ORG-palm.03.L", "ORG-palm.03.R", "ORG-palm.04.L", "ORG-palm.04.R"]

    for bone in bones_to_delete:
        try:
            obj.data.bones[bone].hide = True
        except:
            #print("Could not find bone", bone)
            pass


class class_delete_unused_bones(bpy.types.Operator):
    """DELETE bones that aren't used when using mecanim"""
    bl_idname = "bear.delete_unused_bones"
    bl_label = "Delete Unused"

    @classmethod
    def poll(cls, context):
        return len(context.selected_objects) is not 0

    def execute(self, context):
        delete_unused_bones(context)
        return {'FINISHED'}

##############################################################
#            HIDE/UNHIDE UNINTERESTING BONES
##############################################################

def hide_unused_bones(context):

    obj = bpy.context.active_object
    
    bones_to_hide = ["DEF-chest", "DEF-f_index.01.L.01", "DEF-f_index.01.L.02", "DEF-f_index.01.R.01", "DEF-f_index.01.R.02", "DEF-f_index.02.L", "DEF-f_index.02.R", "DEF-f_index.03.L", "DEF-f_index.03.R", "DEF-f_middle.01.L.01", "DEF-f_middle.01.L.02", "DEF-f_middle.01.R.01", "DEF-f_middle.01.R.02", "DEF-f_middle.02.L", "DEF-f_middle.02.R", "DEF-f_middle.03.L", "DEF-f_middle.03.R", "DEF-f_pinky.01.L.01", "DEF-f_pinky.01.L.02", "DEF-f_pinky.01.R.01", "DEF-f_pinky.01.R.02", "DEF-f_pinky.02.L", "DEF-f_pinky.02.R", "DEF-f_pinky.03.L", "DEF-f_pinky.03.R", "DEF-f_ring.01.L.01", "DEF-f_ring.01.L.02", "DEF-f_ring.01.R.01", "DEF-f_ring.01.R.02", "DEF-f_ring.02.L", "DEF-f_ring.02.R", "DEF-f_ring.03.L", "DEF-f_ring.03.R", "DEF-foot.L", "DEF-foot.R", "DEF-forearm.01.L", "DEF-forearm.01.R", "DEF-forearm.02.L", "DEF-forearm.02.R", "DEF-hand.L", "DEF-hand.R", "DEF-head", "DEF-hips", "DEF-neck", "DEF-palm.01.L", "DEF-palm.01.R", "DEF-palm.02.L", "DEF-palm.02.R", "DEF-palm.03.L", "DEF-palm.03.R", "DEF-palm.04.L", "DEF-palm.04.R", "DEF-shin.01.L", "DEF-shin.01.R", "DEF-shin.02.L", "DEF-shin.02.R", "DEF-shoulder.L", "DEF-shoulder.R", "DEF-spine", "DEF-thigh.01.L", "DEF-thigh.01.R", "DEF-thigh.02.L", "DEF-thigh.02.R", "DEF-thumb.01.L.01", "DEF-thumb.01.L.02", "DEF-thumb.01.R.01", "DEF-thumb.01.R.02", "DEF-thumb.02.L", "DEF-thumb.02.R", "DEF-thumb.03.L", "DEF-thumb.03.R", "DEF-tie.00", "DEF-tie.01", "DEF-tie.02", "DEF-toe.L", "DEF-toe.R", "DEF-upper_arm.01.L", "DEF-upper_arm.01.R", "DEF-upper_arm.02.L", "DEF-upper_arm.02.R", "ORG-heel.02.L", "ORG-heel.02.R", "ORG-heel.L", "ORG-heel.R", "ORG-palm.01.L", "ORG-palm.01.R", "ORG-palm.02.L", "ORG-palm.02.R", "ORG-palm.03.L", "ORG-palm.03.R", "ORG-palm.04.L", "ORG-palm.04.R", "MCH-elbow_hose_p.R", "elbow_hose.R", "MCH-forearm_hose_p.R", "forearm_hose.R", "MCH-forearm_hose_end_p.R", "forearm_hose_end.R", "MCH-upper_arm_hose_end_p.R", "upper_arm_hose_end.R", "MCH-upper_arm_hose_p.R", "upper_arm_hose.R", "MCH-elbow_hose_p.L", "elbow_hose.L", "MCH-forearm_hose_p.L", "forearm_hose.L", "MCH-forearm_hose_end_p.L", "forearm_hose_end.L", "MCH-upper_arm_hose_end_p.L", "upper_arm_hose_end.L", "MCH-upper_arm_hose_p.L", "upper_arm_hose.L", "MCH-knee_hose_p.L", "knee_hose.L", "MCH-shin_hose_p.L", "shin_hose.L", "MCH-shin_hose_end_p.L", "shin_hose_end.L", "MCH-thigh_hose_end_p.L", "thigh_hose_end.L", "MCH-thigh_hose_p.L", "thigh_hose.L", "MCH-knee_hose_p.R", "knee_hose.R", "MCH-shin_hose_p.R", "shin_hose.R", "MCH-shin_hose_end_p.R", "shin_hose_end.R", "MCH-thigh_hose_end_p.R", "thigh_hose_end.R", "MCH-thigh_hose_p.R", "thigh_hose.R"]
    bones_to_unhide = ["ORG-chest", "ORG-f_index.01.L", "ORG-f_index.01.R", "ORG-f_index.02.L", "ORG-f_index.02.R", "ORG-f_index.03.L", "ORG-f_index.03.R", "ORG-f_middle.01.L", "ORG-f_middle.01.R", "ORG-f_middle.02.L", "ORG-f_middle.02.R", "ORG-f_middle.03.L", "ORG-f_middle.03.R", "ORG-f_pinky.01.L", "ORG-f_pinky.01.R", "ORG-f_pinky.02.L", "ORG-f_pinky.02.R", "ORG-f_pinky.03.L", "ORG-f_pinky.03.R", "ORG-f_ring.01.L", "ORG-f_ring.01.R", "ORG-f_ring.02.L", "ORG-f_ring.02.R", "ORG-f_ring.03.L", "ORG-f_ring.03.R", "ORG-foot.L", "ORG-foot.R", "ORG-forearm.L", "ORG-forearm.R", "ORG-hand.L", "ORG-hand.R", "ORG-head", "ORG-hips", "ORG-neck", "ORG-shin.L", "ORG-shin.R", "ORG-shoulder.L", "ORG-shoulder.R", "ORG-spine", "ORG-thigh.L", "ORG-thigh.R", "ORG-thumb.01.L", "ORG-thumb.01.R", "ORG-thumb.02.L", "ORG-thumb.02.R", "ORG-thumb.03.L", "ORG-thumb.03.R", "ORG-toe.L", "ORG-toe.R", "ORG-upper_arm.L", "ORG-upper_arm.R", "EXTRA-jaw", "EXTRA-eye.R", "EXTRA-eye.L", "OlavChest", "OlavLeftIndex1", "OlavRightIndex1", "OlavLeftIndex2", "OlavRightIndex2", "OlavLeftIndex3", "OlavRightIndex3", "OlavLeftMiddle1", "OlavRightMiddle1", "OlavLeftMiddle2", "OlavRightMiddle2", "OlavLeftMiddle3", "OlavRightMiddle3", "OlavLeftPinkie1", "OlavRightPinkie1", "OlavLeftPinkie2", "OlavRightPinkie2", "OlavLeftPinkie3", "OlavRightPinkie3", "OlavLeftRing1", "OlavRightRing1", "OlavLeftRing2", "OlavRightRing2", "OlavLeftRing3", "OlavRightRing3", "OlavLeftFoot", "OlavRightFoot", "OlavLeftLowerArm", "OlavRightLowerArm", "OlavLeftHand", "OlavRightHand", "OlavHead", "OlavHips", "OlavNeck", "OlavLeftLowerLeg", "OlavRightLowerLeg", "OlavLeftShoulder", "OlavRightShoulder", "OlavSpine", "OlavLeftUpperLeg", "OlavRightUpperLeg", "OlavLeftThumb1", "OlavRightThumb1", "OlavLeftThumb2", "OlavRightThumb2", "OlavLeftThumb3", "OlavRightThumb3", "OlavLeftToes", "OlavRightToes", "OlavLeftUpperArm", "OlavRightUpperArm", "OlavJaw", "OlavRightEye", "OlavLeftEye", "EXTRA-tie.01", "OlavTieBone001", "EXTRA-tie.02", "OlavTieBone002", "EXTRA-tie.03", "OlavTieBone003"]

    for bone in bones_to_hide:
        try:
            obj.data.bones[bone].hide = True
        except:
            #print("Could not find bone", bone)
            pass

    for bone in bones_to_unhide:
        try:
            obj.data.bones[bone].hide = False
        except:
            #print("Could not find bone", bone)
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
#            RENAME BONES
##############################################################

def set_char_bone_name(character_name):
    return 0

def rename_bones(context):

    obj = bpy.context.active_object
    
    bones_naming = {"ORG-chest":"OlavChest", "ORG-f_index.01.L":"OlavLeftIndex1", "ORG-f_index.01.R":"OlavRightIndex1", "ORG-f_index.02.L":"OlavLeftIndex2", "ORG-f_index.02.R":"OlavRightIndex2", "ORG-f_index.03.L":"OlavLeftIndex3", "ORG-f_index.03.R":"OlavRightIndex3", "ORG-f_middle.01.L":"OlavLeftMiddle1", "ORG-f_middle.01.R":"OlavRightMiddle1", "ORG-f_middle.02.L":"OlavLeftMiddle2", "ORG-f_middle.02.R":"OlavRightMiddle2", "ORG-f_middle.03.L":"OlavLeftMiddle3", "ORG-f_middle.03.R":"OlavRightMiddle3", "ORG-f_pinky.01.L":"OlavLeftPinkie1", "ORG-f_pinky.01.R":"OlavRightPinkie1", "ORG-f_pinky.02.L":"OlavLeftPinkie2", "ORG-f_pinky.02.R":"OlavRightPinkie2", "ORG-f_pinky.03.L":"OlavLeftPinkie3", "ORG-f_pinky.03.R":"OlavRightPinkie3", "ORG-f_ring.01.L":"OlavLeftRing1", "ORG-f_ring.01.R":"OlavRightRing1", "ORG-f_ring.02.L":"OlavLeftRing2", "ORG-f_ring.02.R":"OlavRightRing2", "ORG-f_ring.03.L":"OlavLeftRing3", "ORG-f_ring.03.R":"OlavRightRing3", "ORG-foot.L":"OlavLeftFoot", "ORG-foot.R":"OlavRightFoot", "ORG-forearm.L":"OlavLeftLowerArm", "ORG-forearm.R":"OlavRightLowerArm", "ORG-hand.L":"OlavLeftHand", "ORG-hand.R":"OlavRightHand", "ORG-head":"OlavHead", "ORG-hips":"OlavHips", "ORG-neck":"OlavNeck", "ORG-shin.L":"OlavLeftLowerLeg", "ORG-shin.R":"OlavRightLowerLeg", "ORG-shoulder.L":"OlavLeftShoulder", "ORG-shoulder.R":"OlavRightShoulder", "ORG-spine":"OlavSpine", "ORG-thigh.L":"OlavLeftUpperLeg", "ORG-thigh.R":"OlavRightUpperLeg", "ORG-thumb.01.L":"OlavLeftThumb1", "ORG-thumb.01.R":"OlavRightThumb1", "ORG-thumb.02.L":"OlavLeftThumb2", "ORG-thumb.02.R":"OlavRightThumb2", "ORG-thumb.03.L":"OlavLeftThumb3", "ORG-thumb.03.R":"OlavRightThumb3", "ORG-toe.L":"OlavLeftToes", "ORG-toe.R":"OlavRightToes", "ORG-upper_arm.L":"OlavLeftUpperArm", "ORG-upper_arm.R":"OlavRightUpperArm", "EXTRA-jaw":"OlavJaw", "EXTRA-eye.R":"OlavRightEye", "EXTRA-eye.L":"OlavLeftEye", "EXTRA-tie.01":"OlavTieBone001", "EXTRA-tie.02":"OlavTieBone002", "EXTRA-tie.03":"OlavTieBone003"}

    for key, value in bones_naming.items():
        try:
            obj.data.bones[key].name = value
        except:
            try:
                obj.data.bones[value].name = key   
            except:
                print("what...")

class class_rename_bones(bpy.types.Operator):
    """Rename bones back and forth"""
    bl_idname = "bear.rename_bones"
    bl_label = "Rename Bones"

    @classmethod
    def poll(cls, context):
        return len(context.selected_objects) is not 0

    def execute(self, context):
        rename_bones(context)
        return {'FINISHED'}

##############################################################
#                  ADD EXTRA BONES
##############################################################

def add_extra_bones(context):

    obj = bpy.context.active_object

    bpy.ops.object.mode_set(mode='EDIT', toggle=True)


    jaw = obj.data.edit_bones.new("EXTRA-jaw")
    jaw.head = mathutils.Vector((0, -0.03455, 1.554))
    jaw.tail = mathutils.Vector((0, -0.10268, 1.554))

    eyeR = obj.data.edit_bones.new("EXTRA-eye.R")
    eyeR.head = mathutils.Vector((-0.036, -0.03455, 1.615))
    eyeR.tail = mathutils.Vector((-0.036, -0.10268, 1.615))

    eyeL = obj.data.edit_bones.new("EXTRA-eye.L")
    eyeL.head = mathutils.Vector((0.036, -0.03455, 1.615))
    eyeL.tail = mathutils.Vector((0.036, -0.10268, 1.615))

    head = 0
    try:
        head = obj.data.edit_bones["ORG-head"]
    except:
        try:
            head = obj.data.edit_bones["OlavHead"]
        except:
            print("Didn't find head bone... Is the name right?")
        pass

    eyeL.parent = head
    eyeR.parent = head
    jaw.parent = head


class class_add_extra_bones(bpy.types.Operator):
    """Add extra bones (eyes, jaw)"""
    bl_idname = "bear.add_extra_bones"
    bl_label = "Add Extra Bones"

    @classmethod
    def poll(cls, context):
        return len(context.selected_objects) is not 0

    def execute(self, context):
        add_extra_bones(context)
        return {'FINISHED'}


##############################################################
#               MAKE PLAYBLAST
##############################################################

def make_playblast(context):

    scene = bpy.context.scene

    armature = bpy.context.active_object
    action = armature.animation_data.action

    # ORIGINAL SETTINGS

    #original_render_engine = scene.render.engine
    #original_bake_type = scene.render.bake_type
    #original_vcol_bake = scene.render.use_bake_to_vertex_color
    original_output_path = scene.render.filepath
    #original_file_extension = scene.render.file_extension

    original_image_settings_file_format = scene.render.image_settings.file_format
    original_ffmpeg_format = scene.render.ffmpeg.format

    original_frame_start = scene.frame_start
    original_frame_end = scene.frame_end

    # NEW DATA
    blend_name = bpy.path.basename(bpy.context.blend_data.filepath).split(".")[0]
    timestamp = datetime.today().strftime('%y%m%d_%H%M%S')
    output_folder = bpy.path.abspath("//") + "Playblast\\"

    final_path = output_folder + blend_name + "_" + action.name + "_" + timestamp + "_"


    # APPLY SETTINGS
    scene.render.filepath = final_path
    
    scene.render.image_settings.file_format = 'H264'
    scene.render.ffmpeg.format = 'H264'
    scene.render.ffmpeg.audio_codec = 'AAC'

    scene.frame_start = action.frame_range[0]
    scene.frame_end = action.frame_range[1]

    print("Rendering playblast.\n"+
        "Output folder: " + final_path + "\n" +
        "Frame range: " + str(action.frame_range)
        )

    # DO THE THINGS
    bpy.ops.render.opengl(animation=True)

    # RESTORE SETTINGS
    scene.render.filepath = original_output_path
    
    scene.render.image_settings.file_format = original_image_settings_file_format
    scene.render.ffmpeg.format = original_ffmpeg_format

    scene.frame_start = int(original_frame_start)
    scene.frame_end = int(original_frame_end)

    # no worky
    #poop_path = final_path + str(int(action.frame_range[0])).zfill(4) + "-" + str(int(action.frame_range[1])).zfill(4) + ".avi"
    #print(poop_path)
    #subprocess.Popen(r'explorer /select,"' + final_path + str(action.frame_range[0]) + "-" + str(action.frame_range[1]) + ".avi\"")
    
    subprocess.Popen('explorer ' + output_folder)


class class_make_playblast(bpy.types.Operator):
    """Render playblast to folder beside blend file"""
    bl_idname = "bear.render_playblast"
    bl_label = "Export Playblast"

    @classmethod
    def poll(cls, context):
        return True
        #if(context.active_object is not None):
        #    if(context.active_object.animation_data.action)
        #return len(context.selected_objects) is not 0 and context.active_object.animation_data.action is not None

    def execute(self, context):
        make_playblast(context)
        return {'FINISHED'}

def set_frame_range_from_action(action):
    scene = bpy.context.scene

    scene.frame_start = action.frame_range[0]
    scene.frame_end = action.frame_range[1]


##############################################################
#               VERIFY RIG COMPATIBILITY
##############################################################

def verify_rig_compatibility(context):

    print("Not implemented yet")

class class_verify_rig_compatibility(bpy.types.Operator):
    """Verify rig compatibility with mecanim"""
    bl_idname = "bear.verify_rig_compatibility"
    bl_label = "Verify"

    @classmethod
    def poll(cls, context):
        return len(context.selected_objects) is not 0

    def execute(self, context):
        verify_rig_compatibility(context)
        return {'FINISHED'}

##############################################################
#               ALIGN FUNCTIONS
##############################################################


class class_align_to_bones(bpy.types.Operator):
    bl_idname = "bear.align_to_bones"
    bl_label = "Object -> Pose Bone"

    #align_mode = bpy.props.EnumProperty(
    #    name="Align Mode",
    #    description="How Should Things Be Aligned",
    #    items=(('OBJECTS_TO_POSE_BONE', "Objects to Pose Bone", "Align selected objects to active pose bone")
    #           ),
    #    default="OBJECTS_TO_POSE_BONE"
    #    )

    @classmethod
    def poll(cls, context):
        return len(context.selected_objects) is not 0 and bpy.context.active_pose_bone is not None

    def execute(self, context):
        #if(self.align_mode is 'OBJECTS_TO_POSE_BONE'):
        align_objects_to_pose_bone(context)

        return {'FINISHED'}

class class_align_pose_bone_to_object(bpy.types.Operator):
    bl_idname = "bear.align_pose_bone_to_object"
    bl_label = "Pose Bone -> Object"

    #align_mode = bpy.props.EnumProperty(
    #    name="Align Mode",
    #    description="How Should Things Be Aligned",
    #    items=(('OBJECTS_TO_POSE_BONE', "Objects to Pose Bone", "Align selected objects to active pose bone")
    #           ),
    #    default="OBJECTS_TO_POSE_BONE"
    #    )

    @classmethod
    def poll(cls, context):
        return len(context.selected_objects) is not 0 and bpy.context.active_pose_bone is not None

    def execute(self, context):
        #if(self.align_mode is 'OBJECTS_TO_POSE_BONE'):
        align_pose_bone_to_object(context)

        return {'FINISHED'}

def align_objects_to_pose_bone(context):
    print("Aligning objects to pose bone")
    C = bpy.context

    pb = C.active_pose_bone

    for obj in C.selected_objects:
        if(obj == C.active_object):
            continue
        loc, rot, scale = pb.matrix.decompose()
        
        if(obj.rotation_mode == 'QUATERNION'):
            print("Aligning quaternion rotations")
            obj.rotation_quaternion = rot
            
        elif(obj.rotation_mode == 'XYZ'):
            print("Aligning euler rotations")
            obj.rotation_euler = rot.to_euler()
            
        else:
            print("Rotation mode not supported. Will not align objects!")

def align_pose_bone_to_object(context):
    print("Aligning objects to pose bone")
    C = bpy.context

    pb = C.active_pose_bone
    aligned = False

    for obj in C.selected_objects:
        if(obj == C.active_object or aligned is True):
            continue

        loc, rot, scale = obj.matrix_local.decompose()
        rot = obj.rotation_quaternion

        if(pb.rotation_mode == 'QUATERNION'):
            print("Aligning quaternion rotations")
            pb.rotation_quaternion = obj.rotation_quaternion * pb.matrix_basis.decompose()[1]
            
        elif(pb.rotation_mode == 'XYZ'):
            print("Aligning euler rotations")
            pb.rotation_euler = obj.rotation_euler
            
        else:
            print("Rotation mode not supported. Will not align objects!")

        aligned = True

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
        col.operator("bear.align_to_bones")
        col.operator("bear.align_pose_bone_to_object")

        col = layout.column(align=True)
        col.label(text="Export")
        col.operator("bear.export_single_action")
        col.operator("bear.export_all_actions")
        col.separator()
        col.operator("bear.export_rigged_character")
        col.label(text="Render")
        col.operator("bear.render_playblast")
        col.label(text="Setup")
        row = col.row()
        col.operator("bear.setup_deformable_bones")
        #col.operator("bear.verify_rig_compatibility")
        row.operator("bear.hide_unused_bones")
        #row.operator("bear.delete_unused_bones")
        #col.operator("bear.rename_bones")
        #col.operator("bear.add_extra_bones")

script_classes = [
    class_bear_rig_buttons,
    class_verify_rig_compatibility,
    class_setup_deformable_bones,
    class_hide_unused_bones,
    class_delete_unused_bones,
    class_rename_bones,
    class_add_extra_bones,
    class_export_single_action,
    class_export_all_actions,
    class_export_rigged_character,
    class_align_to_bones,
    class_align_pose_bone_to_object,
    class_make_playblast,
]

def register():
    for c in script_classes:
        bpy.utils.register_class(c)

def unregister():
    for c in script_classes:
        bpy.utils.unregister_class(c)

if __name__ == "__main__":
    register()
