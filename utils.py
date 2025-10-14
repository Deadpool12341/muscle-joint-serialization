from . import muscle_template as template
import maya.cmds as mc
import logging
import json

logger = logging.getLogger(__name__)


# TrapeziusMuscles
def getTrapeziusMuscles():
    trapeziusData = {}
    for side in ['Left', 'Right']:
        trapeziusData[side] = {}

        for muscleType in 'ABC':
            if not mc.ls('{0}Trapezius{1}_muscleOrigin'.format(side, muscleType)) or not mc.ls(
                    '{0}Trapezius{1}_muscleInsertion'.format(side, muscleType)):
                logger.warning('Cannot find trapezius muscle setup on the {0} side'.format(side))
                continue

            muscleOrigin = mc.ls('{0}Trapezius{1}_muscleOrigin'.format(side, muscleType))[0]
            muscleOriginPos = mc.xform(muscleOrigin, translation=True, q=True, ws=True)
            muscleInsertion = mc.ls('{0}Trapezius{1}_muscleInsertion'.format(side, muscleType))[0]
            muscleInsertionPos = mc.xform(muscleInsertion, translation=True, q=True, ws=True)
            muscleCenter = mc.ls('{0}Trapezius{1}_muscleDriver'.format(side, muscleType))[0]
            muscleCenterPos = mc.xform(muscleCenter, translation=True, q=True, ws=True)
            trapeziusData[side].update({muscleOrigin: muscleOriginPos})
            trapeziusData[side].update({muscleInsertion: muscleInsertionPos})
            trapeziusData[side].update({muscleCenter: muscleCenterPos})

    logger.info(trapeziusData)
    return trapeziusData


# LatissimusDorsiMuscles
def getLatissimusDorsiMuscles():
    latissimusDorsiData = {}
    for side in ['Left', 'Right']:
        latissimusDorsiData[side] = {}
        for muscleType in 'AB':
            if not mc.ls('{0}LatissimusDorsi{1}_muscleOrigin'.format(side, muscleType)) or not mc.ls(
                    '{0}LatissimusDorsi{1}_muscleInsertion'.format(side, muscleType)):
                logger.warning(
                    'Cannot find latissimus dorsi muscle setup for {0} on the {1} side'.format(muscleType, side))
                continue

            muscleOrigin = mc.ls('{0}LatissimusDorsi{1}_muscleOrigin'.format(side, muscleType))[0]
            muscleOriginPos = mc.xform(muscleOrigin, translation=True, q=True, ws=True)
            muscleInsertion = mc.ls('{0}LatissimusDorsi{1}_muscleInsertion'.format(side, muscleType))[0]
            muscleInsertionPos = mc.xform(muscleInsertion, translation=True, q=True, ws=True)
            muscleCenter = mc.ls('{0}LatissimusDorsi{1}_muscleDriver'.format(side, muscleType))[0]
            muscleCenterPos = mc.xform(muscleCenter, translation=True, q=True, ws=True)
            latissimusDorsiData[side].update({muscleOrigin: muscleOriginPos})
            latissimusDorsiData[side].update({muscleInsertion: muscleInsertionPos})
            latissimusDorsiData[side].update({muscleCenter: muscleCenterPos})

    logger.info(latissimusDorsiData)
    return latissimusDorsiData


# TerasMajorMuscles
def getTerasMajorMuscles():
    terasMajorData = {}
    for side in ['Left', 'Right']:
        terasMajorData[side] = {}
        if not mc.ls('{0}TerasMajor_muscleOrigin'.format(side)) or not mc.ls(
                '{0}TerasMajor_muscleInsertion'.format(side)):
            logger.warning('Cannot find teras major muscle setup on the {0} side'.format(side))
            continue

        muscleOrigin = mc.ls('{0}TerasMajor_muscleOrigin'.format(side))[0]
        muscleOriginPos = mc.xform(muscleOrigin, translation=True, q=True, ws=True)
        muscleInsertion = mc.ls('{0}TerasMajor_muscleInsertion'.format(side))[0]
        muscleInsertionPos = mc.xform(muscleInsertion, translation=True, q=True, ws=True)
        muscleCenter = mc.ls('{0}TerasMajor_muscleDriver'.format(side))[0]
        muscleCenterPos = mc.xform(muscleCenter, translation=True, q=True, ws=True)
        terasMajorData[side].update({muscleOrigin: muscleOriginPos})
        terasMajorData[side].update({muscleInsertion: muscleInsertionPos})
        terasMajorData[side].update({muscleCenter: muscleCenterPos})

    logger.info(terasMajorData)
    return terasMajorData


# LatissimusDorsiMuscles
def getPectoralisMajorMuscles():
    pectoralisMajorData = {}
    for side in ['Left', 'Right']:
        pectoralisMajorData[side] = {}
        for muscleType in 'AB':
            if not mc.ls('{0}PectoralisMajor{1}_muscleOrigin'.format(side, muscleType)) or not mc.ls(
                    '{0}PectoralisMajor{1}_muscleInsertion'.format(side, muscleType)):
                logger.warning('Cannot find pectoralis major muscle setup on the {0} side'.format(side))
                continue

            muscleOrigin = mc.ls('{0}PectoralisMajor{1}_muscleOrigin'.format(side, muscleType))[0]
            muscleOriginPos = mc.xform(muscleOrigin, translation=True, q=True, ws=True)
            muscleInsertion = mc.ls('{0}PectoralisMajor{1}_muscleInsertion'.format(side, muscleType))[0]
            muscleInsertionPos = mc.xform(muscleInsertion, translation=True, q=True, ws=True)
            muscleCenter = mc.ls('{0}PectoralisMajor{1}_muscleDriver'.format(side, muscleType))[0]
            muscleCenterPos = mc.xform(muscleCenter, translation=True, q=True, ws=True)
            pectoralisMajorData[side].update({muscleOrigin: muscleOriginPos})
            pectoralisMajorData[side].update({muscleInsertion: muscleInsertionPos})
            pectoralisMajorData[side].update({muscleCenter: muscleCenterPos})

    logger.info(pectoralisMajorData)
    return pectoralisMajorData


# Deltoid
def getDeltoidMuscles():
    deltoidData = {}
    for side in ['Left', 'Right']:
        deltoidData[side] = {}
        for muscleType in 'ABC':
            if not mc.ls('{0}Deltoid{1}_muscleOrigin'.format(side, muscleType)) or not mc.ls(
                    '{0}Deltoid{1}_muscleInsertion'.format(side, muscleType)):
                logger.warning('Cannot find deltoid muscle setup on the {0} side'.format(side))
                continue

            muscleOrigin = mc.ls('{0}Deltoid{1}_muscleOrigin'.format(side, muscleType))[0]
            muscleOriginPos = mc.xform(muscleOrigin, translation=True, q=True, ws=True)
            muscleInsertion = mc.ls('{0}Deltoid{1}_muscleInsertion'.format(side, muscleType))[0]
            muscleInsertionPos = mc.xform(muscleInsertion, translation=True, q=True, ws=True)
            muscleCenter = mc.ls('{0}Deltoid{1}_muscleDriver'.format(side, muscleType))[0]
            muscleCenterPos = mc.xform(muscleCenter, translation=True, q=True, ws=True)
            deltoidData[side].update({muscleOrigin: muscleOriginPos})
            deltoidData[side].update({muscleInsertion: muscleInsertionPos})
            deltoidData[side].update({muscleCenter: muscleCenterPos})

    logger.info(deltoidData)
    return deltoidData


# ArmMuscles
def getArmMuscles():
    armMusclesData = {}
    for side in ['Left', 'Right']:
        armMusclesData[side] = {}
        for muscleType in ['Bicep', 'Tricep']:
            if not mc.ls('{0}{1}_muscleOrigin'.format(side, muscleType)) or not mc.ls(
                    '{0}{1}_muscleInsertion'.format(side, muscleType)):
                logger.warning('Cannot find arm muscle setup on the {0} side'.format(side))
                continue

            muscleOrigin = mc.ls('{0}{1}_muscleOrigin'.format(side, muscleType))[0]
            muscleOriginPos = mc.xform(muscleOrigin, translation=True, q=True, ws=True)
            muscleInsertion = mc.ls('{0}{1}_muscleInsertion'.format(side, muscleType))[0]
            muscleInsertionPos = mc.xform(muscleInsertion, translation=True, q=True, ws=True)
            muscleCenter = mc.ls('{0}{1}_muscleDriver'.format(side, muscleType))[0]
            muscleCenterPos = mc.xform(muscleCenter, translation=True, q=True, ws=True)
            armMusclesData[side].update({muscleOrigin: muscleOriginPos})
            armMusclesData[side].update({muscleInsertion: muscleInsertionPos})
            armMusclesData[side].update({muscleCenter: muscleCenterPos})

    logger.info(armMusclesData)
    return armMusclesData


def exportMuscles(filePath):
    musclesData = {}
    trapeziusData = getTrapeziusMuscles()
    musclesData['Trapezius'] = trapeziusData

    latissimusDorsiData = getLatissimusDorsiMuscles()
    musclesData["LatissimusDorsi"] = latissimusDorsiData

    terasMajorData = getTerasMajorMuscles()
    musclesData["TerasMajor"] = terasMajorData

    pectoralisMajorData = getPectoralisMajorMuscles()
    musclesData["PectoralisMajor"] = pectoralisMajorData

    deltoidData = getDeltoidMuscles()
    musclesData["Deltoid"] = deltoidData

    armsData = getArmMuscles()
    musclesData["Arms"] = armsData

    logger.info(musclesData)

    with open(filePath, 'w') as fp:
        json.dump(musclesData, fp, ensure_ascii=False, indent=4, separators=(',', ': '), sort_keys=True)


def generateMusclesFromFile(filePath):
    with open(filePath) as fp:
        musclesData = json.load(fp)
    # trapezius
    trapeziusData = musclesData.get('Trapezius')

    if trapeziusData:
        for side in trapeziusData.keys():
            builder = template.TrapeziusMuscles(side=side)
            builder.add()
            # Trap A
            originPos = trapeziusData.get(side).get('{0}TrapeziusA_muscleOrigin'.format(side))
            mc.xform(builder.trapeziusA.originLoc, translation=originPos, ws=True)
            insertionPos = trapeziusData.get(side).get('{0}TrapeziusA_muscleInsertion'.format(side))
            mc.xform(builder.trapeziusA.insertionLoc, translation=insertionPos, ws=True)
            centerPos = trapeziusData.get(side).get('{0}TrapeziusA_muscleDriver'.format(side))

            mc.xform(builder.trapeziusA.centerLoc, translation=centerPos, ws=True)
            # Trap B
            originPos = trapeziusData.get(side).get('{0}TrapeziusB_muscleOrigin'.format(side))
            mc.xform(builder.trapeziusB.originLoc, translation=originPos, ws=True)
            insertionPos = trapeziusData.get(side).get('{0}TrapeziusB_muscleInsertion'.format(side))
            mc.xform(builder.trapeziusB.insertionLoc, translation=insertionPos, ws=True)
            centerPos = trapeziusData.get(side).get('{0}TrapeziusB_muscleDriver'.format(side))
            mc.xform(builder.trapeziusB.centerLoc, translation=centerPos, ws=True)
            # Trap C
            originPos = trapeziusData.get(side).get('{0}TrapeziusC_muscleOrigin'.format(side))
            mc.xform(builder.trapeziusC.originLoc, translation=originPos, ws=True)
            insertionPos = trapeziusData.get(side).get('{0}TrapeziusC_muscleInsertion'.format(side))
            mc.xform(builder.trapeziusC.insertionLoc, translation=insertionPos, ws=True)
            centerPos = trapeziusData.get(side).get('{0}TrapeziusC_muscleDriver'.format(side))
            mc.xform(builder.trapeziusC.centerLoc, translation=centerPos, ws=True)
            builder.finalize()


def generateMusclesBpObjects(filePath):
    with open(filePath) as fp:
        musclesData = json.load(fp)

    # trapezius:
    trapeziusData = musclesData.get('Trapezius')
    if trapeziusData:
        trapGroup = mc.group(world=True, empty=True, name="Trapezius")
        for side in trapeziusData.keys():
            sideGroup = mc.group(world=True, empty=True, name=f"{side}")
            mc.parent(sideGroup, trapGroup)
            for region in "ABC":
                originPos = trapeziusData.get(side).get(f'{side}Trapezius{region}_muscleOrigin')
                insertionPos = trapeziusData.get(side).get(f'{side}Trapezius{region}_muscleInsertion')
                centerPos = trapeziusData.get(side).get(f'{side}Trapezius{region}_muscleDriver')

                bpOrigin = mc.createNode("joint", name=f"bp{side}Trapezius{region}_muscleOrigin")
                bpInsertion = mc.createNode("joint", name=f"bp{side}Trapezius{region}_muscleInsertion")
                bpCenter = mc.createNode("joint", name=f"bp{side}Trapezius{region}_muscleDriver")
                mc.setAttr(f"{bpCenter}.radius", 2.0)
                mc.setAttr(f"{bpCenter}.overrideEnabled", 1)
                mc.setAttr(f"{bpCenter}.overrideColor", 13)  # 13 = red
                mc.xform(bpOrigin, translation=originPos, worldSpace=True)
                mc.xform(bpInsertion, translation=insertionPos, worldSpace=True)
                mc.xform(bpCenter, translation=centerPos, worldSpace=True)
                # parent bp objects to group
                mc.parent(bpOrigin, sideGroup)
                mc.parent(bpInsertion, sideGroup)
                mc.parent(bpCenter, sideGroup)


def generateMusclesFromBpObjects():
    # add trapezius muscles
    trapMuscles = {}
    for side in ["Left", "Right"]:
        bpTrap = {"upper": {"origin": f"bp{side}TrapeziusA_muscleOrigin",
                            "insertion": f"bp{side}TrapeziusA_muscleInsertion",
                            "center": f"bp{side}TrapeziusA_muscleDriver"
                            },
                  "middle": {"origin": f"bp{side}TrapeziusB_muscleOrigin",
                             "insertion": f"bp{side}TrapeziusB_muscleInsertion",
                             "center": f"bp{side}TrapeziusB_muscleDriver"
                             },
                  "lower": {"origin": f"bp{side}TrapeziusC_muscleOrigin",
                            "insertion": f"bp{side}TrapeziusC_muscleInsertion",
                            "center": f"bp{side}TrapeziusC_muscleDriver"
                            }
                  }
        trapMuscles[side] = template.TrapeziusMuscles.build(side, bpTrap)
    return trapMuscles
