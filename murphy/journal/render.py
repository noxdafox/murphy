import os
import base64
from html import escape
from pathlib import Path
from typing import Sequence
from itertools import chain, count

from PIL import Image
from graphviz import Digraph

from murphy.journal.node import Node
from murphy.journal.edge import Edge


Image.MAX_IMAGE_PIXELS = None  # disable image size limit check
SEPARATOR = ';' if os.name == 'nt' else ':'


def render_html(nodes: Sequence, path: Path, embed: bool = False):
    """Render the Journal as HTML file.

    If embed is True, the image will be embedded in the HTML file.
    Otherwise a PNG file will be generated to be provide aside of the HTML page.

    """
    html_path = path.joinpath('journal.html')
    img_path = render_dot(nodes, path, 'png')
    map_path = render_dot(nodes, path, 'cmapx')

    save_html(nodes, html_path, map_path, img_path, embed)

    map_path.unlink()
    if embed:
        img_path.unlink()

    return html_path


def render_dot(nodes: Sequence, path: Path, format: str) -> Path:
    dot = Digraph(name='journal',
                  format=format,
                  directory=str(path),
                  comment="MrMurphy's Travel Journal",
                  node_attr={'shape': 'rectangle'},
                  graph_attr={'dpi': '72',
                              'rankdir': 'TB',
                              'bgcolor': 'white',
                              'imagepath': SEPARATOR.join(('.', str(path)))})

    for node in nodes:
        add_image(dot, node, path)
        for edge in node.edges:
            add_image(dot, edge, path)

    render_path = Path(dot.render())

    if format in ('png', 'jpg', 'jpeg'):
        image = Image.open(str(render_path))
        image.save(str(render_path), optimize=True, quality=IMAGE_QUALITY)

    return render_path


def save_html(nodes: Sequence, html_path: Path,
              map_path: Path, img_path: Path, embed: bool):
    modals = build_modals(nodes)
    scripts = build_scripts(nodes)

    with JOURNAL_TEMPLATE_PATH.open() as html_template_file:
        html_template = html_template_file.read()
    with map_path.open() as mapfile:
        html_map = mapfile.read()

    if embed:
        with img_path.open('rb') as imgfile:
            encoded_image = base64.b64encode(imgfile.read()).decode()

        image = EMBED_IMAGE % encoded_image
    else:
        image = img_path.name

    html = html_template.format(
        image=image, modals=modals, map=html_map, scripts=scripts)

    with html_path.open('w') as htmlfile:
        htmlfile.write(html)


def add_image(dot: Digraph, element: (Node, Edge), path: Path):
    try:
        image = find_image(element)
    except LookupError:
        if isinstance(element, Node):
            dot.node(str(element.index), label="%s" % element)
        else:
            dot.edge(str(element.head.index), str(element.tail.index),
                     label="%s" % element.action.text)
    else:
        if isinstance(element, Node):
            render_node(dot, element, image.relative_to(path))
        else:
            render_edge(dot, element, image.relative_to(path))


def render_node(dot: Digraph, node: (Node, Edge), path: Path):
    name = '{}'.format(node.index)
    image = IMG.format(str(path))
    label_content = CELL.format(id=name, title=escape(str(node)), content=image)

    metadata = render_metadata(node)
    label_metadata = '<TD>{}</TD>'.format(
        TABLE.format(metadata) if metadata else '')

    label = '<{}>'.format(TABLE.format(ROW.format(
        '{}{}'.format(label_content, label_metadata))))

    dot.node(str(node.index), label=label, color="white",
             tooltip="%s" % node, style="filled,setlinewidth(0)")


def render_edge(dot: Digraph, edge: (Node, Edge), path: Path):
    name = '{}{}'.format(str(edge.head.index), str(edge.tail.index))
    image = IMG.format(str(path))
    label_content = ROW.format(CELL.format(
        id=name, title=escape(str(edge)), content=image))

    metadata = render_metadata(edge)
    label_metadata = ROW.format(metadata) if metadata else ''

    label = '<{}>'.format(TABLE.format(
        '{}{}'.format(label_content, label_metadata)))

    dot.edge(str(edge.head.index), str(edge.tail.index), label=label,
             tooltip="%s" % edge)


def render_metadata(element: (Node, Edge)) -> str:
    metadata = ''
    index = count()

    if isinstance(element, Node):
        meta_format = ROW.format(CELL)
        name = '{}'.format(element.index)
    else:
        meta_format = CELL
        name = '{}{}'.format(str(element.head.index), str(element.tail.index))

    for element_meta in element.metadata:
        meta_id = '{}meta{}'.format(name, next(index))
        meta_image = IMG.format(element_meta.image)
        meta_cell = meta_format.format(
            id=meta_id, title=escape(element_meta.title), content=meta_image)

        metadata += meta_cell

    return metadata


def build_modals(nodes: Sequence) -> str:
    modals = ''

    with MODAL_TEMPLATE_PATH.open() as modal_template_file:
        modal_template = modal_template_file.read()

    for node in nodes:
        node_index = count()
        node_name = '{}'.format(str(node.index))

        for node_meta in node.metadata:
            identifier = '{}meta{}'.format(node_name, next(node_index))

            modals += modal_template.format(
                identifier=identifier,
                text=splitlines(escape(node_meta.text)))

        for edge in node.edges:
            edge_index = count()
            edge_name = '{}{}'.format(
                str(edge.head.index), str(edge.tail.index))

            for edge_meta in edge.metadata:
                identifier = '{}meta{}'.format(edge_name, next(edge_index))

                modals += modal_template.format(
                    identifier=identifier,
                    text=splitlines(escape(edge_meta.text)))

    return modals


def build_scripts(nodes: Sequence) -> str:
    scripts = ''
    edges = chain.from_iterable(n.edges for n in nodes)

    with SCRIPT_TEMPLATE_PATH.open() as script_template_file:
        script_template = script_template_file.read()

    for node in nodes:
        node_index = count()
        node_name = '{}'.format(str(node.index))

        for _ in node.metadata:
            identifier = '{}meta{}'.format(node_name, next(node_index))
            scripts += '<script>{}</script>'.format(
                script_template.format(identifier=identifier))

        for edge in edges:
            edge_index = count()
            edge_name = '{}{}'.format(
                str(edge.head.index), str(edge.tail.index))

            for _ in edge.metadata:
                identifier = '{}meta{}'.format(edge_name, next(edge_index))
                scripts += '<script>{}</script>'.format(
                    script_template.format(identifier=identifier))

    return scripts


def find_image(element: (Node, Edge)) -> Path:
    matches = []

    for extension in EXTENSIONS:
        matches.extend(element.path.glob('*.%s' % extension))

    try:
        return matches[0]
    except IndexError:
        raise LookupError("Image for element %s not found" % element.path)


def splitlines(string):
    return os.linesep.join('{}<br>'.format(l) for l in string.splitlines())


JOURNAL_TEMPLATE_PATH = Path(__file__).parent.joinpath(
    'html/journal_template.html')
MODAL_TEMPLATE_PATH = Path(__file__).parent.joinpath(
    'html/modal_template.html')
SCRIPT_TEMPLATE_PATH = Path(__file__).parent.joinpath(
    'js/modal_script.js')

IMAGE_QUALITY = 85
EXTENSIONS = 'png', 'svg', 'jpg', 'jpeg'
EMBED_IMAGE = 'data:image/png;base64,%s'

ROW = '<TR>{}</TR>'
IMG = '<IMG SRC="{}"/>'
TABLE = '<TABLE BORDER="0">{}</TABLE>'
CELL = '<TD ID="{id}" HREF="" TITLE="{title}">{content}</TD>'
