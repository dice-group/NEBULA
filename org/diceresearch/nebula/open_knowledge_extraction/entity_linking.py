# parser.add_argument("--path",  default='/upb/users/u/uqudus/profiles/unix/cs/NEBULA/TripleExtraction/rebel_output/FEVER/output/output_train/')
import json
import re
import requests
import ast

dataset_path = ""


class ArgumentParserMock:
    def __init__(self):
        self.args = {}

    def add_argument(self, name, default=None):
        self.args[name] = default

    def parse_args(self, args=[]):
        return self.args


def query_wikidata(search_term):
    # Define the SPARQL query with the search term
    sparql_query = f"""
    SELECT ?relation 
    WHERE {{
      ?relation a wikibase:Property ;
                 rdfs:label ?label .
      FILTER (LANG(?label) = "en" && str(?label) = "{search_term}")
    }}
    """

    # Define the Wikidata endpoint URL
    wikidata_endpoint = "https://query.wikidata.org/sparql"

    # Set up the request headers
    headers = {
        "Accept": "application/sparql-results+json"
    }

    # Make the HTTP request to Wikidata
    response = requests.post(wikidata_endpoint, headers=headers, data={"query": sparql_query})

    # Check if the request was successful (status code 200)
    if response.status_code == 200:
        # Parse the JSON response
        results = response.json()["results"]["bindings"]

        # Extract the relations and labels
        relations = [(result["relation"]["value"]) for result in results]

        return relations

    else:
        # If the request was not successful, raise an exception
        raise Exception(f"Error: Unable to retrieve data from Wikidata. Status code: {response.status_code}")


def check_best_similarity(label, list_of_heads):
    res_element = []
    for h in list_of_heads:
        if str(h[0]).lower() == str(label).lower() and str(h[2]).lower() != '':
            res_element = h
            break
        else:
            res_element = list_of_heads[0]
    return res_element[2]


def add_backslash_to_quotes(input_string):
    # input_string = input_string.replace("'", "\'")
    print(input_string[:2])
    print(input_string[-2:])
    if input_string[:2] == "\"'" and input_string[-2:] == "'\"":
        print(input_string)
        input_string = input_string[2:-2]
        print(input_string)

    if input_string[0] == "\"" and input_string[-1] == "\"":
        input_string = input_string[1:-1]
        print(input_string)

    input_string = repr(input_string)

    if input_string[0] != "\"" and input_string[-1] != "\"":
        input_string = input_string.replace('"', '\\"')
        input_string = "\"" + input_string + "\""

    if input_string[0] == "\"" and input_string[1] == "\"":
        input_string = input_string.replace("\"\"", "\"")
        print(input_string)
        print("!!!!!!!!check why here!!!!!")
        exit(1)

    # print(input_string)
    # exit(1)

    # else:
    # print("input:"+input_string)
    # input_string = input_string.replace('\"', '\\"')[2:-2]
    # input_string = input_string.replace('\\\\\\', '\\')
    # need to be fixed
    # input_string = input_string.replace('"Eat, Pray, Love"', '\\"Eat, Pray, Love\\"')
    # input_string = input_string.replace('"Adjustment Team"', '\\"Adjustment Team\\"')

    input_string = input_string.replace("\\\'", "\'")
    input_string = input_string.replace("\\\\\"", "\"")
    input_string = input_string.replace("\\u200e", "\u200e")
    # input_string = input_string.replace('"', '\"')
    return input_string


def is_valid_json(line):
    try:
        json.loads(line)
        return True
    except json.JSONDecodeError:
        print("invalid:" + line)
        return False


def extract_triples(lines, processed_claims, entities_dict, relations_dict, args):
    triples = []

    dataset_path = args['--path']

    for line in lines:

        print(line)
        if not is_valid_json(line):
            print("invalid string:" + line)
            line = ("{\"head\": " + add_backslash_to_quotes((line.split("\"head\": ")[1].split(",	\"type\":")[0]))
                    + ",	\"type\": " + add_backslash_to_quotes(
                        (line.split(",	\"type\": ")[1].split(",	\"tail\": ")[
                            0])) + ",	\"tail\": " + add_backslash_to_quotes(
                        (line.split(",	\"tail\": ")[1].split(" , \"claim\":")[0])) + " , \"claim\":" + add_backslash_to_quotes((
                        line.split(", \"claim\":")[1].split(" , \"id\":")[0])) + ", \"id\":" + line.split(", \"id\":")[1])

            print("fixed line check:" + line + "->valid check now:" + str(is_valid_json(line)))
        #            exit(1)
        print(line)
        elements_list = json.loads(line)
        query = (elements_list["claim"])
        idd = (elements_list["id"])  # query.replace("{'", "").replace("': '", ": ").replace("', '", " ").replace("'}", "")

        if query[0] == "\"" and query[-1] == "\"":
            query = query[1:-1]
        else:
            query = query

        if query in processed_claims:
            continue

        print("Not processed:" + query)
        # exit(1)
        if elements_list["head"] == "" or elements_list["type"] == "" or elements_list["tail"] == "":
            continue

        if elements_list["head"][0] == "'" and elements_list["head"][-1] == "'":
            head = elements_list["head"][1:-1]
        else:
            head = elements_list["head"]

        if elements_list["tail"][0] == "'" and elements_list["tail"][-1] == "'":
            tail = elements_list["tail"][1:-1]
        else:
            tail = elements_list["tail"]

        if elements_list["type"][0] == "'" and elements_list["type"][-1] == "'":
            rel = elements_list["type"][1:-1]
        else:
            rel = elements_list["type"]

        if head not in query or tail not in query:
            continue
        components = "mgenre_el"
        payload = {
            "query": query,  # head+" "+relation + " "+ tail,
            "components": components,
            "lang": "en",
            "mg_num_return_sequences": 5,
            "ent_mentions": [
                {
                    "start": query.index(head),
                    "end": query.index(head) + len(head),
                    "surface_form": head
                },
                {
                    "start": query.index(tail),
                    "end": query.index(tail) + len(tail),
                    "surface_form": tail
                }
            ]
        }
        headers = {
            'Content-Type': 'application/json'
        }
        # local url
        # http://neamt.cs.upb.de:6100/custom-pipeline
        if head not in entities_dict or tail not in entities_dict:
            response = requests.post("http://porque.cs.upb.de/porque-neamt/custom-pipeline", headers=headers, json=payload,
                                     timeout=600)
            link_info = response.json()
            print(link_info)
            if len(link_info) != 0:
                head_IRI = check_best_similarity(label=head, list_of_heads=link_info['ent_mentions'][0][
                    'link_candidates'])  # link_info['ent_mentions'][0]['link_candidates'][0][2]
                tail_IRI = check_best_similarity(label=tail, list_of_heads=link_info['ent_mentions'][1][
                    'link_candidates'])  # link_info['ent_mentions'][1]['link_candidates'][0][2]
            else:
                head_IRI = ''
                tail_IRI = ''
        else:
            head_IRI = entities_dict[head]
            tail_IRI = entities_dict[tail]
        # Example usage:
        # search_term = re
        if head_IRI != '' and tail_IRI != '':
            relations = []
            entities_dict[head] = head_IRI
            entities_dict[tail] = tail_IRI
            if repr(rel) not in relations_dict:
                # exit(1)
                print("querying wikidata:" + repr(rel))
                relations.append(query_wikidata(rel))
                # exit(1)

                if len(relations) > 0:
                    relation = relations[0]
                    print(len(relation))
                    print(relation)
                    if len(relation) > 0:
                        relations_dict[rel] = relation
                    else:
                        #                     testing phase
                        relations_dict[rel] = 'N/A'
                else:
                    relation = ''
            else:
                relations.append(relations_dict[repr(rel)])
            # Print the results
            for relation in relations:
                print(f"Relation IRI: {relation}")

            # "head: architecture type: part of tail: History of art"
            if len(relation) > 0 and relation != '' and relation != 'N/A':
                relation = str(relation).strip("[]'")
                print("relation:" + relation)
                if (relation[0] == "'" and relation[-1] == "'") or (relation[0] == "\"" and relation[-1] == "\""):
                    relation = "'" + relation[1:-1] + "'"

                if str(relation).startswith("[\'ttp") or str(relation).startswith("[\'tp") or str(relation).startswith(
                        "[\'p"):
                    raise
                print("relation:" + relation)

                triple = (
                    "https://www.wikidata.org/wiki/" + head_IRI, relation, "https://www.wikidata.org/wiki/" + tail_IRI)
                triples.append([triple, add_backslash_to_quotes(head), add_backslash_to_quotes(rel), add_backslash_to_quotes(tail), add_backslash_to_quotes(query), add_backslash_to_quotes(idd)])

                #                 save every 5 triples togather
                if len(triples) % 500 == 0:
                    # Define the file path
                    output_file_path = dataset_path + 'output_triples_IRIs.jsonl'
                    count = 0
                    # Open the file for writing
                    with open(output_file_path, 'a') as file:
                        # Serialize the list to JSON and write it to the file
                        for triple in triples:
                            file.write("{\"triple\":\"" + str(triple[0])[1:-1] + "\",\t\"subject\":" + triple[
                                1] + ",\t\"predicate\":" + triple[2] + ",\t\"object\":" + triple[
                                           3] + ",\t\"claim\":" + triple[4] + ",\t\"id\":" + triple[5] + "}\n")
                            print("saving:" + triple[4])

                    # Define the file path
                    entities_file_path = dataset_path + 'entities_dictionary.jsonl'

                    # Open the file for writing
                    with open(entities_file_path, 'w') as file:
                        # Serialize the dictionary to JSON and write it to the file
                        for entity in entities_dict:
                            file.write("{" + add_backslash_to_quotes(entity) + ":\"" + str(entities_dict[entity]) + "\"}\n")

                    # Define the file path
                    relations_file_path = dataset_path + 'relations_dictionary.jsonl'

                    # Open the file for writing
                    with open(relations_file_path, 'w') as file:
                        # Serialize the dictionary to JSON and write it to the file
                        for rel in relations_dict:
                            if not isinstance(relations_dict[rel],
                                              list):  # relations_dict[rel][0][0] == "[" and relations_dict[rel][0][-1] == "]":
                                print("saving not list relation: " + str(relations_dict[rel]) + ":" + str(
                                    relations_dict[rel])[1:-1])
                                file.write("{" + add_backslash_to_quotes((rel)) + ":\"" + (relations_dict[rel]) + "\"}\n")
                            else:  # if relations_dict[rel][0] != "[" and relations_dict[rel][-1] != "]":
                                print("saving relation: " + str(relations_dict[rel][0]))
                                file.write("{" + add_backslash_to_quotes((rel)) + ":\"" + (relations_dict[rel][0]) + "\"}\n")
                    triples = []

    return triples, entities_dict, relations_dict


def argparse_default(description=None):
    # Create an ArgumentParser instance
    parser = ArgumentParserMock()

    # Paths.
    parser.add_argument("--path", default='/upb/users/u/uqudus/profiles/unix/cs/NEBULA/TripleExtraction/rebel_output/FEVER/output/output_dev/')

    if description is None:
        return parser.parse_args()
    else:
        return parser.parse_args(description)


if __name__ == '__main__':
    args = argparse_default()
    # open a new file
    path = args['--path']
    dataset_path = path

    # Define the file path
    output_file_path = path + 'output_triples_IRIs.jsonl'

    with open(output_file_path, 'r') as file:
        lines2 = file.readlines()
    processed_claims = []
    processed_triples = []
    for ll in lines2:
        # print(ll)
        claim1 = json.loads(ll)['claim']
        processed_triples.append(json.loads(ll))
        processed_claims.append(claim1)
        print("processed claim:" + claim1)
    # exit(1)
    # this can be improved as nikit suggested to check in first 5 results instead of direct results
    file_path = path + 'output_triples_mapping.jsonl'  # Replace with the actual file path
    with open(file_path, 'r') as file:
        lines = file.readlines()

    print("total extracted triples:" + str(len(lines)))
    # Need to write code to check if its already extracted

    relations_dict = dict()
    entities_dict = dict()

    # Define the file path
    entities_file_path = path + 'entities_dictionary.jsonl'

    with open(entities_file_path, 'r') as file:
        entity_lines = file.readlines()

    processed_entities = []
    for ll in entity_lines:
        print(ll)
        dic_ent = json.loads(ll)
        # j_res = repr(dic_ent.keys())
        processed_entities.append(dic_ent)
        entities_dict[list(dic_ent.keys())[0]] = dic_ent[list(dic_ent.keys())[0]]

    # Define the file path
    relations_file_path = path + 'relations_dictionary.jsonl'

    with open(relations_file_path, 'r') as file:
        relation_lines = file.readlines()

    processed_relations = []
    for ll in relation_lines:
        # print("line:" + ll)
        dic_ent = json.loads(ll)
        # print("actual key:" + str(dic_ent.keys()))
        processed_relations.append(dic_ent)
        relations_dict[list(dic_ent.keys())[0]] = dic_ent[list(dic_ent.keys())[0]]

    # exit(1)
    # processed_relations.append(json.loads(ll))

    # ast.literal_eval

    result, entities, relations = extract_triples(lines, processed_claims, entities_dict, relations_dict, args)

    print(f'results saved to {path}')

    # for triple in result:
    #     print(triple)
