from grobid_client.grobid_client import GrobidClient
import shutil
import xmltodict
import os
import re
from rdflib import Graph, Literal, Namespace, RDF, URIRef, BNode, XSD
import sys


def add_authors(ref_instance, g, bib_reference):
    if ref_instance.get("analytic", None):
        if ref_instance["analytic"].get("author", None):
            for i, author_data in enumerate(
                ref_instance["analytic"]["author"], start=1
            ):
                g.add((bib_reference, dcterms.creator, author := BNode()))
                g.add((author, RDF.type, schema.Person))
                if not isinstance(author_data, str):
                    if author_data.get("persName", None):
                        if author_data["persName"].get("forename", None):
                            if isinstance(
                                author_data["persName"]["forename"],
                                list,
                            ):
                                first_name = author_data["persName"]["forename"][0]

                            else:
                                first_name = author_data["persName"]["forename"]
                            g.add(
                                (
                                    author,
                                    schema.givenName,
                                    Literal(first_name["#text"]),
                                )
                            )
                        if author_data["persName"].get("surname", None):
                            g.add(
                                (
                                    author,
                                    schema.familyName,
                                    Literal(author_data["persName"]["surname"]),
                                )
                            )
    return g


def add_title(ref_instance, g, bib_reference):
    if ref_instance.get("analytic", None):
        if ref_instance["analytic"].get("title", None):
            g.add(
                (
                    bib_reference,
                    dcterms.title,
                    Literal(ref_instance["analytic"]["title"]["#text"]),
                )
            )
    return g


def add_year(ref_instance, g, bib_reference):
    if ref_instance["monogr"].get("imprint", None):
        if ref_instance["monogr"]["imprint"].get("date", None):
            if not isinstance(ref_instance["monogr"]["imprint"]["date"], str):
                if ref_instance["monogr"]["imprint"]["date"].get("#text", None):
                    year = re.search(
                        r"\b\d{4}\b",
                        ref_instance["monogr"]["imprint"]["date"]["#text"],
                    )
                    if year:
                        year = year.group()
                        g.add(
                            (
                                bib_reference,
                                dcterms.issued,
                                Literal(int(year)),
                            )
                        )
                elif ref_instance["monogr"]["imprint"]["date"].get("@when", None):
                    year = re.search(
                        r"\b\d{4}\b",
                        ref_instance["monogr"]["imprint"]["date"]["@when"],
                    ).group()
                    g.add(
                        (
                            bib_reference,
                            dcterms.issued,
                            Literal(int(year)),
                        )
                    )
    return g


def add_venue(ref_instance, g, bib_reference):
    if ref_instance["monogr"].get("title", None):
        g.add(
            (
                bib_reference,
                dcterms.publisher,
                publisher := BNode(),
            )
        )
        if isinstance(ref_instance["monogr"]["title"], list):
            info = ref_instance["monogr"]["title"][0]
        else:
            info = ref_instance["monogr"]["title"]
        g.add((publisher, schema.name, Literal(info["#text"])))
    return g


def add_volumes_issues_pages(ref_instance, g, bib_reference):
    if ref_instance["monogr"].get("imprint", None):
        if ref_instance["monogr"]["imprint"].get("biblScope", None):
            biblScope = ref_instance["monogr"]["imprint"]["biblScope"]
            if not isinstance(biblScope, list):
                if biblScope["@unit"] == "volume":
                    g.add(
                        (
                            bib_reference,
                            prism.volume,
                            Literal(biblScope["#text"], datatype=XSD.integer),
                        )
                    )
                if biblScope["@unit"] == "issue":
                    g.add(
                        (
                            bib_reference,
                            prism.issueIdentifier,
                            Literal(biblScope["#text"]),
                        )
                    )
                if biblScope["@unit"] == "page":
                    if biblScope.get("@from", None):
                        g.add(
                            (
                                bib_reference,
                                prism.startingPage,
                                Literal(biblScope["@from"], datatype=XSD.integer),
                            )
                        )
                    if biblScope.get("@to", None):
                        g.add(
                            (
                                bib_reference,
                                prism.endingPage,
                                Literal(biblScope["@to"], datatype=XSD.integer),
                            )
                        )
            else:
                for biblScopeUnit in biblScope:
                    if biblScopeUnit["@unit"] == "volume":
                        g.add(
                            (
                                bib_reference,
                                prism.volume,
                                Literal(biblScopeUnit["#text"], datatype=XSD.integer),
                            )
                        )  # string because we believe that things like 1-2 may happen
                    if biblScopeUnit["@unit"] == "issue":
                        g.add(
                            (
                                bib_reference,
                                prism.issueIdentifier,
                                Literal(biblScopeUnit["#text"], datatype=XSD.integer),
                            )
                        )  # string because we believe that things like 1-2 may happen
                    if biblScopeUnit["@unit"] == "page":
                        if biblScopeUnit.get("@from", None):
                            g.add(
                                (
                                    bib_reference,
                                    prism.strtingPage,
                                    Literal(
                                        biblScopeUnit["@from"], datatype=XSD.integer
                                    ),
                                )
                            )
                        if biblScopeUnit.get("@to", None):
                            g.add(
                                (
                                    bib_reference,
                                    prism.endingPage,
                                    Literal(biblScopeUnit["@to"], datatype=XSD.integer),
                                )
                            )
    return g


def get_doi(ref_instance, g, bib_reference):
    if ref_instance.get("analytic", None):
        if ref_instance["analytic"].get("idno", None):
            if not isinstance(ref_instance["analytic"]["idno"], list):
                if not isinstance(ref_instance["analytic"]["idno"], str):
                    DOI = (
                        "http://dx.doi.org/" + ref_instance["analytic"]["idno"]["#text"]
                    )
                    g.add(
                        (
                            bib_reference,
                            datacite.doi,
                            Literal(DOI, datatype=XSD.anyURI),
                        )
                    )
            else:
                for id_type in ref_instance["analytic"]["idno"]:
                    if id_type["@type"] == "DOI":
                        DOI = "http://dx.doi.org/" + id_type["#text"]
                        g.add(
                            (
                                bib_reference,
                                datacite.doi,
                                Literal(DOI, datatype=XSD.anyURI),
                            )
                        )
                        break
    return g


def to_arabic(number):
    roman_to_arabic_dict = {
        "I": "1",
        "II": "2",
        "III": "3",
        "IV": "4",
        "V": "5",
        "VI": "6",
        "VII": "7",
        "VIII": "8",
        "IX": "9",
        "X": "10",
        "XI": "11",
        "XII": "12",
        "XIII": "13",
        "XIV": "14",
        "XV": "15",
        "XVI": "16",
        "XVII": "17",
        "XVIII": "18",
        "XIX": "19",
        "XX": "20",
        "XXI": "21",
        "XXII": "22",
        "XXIII": "23",
        "XXIV": "24",
        "XXV": "25",
        "XXVI": "26",
        "XXVII": "27",
        "XXVIII": "28",
        "XXIX": "29",
        "XXX": "30",
        "XXXI": "31",
        "XXXII": "32",
        "XXXIII": "33",
        "XXXIV": "34",
        "XXXV": "35",
        "XXXVI": "36",
        "XXXVII": "37",
        "XXXVIII": "38",
        "XXXIX": "39",
        "XL": "40",
        "XLI": "41",
        "XLII": "42",
        "XLIII": "43",
        "XLIV": "44",
        "XLV": "45",
        "XLVI": "46",
        "XLVII": "47",
        "XLVIII": "48",
        "XLIX": "49",
        "L": "50",
    }
    return roman_to_arabic_dict.get(number, number)


def parse_sections_with_ref_and_formulas(g, data_dict, objects_dict):
    formula_counter = 0
    section_counter = 0
    ref_counter = 0
    sections_dict = {}
    first_iter = True
    first_iter_inner = True
    hierarchy = ["", ""]
    prev_section_name = ""
    for i, section in enumerate(data_dict["TEI"]["text"]["body"]["div"]):
        if isinstance(section, dict) and "head" in section:
            if isinstance(section["head"], dict) and "#text" in section["head"]:
                section_name = section["head"]["#text"]
            elif isinstance(section["head"], str):
                section_name = section.get("head", None)
        else:
            section_name = None

        try:
            section_number: str = section["head"]["@n"]
        except:
            section_number = None

        p = section.get("p", None)
        if not isinstance(p, list):
            p = [p]

        for j, paragraph in enumerate(p):
            if not isinstance(paragraph, dict):
                if isinstance(paragraph, str):
                    par_text = paragraph
                else:
                    continue
            else:
                par_text = paragraph.get("#text", None)

            match = re.match(r"^([0-9\s.IVX]+) (.*)$", par_text)

            if not match and not section_name and prev_section_name != "":
                section_name = prev_section_name
            elif match:
                section_number, section_name = match.group(1), match.group(2)
                section_name = section_name.split(". ", 1)[0]
                section_name = section_number + " " + section_name
                prev_section_name = section_name

            if section_name != prev_section_name and section_name:
                match = re.match(r"^([0-9\s.IVX]+) (.*)$", section_name)
                if match:
                    section_number, section_name = match.group(1), match.group(2)
                    section_name = section_name.split(". ", 1)[0]
                    section_name = section_number + " " + section_name
                    prev_section_name = section_name

            if not section_name or not any(c.isalpha() for c in section_name):
                continue
            if not section_number and section_name is not None:
                match = re.match(r"^([0-9\s.IVX]+) (.*)$", section_name)
                if match:
                    section_number = match.group(1)
                else:
                    section_number = None
            match = re.match(r"^([0-9\s.IVX]+) (.*)$", section_name)
            if match:
                section_name = match.group(2)
                section_number = (
                    ".".join(map(to_arabic, section_number.split(".")))
                    if section_number is not None
                    else None
                )
            if (section_name, section_number) not in sections_dict:
                section_counter += 1
                g.add(
                    (
                        section := URIRef(base_namespace + f"section{section_counter}"),
                        RDF.type,
                        doco.Section,
                    )
                )
                g.add(
                    (
                        section_title := URIRef(
                            base_namespace + f"sectionTitle{section_counter}"
                        ),
                        RDF.type,
                        doco.SectionTitle,
                    )
                )
                g.add((section_title, c4o.hasContent, Literal(section_name)))
                g.add((section, po.containsAsHeader, section_title))
                if section_number:
                    g.add(
                        (
                            section_label := URIRef(
                                base_namespace + f"sectionLabel{section_counter}"
                            ),
                            RDF.type,
                            doco.SectionLabel,
                        )
                    )
                    g.add(
                        (
                            section_label,
                            c4o.hasContent,
                            Literal(section_number),
                        )
                    )
                    g.add((section, po.contains, section_label))
                if isinstance(section, dict):
                    if isinstance(section.get("head"), dict):
                        if "@coords" in section["head"]:
                            g.add(
                                (
                                    section,
                                    schema.pagination,
                                    Literal(
                                        int(paragraph["head"]["@coords"].split(",")[0])
                                    ),
                                )
                            )

                sections_dict[(section_name, section_number)] = section

                depth = len(list(filter(None, str(section_number).split("."))))
                if depth == 1:
                    if hierarchy[0] == "":
                        g.add(
                            (
                                body_matter,
                                co.firstItem,
                                body_list_item := BNode(),
                            )
                        )
                    else:
                        g.add(
                            (
                                body_list_item,
                                co.nextItem,
                                next_body_list_item := BNode(),
                            )
                        )
                        body_list_item = next_body_list_item
                    g.add((body_list_item, co.itemContent, section))
                    g.add((body_matter, po.contains, section))
                    hierarchy[0] = section
                    first_iter = True
                elif depth == 2:
                    if first_iter:
                        g.add(
                            (
                                hierarchy[0],
                                co.firstItem,
                                list_item := BNode(),
                            )
                        )
                    else:
                        g.add(
                            (
                                list_item,
                                co.nextItem,
                                next_list_item := BNode(),
                            )
                        )
                        list_item = next_list_item
                    g.add((list_item, co.itemContent, section))
                    g.add((hierarchy[0], po.contains, section))
                    hierarchy[1] = section
                    first_iter = False
                    first_iter_inner = True
                elif hierarchy[1]:
                    if first_iter_inner:
                        g.add(
                            (
                                hierarchy[1],
                                co.firstItem,
                                list_item_inner := BNode(),
                            )
                        )
                    else:
                        g.add(
                            (
                                list_item_inner,
                                co.nextItem,
                                next_list_item_inner := BNode(),
                            )
                        )
                        list_item_inner = next_list_item_inner
                    g.add((list_item_inner, co.itemContent, section))
                    g.add((hierarchy[1], po.contains, section))
                    first_iter_inner = False
            else:
                section = sections_dict[(section_name, section_number)]

            if isinstance(paragraph, dict) and "ref" in paragraph:
                reference = paragraph["ref"]
                if not type(reference) == list:
                    reference = [reference]
                for _, inside_reference in enumerate(reference):
                    parse_reference(
                        g,
                        inside_reference,
                        ref_counter,
                        section,
                        objects_dict,
                    )
                    ref_counter += 1

            if isinstance(section, dict) and "formula" in section:
                if (
                    type(paragraph["formula"]) == dict
                    and "label" in paragraph["formula"]
                ):
                    text = paragraph["formula"]["#text"]
                    label = (
                        paragraph["formula"]["label"].replace("(", "").replace(")", "")
                    )
                    parse_formula(g, section, text, label, formula_counter)
                    formula_counter += 1
                else:
                    for _, formula in enumerate(paragraph["formula"]):
                        if type(formula) == dict and "label" in formula:
                            text = formula["#text"]
                            label = formula["label"].replace("(", "").replace(")", "")
                            parse_formula(g, section, text, label, formula_counter)
                            formula_counter += 1


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
    elif reference["@type"] == "bibr":
        entity = "BIBREF"
    else:
        return

    ref_object = None

    if entity in ["Figure", "Table"]:
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

    elif entity == "BIBREF" and reference.get("@target"):
        ref_id = "BIBREF" + reference.get("@target").lstrip("#b")
        ref_object = URIRef(base_namespace + f"referenceTo{ref_id}")
        g.add(
            (
                section,
                po.contains,
                ref_object,
            )
        )
        g.add((ref_object, RDF.type, deo.Reference))
        ref_text = reference["#text"]
        for char in [",", ".", "[", "]", "(", ")"]:
            ref_text = ref_text.replace(char, "")
        ref_text = f"[{ref_text}]"
        g.add((ref_object, c4o.hasContent, Literal(ref_text)))
        g.add(
            (
                ref_object,
                dcterms.references,
                bib_reference := URIRef(base_namespace + ref_id),
            )
        )
        g.add((bib_reference, RDF.type, deo.BibliographicReference))

    if type(reference) == dict and "@coords" in reference and ref_object:
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

    base_uri = "https://w3id.org/ocs/kg/papers/"

    # Namespaces:
    doco = Namespace("http://purl.org/spar/doco/")
    dcterms = Namespace("http://purl.org/dc/terms/")
    schema = Namespace("http://schema.org/")
    co = Namespace("http://purl.org/co/")
    c4o = Namespace("http://purl.org/spar/c4o/")
    po = Namespace("http://www.essepuntato.it/2008/12/pattern#")
    deo = Namespace("http://purl.org/spar/deo/")
    datacite = Namespace("http://purl.org/spar/datacite/")
    prism = Namespace("http://prismstandard.org/namespaces/basic/2.0/")
    base_namespace = Namespace(base_uri)

    for file_name in os.listdir(output_path):
        file_path = os.path.join(output_path, file_name)

        print(f"Processing {file_name.replace('tei.xml', 'pdf')} file")

        # Create a Graph
        g = Graph()

        g.bind("doco", doco)
        g.bind("dcterms", dcterms)
        g.bind("schema", schema)
        g.bind("co", co)
        g.bind("c4o", c4o)
        g.bind("po", po)
        g.bind("deo", deo)
        g.bind("datacite", datacite)
        g.bind("prism", prism)
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
                if data_dict["TEI"]["text"]["body"].get("figure", None):
                    nr_of_figs = len(data_dict["TEI"]["text"]["body"]["figure"])

                    fig_counter = 0
                    table_counter = 0
                    for i in range(nr_of_figs):
                        if isinstance(data_dict["TEI"]["text"]["body"]["figure"], list):
                            fig_dict = data_dict["TEI"]["text"]["body"]["figure"][i]
                        else:
                            fig_dict = None

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
                                object_box = URIRef(
                                    base_uri + f"figure_box_{fig_counter}"
                                )
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

                            g.add(
                                (
                                    object_box,
                                    c4o.hasContent,
                                    Literal(list(objects_list)),
                                )
                            )

                            g.add((object_box, schema.pagination, Literal(int(page))))

                        if type(fig_dict) == dict and "head" in fig_dict:
                            g.add((object_label, RDF.type, doco.Label))

                            g.add((object, po.contains, object_label))

                            g.add(
                                (
                                    object_label,
                                    c4o.hasContent,
                                    Literal(fig_dict["head"]),
                                )
                            )

                        if type(fig_dict) == dict and "@xml:id" in fig_dict:
                            id = fig_dict["@xml:id"]

                            if id not in objects_dict:
                                objects_dict[id] = object

                    add_list_of_figures(back_matter, objects_dict, base_uri)
                    parse_sections_with_ref_and_formulas(g, data_dict, objects_dict)

                # bibliography
                g.add(
                    (
                        bibliography := base_namespace.bibliography,
                        RDF.type,
                        doco.Bibliography,
                    )
                )
                g.add((bibliography, co.firstItem, list_item := BNode()))
                first_iter = True
                if isinstance(data_dict["TEI"]["text"]["back"]["div"], list):
                    iterate_over = data_dict["TEI"]["text"]["back"]["div"][1]
                else:
                    iterate_over = data_dict["TEI"]["text"]["back"]["div"]
                if iterate_over.get("listBibl", None):
                    for ref_instance in iterate_over["listBibl"]["biblStruct"]:
                        bib_nr = re.search(r"\d+", ref_instance["@xml:id"]).group()
                        g.add(
                            (
                                bibliography,
                                po.contains,
                                bib_reference := base_namespace[f"BIBREF{bib_nr}"],
                            )
                        )
                        if not first_iter:
                            g.add((list_item, co.nextItem, next_list_item := BNode()))
                            list_item = next_list_item
                        g.add((list_item, co.itemContent, bib_reference))
                        # Authors
                        g = add_authors(ref_instance, g, bib_reference)
                        # Title
                        g = add_title(ref_instance, g, bib_reference)

                        if ref_instance.get("monogr", None):
                            # Year
                            g = add_year(ref_instance, g, bib_reference)
                            # Venue
                            g = add_venue(ref_instance, g, bib_reference)
                            # Volumes, issues and pages
                            g = add_volumes_issues_pages(ref_instance, g, bib_reference)
                        # DOI
                        g = get_doi(ref_instance, g, bib_reference)

                        first_iter = False
                g.add((back_matter, po.contains, bibliography))
                g.add((back_matter, co.firstItem, bibliography_list_item := BNode()))
                g.add((bibliography_list_item, co.itemContent, bibliography))

                f = open(
                    os.path.join(sys.argv[2], f"{title.replace('/', '_')}.ttl"), "w"
                )
                ret = g.serialize(format="turtle").decode("utf-8")

                f.write(ret)
                f.close()
        except:
            print(
                f"Processing of file {file_path} failed because there are no figures or grobid didn't succeed in scraping pdf"
            )

    shutil.rmtree(output_path)
