import json
from pathlib import Path

import PIL
from murphy.model import Action


class Edge:
    """An edge describes the transition between two states
    triggered by an Action.

    """

    __slots__ = 'path', 'head', 'tail', 'action', 'metadata'

    def __init__(self, head: 'Node', tail: 'Node', action: Action):
        self.head = head       # type: Node
        """Node at the head of the Edge."""
        self.tail = tail       # type: Node
        """Node at the tail of the Edge."""
        self.action = action   # type: Action
        """Action associated to the Edge."""
        self.path = None       # type: Path
        """Path where the Node is information is stored."""
        self.metadata = set()  # type: Set[Metadata]
        """Additional Metadata added to the Edge."""

    def __str__(self):
        return "%s -> %s -> %s" % (self.head, self.action.text, self.tail)


def dump_edge(edge: Edge, path: Path, index: int, force: bool):
    edge.path = path.joinpath("edge%d" % index)
    image_path = edge.path.joinpath("edge.png")
    edge_path = edge.path.joinpath("edge.json")

    if not edge.path.exists() or force:
        dump = {'head': str(edge.head.path),
                'tail': str(edge.tail.path),
                'action': {'text': edge.action.text,
                           'coordinates': edge.action.coordinates}}

        edge.path.mkdir(parents=True)

        if isinstance(edge.action.image, PIL.Image.Image):
            edge.action.image.save(image_path)
            dump['action']['image'] = str(image_path)

        with edge_path.open('w') as edge_file:
            json.dump(dump, edge_file)
