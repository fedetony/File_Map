import csv
import pandas as pd
import json
from models.class_explorer_tree_model import *
from controllers.class_filemap_cli_manager import FileMapCliManager
from widgets.class_export_widget import *
from class_file_structurer import FileStructurer

class NodeExportFilters:
    @staticmethod
    def all(node: TreeNode) -> bool:
        return True

    @staticmethod
    def files(node: TreeNode) -> bool:
        return node.i_am == "file"
    
    @staticmethod
    def databases(node: TreeNode) -> bool:
        return node.i_am == "database"
    
    @staticmethod
    def maps(node: TreeNode) -> bool:
        return node.i_am == "map"

    @staticmethod
    def dirs(node: TreeNode) -> bool:
        return node.i_am == "dir"
    
    @staticmethod
    def files_and_dirs(node: TreeNode) -> bool:
        return node.i_am in ("dir","file")
    
    @staticmethod
    def existing( node: TreeNode, callback=None) -> bool:
        if callback is None:
            callback = NodeExportFilters.all
        return bool(node.i_exist and callback(node))
    
    @staticmethod
    def container(node: TreeNode) -> bool:
        return node.i_am in ("dir","database","map")

    @staticmethod
    def expanded(node: TreeNode) -> bool:
        # Files are visible as long as their bloodline is expanded
        bl = node.get_bloodline()
        for bl_node in bl[:-1]:
            if bl_node.expand is False:
                return False
        return True

    @staticmethod
    def selected(node: TreeNode) -> bool:
        return node.selected or node.selected_children

    @staticmethod
    def locked(node: TreeNode) -> bool:
        return node.locked


class TreeTextExporter:
    def __init__(self, style: ExportTreeStyle):
        self.style = style

    # ==========================================================
    # Public API
    # ==========================================================

    def export_tree_to_text(
        self,
        start_node: TreeNode,
        *,
        node_filter=None,
        max_level=None,
        include_files=True,
        include_dirs=True,
    ) -> str:
        """
        Export tree to a string.

        Suitable for smaller trees / clipboard use.

        Args:
            start_node:
                Node where export starts.

            node_filter:
                Optional callable(node) -> bool.
                Controls which nodes are printed.

            max_level:
                Optional maximum node.level to print.

            include_files:
                Include file nodes.

            include_dirs:
                Include directory nodes.
        """
        if start_node is None:
            return ""

        lines = []

        for line in self._iter_lines(
            start_node,
            node_filter=node_filter,
            max_level=max_level,
            include_files=include_files,
            include_dirs=include_dirs,
        ):
            lines.append(line)

        return "\n".join(lines)

    def dump_tree_to_file(self,
        filename,
        start_node: TreeNode,
        node_filter=None,
        max_level=None,
        include_files=True,
        include_dirs=True,
        log_callback=None,
        ):

        try:
            with open(filename, "w", encoding="utf-8") as f:
                self.stream_tree_to_file(start_node, f,
                                        node_filter=node_filter,
                                        max_level=max_level,
                                        include_files=include_files,
                                        include_dirs=include_dirs) 
        except Exception as eee:
            if log_callback:
                log_callback(f"[red]Error while dumping file {filename}")
                log_callback(f"{eee}")
    
    def get_single_node_line_text(
        self,
        node: TreeNode,
        is_last: bool,
        branch_state: list[bool] | None = None,
        ) -> str:
        """
        Generate the formatted text for a single tree node.

        The node's ``level`` determines how many indentation levels
        are generated. ``branch_state`` contains the ``is_last`` state
        of ancestor nodes and is used to render the correct vertical
        tree branches.

        Args:
            node:
                TreeNode to render.

            is_last:
                True if this node is the last child of its parent.

            branch_state:
                Optional list containing the ``is_last`` state for each
                ancestor level. If not provided, the current node's
                ``is_last`` state is used for all indentation levels.

        Returns:
            The complete formatted text line for the node, including
            indentation, branch, node text, and postfix formatting.
        """
        prefix = self.style.indent_prefix(node, is_last)
        if node.level > 0:
            for level in range(node.level):
                if not branch_state:
                    prefix += self.style.indent(node, is_last)
                else:
                    prefix += self.style.indent(node, branch_state[level])
            prefix += self.style.branch(node, is_last)
        postfix = self.style.indent_postfix(node, is_last)
        return prefix + self.style.text(node) + postfix

    def stream_tree_to_file(
        self,
        start_node: TreeNode,
        file,
        *, # everythig after has to be passed as a keyword
        node_filter=None,
        max_level=None,
        include_files=True,
        include_dirs=True,
    ):
        """
        Stream the tree directly into an already opened file.

        Example:

            with open("tree.txt", "w", encoding="utf-8") as f:
                exporter.stream_tree_to_file(root, f)

        Nothing is accumulated in memory.
        """

        if start_node is None:
            return

        for line in self._iter_lines(
            start_node,
            node_filter=node_filter,
            max_level=max_level,
            include_files=include_files,
            include_dirs=include_dirs,
        ):
            file.write(line)
            file.write("\n")

    # ==========================================================
    # Line generator
    # ==========================================================

    def _iter_lines(
        self,
        start_node: TreeNode,
        *,
        node_filter=None,
        max_level=None,
        include_files=True,
        include_dirs=True,
    ):
        """
        Generate exported lines one at a time.

        Does not build the complete output in memory.
        """

        # branch_state[level] tells us whether the node at that
        # level was the last sibling.
        branch_state = []

        # Explicit stack instead of recursion.
        #
        # Each item:
        #     (node, is_last, is_start_node)
        #
        stack = [(start_node, True, True)]
        while stack:
            node, is_last, is_start_node = stack.pop()
            # --------------------------------------------------
            # Level limit
            # --------------------------------------------------
            if max_level is not None and node.level > max_level:
                continue
            # --------------------------------------------------
            # Update branch state
            # --------------------------------------------------
            if node.level >= len(branch_state):
                branch_state.extend(
                    [True] * (node.level - len(branch_state) + 1)
                )
            branch_state[node.level] = is_last
            # --------------------------------------------------
            # Decide whether node is printable
            # --------------------------------------------------
            include_node = True
            if node.i_am == "file" and not include_files:
                include_node = False
            if node.i_am == "dir" and not include_dirs:
                include_node = False
            if node_filter is not None:
                if not node_filter(node):
                    include_node = False
            # --------------------------------------------------
            # Render node
            # --------------------------------------------------
            if include_node:
                yield self.get_single_node_line_text(node,is_last,branch_state)

            # --------------------------------------------------
            # Stop descending at maximum level
            # --------------------------------------------------
            if (max_level is not None and node.level >= max_level):
                continue
            # --------------------------------------------------
            # Add children to stack in reverse order.
            #
            # This preserves normal left-to-right output.
            # --------------------------------------------------
            children = node.children
            for index in range(len(children) - 1, -1, -1):
                child = children[index]
                child_is_last = (index == len(children) - 1)
                stack.append((child, child_is_last, False))
                

class TableTextExporter:
    def __init__(self, fmap:FileMapCliManager):
        self.fmap = fmap
        self._fields_cache = {}

    def _get_fields(self, node: TreeNode) -> list[str]:
        """
        Return the database fields associated with a file node.

        Field definitions are cached by ``(node.db, node.map)`` because
        all file nodes belonging to the same database/map pair share
        the same database field order.
        """
        if not node:
            return []

        if node.i_am != "file":
            return []

        if not node.db or not node.map:
            return []

        cache_key = (node.db, node.map)

        if cache_key in self._fields_cache:
            return self._fields_cache[cache_key]

        fm = self.fmap.cma.get_file_map(node.db)

        if not fm:
            self._fields_cache[cache_key] = []
            return []

        fields = fm.db.get_column_list_of_table(node.map)

        self._fields_cache[cache_key] = fields

        return fields

    # ==========================================================
    # Public API
    # ==========================================================
    def dump_to_csv(
        self,
        filename,
        start_node: TreeNode,
        fields: list[str] | None = None,
        node_filter=None,
        max_level=None,
        delimiter=",",
        ):
        """
        Export file nodes to a CSV file.

        The data is streamed directly to the file. The complete
        table is never held in memory.

        Args:
            filename:
                Output filename.

            start_node:
                Node where the export starts.

            fields:
                List of field names to export. If None, all fields
                available on the file nodes are exported.

            node_filter:
                Optional callable(node) -> bool used to determine
                which file nodes are included.

            max_level:
                Optional maximum node level to traverse.

            delimiter:
                CSV field delimiter. Defaults to ",".
        """
        with open(filename, "w", encoding="utf-8", newline="") as f:
            self.stream_to_csv(start_node, f, fields=fields,
                node_filter=node_filter, max_level=max_level, delimiter=delimiter)

    def stream_to_csv(
        self,
        start_node: TreeNode,
        file,
        *,
        fields: list[str] | None = None,
        node_filter=None,
        max_level=None,
        delimiter=",",
    ):
        """
        Stream file-node data into an open CSV file.

        Args:
            start_node:
                Node where the export starts.

            file:
                Open text file object.

            fields:
                Field names to export.

            node_filter:
                Optional callable(node) -> bool.

            max_level:
                Optional maximum node level.

            delimiter:
                CSV field delimiter.
        """
        if start_node is None:
            return
        # ------------------------------------------------------
        # Determine fields
        # ------------------------------------------------------
        if fields is None:
            fields = self._get_fields(start_node)

        if not fields:
            return

        writer = csv.writer(
            file, delimiter=delimiter, lineterminator="\n")
        # ------------------------------------------------------
        # Header
        # ------------------------------------------------------
        writer.writerow(fields)
        # ------------------------------------------------------
        # Data
        # ------------------------------------------------------
        for node in self._iter_file_nodes(
            start_node,
            node_filter=node_filter,
            max_level=max_level,
            ):
            row = self._get_node_row(node, fields)
            writer.writerow(row)

    # ==========================================================
    # Node traversal
    # ==========================================================
    def _iter_file_nodes(
        self, start_node: TreeNode, *, node_filter=None, max_level=None):
        """
        Yield file nodes one at a time.

        Uses an explicit stack so traversal does not depend
        on Python recursion depth.
        """
        stack = [start_node]
        while stack:
            node = stack.pop()
            if node is None:
                continue
            # --------------------------------------------------
            # Level limit
            # --------------------------------------------------
            if (max_level is not None and node.level > max_level):
                continue
            # --------------------------------------------------
            # File nodes are table records
            # --------------------------------------------------
            if node.i_am == "file":
                if (node_filter is None or node_filter(node)):
                    yield node
                # Files normally have no children, but don't
                # assume that unless your tree guarantees it.
                continue
            # --------------------------------------------------
            # Stop descending at maximum level
            # --------------------------------------------------
            if (max_level is not None and node.level >= max_level):
                continue
            # --------------------------------------------------
            # Traverse children
            # --------------------------------------------------
            for child in reversed(node.children):
                stack.append(child)

    # ==========================================================
    # Field handling
    # ==========================================================
    def _parse_node_info(self, node: TreeNode) -> dict:
        """
        Convert the positional node.info data into a field
        dictionary using the database column order.
        """
        if not node:
            return {}
        if node.i_am != "file":
            return {}
        if not node.info:
            return {}
        fields = self._get_fields(node)
        if not fields:
            return {}
        return dict(zip(fields, node.info))

    # ==========================================================
    # Row generation
    # ==========================================================
    def get_node_row(self, node: TreeNode, fields: list[str]) -> list:
        """Api call for getting values out of a node"""
        self._get_node_row(node,fields)

    def _get_node_row(self, node: TreeNode, fields: list[str]) -> list:
        info = self._parse_node_info(node)
        row = []
        for field in fields:
            # --------------------------------------------------
            # Fields stored directly on TreeNode
            # --------------------------------------------------
            if hasattr(node, field):
                row.append(getattr(node, field))
                continue
            # --------------------------------------------------
            # Fields stored in node.info
            # --------------------------------------------------
            row.append(info.get(field, ""))
        return row


class TabulatedTableTextExporter:

    def __init__(self, fmap: FileMapCliManager):
        self.fmap = fmap
        self._fields_cache = {}

    def _get_fields(self, node: TreeNode) -> list[str]:
        """
        Return the database fields associated with a file node.

        Field definitions are cached by ``(node.db, node.map)`` because
        all file nodes belonging to the same database/map pair share
        the same database field order.
        """
        if not node:
            return []

        if node.i_am != "file":
            return []

        if not node.db or not node.map:
            return []

        cache_key = (node.db, node.map)
        if cache_key in self._fields_cache:
            return self._fields_cache[cache_key]

        fm = self.fmap.cma.get_file_map(node.db)
        if not fm:
            self._fields_cache[cache_key] = []
            return []
        
        fields = fm.db.get_column_list_of_table(node.map)
        self._fields_cache[cache_key] = fields
        return fields

    def iter_file_node_batches(
        self,
        start_node: TreeNode,
        batch_size: int = 100,
        node_filter=None,
        max_level=None,
    ):
        """
        Yield file nodes in batches.

        A batch ends when either ``batch_size`` is reached or the
        database/map pair changes. Therefore every yielded batch
        contains file nodes belonging to the same ``(db, map)`` pair.

        Args:
            start_node:
                Node where traversal starts.

            batch_size:
                Maximum number of file nodes in a batch.

            node_filter:
                Optional callable(node) -> bool.

            max_level:
                Optional maximum node level.

        Yields:
            list[TreeNode]:
                A homogeneous batch of file nodes.
        """
        if start_node is None:
            return

        batch = []
        batch_db = None
        batch_map = None
        stack = [start_node]
        while stack:
            node = stack.pop()
            if node is None:
                continue

            if (max_level is not None and node.level > max_level):
                continue
            # ------------------------------------------------------
            # File node
            # ------------------------------------------------------
            if node.i_am == "file":
                if (
                    node_filter is not None
                    and not node_filter(node)
                ):
                    continue
                node_pair = (node.db, node.map)
                # --------------------------------------------------
                # New database/map pair
                # --------------------------------------------------
                if batch and node_pair != (batch_db, batch_map):
                    yield batch
                    batch = []
                    batch_db = None
                    batch_map = None
                # --------------------------------------------------
                # Start new batch
                # --------------------------------------------------
                if not batch:
                    batch_db = node.db
                    batch_map = node.map
                batch.append(node)
                # --------------------------------------------------
                # Batch size reached
                # --------------------------------------------------
                if len(batch) >= batch_size:
                    yield batch

                    batch = []
                    batch_db = None
                    batch_map = None
                continue
            # ------------------------------------------------------
            # Don't descend beyond max level
            # ------------------------------------------------------
            if (max_level is not None and node.level >= max_level):
                continue
            # ------------------------------------------------------
            # Traverse children
            # ------------------------------------------------------
            for child in reversed(node.children):
                stack.append(child)
        # ----------------------------------------------------------
        # Remaining batch
        # ----------------------------------------------------------
        if batch:
            yield batch


    # ==========================================================
    # DataFrame creation
    # ==========================================================

    def batch_to_dataframe(self,nodes: list[TreeNode], fields: list[str]):
        """
        Convert one batch of file nodes into a DataFrame.
        """
        rows = [self._get_node_row(node, fields)
            for node in nodes]

        return pd.DataFrame(
            rows, columns=fields)

    # ==========================================================
    # Node fields
    # ==========================================================
    
    def _parse_node_info(self, node: TreeNode) -> dict:
        """
        Convert node.info into a dictionary using the database
        field order.
        """

        if not node:
            return {}

        if node.i_am != "file":
            return {}

        if not node.info:
            return {}

        fields = self._get_fields(node)

        if not fields:
            return {}

        return dict(zip(fields, node.info))

    def _get_node_row(self, node: TreeNode, fields: list[str]) -> list:
        """
        Return the requested field values for one file node.
        """
        info = self._parse_node_info(node)
        row = []
        for field in fields:
            # --------------------------------------------------
            # Direct TreeNode attribute
            # --------------------------------------------------
            if hasattr(node, field):
                row.append(getattr(node, field))
                continue

            # --------------------------------------------------
            # Database info stored in node.info
            # --------------------------------------------------
            row.append(info.get(field, ""))

        return row
    
    def dump_tabulated_to_file(
        self,
        filename,
        start_node: TreeNode,
        fields: list[str],
        batch_size: int = 100,
        node_filter=None,
        max_level=None,
        print_db_header=True,
        print_map_header=True,
    ):
        """
        Export file-node data as tabulated text.

        File nodes are processed in batches and each batch is formatted
        using pandas ``DataFrame.to_string()``. Optional database and map
        headers are written whenever the corresponding value changes.

        Args:
            filename:
                Output filename.

            start_node:
                Node where the export starts.

            fields:
                Fields/columns to include in the output.

            batch_size:
                Number of file nodes per DataFrame batch.

            node_filter:
                Optional callable receiving a TreeNode and returning True
                if the node should be exported.

            max_level:
                Optional maximum tree level to traverse.

            print_db_header:
                Print a ``Database: ...`` header when the database changes.

            print_map_header:
                Print a ``Map: ...`` header when the map changes.

        Returns:
            int:
                Number of file nodes written.
        """
        if start_node is None or not fields:
            return 0

        rows_written = 0
        first_batch = True
        previous_db = None
        previous_map = None

        with open(filename, "w", encoding="utf-8") as f:

            for nodes in self.iter_file_node_batches(
                start_node,
                batch_size=batch_size,
                node_filter=node_filter,
                max_level=max_level,
            ):
                if not nodes:
                    continue
                # --------------------------------------------------
                # Check database / map changes
                # --------------------------------------------------
                first_node = nodes[0]
                current_db = first_node.db
                current_map = first_node.map
                if current_db != previous_db:
                    if print_db_header:
                        if not first_batch:
                            f.write("\n")
                        f.write(f"Database: {current_db}\n")
                        f.write(f"Map: {current_map}\n")
                    previous_db = current_db
                    previous_map = None

                if current_map != previous_map and current_db != previous_db:
                    if print_map_header:f.write(f"Map: {current_map}\n")

                    previous_map = current_map

                # --------------------------------------------------
                # DataFrame
                # --------------------------------------------------
                df = self.batch_to_dataframe(nodes,fields)

                if df.empty:
                    continue

                f.write(df.to_string(index=False))
                f.write("\n")

                first_batch = False
                rows_written += len(df)

        return rows_written


class FileStructureJsonExporter:
    """
    Export the file structure represented by a loaded TreeNode hierarchy.

    The exporter operates only on the nodes currently present in the tree.
    It does not query the database to discover additional files.

    File nodes are processed in batches so that the intermediate
    FileStructure created for each batch remains bounded in size.

    The project's FileStructure merge functions are used to combine
    the individual batch structures.

    Notes:
        A FileStructure may contain dictionaries and lists. Lists are
        valid FileStructure containers according to the project's
        FileStructure representation.
    """

    def __init__(self, fmap: FileMapCliManager,log_callback=None):
        self.fmap = fmap
        self._fields_cache = {}
        self.log_callback=log_callback

    # ==========================================================
    # Field handling
    # ==========================================================

    def _get_fields(self, node:TreeNode) -> list[str]:
        """
        Return the database fields associated with a file node.

        Field definitions are cached by ``(node.db, node.map)`` because
        all file nodes belonging to the same database/map pair share
        the same database field order.
        """
        if not node:
            return []

        if node.i_am != "file":
            return []

        if not node.db or not node.map:
            return []

        cache_key = (node.db, node.map)

        if cache_key in self._fields_cache:
            return self._fields_cache[cache_key]

        fm = self.fmap.cma.get_file_map(node.db)

        if not fm:
            self._fields_cache[cache_key] = []
            return []

        fields = fm.db.get_column_list_of_table(node.map)

        self._fields_cache[cache_key] = fields

        return fields

    # ==========================================================
    # Node traversal
    # ==========================================================

    def _iter_file_nodes(
        self,
        start_node:TreeNode,
        *,
        node_filter=None,
        max_level=None,
    ):
        """
        Yield file nodes one at a time.

        Uses an explicit stack so traversal does not depend on
        Python recursion depth.
        """
        if start_node is None:
            return

        stack = [start_node]

        while stack:
            node = stack.pop()
            if node is None:
                continue
            # --------------------------------------------------
            # Level limit
            # --------------------------------------------------
            if (max_level is not None and node.level > max_level):
                continue

            # --------------------------------------------------
            # File node
            # --------------------------------------------------
            # if node.i_am == "file":
            if (node_filter is None or node_filter(node)):
                yield node
                # Files normally have no children.
                if node.i_am == "file":
                    continue
            # --------------------------------------------------
            # Stop descending beyond max level
            # --------------------------------------------------
            if (max_level is not None and node.level >= max_level):
                continue
            # --------------------------------------------------
            # Traverse children
            # --------------------------------------------------
            for child in reversed(node.children):
                stack.append(child)

    # ==========================================================
    # Batched traversal
    # ==========================================================

    def iter_file_node_batches(
        self,
        start_node:TreeNode,
        batch_size: int = 100,
        node_filter=None,
        max_level=None,
    ):
        """
        Yield file nodes in batches.

        A batch ends when either ``batch_size`` is reached or the
        database/map pair changes.

        Therefore every yielded batch contains file nodes belonging
        to the same ``(db, map)`` pair.

        Args:
            start_node:
                Node where traversal starts.

            batch_size:
                Maximum number of file nodes per batch.

            node_filter:
                Optional callable(node) -> bool.

            max_level:
                Optional maximum tree level.

        Yields:
            list:
                A homogeneous batch of file nodes.
        """
        if start_node is None:
            return
        if batch_size <= 0:
            raise ValueError("batch_size must be greater than zero")
        batch = []

        batch_db = None
        batch_map = None

        for node in self._iter_file_nodes(
            start_node,
            node_filter=node_filter,
            max_level=max_level,
            ):
            node_pair = (node.db, node.map)
            # --------------------------------------------------
            # Database/map changed.
            #
            # Finish the current batch before starting another
            # database/map pair.
            # --------------------------------------------------
            if batch and node_pair != (batch_db, batch_map):
                yield batch

                batch = []
                batch_db = None
                batch_map = None

            # --------------------------------------------------
            # Start a new batch
            # --------------------------------------------------
            if not batch:
                batch_db = node.db
                batch_map = node.map
            # only add file nodes...
            if node.i_am == "file":
                batch.append(node)

            # --------------------------------------------------
            # Batch full
            # --------------------------------------------------
            if len(batch) >= batch_size:
                yield batch

                batch = []
                batch_db = None
                batch_map = None

        # ------------------------------------------------------
        # Remaining nodes
        # ------------------------------------------------------
        if batch:
            yield batch

    # ==========================================================
    # Node info
    # ==========================================================

    def _parse_node_info(self, node) -> dict:
        """
        Convert the positional node.info data into a field
        dictionary using the database column order.
        """
        if not node:
            return {}

        if node.i_am != "file":
            return {}

        if not node.info:
            return {}

        fields = self._get_fields(node)

        if not fields:
            return {}

        return dict(zip(fields, node.info))
    
    # ==========================================================
    # Batch iterator
    # ==========================================================

    def iter_file_structure_batches(
        self,
        start_node,
        *,
        fields: list[str] | None = None,
        batch_size: int = 100,
        node_filter=None,
        max_level=None,
        ):
        """
        Yield FileStructure objects one batch at a time.

        This is the main memory-friendly API.

        Example:

            for fs_batch in exporter.iter_file_structure_batches(
                start_node,
                batch_size=500,
            ):
                process(fs_batch)

        A yielded value may be either:

            dict

        or:

            list

        because both are valid FileStructure representations.
        """
        if start_node is None:
            return

        for nodes in self.iter_file_node_batches(
            start_node,
            batch_size=batch_size,
            node_filter=node_filter,
            max_level=max_level,
        ):
            if not nodes:
                continue

            fs_batch = self._get_file_structure_batch(nodes, fields)

            if fs_batch:
                yield fs_batch

    # ==========================================================
    # Merge batch FileStructures
    # ==========================================================

    def merge_file_structure_batches(self, fs_batches):
        """
        Merge a sequence of FileStructure batches.

        ``merge_file_structure_lists()`` is the general merge
        operation because a FileStructure may itself be a list.

        The result is a valid FileStructure:

            dict
            or
            list
        """
        merged_list = []

        for fs_batch in fs_batches:
            if not fs_batch:
                continue
            # A dictionary is one FileStructure item.
            if isinstance(fs_batch, dict):
                batch_list = [fs_batch]
            # A list is already a FileStructure list.
            elif isinstance(fs_batch, list):
                batch_list = fs_batch
            else:
                continue

            if not merged_list:
                merged_list = list(batch_list)
                continue

            merged_list = self.fmap.fm.merge_file_structure_lists(
                merged_list, batch_list)

        # ------------------------------------------------------
        # Preserve the convenient dict representation when there
        # is only one structure.
        # ------------------------------------------------------
        if len(merged_list) == 1:
            return merged_list[0]

        return merged_list

    # ==========================================================
    # Public API
    # ==========================================================

    def dump_to_json(
        self,
        filename,
        start_node,
        fields: list[str] | None = None,
        batch_size: int = 100,
        node_filter=None,
        max_level=None,
    ):
        """
        Export loaded TreeNode data to a JSON FileStructure.

        Each batch is written as one item in a top-level FileStructure
        list. Since lists are valid FileStructures, the resulting JSON
        remains compatible with the FileStructure representation.

        Memory usage is bounded approximately by the size of one batch.
        """
        if start_node is None:
            return 0

        batches_written = 0

        with open(filename, "w", encoding="utf-8") as f:
            f.write("[\n")
            first_batch = True
            for fs_batch in self.iter_file_structure_batches(
                start_node,
                fields=fields,
                batch_size=batch_size,
                node_filter=node_filter,
                max_level=max_level,
            ):
                if not fs_batch:
                    continue

                if not first_batch:
                    f.write(",\n")

                json.dump(fs_batch, f, ensure_ascii=False, indent=2)
                first_batch = False
                batches_written += 1
            f.write("\n]")
        return batches_written
    
    # ==========================================================
    # Batch -> FileStructure
    # ==========================================================

    def _get_file_structure_batch(
        self,
        nodes: list[TreeNode],
        fields: list[str],
        ):
       
        if not nodes:
            return {}
        # --------------------------------------------------
        # DataFrame
        # --------------------------------------------------
        df = self.batch_to_dataframe(nodes,fields)
        
        if df.empty:
            return {}
        
        fields_2_tab = []

        for field in fields:
            if field in ("filename", "size"):
                continue
            fields_2_tab.append(field)

        FS=FileStructurer(df,fields_2_tab,log_callback=self.log_callback)
        fs_batch=FS.get_file_structure()
        node = nodes[0]
        node_db=self.fmap.fm.extract_filename(node.db)
        node_map=node.map

        if not node_db in node_map:
            fdb_dict={f"{node_db}::{node_map}":fs_batch}
        else: 
            fdb_dict={f"{node_map}":fs_batch}

        return fdb_dict
    
    def batch_to_dataframe(self,nodes: list[TreeNode], fields: list[str]):
        """
        Convert one batch of file nodes into a DataFrame.
        """
        rows = [self._get_node_row(node, fields)
            for node in nodes]

        return pd.DataFrame(
            rows, columns=fields)
    
    def _get_node_row(self, node: TreeNode, fields: list[str]) -> list:
        """
        Return the requested field values for one file node.
        """
        info = self._parse_node_info(node)
        row = []
        for field in fields:
            # --------------------------------------------------
            # Direct TreeNode attribute
            # --------------------------------------------------
            if hasattr(node, field):
                row.append(getattr(node, field))
                continue

            # --------------------------------------------------
            # Database info stored in node.info
            # --------------------------------------------------
            row.append(info.get(field, ""))

        return row

    
class ExporterHandler:

    def __init__(self, fmap: FileMapCliManager, 
                 export_request_dict, 
                 root_node: TreeNode,
                 style: ExportTreeStyle =None,
                 available_fields: list[ExportField]=None,
                 available_formats: list[ExportFormat]=None,
                 log_callback=None,
                 ):
        self.fmap = fmap
        self.export_request = export_request_dict
        self.root_node = root_node
        if not log_callback:
            log_callback=print
        self.log_callback=log_callback
        if isinstance(style, ExportTreeStyle):
            self.style = style
        else:
            self.style=DefaultExportStyle()
        if available_fields and isinstance(available_fields,list):
            self.available_fields=available_fields
            for av_field in self.available_fields:
                if not isinstance(av_field, ExportField):
                    raise TypeError(f"Fields must be ExportField type {type(ExportField)}")
        else:
            self.available_fields=DC_DEFAULT_FIELDS
        
        if available_formats and isinstance(available_formats,list):
            self.available_formats=available_formats
            for av_format in self.available_formats:
                if not isinstance(av_format, ExportFormat):
                    raise TypeError(f"Fields must be ExportField type {type(ExportFormat)}")
        else:
            self.available_formats=DC_DEFAULT_FORMATS
        
        self.available_selections = DC_DEFAULT_SELECTIONS

        self.filters = NodeExportFilters()
        self.tab_list_ex = TabulatedTableTextExporter(self.fmap)
        self.table_ex = TableTextExporter(self.fmap)
        self.tree_ex = TreeTextExporter(self.style)
        self.filestruct_ex = FileStructureJsonExporter(self.fmap,self.log_callback)
        self.filepath_target = None

        # self.do_export()
    
    def do_export(self)->tuple[bool,str]:
        try:
            selection=self.export_request.get("selection")
            format=self.export_request.get("format")
            fields=self.export_request.get("fields")
            self.filepath_target=self.export_request.get("target")

            field_list=[]
            for field in fields:
                for av_field in self.available_fields:
                    if not isinstance(av_field, ExportField):
                        continue
                    if av_field.id == field:
                        field_list.append(av_field.label)
                        break  
            
            format_obj=None
            for av_format in self.available_formats:
                if not isinstance(av_format, ExportFormat):
                    continue
                if av_format.value == format:
                    format_obj=ExportFormat(av_format.label,av_format.value,av_format.extension)
            
            if format_obj is None:
                raise ValueError(f"Unknown export format: {format}")
            sel_obj=None
            for av_sel in self.available_selections:
                if not isinstance(av_sel, ExportSelection):
                    continue
                if av_sel.value == selection:
                    sel_obj=ExportSelection(av_sel.label,av_sel.value)
            
            if format_obj.value == 'filestruct_json':
                # Do filestructure
                self._do_filestructure(selection,field_list)

            elif format_obj.value == 'list_txt':
                self._do_list_txt(selection, field_list)
            
            elif format_obj.value == 'list_csv':
                self._do_list_csv(selection, field_list)
            
            elif format_obj.value == 'text_tree':
                self._do_tree_txt(selection)
        except (PermissionError,FileExistsError,RuntimeError,ReferenceError,ValueError) as eee:
            return False, str(eee)
        return True, f"Format: {format_obj.label}\nSelection: {sel_obj.label}"

    def _do_tree_txt(self, selection):
        if selection == 'directory_tree':
            self.tree_ex.dump_tree_to_file(filename=self.filepath_target,
                                           start_node=self.root_node,
                                            node_filter=self.filters.container,
                                            max_level=None,
                                            include_files=False,
                                            include_dirs=True,
                                            log_callback=self.log_callback)

        if selection == 'file_tree':
            self.tree_ex.dump_tree_to_file(filename=self.filepath_target,
                                           start_node=self.root_node,
                                            node_filter=self.filters.all,
                                            max_level=None,
                                            include_files=True,
                                            include_dirs=True,
                                            log_callback=self.log_callback)

        if selection == 'selected':
            self.tree_ex.dump_tree_to_file(filename=self.filepath_target,
                                           start_node=self.root_node,
                                            node_filter=self.filters.selected,
                                            max_level=None,
                                            include_files=True,
                                            include_dirs=True,
                                            log_callback=self.log_callback)

        if selection == 'expanded':
            self.tree_ex.dump_tree_to_file(filename=self.filepath_target,
                                           start_node=self.root_node,
                                            node_filter=self.filters.expanded,
                                            max_level=None,
                                            include_files=True,
                                            include_dirs=True,
                                            log_callback=self.log_callback)

    def _do_list_txt(self, selection,field_list):
        batch_size = self.fmap.cfg.export.get("batch_size",100)
        print_db_header = self.fmap.cfg.export.get("print_database_header",True)
        print_map_header = self.fmap.cfg.export.get("print_map_header",True)
        if selection == 'directory_tree':
            self.tab_list_ex.dump_tabulated_to_file(filename=self.filepath_target,
                                      start_node=self.root_node,
                                      fields=field_list, 
                                      batch_size=batch_size,
                                      node_filter=self.filters.container,
                                      max_level=None,
                                      print_db_header=print_db_header,
                                      print_map_header=print_map_header,
                                      ) 

        if selection == 'file_tree':
            self.tab_list_ex.dump_tabulated_to_file(filename=self.filepath_target,
                                      start_node=self.root_node,
                                      fields=field_list, 
                                      batch_size=batch_size,
                                      node_filter=self.filters.all,
                                      max_level=None,
                                      print_db_header=print_db_header,
                                      print_map_header=print_map_header,
                                      ) 

        if selection == 'selected':
            self.tab_list_ex.dump_tabulated_to_file(filename=self.filepath_target,
                                      start_node=self.root_node,
                                      fields=field_list, 
                                      batch_size=batch_size,
                                      node_filter=self.filters.selected,
                                      max_level=None,
                                      print_db_header=print_db_header,
                                      print_map_header=print_map_header,
                                      ) 

        if selection == 'expanded':
            self.tab_list_ex.dump_tabulated_to_file(filename=self.filepath_target,
                                      start_node=self.root_node,
                                      fields=field_list, 
                                      batch_size=batch_size,
                                      node_filter=self.filters.expanded,
                                      max_level=None,
                                      print_db_header=print_db_header,
                                      print_map_header=print_map_header,
                                      ) 

    def _do_list_csv(self, selection,field_list,delimiter=None):
        c_deli = self.fmap.cfg.export.get("csv_delimeter")
        if not delimiter and c_deli:
            delimiter = c_deli
        elif not delimiter and not c_deli:
            delimiter=","

        if selection == 'directory_tree':
            self.table_ex.dump_to_csv(filename=self.filepath_target,
                                      start_node=self.root_node,
                                      fields=field_list,
                                      node_filter=self.filters.container,
                                      max_level=None,
                                      delimiter=delimiter,
                                      )

        if selection == 'file_tree':
            self.table_ex.dump_to_csv(filename=self.filepath_target,
                                      start_node=self.root_node,
                                      fields=field_list,
                                      node_filter=self.filters.all,
                                      max_level=None,
                                      delimiter=delimiter,
                                      )

        if selection == 'selected':
            self.table_ex.dump_to_csv(filename=self.filepath_target,
                                      start_node=self.root_node,
                                      fields=field_list,
                                      node_filter=self.filters.selected,
                                      max_level=None,
                                      delimiter=delimiter,
                                      )

        if selection == 'expanded':
            self.table_ex.dump_to_csv(filename=self.filepath_target,
                                      start_node=self.root_node,
                                      fields=field_list,
                                      node_filter=self.filters.expanded,
                                      max_level=None,
                                      delimiter=delimiter,
                                      )

    def _do_filestructure(self, selection,field_list=None):
        """
        Export the currently loaded TreeNode structure as a
        FileStructure JSON file.

        Unlike the map exporter, this operates only on the nodes
        available in ``self.root_node``.
        """
        batch_size = self.fmap.cfg.export.get("batch_size", 100)
        if selection == "directory_tree":
            # no directory filestructure -> same as file tree
            self.filestruct_ex.dump_to_json(
                filename=self.filepath_target,
                start_node=self.root_node,
                batch_size=batch_size,
                fields=field_list,
                node_filter=self.filters.all,
                max_level=None,
            )

        elif selection == "file_tree":
            self.filestruct_ex.dump_to_json(
                filename=self.filepath_target,
                start_node=self.root_node,
                batch_size=batch_size,
                fields=field_list,
                node_filter=self.filters.all,
                max_level=None,
            )

        elif selection == "selected":
            self.filestruct_ex.dump_to_json(
                filename=self.filepath_target,
                start_node=self.root_node,
                batch_size=batch_size,
                fields=field_list,
                node_filter=self.filters.selected,
                max_level=None,
            )

        elif selection == "expanded":
            self.filestruct_ex.dump_to_json(
                filename=self.filepath_target,
                start_node=self.root_node,
                batch_size=batch_size,
                fields=field_list,
                node_filter=self.filters.expanded,
                max_level=None,
            )


