from typing import Tuple
from pathlib import Path
from collections import deque

from murphy.model import State, Action

from murphy.journal.edge import Edge


class Node:
    """A Node encapsulates the GUI application State within the Journal."""

    __slots__ = 'edges', 'state', 'path', 'metadata', 'index'

    def __init__(self, state: State):
        self.edges = []        # type: list
        """List of edges belonging to the Node."""
        self.state = state     # type: State
        """State associated to the Node."""
        self.path = None       # type: Path
        """Path where the Node is information is stored."""
        self.metadata = set()  # type: Set[Metadata]
        """Additional Metadata added to the Node."""
        self.index = None      # type: int

    def __str__(self):
        return "%s : %d" % (self.state.window.title, self.index)

    def __contains__(self, element: ('Edge', Action)) -> bool:
        """Return True if the Edge or Action is in the Node."""
        return self.find_edge(element) is not None

    def distance(self, node: 'Node') -> int:
        """Returns the distance between this node and the given one.

        LookupError is raised if the given node is not reachable from this one.

        """
        path = self.find_path(node)
        if path is None:
            raise LookupError("No path found between %s and %s" % (self, node))

        return len(path)

    def find_path(self, node: 'Node') -> (Tuple['Edge'], None):
        """Finds the minimum path between this node and the given one.

        None is returned if no Path was found.
        An empty list is returned if the two nodes are the same.

        """
        return search_path(self, node)

    def find_edge(self, element: ('Edge', Action)) -> ('Edge', None):
        """If the given Node or State is in the Journal, return it."""
        action = element.action if isinstance(element, Edge) else element

        for edge in self.edges:
            if edge.action.coordinates == action.coordinates:
                return edge

        return None

    def new_edge(self, action: Action, successor: 'Node') -> 'Edge':
        """Given an Action and the successor Node, construct an Edge,
        add it to the node and return it.

        """
        edge = Edge(self, successor, action)

        self.edges.append(edge)

        return edge


def search_path(start: Node, end: Node) -> (Tuple[Edge], None):
    if start == end:
        return []

    path = {}
    visited_nodes = set([start])
    edges_queue = deque(start.edges)

    while edges_queue:
        edge = edges_queue.popleft()
        destination = edge.tail

        if destination not in visited_nodes:
            path[destination] = edge
            visited_nodes.add(destination)

            if destination == end:
                return construct_path(path, end)

            edges_queue.extend(destination.edges)

    return None


def construct_path(path: dict, node: Node) -> tuple:
    edges = deque()

    while True:
        try:
            edge = path[node]
        except KeyError:
            break

        node = edge.head
        edges.appendleft(edge)

    return tuple(edges)


def dump_node(node: Node, path: Path, force: bool):
    node.path = path.joinpath("node%d" % node.index)

    if not node.path.exists() or force:
        node.state.dump(node.path)
