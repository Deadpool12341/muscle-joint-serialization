import maya.cmds as cmds
import maya.api.OpenMaya as om


def createAimTransformation(aimPoint, targetPoint, upPoint,
                            aimVector=om.MVector.kZaxisVector,
                            upVector=om.MVector.kXaxisVector):
    """Add an aim constraint to the aim point, which convert the target point movement to aim point rotation

    Args:
        aimPoint (Vector4): aim point
        targetPoint (Vector4): current target point
        upPoint (Vector): this point is used to generate the up vector for the aim point
        aimVector (Vector4, optional): aim vector
        upVector (Vector4, optional): up vector

    Returns:
        Quaternion: Quaternion rotation for aim point to look at the target point
    """
    # aim vector
    uVector = (targetPoint - aimPoint).normal()
    # object up vector
    vVector = (upPoint - aimPoint).normal()
    # align the up vector with the object up, the orthognal issue will be fixed later
    wVector = (uVector ^ vVector).normal()
    # get the orthogonal v vector by cross product u and w, the cross product order matters
    vVector = wVector ^ uVector

    # construct TBN matrix
    TBNMatrix = om.MMatrix()
    UVWMatrix = om.MMatrix()
    # assign data to UVW matrix： base is forward/up/right
    UVWMatrix.setElement(0, 0, uVector.x)
    UVWMatrix.setElement(0, 1, uVector.y)
    UVWMatrix.setElement(0, 2, uVector.z)

    UVWMatrix.setElement(1, 0, vVector.x)
    UVWMatrix.setElement(1, 1, vVector.y)
    UVWMatrix.setElement(1, 2, vVector.z)

    UVWMatrix.setElement(2, 0, wVector.x)
    UVWMatrix.setElement(2, 1, wVector.y)
    UVWMatrix.setElement(2, 2, wVector.z)
    # assign data to TBN matrix
    # object's local coordinate system "forward vector", "up vector" and "right vector"
    # not saying where the object is currently facing in the world, but how it's structured internally
    TBNMatrix.setElement(0, 0, aimVector.x)
    TBNMatrix.setElement(0, 1, aimVector.y)
    TBNMatrix.setElement(0, 2, aimVector.z)

    TBNMatrix.setElement(1, 0, upVector.x)
    TBNMatrix.setElement(1, 1, upVector.y)
    TBNMatrix.setElement(1, 2, upVector.z)

    TBNMatrix.setElement(2, 0, (aimVector ^ upVector).x)
    TBNMatrix.setElement(2, 1, (aimVector ^ upVector).y)
    TBNMatrix.setElement(2, 2, (aimVector ^ upVector).z)
    # swap row
    # TBN * transformaionMatrix = UVWMatrix (target world orientation you want the object to match)
    # transformatinoMatrix: M = TBN⁻¹ * UVW (the rotation needed to bring the local orientation into world alignment)
    transformationMatrix = TBNMatrix.inverse() * UVWMatrix

    transformationMatrixFN = om.MTransformationMatrix(transformationMatrix)
    Translation = aimPoint - om.MPoint(0, 0, 0, 1)
    transformationMatrixFN.setTranslation(Translation, om.MSpace.kWorld)

    return transformationMatrixFN.asMatrix()
