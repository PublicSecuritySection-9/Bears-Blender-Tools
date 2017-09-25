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
    "name": "Bear Node Tools",
    "author": "Bjornar Froyse",
    "version": (0,0,0),
    "blender": (2, 76, 0),
    "location": "Node Editor Toolbar or Ctrl-Space",
    "description": "Various tools to enhance and speed up node-based workflow",
    "warning": "",
    "category": "Node",
}

import bpy, blf, bgl
from bpy.types import Operator, Panel, Menu
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty, StringProperty, FloatVectorProperty, CollectionProperty
from bpy_extras.io_utils import ImportHelper
from mathutils import Vector
from math import cos, sin, pi, hypot
from os import path
from glob import glob
from copy import copy

import bpy


def color_ramp_space_points(operator, context):
    space = context.space_data
    node_tree = space.node_tree
    node_active = context.active_node
    node_selected = context.selected_nodes

    # now we have the context, perform a simple operation
    if node_active in node_selected:
        node_selected.remove(node_active)
    if len(node_selected) != 1:
        operator.report({'ERROR'}, "2 nodes must be selected")
        return

    node_other, = node_selected

    # now we have 2 nodes to operate on
    if not node_active.inputs:
        operator.report({'ERROR'}, "Active node has no inputs")
        return

    if not node_other.outputs:
        operator.report({'ERROR'}, "Selected node has no outputs")
        return

    socket_in = node_active.inputs[0]
    socket_out = node_other.outputs[0]

    # add a link between the two nodes
    node_link = node_tree.links.new(socket_in, socket_out)


class ColorRampEvenlySpacePoints(bpy.types.Operator):
    """Tooltip"""
    bl_idname = "node.color_ramp_space_points"
    bl_label = "Space ColorRamp Weights"

    @classmethod
    def poll(cls, context):
        space = context.space_data
        return space.type == 'NODE_EDITOR'

    def execute(self, context):
        color_ramp_space_points(self, context)
        return {'FINISHED'}


class CustomNodeEditorButtons(bpy.types.Panel):
    bl_category = "BEAR"
    bl_label = "Evenly Space ColorRamp Points"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = "TOOLS"

    def draw(self, context):
        layout = self.layout
        layout.operator("node.color_ramp_space_points")

classes = [ColorRampEvenlySpacePoints, CustomNodeEditorButtons]

def register():
    for c in classes:
        bpy.utils.register_class(c)


def unregister():
    for c in reversed(classes):
        bpy.utils.unregister_class(c)


if __name__ == "__main__":
    register()
