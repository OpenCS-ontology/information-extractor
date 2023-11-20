# Information extractor

This component, for a given research article, extracts various structured information such as figures, labels, formulas, sections and bibliographies using the `GROBID` Docker container. It takes articles' PDFs and Turtle files as input and returns new Turtle files enriched with the extracted information. It should be run as a Docker container (we recommend usage of [Docker Desktop](https://www.docker.com/products/docker-desktop/)).

## Authors

- [Tomasz Siudalski](https://github.com/tsiudalski)
- [Grzegorz Zbrzeżny](https://github.com/grzegorzZ1)

## Credits

This project is based on the work of the following authors from the original projects:

### table-and-figure-ie

- [Mateusz Jastrzębiowski](https://github.com/mjastrzebiowski)
- [Aleksandra Muszkowska](https://github.com/muszkowska)

### [section-and-bibliography-ie](https://github.com/OpenCS-ontology/section-and-bibliography-ie)

- [Krystian Kurek](https://github.com/KrystianKurek)
- [Anastasiya Danilenka](https://github.com/adanilenka)

# Solution overwiev
Solution performs following steps on each paper:
1. Take PDF files of given paper from input folder
2. Process it using `GROBID` library which extracts many information from these files (`input`: PDF file, `output`: XML)
3. Parse XML and convert it into dictionary using `xmltodict` library
4. Extract needed information from dictionaries
5. Save the extracted information in the form of a Turtle file using `rdflib` library
6. Merge the basic Turtle file of the original article with the one created during the processing in this module using `rdflib` library
