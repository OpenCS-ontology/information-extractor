import subprocess
from rdflib import Graph
import os
from rapidfuzz import fuzz
from rdflib.compare import isomorphic


def are_graphs_equal(graph1, graph2):
    isomorphic_result = isomorphic(graph1, graph2)

    return isomorphic_result

# def are_graphs_equal(graph1, graph2):
#     # Find triples in graph1 that are not in graph2
#     diff_graph1 = Graph()
#     for triple in graph1:
#         if triple not in graph2:
#             diff_graph1.add(triple)

#     # Find triples in graph2 that are not in graph1
#     diff_graph2 = Graph()
#     for triple in graph2:
#         if triple not in graph1:
#             print(triple)
#             diff_graph2.add(triple)

#     return diff_graph1, diff_graph2


if __name__ == "__main__":
    test_out = "/container_test/created_ttl"
    test_in_ttl = "/container_test/true_ttl"
    if not os.path.exists(test_out):
        os.mkdir(test_out)
    for ttl_file in os.listdir(test_in_ttl):
        final_in_path = os.path.join(test_in_ttl, ttl_file)
        final_out_path = os.path.join(test_out)
        final_output_ttl = ttl_file
        mod_ttl_file = "".join([char for char in ttl_file.lower() if char.isalpha()])
        found_file_flag = False
        for out_ttl in os.listdir(final_out_path):
            mod_out_ttl = "".join([char for char in out_ttl.lower() if char.isalpha()])
            if fuzz.ratio(mod_ttl_file, mod_out_ttl) > 95:
                final_out_path = os.path.join(test_out, out_ttl)
                found_file_flag = True
                break
        if found_file_flag:
            g1 = Graph()
            g2 = Graph()

            g1.parse(final_in_path, format="ttl")
            g2.parse(final_out_path, format="ttl")
            print(
                "Comparing true Turtle file with the one created during current version test"
            )
            assert are_graphs_equal(g1, g2)
        print(f"Test with {ttl_file} passed!")
