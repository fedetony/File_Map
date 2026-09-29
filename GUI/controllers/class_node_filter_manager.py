from dataclasses import dataclass
from typing import Callable, Any
from datetime import datetime
import re

from controllers.class_tree_node_manager import TreeNode,TreeManager
from controllers.class_filemap_cli_manager import FileMapCliManager

def compile_regex(value):
    """
    Compile a regex value.

    Returns:
        compiled re.Pattern or None

    Raises:
        ValueError: invalid regular expression
    """

    if not value:
        return None

    if hasattr(value, "search"):
        return value

    try:
        return re.compile(str(value), re.IGNORECASE)
    except re.error as eee:
        raise ValueError(f"Invalid regular expression: {eee}")
    
@dataclass
class NodeFilter:
    """
    Definition and state of a tree-node filter.
    """

    id: str
    name: str
    value: Any
    predicate: Callable[[Any, Any], bool]

    enabled: bool = True
    description: str = ""
    msg: str = "" # warnings errors to user

    # Optional callback used to validate/prepare the value.
    validator: Callable[[Any], Any] | None = None

    # Optional callback for GUI/display purposes.
    formatter: Callable[[Any], str] | None = None

    def set_value(self, value):
        """Set filter value, optionally passing through validator."""

        if self.validator is not None:
            value = self.validator(value)

        self.value = value

    def matches(self, node:TreeNode) -> bool:
        """Return True if node passes this filter."""

        if not self.enabled:
            return True

        return bool(self.predicate(node, self.value))

    def display_value(self) -> str:
        """Return value formatted for GUI display."""

        if self.formatter is not None:
            return self.formatter(self.value)

        return str(self.value)

@dataclass
class FilterNode:
    filter_id: str

@dataclass
class AndNode:
    children: list

@dataclass
class OrNode:
    children: list

FilterExpression = FilterNode | AndNode | OrNode    

class NodeFilterManager:

    def __init__(self):
        self._filters: dict[str, NodeFilter] = {}
        self._expression: FilterExpression | None = None

    # ---------------------------------------------------------
    # Add
    # ---------------------------------------------------------

    def add_filter(
        self,
        id: str,
        name: str,
        value: Any,
        predicate: Callable[[Any, Any], bool],
        enabled: bool = True,
        description: str = "",
        validator: Callable[[Any], Any] | None = None,
    ) -> NodeFilter:

        if id in self._filters:
            raise ValueError(f"Filter id already exists: {id}")

        node_filter = NodeFilter(
            id=id,
            name=name,
            value=value,
            predicate=predicate,
            enabled=enabled,
            description=description,
            validator=validator,
        )

        self._filters[id] = node_filter

        return node_filter

    # ---------------------------------------------------------
    # Remove
    # ---------------------------------------------------------

    def remove_filter(self, id: str) -> bool:
        """
        Remove a filter by ID.

        Returns:
            True if the filter existed and was removed.
            False if the ID didn't exist.
        """
        if id not in self._filters:
            return False

        del self._filters[id]
        return True

    def remove_all(self):
        """Remove all filters."""
        self._filters.clear()

    # ---------------------------------------------------------
    # Get
    # ---------------------------------------------------------

    def get_filter(self, id: str) -> NodeFilter | None:
        """Get a filter by ID."""
        return self._filters.get(id)

    def get_filter_by_name(self, name: str) -> NodeFilter | None:
        """Get the first filter having the specified name."""
        for node_filter in self._filters.values():
            if node_filter.name == name:
                return node_filter

        return None

    def get_filters(self) -> list[NodeFilter]:
        """Return all filters."""
        return list(self._filters.values())

    def get_filter_ids(self) -> list[str]:
        """Return all filter IDs."""
        return list(self._filters.keys())

    # ---------------------------------------------------------
    # Exists
    # ---------------------------------------------------------

    def has_filter(self, id: str) -> bool:
        """Check whether a filter ID exists."""
        return id in self._filters

    # ---------------------------------------------------------
    # ID
    # ---------------------------------------------------------

    def set_id(self, old_id: str, new_id: str) -> bool:
        """
        Change a filter ID.

        The filter object itself is updated as well.

        Returns:
            True if successful.
            False if old_id doesn't exist.
        """
        if old_id not in self._filters:
            return False

        if new_id in self._filters:
            raise ValueError(f"Filter id already exists: {new_id}")

        node_filter = self._filters.pop(old_id)
        node_filter.id = new_id
        self._filters[new_id] = node_filter

        return True

    # ---------------------------------------------------------
    # Name
    # ---------------------------------------------------------

    def set_name(self, id: str, name: str) -> bool:
        """Change the display name of a filter."""
        node_filter = self.get_filter(id)
        if node_filter is None:
            return False

        node_filter.name = name
        return True

    # ---------------------------------------------------------
    # Value
    # ---------------------------------------------------------
    def set_value(self, id: str, value: Any) -> bool:
        """Change the value of a filter."""
        node_filter = self.get_filter(id)

        if node_filter is None:
            return False

        node_filter.set_value(value)
        return True


    def get_value(self, id: str) -> Any:
        """Get the current value of a filter."""
        node_filter = self.get_filter(id)
        if node_filter is None:
            return None

        return node_filter.value

    # ---------------------------------------------------------
    # Enabled
    # ---------------------------------------------------------

    def set_enabled(self, id: str, enabled: bool) -> bool:
        """Enable or disable a filter."""
        node_filter = self.get_filter(id)
        if node_filter is None:
            return False
        node_filter.enabled = enabled
        return True

    def enable(self, id: str) -> bool:
        return self.set_enabled(id, True)

    def disable(self, id: str) -> bool:
        return self.set_enabled(id, False)

    def is_enabled(self, id: str) -> bool:
        node_filter = self.get_filter(id)
        if node_filter is None:
            return False
        return node_filter.enabled
    
    def enable_all(self,enable=True):
        filters=self.get_filters()
        for a_filter in filters:
            a_filter.enabled = enable

    # ---------------------------------------------------------
    # Matching
    # ---------------------------------------------------------
    def matches(self, node:TreeNode) -> bool:
        """
        Return True when the node passes all enabled filters.
        """
        if self._expression is None:
            return True

        return self._matches_expression(node, self._expression)

    def visible(self, node:TreeNode) -> bool:
        """
        Alias for matches().
        """
        return self.matches(node) 
    
    # =========================================================
    # EVALUATION
    # =========================================================

    def _matches_expression(self, node:TreeNode, expression):
        if isinstance(expression, FilterNode):

            node_filter = self.get_filter(expression.filter_id)
            if node_filter is None:
                return False

            return node_filter.matches(node)

        if isinstance(expression, AndNode):
            return all(
                self._matches_expression(node, child)
                for child in expression.children
            )

        if isinstance(expression, OrNode):
            return any(
                self._matches_expression(node, child)
                for child in expression.children
            )

        raise TypeError(
            f"Unknown filter expression type: "
            f"{type(expression).__name__}"
        )


    # =========================================================
    # EXPRESSION
    # =========================================================
    def set_expression(self, expression: FilterExpression | None ):
        self._validate_expression(expression)
        self._expression = expression

    def get_expression(self):
        return self._expression

    def clear_expression(self):
        self._expression = None
    
    def _validate_expression(self, expression:FilterExpression | None ):
        if expression is None:
            return

        if isinstance(expression, FilterNode):
            if not self.has_filter(expression.filter_id):
                raise ValueError(
                    f"Unknown filter ID: "
                    f"{expression.filter_id!r}"
                )
            return

        if isinstance(expression, (AndNode, OrNode)):
            if not expression.children:
                raise ValueError(
                    "Expression node has no children."
                )
            for child in expression.children:
                self._validate_expression(child)
            return

        raise TypeError(
            f"Unknown filter expression type: "
            f"{type(expression).__name__}"
        )

# Usage:
# filters = NodeFilterManager()

# filters.add_filter(
#     name="Show Hidden Files",
#     value=False,
#     predicate=lambda node, value:
#         value or not (
#             node.i_am == "dir" and
#             node.name.startswith(".")
#         )
# )

class TreeFilterHelper:
    """
    Filtering helper for TreeManager / TreeNode.

    This class provides predefined filters for common TreeNode
    properties and allows arbitrary custom filters.

    Qt-independent.
    """
    _DATE_FIELDS = {
        "dt_data_created",
        "dt_data_modified",
        "dt_file_created",
        "dt_file_modified",
        "dt_file_accessed",
    }

    def __init__(self, fmap:FileMapCliManager, tree_manager:TreeManager, filter_manager=None, log_callback=None):
        self.fmap = fmap
        self.tree_manager = tree_manager
        self._fields_cache={}

        if not log_callback:
            self.log_callback=print
        else:
            self.log_callback=log_callback

        if filter_manager is None:
            filter_manager = NodeFilterManager()

        self.filters = filter_manager

        self._register_default_filters()

    # =========================================================
    # DEFAULT FILTERS
    # =========================================================

    def _register_default_filters(self):
        """Register the standard TreeNode filters."""
        self._predicate_map = {
            "size": self._filter_size,
            "name": self._filter_name_contains,
            "name_contains": self._filter_name_contains,
            "name_startswith": self._filter_name_starts_with,
            "name_endswith": self._filter_name_ends_with,
            "name_regex": self._filter_name_regex,
            "path_contains": self._filter_path_contains,
            "path_regex": self._filter_path_regex,
            "extension": self._filter_extension,
            "hidden_folders": self._filter_hidden,
            "date": self._filter_date,
            "type": self._filter_type,
        }
        self._validator_map = {
            "name_regex": self._validate_regex,
            "path_regex": self._validate_regex,
        }

        # self.filters.add_filter(
        #     id="show_hidden",
        #     name="Show Hidden Files",
        #     value=True,
        #     predicate=self._filter_hidden,
        # )

        # self.filters.add_filter(
        #     id="name_contains",
        #     name="Name Contains",
        #     value="",
        #     predicate=self._filter_name_contains,
        # )

        # self.filters.add_filter(
        #     id="name_starts_with",
        #     name="Name Starts With",
        #     value="",
        #     predicate=self._filter_name_starts_with,
        # )

        # self.filters.add_filter(
        #     id="name_ends_with",
        #     name="Name Ends With",
        #     value="",
        #     predicate=self._filter_name_ends_with,
        # )

        # self.filters.add_filter(
        #     id="path_contains",
        #     name="Path Contains",
        #     value="",
        #     predicate=self._filter_path_contains,
        # )

        # self.filters.add_filter(
        #     id="extension",
        #     name="Extension",
        #     value="",
        #     predicate=self._filter_extension,
        # )

        # self.filters.add_filter(
        #     id="size",
        #     name="Size",
        #     value=None,
        #     predicate=self._filter_size,
        # )

        # self.filters.add_filter(
        #     id="date",
        #     name="Date",
        #     value=None,
        #     predicate=self._filter_date,
        # )

        # self.filters.add_filter(
        #     id="type",
        #     name="Type",
        #     value="",
        #     predicate=self._filter_type,
        # )

        # self.filters.add_filter(
        #     id="name_regex",
        #     name="Name Matches Regex",
        #     value="",
        #     predicate=self._filter_name_regex,
        #     validator=self._validate_regex,
        # )

        # self.filters.add_filter(
        #     id="path_regex",
        #     name="Path Matches Regex",
        #     value="",
        #     predicate=self._filter_path_regex,
        #     validator=self._validate_regex,
        # )

    def build_filter(
        self,
        id,
        name,
        filter_type: str,
        value,
        description="",
    ) -> bool:

        predicate = self._predicate_map.get(filter_type)

        if predicate is None:
            self.log_callback(
                f"Adding Filter: Unknown filter type: {filter_type!r}"
            )
            return False

        validator = self._validator_map.get(filter_type)

        try:
            self.filters.add_filter(
                id=id,
                name=name,
                value=value,
                predicate=predicate,
                enabled=True,
                description=description,
                validator=validator,
            )

            return True

        except ValueError as eee:
            self.log_callback(f"Adding Filter: {eee}")
            return False


    def remove_filter(self, id) -> bool:
        """Remove a filter"""
        return self.filters.remove_filter(id)
    
    def remove_all_filters(self) -> bool:
        """Remove a filter"""
        return self.filters.remove_all()

    # =========================================================
    # BASIC HELPERS
    # =========================================================

    @staticmethod
    def _text(value) -> str:
        if value is None:
            return ""

        return str(value)

    @staticmethod
    def _normalize_text(value) -> str:
        return TreeFilterHelper._text(value).casefold()

    # =========================================================
    # HIDDEN
    # =========================================================

    @staticmethod
    def _filter_hidden(node:TreeNode, show_hidden):
        """
        show_hidden=True:
            everything is allowed.

        show_hidden=False:
            names beginning with '.' are hidden.
        """

        if show_hidden:
            return True

        return not str(node.name).startswith(".")

    # =========================================================
    # NAME
    # =========================================================

    @staticmethod
    def _filter_name_contains(node:TreeNode, value):

        if not value:
            return True

        return (
            TreeFilterHelper._normalize_text(value)
            in TreeFilterHelper._normalize_text(node.name)
        )

    @staticmethod
    def _filter_name_starts_with(node:TreeNode, value):

        if not value:
            return True

        return TreeFilterHelper._normalize_text(
            node.name
        ).startswith(
            TreeFilterHelper._normalize_text(value)
        )

    @staticmethod
    def _filter_name_ends_with(node:TreeNode, value):

        if not value:
            return True

        return TreeFilterHelper._normalize_text(
            node.name
        ).endswith(
            TreeFilterHelper._normalize_text(value)
        )

    # =========================================================
    # PATH
    # =========================================================

    @staticmethod
    def _filter_path_contains(node:TreeNode, value):

        if not value:
            return True

        return (
            TreeFilterHelper._normalize_text(value)
            in TreeFilterHelper._normalize_text(node.path)
        )

    # =========================================================
    # EXTENSION
    # =========================================================

    @staticmethod
    def _filter_extension(node:TreeNode, value):

        if not value:
            return True

        if node.i_am != "file":
            return True
        
        filename = TreeFilterHelper._text(node.name)

        extension = ""

        if "." in filename:
            extension = filename.rsplit(".", 1)[1]

        extension = extension.casefold()

        if isinstance(value, (list, tuple, set)):
            wanted_extensions = {
                TreeFilterHelper._text(x)
                .strip()
                .lstrip(".")
                .casefold()
                for x in value
            }

            return extension in wanted_extensions

        wanted = (
            TreeFilterHelper._text(value)
            .strip()
            .lstrip(".")
            .casefold()
        )

        return extension == wanted


    # =========================================================
    # TYPE
    # =========================================================

    @staticmethod
    def _filter_type(node:TreeNode, value):

        if not value:
            return True

        return TreeFilterHelper._normalize_text(
            node.i_am
        ) == TreeFilterHelper._normalize_text(value)

    # =========================================================
    # REGEX
    # =========================================================
    def _validate_regex(self, value):
        try:
            return compile_regex(value)
        except ValueError as eee:
            self.log_callback(f"Regex Error: {eee}")
            return None

    def _filter_name_regex(self, node:TreeNode, pattern:re.Pattern):
        """
        Filter node names using a regular expression.

        Empty pattern = filter disabled logically, so everything passes.
        Invalid regex = False.
        """
        if pattern is None:
            return True

        return pattern.search(str(node.name)) is not None


    def _filter_path_regex(self, node:TreeNode, pattern:re.Pattern):
        """
        Filter node paths using a regular expression.

        Empty pattern = filter disabled logically, so everything passes.
        Invalid regex = False.
        """
        if pattern is None:
            return True

        return pattern.search(str(node.path or "")) is not None


    # =========================================================
    # SIZE
    # =========================================================

    @staticmethod
    def _filter_size(node:TreeNode, value):
        """
        value can be:

            None
            100
            (">", 100)
            (">=", 100)
            ("<", 100)
            ("<=", 100)
            ("==", 100)
            ("!=", 100)
        """

        if value is None:
            return True

        if node.size is None:
            return False

        if isinstance(value, tuple):
            operator, target = value
        else:
            operator = "=="
            target = value

        try:
            size = float(node.size)
            target = float(target)
        except (TypeError, ValueError):
            return False

        return TreeFilterHelper._compare(
            size,
            operator,
            target,
        )

    # =========================================================
    # NODE DATA / FIELD RESOLUTION
    # =========================================================

    def _get_node_value(self, node, field):
        """
        Get a logical field value from a TreeNode.

        Resolution order:

            1. Direct TreeNode attribute
            2. node.info as a dictionary
            3. Database-backed node.info using db/map field definitions

        Returns:
            The field value, or None if unavailable.
        """

        if node is None:
            return None

        # -----------------------------------------------------
        # Direct TreeNode attribute
        # -----------------------------------------------------

        if hasattr(node, field):
            value = getattr(node, field)

            if value is not None:
                return value

        # -----------------------------------------------------
        # node.info as dictionary
        #
        # Useful for Explorer nodes.
        # -----------------------------------------------------

        info = getattr(node, "info", None)

        if isinstance(info, dict):
            if field in info:
                return info[field]

        # -----------------------------------------------------
        # Database-backed positional info
        #
        # Only attempt this when the node actually belongs
        # to a database/map.
        # -----------------------------------------------------

        if (
            getattr(node, "db", None)
            and getattr(node, "map", None)
            and info
        ):
            fields = self._get_database_fields(node)

            if field in fields:
                index = fields.index(field)

                if index < len(info):
                    return info[index]

        return None
    
    def _get_database_fields(self, node:TreeNode):
        """
        Return database field names for a database-backed node.

        The TreeFilterHelper can optionally use this to interpret
        positional node.info data.
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

        try:
            fm = self.fmap.cma.get_file_map(node.db)
            if not fm:
                self._fields_cache[cache_key] = []
                return []
            fields = fm.db.get_column_list_of_table(node.map)

        except Exception as eee:
            self.log_callback(
                f"Getting database fields: {eee}"
            )
            fields = []

        self._fields_cache[cache_key] = fields

        return fields


    # =========================================================
    # DATE
    # =========================================================
    def _validate_date_filter(self, value):
        try:
            field, operator, target = value
        except (TypeError, ValueError):
            raise ValueError(
                "Date filter must be "
                "(field, operator, value)"
            )

        if field not in self._DATE_FIELDS:
            raise ValueError(
                f"Unknown date field: {field!r}"
            )

        if operator not in {
            "==", "!=", ">", ">=", "<", "<="
        }:
            raise ValueError(
                f"Invalid date operator: {operator!r}"
            )

        target = self._parse_datetime(target)

        if target is None:
            raise ValueError(
                f"Invalid date value: {target!r}"
            )

        return field, operator, target

    def _filter_date(self, node, value):
        """
        Date filter.

        value:

            ("dt_file_modified", ">", datetime)
            ("dt_file_created", ">=", datetime)
            ("dt_file_accessed", "<", datetime)
            ("dt_data_created", "==", datetime)
            ("dt_data_modified", "!=", datetime)
        """

        if value is None:
            return True

        try:
            field, operator, target = value
        except (TypeError, ValueError):
            return False

        node_value = self._get_node_value(node, field)

        if node_value is None:
            return False

        node_value = self._parse_datetime(node_value)

        if node_value is None:
            return False

        target = self._parse_datetime(target)

        if target is None:
            return False

        return self._compare(
            node_value,
            operator,
            target,
        )

    # =========================================================
    # COMPARISON
    # =========================================================
    @staticmethod
    def _compare(value, operator, target):

        if operator == "==":
            return value == target

        if operator == "!=":
            return value != target

        if operator == ">":
            return value > target

        if operator == ">=":
            return value >= target

        if operator == "<":
            return value < target

        if operator == "<=":
            return value <= target

        return False

    # =========================================================
    # DATE EXTRACTION
    # =========================================================
    @staticmethod
    def _parse_datetime(value):
        if isinstance(value, datetime):
            return value

        if value is None:
            return None

        try:
            return datetime.fromisoformat(str(value))
        except (TypeError, ValueError):
            return None


    def _get_node_date(self, node):
        """
        Get the most appropriate date from a node.

        Supports both Explorer and database-backed nodes.
        """

        for field in (
            "date",
            "datetime",
            "modified",
            "mtime",
            "date_modified",
        ):
            value = self._get_node_value(node, field)

            if value is None:
                continue

            value = self._parse_datetime(value)

            if value is not None:
                return value

        return None

    
    # =========================================================
    # NODE FILTERING
    # =========================================================

    def matches(self, node:TreeNode):
        """Return True if the node passes all active filters."""
        return self.filters.matches(node)

    def visible(self, node):
        """Alias for matches()."""
        return self.matches(node)

    # =========================================================
    # TREE OPERATIONS
    # =========================================================

    def filter_nodes(self, nodes)->list[TreeNode]:
        """
        Filter an iterable of TreeNodes.

        Returns a list.
        """

        return [
            node
            for node in nodes
            if self.matches(node)
        ]

    def filter_selection(self, nodes:list[TreeNode]=None):
        """
        Return selected nodes that also pass the filters.

        If nodes is None, obtain nodes from the TreeManager.
        """
        if nodes is None:
            nodes = self._get_selected_nodes()

        return [
            node
            for node in nodes
            if node.selected and self.matches(node)
        ]

    def filter_selected(self, nodes:list[TreeNode]=None):
        """Alias for filter_selection()."""
        return self.filter_selection(nodes)

    def _get_selected_nodes(self):
        """
        Get all selected nodes from the TreeManager.
        """
        return self.tree_manager.get_selected_nodes()

