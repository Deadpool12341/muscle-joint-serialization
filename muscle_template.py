import maya.api.OpenMaya as om
import maya.cmds as mc
import logging

from . import muscle_bone as mb
from . import config as config

logger = logging.getLogger(__name__)


class BilateralMuscles:
    """
    A base class for defining bilateral muscle components in a rigging system.
    This class provides a framework for creating, managing, and manipulating
    bilateral muscles (muscles that exist symmetrically on the left and right sides
    of the body). It includes methods for adding, mirroring, editing, deleting,
    and finalizing muscle components, as well as storing related data.
    """

    def __init__(self, name, side):
        """
        :param name: (str) The name of the muscle group.
        :param side: (str) The side of the body ('Left' or 'Right') this muscle belongs to.
        """
        super().__init__()
        assert side in ['Left', 'Right'], 'Invalid side, should be either Left or Right'
        self.name = name
        self.side = side
        self.allJoints = []

        self.muscleJointGroups = {}

    def add(self):
        """
        Abstract method for creating and positioning the muscle components in the rig.
        """
        pass

    def mirror(self):
        """
        Abstract method for mirroring the muscle structure to the opposite side of the body.
        """
        pass

    def delete(self):
        """
        Deletes all associated muscle joint groups, cleaning up the rig.
        """
        for muscleJointGroup in self.muscleJointGroups.values():
            muscleJointGroup.delete()

    def edit(self):
        """
        Abstract method for editing the muscle's configuration and attributes.
        """

    def finalize(self):
        """
        Abstract method for performing final adjustments to the muscle setup.
        """
        logger.info(f"Complete creating {self.name} muscle component on {self.side} side.")
        for muscleJointGroup in self.muscleJointGroups.values():
            muscleJointGroup.update()

    def __str__(self):
        return f"{self.side}{self.name}"

    @staticmethod
    def getJoint(jointName):
        """
        Return the joint name if it exists in the scene

        Args:
            jointName: joint name

        Returns: jointName if the joint exists in the scene, otherwise raise exception

        """
        if mc.ls(jointName):
            return jointName
        else:
            raise RuntimeError('Failed to find the {0} joint in the scene'.format(jointName))

    @staticmethod
    def getOtherSide(side):
        if side == "Left":
            return "Right"
        elif side == "Right":
            return "Left"
        else:
            raise RuntimeError("Invalid side, should be either Left or Right")

    @staticmethod
    def ensureKeyExists(dictionary, key):
        val = dictionary.get(key)
        if val is None:
            raise KeyError(f"The '{key}' key is missing in bpTrap.")
        return val


class TrapeziusMuscles(BilateralMuscles):
    """
    The TrapeziusMuscles class creates the trapezius muscle system in a character rig.
    This class handles the creation, mirroring, and finalization of the trapezius muscle,
    comprising three parts:
      - Descending (superior) fibers: Neck to clavicle.
      - Transverse (middle) fibers: Spine to scapula.
      - Ascending (inferior) fibers: Spine to scapula.
    """

    def __init__(self, name='Trapezius', side='Left', acromionJoint=None, scapulaJoint=None):
        """

        :param name: (str, optional) The name of the muscle component. Default is 'Trapezius'.
        :param side: (str, optional) The side of the body for the muscle (either 'Left' or 'Right'). Default is 'Left'.
        :param acromionJoint: (str, optional) The name of the acromion joint for the side,
          or None to automatically use the default joint based on the `side` parameter. Default is None.
        :param scapulaJoint: (str, optional) The name of the scapula joint for the side,
          or None to automatically use the default joint based on the `side` parameter. Default is None.
        """
        super(TrapeziusMuscles, self).__init__(name=name, side=side)
        # get all the joint dependencies
        self.headJoint = self.getJoint('JOHead1')
        self.neckJoint = self.getJoint('JONeck1')
        self.clavicalJoint = self.getJoint(f'JO{side}Clavicle1')
        self.spine2Joint = self.getJoint('JOBack2')
        self.spine3Joint = self.getJoint('JOBack3')

        if not acromionJoint:
            self.acromionJoint = self.getJoint('{0}Acromion1'.format(side))
        else:
            self.acromionJoint = self.getJoint(acromionJoint)

        if not scapulaJoint:
            self.scapulaJoint = self.getJoint('{0}ScapulaRoot1'.format(side))
        else:
            self.scapulaJoint = self.getJoint(scapulaJoint)

        self.trapeziusA = None
        self.trapeziusB = None
        self.trapeziusC = None

    def add(self):
        # Descending Part: superior fibers of the trapezius
        # Origin: spinous process of C7 to the occipital bone (neck joint to head joint)
        neckJointPos = om.MVector(mc.xform(self.neckJoint, translation=True, q=True, ws=True))
        headJointPos = om.MVector(mc.xform(self.headJoint, translation=True, q=True, ws=True))
        averagePos = (neckJointPos + headJointPos) / 2.0
        neckJointWorldMatrix = mc.getAttr('{0}.worldMatrix'.format(self.neckJoint))
        offsetVector = om.MVector(neckJointWorldMatrix[8: 11]) * 0.02
        trapeziusAOrigin = offsetVector + averagePos

        # Insertion: lateral third of the clavical
        clavicalJointPos = om.MVector(mc.xform(self.clavicalJoint, translation=True, q=True, ws=True))
        acromoinJointPos = om.MVector(mc.xform(self.acromionJoint, translation=True, q=True, ws=True))
        offsetVector = (clavicalJointPos - acromoinJointPos) / 6.0
        trapeziusAInsertion = acromoinJointPos + offsetVector

        self.trapeziusA = mb.MuscleJointGroup.createFromAttachObjs(muscleName='{0}{1}A'.format(self.side, self.name),
                                                                   originAttachObj=self.neckJoint,
                                                                   insertionAttachObj=self.clavicalJoint,
                                                                   compressionFactor=0.5,
                                                                   stretchFactor=1.5)
        self.muscleJointGroups[self.trapeziusA.muscleName] = self.trapeziusA
        mc.xform(self.trapeziusA.originLoc, translation=trapeziusAOrigin, worldSpace=True)
        mc.xform(self.trapeziusA.insertionLoc, translation=trapeziusAInsertion, worldSpace=True)
        # Transverse Part: middle fibers of the trapezius
        scapulaJointPos = om.MVector(mc.xform(self.scapulaJoint, translation=True, q=True, ws=True))
        # Origin: Broad aponeurosis at spinous processes of vertebrae T1-T4 (or C7-T3)
        averagePos = (neckJointPos + scapulaJointPos) / 2.0
        trapeziusBOrigin = om.MVector(neckJointPos.x, averagePos.y, averagePos.z)
        # Insertion: Medial aspect of acromion, Superior crest of spine of scapula
        offsetVector = (scapulaJointPos - acromoinJointPos) / 4.0
        trapeziusBInsertion = offsetVector + acromoinJointPos
        self.trapeziusB = mb.MuscleJointGroup.createFromAttachObjs(muscleName='{0}{1}B'.format(self.side, self.name),
                                                                   originAttachObj=self.spine3Joint,
                                                                   insertionAttachObj=self.acromionJoint,
                                                                   compressionFactor=0.5,
                                                                   stretchFactor=1.5)
        self.muscleJointGroups[self.trapeziusB.muscleName] = self.trapeziusB
        mc.xform(self.trapeziusB.originLoc, translation=trapeziusBOrigin, worldSpace=True)
        mc.xform(self.trapeziusB.insertionLoc, translation=trapeziusBInsertion, worldSpace=True)
        # Ascending Part: inferior fibers of the trapezius
        # Origin: Arise from the spinous processes of the remaining thoracic vertebrae (T4-T12)
        # roughly is T8 at the same level as the xiphisternum: (JOBack3)
        spine3JointPos = om.MVector(mc.xform(self.spine3Joint, translation=True, q=True, ws=True))
        trapeziusCOrigin = om.MVector(spine3JointPos.x, spine3JointPos.y, trapeziusBOrigin.z)
        # Insertion: Medial end of spine of scapula
        trapeziusCInsertion = offsetVector * 3 + acromoinJointPos
        self.trapeziusC = mb.MuscleJointGroup.createFromAttachObjs(muscleName='{0}{1}C'.format(self.side, self.name),
                                                                   originAttachObj=self.spine2Joint,
                                                                   insertionAttachObj=self.acromionJoint,
                                                                   compressionFactor=0.5,
                                                                   stretchFactor=1.5)
        self.muscleJointGroups[self.trapeziusC.muscleName] = self.trapeziusC
        mc.xform(self.trapeziusC.originLoc, translation=trapeziusCOrigin, worldSpace=True)
        mc.xform(self.trapeziusC.insertionLoc, translation=trapeziusCInsertion, worldSpace=True)

    def mirror(self):
        mirroredTrap = TrapeziusMuscles(name=self.name, side=self.getOtherSide(self.side))
        mirroredTrap.trapeziusA = self.trapeziusA.mirror(f"{self.getOtherSide(self.side)}{self.name}A",
                                                         mirroredTrap.neckJoint, mirroredTrap.acromionJoint)

        mirroredTrap.muscleJointGroups[mirroredTrap.trapeziusA.muscleName] = mirroredTrap.trapeziusA

        mirroredTrap.trapeziusB = self.trapeziusB.mirror(f"{self.getOtherSide(self.side)}{self.name}B",
                                                         mirroredTrap.spine3Joint, mirroredTrap.acromionJoint)

        mirroredTrap.muscleJointGroups[mirroredTrap.trapeziusB.muscleName] = mirroredTrap.trapeziusB

        mirroredTrap.trapeziusC = self.trapeziusC.mirror(f"{self.getOtherSide(self.side)}{self.name}C",
                                                         mirroredTrap.spine2Joint, mirroredTrap.acromionJoint)

        mirroredTrap.muscleJointGroups[mirroredTrap.trapeziusC.muscleName] = mirroredTrap.trapeziusC
        return mirroredTrap

    def finalize(self):
        super(TrapeziusMuscles, self).finalize()
        mc.delete(self.trapeziusA.mainAimConstraint)
        self.mainAimConstraint = mc.aimConstraint(self.trapeziusA.muscleInsertion, self.trapeziusA.muscleBase,
                                                  aimVector=[0, 1, 0],
                                                  upVector=[1, 0, 0],
                                                  worldUpType='objectrotation', worldUpObject=self.spine3Joint,
                                                  worldUpVector=[0, 1, 0])
        mc.parentConstraint(self.neckJoint, self.headJoint, self.trapeziusA.muscleOrigin, weight=True, mo=True)

        mc.parentConstraint(self.spine3Joint, self.spine2Joint, self.trapeziusC.muscleOrigin, weight=True, mo=True)

    @classmethod
    def build(cls, side, bpTrapezius):
        """
        Builds a BilateralMuscles component for the trapezius muscle.
        :param side: (Side Enum) The side of the body for which the trapezius muscle is being built.
        :param bpTrapezius: (dict) A blueprint dictionary containing the configuration for the
                            trapezius muscle segments. Expected keys are "upper", "middle",
                            and "lower", each mapping to dictionaries with:
                                - "origin": The origin point of the muscle segment.
                                - "insertion": The insertion point of the muscle segment.
                                - "center": The center control point of the muscle segment.
        Example:
        # Blueprint for trapezius muscle
        bpTrapezius = {
            "upper": {"origin": originNode1, "insertion": insertionNode1, "center": centerNode1},
            "middle": {"origin": originNode2, "insertion": insertionNode2, "center": centerNode2},
            "lower": {"origin": originNode3, "insertion": insertionNode3, "center": centerNode3},
        }
        # Build trapezius muscles for the left side
        leftTrapezius = BilateralMuscles.build(side=Side("Left"), bpTrapezius=bpTrapezius)
        :return: (TrapeziusMuscles) An instance of the "TrapeziusMuscles" class
        """
        trapMuscles = cls(side=side)
        bpUpperTrap = trapMuscles.ensureKeyExists(bpTrapezius, "upper")
        trapMuscles.trapeziusA = mb.MuscleJointGroup.createFromBlueprint(bpOrigin=bpUpperTrap.get("origin"),
                                                                         bpInsertion=bpUpperTrap.get("insertion"),
                                                                         bpCenter=bpUpperTrap.get("center"),
                                                                         originAttachObj=trapMuscles.neckJoint,
                                                                         insertionAttachObj=trapMuscles.clavicalJoint,
                                                                         compressionFactor=0.5,
                                                                         stretchFactor=1.5)
        trapMuscles.muscleJointGroups[trapMuscles.trapeziusA.muscleName] = trapMuscles.trapeziusA
        bpMiddleTrap = trapMuscles.ensureKeyExists(bpTrapezius, "middle")
        trapMuscles.trapeziusB = mb.MuscleJointGroup.createFromBlueprint(bpOrigin=bpMiddleTrap.get("origin"),
                                                                         bpInsertion=bpMiddleTrap.get("insertion"),
                                                                         bpCenter=bpMiddleTrap.get("center"),
                                                                         originAttachObj=trapMuscles.spine3Joint,
                                                                         insertionAttachObj=trapMuscles.acromionJoint,
                                                                         compressionFactor=0.5,
                                                                         stretchFactor=1.5)
        trapMuscles.muscleJointGroups[trapMuscles.trapeziusB.muscleName] = trapMuscles.trapeziusB
        bpLowerTrap = trapMuscles.ensureKeyExists(bpTrapezius, "lower")
        trapMuscles.trapeziusC = mb.MuscleJointGroup.createFromBlueprint(bpOrigin=bpLowerTrap.get("origin"),
                                                                         bpInsertion=bpLowerTrap.get("insertion"),
                                                                         bpCenter=bpLowerTrap.get("center"),
                                                                         originAttachObj=trapMuscles.spine2Joint,
                                                                         insertionAttachObj=trapMuscles.acromionJoint,
                                                                         compressionFactor=0.5,
                                                                         stretchFactor=1.5)
        trapMuscles.muscleJointGroups[trapMuscles.trapeziusC.muscleName] = trapMuscles.trapeziusC
        # trapMuscles.finalize()
        return trapMuscles


class LatissimusDorsiMuscles(BilateralMuscles):
    """
    Create the latissimus dorsi muscle joint groups for a given side of the body.
    """

    def __init__(self, name='LatissimusDorsi', side='Left', upperArmTwistJoint=None):
        """
        Initializes the LatissimusDorsiMuscles object and sets up the joint dependencies
        required for constructing the latissimus dorsi muscle system. This includes spine
        and upper arm joints, as well as an optional upper arm twist joint.
        :param name: (str, optional) The name of the muscle component. Default is 'LatissimusDorsi'.
        :param side: (str, optional) The side of the body for the muscle (either 'Left' or 'Right'). Default is 'Left'.
        *** based on the twist joint count, it is currently using JOUpperArm1Twist1 as parent for insertion ***
        :param upperArmTwistJoint: (str, optional): The name of the upper arm twist joint,
            or None to automatically use the default joint based on the `side` parameter. Default is None.
        """
        super(LatissimusDorsiMuscles, self).__init__(name=name, side=side)
        # get all the joint dependencies
        self.spine3Joint = self.getJoint('JOBack3')
        self.spine2Joint = self.getJoint('JOBack2')
        self.spine1Joint = self.getJoint('JOBack1')
        self.upperArmJoint = self.getJoint(f'JO{side}UpperArm1')

        if not upperArmTwistJoint:
            self.upperArmTwistJoint = self.getJoint('{0}UpperArm1Twist1'.format(side))
        else:
            self.upperArmTwistJoint = self.getJoint(upperArmTwistJoint)

        self.latissimusDorsiA = None
        self.latissimusDorsiB = None

    def add(self):
        spine1JointPos = om.MVector(mc.xform(self.spine1Joint, translation=True, q=True, ws=True))
        spine2JointPos = om.MVector(mc.xform(self.spine2Joint, translation=True, q=True, ws=True))
        latissimusDorsiAOrigin = (spine1JointPos + spine2JointPos) / 2.0 - om.MVector(0.06, 0, 0) * \
                                 {'Left': 1, 'Right': -1}[self.side]
        upperArmJointPos = om.MVector(mc.xform(self.upperArmJoint, translation=True, q=True, ws=True))
        upperArmTwistJointPos = om.MVector(mc.xform(self.upperArmTwistJoint, translation=True, q=True, ws=True))
        offsetVector = (upperArmTwistJointPos - upperArmJointPos) / 2.0
        latissimusDorsiAInsertion = upperArmJointPos + offsetVector
        self.latissimusDorsiA = mb.MuscleJointGroup.createFromAttachObjs(
            muscleName='{0}{1}A'.format(self.side, self.name),
            originAttachObj=self.spine1Joint,
            insertionAttachObj=self.upperArmTwistJoint,
            compressionFactor=0.5,
            stretchFactor=1.5)
        self.muscleJointGroups[self.latissimusDorsiA.muscleName] = self.latissimusDorsiA
        mc.xform(self.latissimusDorsiA.originLoc, translation=latissimusDorsiAOrigin, worldSpace=True)
        mc.xform(self.latissimusDorsiA.insertionLoc, translation=latissimusDorsiAInsertion, worldSpace=True)

        spine3JointPos = om.MVector(mc.xform(self.spine3Joint, translation=True, q=True, ws=True))
        latissimusDorsiBOrigin = (spine2JointPos + spine3JointPos) / 2.0
        offsetVector = (upperArmTwistJointPos - upperArmJointPos) / 2.0
        latissimusDorsiBInsertion = upperArmJointPos + offsetVector * 0.9
        self.latissimusDorsiB = mb.MuscleJointGroup.createFromAttachObjs(
            muscleName='{0}{1}B'.format(self.side, self.name),
            originAttachObj=self.spine2Joint,
            insertionAttachObj=self.upperArmTwistJoint,
            compressionFactor=0.5,
            stretchFactor=1.5)
        self.muscleJointGroups[self.latissimusDorsiB.muscleName] = self.latissimusDorsiB
        LatissimusDorsiBCenter = (latissimusDorsiBInsertion - latissimusDorsiBOrigin) / 4.0 + latissimusDorsiBOrigin
        mc.xform(self.latissimusDorsiB.originLoc, translation=latissimusDorsiBOrigin, worldSpace=True)
        mc.xform(self.latissimusDorsiB.insertionLoc, translation=latissimusDorsiBInsertion, worldSpace=True)
        mc.xform(self.latissimusDorsiB.centerLoc, translation=LatissimusDorsiBCenter, worldSpace=True)

    def mirror(self):
        mirroredLat = LatissimusDorsiMuscles(name=self.name, side=self.getOtherSide(self.side))
        mirroredLat.latissimusDorsiA = self.latissimusDorsiA.mirror(f"{self.getOtherSide(self.side)}{self.name}A",
                                                                    mirroredLat.spine1Joint,
                                                                    mirroredLat.upperArmTwistJoint)

        mirroredLat.muscleJointGroups[mirroredLat.latissimusDorsiA.muscleName] = mirroredLat.latissimusDorsiA

        mirroredLat.latissimusDorsiB = self.latissimusDorsiB.mirror(f"{self.getOtherSide(self.side)}{self.name}B",
                                                                    mirroredLat.spine2Joint,
                                                                    mirroredLat.upperArmTwistJoint)

        mirroredLat.muscleJointGroups[mirroredLat.latissimusDorsiB.muscleName] = mirroredLat.latissimusDorsiB

        return mirroredLat

    def finalize(self):
        super(LatissimusDorsiMuscles, self).finalize()
        # engine only support all-axis constraint, so constrain the dummy node with all axis and create connections
        # from the dummy node to the target node
        dummyNode = mc.duplicate(self.latissimusDorsiA.muscleOffset, name=self.latissimusDorsiA.muscleOffset + '_dummy',
                                 parentOnly=True)[0]
        # outputNode = mc.duplicate(self.latissimusDorsiA.muscleOffset, name='outputNode', parentOnly=True)[0]

        # self.latissimusDorsiAConstraint = mc.pointConstraint(self.spine3Joint, self.latissimusDorsiA.muscleOffset,
        #                                                      mo=True, weight=1, skip='y')
        mc.pointConstraint(self.spine3Joint, dummyNode, mo=True, weight=1)
        mc.connectAttr('{0}.tx'.format(dummyNode), '{0}.tx'.format(self.latissimusDorsiA.muscleOffset))
        mc.connectAttr('{0}.tz'.format(dummyNode), '{0}.tz'.format(self.latissimusDorsiA.muscleOffset))

        trapCJoint = self.getJoint('{0}TrapeziusC_muscleOffset'.format(self.side))
        self.latissimusDorsiBConstraint = mc.pointConstraint(self.latissimusDorsiA.muscleOffset, trapCJoint,
                                                             self.latissimusDorsiB.muscleOffset, mo=True, weight=1)

    @classmethod
    def build(cls, side, bpLatissimusDorsi):
        """
        :param side: (Side Enum): The side of the body for the muscle.
        :param bpLatissimusDorsi: (dict) A blueprint dictionary containing configuration data for the latissimus dorsi muscles
        bpLatissimusDorsi = {
            "vertebral": {"origin": ..., "insertion": ..., "center": ...},
            "fascia": {"origin": ..., "insertion": ..., "center": ...}
        }
        :return: (LatissimusDorsiMuscles): An instance of the "LatissimusDorsiMuscles" class, fully constructed with
          muscle joints and their configurations.
        """
        latMuscles = cls(side=side)
        bpVertebralLat = latMuscles.ensureKeyExists(bpLatissimusDorsi, "vertebral")
        latMuscles.latissimusDorsiA = mb.MuscleJointGroup.createFromBlueprint(bpOrigin=bpVertebralLat.get("origin"),
                                                                              bpInsertion=bpVertebralLat.get(
                                                                                  "insertion"),
                                                                              bpCenter=bpVertebralLat.get("center"),
                                                                              originAttachObj=latMuscles.spine1Joint,
                                                                              insertionAttachObj=latMuscles.upperArmTwistJoint,
                                                                              compressionFactor=0.5,
                                                                              stretchFactor=1.5)
        latMuscles.muscleJointGroups[latMuscles.latissimusDorsiA.muscleName] = latMuscles.latissimusDorsiA
        bpFasciaLat = latMuscles.ensureKeyExists(bpLatissimusDorsi, "fascia")
        latMuscles.latissimusDorsiB = mb.MuscleJointGroup.createFromBlueprint(bpOrigin=bpFasciaLat.get("origin"),
                                                                              bpInsertion=bpFasciaLat.get("insertion"),
                                                                              bpCenter=bpFasciaLat.get("center"),
                                                                              originAttachObj=latMuscles.spine2Joint,
                                                                              insertionAttachObj=latMuscles.upperArmTwistJoint,
                                                                              compressionFactor=0.5,
                                                                              stretchFactor=1.5)
        latMuscles.muscleJointGroups[latMuscles.latissimusDorsiB.muscleName] = latMuscles.latissimusDorsiB

        # latMuscles.finalize()
        return latMuscles


class TerasMajorMuscles(BilateralMuscles):
    def __init__(self, name='TerasMajor', side='Left', scapulaJoint=None, inferiorAngleJoint=None,
                 upperArmTwistJoint=None):
        """
        Initializes the TerasMajorMuscles object and sets up the joint dependencies required
        for constructing the teras major muscle system. This includes upper arm and scapula-related joints,
        as well as optional inferior angle and upper arm twist joints.
        :param name: (str, optional) The name of the muscle component. Default is 'TerasMajor'.
        :param side: (str, optional) The side of the body for the muscle (either 'Left' or 'Right'). Default is 'Left'.
        :param scapulaJoint: (str) The name of the scapula root joint. If not specified, it will be inferred
            based on the `side`. Default is None.
        :param inferiorAngleJoint: (str, optional): The name of the inferior angle joint of the scapula.
            If not specified, it will be inferred based on the `side`. Default is None.
        :param upperArmTwistJoint: (str, optional): The name of the upper arm twist joint. If not specified, it will be
          inferred based on the `side`. Default is None.
        """
        super(TerasMajorMuscles, self).__init__(name=name, side=side)
        # get all the joint dependencies
        self.upperArmJoint = self.getJoint(f'JO{side}UpperArm1')

        if not scapulaJoint:
            self.scapulaJoint = self.getJoint('{0}ScapulaRoot1'.format(side))
        else:
            self.scapulaJoint = self.getJoint(scapulaJoint)

        if not inferiorAngleJoint:
            self.inferiorAngleJoint = self.getJoint('{0}InferiorAngle1'.format(side))
        else:
            self.inferiorAngleJoint = self.getJoint(inferiorAngleJoint)

        if not upperArmTwistJoint:
            self.upperArmTwistJoint = self.getJoint('{0}UpperArm1Twist1'.format(side))
        else:
            self.upperArmTwistJoint - self.getJoint(upperArmTwistJoint)

        self.terasMajor = None

    def add(self):
        upperArmJointPos = om.MVector(mc.xform(self.upperArmJoint, translation=True, q=True, ws=True))
        upperArmTwistJointPos = om.MVector(mc.xform(self.upperArmTwistJoint, translation=True, q=True, ws=True))
        offsetVector = (upperArmTwistJointPos - upperArmJointPos) / 2.0
        terasMajorInsertion = upperArmJointPos + offsetVector * 1.1
        scapulaJointPos = om.MVector(mc.xform(self.scapulaJoint, translation=True, q=True, ws=True))
        inferiorAngleJointPos = om.MVector(mc.xform(self.inferiorAngleJoint, translation=True, q=True, ws=True))
        terasMajorOrigin = (inferiorAngleJointPos - scapulaJointPos) * 0.9 + scapulaJointPos
        self.terasMajor = mb.MuscleJointGroup.createFromAttachObjs(muscleName='{0}{1}'.format(self.side, self.name),
                                                                   originAttachObj=self.scapulaJoint,
                                                                   insertionAttachObj=self.upperArmTwistJoint,
                                                                   compressionFactor=0.5,
                                                                   stretchFactor=1.5)
        self.muscleJointGroups[self.terasMajor.muscleName] = self.terasMajor
        mc.xform(self.terasMajor.originLoc, translation=terasMajorOrigin, worldSpace=True)
        mc.xform(self.terasMajor.insertionLoc, translation=terasMajorInsertion, worldSpace=True)

    def mirror(self):
        mirroredTerasMajor = TerasMajorMuscles(name=self.name, side=self.getOtherSide(self.side))
        mirroredTerasMajor.terasMajor = self.terasMajor.mirror(f"{self.getOtherSide(self.side)}{self.name}A",
                                                               mirroredTerasMajor.scapulaJoint,
                                                               mirroredTerasMajor.upperArmTwistJoint)

        mirroredTerasMajor.muscleJointGroups[mirroredTerasMajor.terasMajor.muscleName] = mirroredTerasMajor.terasMajor

        return mirroredTerasMajor

    @classmethod
    def build(cls, side, bpTerasMajor):
        """
        :param side: (Side Enum): The side of the body for the muscle.
        :param bpTerasMajor: (dict): A blueprint dictionary containing configuration data for the teres major muscle,
          including:
            - `"origin"`: Origin position data for the muscle.
            - `"insertion"`: Insertion position data for the muscle.
            - `"center"`: Center position data for the muscle.
        :return: (TerasMajorMuscles) An instance of the "TerasMajorMuscles" class.

        """
        terasMajorMuscles = cls(side=side)
        terasMajorMuscles.terasMajor = mb.MuscleJointGroup.createFromBlueprint(bpOrigin=bpTerasMajor.get("origin"),
                                                                               bpInsertion=bpTerasMajor.get(
                                                                                   "insertion"),
                                                                               bpCenter=bpTerasMajor.get("center"),
                                                                               originAttachObj=terasMajorMuscles.scapulaJoint,
                                                                               insertionAttachObj=terasMajorMuscles.upperArmTwistJoint,
                                                                               compressionFactor=0.5,
                                                                               stretchFactor=1.5)
        terasMajorMuscles.muscleJointGroups[terasMajorMuscles.terasMajor.muscleName] = terasMajorMuscles.terasMajor

        # terasMajorMuscles.finalize()
        return terasMajorMuscles


class PectoralisMajorMuscles(BilateralMuscles):
    """
    Create the pectoralis major muscle joint groups for a given side of the body.
    """

    def __init__(self, name='PectoralisMajor', side='Left', acromionJoint=None, upperArmTwistJoint=None):
        """
        :param name: (str) The name of the muscle component. Defaults to 'PectoralisMajor'.
        :param side: (str): The side of the body ('Left' or 'Right'). Defaults to 'Left'.
        :param acromionJoint: (str, optional): The acromion joint name.
        :param upperArmTwistJoint: (str, optional): The upper arm twist joint name.
        """
        super(PectoralisMajorMuscles, self).__init__(name=name, side=side)
        # get all the joint dependencies
        self.spine3Joint = mc.ls('JOBack3')[0]
        self.clavicalJoint = self.getJoint(f'JO{side}Clavicle1')
        self.upperArmJoint = self.getJoint(f'JO{side}UpperArm1')

        if not acromionJoint:
            self.acromionJoint = self.getJoint('{0}Acromion1'.format(side))
        else:
            self.acromionJoint = self.getJoint(acromionJoint)

        if not upperArmTwistJoint:
            self.upperArmTwistJoint = self.getJoint('{0}UpperArm1Twist1'.format(side))
        else:
            self.upperArmTwistJoint = self.getJoint(upperArmTwistJoint)

        self.pectoralisMajorA = None
        self.pectoralisMajorB = None

    def add(self):
        spine3JointPos = om.MVector(mc.xform(self.spine3Joint, translation=True, q=True, ws=True))
        upperArmJointPos = om.MVector(mc.xform(self.upperArmJoint, translation=True, q=True, ws=True))
        upperArmTwistJointPos = om.MVector(mc.xform(self.upperArmTwistJoint, translation=True, q=True, ws=True))
        pectoralisMajorAOrigin = spine3JointPos + om.MVector(-0.05, 0, 0) * {'Left': 1, 'Right': -1}[self.side]
        offsetVector = (upperArmTwistJointPos - upperArmJointPos) / 2.0
        pectoralisMajorAInsertion = upperArmJointPos + offsetVector * 1.3
        pectoralisMajorBInsertion = upperArmJointPos + offsetVector * 1.5
        self.pectoralisMajorA = mb.MuscleJointGroup.createFromAttachObjs(
            muscleName='{0}{1}A'.format(self.side, self.name),
            originAttachObj=self.spine3Joint,
            insertionAttachObj=self.upperArmTwistJoint,
            compressionFactor=0.5,
            stretchFactor=1.5)
        self.muscleJointGroups[self.pectoralisMajorA.muscleName] = self.pectoralisMajorA
        mc.xform(self.pectoralisMajorA.originLoc, translation=pectoralisMajorAOrigin, worldSpace=True)
        mc.xform(self.pectoralisMajorA.insertionLoc, translation=pectoralisMajorAInsertion, worldSpace=True)

        # Insertion: medial half of the clavical
        clavicalJointPos = om.MVector(mc.xform(self.clavicalJoint, translation=True, q=True, ws=True))
        acromoinJointPos = om.MVector(mc.xform(self.acromionJoint, translation=True, q=True, ws=True))
        offsetVector = (acromoinJointPos - clavicalJointPos) / 4.0
        pectoralisMajorBOrigin = clavicalJointPos + offsetVector

        self.pectoralisMajorB = mb.MuscleJointGroup.createFromAttachObjs(
            muscleName='{0}{1}B'.format(self.side, self.name),
            originAttachObj=self.clavicalJoint,
            insertionAttachObj=self.upperArmTwistJoint,
            compressionFactor=0.5,
            stretchFactor=1.5)
        self.muscleJointGroups[self.pectoralisMajorB.muscleName] = self.pectoralisMajorB
        mc.xform(self.pectoralisMajorB.originLoc, translation=pectoralisMajorBOrigin, worldSpace=True)
        mc.xform(self.pectoralisMajorB.insertionLoc, translation=pectoralisMajorBInsertion, worldSpace=True)

    def mirror(self):
        mirroredPec = PectoralisMajorMuscles(name=self.name, side=self.getOtherSide(self.side))
        mirroredPec.pectoralisMajorA = self.pectoralisMajorA.mirror(f"{self.getOtherSide(self.side)}{self.name}A",
                                                                    mirroredPec.spine3Joint,
                                                                    mirroredPec.upperArmTwistJoint)

        mirroredPec.muscleJointGroups[mirroredPec.pectoralisMajorA.muscleName] = mirroredPec.pectoralisMajorA

        mirroredPec.pectoralisMajorB = self.pectoralisMajorB.mirror(f"{self.getOtherSide(self.side)}{self.name}B",
                                                                    mirroredPec.clavicalJoint,
                                                                    mirroredPec.upperArmTwistJoint)

        mirroredPec.muscleJointGroups[mirroredPec.pectoralisMajorB.muscleName] = mirroredPec.pectoralisMajorB

        return mirroredPec

    @classmethod
    def build(cls, side, bpPectoralisMajor):
        """
        :param side: (Side Enum) The side of the body.
        :param bpPectoralisMajor:  A blueprint dictionary containing configuration data for the muscles.
                bpPectoralisMajor = {
                    "sterno": {"origin": [...], "insertion": [...], "center": [...]},
                    "clavicular": {"origin": [...], "insertion": [...], "center": [...]}}
        :return: (PectoralisMajorMuscles) An instance of "PectoralisMajorMuscles" with initialized muscle joints.
        """
        pecMuscles = cls(side=side)
        bpSternoPec = pecMuscles.ensureKeyExists(bpPectoralisMajor, "sterno")
        pecMuscles.pectoralisMajorA = mb.MuscleJointGroup.createFromBlueprint(bpOrigin=bpSternoPec.get("origin"),
                                                                              bpInsertion=bpSternoPec.get("insertion"),
                                                                              bpCenter=bpSternoPec.get("center"),
                                                                              originAttachObj=pecMuscles.spine3Joint,
                                                                              insertionAttachObj=pecMuscles.upperArmTwistJoint,
                                                                              compressionFactor=0.5,
                                                                              stretchFactor=1.5)
        pecMuscles.muscleJointGroups[pecMuscles.pectoralisMajorA.muscleName] = pecMuscles.pectoralisMajorA
        bpClavicularPec = pecMuscles.ensureKeyExists(bpPectoralisMajor, "clavicular")
        pecMuscles.pectoralisMajorB = mb.MuscleJointGroup.createFromBlueprint(bpOrigin=bpClavicularPec.get("origin"),
                                                                              bpInsertion=bpClavicularPec.get(
                                                                                  "insertion"),
                                                                              bpCenter=bpClavicularPec.get("center"),
                                                                              originAttachObj=pecMuscles.clavicalJoint,
                                                                              insertionAttachObj=pecMuscles.upperArmTwistJoint,
                                                                              compressionFactor=0.5,
                                                                              stretchFactor=1.5)
        pecMuscles.muscleJointGroups[pecMuscles.pectoralisMajorB.muscleName] = pecMuscles.pectoralisMajorB

        # pecMuscles.finalize()
        return pecMuscles


class DeltoidMuscles(BilateralMuscles):
    """
    Create the deltoid muscle joint groups for a given side of the body.
    """

    def __init__(self, name='Deltoid', side='Left', acromionJoint=None, scapulaJoint=None,
                 upperArmTwist0Joint=None, upperArmTwist1Joint=None):
        """
        :param name: (str, optional) The name of the muscle component. Default is "Deltoid".
        :param side: (str, optional) The side of the body ('Left' or 'Right'). Default is `'Left'`.
        :param acromionJoint: (str or None) The name of the joint for the acromion. If None, the joint will
          be derived using a naming convention.
        :param scapulaJoint: (str or None) The name of the joint for the scapula. If None, the joint will
          be derived using a naming convention.
        *** twist0 joint is used to drive the twisting of deltoid muscle groups ***
        :param upperArmTwist0Joint:(str or None) The name of the first twist joint in the upper arm. If None,
          the joint will be derived using a naming convention.
        :param upperArmTwist1Joint: (str or None) The name of the second twist joint in the upper arm. If None,
          the joint will be derived using a naming convention.

        """
        super(DeltoidMuscles, self).__init__(name=name, side=side)
        # get all the joint dependencies
        self.clavicalJoint = self.getJoint(f'JO{side}Clavicle1')
        self.upperArmJoint = self.getJoint(f'JO{side}UpperArm1')

        if not acromionJoint:
            self.acromionJoint = self.getJoint('{0}Acromion1'.format(side))
        else:
            self.acromionJoint = self.getJoint(acromionJoint)

        if not scapulaJoint:
            self.scapulaJoint = self.getJoint('{0}ScapulaRoot1'.format(side))
        else:
            self.scapulaJoint = self.getJoint(scapulaJoint)

        if not upperArmTwist0Joint:
            self.upperArmTwist0Joint = self.getJoint('{0}UpperArm1Twist0'.format(side))
        else:
            self.upperArmTwist0Joint = self.getJoint(upperArmTwist0Joint)

        if not upperArmTwist1Joint:
            self.upperArmTwist1Joint = self.getJoint('{0}UpperArm1Twist1'.format(side))
        else:
            self.upperArmTwist1Joint = self.getJoint(upperArmTwist1Joint)

        self.deltoidA = None
        self.deltoidB = None
        self.deltoidC = None

    def add(self):
        # origin: lateral third of the clavical
        clavicalJointPos = om.MVector(mc.xform(self.clavicalJoint, translation=True, q=True, ws=True))
        acromoinJointPos = om.MVector(mc.xform(self.acromionJoint, translation=True, q=True, ws=True))
        upperArmTwist1JointPos = om.MVector(
            mc.xform(self.upperArmTwist1Joint, translation=True, q=True, ws=True))
        offsetVector = (clavicalJointPos - acromoinJointPos) / 6.0
        deltoidAOrigin = acromoinJointPos + offsetVector
        # deltoid insertion
        deltoidInsertion = upperArmTwist1JointPos
        self.deltoidA = mb.MuscleJointGroup.createFromAttachObjs(muscleName='{0}{1}A'.format(self.side, self.name),
                                                                 originAttachObj=self.clavicalJoint,
                                                                 insertionAttachObj=self.upperArmTwist1Joint,
                                                                 compressionFactor=0.5,
                                                                 stretchFactor=1.5)
        self.muscleJointGroups[self.deltoidA.muscleName] = self.deltoidA
        mc.xform(self.deltoidA.originLoc, translation=deltoidAOrigin, worldSpace=True)
        mc.xform(self.deltoidA.insertionLoc, translation=deltoidInsertion, worldSpace=True)
        # origin: aromion of scapula
        deltoidBOrigin = acromoinJointPos
        self.deltoidB = mb.MuscleJointGroup.createFromAttachObjs(muscleName='{0}{1}B'.format(self.side, self.name),
                                                                 originAttachObj=self.clavicalJoint,
                                                                 insertionAttachObj=self.upperArmTwist1Joint,
                                                                 compressionFactor=0.5,
                                                                 stretchFactor=1.5)
        self.muscleJointGroups[self.deltoidB.muscleName] = self.deltoidB
        mc.xform(self.deltoidB.originLoc, translation=deltoidBOrigin, worldSpace=True)
        mc.xform(self.deltoidB.insertionLoc, translation=deltoidInsertion, worldSpace=True)
        scapulaJointPos = om.MVector(mc.xform(self.scapulaJoint, translation=True, q=True, ws=True))
        offsetVector = (scapulaJointPos - acromoinJointPos) / 4.0
        # origin: lateral third of the spine of scapula
        deltoidCOrigin = offsetVector + acromoinJointPos
        self.deltoidC = mb.MuscleJointGroup.createFromAttachObjs(muscleName='{0}{1}C'.format(self.side, self.name),
                                                                 originAttachObj=self.scapulaJoint,
                                                                 insertionAttachObj=self.upperArmTwist1Joint,
                                                                 compressionFactor=0.5,
                                                                 stretchFactor=1.5)
        self.muscleJointGroups[self.deltoidC.muscleName] = self.deltoidC
        mc.xform(self.deltoidC.originLoc, translation=deltoidCOrigin, worldSpace=True)
        mc.xform(self.deltoidC.insertionLoc, translation=deltoidInsertion, worldSpace=True)

    def mirror(self):
        mirroredDeltoid = DeltoidMuscles(name=self.name, side=self.getOtherSide(self.side))
        mirroredDeltoid.deltoidA = self.deltoidA.mirror(f"{self.getOtherSide(self.side)}{self.name}A",
                                                        mirroredDeltoid.clavicalJoint,
                                                        mirroredDeltoid.upperArmTwist1Joint)

        mirroredDeltoid.muscleJointGroups[mirroredDeltoid.deltoidA.muscleName] = mirroredDeltoid.deltoidA

        mirroredDeltoid.deltoidB = self.deltoidB.mirror(f"{self.getOtherSide(self.side)}{self.name}B",
                                                        mirroredDeltoid.clavicalJoint,
                                                        mirroredDeltoid.upperArmTwist1Joint)

        mirroredDeltoid.muscleJointGroups[mirroredDeltoid.deltoidB.muscleName] = mirroredDeltoid.deltoidB

        mirroredDeltoid.deltoidC = self.deltoidC.mirror(f"{self.getOtherSide(self.side)}{self.name}C",
                                                        mirroredDeltoid.scapulaJoint,
                                                        mirroredDeltoid.upperArmTwist1Joint)

        mirroredDeltoid.muscleJointGroups[mirroredDeltoid.deltoidB.muscleName] = mirroredDeltoid.deltoidB

        return mirroredDeltoid

    def finalize(self):
        super(DeltoidMuscles, self).finalize()
        mc.delete(self.deltoidA.mainAimConstraint)
        self.mainAimConstraint = mc.aimConstraint(self.deltoidA.muscleInsertion, self.deltoidA.muscleBase,
                                                  aimVector=[0, 1, 0],
                                                  upVector=[1, 0, 0],
                                                  worldUpType='objectrotation',
                                                  worldUpObject=self.upperArmTwist0Joint,
                                                  worldUpVector=config.BIPED_UPPERARMS_TWIST_DATA.get(self.side).get(
                                                      'upAxis'),
                                                  maintainOffset=True)
        mc.delete(self.deltoidB.mainAimConstraint)
        self.mainAimConstraint = mc.aimConstraint(self.deltoidB.muscleInsertion, self.deltoidB.muscleBase,
                                                  aimVector=[0, 1, 0],
                                                  upVector=[1, 0, 0],
                                                  worldUpType='objectrotation',
                                                  worldUpObject=self.upperArmTwist0Joint,
                                                  worldUpVector=config.BIPED_UPPERARMS_TWIST_DATA.get(self.side).get(
                                                      'upAxis'),
                                                  maintainOffset=True)
        mc.delete(self.deltoidC.mainAimConstraint)
        self.mainAimConstraint = mc.aimConstraint(self.deltoidC.muscleInsertion, self.deltoidC.muscleBase,
                                                  aimVector=[0, 1, 0],
                                                  upVector=[1, 0, 0],
                                                  worldUpType='objectrotation',
                                                  worldUpObject=self.upperArmTwist0Joint,
                                                  worldUpVector=config.BIPED_UPPERARMS_TWIST_DATA.get(self.side).get(
                                                      'upAxis'),
                                                  maintainOffset=True)

        self.deltoidBConstraint = mc.pointConstraint(self.deltoidA.muscleOffset, self.deltoidC.muscleOffset,
                                                     self.deltoidB.muscleOffset, maintainOffset=True, weight=1)

        dummyNode = mc.duplicate(self.deltoidC.muscleOffset, name=self.deltoidC.muscleOffset + '_dummy',
                                 parentOnly=True)[0]
        # outputNode = mc.duplicate(self.deltoidC.muscleOffset, name='outputNode', parentOnly=True)[0]

        # self.deltoidCConstraint = mc.pointConstraint(self.upperArmJoint, self.deltoidC.muscleOffset,
        #                                              mo=True, weight=1, skip=['x', 'y'])

        mc.pointConstraint(self.upperArmJoint, dummyNode, maintainOffset=True, weight=1)
        mc.connectAttr('{0}.tz'.format(dummyNode), '{0}.tz'.format(self.deltoidC.muscleOffset))

    @classmethod
    def build(cls, side, bpDeltoid):
        """
         Builds the deltoid muscle group for a specified side using blueprint data.
         This method constructs the three components of the deltoid muscle: anterior, lateral, and posterior,
         based on provided blueprint definitions.
        :param side: (Side Enum): The side of the body.
        :param bpDeltoid: (dict) A blueprint dictionary containing the definitions for the deltoid.
                bpDeltoid = {"anterior": {"origin": ..., "insertion": ..., "center": ...},
                             "lateral": {"origin": ..., "insertion": ..., "center": ...},
                             "posterior": {"origin": ..., "insertion": ..., "center": ...}}
        :return: (DeltoidMuscles) An instance of "DeltoidMuscles"`" populated with the created muscle joints.
        """
        deltoidMuscles = cls(side=side)
        bpAnteriorDeltoid = deltoidMuscles.ensureKeyExists(bpDeltoid, "anterior")
        deltoidMuscles.deltoidA = mb.MuscleJointGroup.createFromBlueprint(bpOrigin=bpAnteriorDeltoid.get("origin"),
                                                                          bpInsertion=bpAnteriorDeltoid.get(
                                                                              "insertion"),
                                                                          bpCenter=bpAnteriorDeltoid.get("center"),
                                                                          originAttachObj=deltoidMuscles.clavicalJoint,
                                                                          insertionAttachObj=deltoidMuscles.upperArmTwist1Joint,
                                                                          compressionFactor=0.5,
                                                                          stretchFactor=1.5)
        deltoidMuscles.muscleJointGroups[deltoidMuscles.deltoidA.muscleName] = deltoidMuscles.deltoidA

        bpLateralDeltoid = deltoidMuscles.ensureKeyExists(bpDeltoid, "lateral")
        deltoidMuscles.deltoidB = mb.MuscleJointGroup.createFromBlueprint(bpOrigin=bpLateralDeltoid.get("origin"),
                                                                          bpInsertion=bpLateralDeltoid.get("insertion"),
                                                                          bpCenter=bpLateralDeltoid.get("center"),
                                                                          originAttachObj=deltoidMuscles.clavicalJoint,
                                                                          insertionAttachObj=deltoidMuscles.upperArmTwist1Joint,
                                                                          compressionFactor=0.5,
                                                                          stretchFactor=1.5)
        deltoidMuscles.muscleJointGroups[deltoidMuscles.deltoidB.muscleName] = deltoidMuscles.deltoidB

        bpPosteriorDetoid = deltoidMuscles.ensureKeyExists(bpDeltoid, "posterior")
        deltoidMuscles.deltoidC = mb.MuscleJointGroup.createFromBlueprint(bpOrigin=bpPosteriorDetoid.get("origin"),
                                                                          bpInsertion=bpPosteriorDetoid.get(
                                                                              "insertion"),
                                                                          bpCenter=bpPosteriorDetoid.get("center"),
                                                                          originAttachObj=deltoidMuscles.scapulaJoint,
                                                                          insertionAttachObj=deltoidMuscles.upperArmTwist1Joint,
                                                                          compressionFactor=0.5,
                                                                          stretchFactor=1.5)
        deltoidMuscles.muscleJointGroups[deltoidMuscles.deltoidC.muscleName] = deltoidMuscles.deltoidC

        # deltoidMuscles.finalize()
        return deltoidMuscles


class UpperArmMuscles(BilateralMuscles):
    """
    Create the deltoid muscle joint groups for a given side of the body.
    """

    def __init__(self, name='upperArmMuscles', side='Left',
                 upperArmTwistJoint=None, lowerArmTwistJoint=None,
                 scapulaJoint=None, inferiorAngleJoint=None):
        """
        Represents the upper arm muscle groups, including bicep and tricep muscles, for a given side of the body.
        :param name: (str, optional) The name of the muscle component
        :param side: (str, optional) The side of the body ('Left' or 'Right'). Default is `'Left'`.
        :param upperArmTwistJoint:  (str, optional) The name of the twist joint as attachment on the upper arm
        :param lowerArmTwistJoint: (str, optional) The name of the twist joint as attachment on the lower arm
        :param scapulaJoint: (str, optional) The name of the scapula root joint
        :param inferiorAngleJoint: (str, optional) The name of the scapula tip joint
        """
        super(UpperArmMuscles, self).__init__(name=name, side=side)
        # get all the joint dependencies
        self.lowerArmJoint = self.getJoint(f'JO{side}LowerArm1')
        self.upperArmJoint = self.getJoint(f'JO{side}UpperArm1')

        if not scapulaJoint:
            self.scapulaJoint = self.getJoint('{0}ScapulaRoot1'.format(side))
        else:
            self.scapulaJoint = self.getJoint(scapulaJoint)

        if not inferiorAngleJoint:
            self.inferiorAngleJoint = self.getJoint('{0}InferiorAngle1'.format(side))
        else:
            self.inferiorAngleJoint = self.getJoint(inferiorAngleJoint)

        if not upperArmTwistJoint:
            self.upperArmTwistJoint = self.getJoint('{0}UpperArm1Twist1'.format(side))
        else:
            self.upperArmTwistJoint = self.getJoint(upperArmTwistJoint)

        if not lowerArmTwistJoint:
            self.lowerArmTwistJoint = self.getJoint('{0}LowerArm1Twist0'.format(side))
        else:
            self.lowerArmTwistJoint = self.getJoint(lowerArmTwistJoint)

        self.bicep = None
        self.tricep = None

    def add(self):
        upperArmJointPos = om.MVector(mc.xform(self.upperArmJoint, translation=True, q=True, ws=True))
        upperArmTwistJointPos = om.MVector(mc.xform(self.upperArmTwistJoint, translation=True, q=True, ws=True))
        bipedOrigin = upperArmJointPos + (upperArmTwistJointPos - upperArmJointPos) * 0.2
        lowerArmJointPos = om.MVector(mc.xform(self.lowerArmJoint, translation=True, q=True, ws=True))
        lowerArmTwistJointPos = om.MVector(mc.xform(self.lowerArmTwistJoint, translation=True, q=True, ws=True))
        lowerArmJointWorldMatrix = mc.getAttr('{0}.worldMatrix'.format(self.lowerArmJoint))
        bipedInsertion = lowerArmJointPos + (lowerArmTwistJointPos - lowerArmJointPos) * 0.2 - om.MVector(
            lowerArmJointWorldMatrix[8: 11]) * 0.02
        self.bicep = mb.MuscleJointGroup.createFromAttachObjs(muscleName='{0}Bicep'.format(self.side),
                                                              originAttachObj=self.upperArmTwistJoint,
                                                              insertionAttachObj=self.lowerArmTwistJoint,
                                                              compressionFactor=0.5,
                                                              stretchFactor=1.5)
        self.muscleJointGroups[self.bicep.muscleName] = self.bicep
        mc.xform(self.bicep.originLoc, translation=bipedOrigin, worldSpace=True)
        mc.xform(self.bicep.insertionLoc, translation=bipedInsertion, worldSpace=True)

        self.tricep = mb.MuscleJointGroup.createFromAttachObjs(muscleName='{0}Tricep'.format(self.side),
                                                               originAttachObj=self.scapulaJoint,
                                                               insertionAttachObj=self.lowerArmJoint,
                                                               compressionFactor=0.5,
                                                               stretchFactor=1.5)
        self.muscleJointGroups[self.tricep.muscleName] = self.tricep
        inferiorAngleJointPos = om.MVector(mc.xform(self.inferiorAngleJoint, translation=True, q=True, ws=True))
        tricepOrigin = upperArmJointPos + (inferiorAngleJointPos - upperArmJointPos) * 0.2
        mc.xform(self.tricep.originLoc, translation=tricepOrigin, worldSpace=True)

    def mirror(self):
        mirroredArmMuscles = UpperArmMuscles(name=self.name, side=self.getOtherSide(self.side))
        mirroredArmMuscles.bicep = self.bicep.mirror(f"{self.getOtherSide(self.side)}{self.name}A",
                                                     mirroredArmMuscles.upperArmTwistJoint,
                                                     mirroredArmMuscles.lowerArmTwistJoint)

        mirroredArmMuscles.muscleJointGroups[mirroredArmMuscles.bicep.muscleName] = mirroredArmMuscles.bicep

        mirroredArmMuscles.tricep = self.tricep.mirror(f"{self.getOtherSide(self.side)}{self.name}B",
                                                       mirroredArmMuscles.scapulaJoint,
                                                       mirroredArmMuscles.lowerArmJoint)

        mirroredArmMuscles.muscleJointGroups[mirroredArmMuscles.tricep.muscleName] = mirroredArmMuscles.tricep

        return mirroredArmMuscles

    def finalize(self):
        super(UpperArmMuscles, self).finalize()
        # twist setup: get the twist value joint and twist basis joint and orient constraint the bicep joint
        twistValueJoint = self.getJoint('{0}UpperArm1TwistValue1'.format(self.side))
        basisOffsetJoint = self.getJoint('{0}UpperArm1BasisOffset1'.format(self.side))
        # twist2Joint = self.getJoint('{0}UpperArm1Twist2'.format(self.side))
        orientConstraint = \
            mc.orientConstraint(twistValueJoint, basisOffsetJoint, self.bicep.muscleOrigin, mo=True, weight=1)[0]
        mc.setAttr('{0}.interpType'.format(orientConstraint), 2)

        dummyNode = mc.duplicate(self.bicep.muscleOffset, name=self.bicep.muscleOffset + '_dummy',
                                 parentOnly=True)[0]
        # outputNode = mc.duplicate(self.bicep.muscleOffset, name='outputNode', parentOnly=True)[0]

        # mc.parentConstraint(self.upperArmTwistJoint, twist2Joint, self.bicep.muscleOffset, mo=True, weight=1,
        #                     skipRotate=['x', 'y', 'z'],
        #                     skipTranslate=['x', 'y'])

        mc.parentConstraint(self.upperArmJoint, dummyNode, mo=True, weight=1)
        mc.connectAttr('{0}.tz'.format(dummyNode), '{0}.tz'.format(self.bicep.muscleOffset))

        orientConstraint = \
            mc.orientConstraint(twistValueJoint, basisOffsetJoint, self.tricep.muscleOrigin, mo=True, weight=1)[0]
        mc.setAttr('{0}.interpType'.format(orientConstraint), 2)

        dummyNode = mc.duplicate(self.tricep.muscleOffset, name=self.tricep.muscleOffset + '_dummy',
                                 parentOnly=True)[0]
        # outputNode = mc.duplicate(self.tricep.muscleOffset, name='outputNode', parentOnly=True)[0]

        # mc.parentConstraint(self.upperArmTwistJoint, twist2Joint, self.tricep.muscleOffset, mo=True, weight=1,
        #                     skipRotate=['x', 'y', 'z'],
        #                     skipTranslate=['x', 'y'])

        mc.parentConstraint(self.upperArmJoint, dummyNode, mo=True, weight=1)
        mc.connectAttr('{0}.tz'.format(dummyNode), '{0}.tz'.format(self.tricep.muscleOffset))

    @classmethod
    def build(cls, side, bpArmMuscles):
        """
        Builds and sets up the upper arm muscle group for a given side of the body using the provided blueprint data.
        :param side: (Side Enum): The side of the body.
        :param bpArmMuscles: (dict) A dictionary containing the blueprint data for the arm muscles:
                        bpArmMuscles = {"bicep": {"origin": ..., "insertion": ..., "center": ...},
                                        "tricep": {"origin": ..., "insertion": ..., "center": ...}}
        :return: (UpperArmMuscles)  An instance of `UpperArmMuscles` with the bicep and tricep muscles.
        """
        armMuscles = cls(side=side)
        bpBicep = armMuscles.ensureKeyExists(bpArmMuscles, "bicep")
        armMuscles.bicep = mb.MuscleJointGroup.createFromBlueprint(bpOrigin=bpBicep.get("origin"),
                                                                   bpInsertion=bpBicep.get("insertion"),
                                                                   bpCenter=bpBicep.get("center"),
                                                                   originAttachObj=armMuscles.upperArmTwistJoint,
                                                                   insertionAttachObj=armMuscles.lowerArmTwistJoint,
                                                                   compressionFactor=0.5,
                                                                   stretchFactor=1.5)
        armMuscles.muscleJointGroups[armMuscles.bicep.muscleName] = armMuscles.bicep

        bpTricep = armMuscles.ensureKeyExists(bpArmMuscles, "tricep")
        armMuscles.tricep = mb.MuscleJointGroup.createFromBlueprint(bpOrigin=bpTricep.get("origin"),
                                                                    bpInsertion=bpTricep.get("insertion"),
                                                                    bpCenter=bpTricep.get("center"),
                                                                    originAttachObj=armMuscles.scapulaJoint,
                                                                    insertionAttachObj=armMuscles.lowerArmJoint,
                                                                    compressionFactor=0.5,
                                                                    stretchFactor=1.5)
        armMuscles.muscleJointGroups[armMuscles.tricep.muscleName] = armMuscles.tricep

        # armMuscles.finalize()
        return armMuscles
