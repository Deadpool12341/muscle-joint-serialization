import math


class MuscleJointGroup:
    def __init__(self,
                 muscleName="Muscle",
                 muscleLength=5.0,
                 compressionFactor=1.0,
                 stretchFactor=1.0,
                 stretchOffset=None,
                 compressionOffset=None):
        """
        A joint-based muscle rig system inspired by techniques used in *God of War: Ragnarök*.

        This class represents a systematic joint-based rig designed to align with the curved fiber
        structure of anatomical muscles. It supports dynamic deformation behavior based on stretch
        and compression while maintaining volume preservation. The system is ideal for simulating
        realistic muscle behavior in character rigs by driving scale or position of intermediate joints
        based on fiber length changes.

        :param muscleName: (str) The name of the muscle group.
        :param muscleLength: (float) The original/rest length of the muscle.
        :param compressionFactor: (float) The amount of compression deformation applied (scale multiplier).
        :param stretchFactor: (float) The amount of stretch deformation applied (scale multiplier).
        :param stretchOffset: (float or None) Optional offset applied when the muscle is stretched.
        :param compressionOffset: (float or None) Optional offset applied when the muscle is compressed.

        """
        self.muscleName = muscleName
        self.muscleLength = muscleLength
        self.compressionFactor = compressionFactor
        self.stretchFactor = stretchFactor
        self.stretchOffset = stretchOffset
        self.compressionOffset = compressionOffset
        self.muscleOrigin = None
        self.muscleInsertion = None
        self.muscleBase = None
        self.muscleTip = None
        self.muscleDriver = None
        self.mainPointConstraint = None
        self.mainAimConstraint = None
        self.muscleOffset = None
        self.muscleJoint = None
        # edit mode:
        self.ptConstraintsEdits = []
        self.originLoc = None
        self.insertionLoc = None
        self.centerLoc = None

        # creation
        self.create()
        self.edit()

    @staticmethod
    def createJoint(jointName, parent=None, radius=1.0):
        jnt = mc.createNode("joint", name=jointName)
        mc.setAttr('{0}.radius'.format(jnt), radius)
        if parent:
            mc.parent(jnt, parent)
            mc.setAttr('{0}.t'.format(jnt), 0, 0, 0)
            mc.setAttr('{0}.r'.format(jnt), 0, 0, 0)
            mc.setAttr('{0}.jo'.format(jnt), 0, 0, 0)
        return jnt

    def create(self):
        """ construct muscle joint group"""
        self.muscleOrigin = self.createJoint('{0}_muscleOrigin'.format(self.muscleName))

        self.muscleInsertion = self.createJoint('{0}_muscleInsertion'.format(self.muscleName))

        mc.setAttr('{0}.tx'.format(self.muscleInsertion), self.muscleLength)
        # use Y axis as aim axis
        mc.delete(mc.aimConstraint(self.muscleInsertion, self.muscleOrigin, aimVector=[0, 1, 0], upVector=[1, 0, 0],
                                   worldUpType='scene', offset=[0, 0, 0], weight=1))

        self.muscleBase = self.createJoint('{0}_muscleBase'.format(self.muscleName), radius=0.5)
        mc.pointConstraint(self.muscleOrigin, self.muscleBase, maintainOffset=False, weight=1)
        # use Y axis as the aim vector and X axis as the up vector
        self.mainAimConstraint = mc.aimConstraint(self.muscleInsertion, self.muscleBase, aimVector=[0, 1, 0],
                                                  upVector=[1, 0, 0],
                                                  worldUpType='objectrotation', worldUpObject=self.muscleOrigin,
                                                  worldUpVector=[1, 0, 0])

        self.muscleTip = self.createJoint('{0}_muscleTip'.format(self.muscleName), radius=0.5, parent=self.muscleBase)
        mc.pointConstraint(self.muscleInsertion, self.muscleTip, maintainOffset=False, weight=1)

        self.muscleDriver = self.createJoint('{0}_muscleDriver'.format(self.muscleName), radius=0.5,
                                             parent=self.muscleBase)
        self.mainPointConstraint = mc.pointConstraint(self.muscleBase, self.muscleTip, self.muscleDriver,
                                                      maintainOffset=False,
                                                      weight=1)

        mc.parent(self.muscleBase, self.muscleOrigin)
        self.muscleOffset = self.createJoint('{0}_muscleOffset'.format(self.muscleName), radius=0.75,
                                             parent=self.muscleDriver)
        self.muscleJoint = self.createJoint('{0}_JOmuscle'.format(self.muscleName), radius=1.0,
                                            parent=self.muscleOffset)

        self._addSDK()

    def edit(self):
        """Enter the edit mode"""

        def createSpaceLocator(scaleValue, **kwargs):
            loc = mc.spaceLocator(**kwargs)[0]
            for axis in 'XYZ':
                mc.setAttr('{0}.localScale{1}'.format(loc, axis), scaleValue)
            return loc

        mc.setAttr('{0}.overrideEnabled'.format(self.muscleOrigin), 1)
        mc.setAttr('{0}.overrideDisplayType'.format(self.muscleOrigin), 1)
        mc.setAttr('{0}.overrideEnabled'.format(self.muscleInsertion), 1)
        mc.setAttr('{0}.overrideDisplayType'.format(self.muscleInsertion), 1)

        self.originLoc = createSpaceLocator(0.1, name='{0}_muscleOrigin_loc'.format(self.muscleName))
        # if self.originAttachObj:
        #     mc.parent(self.originLoc, self.originAttachObj)

        # mc.delete(mc.pointConstraint(self.muscleOrigin, self.originLoc, mo=False, w=True))
        mc.matchTransform(self.originLoc, self.muscleOrigin, position=True, rotation=False, scale=False)
        self.ptConstraintsEdits.append(mc.pointConstraint(self.originLoc, self.muscleOrigin, mo=False, w=True)[0])
        self.insertionLoc = createSpaceLocator(0.1, name='{0}_muscleInsertion_loc'.format(self.muscleName))

        # if self.insertionAttachObj:
        #     mc.parent(self.insertionLoc, self.insertionAttachObj)

        # mc.delete(mc.pointConstraint(self.muscleInsertion, self.insertionLoc, mo=False, w=True))
        mc.matchTransform(self.insertionLoc, self.muscleInsertion, position=True, rotation=False, scale=False)
        self.ptConstraintsEdits.append(
            mc.pointConstraint(self.insertionLoc, self.muscleInsertion, mo=False, w=True)[0])

        # use Y axis as aim axis: look at each other
        mc.aimConstraint(self.insertionLoc, self.originLoc, aimVector=[0, 1, 0], upVector=[1, 0, 0],
                         worldUpType='scene', offset=[0, 0, 0], weight=1)
        mc.aimConstraint(self.originLoc, self.insertionLoc, aimVector=[0, -1, 0], upVector=[1, 0, 0],
                         worldUpType='scene', offset=[0, 0, 0], weight=1)

        driverGrp = mc.group(name='{0}_muscleCenter_grp'.format(self.muscleName), empty=True)
        self.centerLoc = createSpaceLocator(0.1, name='{0}_muscleCenter_loc'.format(self.muscleName))
        mc.parent(self.centerLoc, driverGrp)
        mc.matchTransform(driverGrp, self.muscleDriver, position=True, rotation=True, scale=False)
        # mc.delete(mc.pointConstraint(self.muscleDriver, driverGrp, mo=False, w=True))
        mc.parent(driverGrp, self.originLoc)
        mc.pointConstraint(self.originLoc, self.insertionLoc, driverGrp, mo=True, w=True)
        # mc.setAttr('{0}.r'.format(driverGrp), 0, 0, 0)
        mc.delete(self.mainPointConstraint)
        self.ptConstraintsEdits.append(mc.pointConstraint(self.centerLoc, self.muscleDriver, mo=False, w=True)[0])

    def update(self):
        """Apply the edits"""
        # remove control
        for ptConstraint_tmp in self.ptConstraintsEdits:
            if mc.objExists(ptConstraint_tmp):
                mc.delete(ptConstraint_tmp)

        for loc in [self.originLoc, self.insertionLoc, self.centerLoc]:
            if mc.objExists(loc):
                mc.delete(loc)

        mc.setAttr('{0}.overrideEnabled'.format(self.muscleOrigin), 0)
        mc.setAttr('{0}.overrideDisplayType'.format(self.muscleOrigin), 0)
        mc.setAttr('{0}.overrideEnabled'.format(self.muscleInsertion), 0)
        mc.setAttr('{0}.overrideDisplayType'.format(self.muscleInsertion), 0)

        mc.delete(self.mainAimConstraint)

        self.mainPointConstraint = mc.pointConstraint(self.muscleBase, self.muscleTip, self.muscleDriver, mo=True,
                                                      weight=1)[0]
        # use Y axis as aim axis
        mc.delete(mc.aimConstraint(self.muscleInsertion, self.muscleOrigin, aimVector=[0, 1, 0], upVector=[1, 0, 0],
                                   worldUpType='scene', offset=[0, 0, 0], weight=1))

        self.mainAimConstraint = mc.aimConstraint(self.muscleInsertion, self.muscleBase, aimVector=[0, 1, 0],
                                                  upVector=[1, 0, 0],
                                                  worldUpType='objectrotation', worldUpObject=self.muscleOrigin,
                                                  worldUpVector=[1, 0, 0])[0]
        # remove existing sdk nodes
        animCurveNodes = mc.ls(mc.listConnections(self.muscleJoint, s=True, d=False),
                               type=('animCurveUU', 'animCurveUL'))
        mc.delete(animCurveNodes)
        self._addSDK()

    def delete(self):
        try:
            self.update()
        except RuntimeError as e:
            print(type(e).__name__, e)

        if mc.objExists(self.muscleOrigin):
            mc.delete(self.muscleOrigin)

        if mc.objExists(self.muscleInsertion):
            mc.delete(self.muscleInsertion)

    def _addSDK(self):
        """
        Adds driven keyframe relationships to simulate muscle deformation based on the Y-translation
        of the muscle tip joint. This function sets up squash and stretch behavior by keying the
        scale and translation of the muscle joint across all axes (X, Y, Z).
        """
        xzSquashScale = math.sqrt(1.0 / self.compressionFactor)
        xzStretchScale = math.sqrt(1.0 / self.stretchFactor)

        if self.stretchOffset is None:
            stretchOffset = [0.0, 0.0, 0.0]
        else:
            stretchOffset = self.stretchOffset
        if self.compressionOffset is None:
            compressionOffset = [0.0, 0.0, 0.0]
        else:
            compressionOffset = self.compressionOffset

        restLength = mc.getAttr('{0}.translateY'.format(self.muscleTip))

        for index, axis in enumerate('XYZ'):
            # relax length
            mc.setAttr('{0}.scale{1}'.format(self.muscleJoint, axis), 1.0)
            mc.setAttr('{0}.translate{1}'.format(self.muscleJoint, axis), 0.0)
            mc.setDrivenKeyframe('{0}.scale{1}'.format(self.muscleJoint, axis),
                                 currentDriver='{0}.translateY'.format(self.muscleTip), inTangentType="linear",
                                 outTangentType="linear")
            mc.setDrivenKeyframe('{0}.translate{1}'.format(self.muscleJoint, axis),
                                 currentDriver='{0}.translateY'.format(self.muscleTip), inTangentType="linear",
                                 outTangentType="linear")

            # stretch length
            mc.setAttr('{0}.translateY'.format(self.muscleTip), restLength * self.stretchFactor)
            if axis == 'Y':
                mc.setAttr('{0}.scale{1}'.format(self.muscleJoint, axis), self.stretchFactor)
            else:
                mc.setAttr('{0}.scale{1}'.format(self.muscleJoint, axis), xzStretchScale)
                mc.setAttr('{0}.translate{1}'.format(self.muscleJoint, axis), stretchOffset[index])

            mc.setDrivenKeyframe('{0}.scale{1}'.format(self.muscleJoint, axis),
                                 currentDriver='{0}.translateY'.format(self.muscleTip), inTangentType="linear",
                                 outTangentType="linear")
            mc.setDrivenKeyframe('{0}.translate{1}'.format(self.muscleJoint, axis),
                                 currentDriver='{0}.translateY'.format(self.muscleTip), inTangentType="linear",
                                 outTangentType="linear")
            # compression length
            mc.setAttr('{0}.translateY'.format(self.muscleTip), restLength * self.compressionFactor)
            if axis == 'Y':
                mc.setAttr('{0}.scale{1}'.format(self.muscleJoint, axis), self.compressionFactor)
            else:
                mc.setAttr('{0}.scale{1}'.format(self.muscleJoint, axis), xzSquashScale)
                mc.setAttr('{0}.translate{1}'.format(self.muscleJoint, axis), compressionOffset[index])

            mc.setDrivenKeyframe('{0}.scale{1}'.format(self.muscleJoint, axis),
                                 currentDriver='{0}.translateY'.format(self.muscleTip),
                                 inTangentType="linear", outTangentType="linear")
            mc.setDrivenKeyframe('{0}.translate{1}'.format(self.muscleJoint, axis),
                                 currentDriver='{0}.translateY'.format(self.muscleTip),
                                 inTangentType="linear", outTangentType="linear")

            mc.setAttr('{0}.translateY'.format(self.muscleTip), restLength)

    @classmethod
    def createFromAttachObjs(cls, muscleName, originAttachObj, insertionAttachObj, compressionFactor=1.0,
                             stretchFactor=1.0, stretchOffset=None, compressionOffset=None):

        originAttachPos = om.MVector(mc.xform(originAttachObj, translation=True, worldSpace=True, query=True))
        insertionAttachPos = om.MVector(mc.xform(insertionAttachObj, translation=True, worldSpace=True, query=True))
        muscleLength = om.MVector(insertionAttachPos - originAttachPos).length()
        muscleJointGroup = cls(muscleName, muscleLength, compressionFactor, stretchFactor, compressionOffset,
                               stretchOffset)

        # edit mode
        mc.matchTransform(muscleJointGroup.originLoc, originAttachObj)
        mc.matchTransform(muscleJointGroup.insertionLoc, insertionAttachObj)

        muscleJointGroup.originAttachObj = originAttachObj
        muscleJointGroup.insertionAttachObj = insertionAttachObj

        mc.parent(muscleJointGroup.muscleOrigin, originAttachObj)
        mc.parent(muscleJointGroup.muscleInsertion, insertionAttachObj)
        mc.parent(muscleJointGroup.originLoc, originAttachObj)
        mc.parent(muscleJointGroup.insertionLoc, insertionAttachObj)

        return muscleJointGroup

    @classmethod
    def createFromBlueprint(cls, bpOrigin, bpInsertion, bpCenter=None,
                            originAttachObj=None, insertionAttachObj=None,
                            compressionFactor=0.5, stretchFactor=1.5,
                            stretchOffset=None, compressionOffset=None):

        def removeBpPrefix(name):
            return name.split("_")[0].removeprefix("bp")

        if not mc.ls(bpOrigin):
            raise RuntimeError("fpOrigin: {bpOrigin} does not exist in the scene.")

        if not mc.ls(bpInsertion):
            raise RuntimeError("bpInsertion: {bpInsertion} does not exist in the scene.")

        originPos = om.MVector(mc.xform(bpOrigin, translation=True, worldSpace=True, query=True))
        insertionPos = om.MVector(mc.xform(bpInsertion, translation=True, worldSpace=True, query=True))
        muscleLength = om.MVector(insertionPos - originPos).length()
        muscleName = removeBpPrefix(bpOrigin)
        muscleJointGroup = cls(muscleName, muscleLength, compressionFactor, stretchFactor, compressionOffset,
                               stretchOffset)

        # edit mode
        mc.matchTransform(muscleJointGroup.originLoc, bpOrigin, position=True, rotation=False, scale=False)
        mc.matchTransform(muscleJointGroup.insertionLoc, bpInsertion, position=True, rotation=False, scale=False)

        if mc.ls(bpCenter):
            mc.matchTransform(muscleJointGroup.centerLoc, bpCenter, position=True, rotation=False, scale=False)

        muscleJointGroup.originAttachObj = originAttachObj
        muscleJointGroup.insertionAttachObj = insertionAttachObj

        mc.parent(muscleJointGroup.muscleOrigin, originAttachObj)
        mc.parent(muscleJointGroup.muscleInsertion, insertionAttachObj)
        mc.parent(muscleJointGroup.originLoc, originAttachObj)
        mc.parent(muscleJointGroup.insertionLoc, insertionAttachObj)
        return muscleJointGroup

    def mirror(self, newMuscleName, originAttachObj, insertionAttachObj):

        originPos = om.MVector(mc.xform(self.muscleOrigin, translation=True, ws=True, query=True))
        insertionPos = om.MVector(mc.xform(self.muscleInsertion, translation=True, ws=True, query=True))
        centerPos = om.MVector(mc.xform(self.muscleDriver, translation=True, ws=True, query=True))

        mirrorOriginPos = om.MVector(-originPos.x, originPos.y, originPos.z)
        mirrorInsertionPos = om.MVector(-insertionPos.x, insertionPos.y, insertionPos.z)
        mirrorCenterPos = om.MVector(-centerPos.x, centerPos.y, centerPos.z)

        muscleLength = om.MVector(insertionPos - originPos).length()

        mirrorMuscleJointGrp = MuscleJointGroup(newMuscleName, muscleLength,
                                                self.compressionFactor, self.stretchFactor,
                                                self.stretchOffset, self.compressionOffset)

        mc.xform(mirrorMuscleJointGrp.originLoc, translation=mirrorOriginPos, worldSpace=True)
        mc.xform(mirrorMuscleJointGrp.insertionLoc, translation=mirrorInsertionPos, worldSpace=True)
        mc.xform(mirrorMuscleJointGrp.centerLoc, translation=mirrorCenterPos, worldSpace=True)

        mc.parent(mirrorMuscleJointGrp.muscleOrigin, originAttachObj)
        mc.parent(mirrorMuscleJointGrp.originLoc, originAttachObj)
        mc.parent(mirrorMuscleJointGrp.muscleInsertion, insertionAttachObj)
        mc.parent(mirrorMuscleJointGrp.insertionLoc, insertionAttachObj)

        return mirrorMuscleJointGrp


if __name__ == "__main__":
    import jointBasedMuscle.muscle_bone as mb
    import maya.api.OpenMaya as om
    import maya.cmds as mc
    import importlib

    importlib.reload(mb)

    X = mb.MuscleJointGroup.createFromAttachObjs("LeftTrapeziusA", "JONeck1", "JOLeftClavicle1",
                                                 compressionFactor=0.5, stretchFactor=1.5)
    X.update()

    Y = X.mirror("RightTrapeziusA", "JONeck1", "JORightClavicle1")
    Y.update()

    Y = mb.MuscleJointGroup.createFromAttachObjs("LeftTrapeziusB", "JOBack3", "LeftAcromion1",
                                                 compressionFactor=0.5, stretchFactor=1.5)
    Y.update()

    Z = Y.mirror("RightTrapeziusB", "JOBack3", "RightAcromion1")
    Z.update()

    Y = mb.MuscleJointGroup.createFromAttachObjs("LeftTrapeziusC", "JOBack3", "LeftAcromion1",
                                                 compressionFactor=0.5, stretchFactor=1.5)
    Y.update()

    Z = Y.mirror("RightTrapeziusC", "JOBack3", "RightAcromion1")
    Z.update()


    def offsetLoc(loc, startJoint, endJoint, ratio):
        startJointPos = om.MVector(mc.xform(startJoint, query=True, translation=True, ws=True))
        endJointPos = om.MVector(mc.xform(endJoint, query=True, translation=True, ws=True))
        interpolatePos = (endJointPos - startJointPos) * ratio + startJointPos
        mc.xform(loc, translation=interpolatePos, worldSpace=True)
        return interpolatePos


    pos = offsetLoc("LeftTrapC_muscleInsertion_loc", "LeftAcromion1", "LeftScapulaRoot1", 3 / 4)
