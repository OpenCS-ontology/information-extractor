from grobid_client.grobid_client import GrobidClient
import shutil
import xmltodict
import os
from rdflib import Graph, Literal, Namespace, RDF, URIRef
from rdflib.namespace import FOAF
import sys


def parse_sections_with_ref_and_formulas(g, doc_as_dict, objects_dict):
    formula_counter = 0
    ref_counter = 0
    section_counter = 0
    for _, paragraph in enumerate(doc_as_dict["TEI"]["text"]["body"]["div"]):
        if type(paragraph) != dict or "head" not in paragraph:
            continue

        if type(paragraph["head"]) != dict or "#text" not in paragraph["head"]:
            continue

        section_name: str = paragraph["head"]["#text"]

        g.add(
            (
                section := base_namespace[f"section{section_counter}"],
                RDF.type,
                doco.Section,
            )
        )
        g.add(
            (
                section_title := base_namespace[f"section_title{section_counter}"],
                RDF.type,
                doco.SectionTitle,
            )
        )
        g.add((section_title, c4o.hasContent, Literal(section_name)))
        g.add((section, po.containsAsHeader, section_title))

        section_counter += 1
        if type(paragraph["head"]) == dict and "@coords" in paragraph["head"]:
            g.add(
                (
                    section,
                    schema.pagination,
                    Literal(int(paragraph["head"]["@coords"].split(",")[0])),
                )
            )

        g.add((body_matter, po.contains, section))

        if "formula" in paragraph:
            if type(paragraph["formula"]) == dict and "label" in paragraph["formula"]:
                text = paragraph["formula"]["#text"]
                label = paragraph["formula"]["label"].replace("(", "").replace(")", "")
                parse_formula(g, section, text, label, formula_counter)
                formula_counter += 1
            else:
                for _, formula in enumerate(paragraph["formula"]):
                    if type(formula) == dict and "label" in formula:
                        text = formula["#text"]
                        label = formula["label"].replace("(", "").replace(")", "")
                        parse_formula(g, section, text, label, formula_counter)
                        formula_counter += 1

        if "p" in paragraph:
            if type(paragraph["p"]) == list:
                for _, reference in enumerate(paragraph["p"]):
                    if type(reference) == dict and "ref" in reference:
                        if type(reference["ref"]) == list:
                            for _, inside_reference in enumerate(reference["ref"]):
                                parse_reference(
                                    g,
                                    inside_reference,
                                    ref_counter,
                                    section,
                                    objects_dict,
                                )
                                ref_counter += 1
                        else:
                            parse_reference(
                                g, reference["ref"], ref_counter, section, objects_dict
                            )
                            ref_counter += 1


def parse_formula(g, section, formula_text, formula_label, formula_counter):
    formula_object = URIRef(base_uri + f"formula_{formula_counter}")
    g.add((formula_object, RDF.type, doco.Formula))

    g.add((formula_object, c4o.hasContent, Literal(formula_text)))
    g.add((section, po.contains, formula_object))

    formula_label_object = URIRef(base_uri + f"formula_label_{formula_counter}")
    g.add((formula_label_object, RDF.type, doco.Label))
    g.add((formula_label_object, c4o.hasContent, Literal(formula_label)))

    g.add((formula_object, po.contains, formula_label_object))


def parse_reference(
    g: Graph, reference: dict, ref_counter: int, section, objects_dict: dict
):
    if reference["@type"] == "figure":
        entity = "Figure"
    elif reference["@type"] == "table":
        entity = "Table"
    else:
        entity = None

    if entity is not None:
        ref_object = URIRef(base_uri + f"reference_{ref_counter}")
        g.add((ref_object, RDF.type, deo.Reference))
        g.add((ref_object, c4o.hasContent, Literal(entity + " " + reference["#text"])))
        g.add((section, po.contains, ref_object))

        if (
            type(reference) == dict
            and "@target" in reference
            and reference["@target"].replace("#", "") in objects_dict
        ):
            id = reference["@target"].replace("#", "")
            g.add((ref_object, dcterms.references, objects_dict[id]))

        if type(reference) == dict and "@coords" in reference:
            g.add(
                (
                    ref_object,
                    schema.pagination,
                    Literal(int(reference["@coords"].split(",")[0])),
                )
            )


def add_list_of_figures(back_matter, objects_dict, base_uri):
    listOfTables = URIRef(base_uri + "ListOfTables")
    listOfFigures = URIRef(base_uri + "ListOfFigures")

    g.add((listOfTables, RDF.type, doco.ListOfTables))
    g.add((listOfFigures, RDF.type, doco.ListOfFigures))

    for _, id in enumerate(objects_dict):
        if "fig" in id:
            g.add((listOfFigures, po.contains, objects_dict[id]))
        elif "tab" in id:
            g.add((listOfTables, po.contains, objects_dict[id]))

    g.add((back_matter, po.contains, listOfTables))
    g.add((back_matter, po.contains, listOfFigures))


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(
            "Please, pass all of the arguments: input folder path, output folder path"
        )
        sys.exit()

    input_path = sys.argv[1]
    output_path = "/home/output_xml_files"

    if not os.path.exists(sys.argv[2]):
        os.mkdir(sys.argv[2])

    client = GrobidClient(config_path="/home/grobid_client_python/config.json")
    client.process(
        "processFulltextDocument",
        input_path,
        output=output_path,
        consolidate_citations=True,
        tei_coordinates=True,
        force=True,
    )

    base_uri = "https://w3id.org/ocs/ont/papers/"

    # Namespaces:
    doco = Namespace("http://purl.org/spar/doco/")
    dcterms = Namespace("http://purl.org/dc/terms/")
    schema = Namespace("http://schema.org/")
    co = Namespace("http://purl.org/co/")
    c4o = Namespace("http://purl.org/spar/c4o/")
    po = Namespace("http://www.essepuntato.it/2008/12/pattern#")
    deo = Namespace("http://purl.org/spar/deo/")
    base_namespace = Namespace(base_uri)

    for file_name in os.listdir(output_path):
        file_path = os.path.join(output_path, file_name)

        print(f"Processing {file_name.replace('tei.xml', 'pdf')} file")

        # Create a Graph
        g = Graph()

        # Bind the FOAF namespace to a prefix for more readable output
        g.bind("foaf", FOAF)
        g.bind("doco", doco)
        g.bind("dcterms", dcterms)
        g.bind("schema", schema)
        g.bind("co", co)
        g.bind("c4o", c4o)
        g.bind("po", po)
        g.bind("deo", deo)
        g.bind("", base_namespace)

        paper = URIRef(base_uri + "paper")
        body_matter = URIRef(base_uri + "body_matter")
        g.add((paper, po.contains, body_matter))
        g.add((body_matter, RDF.type, doco.BodyMatter))

        back_matter = URIRef(base_uri + "back_matter")
        g.add((paper, po.contains, back_matter))
        g.add((back_matter, RDF.type, doco.BackMatter))

        try:
            with open(file_path, encoding="utf8") as xml_file:
                data_dict = xmltodict.parse(xml_file.read())

                objects_dict = dict()

                title = (
                    data_dict["TEI"]["teiHeader"]["fileDesc"]["titleStmt"]["title"][
                        "#text"
                    ]
                    .replace(" ", "_")
                    .replace(":", "_")
                )

                nr_of_figs = len(data_dict["TEI"]["text"]["body"]["figure"])

                fig_counter = 0
                table_counter = 0
                for i in range(nr_of_figs):
                    fig_dict = data_dict["TEI"]["text"]["body"]["figure"][i]

                    if type(fig_dict) == dict and "@type" in fig_dict:
                        if fig_dict["@type"] == "table":
                            object = URIRef(base_uri + f"table_{table_counter}")
                            g.add((object, RDF.type, doco.Table))

                            if "figDesc" in fig_dict:
                                object_desc = URIRef(
                                    base_uri + f"table_description_{table_counter}"
                                )
                                g.add((object_desc, RDF.type, doco.TableLabel))

                            if "@coords" in fig_dict:
                                object_box = URIRef(
                                    base_uri + f"table_box_{table_counter}"
                                )
                                g.add((object_box, RDF.type, doco.TableBox))

                            if "head" in fig_dict:
                                object_label = URIRef(
                                    base_uri + f"table_label_{table_counter}"
                                )

                            table_counter += 1

                    elif type(fig_dict) == dict and "@type" not in fig_dict:
                        object = URIRef(base_uri + f"figure_{fig_counter}")
                        g.add((object, RDF.type, doco.Figure))

                        if "figDesc" in fig_dict:
                            object_desc = URIRef(
                                base_uri + f"figure_description_{fig_counter}"
                            )
                            g.add((object_desc, RDF.type, doco.FigureLabel))

                        if "@coords" in fig_dict:
                            object_box = URIRef(base_uri + f"figure_box_{fig_counter}")
                            g.add((object_box, RDF.type, doco.FigureBox))

                        if "head" in fig_dict:
                            object_label = URIRef(
                                base_uri + f"figure_label_{fig_counter}"
                            )

                        fig_counter += 1

                    if type(fig_dict) == dict and "figDesc" in fig_dict:
                        g.add((object, po.contains, object_desc))

                        figDesc = fig_dict["figDesc"]

                        if type(fig_dict["figDesc"]) != str and type(
                            fig_dict["figDesc"]
                        ) != type(None):
                            figDesc = fig_dict["figDesc"]["#text"]

                        g.add(
                            (
                                object_desc,
                                c4o.hasContent,
                                Literal(figDesc),
                            )
                        )

                    if type(fig_dict) == dict and "@coords" in fig_dict:
                        g.add((object, po.contains, object_box))
                        objects_list = []
                        for im in fig_dict["@coords"].split(";"):
                            im = im.replace("'", "")
                            im = im.split(",")
                            page = im[0]
                            im_list = [float(coord) for coord in im[1:]]
                            objects_list.append(im_list)

                        g.add((object_box, c4o.hasContent, Literal(list(objects_list))))

                        g.add((object_box, schema.pagination, Literal(int(page))))

                    if type(fig_dict) == dict and "head" in fig_dict:
                        g.add((object_label, RDF.type, doco.Label))

                        g.add((object, po.contains, object_label))

                        g.add((object_label, c4o.hasContent, Literal(fig_dict["head"])))

                    if type(fig_dict) == dict and "@xml:id" in fig_dict:
                        id = fig_dict["@xml:id"]

                        if id not in objects_dict:
                            objects_dict[id] = object

                parse_sections_with_ref_and_formulas(g, data_dict, objects_dict)
                add_list_of_figures(back_matter, objects_dict, base_uri)

                f = open(os.path.join(sys.argv[2], f"{title}.ttl"), "w")
                ret = g.serialize(format="turtle").decode("utf-8")

                f.write(ret)
                f.close()
        except:
            print(
                f"Processing of file {file_path} failed because there are no figures or grobid didn't succeed in scraping pdf"
            )

    shutil.rmtree(output_path)
