# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

bl_info = {
    "name": "Bear - Align Selection To Curve",
    "description": "",
    "author": "Bjørnar Frøyse",
    "version": (0, 0, 1),
    "blender": (2, 7, 1),
    "location": "Tool Shelf",
    "warning": "",  # used for warning icon and text in addons panel
    "wiki_url": "",
    "tracker_url": "",
    "category": "Mesh"}


import bpy
from bpy_extras import view3d_utils
import bmesh
import mathutils
from bpy.props import FloatProperty, IntProperty
import math


class AlignVertsToCurve(bpy.types.Operator):
    """Aligns selection to curve"""
    bl_idname = "mesh.align_verts_to_curve"
    bl_label = "Align Verts to Curve"
    bl_options = {'REGISTER', 'UNDO'}

    influence = FloatProperty(
            name="Influence",
            description="Influence",
            min=0.0, max=1.0,
            default=1.0,
            )

    # 0 is Auto, 1 is Horizontal, 2 is Vertical alignment
    direction = IntProperty(
            name="Direction",
            description="Influence",
            min=0, max=2,
            default=0,
            )

    def execute(self, context):
        align_vertices(context, self.influence, self.direction)
        return {'FINISHED'}

    @classmethod
    def poll(cls, context):
       if len(bpy.context.selected_objects) is 2:
           return True
       else:
           return False

def align_vertices(context, influence, direction):
    C = bpy.context
    edit_obj = bpy.context.selected_objects[0]
    curve_obj = bpy.context.selected_objects[1]

    if (curve_obj == bpy.context.edit_object):
        edit_obj = bpy.context.selected_objects[1]
        curve_obj = bpy.context.selected_objects[0]

    edit_obj.select = False
    bpy.context.scene.objects.active = curve_obj
    bpy.ops.object.convert(target='MESH', keep_original=True)
    curve_mesh_obj = bpy.context.scene.objects.active

    edit_obj = bpy.context.edit_object
    # Object's mesh datablock.
    me = edit_obj.data
    # Convert mesh data to bmesh.
    bm = bmesh.from_edit_mesh(me)

    # Get all selected vertices (in their local space).
    selected_verts = [v for v in bm.verts if v.select]

    verts_local_3d = [v.co for v in selected_verts]

    # Convert selected vertices' positions to 2D screen space.
    # IMPORTANT: Multiply vertex coordinates with the world matrix to get their WORLD position, not local position.
    verts_world_2d = vectors_to_screenpos(context, verts_local_3d, edit_obj.matrix_world)

    # For each vert, look up or to the side and find the nearest interpolated gpencil point for this vertex.
    for i, v in enumerate(selected_verts):
        nearest_point = get_nearest_interpolated_point_on_curve(verts_world_2d[i], curve_to_screenpos(curve_mesh_obj, context), direction, context)
        # Get new vertex coordinate by converting from 2D screen space to 3D world space. Must multiply depth coordinate
        # with world matrix and then final result by INVERTED world matrix to get a correct final value.
        newcoord = edit_obj.matrix_world.inverted() * region_to_location(nearest_point, edit_obj.matrix_world * v.co)
        # Apply the final position using an influence slider.
        v.co = v.co.lerp(newcoord, influence)

    # Recalculate mesh normals
    for edge in bm.edges:
        edge.normal_update()

    # Push bmesh changes back to the actual mesh datablock.
    bmesh.update_edit_mesh(me, True)

    curve_mesh_obj_mesh = curve_mesh_obj.data
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.object.delete()
    bpy.data.meshes.remove(curve_mesh_obj_mesh)
    edit_obj.select = True
    curve_obj.select = True
    bpy.context.scene.objects.active = edit_obj
    bpy.ops.object.mode_set(mode='EDIT')

def get_nearest_interpolated_point_on_curve(vertex_2d, points_2d, direction, context):
    # Define variables used for the two different axes (horizontal or vertical).
    # Doing it like this in order to use the same code for both axes.
    a = 1
    b = 0

    if (direction == 0):
        if not is_vertical(vertex_2d, points_2d):
            a = 0
            b = 1
    elif (direction == 2):
        a = 0
        b = 1

    # Init distance to 9999 in order to guarantee any vertex found is closer.
    nearest_distance = 9999.0
    nearest_point = (0, 0)
    point_upper = 0.0
    point_lower = 0.0
    coord_interpolated = 0

    # I have a feeling this is not the best way to do this, but anyway;
    # This bit of code finds (in 2D) the point (on a line) closest to another point.

    # Works by finding the closest in one direction, then the other, then
    # calculating the interpolated position between these two outer points.
    for i, gpoint_2d in enumerate(points_2d):
        # Variables used to find points relative to the current point (i),
        # clamped to avoid out of range errors.
        previous_point = clamp(0, len(points_2d)-1, i - 1)
        next_point = clamp(0, len(points_2d)-1, i + 1)

        # Gets the absolute (non-negative) distance from the
        # current vertex to the current grease pencil point.
        distance = abs(vertex_2d[a] - gpoint_2d[a])

        # If the current gpencil point is the closest so far, calculate
        # everything and push the values to the variables defined earlier.
        if (distance < nearest_distance):
            nearest_distance = distance
            # If the nearest gpoint is ABOVE the current vertex,
            # find the nearest point BELOW as well.
            # TODO: Make this more readable/elegant? It works, so no need, but still.
            if (gpoint_2d[a] >= vertex_2d[a]):
                point_upper = gpoint_2d
                point_lower = points_2d[previous_point]

                # If the lower point is actually above the vertex,
                # we picked the wrong point and need to correct.
                if (point_lower[a] > point_upper[a]) or (point_upper == point_lower):
                    point_lower = points_2d[next_point]
            else:
                # The opposite of the previous lines
                point_lower = gpoint_2d
                point_upper = points_2d[previous_point]
                if (point_upper[a] <= point_lower[a]) or (point_upper == point_lower):
                    point_upper = points_2d[next_point]

            # Define min and max ranges to calculate the interpolated po<int from
            hrange = (point_upper[b], point_lower[b])
            vrange = (point_upper[a], point_lower[a])
            coord_interpolated = map_range(vrange, hrange, vertex_2d[a])

            # Push the interpolated coord to the correct axis
            if a == 1:
                nearest_point = (coord_interpolated, vertex_2d[1])
            if a == 0:
                nearest_point = (vertex_2d[0], coord_interpolated)

    return nearest_point


def curve_to_screenpos(obj, context):
    # Object currently in edit mode.
    #obj = bpy.context.edit_object
    # Object's mesh datablock.

    me = obj.data

    verts_local_3d = [v.co for v in me.vertices]

    # Convert selected vertices' positions to 2D screen space.
    # IMPORTANT: Multiply vertex coordinates with the world matrix to get their WORLD position, not local position.
    verts_world_2d = vectors_to_screenpos(context, verts_local_3d, obj.matrix_world)

    return verts_world_2d


def vectors_to_screenpos(context, list_of_vectors, matrix):
    if type(list_of_vectors) is mathutils.Vector:
        return location_to_region(matrix * list_of_vectors)
    else:
        return [location_to_region(matrix * vector) for vector in list_of_vectors]


# Generic clamp function
def clamp(a, b, v):
    if (v <= a):
        return a
    elif (v >= b):
        return b
    else:
        return v


# Function for determining if a sequence of 2D
# coordinates form a vertical or horizontal line.
def is_vertical(vertex, list_of_vec2):
    if len(list_of_vec2) == 1:
        if abs(list_of_vec2[0][0] - vertex[0]) > abs(list_of_vec2[0][1] - vertex[1]):
            return True
        else:
            return False

    minval = list(map(min, *list_of_vec2))
    maxval = list(map(max, *list_of_vec2))

    if (maxval[0] - minval[0] > maxval[1] - minval[1]):
        return False
    if (maxval[0] - minval[0] < maxval[1] - minval[1]):
        return True


# Generic map range function.
# grabbed from here: www.rosettacode.org/wiki/Map_range
def map_range(fromrange, torange, value):
    (a1, a2), (b1, b2) = fromrange, torange
    # WORKAROUND: If torange start and end is equal, division by zero occurs.
    # A tiny amount is added to one of them to avoid a zero value here.
    if (a1 == a2):
        a2 += 0.0001
    return b1 + ((value - a1) * (b2 - b1) / (a2 - a1))


import bpy_extras


# Utility functions for converting between 2D and 3D coordinates
def location_to_region(worldcoords):
    out = bpy_extras.view3d_utils.location_3d_to_region_2d(bpy.context.region, bpy.context.space_data.region_3d, worldcoords)
    return out


def region_to_location(viewcoords, depthcoords):
    return bpy_extras.view3d_utils.region_2d_to_location_3d(bpy.context.region, bpy.context.space_data.region_3d, viewcoords, depthcoords)


class AlignVertsToCurveBUTTON(bpy.types.Panel):
    bl_category = "Tools"
    bl_label = "Curve Align"
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"
    #bl_context = "mesh_edit"

    def draw(self, context):
        layout = self.layout
        layout.operator("mesh.align_verts_to_curve")

def register():
    bpy.utils.register_class(AlignVertsToCurve)
    bpy.utils.register_class(AlignVertsToCurveBUTTON)


def unregister():
    bpy.utils.unregister_class(AlignVertsToCurve)
    bpy.utils.unregister_class(AlignVertsToCurveBUTTON)

if __name__ == "__main__":
    register()
