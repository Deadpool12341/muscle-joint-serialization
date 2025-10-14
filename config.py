import maya.api.OpenMaya as om

BIPED_UPPERARMS_TWIST_DATA = {'Left': {'twistAxis': om.MVector.kYaxisVector,
                                       'upAxis': om.MVector.kXaxisVector},
                              'Right': {'twistAxis': om.MVector.kYaxisVector,
                                        'upAxis': om.MVector.kXnegAxisVector}}

BIPED_FOREARMS_TWIST_DATA = {'Left': {'twistAxis': om.MVector.kYaxisVector,
                                      'upAxis': om.MVector.kZaxisVector},
                             'Right': {'twistAxis': om.MVector.kYaxisVector,
                                       'upAxis': om.MVector.kZaxisVector}}
