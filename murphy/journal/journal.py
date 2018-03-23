from pathlib import Path
from itertools import count

from murphy.model import State, Interpreter

from murphy.journal.edge import dump_edge
from murphy.journal.node import Node, dump_node
from murphy.journal.render import render_dot, render_html


METADATA_ICON = Path(__file__).parent.joinpath('images/info.png')


class Journal:
    """The Mr. Murphy Travel Journal offers facilities to help tracking
    the GUI application execution.

    States can be added to the Journal and they can be linked together
    via the Actions which led to such state transitions.

    The Journal can be saved and rendered in multiple formats.

    """

    __slots__ = 'nodes', 'path', 'current_node', '_node_count'

    def __init__(self, path: Path):
        self.nodes = []
        """List of Nodes saved within the Journal."""
        self.current_node = None
        """Current position within the Journal."""
        self.path = path
        """Journal folder path."""

        self._node_count = count()

    def __contains__(self, element: ('Node', State)) -> bool:
        """Return True if the Node or State is in the Journal."""
        return self.find_node(element) is not None

    @property
    def initial_node(self):
        """The first node added to the journal.
        Acts as the Journal entry point.

        """
        try:
            return self.nodes[0]
        except IndexError:
            return None

    def find_node(self, element: ('Node', State)) -> ('Node', None):
        """If the given Node or State is in the Journal, return it."""
        state = element.state if isinstance(element, Node) else element

        for node in self.nodes:
            if node.state == state:
                return node

        return None

    def new_node(self, element: ('Node', State)) -> 'Node':
        """Add the given Node or State into the Journal.

        The new Node is returned.

        """
        node = element if isinstance(element, Node) else Node(element)
        node.index = next(self._node_count)

        self.nodes.append(node)

        return node

    def dump(self, full: bool = False):
        """Save the journal at its root path.

        If `full` is True, the whole Journal gets dumped.
        Otherwise, only the information added since the last dump will be saved.

        """
        self.path.mkdir(parents=True, exist_ok=True)

        for node in self.nodes:
            edge_index = count()

            dump_node(node, self.path, full)

            for edge in node.edges:
                dump_edge(edge, node.path, next(edge_index), full)

    def load(self, interpreter: Interpreter):
        """Load a Journal from its root folder.

        The `interpreter` should be of the same type of the one used
        for generating the States encapsulated by the Journal Nodes.

        """
        raise NotImplementedError()

    def render(self, format: str = 'html') -> Path:
        """Render the Journal as a file with the given format.

        The supported rendering formats are listed here:

          https://www.graphviz.org/doc/info/output.html

        Two additional formats are supported:

          * html: a HTML page mapped on top of a PNG image
          * html_embedded: same as `html` but with the PNG image embedded

        The path of the rendered Journal is returned.

        This method triggers a Journal dump.

        """
        self.dump()

        if format == 'html':
            return render_html(self.nodes, self.path)

        if format == 'html_embedded':
            return render_html(self.nodes, self.path, embed=True)

        return render_dot(self.nodes, self.path, format)


class Metadata:
    """Additional information to append to Nodes and Edges.

    This affects mostly the HTML rendering type.

    """

    __slots__ = 'title', 'text', 'image'

    def __init__(self, title: str, text: str, image: Path = METADATA_ICON):
        self.text = text    # type: str
        """Text to show on User click."""
        self.title = title  # type: str
        """Text to show as tooltip."""
        self.image = image  # type: Path
        """Image or icon to associate to the Metadata element."""

    def __eq__(self, metadata: 'EdgeMeta') -> bool:
        return self.title == metadata.title and self.text == metadata.text

    def __hash__(self):
        return hash(self.title) + hash(self.text)
