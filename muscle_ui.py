import sys
import maya.cmds as cmds
import logging

# Maya 2023 uses PySide2
try:
    from PySide2.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                                   QHBoxLayout, QGridLayout, QPushButton, QLabel,
                                   QComboBox, QGroupBox, QCheckBox, QSpinBox,
                                   QDoubleSpinBox, QMessageBox, QScrollArea, QFileDialog)
    from PySide2.QtCore import Qt, Signal
    from PySide2.QtGui import QIcon, QPixmap, QFont
    PYSIDE2_AVAILABLE = True
except ImportError:
    PYSIDE2_AVAILABLE = False
    raise ImportError("PySide2 not found. Maya 2023 requires PySide2 to be available.")

from . import muscle_template as mt
from . import utils
from . import helper_bone
from . import avg_push_joint
from .rollBone import rollBone
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

        # Twist Axis selection
        options_layout.addWidget(QLabel("Twist Axis:"), 2, 0)
        self.twist_axis_combo = QComboBox()
        self.twist_axis_combo.addItems(["X (1,0,0)", "Y (0,1,0)", "Z (0,0,1)", "-X (-1,0,0)", "-Y (0,-1,0)", "-Z (0,0,-1)"])
        self.twist_axis_combo.setCurrentText("Y (0,1,0)")
        options_layout.addWidget(self.twist_axis_combo, 2, 1)

        # Up Axis selection
        options_layout.addWidget(QLabel("Up Axis:"), 2, 2)
        self.up_axis_combo = QComboBox()
        self.up_axis_combo.addItems(["X (1,0,0)", "Y (0,1,0)", "Z (0,0,1)", "-X (-1,0,0)", "-Y (0,-1,0)", "-Z (0,0,-1)"])
        self.up_axis_combo.setCurrentText("X (1,0,0)")
        options_layout.addWidget(self.up_axis_combo, 2, 3)

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

        # Helper Bones section
        helper_group = QGroupBox("Helper Bones")
        helper_layout = QGridLayout(helper_group)

        self.scapula_btn = QPushButton("Add Scapula Joints")
        self.scapula_btn.setMinimumHeight(40)
        self.scapula_btn.setStyleSheet("QPushButton { background-color: #00BCD4; color: white; font-weight: bold; }")
        helper_layout.addWidget(self.scapula_btn, 0, 0)

        self.mirror_scapula_btn = QPushButton("Mirror Scapula Joints")
        self.mirror_scapula_btn.setMinimumHeight(40)
        self.mirror_scapula_btn.setStyleSheet("QPushButton { background-color: #009688; color: white; font-weight: bold; }")
        helper_layout.addWidget(self.mirror_scapula_btn, 0, 1)

        parent_layout.addWidget(helper_group)

        # Twist Joint section
        twist_group = QGroupBox("Twist Joints")
        twist_layout = QGridLayout(twist_group)

        self.twist_joint_btn = QPushButton("Setup Twist Joint Chain")
        self.twist_joint_btn.setMinimumHeight(40)
        self.twist_joint_btn.setStyleSheet("QPushButton { background-color: #3F51B5; color: white; font-weight: bold; }")
        twist_layout.addWidget(self.twist_joint_btn, 0, 0)

        self.counter_twist_btn = QPushButton("Setup Counter Twist Chain")
        self.counter_twist_btn.setMinimumHeight(40)
        self.counter_twist_btn.setStyleSheet("QPushButton { background-color: #673AB7; color: white; font-weight: bold; }")
        twist_layout.addWidget(self.counter_twist_btn, 0, 1)

        self.non_flip_twist_btn = QPushButton("Setup Non-Flip Twist Chain")
        self.non_flip_twist_btn.setMinimumHeight(40)
        self.non_flip_twist_btn.setStyleSheet("QPushButton { background-color: #9C27B0; color: white; font-weight: bold; }")
        twist_layout.addWidget(self.non_flip_twist_btn, 1, 0, 1, 2)

        # Twist joint count control
        twist_layout.addWidget(QLabel("Twist Joint Count:"), 2, 0)
        self.twist_count_spin = QSpinBox()
        self.twist_count_spin.setRange(1, 10)
        self.twist_count_spin.setValue(3)
        twist_layout.addWidget(self.twist_count_spin, 2, 1)

        parent_layout.addWidget(twist_group)

        # Average & Push Joints section
        avg_push_group = QGroupBox("Average & Push Joints")
        avg_push_layout = QGridLayout(avg_push_group)

        # Buttons spanning full width
        self.create_avg_push_btn = QPushButton("Create Average and Push Joints")
        self.create_avg_push_btn.setMinimumHeight(45)
        self.create_avg_push_btn.setStyleSheet("QPushButton { background-color: #FF5722; color: white; font-weight: bold; }")
        avg_push_layout.addWidget(self.create_avg_push_btn, 0, 0, 1, 4)

        self.batch_all_avg_push_btn = QPushButton("Fingers Average and Push Joints")
        self.batch_all_avg_push_btn.setMinimumHeight(45)
        self.batch_all_avg_push_btn.setStyleSheet("QPushButton { background-color: #E91E63; color: white; font-weight: bold; }")
        avg_push_layout.addWidget(self.batch_all_avg_push_btn, 1, 0, 1, 4)

        # Two-column layout for parameters
        # Left column - Basic parameters
        row = 2
        avg_push_layout.addWidget(QLabel("Avg Weight:"), row, 0)
        self.avg_weight_spin = QDoubleSpinBox()
        self.avg_weight_spin.setRange(0.0, 1.0)
        self.avg_weight_spin.setValue(0.5)
        self.avg_weight_spin.setSingleStep(0.1)
        avg_push_layout.addWidget(self.avg_weight_spin, row, 1)

        # Right column - Twist Axis
        avg_push_layout.addWidget(QLabel("Twist Axis:"), row, 2)
        self.avg_twist_axis_combo = QComboBox()
        self.avg_twist_axis_combo.addItems(["X", "Y", "Z"])
        self.avg_twist_axis_combo.setCurrentText("Z")
        avg_push_layout.addWidget(self.avg_twist_axis_combo, row, 3)

        # Left column - Push Axis
        row += 1
        avg_push_layout.addWidget(QLabel("Push Axis:"), row, 0)
        self.avg_push_axis_combo = QComboBox()
        self.avg_push_axis_combo.addItems(["X", "Y", "Z"])
        self.avg_push_axis_combo.setCurrentText("Y")
        avg_push_layout.addWidget(self.avg_push_axis_combo, row, 1)

        # Right column - Scale Value
        avg_push_layout.addWidget(QLabel("Scale Value:"), row, 2)
        self.push_scale_value_spin = QDoubleSpinBox()
        self.push_scale_value_spin.setRange(0, 2)
        self.push_scale_value_spin.setValue(0.2)
        self.push_scale_value_spin.setSingleStep(0.1)
        avg_push_layout.addWidget(self.push_scale_value_spin, row, 3)

        # RemapValue parameters section
        row += 1
        remap_label = QLabel("Remap Value Settings")
        remap_label.setStyleSheet("font-weight: bold; color: #FFD700; margin-top: 5px;")
        avg_push_layout.addWidget(remap_label, row, 0, 1, 4)

        # Left column - Input Min
        row += 1
        avg_push_layout.addWidget(QLabel("Input Min:"), row, 0)
        self.remap_input_min_spin = QDoubleSpinBox()
        self.remap_input_min_spin.setRange(-360, 360)
        self.remap_input_min_spin.setValue(0.0)
        self.remap_input_min_spin.setSingleStep(1.0)
        avg_push_layout.addWidget(self.remap_input_min_spin, row, 1)

        # Right column - Input Max
        avg_push_layout.addWidget(QLabel("Input Max:"), row, 2)
        self.remap_input_max_spin = QDoubleSpinBox()
        self.remap_input_max_spin.setRange(-360, 360)
        self.remap_input_max_spin.setValue(90.0)
        self.remap_input_max_spin.setSingleStep(1.0)
        avg_push_layout.addWidget(self.remap_input_max_spin, row, 3)

        # Left column - Output Min
        row += 1
        avg_push_layout.addWidget(QLabel("Output Min:"), row, 0)
        self.remap_output_min_spin = QDoubleSpinBox()
        self.remap_output_min_spin.setRange(-100, 100)
        self.remap_output_min_spin.setValue(0.0)
        self.remap_output_min_spin.setSingleStep(0.1)
        avg_push_layout.addWidget(self.remap_output_min_spin, row, 1)

        # Right column - Output Max
        avg_push_layout.addWidget(QLabel("Output Max:"), row, 2)
        self.remap_output_max_spin = QDoubleSpinBox()
        self.remap_output_max_spin.setRange(-100, 100)
        self.remap_output_max_spin.setValue(5.0)
        self.remap_output_max_spin.setSingleStep(0.1)
        avg_push_layout.addWidget(self.remap_output_max_spin, row, 3)

        parent_layout.addWidget(avg_push_group)

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

        # Import/Export section
        io_group = QGroupBox("Import/Export")
        io_layout = QHBoxLayout(io_group)

        self.export_btn = QPushButton("Export to JSON")
        self.export_btn.setMinimumHeight(35)
        self.export_btn.setStyleSheet("QPushButton { background-color: #FF9800; color: white; }")
        io_layout.addWidget(self.export_btn)

        self.import_btn = QPushButton("Import from JSON")
        self.import_btn.setMinimumHeight(35)
        self.import_btn.setStyleSheet("QPushButton { background-color: #2196F3; color: white; }")
        io_layout.addWidget(self.import_btn)

        parent_layout.addWidget(io_group)

    def connect_signals(self):
        """Connect button signals to their respective slots"""
        # Individual muscle buttons
        self.trapezius_btn.clicked.connect(lambda: self.create_muscle("Trapezius"))
        self.latissimus_btn.clicked.connect(lambda: self.create_muscle("LatissimusDorsi"))
        self.teres_major_btn.clicked.connect(lambda: self.create_muscle("TerasMajor"))
        self.pectoralis_btn.clicked.connect(lambda: self.create_muscle("PectoralisMajor"))
        self.deltoid_btn.clicked.connect(lambda: self.create_muscle("Deltoid"))
        self.upper_arm_btn.clicked.connect(lambda: self.create_muscle("UpperArm"))

        # Helper bone buttons
        self.scapula_btn.clicked.connect(self.add_scapula_joints)
        self.mirror_scapula_btn.clicked.connect(self.mirror_scapula_joints)

        # Twist joint buttons
        self.twist_joint_btn.clicked.connect(self.setup_twist_joint_chain)
        self.counter_twist_btn.clicked.connect(self.setup_counter_twist_chain)
        self.non_flip_twist_btn.clicked.connect(self.setup_non_flip_twist)

        # Average & Push joint buttons
        self.create_avg_push_btn.clicked.connect(self.create_avg_push_from_selection)
        self.batch_all_avg_push_btn.clicked.connect(self.batch_create_all_avg_push)

        # Batch creation buttons
        self.create_all_btn.clicked.connect(self.create_all_muscles)
        self.create_torso_btn.clicked.connect(self.create_torso_muscles)
        self.create_arms_btn.clicked.connect(self.create_arm_muscles)

        # Control buttons
        self.finalize_btn.clicked.connect(self.finalize_all_muscles)
        self.delete_all_btn.clicked.connect(self.delete_all_muscles)
        self.refresh_btn.clicked.connect(self.refresh_ui)

        # Import/Export buttons
        self.export_btn.clicked.connect(self.export_muscles)
        self.import_btn.clicked.connect(self.import_muscles)

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
                if not cmds.objExists(muscle.muscleOrigin):
                    muscles_to_remove.append(muscle_name)
            except:
                muscles_to_remove.append(muscle_name)

        for muscle_name in muscles_to_remove:
            del self.created_muscles[muscle_name]

        self.show_success(f"UI refreshed. Tracking {len(self.created_muscles)} muscles.")

    def export_muscles(self):
        """Export current muscles to JSON file"""
        try:
            # Open file dialog to select save location
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Export Muscles to JSON",
                "",
                "JSON Files (*.json);;All Files (*)"
            )

            if not file_path:
                return

            # Ensure .json extension
            if not file_path.endswith('.json'):
                file_path += '.json'

            # Use utils export function
            utils.exportMuscles(file_path)
            self.show_success(f"Muscles exported successfully to:\n{file_path}")
            logger.info(f"Exported muscles to {file_path}")

        except Exception as e:
            self.show_error(f"Error exporting muscles: {str(e)}")
            logger.error(f"Error in export_muscles: {e}")

    def import_muscles(self):
        """Import muscles from JSON file"""
        try:
            # Open file dialog to select JSON file
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "Import Muscles from JSON",
                "",
                "JSON Files (*.json);;All Files (*)"
            )

            if not file_path:
                return

            # Confirm import
            reply = QMessageBox.question(
                self, "Confirm Import",
                "This will create muscles based on the JSON file. Continue?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )

            if reply == QMessageBox.No:
                return

            # Use utils generate function
            utils.generateMusclesFromFile(file_path)
            self.show_success(f"Muscles imported successfully from:\n{file_path}")
            logger.info(f"Imported muscles from {file_path}")

            # Refresh UI to track imported muscles
            self.refresh_ui()

        except Exception as e:
            self.show_error(f"Error importing muscles: {str(e)}")
            logger.error(f"Error in import_muscles: {e}")

    def create_avg_push_from_selection(self):
        """Create both average and push joints from selected joint(s)"""
        try:
            # Get current selection
            selection = cmds.ls(selection=True, type='joint')

            # Validate selection - now we only need 1 joint (target), driver will be auto-detected
            if len(selection) == 0:
                self.show_error("Please select at least 1 joint (target joint).\nDriver joint will be auto-detected as parent.")
                return
            elif len(selection) > 2:
                self.show_error("Please select 1 or 2 joints:\n1. Target joint (required)\n2. Driver joint (optional, will use parent if not specified)")
                return

            target_joint = selection[0]
            driver_joint = selection[1] if len(selection) == 2 else None

            # Get parameters from UI
            weight = self.avg_weight_spin.value()
            twist_axis = self.avg_twist_axis_combo.currentText().lower()
            push_axis = self.avg_push_axis_combo.currentText().lower()
            scale_value = self.push_scale_value_spin.value()

            # Remap value parameters
            input_min = self.remap_input_min_spin.value()
            input_max = self.remap_input_max_spin.value()
            output_min = self.remap_output_min_spin.value()
            output_max = self.remap_output_max_spin.value()

            # Create average and push joints using the rewritten function
            avg_jnt, push_jnt = avg_push_joint.createAvgPushJointForFinger(
                finger_joint=target_joint,
                driver_joint=driver_joint,
                weight=weight,
                driver_axis=twist_axis,
                distance_axis=push_axis,
                scale_axis='x',
                driver_value=input_max,  # Use input_max as the driver value
                distance_value=output_max,  # Use output_max as the distance value
                scale_value=scale_value,
                create_push=True,
                input_min=input_min,
                input_max=input_max,
                output_min=output_min,
                output_max=output_max
            )

            driver_info = driver_joint if driver_joint else "auto-detected parent"
            self.show_success(f"Successfully created avg + push joints:\n" +
                            f"Target: {target_joint}\n" +
                            f"Driver: {driver_info}\n" +
                            f"Average: {avg_jnt}\n" +
                            f"Push: {push_jnt}\n" +
                            f"{twist_axis.upper()} rotation → {push_axis.upper()} push\n" +
                            f"Remap: [{input_min}, {input_max}] → [{output_min}, {output_max}]")
            logger.info(f"Created avg + push: {avg_jnt}, {push_jnt}")

        except Exception as e:
            self.show_error(f"Error creating avg + push joints:\n{str(e)}")
            logger.error(f"Error in create_avg_push_from_selection: {e}")

    def batch_create_all_avg_push(self):
        """Batch create average and push joints for fingers, elbows, and knees"""
        try:
            # Always process both sides for batch operation
            side = 'Both'

            # Get parameters from UI
            weight = self.avg_weight_spin.value()
            twist_axis = self.avg_twist_axis_combo.currentText().lower()
            push_axis = self.avg_push_axis_combo.currentText().lower()
            scale_value = self.push_scale_value_spin.value()

            # Remap value parameters
            input_min = self.remap_input_min_spin.value()
            input_max = self.remap_input_max_spin.value()
            output_min = self.remap_output_min_spin.value()
            output_max = self.remap_output_max_spin.value()

            # Call the rewritten batch function - only fingers, no elbows/knees
            created_joints = avg_push_joint.batchCreateAllAvgPush(
                side=side,
                fingers=None,  # Uses default: ['Thumb', 'Index', 'Middle', 'Ring', 'Pinky']
                weight=weight,
                driver_axis=twist_axis,
                distance_axis=push_axis,
                scale_axis='x',
                driver_value=input_max,
                distance_value=output_max,
                scale_value=scale_value,
                input_min=input_min,
                input_max=input_max,
                output_min=output_min,
                output_max=output_max,
                include_limbs=False  # Only create for fingers, not elbows/knees
            )

            # Build success message with details
            success_msg = f"Successfully batch created avg + push joints:\n"
            success_msg += f"Total joints processed: {len(created_joints)}\n"
            success_msg += f"Includes: All fingers (Base/Mid/Tip) for Both sides\n"
            success_msg += f"Weight: {weight}\n"
            success_msg += f"{twist_axis.upper()} rotation → {push_axis.upper()} push\n"
            success_msg += f"Remap: [{input_min}, {input_max}] → [{output_min}, {output_max}]"

            self.show_success(success_msg)
            logger.info(f"Batch created {len(created_joints)} avg+push joint pairs")

        except Exception as e:
            self.show_error(f"Error batch creating joints:\n{str(e)}")
            logger.error(f"Error in batch_create_all_avg_push: {e}")

    def get_axis_from_combo(self, combo_text):
        """Parse axis combo box text to tuple"""
        axis_map = {
            "X (1,0,0)": (1, 0, 0),
            "Y (0,1,0)": (0, 1, 0),
            "Z (0,0,1)": (0, 0, 1),
            "-X (-1,0,0)": (-1, 0, 0),
            "-Y (0,-1,0)": (0, -1, 0),
            "-Z (0,0,-1)": (0, 0, -1)
        }
        return axis_map.get(combo_text, (0, 1, 0))

    def setup_twist_joint_chain(self):
        """Setup twist joint chain from selected joints"""
        try:
            # Get current selection
            selection = cmds.ls(selection=True, type='joint')

            # Validate selection
            if len(selection) != 2:
                self.show_error("Please select exactly 2 joints:\n1. Start joint\n2. End joint")
                return

            startJoint = selection[0]
            endJoint = selection[1]

            # Get parameters from UI
            twist_count = self.twist_count_spin.value()
            twist_axis = self.get_axis_from_combo(self.twist_axis_combo.currentText())
            up_axis = self.get_axis_from_combo(self.up_axis_combo.currentText())

            # Call the rollBone function
            twist_joints, basis_joint = rollBone.setupTwistJointChain(
                startJoint, endJoint, twist_count, twist_axis, up_axis
            )

            self.show_success(f"Successfully created twist joint chain:\n" +
                            f"Start: {startJoint}\n" +
                            f"End: {endJoint}\n" +
                            f"Twist Joints: {len(twist_joints)}")
            logger.info(f"Created twist joints: {twist_joints}")

        except Exception as e:
            self.show_error(f"Error setting up twist joint chain:\n{str(e)}")
            logger.error(f"Error in setup_twist_joint_chain: {e}")

    def setup_counter_twist_chain(self):
        """Setup counter twist joint chain from selected joints"""
        try:
            # Get current selection
            selection = cmds.ls(selection=True, type='joint')

            # Validate selection
            if len(selection) != 2:
                self.show_error("Please select exactly 2 joints:\n1. Start joint\n2. End joint")
                return

            startJoint = selection[0]
            endJoint = selection[1]

            # Get parameters from UI
            twist_count = self.twist_count_spin.value()
            twist_axis = self.get_axis_from_combo(self.twist_axis_combo.currentText())
            up_axis = self.get_axis_from_combo(self.up_axis_combo.currentText())

            # Call the rollBone function
            twist_joints, up_joint, basis_joint = rollBone.setupCounterTwistJointChain(
                startJoint, endJoint, twist_count, twist_axis, up_axis
            )

            self.show_success(f"Successfully created counter twist joint chain:\n" +
                            f"Start: {startJoint}\n" +
                            f"End: {endJoint}\n" +
                            f"Twist Joints: {len(twist_joints)}")
            logger.info(f"Created counter twist joints: {twist_joints}")

        except Exception as e:
            self.show_error(f"Error setting up counter twist chain:\n{str(e)}")
            logger.error(f"Error in setup_counter_twist_chain: {e}")

    def setup_non_flip_twist(self):
        """Setup non-flip twist chain from selected joints"""
        try:
            # Get current selection
            selection = cmds.ls(selection=True, type='joint')

            # Validate selection - need start, end, and up joint
            if len(selection) != 3:
                self.show_error("Please select exactly 3 joints:\n1. Start joint\n2. End joint\n3. Up joint")
                return

            startJoint = selection[0]
            endJoint = selection[1]
            upJoint = selection[2]

            # Get up axis from UI
            up_axis_tuple = self.get_axis_from_combo(self.up_axis_combo.currentText())
            up_axis = om.MVector(up_axis_tuple)

            # Call the rollBone function
            dot_product_joint = rollBone.setupNonFlipTwistChain(
                startJoint, endJoint, upJoint, up_axis
            )

            self.show_success(f"Successfully created non-flip twist chain:\n" +
                            f"Start: {startJoint}\n" +
                            f"End: {endJoint}\n" +
                            f"Up Joint: {upJoint}")
            logger.info(f"Created non-flip twist with dot product joint: {dot_product_joint}")

        except Exception as e:
            self.show_error(f"Error setting up non-flip twist chain:\n{str(e)}")
            logger.error(f"Error in setup_non_flip_twist: {e}")

    def add_scapula_joints(self):
        """Add scapula joints based on selected locators"""
        try:
            # Get current selection
            selection = cmds.ls(selection=True, transforms=True)

            # Validate selection
            if len(selection) != 3:
                self.show_error("Please select exactly 3 locators:\n1. Acromion locator\n2. Scapula root locator\n3. Scapula tip locator")
                return

            # Get the three locators from selection
            acromionLoc = selection[0]
            scapulaLoc = selection[1]
            scapulaTipLoc = selection[2]

            # Verify they are valid objects
            for loc in selection:
                if not cmds.objExists(loc):
                    self.show_error(f"Selected object does not exist: {loc}")
                    return

            # Get side from UI
            side = self.side_combo.currentText()
            if side == "Both":
                side = "Left"  # Default to Left if Both is selected

            # Call the helper function to add scapula joints
            created_joints = helper_bone.addScapulaJointsToBiped(acromionLoc, scapulaLoc, scapulaTipLoc, side=side)

            self.show_success(f"Successfully created scapula joints for {side} side:\n" +
                            f"- {created_joints[0]}\n- {created_joints[1]}\n- {created_joints[2]}")
            logger.info(f"Created scapula joints: {created_joints}")

        except RuntimeError as e:
            self.show_error(f"Failed to create scapula joints:\n{str(e)}")
            logger.error(f"RuntimeError in add_scapula_joints: {e}")
        except Exception as e:
            self.show_error(f"Error creating scapula joints:\n{str(e)}")
            logger.error(f"Error in add_scapula_joints: {e}")

    def mirror_scapula_joints(self):
        """Mirror scapula joints from one side to the other"""
        try:
            # Get side from UI
            side = self.side_combo.currentText()
            if side == "Both":
                self.show_error("Please select either 'Left' or 'Right' as the source side for mirroring.")
                return

            # Call the mirror function
            mirrored_joints = helper_bone.mirrorScapulaJoints(sourceSide=side)

            target_side = "Right" if side == "Left" else "Left"
            self.show_success(f"Successfully mirrored scapula joints from {side} to {target_side}:\n" +
                            f"- {mirrored_joints[0]}\n- {mirrored_joints[1]}\n- {mirrored_joints[2]}")
            logger.info(f"Mirrored scapula joints: {mirrored_joints}")

        except RuntimeError as e:
            self.show_error(f"Failed to mirror scapula joints:\n{str(e)}")
            logger.error(f"RuntimeError in mirror_scapula_joints: {e}")
        except Exception as e:
            self.show_error(f"Error mirroring scapula joints:\n{str(e)}")
            logger.error(f"Error in mirror_scapula_joints: {e}")

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