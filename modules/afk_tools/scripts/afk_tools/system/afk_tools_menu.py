import os
import maya.cmds as cmds

MENU_NAME = "AFKToolsMenu"
MENU_LABEL = "AFK Tools"

def create_menu():
    """Create the custom AFK Tools menu in Maya's main window."""
    # Ensure we don't duplicate the menu
    if cmds.menu(MENU_NAME, exists=True):
        cmds.deleteUI(MENU_NAME, menu=True)
        
    # Create the top-level menu
    cmds.menu(MENU_NAME, label=MENU_LABEL, parent="MayaWindow", tearOff=True)

    # Add tools as menu items below
    current_dir = os.path.dirname(os.path.abspath(__file__))
    path = os.path.normpath(os.path.join(current_dir, "..", "..", "..", "snippets")).replace("\\", "/")
    
    cmds.menuItem(
        "ReloadPluginMenuItem",
        label="Reload Plugin",
        parent=MENU_NAME,
        command="import maya.cmds as cmds; cmds.evalDeferred('cmds.unloadPlugin(\"afk_tools\"); cmds.loadPlugin(\"afk_tools\")')"
    )

    cmds.menuItem(divider=True, parent=MENU_NAME)
    
    cmds.menuItem(
        "MayaSnippetsToolMenuItem",
        label="Maya Snippets Tool",
        parent=MENU_NAME,
        command=f"from afk_tools.maya_snippets_tool import maya_snippets_tool; maya_snippets_tool.MayaSnippetTool.show_tool('{path}')"
    )
    
    cmds.menuItem(divider=True, parent=MENU_NAME)
    
    cmds.menuItem(
        "OrientPlanarJointsMenuItem",
        label="Orient Planar Joints",
        parent=MENU_NAME,
        command="from afk_tools.rig_utils.orient_planar_joints import orient_planar_joints_ui; orient_planar_joints_ui()"
    )
    
    cmds.menuItem(
        "CreateJointsOnCurveMenuItem",
        label="Create Joints on Curve",
        parent=MENU_NAME,
        command="from afk_tools.rig_utils.create_joints_on_curve import create_joints_on_curve_ui; create_joints_on_curve_ui()"
    )
    
    cmds.menuItem(divider=True, parent=MENU_NAME)
    
    cmds.menuItem(
        "TagJointsMenuItem",
        label="Tag Joints",
        parent=MENU_NAME,
        command="from afk_tools.rig_utils.joint_metadata import tag_selected_joints_ui; tag_selected_joints_ui()"
    )

def remove_menu():
    """Remove the custom AFK Tools menu from Maya."""
    if cmds.menu(MENU_NAME, exists=True):
        cmds.deleteUI(MENU_NAME, menu=True)
