# -*- coding: utf-8 -*-

import os

import bpy
from bpy.types import PropertyGroup
from bpy.props import BoolProperty, EnumProperty, FloatProperty, FloatVectorProperty, IntProperty, StringProperty

from mmd_tools.core import material
from mmd_tools.core.material import FnMaterial


def _updateSphereMapType(prop, context):
    FnMaterial(prop.id_data).update_sphere_texture_type()

def _updateToonTexture(prop, context):
    mat = FnMaterial(prop.id_data)
    mmd_mat = prop.id_data.mmd_material
    if mmd_mat.is_shared_toon_texture:
        user_preferences = context.user_preferences
        addon_prefs = user_preferences.addons['mmd_tools'].preferences
        toon_path = os.path.join(addon_prefs.shared_toon_folder, 'toon%02d.bmp'%(mmd_mat.shared_toon_texture+1))
        mat.create_toon_texture(bpy.path.resolve_ncase(path=toon_path))
    elif mmd_mat.toon_texture != '':
        mat.create_toon_texture(mmd_mat.toon_texture)
    else:
        mat.remove_toon_texture()


#===========================================
# Property classes
#===========================================
class MMDMaterial(PropertyGroup):
    """ マテリアル
    """
    name_j = StringProperty(
        name='Name',
        description='Japanese Name',
        default='',
        )

    name_e = StringProperty(
        name='Name(Eng)',
        description='English Name',
        default='',
        )

    material_id = IntProperty(
        name='Material ID',
        default=-1
        )

    ambient_color = FloatVectorProperty(
        name='Ambient',
        subtype='COLOR',
        size=3,
        min=0,
        max=1,
        precision=3,
        step=0.1,
        default=[0, 0, 0],
        )

    shininess = FloatProperty(
        name='Shininess',
        min=0,
        max=500,
        step=100.0,
        default=0.0,
        )

    is_double_sided = BoolProperty(
        name='Double Sided',
        description='',
        default=True,
        )

    enabled_drop_shadow = BoolProperty(
        name='Drop Shadow',
        description='',
        default=True,
        )

    enabled_self_shadow_map = BoolProperty(
        name='Self Shadow Map',
        description='',
        default=True,
        )

    enabled_self_shadow = BoolProperty(
        name='Self Shadow',
        description='',
        default=True,
        )

    enabled_toon_edge = BoolProperty(
        name='Toon Edge',
        description='',
        default=True,
        )

    edge_color = FloatVectorProperty(
        name='Edge Color',
        subtype='COLOR',
        size=4,
        min=0,
        max=1,
        precision=3,
        step=0.1,
        default=[0, 0, 0, 1],
        )

    edge_weight = FloatProperty(
        name='Edge Weight',
        min=0,
        max=100,
        step=1.0,
        default=0.5,
        )

    sphere_texture_type = EnumProperty(
        name='Sphere Map Type',
        description='',
        items = [
            (str(material.SPHERE_MODE_OFF),    'Off',        '', 1),
            (str(material.SPHERE_MODE_MULT),   'Multiply',   '', 2),
            (str(material.SPHERE_MODE_ADD),    'Add',        '', 3),
            (str(material.SPHERE_MODE_SUBTEX), 'SubTexture', '', 4),
            ],
        update=_updateSphereMapType,
        )

    is_shared_toon_texture = BoolProperty(
        name='Use Shared Toon Texture',
        description='',
        default=False,
        update=_updateToonTexture,
        )

    toon_texture = StringProperty(
        name='Toon Texture',
        subtype='FILE_PATH',
        description='',
        default='',
        update=_updateToonTexture,
        )

    shared_toon_texture = IntProperty(
        name='Shared Toon Texture',
        description='',
        default=0,
        min=0,
        max=9,
        update=_updateToonTexture,
        )

    comment = StringProperty(
        name='Comment',
        )

