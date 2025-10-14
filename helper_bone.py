import maya.cmds as mc


def addScapulaJointsToBiped(acromionLoc, scapulaLoc, scapulaTipLoc, side='Left'):
    """
    Add scapula joints to biped. It requires to have neck joint 'JONeck' and back3 joint "JOBack3".
    The scapula driver joint aims to the neck joint with Y axis and X axis matches spine joint 'JOBack3' as worldUpObject.
    Args:
        acromionLoc: locator for acromion position
        scapulaLoc: locator for root scapula position, spine of scapula
        scapulaTipLoc: locator for scapula inferior angle

    """
    assert side in ['Left', 'Right'], 'Invalid side, should be either Left or Right'
    if mc.ls('JONeck1'):
        neckJoint = mc.ls('JONeck1')[0]
    else:
        raise RuntimeError('Failed to find the neck joint: JONeck1 in the scene.')

    if mc.ls('JOBack3'):
        back3Joint = mc.ls('JOBack3')[0]
    else:
        raise RuntimeError('Failed to find the back joint: JOBack3 in the scene.')

    if mc.ls('JO{0}Clavicle1'.format(side)):
        clavicalJoint = mc.ls('JO{0}Clavicle1'.format(side))[0]
    else:
        raise RuntimeError('Failed to find the clavical joint: JO{0}Clavicle1 in the scene.'.
                           format(side))

    scapulaDriver = mc.createNode("joint", name=f'{side}Acromion1')
    mc.matchTransform(scapulaDriver, acromionLoc, position=True, rotation=False, scale=True)
    scapulaJoint = mc.createNode("joint", name=f'{side}ScapulaRoot1')
    mc.matchTransform(scapulaJoint, scapulaLoc, position=True, rotation=False, scale=True)
    scapulaTip = mc.createNode("joint", name=f'{side}InferiorAngle1')
    mc.matchTransform(scapulaTip, scapulaTipLoc, position=True, rotation=False, scale=True)

    mc.parent(scapulaTip, scapulaJoint)
    mc.parent(scapulaJoint, scapulaDriver)

    # use Y axis as aim axis, and z axis align to world Z direction
    mc.joint(scapulaDriver, edit=True, orientJoint='yzx', secondaryAxisOrient='zup', children=True,
             zeroScaleOrient=True)
    mc.parent(scapulaDriver, clavicalJoint)

    mc.aimConstraint(neckJoint, scapulaDriver, aimVector=[0, 1, 0], upVector=[1, 0, 0], worldUpType='objectrotation',
                     worldUpObject=back3Joint, worldUpVector=[0, 1, 0], maintainOffset=True, weight=True)

    return [scapulaDriver, scapulaJoint, scapulaTip]
