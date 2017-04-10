import bpy
import os
from bpy_extras.io_utils import (ExportHelper,
                                path_reference_mode,
                                )
from bpy.types import Operator, Panel
from bpy.props import (StringProperty,
                       BoolProperty,
                       FloatProperty,
                       EnumProperty,
                       )

bl_info = {
    "name": "Bear's Batch Exporter",
    "description": "Various batch export scripts",
    "author": "Bjørnar Frøyse",
    "version": (1, 0, 0),
    "blender": (2, 7, 4),
    "location": "Tool Shelf",
    "warning": "", 
    "wiki_url": "",
    "tracker_url": "",
    "category": "Import-Export"}


class ExportObjects(Operator, ExportHelper):
    """Tooltip"""
    bl_idname = "bear.export_objects_to_fbx"
    bl_label = "Export FBX"
    filename_ext = ""

    filepath = ""

    e_do_merge_objects = BoolProperty(
            name="Merge Objects When Exporting",
            description="",
            default=False,
            )

    e_selected_groups_as_objects = BoolProperty(
            name="Treat Groups As Objects",
            description="",
            default=False,
            )

    e_clear_materials = EnumProperty(
        name="Materials",
        items=(('KEEP', "Keep Original", ""),
               ('CLEAR', "Clear All", ""),
               ('CONSOLIDATE', "Consolidate", "")#,
               #('CLEAR_WITH_VERTEX_COLOR', "Material To Vertex Color", "")
               ),
        default='CONSOLIDATE',
        )

    e_decimate_groups = BoolProperty(
            name="Decimate Groups On Export",
            description="",
            default=False,
            )

    e_decimate_groups_ratio = FloatProperty(
            name="Decimation Ratio",
            description="Decimate All Groups With This Ratio",
            min=0.0, max=1.0,
            default=1.0,
            )

    version = EnumProperty(
            items=(('BIN7400', "FBX 7.4 binary", "Newer 7.4 binary version, still in development (no animation yet)"),
                   ('ASCII6100', "FBX 6.1 ASCII", "Legacy 6.1 ascii version"),
                   ),
            name="Version",
            description="Choose which version of the exporter to use",
            )
    global_scale = FloatProperty(
            name="Scale",
            description="Scale all data (Some importers do not support scaled armatures!)",
            min=0.001, max=1000.0,
            soft_min=0.01, soft_max=1000.0,
            default=1.0,
            )
    axis_forward = EnumProperty(
            name="Forward",
            items=(('X', "X Forward", ""),
                   ('Y', "Y Forward", ""),
                   ('Z', "Z Forward", ""),
                   ('-X', "-X Forward", ""),
                   ('-Y', "-Y Forward", ""),
                   ('-Z', "-Z Forward", ""),
                   ),
            default='Z',
            )
    axis_up = EnumProperty(
            name="Up",
            items=(('X', "X Up", ""),
                   ('Y', "Y Up", ""),
                   ('Z', "Z Up", ""),
                   ('-X', "-X Up", ""),
                   ('-Y', "-Y Up", ""),
                   ('-Z', "-Z Up", ""),
                   ),
            default='Y',
            )
    # 7.4 only
    bake_space_transform = BoolProperty(
            name="Apply Transform",
            description=("Bake space transform into object data, avoids getting unwanted rotations to objects when "
                         "target space is not aligned with Blender's space "
                         "(WARNING! experimental option, might give odd/wrong results)"),
            default=True,
            )

    object_types = EnumProperty(
            name="Object Types",
            options={'ENUM_FLAG'},
            items=(('EMPTY', "Empty", ""),
                   ('CAMERA', "Camera", ""),
                   ('LAMP', "Lamp", ""),
                   ('ARMATURE', "Armature", ""),
                   ('MESH', "Mesh", ""),
                   ('OTHER', "Other", "Other geometry types, like curve, metaball, etc. (converted to meshes)"),
                   ),
            description="Which kind of object to export",
            default={'MESH'},
            )

    use_mesh_modifiers = BoolProperty(
            name="Apply Modifiers",
            description="Apply modifiers to mesh objects (except Armature ones!)",
            default=True,
            )
    mesh_smooth_type = EnumProperty(
            name="Smoothing",
            items=(('OFF', "Off", "Don't write smoothing, export normals instead"),
                   ('FACE', "Face", "Write face smoothing"),
                   ('EDGE', "Edge", "Write edge smoothing"),
                   ),
            description=("Export smoothing information "
                         "(prefer 'Off' option if your target importer understand split normals)"),
            default='OFF',
            )
    use_mesh_edges = BoolProperty(
            name="Loose Edges",
            description="Export loose edges (as two-vertices polygons)",
            default=False,
            )
    # 7.4 only
    use_tspace = BoolProperty(
            name="Tangent Space",
            description=("Add binormal and tangent vectors, together with normal they form the tangent space "
                         "(will only work correctly with tris/quads only meshes!)"),
            default=False,
            )
    # 7.4 only
    use_custom_props = BoolProperty(
            name="Custom Properties",
            description="Export custom properties",
            default=False,
            )
    use_armature_deform_only = BoolProperty(
            name="Only Deform Bones",
            description="Only write deforming bones (and non-deforming ones when they have deforming children)",
            default=False,
            )
    # Anim - 7.4
    bake_anim = BoolProperty(
            name="Baked Animation",
            description="Export baked keyframe animation",
            default=True,
            )
    bake_anim_use_nla_strips = BoolProperty(
            name="NLA Strips",
            description=("Export each non-muted NLA strip as a separated FBX's AnimStack, if any, "
                         "instead of global scene animation"),
            default=True,
            )
    bake_anim_use_all_actions = BoolProperty(
            name="All Actions",
            description=("Export each action as a separated FBX's AnimStack, "
                         "instead of global scene animation"),
            default=True,
            )
    bake_anim_step = FloatProperty(
            name="Sampling Rate",
            description=("How often to evaluate animated values (in frames)"),
            min=0.01, max=100.0,
            soft_min=0.1, soft_max=10.0,
            default=1.0,
            )
    bake_anim_simplify_factor = FloatProperty(
            name="Simplify",
            description=("How much to simplify baked values (0.0 to disable, the higher the more simplified"),
            min=0.0, max=10.0,  # No simplification to up to 0.05 slope/100 max_frame_step.
            default=1.0,  # default: min slope: 0.005, max frame step: 10.
            )
    # Anim - 6.1
    use_anim = BoolProperty(
            name="Animation",
            description="Export keyframe animation",
            default=True,
            )
    use_anim_action_all = BoolProperty(
            name="All Actions",
            description=("Export all actions for armatures or just the currently selected action"),
            default=True,
            )
    use_default_take = BoolProperty(
            name="Default Take",
            description=("Export currently assigned object and armature animations into a default take from the scene "
                         "start/end frames"),
            default=True
            )
    use_anim_optimize = BoolProperty(
            name="Optimize Keyframes",
            description="Remove double keyframes",
            default=True,
            )
    anim_optimize_precision = FloatProperty(
            name="Precision",
            description=("Tolerance for comparing double keyframes (higher for greater accuracy)"),
            min=0.0, max=20.0,  # from 10^2 to 10^-18 frames precision.
            soft_min=1.0, soft_max=16.0,
            default=6.0,  # default: 10^-4 frames.
            )
    path_mode = path_reference_mode
    embed_textures = BoolProperty(
        name="Embed Textures",
        description="Embed textures in FBX binary file (only for \"Copy\" path mode!)",
        default=False,
        )


    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):

        selection = bpy.context.selected_objects
        active = bpy.context.active_object

        if(self.e_do_merge_objects):

            if(self.e_selected_groups_as_objects):

                print("Export groups to files, DO merge")

                groups_to_export = []

                for obj in bpy.context.selected_objects:
                    if(len(obj.users_group) > 0):
                        for group in obj.users_group:
                            if (group.name.startswith("EXPORT:")):
                                groups_to_export.append(group)

                groups_to_export = list(set(groups_to_export))

                bpy.ops.object.select_all(action='DESELECT')

                for group in groups_to_export:
                    print(group.name)
                    for obj in group.objects:
                        obj.select = True

                    bpy.context.scene.objects.active = group.objects[0]   
                    bpy.ops.object.duplicate()
                    bpy.ops.object.make_single_user(type='SELECTED_OBJECTS', object=False, obdata=True, material=False, texture=False, animation=False)
                    bpy.ops.object.convert()
                    bpy.ops.object.join()
                    bpy.context.scene.objects.active = bpy.context.selected_objects[0]

                    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

                    if(self.e_decimate_groups):
                        bpy.context.active_object.modifiers.new("export_decimation", type='DECIMATE')
                        bpy.context.active_object.modifiers['export_decimation'].ratio = self.e_decimate_groups_ratio

                    name = group.name.replace("EXPORT:", "")
                    obj.data.name = name

                    selected_to_single_fbx(context, self, name)

                    bpy.ops.object.delete()

            else:

                print("Merge, ignore groups")

                bpy.ops.object.duplicate()
                bpy.ops.object.make_single_user(type='SELECTED_OBJECTS', object=False, obdata=True, material=False, texture=False, animation=False)
                bpy.ops.object.convert()
                bpy.ops.object.join()
                bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

                name = bpy.path.clean_name(bpy.context.active_object.name)

                selected_to_single_fbx(context, self, "")

                bpy.ops.object.delete()

        # GROUPS AS OBJECTS, NO MERGING

        elif(self.e_selected_groups_as_objects and not self.e_do_merge_objects):

            print("Export groups to files, don't merge")

            groups_to_export = []

            for obj in bpy.context.selected_objects:
                if(len(obj.users_group) > 0):
                    for group in obj.users_group:
                        if (group.name.startswith("EXPORT:")):
                            groups_to_export.append(group)

            groups_to_export = list(set(groups_to_export))

            bpy.ops.object.select_all(action='DESELECT')

            for group in groups_to_export:
                for obj in group.objects:
                    obj.select = True

                name = group.name.replace("EXPORT:", "")

                selected_to_single_fbx(context, self, name)

                for obj in group.objects:
                    obj.select = False

        # SELECTED OBJECTS TO INDIVIDUAL FILES

        else:
            print("Selected to separate files")

            bpy.ops.object.select_all(action='DESELECT')

            for obj in selection:

                obj.select = True

                name = bpy.path.clean_name(obj.name)

                selected_to_single_fbx(context, self, name)

                obj.select = False

        for obj in selection:
            obj.select = True

        bpy.context.scene.objects.active = active
        print("Exported", len(selection), "objects with the following settings:", "Keep Materials: ", self.e_clear_materials)
        return {'FINISHED'}


def selected_to_single_fbx(context, self, new_name):

    supported_types = ['MESH', 'CURVE']

    if(self.e_clear_materials == 'CLEAR'):
        objects = bpy.context.selected_objects
        old_materials = {obj: [mat for mat in obj.data.materials] for obj in objects if obj.type in supported_types}

        for obj in objects:
            if(obj.type in supported_types):
                obj.data.materials.clear()

        export(self, new_name)

        for obj in objects:
            if(obj.type in supported_types):
                for mat in old_materials[obj]:
                    obj.data.materials.append(mat)
    elif(self.e_clear_materials == 'CONSOLIDATE'):
        keywords = ['Window', 'Glowing', 'Surface', 'Glass', 'FX', 'Reflective']
        generic_material_name = '__Other'

        objects = bpy.context.selected_objects

        old_materials = {obj: [mat for mat in obj.data.materials] for obj in objects}
        new_materials = {obj: [mat for mat in obj.data.materials if mat is not None] for obj in objects}
        #new_materials = {}

        generic_material = None
        try:
            generic_material = bpy.data.materials[generic_material_name]
        except KeyError:     
            bpy.data.materials.new(generic_material_name)
            generic_material = bpy.data.materials[generic_material_name]

        for obj in objects:
            same_materials = {keyword: [mat for mat in new_materials[obj] if mat.name.startswith(keyword)] for keyword in keywords}
            #same_materials = {k: v for k, v in same_materials.items() if v != []}

            for i, mat in enumerate(new_materials[obj]):
                for j, keyword in enumerate(keywords):
                    if(mat.name.startswith(keyword)):
                        new_materials[obj][i] = same_materials[keyword][i]
                        break
                    else:
                        new_materials[obj][i] = generic_material

        for obj in objects:
            obj.data.materials.clear()
            for mat in new_materials[obj]:
                obj.data.materials.append(mat)

        export(self, new_name)

        for obj in objects:
            obj.data.materials.clear()
            for mat in old_materials[obj]:
                obj.data.materials.append(mat)

        print(new_materials)

    elif(self.e_clear_materials == 'KEEP'):
        export(self, new_name)



def export(self, new_name):

    name = bpy.path.clean_name(new_name)
    fn = self.filepath + name + ".fbx"

    bpy.ops.export_scene.fbx(
    filepath = fn,
    filter_glob = "*.fbx",
    version = self.version,
    axis_forward = self.axis_forward,
    axis_up = self.axis_up,
    bake_space_transform = self.bake_space_transform,
    use_selection = True,
    global_scale = self.global_scale,
    object_types = self.object_types,
    use_mesh_modifiers = self.use_mesh_modifiers,
    mesh_smooth_type = self.mesh_smooth_type,
    use_mesh_edges = self.use_mesh_edges,
    use_tspace = self.use_tspace,
    use_custom_props = self.use_custom_props,
    use_armature_deform_only = self.use_armature_deform_only,
    bake_anim = self.bake_anim,
    bake_anim_use_nla_strips = self.bake_anim_use_nla_strips,
    bake_anim_use_all_actions = self.bake_anim_use_all_actions,
    bake_anim_step = self.bake_anim_step,
    bake_anim_simplify_factor = self.bake_anim_simplify_factor,
    use_anim = self.use_anim,
    use_anim_action_all = self.use_anim_action_all,
    use_default_take = self.use_default_take,
    use_anim_optimize = self.use_anim_optimize,
    anim_optimize_precision = self.anim_optimize_precision,
    path_mode = self.path_mode,
    embed_textures = self.embed_textures
    )


class Buttons(Panel):
    bl_category = "Custom"
    bl_label = "Batch Exporter"
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"

    def draw(self, context):
        layout = self.layout
        layout.operator("bear.export_objects_to_fbx")


script_classes = [
    Buttons,
    ExportObjects,
    ]

addon_keymaps = []

def register():
    for c in script_classes:
        bpy.utils.register_class(c)

    km = bpy.context.window_manager.keyconfigs.addon.keymaps.new(name='3D View', space_type='VIEW_3D')
    kmi = km.keymap_items.new("bear.export_objects_to_fbx", 'F', 'PRESS')
    addon_keymaps.append((km, kmi))

def unregister():
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()

    for c in script_classes:
        bpy.utils.unregister_class(c)

if __name__ == "__main__":
    register()
