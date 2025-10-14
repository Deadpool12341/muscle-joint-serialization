import sys
import maya.cmds as mc
import logging

# Maya 2023 uses PySide2
try:
    from PySide2.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                                   QHBoxLayout, QGridLayout, QPushButton, QLabel,
                                   QComboBox, QGroupBox, QCheckBox, QSpinBox,
                                   QDoubleSpinBox, QMessageBox, QScrollArea)
    from PySide2.QtCore import Qt, Signal
    from PySide2.QtGui import QIcon, QPixmap, QFont
    PYSIDE2_AVAILABLE = True
except ImportError:
    PYSIDE2_AVAILABLE = False
    raise ImportError("PySide2 not found. Maya 2023 requires PySide2 to be available.")

import muscle_template as mt
import maya.api.OpenMaya as om

logger = logging.getLogger(__name__)


class MuscleRigUI(QMainWindow):
    """
    A comprehensive UI for creating and managing the joint-based muscle rig system.
    Provides buttons for each muscle group with automatic creation functionality.
    """

    def __init__(self, parent=None):
        super(MuscleRigUI, self).__init__(parent)
        self.setWindowTitle("Muscle Rig System - Maya 2023")
        self.setMinimumSize(400, 600)
        self.resize(500, 700)

        # Maya 2023 specific window settings
        self.setWindowFlags(Qt.Window | Qt.WindowCloseButtonHint | Qt.WindowMinimizeButtonHint)
        self.setAttribute(Qt.WA_DeleteOnClose, True)

        # Store created muscle instances
        self.created_muscles = {}

        # Apply Maya-style theme
        self.apply_maya_styling()

        # Setup UI
        self.setup_ui()
        self.connect_signals()

    def apply_maya_styling(self):
        """Apply Maya 2023 compatible styling"""
        maya_style = """
            QMainWindow {
                background-color: #393939;
                color: #CCCCCC;
            }
            QGroupBox {
                font-weight: bold;
                border: 1px solid #555555;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 5px;
                background-color: #424242;
                color: #FFFFFF;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QLabel {
                color: #CCCCCC;
            }
            QComboBox {
                background-color: #555555;
                border: 1px solid #777777;
                border-radius: 3px;
                padding: 2px;
                color: #FFFFFF;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 15px;
                border-left-width: 1px;
                border-left-color: #777777;
                border-left-style: solid;
            }
            QCheckBox {
                color: #CCCCCC;
            }
            QSpinBox, QDoubleSpinBox {
                background-color: #555555;
                border: 1px solid #777777;
                border-radius: 3px;
                padding: 2px;
                color: #FFFFFF;
            }
        """
        self.setStyleSheet(maya_style)

    def setup_ui(self):
        """Setup the main UI layout and widgets"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # Title
        title_label = QLabel("Joint-Based Muscle Rig System")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; padding: 10px;")
        main_layout.addWidget(title_label)

        # Options section
        self.setup_options_section(main_layout)

        # Scroll area for muscle buttons
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)

        # Muscle groups
        self.setup_muscle_groups(scroll_layout)

        scroll_area.setWidget(scroll_widget)
        main_layout.addWidget(scroll_area)

        # Control buttons
        self.setup_control_buttons(main_layout)

    def setup_options_section(self, parent_layout):
        """Setup the options and settings section"""
        options_group = QGroupBox("Options")
        options_layout = QGridLayout(options_group)

        # Side selection
        options_layout.addWidget(QLabel("Side:"), 0, 0)
        self.side_combo = QComboBox()
        self.side_combo.addItems(["Left", "Right", "Both"])
        self.side_combo.setCurrentText("Left")
        options_layout.addWidget(self.side_combo, 0, 1)

        # Auto mirror option
        self.auto_mirror_check = QCheckBox("Auto Mirror")
        self.auto_mirror_check.setChecked(True)
        options_layout.addWidget(self.auto_mirror_check, 0, 2)

        # Compression factor
        options_layout.addWidget(QLabel("Compression:"), 1, 0)
        self.compression_spin = QDoubleSpinBox()
        self.compression_spin.setRange(0.1, 2.0)
        self.compression_spin.setValue(0.5)
        self.compression_spin.setSingleStep(0.1)
        options_layout.addWidget(self.compression_spin, 1, 1)

        # Stretch factor
        options_layout.addWidget(QLabel("Stretch:"), 1, 2)
        self.stretch_spin = QDoubleSpinBox()
        self.stretch_spin.setRange(0.1, 3.0)
        self.stretch_spin.setValue(1.5)
        self.stretch_spin.setSingleStep(0.1)
        options_layout.addWidget(self.stretch_spin, 1, 3)

        parent_layout.addWidget(options_group)

    def setup_muscle_groups(self, parent_layout):
        """Setup muscle group buttons organized by body region"""

        # Torso muscles
        torso_group = QGroupBox("Torso Muscles")
        torso_layout = QGridLayout(torso_group)

        self.trapezius_btn = QPushButton("Trapezius")
        self.trapezius_btn.setMinimumHeight(40)
        self.trapezius_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; font-weight: bold; }")
        torso_layout.addWidget(self.trapezius_btn, 0, 0)

        self.latissimus_btn = QPushButton("Latissimus Dorsi")
        self.latissimus_btn.setMinimumHeight(40)
        self.latissimus_btn.setStyleSheet("QPushButton { background-color: #2196F3; color: white; font-weight: bold; }")
        torso_layout.addWidget(self.latissimus_btn, 0, 1)

        self.teres_major_btn = QPushButton("Teres Major")
        self.teres_major_btn.setMinimumHeight(40)
        self.teres_major_btn.setStyleSheet("QPushButton { background-color: #FF9800; color: white; font-weight: bold; }")
        torso_layout.addWidget(self.teres_major_btn, 1, 0)

        self.pectoralis_btn = QPushButton("Pectoralis Major")
        self.pectoralis_btn.setMinimumHeight(40)
        self.pectoralis_btn.setStyleSheet("QPushButton { background-color: #9C27B0; color: white; font-weight: bold; }")
        torso_layout.addWidget(self.pectoralis_btn, 1, 1)

        parent_layout.addWidget(torso_group)

        # Shoulder muscles
        shoulder_group = QGroupBox("Shoulder Muscles")
        shoulder_layout = QGridLayout(shoulder_group)

        self.deltoid_btn = QPushButton("Deltoid")
        self.deltoid_btn.setMinimumHeight(40)
        self.deltoid_btn.setStyleSheet("QPushButton { background-color: #F44336; color: white; font-weight: bold; }")
        shoulder_layout.addWidget(self.deltoid_btn, 0, 0)

        parent_layout.addWidget(shoulder_group)

        # Arm muscles
        arm_group = QGroupBox("Arm Muscles")
        arm_layout = QGridLayout(arm_group)

        self.upper_arm_btn = QPushButton("Upper Arm (Bicep/Tricep)")
        self.upper_arm_btn.setMinimumHeight(40)
        self.upper_arm_btn.setStyleSheet("QPushButton { background-color: #607D8B; color: white; font-weight: bold; }")
        arm_layout.addWidget(self.upper_arm_btn, 0, 0)

        parent_layout.addWidget(arm_group)

        # Combined options
        combined_group = QGroupBox("Batch Creation")
        combined_layout = QGridLayout(combined_group)

        self.create_all_btn = QPushButton("Create All Muscles")
        self.create_all_btn.setMinimumHeight(50)
        self.create_all_btn.setStyleSheet("QPushButton { background-color: #795548; color: white; font-weight: bold; font-size: 14px; }")
        combined_layout.addWidget(self.create_all_btn, 0, 0, 1, 2)

        self.create_torso_btn = QPushButton("Create Torso Only")
        self.create_torso_btn.setMinimumHeight(40)
        combined_layout.addWidget(self.create_torso_btn, 1, 0)

        self.create_arms_btn = QPushButton("Create Arms Only")
        self.create_arms_btn.setMinimumHeight(40)
        combined_layout.addWidget(self.create_arms_btn, 1, 1)

        parent_layout.addWidget(combined_group)

    def setup_control_buttons(self, parent_layout):
        """Setup control buttons for managing created muscles"""
        control_group = QGroupBox("Control")
        control_layout = QHBoxLayout(control_group)

        self.finalize_btn = QPushButton("Finalize All")
        self.finalize_btn.setMinimumHeight(35)
        self.finalize_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; }")
        control_layout.addWidget(self.finalize_btn)

        self.delete_all_btn = QPushButton("Delete All")
        self.delete_all_btn.setMinimumHeight(35)
        self.delete_all_btn.setStyleSheet("QPushButton { background-color: #F44336; color: white; }")
        control_layout.addWidget(self.delete_all_btn)

        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.setMinimumHeight(35)
        control_layout.addWidget(self.refresh_btn)

        parent_layout.addWidget(control_group)

    def connect_signals(self):
        """Connect button signals to their respective slots"""
        # Individual muscle buttons
        self.trapezius_btn.clicked.connect(lambda: self.create_muscle("Trapezius"))
        self.latissimus_btn.clicked.connect(lambda: self.create_muscle("LatissimusDorsi"))
        self.teres_major_btn.clicked.connect(lambda: self.create_muscle("TerasMajor"))
        self.pectoralis_btn.clicked.connect(lambda: self.create_muscle("PectoralisMajor"))
        self.deltoid_btn.clicked.connect(lambda: self.create_muscle("Deltoid"))
        self.upper_arm_btn.clicked.connect(lambda: self.create_muscle("UpperArm"))

        # Batch creation buttons
        self.create_all_btn.clicked.connect(self.create_all_muscles)
        self.create_torso_btn.clicked.connect(self.create_torso_muscles)
        self.create_arms_btn.clicked.connect(self.create_arm_muscles)

        # Control buttons
        self.finalize_btn.clicked.connect(self.finalize_all_muscles)
        self.delete_all_btn.clicked.connect(self.delete_all_muscles)
        self.refresh_btn.clicked.connect(self.refresh_ui)

    def get_muscle_class(self, muscle_type):
        """Get the appropriate muscle class"""
        muscle_classes = {
            "Trapezius": mt.TrapeziusMuscles,
            "LatissimusDorsi": mt.LatissimusDorsiMuscles,
            "TerasMajor": mt.TerasMajorMuscles,
            "PectoralisMajor": mt.PectoralisMajorMuscles,
            "Deltoid": mt.DeltoidMuscles,
            "UpperArm": mt.UpperArmMuscles
        }
        return muscle_classes.get(muscle_type)

    def create_muscle(self, muscle_type):
        """Create a specific muscle type"""
        try:
            muscle_class = self.get_muscle_class(muscle_type)
            if not muscle_class:
                self.show_error(f"Unknown muscle type: {muscle_type}")
                return

            side = self.side_combo.currentText()
            auto_mirror = self.auto_mirror_check.isChecked()

            sides_to_create = []
            if side == "Both":
                sides_to_create = ["Left", "Right"]
            else:
                sides_to_create = [side]
                if auto_mirror and side in ["Left", "Right"]:
                    other_side = "Right" if side == "Left" else "Left"
                    sides_to_create.append(other_side)

            created_muscles = []
            for current_side in sides_to_create:
                try:
                    # Create muscle instance
                    muscle_name = f"{current_side}{muscle_type}"

                    # Check if muscle already exists
                    if muscle_name in self.created_muscles:
                        reply = QMessageBox.question(
                            self, "Muscle Exists",
                            f"{muscle_name} already exists. Replace it?",
                            QMessageBox.Yes | QMessageBox.No,
                            QMessageBox.No
                        )
                        if reply == QMessageBox.No:
                            continue
                        else:
                            # Delete existing muscle
                            self.created_muscles[muscle_name].delete()
                            del self.created_muscles[muscle_name]

                    # Create new muscle
                    if current_side == sides_to_create[0]:
                        # Create primary muscle
                        muscle = muscle_class(side=current_side)
                        muscle.add()
                        created_muscles.append(muscle)
                        self.created_muscles[muscle_name] = muscle
                        logger.info(f"Created {muscle_name}")

                    else:
                        # Mirror from first created muscle
                        if created_muscles:
                            primary_muscle = created_muscles[0]
                            mirrored_muscle = primary_muscle.mirror()
                            created_muscles.append(mirrored_muscle)
                            self.created_muscles[muscle_name] = mirrored_muscle
                            logger.info(f"Mirrored {muscle_name}")

                except Exception as e:
                    self.show_error(f"Failed to create {current_side} {muscle_type}: {str(e)}")
                    logger.error(f"Error creating {current_side} {muscle_type}: {e}")

            if created_muscles:
                self.show_success(f"Successfully created {muscle_type} muscle(s)")

        except Exception as e:
            self.show_error(f"Error creating {muscle_type}: {str(e)}")
            logger.error(f"Error in create_muscle: {e}")

    def create_all_muscles(self):
        """Create all available muscle types"""
        muscle_types = ["Trapezius", "LatissimusDorsi", "TerasMajor", "PectoralisMajor", "Deltoid", "UpperArm"]

        failed_muscles = []
        for muscle_type in muscle_types:
            try:
                self.create_muscle(muscle_type)
            except Exception as e:
                failed_muscles.append(muscle_type)
                logger.error(f"Failed to create {muscle_type}: {e}")

        if failed_muscles:
            self.show_error(f"Failed to create: {', '.join(failed_muscles)}")
        else:
            self.show_success("Successfully created all muscles!")

    def create_torso_muscles(self):
        """Create only torso muscles"""
        torso_muscles = ["Trapezius", "LatissimusDorsi", "TerasMajor", "PectoralisMajor"]

        for muscle_type in torso_muscles:
            try:
                self.create_muscle(muscle_type)
            except Exception as e:
                logger.error(f"Failed to create {muscle_type}: {e}")

        self.show_success("Torso muscles created!")

    def create_arm_muscles(self):
        """Create only arm and shoulder muscles"""
        arm_muscles = ["Deltoid", "UpperArm"]

        for muscle_type in arm_muscles:
            try:
                self.create_muscle(muscle_type)
            except Exception as e:
                logger.error(f"Failed to create {muscle_type}: {e}")

        self.show_success("Arm muscles created!")

    def finalize_all_muscles(self):
        """Finalize all created muscles"""
        if not self.created_muscles:
            self.show_error("No muscles to finalize!")
            return

        try:
            for muscle_name, muscle in self.created_muscles.items():
                muscle.finalize()
                logger.info(f"Finalized {muscle_name}")

            self.show_success("All muscles finalized!")

        except Exception as e:
            self.show_error(f"Error finalizing muscles: {str(e)}")
            logger.error(f"Error in finalize_all_muscles: {e}")

    def delete_all_muscles(self):
        """Delete all created muscles"""
        if not self.created_muscles:
            self.show_error("No muscles to delete!")
            return

        reply = QMessageBox.question(
            self, "Confirm Delete",
            "Are you sure you want to delete all muscles?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                for muscle_name, muscle in self.created_muscles.items():
                    muscle.delete()
                    logger.info(f"Deleted {muscle_name}")

                self.created_muscles.clear()
                self.show_success("All muscles deleted!")

            except Exception as e:
                self.show_error(f"Error deleting muscles: {str(e)}")
                logger.error(f"Error in delete_all_muscles: {e}")

    def refresh_ui(self):
        """Refresh the UI state"""
        # Clear non-existent muscles from tracking
        muscles_to_remove = []
        for muscle_name, muscle in self.created_muscles.items():
            try:
                # Check if muscle still exists in scene
                if not mc.objExists(muscle.muscleOrigin):
                    muscles_to_remove.append(muscle_name)
            except:
                muscles_to_remove.append(muscle_name)

        for muscle_name in muscles_to_remove:
            del self.created_muscles[muscle_name]

        self.show_success(f"UI refreshed. Tracking {len(self.created_muscles)} muscles.")

    def show_success(self, message):
        """Show success message"""
        QMessageBox.information(self, "Success", message)

    def show_error(self, message):
        """Show error message"""
        QMessageBox.critical(self, "Error", message)
        logger.error(message)


def show_muscle_ui():
    """Show the muscle rig UI optimized for Maya 2023"""
    try:
        # Maya 2023 specific imports
        import maya.OpenMayaUI as omui
        from shiboken2 import wrapInstance

        # Get Maya's main window
        maya_main_window_ptr = omui.MQtUtil.mainWindow()
        maya_main_window = wrapInstance(int(maya_main_window_ptr), QWidget)

        # Create and show UI
        ui = MuscleRigUI(parent=maya_main_window)
        ui.setWindowFlags(ui.windowFlags() | Qt.Window)  # Ensure it's treated as a window
        ui.show()
        ui.raise_()  # Bring to front
        ui.activateWindow()  # Activate the window

        return ui

    except ImportError as e:
        print(f"Error: This UI is designed for Maya 2023 with PySide2. {e}")
        return None
    except Exception as e:
        print(f"Error launching UI: {e}")
        return None

def test():
    print("import successfully")


if __name__ == "__main__":
    show_muscle_ui()