# -*- coding: utf-8 -*-

import bpy
from bpy.types import Operator
from bpy_extras.io_utils import ImportHelper

from . import import_pmx
from . import import_pmd
from . import export_pmx
from . import import_vmd
from . import export_vmd
from . import bpyutils

from . import mmd_camera
from . import utils
from . import cycles_converter
from . import auto_scene_setup
from . import rigging

import logging
import logging.handlers
import traceback
import re


LOG_LEVEL_ITEMS = [
    ('DEBUG', '4. DEBUG', '', 1),
    ('INFO', '3. INFO', '', 2),
    ('WARNING', '2. WARNING', '', 3),
    ('ERROR', '1. ERROR', '', 4),
    ]

def log_handler(log_level, filepath=None):
    if filepath is None:
        handler = logging.StreamHandler()
    else:
        handler = logging.FileHandler(filepath, mode='w', encoding='utf-8')
    formatter = logging.Formatter('%(message)s')
    handler.setFormatter(formatter)
    return handler


###########################
# Import/Export Operators #
###########################
class ImportPmx(Operator, ImportHelper):
    bl_idname = 'mmd_tools.import_model'
    bl_label = 'Import Model file (.pmd, .pmx)'
    bl_description = 'Import a Model file (.pmd, .pmx)'
    bl_options = {'PRESET'}

    filename_ext = '.pmx'
    filter_glob = bpy.props.StringProperty(default='*.pmx;*.pmd', options={'HIDDEN'})

    scale = bpy.props.FloatProperty(name='Scale', default=0.2)
    renameBones = bpy.props.BoolProperty(name='Rename bones', default=True)
    hide_rigids = bpy.props.BoolProperty(name='Hide rigid bodies and joints', default=True)
    only_collisions = bpy.props.BoolProperty(name='Ignore rigid bodies', default=False)
    ignore_non_collision_groups = bpy.props.BoolProperty(name='Ignore  non collision groups', default=False)
    distance_of_ignore_collisions = bpy.props.FloatProperty(name='Distance of ignore collisions', default=1.5)
    use_mipmap = bpy.props.BoolProperty(name='use MIP maps for UV textures', default=True)
    sph_blend_factor = bpy.props.FloatProperty(name='influence of .sph textures', default=1.0)
    spa_blend_factor = bpy.props.FloatProperty(name='influence of .spa textures', default=1.0)
    log_level = bpy.props.EnumProperty(items=LOG_LEVEL_ITEMS, name='Log level', default='DEBUG')
    save_log = bpy.props.BoolProperty(name='Create a log file', default=False)

    def execute(self, context):
        logger = logging.getLogger()
        logger.setLevel(self.log_level)
        if self.save_log:
            handler = log_handler(self.log_level, filepath=self.filepath + '.mmd_tools.import.log')
        else:
            handler = log_handler(self.log_level)
        logger.addHandler(handler)
        try:
            if re.search('\.pmd$', self.filepath, flags=re.I):
                import_pmd.import_pmd(
                    filepath=self.filepath,
                    scale=self.scale,
                    rename_LR_bones=self.renameBones,
                    hide_rigids=self.hide_rigids,
                    only_collisions=self.only_collisions,
                    ignore_non_collision_groups=self.ignore_non_collision_groups,
                    distance_of_ignore_collisions=self.distance_of_ignore_collisions,
                    use_mipmap=self.use_mipmap,
                    sph_blend_factor=self.sph_blend_factor,
                    spa_blend_factor=self.spa_blend_factor
                    )
            else:
                importer = import_pmx.PMXImporter()
                importer.execute(
                    filepath=self.filepath,
                    scale=self.scale,
                    rename_LR_bones=self.renameBones,
                    hide_rigids=self.hide_rigids,
                    only_collisions=self.only_collisions,
                    ignore_non_collision_groups=self.ignore_non_collision_groups,
                    distance_of_ignore_collisions=self.distance_of_ignore_collisions,
                    use_mipmap=self.use_mipmap,
                    sph_blend_factor=self.sph_blend_factor,
                    spa_blend_factor=self.spa_blend_factor
                    )
        except Exception as e:
            logging.error(traceback.format_exc())
            self.report({'ERROR'}, str(e))
        finally:
            logger.removeHandler(handler)

        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        wm.fileselect_add(self)
        return {'RUNNING_MODAL'}


class ImportVmd(Operator, ImportHelper):
    bl_idname = 'mmd_tools.import_vmd'
    bl_label = 'Import VMD file (.vmd)'
    bl_description = 'Import a VMD file (.vmd)'
    bl_options = {'PRESET'}

    filename_ext = '.vmd'
    filter_glob = bpy.props.StringProperty(default='*.vmd', options={'HIDDEN'})

    scale = bpy.props.FloatProperty(name='Scale', default=0.2)
    margin = bpy.props.IntProperty(name='Margin', default=5, min=0)
    update_scene_settings = bpy.props.BoolProperty(name='Update scene settings', default=True)

    def execute(self, context):
        importer = import_vmd.VMDImporter(filepath=self.filepath, scale=self.scale, frame_margin=self.margin)
        for i in context.selected_objects:
            importer.assign(i)
        if self.update_scene_settings:
            auto_scene_setup.setupFrameRanges()
            auto_scene_setup.setupFps()

        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        wm.fileselect_add(self)
        return {'RUNNING_MODAL'}


class ImportVmdToMMDModel(Operator, ImportHelper):
    bl_idname = 'mmd_tools.import_vmd_to_mmd_model'
    bl_label = 'Import VMD file To MMD Model'
    bl_description = 'Import a VMD file (.vmd)'
    bl_options = {'PRESET'}

    filename_ext = '.vmd'
    filter_glob = bpy.props.StringProperty(default='*.vmd', options={'HIDDEN'})

    margin = bpy.props.IntProperty(name='Margin', default=5, min=0)
    update_scene_settings = bpy.props.BoolProperty(name='Update scene settings', default=True)

    def execute(self, context):
        obj = context.active_object
        root = rigging.Rig.findRoot(obj)
        rig = rigging.Rig(root)
        importer = import_vmd.VMDImporter(filepath=self.filepath, scale=root.mmd_root.scale, frame_margin=self.margin)
        arm = rig.armature()
        t = arm.hide
        arm.hide = False
        importer.assign(arm)
        arm.hide = t
        for i in rig.meshes():
            t = i.hide
            i.hide = False
            importer.assign(i)
            i.hide = t
        if self.update_scene_settings:
            auto_scene_setup.setupFrameRanges()
            auto_scene_setup.setupFps()

        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        wm.fileselect_add(self)
        return {'RUNNING_MODAL'}


class ExportPmx(Operator, ImportHelper):
    bl_idname = 'mmd_tools.export_pmx'
    bl_label = 'Export PMX file (.pmx)'
    bl_description = 'Export a PMX file (.pmx)'
    bl_options = {'PRESET'}

    filename_ext = '.pmx'
    filter_glob = bpy.props.StringProperty(default='*.pmx', options={'HIDDEN'})

    # scale = bpy.props.FloatProperty(name='Scale', default=0.2)
    copy_textures = bpy.props.BoolProperty(name='Copy textures', default=False)

    log_level = bpy.props.EnumProperty(items=LOG_LEVEL_ITEMS, name='Log level', default='DEBUG')
    save_log = bpy.props.BoolProperty(name='Create a log file', default=False)

    def execute(self, context):
        logger = logging.getLogger()
        logger.setLevel(self.log_level)
        if self.save_log:
            handler = log_handler(self.log_level, filepath=self.filepath + '.mmd_tools.export.log')
        else:
            handler = log_handler(self.log_level)
        logger.addHandler(handler)

        root = rigging.Rig.findRoot(context.active_object)
        rig = rigging.Rig(root)
        rig.clean()
        try:
            export_pmx.export(
                filepath=self.filepath,
                scale=root.mmd_root.scale,
                root=rig.rootObject(),
                armature=rig.armature(),
                meshes=rig.meshes(),
                rigid_bodies=rig.rigidBodies(),
                joints=rig.joints(),
                copy_textures=self.copy_textures,
                )
        finally:
            logger.removeHandler(handler)

        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        wm.fileselect_add(self)
        return {'RUNNING_MODAL'}


class ExportVmd(Operator, ImportHelper):
    bl_idname = 'mmd_tools.export_vmd'
    bl_label = 'Export VMD file (.vmd)'
    bl_description = 'Export a VMD file (.vmd)'
    bl_options = {'PRESET'}
    
    filename_ext = '.vmd'
    filter_glob = bpy.props.StringProperty(default='*.vmd', options={'HIDDEN'})
    
    log_level = bpy.props.EnumProperty(items=LOG_LEVEL_ITEMS, name='Log level', default='DEBUG')
    save_log = bpy.props.BoolProperty(name='Create a log file', default=False)
    
    def execute(self, context):
        logger = logging.getLogger()
        logger.setLevel(self.log_level)
        if self.save_log:
            handler = log_handler(self.log_level, filepath=self.filepath + '.mmd_tools.export.log')
        else:
            handler = log_handler(self.log_level)
        logger.addHandler(handler)
        
        root = rigging.Rig.findRoot(context.active_object)
        rig = rigging.Rig(root)
        rig.clean()
        try:
            export_vmd.export(
                              filepath=self.filepath,
                              scale=root.mmd_root.scale,
                              root=rig.rootObject(),
                              armature=rig.armature(),
                              meshes=rig.meshes()
                              )
        finally:
            logger.removeHandler(handler)
        
        return {'FINISHED'}
    
    def invoke(self, context, event):
        wm = context.window_manager
        wm.fileselect_add(self)
        return {'RUNNING_MODAL'}


####################
# Object Operators #
####################
class SeparateByMaterials(Operator):
    bl_idname = 'mmd_tools.separate_by_materials'
    bl_label = 'Separate by materials'
    bl_description = 'Separate by materials'
    bl_options = {'PRESET'}

    def execute(self, context):
        obj = context.active_object
        if obj is None or obj.type != 'MESH':
            return {'FINISHED'}

        utils.separateByMaterials(obj)
        return {'FINISHED'}


##################
# View Operators #
##################
class SetGLSLShading(Operator):
    bl_idname = 'mmd_tools.set_glsl_shading'
    bl_label = 'GLSL View'
    bl_description = ''
    bl_options = {'PRESET'}

    def execute(self, context):
        bpy.ops.mmd_tools.reset_shading()
        bpy.context.scene.render.engine = 'BLENDER_RENDER'
        for i in filter(lambda x: x.type == 'MESH', context.scene.objects):
            for s in i.material_slots:
                s.material.use_shadeless = False
        if len(list(filter(lambda x: x.is_mmd_glsl_light, context.scene.objects))) == 0:
            bpy.ops.object.lamp_add(type='HEMI', view_align=False, location=(0, 0, 0), rotation=(0, 0, 0))
            light = context.selected_objects[0]
            light.is_mmd_glsl_light = True
            light.hide = True

        context.area.spaces[0].viewport_shade='TEXTURED'
        bpy.context.scene.game_settings.material_mode = 'GLSL'
        return {'FINISHED'}

class SetShadelessGLSLShading(Operator):
    bl_idname = 'mmd_tools.set_shadeless_glsl_shading'
    bl_label = 'Shadeless GLSL View'
    bl_description = ''
    bl_options = {'PRESET'}

    def execute(self, context):
        bpy.ops.mmd_tools.reset_shading()
        bpy.context.scene.render.engine = 'BLENDER_RENDER'
        for i in filter(lambda x: x.type == 'MESH', context.scene.objects):
            for s in i.material_slots:
                s.material.use_shadeless = True
        for i in filter(lambda x: x.is_mmd_glsl_light, context.scene.objects):
            context.scene.objects.unlink(i)

        try:
            bpy.context.scene.display_settings.display_device = 'None'
        except TypeError:
            pass # Blender was built without OpenColorIO:

        context.area.spaces[0].viewport_shade='TEXTURED'
        bpy.context.scene.game_settings.material_mode = 'GLSL'
        return {'FINISHED'}

class SetCyclesRendering(Operator):
    bl_idname = 'mmd_tools.set_cycles_rendering'
    bl_label = 'Cycles'
    bl_description = 'Convert blender render shader to Cycles shader'
    bl_options = {'PRESET'}

    def execute(self, context):
        bpy.ops.mmd_tools.reset_shading()
        bpy.context.scene.render.engine = 'CYCLES'
        for i in filter(lambda x: x.type == 'MESH', context.scene.objects):
            cycles_converter.convertToCyclesShader(i)
        context.area.spaces[0].viewport_shade='MATERIAL'
        return {'FINISHED'}

class ResetShading(Operator):
    bl_idname = 'mmd_tools.reset_shading'
    bl_label = 'Reset View'
    bl_description = ''
    bl_options = {'PRESET'}

    def execute(self, context):
        bpy.context.scene.render.engine = 'BLENDER_RENDER'
        for i in filter(lambda x: x.type == 'MESH', context.scene.objects):
            for s in i.material_slots:
                s.material.use_shadeless = False
                s.material.use_nodes = False

        for i in filter(lambda x: x.is_mmd_glsl_light, context.scene.objects):
            context.scene.objects.unlink(i)

        bpy.context.scene.display_settings.display_device = 'sRGB'
        context.area.spaces[0].viewport_shade='SOLID'
        bpy.context.scene.game_settings.material_mode = 'MULTITEXTURE'
        return {'FINISHED'}

########################
# MMD Camera Oparators #
########################
class ConvertToMMDCamera(Operator):
    bl_idname = 'mmd_tools.convert_to_mmd_camera'
    bl_label = 'Convert to MMD Camera'
    bl_description = 'create a camera rig for mmd.'
    bl_options = {'PRESET'}

    def execute(self, context):
        mmd_camera.MMDCamera.convertToMMDCamera(context.active_object)
        return {'FINISHED'}


#######################
# Animation Operators #
#######################
class SetFrameRange(Operator):
    bl_idname = 'mmd_tools.set_frame_range'
    bl_label = 'Set range'
    bl_description = 'Set the frame range to best values to play the animation from start to finish. And set the frame rate to 30.0.'
    bl_options = {'PRESET'}

    def execute(self, context):
        auto_scene_setup.setupFrameRanges()
        auto_scene_setup.setupFps()
        return {'FINISHED'}


##########################
# Display Item Operators #
##########################
class AddDisplayItemFrame(Operator):
    bl_idname = 'mmd_tools.add_display_item_frame'
    bl_label = 'Add Display Item Frame'
    bl_description = ''
    bl_options = {'PRESET'}

    def execute(self, context):
        obj = context.active_object
        root = rigging.Rig.findRoot(obj)
        mmd_root = root.mmd_root
        item = mmd_root.display_item_frames.add()
        item.name = 'Display Frame'
        return {'FINISHED'}

class RemoveDisplayItemFrame(Operator):
    bl_idname = 'mmd_tools.remove_display_item_frame'
    bl_label = 'Remove Display Item Frame'
    bl_description = ''
    bl_options = {'PRESET'}

    def execute(self, context):
        obj = context.active_object
        root = rigging.Rig.findRoot(obj)
        mmd_root = root.mmd_root
        mmd_root.display_item_frames.remove(mmd_root.active_display_item_frame)
        return {'FINISHED'}

class MoveUpDisplayItemFrame(Operator):
    bl_idname = 'mmd_tools.move_up_display_item_frame'
    bl_label = 'Move Up Display Item Frame'
    bl_description = ''
    bl_options = {'PRESET'}

    def execute(self, context):
        obj = context.active_object
        root = rigging.Rig.findRoot(obj)
        mmd_root = root.mmd_root
        if mmd_root.active_display_item_frame <= 0:
            return {'FINISHED'}

        mmd_root.display_item_frames.move(mmd_root.active_display_item_frame, mmd_root.active_display_item_frame-1)
        mmd_root.active_display_item_frame -= 1
        return {'FINISHED'}

class MoveDownDisplayItemFrame(Operator):
    bl_idname = 'mmd_tools.move_down_display_item_frame'
    bl_label = 'Move Down Display Item Frame'
    bl_description = ''
    bl_options = {'PRESET'}

    def execute(self, context):
        obj = context.active_object
        root = rigging.Rig.findRoot(obj)
        mmd_root = root.mmd_root
        if len( mmd_root.display_item_frames)-1 <= mmd_root.active_display_item_frame:
            return {'FINISHED'}

        mmd_root.display_item_frames.move(mmd_root.active_display_item_frame, mmd_root.active_display_item_frame+1)
        mmd_root.active_display_item_frame += 1
        return {'FINISHED'}

class AddDisplayItem(Operator):
    bl_idname = 'mmd_tools.add_display_item'
    bl_label = 'Add Display Item Frame'
    bl_description = ''
    bl_options = {'PRESET'}

    def execute(self, context):
        obj = context.active_object
        root = rigging.Rig.findRoot(obj)
        mmd_root = root.mmd_root
        frame = mmd_root.display_item_frames[mmd_root.active_display_item_frame]
        item = frame.items.add()
        item.name = 'Display Item'
        return {'FINISHED'}

class RemoveDisplayItem(Operator):
    bl_idname = 'mmd_tools.remove_display_item'
    bl_label = 'Remove Display Item Frame'
    bl_description = ''
    bl_options = {'PRESET'}

    def execute(self, context):
        obj = context.active_object
        root = rigging.Rig.findRoot(obj)
        mmd_root = root.mmd_root
        frame = mmd_root.display_item_frames[mmd_root.active_display_item_frame]
        frame.items.remove(frame.active_item)
        return {'FINISHED'}

class MoveUpDisplayItem(Operator):
    bl_idname = 'mmd_tools.move_up_display_item'
    bl_label = 'Move Up Display Item Frame'
    bl_description = ''
    bl_options = {'PRESET'}

    def execute(self, context):
        obj = context.active_object
        root = rigging.Rig.findRoot(obj)
        mmd_root = root.mmd_root
        frame = mmd_root.display_item_frames[mmd_root.active_display_item_frame]
        if frame.active_item <= 0:
            return {'FINISHED'}

        frame.items.move(frame.active_item, frame.active_item-1)
        frame.active_item -= 1
        return {'FINISHED'}

class MoveDownDisplayItem(Operator):
    bl_idname = 'mmd_tools.move_down_display_item'
    bl_label = 'Move Down Display Item Frame'
    bl_description = ''
    bl_options = {'PRESET'}

    def execute(self, context):
        obj = context.active_object
        root = rigging.Rig.findRoot(obj)
        mmd_root = root.mmd_root
        frame = mmd_root.display_item_frames[mmd_root.active_display_item_frame]
        if len(frame.items)-1 <= frame.active_item:
            return {'FINISHED'}

        frame.items.move(frame.active_item, frame.active_item+1)
        frame.active_item += 1
        return {'FINISHED'}

class SelectCurrentDisplayItem(Operator):
    bl_idname = 'mmd_tools.select_current_display_item'
    bl_label = 'Select Current Display Item Frame'
    bl_description = ''
    bl_options = {'PRESET'}

    def execute(self, context):
        obj = context.active_object
        root = rigging.Rig.findRoot(obj)
        rig = rigging.Rig(root)
        mmd_root = root.mmd_root

        try:
            bpy.ops.object.mode_set(mode='OBJECT')
        except Exception:
            pass

        arm = rig.armature()
        for i in context.scene.objects:
            i.select = False
        arm.hide = False
        arm.select = True
        context.scene.objects.active = arm

        bpy.ops.object.mode_set(mode='POSE')
        frame = mmd_root.display_item_frames[mmd_root.active_display_item_frame]
        item = frame.items[frame.active_item]
        bone_name = item.name
        for i in arm.pose.bones:
            i.bone.select = (i.name == bone_name)
        return {'FINISHED'}

#######################
# Edit Menu Operators #
#######################

class CreateMMDModelRoot(Operator):
    bl_idname = 'mmd_tools.create_mmd_model_root_object'
    bl_label = 'Create a MMD Model Root Object'
    bl_description = ''
    bl_options = {'PRESET'}

    scale = bpy.props.FloatProperty(name='Scale', default=0.2)

    def execute(self, context):
        rig = rigging.Rig.create('New MMD Model', 'New MMD Model', self.scale)
        arm = rig.armature()
        with bpyutils.edit_object(arm) as data:
            bone = data.edit_bones.new(name=u'全ての親')
            bone.head = [0.0, 0.0, 0.0]
            bone.tail = [0.0, 0.0, 1.0*self.scale]
        mmd_root = rig.rootObject().mmd_root
        frame_root = mmd_root.display_item_frames.add()
        frame_root.name = 'Root'
        frame_root.is_special = True
        frame_facial = mmd_root.display_item_frames.add()
        frame_facial.name = u'表情'
        frame_facial.is_special = True

        return {'FINISHED'}

    def invoke(self, context, event):
        vm = context.window_manager
        return vm.invoke_props_dialog(self)
