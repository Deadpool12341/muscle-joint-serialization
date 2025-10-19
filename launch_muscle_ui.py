"""
Muscle Rig UI Launcher for Maya 2023
====================================

Optimized launcher script for the muscle rig system UI in Maya 2023.
This version is specifically designed for Maya 2023's PySide2 environment.

Usage in Maya 2023:
    import sys
    sys.path.append(r"E:\python work\jointBasedMuscle_template")
    import launch_muscle_ui
    ui = launch_muscle_ui.launch()

Or copy and paste this script directly in Maya's Script Editor.
"""

import sys
import os
import importlib

def check_maya_version():
    """Check if running in Maya 2023"""
    try:
        import maya.cmds as cmds
        maya_version = cmds.about(version=True)
        print(f"Detected Maya version: {maya_version}")

        if "2023" not in maya_version:
            print("Warning: This UI is optimized for Maya 2023. Other versions may have compatibility issues.")

        return True
    except ImportError:
        print("Error: Maya not detected. This script should be run inside Maya.")
        return False

def check_pyside2():
    """Check if PySide2 is available"""
    try:
        import PySide2
        print(f"PySide2 version: {PySide2.__version__}")
        return True
    except ImportError:
        print("Error: PySide2 not found. Maya 2023 should have PySide2 built-in.")
        return False

def reload_modules():
    """Reload all muscle system modules for development"""
    modules_to_reload = [
        'jointBasedMuscle_template.config',
        'jointBasedMuscle_template.utils',
        'jointBasedMuscle_template.helper_bone',
        'jointBasedMuscle_template.avg_push_joint',
        'jointBasedMuscle_template.rollBone.rollBone',
        'jointBasedMuscle_template.muscle_bone',
        'jointBasedMuscle_template.muscle_template',
        'jointBasedMuscle_template.muscle_ui'
    ]

    reloaded = []
    for module_name in modules_to_reload:
        try:
            if module_name in sys.modules:
                importlib.reload(sys.modules[module_name])
                reloaded.append(module_name)
                print(f"  - Reloaded: {module_name}")
        except Exception as e:
            print(f"Warning: Could not reload {module_name}: {e}")

    if reloaded:
        print(f"✓ Successfully reloaded {len(reloaded)} modules")

    return reloaded

def launch(reload=False):
    """Launch the muscle rig UI for Maya 2023"""
    try:
        # Check environment
        if not check_maya_version():
            return None

        if not check_pyside2():
            return None

        # Add current directory to path if not already there
        current_dir = os.path.dirname(__file__)
        if current_dir not in sys.path:
            sys.path.append(current_dir)
            print(f"Added to Python path: {current_dir}")

        # Reload modules if requested (useful for development)
        if reload:
            reload_modules()

        # Import and show UI
        from muscle_ui import show_muscle_ui
        ui = show_muscle_ui()

        if ui:
            print("🎉 Muscle Rig UI launched successfully in Maya 2023!")
            print("Ready to create muscle rigs!")
        else:
            print("❌ Failed to launch UI.")

        return ui

    except ImportError as e:
        print(f"Import Error: {e}")
        print("Troubleshooting:")
        print("1. Make sure you're running this in Maya 2023")
        print("2. Check that all muscle system files are in the same directory")
        print("3. Verify PySide2 is available in Maya")
        return None

    except Exception as e:
        print(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return None

def launch_simple(reload=False):
    """Simple launcher without extensive checks (for advanced users)"""
    try:
        current_dir = os.path.dirname(__file__)
        if current_dir not in sys.path:
            sys.path.append(current_dir)

        if reload:
            reload_modules()

        from muscle_ui import show_muscle_ui
        return show_muscle_ui()
    except Exception as e:
        print(f"Launch failed: {e}")
        return None

def launch_with_reload():
    """Launch with automatic module reloading (for development)"""
    return launch(reload=True)

# Quick access functions for Maya Script Editor
def quick_launch():
    """One-line launcher for copy-paste into Script Editor"""
    return launch()

if __name__ == "__main__":
    # If running directly in Maya Script Editor
    launch()