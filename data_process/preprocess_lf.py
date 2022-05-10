import re

def valid(m_str):
    if not any(str(n) in m_str for n in range(0, 9)):
        return False
    return True

def preprocess_sparql(sparql):
    """Preprocess for sparql logic form"""
    sparql = sparql.strip()
    sparql = sparql.lower()  # lower
    sparql = re.sub('\t', ' ', sparql)  # replace \t with ' '
    # 0. remove the meaningless header and \n
    sparql = sparql.replace('#MANUAL SPARQL'.lower(), '')
    sparql = sparql.replace('prefix ns: <http://rdf.freebase.com/ns/>', '')
    sparql = sparql.replace('\n', ' ')  # remove \n
    sparql = re.sub('\n', ' ', sparql)  # remove \n
    # 1. replace entity
    patterns = [possible_entity_pattern for possible_entity_pattern in re.findall('ns:m.[a-z_0-9]*', sparql) if
                valid(possible_entity_pattern)]

    for i, pattern in enumerate(patterns):
        num = i+1
        sparql = sparql.replace(pattern, '#entity%s#'%(num))
    # 2. remove type header
    sparql = re.sub(r"select distinct[ ]*\?x[ ]*where[ ]*{[ ]*", " ", sparql)  # remove main clause
    sparql = re.sub('}[ ]?$', ' ', sparql)  # remove } in the tail
    sparql = sparql.replace(
        "filter (?x != ?c) filter (!isliteral(?x) or lang(?x) = '' or langmatches(lang(?x), 'en'))",
        '<sparql-header-1> ')  # replace fixed header of one type LF
    sparql = sparql.replace(
        "filter (?x != #entity#) filter (!isliteral(?x) or lang(?x) = '' or langmatches(lang(?x), 'en'))",
        "<sparql-header-2> ")  # replace fixed header of another type LF
    # 3. sep special chars
    sparql = re.sub(r'([a-z_0-9!?) \'#])([{()}])([#, )a-z_0-9!?])', r"\1 \2 \3", sparql)  # sep ( ) in word start
    sparql = re.sub(r'([a-z_0-9!?)\" \'])\^\^([, )a-z_0-9!?])', r"\1 ^^ \2", sparql)  # sep ^^
    sparql = re.sub(r'([a-z_0-9@)])["\'] ', r'\1 `` ', sparql)  # sep " in word tail
    sparql = re.sub(r' ["\']([a-z_0-9@)])', r" '' \1", sparql)  # sep " in word start
    sparql = re.sub(' [ ]+', ' ', sparql).strip()  # extra whitespace
    return sparql

if __name__ == "__main__":

    # Test preprocessing functionality: 
    # input: original sparql query; output: preprocessed sparql
    lf = "PREFIX ns: <http://rdf.freebase.com/ns/>\nSELECT DISTINCT ?x\nWHERE {\nFILTER (?x != ?c)\nFILTER (!isLiteral(?x) OR lang(?x) = '' OR langMatches(lang(?x), 'en'))\n?c ns:organization.organization.leadership ?k .\n?k ns:organization.leadership.person ns:m.02vymvp . \n?c ns:education.educational_institution.mascot ?x .\n}\n"
    new_lf = preprocess_sparql(lf)

