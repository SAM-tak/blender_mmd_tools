# -*- coding: utf-8 -*-
from . import vmd
from . import rigging
from . import bpyutils
from . import import_vmd

import bpy
import re
import mathutils

class __VmdExporter:

    def __init__(self):
        self.__vmdFile = vmd.File()


    @staticmethod
    def convertBlenderRotationToVMDBone(blender_bone, rotation):
        if not isinstance(rotation, mathutils.Quaternion):
            rot = mathutils.Quaternion()
            rot.x, rot.y, rot.z, rot.w = rotation
            rotation = rot
        mat = mathutils.Matrix()
        mat[0][0], mat[1][0], mat[2][0] = blender_bone.x_axis.x, blender_bone.y_axis.x, blender_bone.z_axis.x
        mat[0][1], mat[1][1], mat[2][1] = blender_bone.x_axis.y, blender_bone.y_axis.y, blender_bone.z_axis.y
        mat[0][2], mat[1][2], mat[2][2] = blender_bone.x_axis.z, blender_bone.y_axis.z, blender_bone.z_axis.z
        (vec, angle) = rotation.to_axis_angle()
        v = mathutils.Vector((-vec.x, -vec.z, -vec.y))
        return mathutils.Quaternion(mat*v, angle).normalized()


    @staticmethod
    def __fixRotations(rotation_ary):
        rotation_ary = list(rotation_ary)
        if len(rotation_ary) == 0:
            return rotation_ary

        pq = rotation_ary.pop(0)
        res = [pq]
        for q in rotation_ary:
            nq = q.copy()
            nq.negate()
            t1 = (pq.w-q.w)**2+(pq.x-q.x)**2+(pq.y-q.y)**2+(pq.z-q.z)**2
            t2 = (pq.w-nq.w)**2+(pq.x-nq.x)**2+(pq.y-nq.y)**2+(pq.z-nq.z)**2
            # t1 = pq.axis.dot(q.axis)
            # t2 = pq.axis.dot(nq.axis)
            if t2 < t1:
                res.append(nq)
                pq = nq
            else:
                res.append(q)
                pq = q
        return res


    def __exportArmatureTracks(self):
        """ Export bone animation.
        @return the dictionary to map Blender bone names to bone indices of the pmx.model instance.
        """

        armature = self.__armature
        rePath = re.compile('^pose\.bones\["(.+)"\]\.([a-z_]+)$')
        pose_bones = armature.pose.bones
        boneanims = {}
        qut_idx = [3, 0, 1, 2]
        for fcurve in self.__armature.animation_data.action.fcurves:
            m = rePath.match(fcurve.data_path)
            if m and m.group(1) in pose_bones and m.group(2) in ['location', 'rotation_quaternion']:
                #v = eval("armature."+fcurve.data_path+"["+str(fcurve.array_index)+"]")
                #print('fcurve = ', v, fcurve.array_index, m.group(1), len(fcurve.keyframe_points), fcurve.keyframe_points[0].co, fcurve.keyframe_points[-1].co)
                bonename = m.group(1)
                p_bone = pose_bones[bonename]
                if p_bone.is_mmd_shadow_bone:
                    continue
                for i in fcurve.keyframe_points:
                    if bonename not in boneanims:
                        boneanims[bonename] = {}
                    kfs = boneanims[bonename]
                    kf = None
                    if i.co[0] not in kfs:
                        kf = vmd.BoneFrameKey()
                        kf.frame_number = int(i.co[0])
                        kf.location = [0, 0, 0]
                        kf.rotation = [0, 0, 0, 1]
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
                        kf.location[fcurve.array_index] = i.co[1]
                    elif m.group(2) == 'rotation_quaternion':
                        kf.rotation[qut_idx[fcurve.array_index]] = i.co[1]

        for k, v in boneanims.items():
            self.__vmdFile.boneAnimation.count += len(v)
            p_bone = pose_bones[k]
            mat = import_vmd.VMDImporter.makeVMDBoneLocationToBlenderMatrix(p_bone)
            mat.invert()
            v = v.values()
            for i in v:
                loc = mat * mathutils.Vector(i.location) * self.__scale
                rot = self.convertBlenderRotationToVMDBone(p_bone, i.rotation)
                i.location = loc.xyz
                i.rotation = rot

            fixed_rot = self.__fixRotations(map(lambda i: i.rotation, v))
            ii = 0
            for i in v:
                rot = fixed_rot[ii]
                i.rotation = [rot.x, rot.y, rot.z, rot.w]
                ii += 1

            bonename = k
            if p_bone.mmd_bone.name_j != '':
                bonename = p_bone.mmd_bone.name_j
            else:
                bonename = p_bone.name
            self.__vmdFile.boneAnimation[bonename] = v


    def execute(self, filepath, **args):
        
        root = args.get('root', None)

        self.__armature = args.get('armature', None)
        self.__scale = 1.0/float(args.get('scale', 0.2))
        self.__vmdFile.header.model_name = root.name

        self.__exportArmatureTracks()
        self.__vmdFile.save(filepath=filepath)

def export(filepath, **kwargs):
    exporter = __VmdExporter()
    exporter.execute(filepath, **kwargs)
