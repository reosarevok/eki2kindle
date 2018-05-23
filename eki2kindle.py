from lxml import etree
from estnltk import synthesize
import json


def synthesize_forms(headword, wordtype):
    forms = []
    forms_S = ['sg ab', 'sg abl', 'sg ad', 'sg adt', 'sg all', 'sg el', 'sg es', 'sg g', 'sg ill', 'sg in', 'sg kom', 'sg p', 'sg pl', 'sg sg', 'sg ter', 'sg tr', 'pl ab', 'pl abl', 'pl ad', 'pl adt', 'pl all', 'pl el', 'pl es', 'pl g', 'pl ill', 'pl in', 'pl kom', 'pl n', 'pl p', 'pl pl', 'pl sg', 'pl ter', 'pl tr']
    forms_V = ['b', 'd', 'da', 'des', 'ge', 'gem', 'gu', 'ks', 'ksid', 'ksime', 'ksin', 'ksite', 'ma', 'maks', 'mas', 'mast', 'mata', 'me', 'n', 'neg ge', 'neg gem', 'neg gu', 'neg ks', 'neg nud', 'neg nuks', 'neg o', 'neg vat', 'nud', 'nuks', 'nuksid', 'nuksime', 'nuksin', 'nuksite', 'nuvat', 'o', 's', 'sid', 'sime', 'sin', 'site', 'ta', 'tagu', 'taks', 'takse', 'tama', 'tav', 'tavat', 'te', 'ti', 'tud', 'tuks', 'tuvat', 'v', 'vad', 'vat']
    if wordtype == 'V':
        # Need to deal with verbs with extra words ("meelde tuletama"). We take the word that needs conjugating here...
        if ' ' in headword:
            extra = headword.rsplit(' ', 1)[0]
            headword = headword.rsplit(' ', 1)[1]
        else:
            extra = None

        for form in forms_V:
            form_results = synthesize(headword, form)
            for result in form_results:
                # And we put them back together here. Won't help all the time, often real usage "PART1 blah blah PART2"
                if extra is not None:
                    result2 = result + ' ' + extra
                    forms.append(result2)
                    result = extra + ' ' + result
                forms.append(result)
    # TODO: figure out if we can get comparative forms of adjectives
    else:
        for form in forms_S:
            form_results = synthesize(headword, form)
            for result in form_results:
                forms.append(result)
    # We only need unique forms, since we just want this to redirect to the dictionary entries
    formSet = list(set(forms))
    return formSet


tree = etree.parse('psv_EKI_CCBY40.xml')
dictionaryXML = tree.getroot()
dictionary = []

for word in dictionaryXML:
    entry = {'definitions': [], 'forms': []}
    headword = word.find('c:P/c:mg/c:m', dictionaryXML.nsmap).text
    entry['headword'] = headword
    try:
        wordtype = word.find('c:P/c:mg/c:sl', dictionaryXML.nsmap).text
    except AttributeError:
        wordtype = None
    entry['wordtype'] = wordtype
    wordDefinitions = word.findall('c:S/c:tp', dictionaryXML.nsmap)
    for definition in wordDefinitions:
        definitionEntry = {'definitionTexts': [], 'definitionExamples': []}
        definitionTexts = definition.findall('c:tg/c:dg/c:d', dictionaryXML.nsmap)
        for definitionText in definitionTexts:
            definitionEntry['definitionTexts'].append(definitionText.text)
        definitionExamples = definition.findall('c:tg/c:ng/c:n', dictionaryXML.nsmap)
        for definitionExample in definitionExamples:
            definitionEntry['definitionExamples'].append(definitionExample.text)
        entry['definitions'].append(definitionEntry)
    if wordtype is not None:
        entry['forms'] = synthesize_forms(headword, wordtype)
    dictionary.append(entry)

with open('data.json', 'w') as fp:
    json.dump(dictionary, fp, indent=4)
