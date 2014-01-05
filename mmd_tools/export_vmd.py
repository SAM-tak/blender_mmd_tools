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
        self.__motion = None

    def execute(self, filepath, **args):
        self.__motion = vmd.File()

        vmd.save(filepath, self.__motion)

def export(filepath, **kwargs):
    exporter = __VmdExporter()
    exporter.execute(filepath, **kwargs)
