import re


def replace_quotes(json_string):
    json_string = str(json_string)
    # Match keys and string values enclosed in single quotes

    """- after    '{'
    - before    '}'
    - after    space
    - after    ':'
    - before    ':'"""

    pattern = r"(?<=\{|:|\s)('[^']*')(?=\}|:|\s)|('[^']*')(?=:)"


    def replace(match):
        # Replace single quotes with double quotes
        return match.group(1).replace("'", '"')

    # Replace single quotes with double quotes for keys and string values
    result = re.sub(pattern, replace, json_string)
    return result


def make_standard_json(json_string):
    json_string = replace_quotes(json_string)
    json_string = json_string.replace("False", "false").replace("True", "true")
    return json_string

