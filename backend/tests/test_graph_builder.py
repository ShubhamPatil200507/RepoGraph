from pathlib import Path
from app.models.graph import ArchitecturalLayer, GraphNode, NodeType
from app.services.graph_builder import GraphBuilder
from app.services.parser.python_parser import PythonASTParser


def test_graph_builder_normalization_and_layout():
    builder = GraphBuilder()
    parser = PythonASTParser()

    code1 = """
class OrderService:
    def create(self):
        pass
"""
    nodes1, edges1, er1, rel1 = parser.parse(Path("services/order.py"), "services/order.py", code1)
    builder.add_parsed_results(nodes1, edges1, er1, rel1, "services/order.py", 100, "python")

    norm_graph, er_diagram, file_tree = builder.build_normalized_graph()

    assert norm_graph.summary.total_files == 1
    assert norm_graph.summary.total_nodes > 0

    # Ensure deterministic 3D and 2D positions were calculated
    for node in norm_graph.nodes:
        assert node.position_3d is not None
        assert node.position_2d is not None
        assert isinstance(node.position_3d.x, float)
        assert isinstance(node.position_3d.y, float)
        assert isinstance(node.position_3d.z, float)

    # File tree root check
    assert file_tree.name == "repository_root"
    assert len(file_tree.children) > 0
