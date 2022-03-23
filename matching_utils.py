import re

from bleach import clean
from fuzzywuzzy import fuzz
import jellyfish as jf
from cleanco import basename


def f_get_modified_str(input_str):
    # Transform to lower case
    input_str = input_str.strip().lower()
    # Replace '&' char to word 'and'
    input_str = input_str.replace(" & ", " and ")
    # Remove all other special chars
    input_str = " ".join(re.findall("[a-zA-Z0-9]+", input_str))
    # Remove extra spaces
    input_str = " ".join(input_str.split())
    return input_str.strip()


def to_unicode(obj, encoding="utf-8"):
    if not isinstance(obj, str):
        return obj.decode(encoding, errors="ignore")
    return obj


def name_match(name1, name2):
    name1 = name1.split()
    name2 = name2.split()
    if name1 and name2:
        ratio1 = 0.0
        for i in range(len(name1)):
            for j in range(i, len(name2)):
                if fuzz.ratio(name1[i], name2[j]) > 90:
                    ratio1 += 1.0
                    break
        try:
            ratio1 = 100 * (ratio1 / len(name1))
        except ZeroDivisionError:
            ratio1 = 0.0
        ratio2 = 0.0
        for i in range(len(name2)):
            for j in range(i, len(name1)):
                if fuzz.ratio(name2[i], name1[j]) > 90:
                    ratio2 += 1.0
                    break
        try:
            ratio2 = 100 * (ratio2 / len(name2))
        except ZeroDivisionError:
            ratio2 = 0.0
        return int(max(ratio1, ratio2))
    return 0


def f_name_match_score(str1, str2):
    # Transform name
    if len(str1) > 1 and len(str2) > 1:
        str1 = clean_company_legal_entities(str1)
        str2 = clean_company_legal_entities(str2)
        str1 = f_get_modified_str(str1)
        str2 = f_get_modified_str(str2)
        print(str1)
        print(str2)
        # Convert to unicode to avoid error
        str1 = to_unicode(str1)
        str2 = to_unicode(str2)
        # Compute match scores
        score1 = fuzz.ratio(str1, str2)
        score2 = fuzz.token_sort_ratio(str1, str2)
        score3 = jf.levenshtein_distance(str1, str2)
        score3 = (1 - (score3 / max(len(str1), len(str2)))) * 100
        # score4 = name_match(str1, str2)
        if len(str1.split()) == 1:
            score4 = fuzz.ratio(str1.split()[0], str2.split()[0])
        s_max = max(score1, score2, score3)
    else:
        s_max = 0
    return s_max


def clean_company_legal_entities(entity_name):
    rp = [
        "LLC",
        "PJSC",
        "CJSC",
        "IP",
        "GUP",
        "OJSC",
        "JSC",
        "OOO",
        "OO",
        "Limited Liability Company",
        "Open Joint Stock Company",
        "Public Joint Stock Company",
        "Joint Stock Company",
        "AO",
    ]
    rp = [legal_name.lower() for legal_name in rp]
    for k in rp:
        if k in entity_name:
            entity_name = entity_name.replace(k, "")
    # Using basename twice for better clean
    entity_name = basename(entity_name)
    entity_name = basename(entity_name)
    return entity_name.strip()
