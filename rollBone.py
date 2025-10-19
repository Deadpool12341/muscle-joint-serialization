import math
import logging
import maya.cmds as cmds
import maya.api.OpenMaya as om

logger = logging.getLogger(__name__)


def calculateUpVecterPosition(startJoint, upJoint, offsetMatrix):
    newWorldMatrix = offsetMatrix * om.MMatrix(cmds.getAttr('{0}.worldMatrix'.format(startJoint)))
    localMatrix = newWorldMatrix * om.MMatrix(cmds.getAttr('{0}.parentInverseMatrix'.format(upJoint)))
    translation = om.MTransformationMatrix(localMatrix).translation(4)
    cmds.setAttr('{0}.t'.format(upJoint), *translation)


def projectJointChainToPlane(startJoint, endJoint, upAxis, planeNormal=None, negative=False):
    """rotate the joint chain with local axis cross product by aimAxis and upAxis to project it to plane with given normal
    # (p1 - u*d -p0) * n = 0
    Args:
        startJoint (str): parent joint name of the joint chain
        endJoint (str): child joint name of the joint chain
        upAxis (MVector): up axis of the joint chain (project direction to the plane)
        planeNormal (MVector, optional): rotate the joint chain to the plane with normal specified, otherwise use the
        aim vector of the joint chain as the plane normal
        negative (boolean, optional): project the joint chain to the plane with obtuse angle
    """
    # rotate joint with one axis to project it to plane with given normal
    startJointMatrix = om.MMatrix(cmds.getAttr('{0}.worldMatrix'.format(startJoint)))
    # get start joint world position
    startJointWs = om.MVector([startJointMatrix.getElement(3, index) for index in range(3)])
    # get end joint world position
    endJointMatrix = om.MMatrix(cmds.getAttr('{0}.worldMatrix'.format(endJoint)))
    endJointWs = om.MVector([endJointMatrix.getElement(3, index) for index in range(3)])
    # get world space up vector for start joint:
    startJointUpVec = upAxis * startJointMatrix
    # vector for joint chain
    aimVec = endJointWs - startJointWs
    if not planeNormal:
        planeNormal = aimVec
    # if the joint chain is perpendicular to the plane...
    if not startJointUpVec * planeNormal:
        axis = aimVec ^ startJointUpVec
        quaternion = om.MQuaternion()
        if negative:
            quaternion.setValue(axis, -math.pi / 2.0)
        else:
            quaternion.setValue(axis, math.pi / 2.0)
    else:

        d = aimVec * planeNormal / (startJointUpVec * planeNormal)
        # get the point projected to the plane
        p_ = endJointWs - d * startJointUpVec
        if negative:
            targetVec = -om.MVector(p_ - startJointWs)
        else:
            targetVec = om.MVector(p_ - startJointWs)
        axis = aimVec ^ targetVec
        quaternion = om.MQuaternion()
        quaternion.setValue(axis, targetVec.angle(aimVec))

    sel_list = om.MSelectionList()
    sel_list.add(startJoint)
    dagPath = sel_list.getDagPath(0)
    transformFn = om.MFnTransform(dagPath)
    transformFn.rotateBy(quaternion, om.MSpace.kWorld)


def setupTwistJointChain(startJoint, endJoint=None, twistJointCount=3,
                         twistAxis=(0, 1, 0),
                         upAxis=(0, 0, 1)):
    """
    Twist Joint Chain: By distributing the rotation across multiple helper joints along the chain, it can help to preserve the volume
    Used to solve the "candy wrapper" effect that the linear skinning gives when twisting along the joint axis
    * The twisting is driven by the endJoint compared to function "setupCounterTwistJointChain" which the twisting is driven by startJoint

    Args:
        startJoint (str): parent joint name of the joint chain
        endJoint (None, optional): child joint name of the joint chain, it drives the twist rotation
        twistJointCount (int, optional): number of helper joints distributed along the chain
        twistAxis (tuple, optional): twist axis of the start joint
        upAxis (tuple, optional): up axis, the least possible flipping axis

    Returns:
        Return all newly created joints
    """
    if not endJoint:
        childrenJoints = cmds.listRelatives(startJoint, children=True, type='joint')
        if childrenJoints:
            endJoint = childrenJoints[0]

    if not cmds.ls(endJoint):
        raise Exception('Cannot find a valid joint chain start with {0}'.format(startJoint))

    # create twist joints
    twistJoints = []
    for index in range(twistJointCount):
        cmds.select(startJoint)
        twistJoint = cmds.joint()
        twistJointName = startJoint.lstrip('JO') + f'Twist{index}'
        cmds.rename(twistJoint, twistJointName)
        twistJoints.append(twistJointName)

    jointChainLength = (om.MVector(cmds.xform(endJoint, translation=True, q=True, ws=True)) - om.MVector(
        cmds.xform(startJoint, translation=True, q=True, ws=True))).length()
    # create offset between the last twist joint and end joint: this is used for skinweights transfer
    offsetRatio = 0.02
    jointChainLength *= (1 - offsetRatio)
    distributionDistance = jointChainLength / (len(twistJoints))
    for index, twistJoint in enumerate(twistJoints):
        translation = distributionDistance * om.MVector(twistAxis) * (index + 1)
        cmds.setAttr('{0}.t'.format(twistJoint), *translation)
        cmds.setAttr('{0}.radius'.format(twistJoint), 1.0)

    # setup twist basis joint grp
    cmds.select(clear=True)
    twistBasisJoint1 = cmds.joint(name=startJoint.lstrip('JO') + 'TwistBasis1')
    cmds.matchTransform(twistBasisJoint1, startJoint)
    cmds.parent(twistBasisJoint1, startJoint)
    cmds.setAttr('{0}.radius'.format(twistBasisJoint1), 0.5)
    cmds.select(twistBasisJoint1)
    twistValueJoint = cmds.joint(name=startJoint.lstrip('JO') + 'TwistValue1')
    cmds.aimConstraint(endJoint, twistValueJoint, aimVector=twistAxis, upVector=upAxis, worldUpType='objectrotation',
                     worldUpObject=endJoint, worldUpVector=upAxis, maintainOffset=False)

    # create twist offset joint
    cmds.select(twistBasisJoint1)
    twistOffsetJoint = cmds.joint(name=startJoint.lstrip('JO') + 'BasisOffset1')

    # use orient constraint to distribute the twisting along the joint chain.
    orientConstraint = cmds.orientConstraint(twistValueJoint, twistJoints[-1], maintainOffset=False, weight=1)[0]
    # set orientConstraint interp Type to shortest
    cmds.setAttr('{0}.interpType'.format(orientConstraint), 2)
    weightUnit = 1.0 / (twistJointCount)
    for index in range(twistJointCount - 1):
        orientConstraint = cmds.orientConstraint(twistOffsetJoint, twistValueJoint, twistJoints[index],
                                               maintainOffset=False, weight=1)[0]
        # set orientConstraint interp Type to shortest
        cmds.setAttr('{0}.interpType'.format(orientConstraint), 2)
        cmds.setAttr('{0}.{1}W0'.format(orientConstraint, twistOffsetJoint), (1 - weightUnit * (index + 1)))
        cmds.setAttr('{0}.{1}W1'.format(orientConstraint, twistValueJoint), weightUnit * (index + 1))

    return twistJoints, twistBasisJoint1


def setupCounterTwistJointChain(startJoint, endJoint=None, twistJointCount=3,
                                twistAxis=(0, 1, 0),
                                upAxis=(1, 0, 0)):
    """
        Twist Joint Chain: By distributing the rotation across multiple helper joints along the chain, it can help to preserve the volume
        Used to solve the "candy wrapper" effect that the linear skinning gives when twisting along the joint axis
        * The twisting is driven by the startJoint compared to function "setupTwistJointChain" which the twisting is driven by endJoint
    Args:
        startJoint (str): parent joint name of the joint chain
        endJoint (str, optional): child joint name of the joint chain
        twistJointCount (int, optional): number of helper joints distributed along the chain
        twistAxis (MVector, optional): twist axis of the driving joint
        upAxis (MVector, optional): up axis

    Raises:
        Exception: Cannot find the end joint or Cannot find the parent joint for the startJoint

    Returns:
        Return all the newly created joints
    """
    if not endJoint:
        childrenJoints = cmds.listRelatives(startJoint, children=True, type='joint')
        if childrenJoints:
            endJoint = childrenJoints[0]

    if not cmds.ls(endJoint):
        raise Exception('Cannot find a valid joint chain start with {0}'.format(startJoint))

    # create twist joint setup
    twistJoints = []
    for index in range(twistJointCount):
        cmds.select(startJoint)
        twistJoint = cmds.joint()
        twistJointName = startJoint.lstrip('JO') + 'Twist{0}'.format(index)
        cmds.rename(twistJoint, twistJointName)
        twistJoints.append(twistJointName)

    jointChainLength = (om.MVector(cmds.xform(endJoint, translation=True, q=True, ws=True)) - om.MVector(
        cmds.xform(startJoint, translation=True, q=True, ws=True))).length()
    # create offset between the first twist joint and start joint: this is used for skinweights transfer
    offsetRatio = 0.02
    offset = jointChainLength * offsetRatio
    distributionDistance = (jointChainLength - offset) / (len(twistJoints))

    for index, twistJoint in enumerate(twistJoints):
        translation = distributionDistance * om.MVector(twistAxis) * index + offset * om.MVector(twistAxis)
        cmds.setAttr('{0}.t'.format(twistJoint), *translation)
        cmds.setAttr('{0}.radius'.format(twistJoint), 1.0)

    # setup counterTwist joint with aim constraint
    cmds.select(clear=True)
    twistBasisJointName = startJoint.lstrip('JO') + 'TwistBasis1'
    twistBasisJoint = cmds.joint(name=twistBasisJointName)
    cmds.setAttr('{0}.radius'.format(twistBasisJointName), 0.5)
    cmds.parent(twistBasisJoint, startJoint)
    cmds.matchTransform(twistBasisJoint, startJoint)
    # create up object to lock the rotation of the first twist joint
    cmds.select(cl=True)
    upJoint = cmds.joint(name=startJoint.lstrip('JO') + 'TwistUp1')
    cmds.setAttr('{0}.radius'.format(upJoint), 1)
    cmds.matchTransform(upJoint, startJoint)
    # cmds.delete(cmds.parentConstraint(startJoint, upJoint, mo=False, weight=True))
    # move up the locator along the up axis by 0.05 unit at local space
    cmds.parent(upJoint, startJoint)
    print(om.MVector(upAxis))
    cmds.setAttr('{0}.translate'.format(upJoint), *(om.MVector(upAxis) * 1))
    # cmds.setAttr('{0}.translate'.format(upJoint), *(om.MVector(1, 0, 0) * 1))

    # parent upJoint to startJoint's parent node if exists
    startJointParent = cmds.listRelatives(startJoint, parent=True, type='joint')

    if not startJointParent:
        raise Exception('Fialed to find the parent joint for startJoint: {0}'.format(startJoint))

    startJointParent = startJointParent[0]
    cmds.parent(upJoint, startJointParent)

    cmds.aimConstraint(endJoint, twistBasisJoint, aimVector=twistAxis, upVector=upAxis,
                     worldUpType='object', worldUpObject=upJoint)
    # create joint used to store the actual twist value: This is from Axel's prototype.
    cmds.select(twistBasisJoint)
    twistValueJoint = cmds.joint(name=startJoint.lstrip('JO') + 'TwistValue1')
    cmds.aimConstraint(endJoint, twistValueJoint, aimVector=twistAxis, upVector=upAxis,
                     worldUpType='objectrotation', worldUpObject=startJoint, worldUpVector=upAxis)
    # create twist offset joint
    cmds.select(twistBasisJoint)
    twistOffsetJoint = cmds.joint(name=startJoint.lstrip('JO') + 'BasisOffset1')

    # use orient constraint to distribute the twisting along the joint chain.
    orientConstraint = cmds.orientConstraint(twistOffsetJoint, twistValueJoint, twistJoints[0], mo=False, weight=1)[0]
    # set orientConstraint interp Type to shortest
    cmds.setAttr('{0}.interpType'.format(orientConstraint), 2)
    cmds.setAttr('{0}.{1}W0'.format(orientConstraint, twistOffsetJoint), 0.9)
    cmds.setAttr('{0}.{1}W1'.format(orientConstraint, twistValueJoint), 0.1)
    weightUnit = 1.0 / (twistJointCount)
    for index in range(1, twistJointCount):
        orientConstraint = cmds.orientConstraint(twistOffsetJoint, twistValueJoint,
                                               twistJoints[index], mo=False, weight=1)[0]
        # set orientConstraint interp Type to shortest
        cmds.setAttr('{0}.interpType'.format(orientConstraint), 2)
        cmds.setAttr('{0}.{1}W0'.format(orientConstraint, twistOffsetJoint), (1 - weightUnit * index))
        cmds.setAttr('{0}.{1}W1'.format(orientConstraint, twistValueJoint), weightUnit * index)

    # return all the dependencies
    return twistJoints, upJoint, twistBasisJoint


def setupNonFlipTwistChain(startJoint, endJoint, upJoint, upAxis):
    """Prevent twist chain flipping.
    The upJoint will follow the startJoint within the range between the plane normals defined.
    This will usually indicates Yaw or Pitch for the joint chain rotation

    Args:
        startJoint (str): parent joint chain name, JOShoulder
        endJoint (str): child joint chain name
        upJoint (str): up joint chian name
        upAxis (MVector): up axis of the joint chain
        planeNormals (list, optional): list of MVectors defines the joint chain rotation limit either for YAW or Pitch

    Returns:
        Return the newly created dotProduct
    """
    # use dot product outputs to drive upJoint positoin
    # create a marker to detect the joint chain rotation
    startJointParent = cmds.listRelatives(startJoint, parent=True, type='joint')
    if not startJointParent:
        logger.error('Failed to find the parent for angle marker.')
        return
    # first parent joint to select: clavicle
    startJointParent = startJointParent[0]
    cmds.select(clear=True)
    dotProductJoint = cmds.joint(name=startJoint.lstrip('JO') + 'Twist_{0}'.format(startJointParent.lstrip('JO'))) #LeftShoulder1Twist_LeftClavicle1
    cmds.matchTransform(dotProductJoint, startJoint)
    cmds.parent(dotProductJoint, startJoint)
    cmds.setAttr('{0}.t'.format(dotProductJoint), 0, 0, 0)
    offsetVec = -1 * om.MVector(upAxis)
    cmds.move(offsetVec.x, offsetVec.y, offsetVec.z, dotProductJoint, r=True, os=True)
    cmds.parent(dotProductJoint, startJointParent)

    """DEBUG: Calculate default arm rotation in world space. This is for debug only"""
    # orientationLocator = cmds.spaceLocator(name=startJoint.lstrip('JO') + 'Orientation')[0]
    # cmds.delete(cmds.parentConstraint(startJoint, orientationLocator, mo=False, weight=1))

    dotProductNode = cmds.shadingNode('vectorProduct', asUtility=True, name=startJoint.lstrip('JO') + '_DPN')
    multMatrixNode = cmds.shadingNode('multMatrix', asUtility=True, name=startJoint.lstrip('JO') + '_MMN')
    decomposeMatrixNode = cmds.shadingNode('decomposeMatrix', asUtility=True, name=startJoint.lstrip('JO') + '_DMN')
    cmds.connectAttr('{0}.worldMatrix'.format(dotProductJoint), '{0}.matrixIn[0]'.format(multMatrixNode))
    cmds.connectAttr('{0}.worldInverseMatrix'.format(startJoint), '{0}.matrixIn[1]'.format(multMatrixNode))
    cmds.connectAttr('{0}.matrixSum'.format(multMatrixNode), '{0}.inputMatrix'.format(decomposeMatrixNode))

    cmds.connectAttr('{0}.outputTranslate'.format(decomposeMatrixNode), '{0}.input1'.format(dotProductNode))
    cmds.connectAttr('{0}.t'.format(endJoint), '{0}.input2'.format(dotProductNode))

    cmds.setAttr('{0}.normalizeOutput'.format(dotProductNode), 1.0)

    upJointMatrix = om.MMatrix(cmds.getAttr('{0}.worldMatrix'.format(upJoint)))
    startJointMatrix = om.MMatrix(cmds.getAttr('{0}.worldMatrix'.format(startJoint)))
    offsetMatrix = upJointMatrix * startJointMatrix.inverse()

    def setDrivenKeys():
        cmds.setDrivenKeyframe(upJoint + '.' + 'translateX', cd=dotProductNode + '.' + 'outputX',
                             inTangentType='linear', outTangentType='linear')
        cmds.setDrivenKeyframe(upJoint + '.' + 'translateY', cd=dotProductNode + '.' + 'outputX',
                             inTangentType='linear', outTangentType='linear')
        cmds.setDrivenKeyframe(upJoint + '.' + 'translateZ', cd=dotProductNode + '.' + 'outputX',
                             inTangentType='linear', outTangentType='linear')

    # create a temp dagpose
    cmds.dagPose(startJoint, save=True, name='tempDagPose1')
    setDrivenKeys()

    # rotate the joint chain to the plane
    projectJointChainToPlane(startJoint, endJoint, upAxis)
    # calculate upJoint position
    calculateUpVecterPosition(startJoint, upJoint, offsetMatrix)
    setDrivenKeys()

    cmds.dagPose('tempDagPose1', restore=True)

    projectJointChainToPlane(startJoint, endJoint, upAxis, negative=True)
    # calculate upJoint position
    calculateUpVecterPosition(startJoint, upJoint, offsetMatrix)
    setDrivenKeys()

    cmds.dagPose('tempDagPose1', restore=True)

    cmds.delete('tempDagPose1')

    return dotProductJoint
