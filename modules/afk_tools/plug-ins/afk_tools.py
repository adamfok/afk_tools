import maya.api.OpenMaya as om
import importlib

vendor = "Chun Wai (Adam) Fok"
version = "1.0.0"


def maya_useNewAPI():
    pass


def initializePlugin(plugin):
    om.MFnPlugin(plugin, vendor, version)

    import afk_tools.system.install
    afk_tools.system.install.run()
    
    # Create the custom Maya menu
    import afk_tools.system.afk_tools_menu
    importlib.reload(afk_tools.system.afk_tools_menu)
    afk_tools.system.afk_tools_menu.create_menu()


def uninitializePlugin(plugin):
    # Remove the custom Maya menu
    import afk_tools.system.afk_tools_menu
    afk_tools.system.afk_tools_menu.remove_menu()
