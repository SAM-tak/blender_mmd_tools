# -*- coding: utf-8 -*-
from . import vmd
from . import rigging
from . import bpyutils

import bpy
import re

class __VmdExporter:

    def __init__(self):
        self.__vmdFile = vmd.File()

    
    def __exportArmatureTracksRecursive(self, bonename):
        pass
    
    
    def __exportArmatureTracks(self):
        """ Export bone animation.
        @return the dictionary to map Blender bone names to bone indices of the pmx.model instance.
        """

        armature = self.__armature
        rePath = re.compile('^pose\.bones\["(.+)"\]\.([a-z_]+)$')
        boneanims = {}
        for fcurve in self.__armature.animation_data.action.fcurves:
            m = rePath.match(fcurve.data_path)
            if m and m.group(2) in ['location', 'rotation_quaternion']:
                #v = eval("armature."+fcurve.data_path+"["+str(fcurve.array_index)+"]")
                #print('fcurve = ', v, fcurve.array_index, m.group(1), len(fcurve.keyframe_points), fcurve.keyframe_points[0].co, fcurve.keyframe_points[-1].co)
                for i in fcurve.keyframe_points:
                    if m.group(1) not in boneanims:
                        boneanims[m.group(1)] = {}
                    kfs = boneanims[m.group(1)]
                    kf = None
                    if i.co[0] not in kfs:
                        kf = vmd.BoneFrameKey()
                        kf.frame_number = int(i.co[0])
                        kf.location = [0, 0, 0]
                        kf.rotation = [0, 0, 0, 0]
                        kf.interp = bytearray([
                                0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1,
                                0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0,
                                0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0,
                            ])
                        kfs[i.co[0]] = kf
                    else:
                        kf = kfs[i.co[0]]
                    if m.group(2) == 'location':
                        if fcurve.array_index == 2:
                            kf.location[fcurve.array_index] = -i.co[1]
                        else:
                            kf.location[fcurve.array_index] = i.co[1]
                    elif m.group(2) == 'rotation_quaternion':
                        if fcurve.array_index == 0:
                            kf.rotation[3] = i.co[1]
                        elif fcurve.array_index < 3:
                            kf.rotation[fcurve.array_index-1] = -i.co[1]
                        else:
                            kf.rotation[fcurve.array_index-1] = i.co[1]

        for k, v in boneanims.items():
            self.__vmdFile.boneAnimation.count += len(v)
            self.__vmdFile.boneAnimation[k] = v.values()


    def execute(self, filepath, **args):
        
        root = args.get('root', None)

        self.__armature = args.get('armature', None)
        self.__vmdFile.header.model_name = root.name

        self.__exportArmatureTracks()
        self.__vmdFile.save(filepath=filepath)

def export(filepath, **kwargs):
    exporter = __VmdExporter()
    exporter.execute(filepath, **kwargs)
