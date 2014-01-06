# -*- coding: utf-8 -*-
from . import vmd
from . import rigging
from . import bpyutils

import collections
import os
import copy
import logging
import shutil

import mathutils
import bpy
import bmesh

class __VmdExporter:

    def __init__(self):
        self.__vmdFile = vmd.File()
    
    
    def __exportArmatureTracksRecursive(self, bonename):
        pass
    
    
    def __exportArmatureTracks(self):
        """ Export bone animation.
        @return the dictionary to map Blender bone names to bone indices of the pmx.model instance.
        """
        
        for bone in self.__armature.bones:
            self.__exportArmatureTracksRecursive(bone.name)

    def execute(self, filepath, **args):
        
        self.__armature = args.get('armature', None)
        
        vmd.save(filepath, self.__vmdFile)

def export(filepath, **kwargs):
    exporter = __VmdExporter()
    exporter.execute(filepath, **kwargs)
