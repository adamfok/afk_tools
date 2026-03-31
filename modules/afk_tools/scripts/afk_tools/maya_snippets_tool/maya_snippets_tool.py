import os
import sys
from PySide2 import QtWidgets, QtCore, QtGui

import maya.cmds as cmds
import maya.mel as mel
from maya.app.general.mayaMixin import MayaQWidgetDockableMixin
import shutil

class SnippetTreeWidget(QtWidgets.QTreeWidget):
    def __init__(self, parent_tool, parent=None):
        super(SnippetTreeWidget, self).__init__(parent)
        self.tool = parent_tool
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setDragDropMode(QtWidgets.QAbstractItemView.InternalMove)

    def dropEvent(self, event):
        source_item = self.currentItem()
        if not source_item:
            return
            
        source_path = source_item.data(0, QtCore.Qt.UserRole)
        if not source_path:
            return

        drop_target = self.itemAt(event.pos())
        if drop_target:
            target_path = drop_target.data(0, QtCore.Qt.UserRole)
        else:
            target_path = self.tool.dir_path_edit.text()
            
        if not target_path:
            return
            
        if os.path.isfile(target_path):
            target_dir = os.path.dirname(target_path)
        else:
            target_dir = target_path
            
        # Prevent moving a folder into itself
        if target_dir == source_path or target_dir.startswith(source_path + os.sep) or target_dir.startswith(source_path + '/'):
            cmds.warning("Cannot move a folder into itself.")
            return

        if os.path.dirname(source_path) == target_dir:
            return
            
        new_path = os.path.join(target_dir, os.path.basename(source_path))
        if os.path.exists(new_path):
            cmds.warning("A file or folder with that name already exists at the destination.")
            return

        try:
            shutil.move(source_path, new_path)
            self.tool.populate_files()
        except Exception as e:
            cmds.warning("Failed to move item: {}".format(e))

class MayaSnippetTool(MayaQWidgetDockableMixin, QtWidgets.QWidget):
    CONTROL_NAME = "MayaSnippetToolControl"
    WINDOW_TITLE = "Maya Snippets"
    OPTION_VAR_NAME = "MayaSnippetTool_LastDir"

    def __init__(self, init_path=None, parent=None):
        super(MayaSnippetTool, self).__init__(parent)
        self.setWindowTitle(self.WINDOW_TITLE)
        self.setObjectName(self.CONTROL_NAME) # Object name should match control name
        self.init_path = init_path
        
        self.setup_ui()
        
    def setup_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        
        # Directory selection
        dir_layout = QtWidgets.QHBoxLayout()
        self.dir_path_edit = QtWidgets.QLineEdit()
        self.dir_path_edit.setPlaceholderText("Select snippets directory...")
        
        browse_btn = QtWidgets.QPushButton("Browse")
        browse_btn.clicked.connect(self.browse_directory)
        
        # Refresh button beside Browse
        refresh_btn = QtWidgets.QPushButton()
        refresh_btn.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_BrowserReload))
        refresh_btn.setToolTip("Refresh file list")
        refresh_btn.clicked.connect(self.populate_files)
        
        dir_layout.addWidget(self.dir_path_edit)
        dir_layout.addWidget(browse_btn)
        dir_layout.addWidget(refresh_btn)
        layout.addLayout(dir_layout)
        
        # Search bar
        self.search_bar = QtWidgets.QLineEdit()
        self.search_bar.setPlaceholderText("Search scripts...")
        self.search_bar.textChanged.connect(self.filter_files)
        layout.addWidget(self.search_bar)
        
        # File list
        self.file_list = SnippetTreeWidget(self)
        self.file_list.setHeaderLabels(["Name"])
        self.file_list.setColumnWidth(0, 300)
        self.file_list.itemDoubleClicked.connect(self.on_item_double_clicked)
        
        # Context menu for adding scripts
        self.file_list.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.file_list.customContextMenuRequested.connect(self.on_context_menu)
        
        layout.addWidget(self.file_list)
        
        # Determine start directory:
        # 1. User defined path (arg)
        # 2. Last used path (optionVar)
        start_dir = None
        if self.init_path and os.path.isdir(self.init_path):
            start_dir = self.init_path
        elif cmds.optionVar(exists=self.OPTION_VAR_NAME):
            last_dir = cmds.optionVar(query=self.OPTION_VAR_NAME)
            if os.path.isdir(last_dir):
                start_dir = last_dir
                
        if start_dir:
            self.dir_path_edit.setText(start_dir)
            # Defer population slightly to ensure UI is ready
            QtCore.QTimer.singleShot(0, self.populate_files)
        else:
            self.add_placeholder("Click 'Browse' to select a folder")

    def add_placeholder(self, text):
        self.file_list.clear()
        placeholder = QtWidgets.QTreeWidgetItem(self.file_list)
        placeholder.setText(0, text)
        placeholder.setForeground(0, QtGui.QColor(120, 120, 120))
        placeholder.setFlags(QtCore.Qt.NoItemFlags)

    def browse_directory(self):
        selected_dir = QtWidgets.QFileDialog.getExistingDirectory(
            self, "Select Directory", self.dir_path_edit.text() or os.getcwd()
        )
        if selected_dir:
            self.dir_path_edit.setText(selected_dir)
            self.populate_files()

    def populate_files(self):
        root_dir = self.dir_path_edit.text()
        if not root_dir or not os.path.isdir(root_dir):
            self.add_placeholder("Invalid directory selected")
            return
            
        # Save to optionVar
        cmds.optionVar(stringValue=(self.OPTION_VAR_NAME, root_dir))
            
        self.file_list.clear()
        
        # Dictionary to keep track of folder items
        folder_items = {root_dir: self.file_list.invisibleRootItem()}
        found_any = False
        
        for root, dirs, files in os.walk(root_dir):
            # Sort for consistency
            dirs.sort()
            files.sort()
            
            # Create items for directories
            for d in dirs:
                full_path = os.path.join(root, d)
                parent_path = root
                
                if parent_path in folder_items:
                    parent_item = folder_items[parent_path]
                    item = QtWidgets.QTreeWidgetItem(parent_item)
                    item.setText(0, d)
                    item.setIcon(0, self.style().standardIcon(QtWidgets.QStyle.SP_DirIcon))
                    item.setData(0, QtCore.Qt.UserRole, full_path) # Store path for folder too
                    folder_items[full_path] = item
            
            # Create items for files
            for f in files:
                if f.endswith(('.py', '.mel')):
                    found_any = True
                    full_path = os.path.join(root, f)
                    ext = os.path.splitext(f)[1].lower()
                    
                    parent_item = folder_items.get(root, self.file_list.invisibleRootItem())
                    item = QtWidgets.QTreeWidgetItem(parent_item)
                    item.setText(0, f)
                    item.setData(0, QtCore.Qt.UserRole, full_path)
                    
                    # Set icon based on type
                    if ext == '.py':
                        item.setForeground(0, QtGui.QColor(128, 200, 255)) # Light blue for python
                    else:
                        item.setForeground(0, QtGui.QColor(255, 200, 128)) # Orange for mel
        
        self.file_list.expandAll()
        
        if not found_any:
            self.add_placeholder("No .py or .mel files found in this directory")

    def on_item_double_clicked(self, item, column):
        """Load the selected script into the focused Script Editor executer."""
        full_path = item.data(0, QtCore.Qt.UserRole)
        self.load_script_to_editor(full_path)

    def filter_files(self, text):
        """Filter the tree list based on the search text."""
        search_text = text.lower()
        
        def traverse_and_filter(item):
            # Check if this item matches
            item_text = item.text(0).lower()
            match = search_text in item_text
            
            # Check children
            child_match = False
            for i in range(item.childCount()):
                child = item.child(i)
                if traverse_and_filter(child):
                    child_match = True
            
            # Show if item matches or any child matches
            should_show = match or child_match
            item.setHidden(not should_show)
            
            # Expand if showing and has matching children (and we are searching)
            if should_show and child_match and search_text:
                item.setExpanded(True)
                
            return should_show

        # Loop through top-level items
        root = self.file_list.invisibleRootItem()
        for i in range(root.childCount()):
            traverse_and_filter(root.child(i))

    def load_script_to_editor(self, full_path):
        """Native Maya command to load a file into the focused executer using user-provided MEL."""
        if not full_path or not os.path.isfile(full_path):
            return

        safe_path = full_path.replace("\\", "/")
        
        # User-provided MEL snippet adapted for Python injection
        # We assume global variables like $gCommandExecuterTabs allow access to the UI
        # Wrapped in { } to create a local scope and avoid variable redeclaration warnings
        # Using %s for string formatting to ensure Python 2.7 compatibility
        mel_script = """
        {
            global string $gCommandExecuterTabs;
            global string $gLastFocusedCommandExecuter;
            
            string $loadFile = "%s";
            
            // Check if file is already open. If NOT open, proceed to create.
            // (Using if block instead of return because 'return' is only valid in procs)
            if (!selectExecuterTabByName($loadFile)) {
                string $ext = fileExtension($loadFile);
                
                int $sel = 1;
                if ($ext == "py") {
                    buildNewExecuterTab(-1, "Python", "python", 0);
                } else if ($ext == "mel") {
                    buildNewExecuterTab(-1, "MEL", "mel", 0);
                } else {
                    $sel = 0;
                    addNewExecuterTab("", 0);
                }

                if ($sel) {
                    // select the last tab created
                    tabLayout -e -selectTabIndex `tabLayout -q -numberOfChildren $gCommandExecuterTabs` $gCommandExecuterTabs;
                    selectCurrentExecuterControl();
                }

                // Then load the file contents into the new field
                delegateCommandToFocusedExecuterWindow("-e -loadFile \\"" + $loadFile + "\\"", 0);

                // Get the filename and rename the tab.
                string $filename = `cmdScrollFieldExecuter -query -filename $gLastFocusedCommandExecuter`;
                if (size($filename) > 0) {
                    renameCurrentExecuterTab($filename, 0);
                    delegateCommandToFocusedExecuterWindow "-e -modificationChangedCommand executerTabModificationChanged" 0;
                    delegateCommandToFocusedExecuterWindow "-e -fileChangedCommand executerTabFileChanged" 0;
                }
            }
        }
        """
        
        try:
            # Format the MEL script with the file path
            final_mel = mel_script % safe_path
            mel.eval(final_mel)
        except Exception as e:
            cmds.warning("Error loading script via MEL: %s" % e)

    def on_context_menu(self, pos):
        """Show context menu for items (files or folders)."""
        item = self.file_list.itemAt(pos)
        if not item:
            directory = self.dir_path_edit.text()
            if not directory or not os.path.isdir(directory):
                return
            path = directory
            item_type = "root"
        else:
            path = item.data(0, QtCore.Qt.UserRole)
            if not path:
                return
            item_type = 'file' if os.path.isfile(path) else 'folder'
            if os.path.isfile(path):
                directory = os.path.dirname(path)
            elif os.path.isdir(path):
                directory = path
            else:
                return
            
        menu = QtWidgets.QMenu(self)
        add_script_action = menu.addAction("Add Script...")
        add_script_action.triggered.connect(lambda: self.show_create_dialog(directory))
        
        add_folder_action = menu.addAction("Add Folder...")
        add_folder_action.triggered.connect(lambda: self.show_create_folder_dialog(directory))
        
        if item_type != "root":
            menu.addSeparator()
            remove_action = menu.addAction("Remove")
            remove_action.triggered.connect(lambda: self.delete_item(path))
        
        menu.exec_(self.file_list.mapToGlobal(pos))

    def delete_item(self, path):
        if not path or not os.path.exists(path):
            return
        
        is_file = os.path.isfile(path)
        item_type = "Script" if is_file else "Folder"
        
        result = QtWidgets.QMessageBox.question(
            self,
            "Confirm Delete",
            "Are you sure you want to delete this {}?\n\n{}".format(item_type, os.path.basename(path)),
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.No
        )
        
        if result == QtWidgets.QMessageBox.Yes:
            try:
                if is_file:
                    os.remove(path)
                else:
                    shutil.rmtree(path)
                self.populate_files()
            except Exception as e:
                cmds.warning("Failed to delete {}: {}".format(item_type, e))

    def show_create_folder_dialog(self, directory):
        result, ok = QtWidgets.QInputDialog.getText(self, "New Folder", "Folder Name:")
        if ok and result:
            new_dir = os.path.join(directory, result)
            if not os.path.exists(new_dir):
                try:
                    os.makedirs(new_dir)
                    self.populate_files()
                except Exception as e:
                    cmds.warning("Failed to create folder: {}".format(e))
            else:
                cmds.warning("Folder already exists.")

    def show_create_dialog(self, directory):
        """Prompt user for script name and type."""
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("Add New Script")
        dialog.setFixedWidth(300)
        
        layout = QtWidgets.QVBoxLayout(dialog)
        
        name_layout = QtWidgets.QHBoxLayout()
        name_layout.addWidget(QtWidgets.QLabel("Name:"))
        name_edit = QtWidgets.QLineEdit()
        name_layout.addWidget(name_edit)
        layout.addLayout(name_layout)
        
        btn_layout = QtWidgets.QHBoxLayout()
        py_btn = QtWidgets.QPushButton("Python (.py)")
        mel_btn = QtWidgets.QPushButton("MEL (.mel)")
        btn_layout.addWidget(py_btn)
        btn_layout.addWidget(mel_btn)
        layout.addLayout(btn_layout)
        
        def create_py():
            self.create_script(directory, name_edit.text(), ".py")
            dialog.accept()
            
        def create_mel():
            self.create_script(directory, name_edit.text(), ".mel")
            dialog.accept()
            
        py_btn.clicked.connect(create_py)
        mel_btn.clicked.connect(create_mel)
        
        py_btn.setDefault(True)
        name_edit.returnPressed.connect(create_py)
        
        dialog.exec_()

    def create_script(self, directory, name, ext):
        """Create the actual file, refresh, and auto-open."""
        if not name:
            cmds.warning("Please provide a name for the script")
            return
            
        if not name.endswith(ext):
            filename = name + ext
        else:
            filename = name
            
        full_path = os.path.join(directory, filename)
        
        if os.path.exists(full_path):
            cmds.warning("File already exists: %s" % filename)
            return
            
        try:
            with open(full_path, 'w') as f:
                f.write("")
            
            # Refresh list
            self.populate_files()
            
            # Auto-open the new file
            self.load_script_to_editor(full_path)
            
        except Exception as e:
            cmds.warning("Failed to create script: %s" % e)

    @classmethod
    def show_tool(cls, path=None):
        """Show the tool using MayaQWidgetDockableMixin with cleanup.
        
        Args:
            path (str, optional): Initial directory to open.
        """
        # Explicitly delete existing control and window to avoid "name not unique" errors
        workspace_name = cls.CONTROL_NAME + "WorkspaceControl"
        if cmds.workspaceControl(workspace_name, exists=True):
            cmds.deleteUI(workspace_name)
        
        if cmds.window(cls.CONTROL_NAME, exists=True):
            cmds.deleteUI(cls.CONTROL_NAME)

        # Using MayaQWidgetDockableMixin's show method
        window = cls(init_path=path)
        window.show(dockable=True, floating=True, area="right", width=300)
        return window

if __name__ == "__main__":
    MayaSnippetTool.show_tool()
