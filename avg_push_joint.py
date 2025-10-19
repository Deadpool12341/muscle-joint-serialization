import maya.cmds as cmds
import logging

logger = logging.getLogger(__name__)

import maya.cmds as cmds


def _resolve_joint(joint_name_or_none):
    """返回关节的长路径；支持 None(用选择)、短名、含命名空间、层级中的短名。"""
    if joint_name_or_none is None:
        sel = cmds.ls(sl=True, type='joint', long=True) or cmds.ls(sl=True, long=True) or []
        if not sel:
            raise RuntimeError("未选择关节且未提供 elbow_joint。请选中一个关节或传入名字。")
        # 若选中了transform但不是joint，尝试取其shape/parent不再赘述；简单用第一个
        return sel[0]

    name = joint_name_or_none

    # 先精确找
    cands = cmds.ls(name, type='joint', long=True) or cmds.ls(name, long=True) or []
    # 若没找到且不含命名空间，尝试 *:name
    if not cands and ':' not in name:
        cands = cmds.ls('*:%s' % name, type='joint', long=True) or []
    # 再尝试在层级内匹配（可能同名）
    if not cands:
        cands = cmds.ls('**|%s' % name, type='joint', long=True) or []

    if not cands:
        raise RuntimeError("找不到关节：%s" % name)
    if len(cands) > 1:
        cmds.warning("找到多个同名关节，将使用第一个：%s" % cands[0])
    return cands[0]


def setup_elbow_avg_push(
        elbow_joint=None,  # None=用当前选择
        inherit_axis='x',  # 'x'/'y'/'z'，LeftElbowAvg继承该轴的一半旋转
        remap_output_min=-5.0,  # remapValue.outputMin，可外部暴露
        avg_name=None,  # None=自动从关节名生成，例如 JOLeftElbow1 -> LeftElbowAvg
        push_name=None  # None=自动从关节名生成，例如 JOLeftElbow1 -> LeftElbowPush
):
    assert inherit_axis.lower() in ('x', 'y', 'z'), "inherit_axis 必须是 'x' 'y' 或 'z'"
    axis = inherit_axis.lower()

    elbow_joint = _resolve_joint(elbow_joint)

    # Auto-generate avg_name and push_name if not provided
    if avg_name is None or push_name is None:
        import re
        elbow_short_name = elbow_joint.split('|')[-1]

        # Remove 'JO' prefix and trailing numbers to get base name
        if elbow_short_name.startswith('JO'):
            base_name = elbow_short_name[2:]  # Remove 'JO'
        else:
            base_name = elbow_short_name

        # Remove trailing numbers (e.g., '1' from 'LeftElbow1')
        base_name = re.sub(r'\d+$', '', base_name)

        if avg_name is None:
            avg_name = f"{base_name}Avg"
        if push_name is None:
            push_name = f"{base_name}Push"

    # 1) 父级
    parent_list = cmds.listRelatives(elbow_joint, parent=True, fullPath=True) or []
    if not parent_list:
        raise RuntimeError("关节 %s 没有父级，无法把 %s 挂到其父级下。" % (elbow_joint, avg_name))
    elbow_parent = parent_list[0]

    # 2) 创建/获取 Avg 与 Push 关节
    def ensure_joint(name):
        if cmds.objExists(name):
            return cmds.ls(name, long=True)[0]
        return cmds.createNode('joint', name=name)

    avg_jnt = ensure_joint(avg_name)
    push_jnt = ensure_joint(push_name)

    # 3) 层级
    try:
        cmds.parent(avg_jnt, elbow_parent)
    except:
        pass
    try:
        cmds.parent(push_jnt, avg_jnt)
    except:
        pass

    # 4) match transform 到肘关节
    m = cmds.xform(elbow_joint, q=True, ws=True, m=True)
    for j in (avg_jnt, push_jnt):
        for attr in ('t', 'r', 's'):
            for a in ('x', 'y', 'z'):
                at = "%s.%s%s" % (j, attr, a)
                if cmds.getAttr(at, lock=True):
                    cmds.setAttr(at, lock=False)
        cmds.xform(j, ws=True, m=m)

    # 5) 删除历史 & 半径
    for j in (avg_jnt, push_jnt):
        try:
            cmds.delete(j, ch=True)
        except:
            pass
        if cmds.attributeQuery('radius', n=j, exists=True):
            cmds.setAttr(j + '.radius', 0.5)

    # 5.5) Copy jointOrient from target joint and freeze transforms
    # Copy jointOrient from elbow to avg joint to maintain proper orientation
    for axis_name in ('X', 'Y', 'Z'):
        jo_attr = 'jointOrient{}'.format(axis_name)
        if cmds.attributeQuery(jo_attr, n=elbow_joint, exists=True):
            jo_value = cmds.getAttr('{}.{}'.format(elbow_joint, jo_attr))
            if cmds.attributeQuery(jo_attr, n=avg_jnt, exists=True):
                if cmds.getAttr('{}.{}'.format(avg_jnt, jo_attr), lock=True):
                    cmds.setAttr('{}.{}'.format(avg_jnt, jo_attr), lock=False)
                cmds.setAttr('{}.{}'.format(avg_jnt, jo_attr), jo_value)

    # Copy jointOrient from avg to push joint
    for axis_name in ('X', 'Y', 'Z'):
        jo_attr = 'jointOrient{}'.format(axis_name)
        if cmds.attributeQuery(jo_attr, n=avg_jnt, exists=True):
            jo_value = cmds.getAttr('{}.{}'.format(avg_jnt, jo_attr))
            if cmds.attributeQuery(jo_attr, n=push_jnt, exists=True):
                if cmds.getAttr('{}.{}'.format(push_jnt, jo_attr), lock=True):
                    cmds.setAttr('{}.{}'.format(push_jnt, jo_attr), lock=False)
                cmds.setAttr('{}.{}'.format(push_jnt, jo_attr), jo_value)

    # Freeze rotation for avg joint
    for axis_attr in ('rotateX', 'rotateY', 'rotateZ'):
        attr_path = "{}.{}".format(avg_jnt, axis_attr)
        if cmds.getAttr(attr_path, lock=True):
            cmds.setAttr(attr_path, lock=False)
        cmds.setAttr(attr_path, 0)

    # Freeze both rotation and translation for push joint
    for axis_attr in ('translateX', 'translateY', 'translateZ', 'rotateX', 'rotateY', 'rotateZ'):
        attr_path = "{}.{}".format(push_jnt, axis_attr)
        if cmds.getAttr(attr_path, lock=True):
            cmds.setAttr(attr_path, lock=False)
        cmds.setAttr(attr_path, 0)

    # 6) Avg 继承 Elbow 指定轴的一半旋转
    # IMPORTANT: Connect from elbow_joint (not parent), using inherit_axis
    half_mdl = cmds.createNode('multDoubleLinear', name='{}_half_{}_mdl'.format(avg_name, axis))
    cmds.setAttr(half_mdl + '.input2', 0.5)
    # Connect elbow's rotation to avg (e.g., JOLeftElbow1.rotateX -> LeftElbowAvg.rotateX * 0.5)
    cmds.connectAttr('{}.rotate{}'.format(elbow_joint, axis.upper()), half_mdl + '.input1', f=True)

    rot_attr = '{}.rotate{}'.format(avg_jnt, axis.upper())
    if cmds.getAttr(rot_attr, lock=True):
        cmds.setAttr(rot_attr, lock=False)
    cmds.connectAttr(half_mdl + '.output', rot_attr, f=True)

    # 7) remapValue: 使用 Avg 的 inherit_axis 旋转作为输入
    # Use the same axis for remap input as the avg inherit axis
    rmp = cmds.createNode('remapValue', name='{}_r{}_to_{}_tz_rmp'.format(avg_name, axis, push_name))
    cmds.setAttr(rmp + '.inputMin', -90.0)
    cmds.setAttr(rmp + '.inputMax', 0.0)
    cmds.setAttr(rmp + '.outputMax', 0.0)
    cmds.setAttr(rmp + '.outputMin', float(remap_output_min))
    # Connect avg's rotation on the inherit axis (e.g., LeftElbowAvg.rotateX)
    cmds.connectAttr('{}.rotate{}'.format(avg_jnt, axis.upper()), rmp + '.inputValue', f=True)

    # 8) outValue 处理 -> Push.translateZ
    # Detect if this is a right side joint - need to invert translation for right side
    elbow_short_name = elbow_joint.split('|')[-1]
    is_right_side = 'Right' in elbow_short_name or elbow_short_name.startswith('JORight')

    # For right side, multiply by -1; for left side, keep as is (multiply by 1)
    multiplier = -1.0 if is_right_side else 1.0

    negate_mdl = cmds.createNode('multDoubleLinear', name='{}_tz_multiplier_mdl'.format(push_name))
    cmds.setAttr(negate_mdl + '.input2', multiplier)
    cmds.connectAttr(rmp + '.outValue', negate_mdl + '.input1', f=True)

    tz_attr = '{}.translateZ'.format(push_jnt)
    if cmds.getAttr(tz_attr, lock=True):
        cmds.setAttr(tz_attr, lock=False)
    cmds.connectAttr(negate_mdl + '.output', tz_attr, f=True)

    return {
        'resolved_elbow_joint': elbow_joint,
        'avg_joint': avg_jnt,
        'push_joint': push_jnt,
        'half_node': half_mdl,
        'remap_node': rmp,
        'negate_node': negate_mdl,
        'inherit_axis': axis,
        'remap_output_min': remap_output_min
    }


# setup_elbow_avg_push()  # Commented out - don't execute on module import

def createAvgPushJointForFinger(finger_joint, driver_joint=None, weight=0.5,
                                driver_axis='z', distance_axis='y', scale_axis='x',
                                driver_value=90, distance_value=5, scale_value=0.2,
                                create_push=True,
                                input_min=0.0, input_max=90.0,
                                output_min=0.0, output_max=5.0):
    """
    Create average and push joints for a finger joint, following the same pattern as setup_elbow_avg_push.

    Examples:
        JOLeftElbow1 -> LeftElbowAvg, LeftElbowPush
        JOLeftThumbMid1 -> LeftThumbMidAvg, LeftThumbMidPush
        JOLeftIndexBase1 -> LeftIndexBaseAvg, LeftIndexBasePush

    :param finger_joint: Target finger joint (e.g., JOLeftThumbMid1, JOLeftElbow1)
    :param driver_joint: Parent/driver joint (if None, uses parent of finger_joint)
    :param weight: Weight for average - how much rotation from target joint (0.5 = half)
    :param driver_axis: Rotation axis that drives the push (twist axis) ('x', 'y', or 'z')
    :param distance_axis: Axis along which joint pushes out (push axis) ('x', 'y', or 'z')
    :param scale_axis: Axis along which joint scales ('x', 'y', or 'z')
    :param driver_value: Maximum rotation value (in degrees) - deprecated, use input_max
    :param distance_value: Maximum push distance - deprecated, use output_max
    :param scale_value: Maximum scale value
    :param create_push: Whether to create push joint (default True)
    :param input_min: RemapValue input minimum (rotation in degrees)
    :param input_max: RemapValue input maximum (rotation in degrees)
    :param output_min: RemapValue output minimum (translation distance)
    :param output_max: RemapValue output maximum (translation distance)
    :return: Tuple of (avg_joint, push_joint) or (avg_joint, None) if create_push is False
    """
    # Resolve finger joint using the same logic as setup_elbow_avg_push
    finger_joint = _resolve_joint(finger_joint)

    # Get driver joint (parent of finger joint)
    if driver_joint is None:
        parent_joints = cmds.listRelatives(finger_joint, parent=True, type='joint', fullPath=True)
        if not parent_joints:
            raise RuntimeError(f'No parent joint found for: {finger_joint}')
        driver_joint = parent_joints[0]
    else:
        driver_joint = _resolve_joint(driver_joint)

    # Get the parent of the finger joint to parent the avg joint to
    finger_parent_list = cmds.listRelatives(finger_joint, parent=True, fullPath=True) or []
    if not finger_parent_list:
        raise RuntimeError(f"关节 {finger_joint} 没有父级，无法创建 Avg 关节。")
    finger_parent = finger_parent_list[0]

    # Generate names for avg and push joints following the naming convention
    # JOLeftElbow1 -> LeftElbowAvg, LeftElbowPush
    # JOLeftThumbMid1 -> LeftThumbMidAvg, LeftThumbMidPush
    finger_short_name = finger_joint.split('|')[-1]

    # Remove 'JO' prefix and trailing number to get base name
    if finger_short_name.startswith('JO'):
        base_name = finger_short_name[2:]  # Remove 'JO'
    else:
        base_name = finger_short_name

    # Remove trailing numbers (e.g., '1' from 'LeftElbow1')
    import re
    base_name = re.sub(r'\d+$', '', base_name)

    avg_name = f"{base_name}Avg"
    push_name = f"{base_name}Push"

    # Create/get Avg and Push joints (same as setup_elbow_avg_push)
    def ensure_joint(name):
        if cmds.objExists(name):
            return cmds.ls(name, long=True)[0]
        return cmds.createNode('joint', name=name)

    avg_jnt = ensure_joint(avg_name)

    # Parent avg joint to finger's parent
    try:
        cmds.parent(avg_jnt, finger_parent)
    except:
        pass

    # Match transform to finger joint
    m = cmds.xform(finger_joint, q=True, ws=True, m=True)
    for attr in ('t', 'r', 's'):
        for a in ('x', 'y', 'z'):
            at = f"{avg_jnt}.{attr}{a}"
            if cmds.getAttr(at, lock=True):
                cmds.setAttr(at, lock=False)
    cmds.xform(avg_jnt, ws=True, m=m)

    # Delete history & set radius
    try:
        cmds.delete(avg_jnt, ch=True)
    except:
        pass
    if cmds.attributeQuery('radius', n=avg_jnt, exists=True):
        cmds.setAttr(avg_jnt + '.radius', 0.5)

    # Copy jointOrient from target joint to maintain proper orientation
    for axis in ('X', 'Y', 'Z'):
        jo_attr = f'jointOrient{axis}'
        if cmds.attributeQuery(jo_attr, n=finger_joint, exists=True):
            jo_value = cmds.getAttr(f'{finger_joint}.{jo_attr}')
            if cmds.attributeQuery(jo_attr, n=avg_jnt, exists=True):
                if cmds.getAttr(f'{avg_jnt}.{jo_attr}', lock=True):
                    cmds.setAttr(f'{avg_jnt}.{jo_attr}', lock=False)
                cmds.setAttr(f'{avg_jnt}.{jo_attr}', jo_value)

    # Freeze Transform on avg joint - reset rotation values to 0 before connecting
    for axis_attr in ('rotateX', 'rotateY', 'rotateZ'):
        attr_path = f"{avg_jnt}.{axis_attr}"
        if cmds.getAttr(attr_path, lock=True):
            cmds.setAttr(attr_path, lock=False)
        cmds.setAttr(attr_path, 0)

    # Avg inherits weighted rotation from the target finger/elbow joint (NOT the driver/parent)
    # Using the same approach as setup_elbow_avg_push: multiply rotation by weight factor
    driver_axis_upper = driver_axis.upper()

    # Create multDoubleLinear node to apply weight to target joint's rotation
    # IMPORTANT: Connect from finger_joint (target), not driver_joint (parent)
    weight_mdl = cmds.createNode('multDoubleLinear', name=f'{avg_name}_weight_{driver_axis}_mdl')
    cmds.setAttr(weight_mdl + '.input2', weight)
    # Connect target joint's rotation (e.g., JOLeftElbow1.rotateX), not parent's rotation
    cmds.connectAttr(f'{finger_joint}.rotate{driver_axis_upper}', weight_mdl + '.input1', f=True)

    # Connect weighted rotation to avg joint
    rot_attr = f'{avg_jnt}.rotate{driver_axis_upper}'
    if cmds.getAttr(rot_attr, lock=True):
        cmds.setAttr(rot_attr, lock=False)
    cmds.connectAttr(weight_mdl + '.output', rot_attr, f=True)

    # Create push joint if requested
    push_jnt = None
    if create_push:
        push_jnt = ensure_joint(push_name)

        # Parent push to avg
        try:
            cmds.parent(push_jnt, avg_jnt)
        except:
            pass

        # Match transform to avg joint
        for attr in ('t', 'r', 's'):
            for a in ('x', 'y', 'z'):
                at = f"{push_jnt}.{attr}{a}"
                if cmds.getAttr(at, lock=True):
                    cmds.setAttr(at, lock=False)
        cmds.xform(push_jnt, ws=True, m=m)

        # Delete history & set radius
        try:
            cmds.delete(push_jnt, ch=True)
        except:
            pass
        if cmds.attributeQuery('radius', n=push_jnt, exists=True):
            cmds.setAttr(push_jnt + '.radius', 0.5)

        # Copy jointOrient from avg joint to maintain proper orientation
        for axis in ('X', 'Y', 'Z'):
            jo_attr = f'jointOrient{axis}'
            if cmds.attributeQuery(jo_attr, n=avg_jnt, exists=True):
                jo_value = cmds.getAttr(f'{avg_jnt}.{jo_attr}')
                if cmds.attributeQuery(jo_attr, n=push_jnt, exists=True):
                    if cmds.getAttr(f'{push_jnt}.{jo_attr}', lock=True):
                        cmds.setAttr(f'{push_jnt}.{jo_attr}', lock=False)
                    cmds.setAttr(f'{push_jnt}.{jo_attr}', jo_value)

        # Freeze Transform on push joint - reset translation and rotation to 0 before connecting
        for axis_attr in ('translateX', 'translateY', 'translateZ', 'rotateX', 'rotateY', 'rotateZ'):
            attr_path = f"{push_jnt}.{axis_attr}"
            if cmds.getAttr(attr_path, lock=True):
                cmds.setAttr(attr_path, lock=False)
            cmds.setAttr(attr_path, 0)

        # Setup remapValue node to drive push translation (same pattern as setup_elbow_avg_push)
        distance_axis_upper = distance_axis.upper()

        rmp = cmds.createNode('remapValue', name=f'{avg_name}_r{driver_axis}_to_{push_name}_t{distance_axis}_rmp')
        # Use the remap parameters from UI
        cmds.setAttr(rmp + '.inputMin', float(input_min))
        cmds.setAttr(rmp + '.inputMax', float(input_max))
        cmds.setAttr(rmp + '.outputMin', float(output_min))
        cmds.setAttr(rmp + '.outputMax', float(output_max))

        # Connect avg rotation to remap input
        cmds.connectAttr(f'{avg_jnt}.rotate{driver_axis_upper}', rmp + '.inputValue', f=True)

        # Detect if this is a right side joint - need to invert translation for right side
        finger_short_name = finger_joint.split('|')[-1]
        is_right_side = 'Right' in finger_short_name or finger_short_name.startswith('JORight')

        # Connect remap output to push translation
        translate_attr = f'{push_jnt}.translate{distance_axis_upper}'
        if cmds.getAttr(translate_attr, lock=True):
            cmds.setAttr(translate_attr, lock=False)

        if is_right_side:
            # For right side, multiply by -1 to invert the translation direction
            invert_mdl = cmds.createNode('multDoubleLinear', name=f'{push_name}_t{distance_axis}_invert_mdl')
            cmds.setAttr(invert_mdl + '.input2', -1.0)
            cmds.connectAttr(rmp + '.outValue', invert_mdl + '.input1', f=True)
            cmds.connectAttr(invert_mdl + '.output', translate_attr, f=True)
        else:
            # For left side, connect directly
            cmds.connectAttr(rmp + '.outValue', translate_attr, f=True)

    return avg_jnt, push_jnt


def batchCreateAllAvgPush(side='Both', fingers=None, weight=0.5,
                          driver_axis='z', distance_axis='y', scale_axis='x',
                          driver_value=90, distance_value=5, scale_value=0.2,
                          input_min=0.0, input_max=90.0,
                          output_min=0.0, output_max=5.0,
                          include_limbs=True):
    """
    Batch create average and push joints for all fingers, and optionally elbows and knees.

    :param side: 'Left' or 'Right' or 'Both'
    :param fingers: List of finger names, default: ['Thumb', 'Index', 'Middle', 'Ring', 'Pinky']
    :param weight: Weight for average constraint (0.0 to 1.0)
    :param driver_axis: Rotation axis that drives the push (default 'z')
    :param distance_axis: Axis along which joint pushes out (default 'y')
    :param scale_axis: Axis along which joint scales (default 'x')
    :param driver_value: Maximum rotation value (default 90 degrees)
    :param distance_value: Maximum push distance
    :param scale_value: Maximum scale value
    :param input_min: RemapValue input minimum
    :param input_max: RemapValue input maximum
    :param output_min: RemapValue output minimum
    :param output_max: RemapValue output maximum
    :param include_limbs: Whether to include elbows and knees (default True)
    :return: Dictionary of created joints with structure {joint_name: {'avg': avg_joint, 'push': push_joint}}
    """
    if fingers is None:
        fingers = ['Thumb', 'Index', 'Middle', 'Ring', 'Pinky']

    sides_to_process = []
    if side == 'Both':
        sides_to_process = ['Left', 'Right']
    else:
        sides_to_process = [side]

    created_joints = {}
    success_count = 0
    fail_count = 0

    for current_side in sides_to_process:
        # Process fingers - all three segments: Base, Mid, Tip
        digits = ['Base', 'Mid', 'Tip']
        for finger in fingers:
            for digit in digits:
                jnt = f'JO{current_side}{finger}{digit}1'
                if cmds.objExists(jnt):
                    try:
                        avg_jnt, push_jnt = createAvgPushJointForFinger(
                            jnt,
                            driver_joint=None,  # Will auto-detect parent
                            weight=weight,
                            driver_axis=driver_axis,
                            distance_axis=distance_axis,
                            scale_axis=scale_axis,
                            driver_value=driver_value,
                            distance_value=distance_value,
                            scale_value=scale_value,
                            create_push=True,
                            input_min=input_min,
                            input_max=input_max,
                            output_min=output_min,
                            output_max=output_max
                        )
                        created_joints[jnt] = {'avg': avg_jnt, 'push': push_jnt}
                        logger.info(f'Created avg/push for {jnt}')
                        success_count += 1
                    except Exception as e:
                        logger.warning(f'Failed to create avg/push for {jnt}: {e}')
                        fail_count += 1
                else:
                    logger.debug(f'Joint does not exist: {jnt}')

        # Process elbow and knee joints (only if include_limbs is True)
        if include_limbs:
            limb_joints = [f'JO{current_side}Elbow1', f'JO{current_side}Knee1']
            for jnt in limb_joints:
                if cmds.objExists(jnt):
                    try:
                        avg_jnt, push_jnt = createAvgPushJointForFinger(
                            jnt,
                            driver_joint=None,  # Will auto-detect parent
                            weight=weight,
                            driver_axis=driver_axis,
                            distance_axis=distance_axis,
                            scale_axis=scale_axis,
                            driver_value=driver_value,
                            distance_value=distance_value,
                            scale_value=scale_value,
                            create_push=True,
                            input_min=input_min,
                            input_max=input_max,
                            output_min=output_min,
                            output_max=output_max
                        )
                        created_joints[jnt] = {'avg': avg_jnt, 'push': push_jnt}
                        logger.info(f'Created avg/push for {jnt}')
                        success_count += 1
                    except Exception as e:
                        logger.warning(f'Failed to create avg/push for {jnt}: {e}')
                        fail_count += 1
                else:
                    logger.debug(f'Joint does not exist: {jnt}')

    logger.info(f'Batch complete: {success_count} succeeded, {fail_count} failed')
    return created_joints
