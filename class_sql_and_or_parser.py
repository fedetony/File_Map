from dataclasses import dataclass
from typing import Union


# ============================================================
# Query expression nodes
# ============================================================

@dataclass
class QueryNode:
    """A leaf query, e.g. 'filename ~= foo'."""
    text: str

@dataclass
class AndNode:
    """Logical AND of child expressions."""
    children: list

@dataclass
class OrNode:
    """Logical OR of child expressions."""
    children: list

@dataclass
class OperationNode:
    operation: str
    operator: str
    query_text: str
    is_valid: bool = True

QueryExpression = Union[QueryNode, AndNode, OrNode]

# ============================================================
# AND / OR parser
# ============================================================

class QueryExpressionParser:
    """
    Parses expressions containing:

        &&      AND
        ||      OR
        ( )     grouping

    AND has higher precedence than OR.

    Examples:

        foo && bar

        foo || bar

        foo || bar && baz
        -> foo || (bar && baz)

        (foo || bar) && baz

        foo && (bar || baz)
    """

    def __init__(self, text):
        self.text = text
        self.pos = 0
        self.length = len(text)

    # --------------------------------------------------------
    # Public entry point
    # --------------------------------------------------------

    def parse(self):
        self._skip_spaces()

        if self.pos >= self.length:
            return QueryNode("")

        result = self._parse_or()

        self._skip_spaces()

        if self.pos < self.length:
            raise ValueError(
                f"Unexpected text at position {self.pos}: "
                f"{self.text[self.pos:]!r}"
            )

        return result

    # --------------------------------------------------------
    # OR has the lowest precedence
    #
    # expression:
    #     and_expression ('||' and_expression)*
    # --------------------------------------------------------

    def _parse_or(self):
        children = [self._parse_and()]

        while True:
            self._skip_spaces()

            if self._is_boolean_operator("||"):
                self.pos += 2
                children.append(self._parse_and())
            else:
                break

        if len(children) == 1:
            return children[0]

        return OrNode(children)

    # --------------------------------------------------------
    # AND has higher precedence than OR
    #
    # and_expression:
    #     primary ('&&' primary)*
    # --------------------------------------------------------

    def _parse_and(self):
        children = [self._parse_primary()]

        while True:
            self._skip_spaces()

            if self._is_boolean_operator("&&"):
                self.pos += 2
                children.append(self._parse_primary())
            else:
                break

        if len(children) == 1:
            return children[0]

        return AndNode(children)

    # --------------------------------------------------------
    # Primary expression:
    #
    #     '(' expression ')'
    #     query
    # --------------------------------------------------------

    def _parse_primary(self):
        self._skip_spaces()

        if self._match("("):
            expression = self._parse_or()

            self._skip_spaces()

            if not self._match(")"):
                raise ValueError(
                    f"Missing ')' at position {self.pos} "
                    f"in {self.text!r}"
                )

            return expression

        return self._parse_query()

    # --------------------------------------------------------
    # Parse a leaf query.
    #
    # Everything until a valid &&, ||, or ')' belongs
    # to the query.
    # --------------------------------------------------------

    def _parse_query(self):
        start = self.pos

        while self.pos < self.length:
            if self._is_boolean_operator("&&"):
                break

            if self._is_boolean_operator("||"):
                break

            if self.text[self.pos] == ")":
                break

            self.pos += 1

        query = self.text[start:self.pos].strip()

        if not query:
            raise ValueError(
                f"Expected query at position {start} "
                f"in {self.text!r}"
            )

        return QueryNode(query)

    # --------------------------------------------------------
    # Helpers
    # --------------------------------------------------------

    def _skip_spaces(self):
        while (
            self.pos < self.length
            and self.text[self.pos].isspace()
        ):
            self.pos += 1

    def _match(self, value):
        if self.text.startswith(value, self.pos):
            self.pos += len(value)
            return True

        return False

    def _is_boolean_operator(self, operator):
        if not self.text.startswith(operator, self.pos):
            return False

        left_ok = (
            self.pos == 0
            or self.text[self.pos - 1].isspace()
            or self.text[self.pos - 1] == "("
        )

        right_pos = self.pos + len(operator)

        right_ok = (
            right_pos >= self.length
            or self.text[right_pos].isspace()
            or self.text[right_pos] in "()"
        )

        return left_ok and right_ok


# ============================================================
# Convenience function
# ============================================================

def parse_query_expression(text):
    """
    Parse a query expression into QueryNode / AndNode / OrNode.

    Raises ValueError when the expression is malformed.
    """
    return QueryExpressionParser(text).parse()


# ============================================================
# SQL generation
# ============================================================

def expression_to_sql(self, node):
    """
    Convert a parsed query expression into SQL.

    QueryNode is handed to your existing query parser / SQL
    generation code.

    AND / OR structure is handled here, rather than by doing
    string replacements such as:

        sql.replace(' OR ', ' AND ')
    """

    if isinstance(node, QueryNode):
        query = node.text.strip()

        if not query:
            return ""

        # ----------------------------------------------------
        # IMPORTANT:
        #
        # Replace this with whatever currently turns one
        # individual query into SQL.
        #
        # For example, if you already have:
        #
        #     self.get_sql_for_query(query)
        #
        # use that here.
        # ----------------------------------------------------

        return self.get_sql_for_single_query(query)

    if isinstance(node, AndNode):
        parts = []

        for child in node.children:
            child_sql = expression_to_sql(self, child)

            if child_sql:
                parts.append(child_sql)

        if not parts:
            return ""

        if len(parts) == 1:
            return parts[0]

        return "(" + " AND ".join(parts) + ")"

    if isinstance(node, OrNode):
        parts = []

        for child in node.children:
            child_sql = expression_to_sql(self, child)

            if child_sql:
                parts.append(child_sql)

        if not parts:
            return ""

        if len(parts) == 1:
            return parts[0]

        return "(" + " OR ".join(parts) + ")"

    raise TypeError(
        f"Unknown query expression node: {type(node).__name__}"
    )


# ============================================================
# Optional debugging helper
# ============================================================

def dump_query_expression(node, indent=0):
    """
    Pretty-print the expression tree. Very useful while
    debugging the query editor.
    """

    prefix = " " * indent

    if isinstance(node, QueryNode):
        print(f"{prefix}QUERY: {node.text!r}")
        return

    if isinstance(node, AndNode):
        print(f"{prefix}AND")

        for child in node.children:
            dump_query_expression(child, indent + 4)

        return

    if isinstance(node, OrNode):
        print(f"{prefix}OR")

        for child in node.children:
            dump_query_expression(child, indent + 4)

        return

    print(f"{prefix}UNKNOWN: {node!r}")

if __name__ == "__main__":
    # Usage
    expression = parse_query_expression("foo && (bar || baz)")
    print("*"*33)
    print(expression)
    dump_query_expression(expression)

    # prints:

    # AND
    #     QUERY: 'foo'
    #     OR
    #         QUERY: 'bar'
    #         QUERY: 'baz'
    expression = parse_query_expression("(foo || bar) && (baz || qux)")
    print("*"*33)
    print(expression)
    dump_query_expression(expression)

    expression = parse_query_expression(
        "filename == 23 && (filename= 30 || filepath= 25)"
    )

    print(expression)
    dump_query_expression(expression)

    expression = parse_query_expression("23&& ||(30 && filepath= 25)")
    print(expression)
    dump_query_expression(expression)
    # prints:

    # AND
    #     OR
    #         QUERY: 'foo'
    #         QUERY: 'bar'
    #     OR
    #         QUERY: 'baz'
    #         QUERY: 'qux'

    # Important integration point
    # The only piece you need to connect to your existing code is this:
    # return self.get_sql_for_single_query(query)
    # Your existing get_sql_for_operation() is not that function because it operates on an already-separated:

    # operation
    # operator
    # q_txt

    # So your existing pipeline that converts one ordinary query into those three pieces should be called there.
    # The important architectural change is:

    #                    user expression
    #                          │
    #                          ▼
    #                  QueryExpressionParser
    #                          │
    #                          ▼
    #                     expression tree
    #                          │
    #               ┌──────────┴──────────┐
    #               ▼                     ▼
    #             AND                   OR
    #           /  |  \                /   \
    #        query query query      query query
    #           │                     │
    #           └──────────┬──────────┘
    #                      ▼
    #               existing leaf parser
    #                      │
    #                      ▼
    #                     SQL

    # So your existing operation parser doesn't need to know anything about &&, ||, or parentheses anymore.
    # And absolutely delete this old trick:
    # opt_sql.replace(' OR ', ' AND ')
    # That is the bit most likely to come back from the dead and eat your lunch. 😄