# Muscle Rig System UI - Maya 2023

A comprehensive PyQt/PySide UI for creating anatomically accurate muscle rigs in Maya 2023.

## Maya 2023 Compatibility

This UI is specifically optimized for **Maya 2023** and uses **PySide2** (Maya's built-in UI framework).

### Requirements
- Maya 2023
- PySide2 (included with Maya 2023)
- Python 3.7+ (Maya 2023's Python)

## Quick Start

### Method 1: Simple Launch
```python
# In Maya 2023 Script Editor (Python tab):
import sys
sys.path.append(r"E:\python work\jointBasedMuscle_template")
import launch_muscle_ui
ui = launch_muscle_ui.launch()
```

### Method 2: Setup Test + Launch
```python
# Run complete setup test first:
import sys
sys.path.append(r"E:\python work\jointBasedMuscle_template")
exec(open(r"E:\python work\jointBasedMuscle_template\maya2023_setup.py").read())
```

## UI Features

### 🎯 Muscle Creation Buttons
- **Trapezius** (Green) - 3-part trapezius muscle
- **Latissimus Dorsi** (Blue) - 2-part lat muscle
- **Teres Major** (Orange) - Teres major muscle
- **Pectoralis Major** (Purple) - 2-part pec muscle
- **Deltoid** (Red) - 3-part deltoid muscle
- **Upper Arm** (Gray) - Bicep and tricep muscles

### ⚙️ Options Panel
- **Side Selection**: Left, Right, or Both
- **Auto Mirror**: Automatically create opposite side
- **Compression Factor**: Muscle compression amount (0.1-2.0)
- **Stretch Factor**: Muscle stretch amount (0.1-3.0)

### 🔧 Control Panel
- **Finalize All**: Apply final constraints to all muscles
- **Delete All**: Remove all created muscles
- **Refresh**: Update UI state

## Workflow

1. **Set Options** → Choose side and deformation factors
2. **Click Muscle Button** → Instantly creates muscle rig
3. **Auto Mirror** → Creates opposite side automatically
4. **Finalize** → Applies constraints and cleanup
5. **Animate** → Your muscles respond to joint movement!

## Troubleshooting

### Common Issues

**"PySide2 not found"**
- Maya 2023 includes PySide2 by default
- Try restarting Maya
- Check Maya installation

**"Import Error: muscle_template"**
- Verify all files are in the same directory
- Check the file path in sys.path.append()
- Ensure no spaces in folder names

**"Failed to find joint"**
- Your character rig must have the expected joint names
- Check joint naming conventions in your rig

### Testing Your Setup

Run the setup test to verify everything works:
```python
exec(open(r"E:\python work\jointBasedMuscle_template\maya2023_setup.py").read())
```

## Maya 2023 Specific Features

- **Native PySide2 Integration**: Uses Maya's built-in UI framework
- **Maya-Style Theming**: Dark theme matching Maya 2023
- **Proper Window Management**: Integrates with Maya's window system
- **shiboken2 Integration**: Proper Maya main window parenting

## File Structure
```
jointBasedMuscle_template/
├── muscle_template.py      # Main muscle classes
├── muscle_bone.py          # Core muscle joint system
├── config.py              # Configuration data
├── muscle_ui.py           # Maya 2023 UI (PySide2)
├── launch_muscle_ui.py    # Maya 2023 launcher
├── maya2023_setup.py      # Setup test script
└── README_Maya2023.md     # This file
```

## Support

If you encounter issues:
1. Run `maya2023_setup.py` for diagnostic information
2. Check Maya's Script Editor for error messages
3. Verify your character rig has the expected joint names
4. Ensure all files are in the same directory

## Version Notes

- **Maya 2023**: Fully supported with PySide2
- **Maya 2022**: May work but not officially tested
- **Maya 2024+**: Should work but may need minor adjustments

---

**Happy Rigging!** 🎬💪