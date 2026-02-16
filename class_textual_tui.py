from textual.app import App, ComposeResult
from textual.widgets import Static, ListView, ListItem, Label 
from rich.text import Text
from textual.widgets import Button
from textual.containers import Horizontal, Vertical
from textual.widgets import Header, Footer
from textual.widgets import Tree
from textual.reactive import reactive
from textual import events

from class_tree_viewer import TreeViewer,TreeNode

class MessageBoxApp(App):

    CSS = """
    #question {
        padding: 0;
        margin: 0;
    }
    #buttons {
        padding: 0;
        margin: 1 0 0 0;
    }
    """

    def __init__(self, title, question, default=True):
        super().__init__()
        self.title = title
        self.question = question
        self.default = default
        self.choice = None

    def compose(self):
        yield Header(show_clock=False)

        yield Vertical(
            Static(self.question, id="question"),
            Horizontal(
                Button("Yes", id="yes"),
                Button("No", id="no"),
                id="buttons"
            )
        )

        yield Footer()

    def on_mount(self):
        # Highlight default button
        if self.default:
            self.query_one("#yes", Button).focus()
        else:
            self.query_one("#no", Button).focus()

    def on_button_pressed(self, event: Button.Pressed):
        self.choice = (event.button.id == "yes")
        self.exit(self.choice)

    def on_key(self, event: events.Key):
        yes_btn = self.query_one("#yes", Button)
        no_btn = self.query_one("#no", Button)

        # ESC → False
        if event.key == "escape":
            self.exit(False)

        # ENTER → default choice
        elif event.key == "enter":
            self.exit(self.default)

        # TAB or RIGHT → move focus
        elif event.key in ("tab", "right"):
            if yes_btn.has_focus:
                no_btn.focus()
            else:
                yes_btn.focus()

        # SHIFT+TAB or LEFT → move focus backward
        elif event.key in ("left", "shift+tab"):
            if no_btn.has_focus:
                yes_btn.focus()
            else:
                no_btn.focus()

class MenuItem(ListItem):
    def __init__(self, text: str, locked: bool = False, prefix: str = None):
        self.text = text
        self.locked = locked
        self.prefix=prefix
        pre_txt=""
        if prefix:
            pre_txt+=f"{self.prefix}"
        if locked:
            label = Label(f"{pre_txt}🔒[dim]{text}[/dim]")
        else:
            label = Label(f"{pre_txt}{text}")

        super().__init__(label)
        

class MenuApp(App):
 
    CSS = """
    Screen {
        align: center middle;
    }
    #title {
        margin-bottom: 0;
        text-style: bold;
    }
    #title, #help {
        padding: 0;
        margin: 0;
        height: auto;
        min-height: 0;
    }
    Vertical {
        padding: 0;
        margin: 0;
    }
    """

    def __init__(self, menu_items, menu_options=None):
        super().__init__()
        self.button_flag=None
        # Normalize menu_items
        if isinstance(menu_items, dict):
            self.menu_dict = menu_items
            self.menu_items = list(menu_items.keys())
        else:
            self.menu_dict = None
            self.menu_items = menu_items

        self.menu_options = menu_options or {}
        self.default_selection = self.menu_options.get(
            "default_selection",
            self.menu_items[0]
        )
        self.locked_items = set(self.menu_options.get("locked", []))
        self.pre_texts = []
        do_enumerate=self.menu_options.get("enumerate",False)
        prefix=self.menu_options.get("prefix","")
        for iii,_ in enumerate(self.menu_items):
            if do_enumerate:
                self.pre_texts.append(f"{iii+1}{prefix}")
            else:
                if do_enumerate:
                    self.pre_texts.append(f"{prefix}")
        self.title=self.menu_options.get("title","Menu")
    
    def compose(self):
        
        yield Header(show_clock=False, id="header")

        yield Vertical(
            Static(self.menu_options.get("subtitle", ""), id="subtitle"),
            Static("", id="help"),
            ListView(
                *[
                    MenuItem(item, locked=item in self.locked_items, prefix=pre_txt)
                    for item, pre_txt in zip(self.menu_items, self.pre_texts)
                ],
                id="menu"
            )
        )

        yield Footer()    
    # def compose(self):
    #     yield Header(show_clock=False)

    #     yield Vertical(
    #         Static(self.menu_options.get("title", "Select an option"), id="title"),
    #         Static(self.menu_options.get("subtitle", ""), id="help"),
    #         ListView(
    #             *[
    #                 MenuItem(item, locked=item in self.locked_items, prefix=pre_txt)
    #                 for item, pre_txt in zip(self.menu_items, self.pre_texts)
    #             ],
    #             id="menu"
    #         )
    #     )

    #     yield Footer() 

    def on_mount(self):
        """Highlight default selection after UI is ready."""
        list_view = self.query_one("#menu", ListView)
        index = self.menu_items.index(self.default_selection)
        # set the selected index
        list_view.index = index
        # give focus to the ListView itself
        list_view.focus()

    def on_list_view_highlighted(self, event: ListView.Highlighted) -> None:
        item = event.item
        key = item.text

        if self.menu_dict:
            help_label = self.query_one("#help", Static)
            help_label.update(self.menu_dict[key])

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        item = event.item
        selected_key = item.text
        # Update help text if using dict mode
        if self.menu_dict:
            help_label = self.query_one("#help", Static)
            help_label.update(self.menu_dict[selected_key])
        # Block locked items
        if item.locked:
            return
        # Block left-click selection
        if self.button_flag == 1:
            self.button_flag = None
            return
        # Reset right-click flag
        if self.button_flag == 3:
            self.button_flag = None
        # Exit with the selected key
        self.exit(selected_key)
    
    def on_mouse_down(self, event: events.MouseDown):
        """Handle left and right mouse clicks on nodes."""
        self.button_flag=event.button

    def on_key(self, event: events.Key) -> None:
        list_view = self.query_one("#menu", ListView)
        items = list_view.children
        count = len(items)
        index = list_view.index
        # ESC → exit with empty list
        if event.key == "escape":
            self.exit([])
        # ENTER → select
        elif event.key == "enter":
            list_view.action_select_cursor()
        # HOME → first selectable
        elif event.key == "home":
            self._jump_to_selectable(list_view, start=-1, forward=True)
        # END → last selectable
        elif event.key == "end":
            self._jump_to_selectable(list_view, start=count, forward=False)
        # TAB → next selectable
        elif event.key == "tab":
            self._jump_to_selectable(list_view, start=index, forward=True)
        # SHIFT+TAB → previous selectable
        elif event.key == "shift+tab":
            self._jump_to_selectable(list_view, start=index, forward=False)

    def _jump_to_selectable(self, list_view, start, forward=True):
        items = list_view.children
        count = len(items)

        step = 1 if forward else -1
        index = start

        for _ in range(count):
            index = (index + step) % count
            item = items[index]

            if not item.locked:
                list_view.index = index
                list_view.focus()
                return

class CheckTreeWidget(Tree):

    # Override the Tree's own key bindings
    BINDINGS = [
        ("right", "expand_node", "Expand"),
        ("left", "collapse_node", "Collapse"),
        ("enter", "noop", "Return Selection"),
        ("space", "action_toggle_select", "Toggle"),
        ("tab", "action_toggle_select", "Toggle"),
    ]

    # Disable space toggling completely
    def action_toggle_node(self):
        pass

    # Right arrow expands
    def action_expand_node(self):
        node = self.cursor_node
        if node and not node.is_expanded:
            node.expand()

    # Left arrow collapses
    def action_collapse_node(self):
        node = self.cursor_node
        if node and node.is_expanded:
            node.collapse()
    
    def action_noop(self):
        pass

    
class CheckTreeApp(App):

    CSS = """
    Screen {
        align: center middle;
    }
    #title {
        margin-bottom: 1;
        text-style: bold;
    }
    Tree .locked {
        color: #666666;
        text-style: dim italic;
    }
    """

    BINDINGS = [
        #("space", "toggle_select", "Select / Unselect"),
        ("esc", "quit", "Quit"),
        ("q", "quit", "Quit"),
        #("enter", "noop", "Return Selection"),   
        ('ctrl+a', "select_all", "Select All"),
        ('ctrl+u', "unselect_all", "Unselect All"),   

    ]
    def __init__(self, tree_viewer: TreeViewer, tree_mode:dict=None, **kwargs):
            super().__init__(**kwargs)
            self.viewer = tree_viewer
            self.tree_mode=tree_mode
            self.button_flag=None
            self.one_selection=self.tree_mode.get("one_selection",False)
            self.return_id=self.tree_mode.get("return_id",True)


    def compose(self) -> ComposeResult:
        yield Header()
        yield Vertical(
            Label("Checkbox TreeView Example", id="title"),
            CheckTreeWidget("Root", id="tree")
        )
        yield Footer()

    def build_textual_tree(self, tparent, viewer_node:TreeNode):
        if not isinstance(viewer_node,TreeNode):
            return
        data={
            "node": viewer_node.id, # <-- direct reference
            "selected": viewer_node.selected or False,
            "raw": viewer_node.name,
            }
        if viewer_node.parent is None:
            tnode=tparent
            tnode.set_label(viewer_node.name)
            tnode.data=data
        else:    
            # Create a Textual node and attach TreeNode to it
            tnode = tparent.add(
                viewer_node.name,
                data=data
            )
        root_selectable=True
        dir_selectable=True
        only_dir=False
        locked_items=[]
        tnode.allow_expand = (viewer_node.i_am == "dir")
        root_selectable,dir_selectable,only_dir,locked_items,default_selected_items=(True,True,False,[],[])
        if isinstance(self.tree_mode,dict):
            root_selectable=self.tree_mode.get("root_selectable",True)
            dir_selectable=self.tree_mode.get("dir_selectable",True)
            only_dir=self.tree_mode.get("only_dir",False)
            locked_items=self.tree_mode.get("locked_items",[])
            default_selected_items=self.tree_mode.get("default_selected_items",[])
        
        if viewer_node.parent is None and not root_selectable:
            viewer_node.selectable=False

        if viewer_node.id in default_selected_items:
            viewer_node.selected=True
            self.viewer.set_selected_children(self.viewer.main_node)

        if viewer_node.id in locked_items:
            viewer_node.selectable=False

        if viewer_node.i_am == 'dir':
            viewer_node.selectable=dir_selectable

        # Expand/collapse based on model
        if viewer_node.i_am == 'dir':
            if viewer_node.expand:
                tnode.expand()
            else:
                tnode.collapse()
        
        # Recurse
        if isinstance (viewer_node.children,list) and len(viewer_node.children)>0: 
            for child in viewer_node.children:
                if child.i_am != 'dir' and only_dir:
                    continue  
                self.build_textual_tree(tnode, child)

        return tnode
    
    def on_mount(self):
        tree = self.query_one("#tree")

        # Build only the root
        root = self.viewer.main_node
        self.build_textual_tree(tree.root, root)
        self.refresh_labels(tree.root)

    # Format label with checkbox
    def format_label(self, node):
        if node.data is None:
            return
        viewer_node = self.viewer.get_nodes_by_attribute("id", node.data["node"])[0]
        node.data["selected"]=viewer_node.selected
        checked = node.data["selected"]
        raw = node.data.get("raw",node.label)
        raw = self.strip_checkbox(raw)
        if hasattr(viewer_node,"selectable"):
            locked_items=self.tree_mode.get("locked_items",[])
        
            if viewer_node.id in locked_items:
                raw_styled = Text(raw, style="dim italic")
                return f"🔒 {raw_styled}"
            if viewer_node.selectable == False or self.one_selection:
                return f"{raw}"        
        box = "[X]" if checked else "[ ]"
        return f"{box} {raw}"
    
    def strip_checkbox(self, alabel: str) -> str:
        alabel=str(alabel)
        if alabel.startswith("[x] ") or alabel.startswith("[ ] "):
            return alabel[4:]
        return alabel
    
    # Recursively refresh labels
    def refresh_labels(self, node):
        # Normalize data for every node
        if node.data is None:
            return 
        node.set_label(self.format_label(node))

        for child in node.children:
            self.refresh_labels(child)

    def on_tree_node_highlighted(self, event: Tree.NodeHighlighted):
        self.last_node = event.node
    
    def on_tree_node_expanded(self, event: Tree.NodeExpanded):
        node = event.node
        viewer_node = self.viewer.get_nodes_by_attribute("id", node.data["node"])[0]
        if viewer_node.i_am == 'dir':
            viewer_node.expand = True
        else:
            viewer_node.expand = None
        event.stop()

    def on_tree_node_collapsed(self, event: Tree.NodeCollapsed):
        node = event.node
        viewer_node = self.viewer.get_nodes_by_attribute("id", node.data["node"])[0]
        if viewer_node.i_am == 'dir':
            viewer_node.expand = False
        else:
            viewer_node.expand = None
        event.stop()
    
    def on_mouse_down(self, event: events.MouseDown):
        """Handle left and right mouse clicks on nodes."""
        self.button_flag=event.button

    def on_tree_node_selected(self, event: Tree.NodeSelected):
        self.cursor_node = event.node
        # LEFT CLICK 
        if self.button_flag == 1:
            self.button_flag=None

        # RIGHT CLICK 
        if self.button_flag == 3:
            self.button_flag=None
            self.action_toggle_select()

    def on_key(self, event):
        self.log(event.key)
        if event.key == "tab":
            self.action_toggle_select()
            return
        if event.key == "space":
            self.action_toggle_select()
            return
        if event.key == 'ctrl+a':
            self.select_all()
            return
        if event.key == 'ctrl+u':
            self.unselect_all()
            return
        if event.key == "escape":
            self.exit()
        if event.key == "enter":
            self.action_quit()
              
    
    def select_recursive(self,node: TreeNode,selection=True):
        node.selected=selection
        for child in node.children:
            self.select_recursive(child,selection)

    def select_all(self):
        tree = self.query_one("#tree")
        main_node=self.viewer.main_node
        self.select_recursive(main_node,True)
        self.refresh_labels(tree.root)
    
    def unselect_all(self):
        tree = self.query_one("#tree")
        main_node=self.viewer.main_node
        self.select_recursive(main_node,False)
        self.refresh_labels(tree.root)

    def action_toggle_select(self):
        tree = self.query_one("#tree")
        node = tree.cursor_node
        # Ensure metadata exists
        if node.data is None:
            return
        # Toggle
        viewer_node_list=self.viewer.get_nodes_by_attribute("id",node.data["node"]) 
        viewer_node=viewer_node_list[0]
        if viewer_node.selectable in [True,None]:
            viewer_node.selected = not viewer_node.selected
            self.viewer.set_selected_children(self.viewer.main_node)
        # Set to tree
        node.data["selected"] = viewer_node.selected
        if self.one_selection:
            self.action_quit()
        # Update label
        node.set_label(self.format_label(node))

    def get_selected_items(self):
        tree = self.query_one("#tree")
        selected = []

        def walk(node):
            if node.data and node.data.get("selected"):
                if not self.return_id:
                    selected.append(node.data["raw"])
                else:
                    selected.append(node.data["node"])
            for child in node.children:
                walk(child)

        walk(tree.root)
        return selected
    
    def action_quit(self):
        selected = self.get_selected_items()
        if self.one_selection and len(selected) == 0:
            tree = self.query_one("#tree")
            node = tree.cursor_node
            # Ensure metadata exists
            if node.data is None:
                return
            # Toggle
            viewer_node_list=self.viewer.get_nodes_by_attribute("id",node.data["node"]) 
            viewer_node=viewer_node_list[0]
            if viewer_node.selectable in [True,None]:
                viewer_node.selected = not viewer_node.selected
                self.viewer.set_selected_children(self.viewer.main_node)
                # Set to tree
                node.data["selected"] = viewer_node.selected
                # Read selection from tree
                selected = self.get_selected_items()
            else:
                return    
        self.exit(selected)
   

if __name__ == "__main__":
    items = {
        "Tree Example":"Tree List Selection",
        "File Example":"File path explorer Example",
        "Locked Example":"To Lock",
        "Locked Example 2":"2nd Locked",
        "Exit":"Quitting?"
    }
    items_list=list(items.keys())
    menu_options={
        "title": "Main Menu",
        "subtitle": "[yellow]Please Select one option:[/yellow]",
        "default_selection":items_list[1],
        "locked":[items_list[2],items_list[3]],
        "enumerate":True,
        "prefix":". "
        }
    menu_selection = MenuApp(items,menu_options).run()
    if menu_selection == "Tree Example":

        # Example dynamic structure
        tree_data = {
            "Root_item": [
                {"expandable_item1": [("selectable_item1",1), ("selectable_item2",2)]},
                {"expandable_item2": [
                    {"expandable_item3": [("selectable_item4",3)]},
                    "selectable_item1"
                ]},
                ("selectable_item5",4),
                ("selectable_item6",5)
            ]
        }
        tree_mode={
                "one_selection":True,
                "root_selectable":True,
                "dir_selectable":False,
                "only_dir":False, 
                "locked_items":[3,5],
                "default_selected_items":[],
                "return_id":True
                }
        
        tree_viewer=TreeViewer(tree_data,{'name':0,"size":1})
        result = CheckTreeApp(tree_viewer,tree_mode).run()
        print("Selected items:", result)
    if menu_selection == "File Example":
        import os
        from class_autocomplete_input import AutocompletePathFile
        from class_file_manipulate import FileManipulate
        FM = FileManipulate()
        input_path = AutocompletePathFile('return string [cyan]ENTER[/cyan], Autofill path/file [cyan]TAB[/cyan], Cancel [cyan]ESC[/cyan]\nOr type complete path to file: ',
                                            FM.get_app_path(),absolute_path=False,verbose=True).get_input()
        (file_exist, is_file)=FM.validate_path_file(input_path)
        if file_exist:
            if is_file:
                input_path=FM.extract_path(input_path,False)
            else:
                input_path=FM.remove_separator_in_path_end(input_path)
            print(f"\nBuilding structure for: {input_path}")
            def add_size(file):
                try:
                    return (FM.extract_filename(file,True),FM.get_file_size(file))
                except:
                    return (file,-1)
            file_struct=FM.get_file_structure_from_active_path(input_path,input_path,{},fcn_call=add_size)
            
            tree_mode={
                "one_selection":False,
                "root_selectable":True,
                "dir_selectable":False,
                "only_dir":False, 
                "locked_items":[],
                "default_selected_items":[]
                }
            
            tree_viewer=TreeViewer(file_struct,{'name':0,"size":1})
            tree_viewer.expand_all_treenodes(False)
            result = CheckTreeApp(tree_viewer,tree_mode).run()
            path_results=[]
            for id in result:
                try:
                    node=tree_viewer.get_nodes_by_attribute("id",id)[0]
                    print(f"{node.info[0]}: {FM.get_size_str_formatted(node.info[1],11,True)}")
                    s_path_list=tree_viewer.trace_path(node)
                    s_path=str(os.sep).join(s_path_list)
                    path_results.append(s_path)
                except (TypeError,IndexError):
                    pass
            print("Selected items:", result)
            print("Selected paths:", path_results)
    elif menu_selection == "Exit":
        result = MessageBoxApp(
                                title="Confirm Exit",
                                question="Are you sure you want to Exit?",
                                default=True
                                ).run()
        print("I quitted before user chose:", result)

    print("Bye Bye")
