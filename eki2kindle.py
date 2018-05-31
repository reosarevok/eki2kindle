from lxml import etree
from estnltk import synthesize


def synthesize_forms(headword, wordtype):
    forms = []
    forms_S = ['sg ab', 'sg abl', 'sg ad', 'sg adt', 'sg all', 'sg el', 'sg es', 'sg g', 'sg ill', 'sg in', 'sg kom',
               'sg p', 'sg pl', 'sg sg', 'sg ter', 'sg tr', 'pl ab', 'pl abl', 'pl ad', 'pl adt', 'pl all', 'pl el',
               'pl es', 'pl g', 'pl ill', 'pl in', 'pl kom', 'pl n', 'pl p', 'pl pl', 'pl sg', 'pl ter', 'pl tr']
    forms_V = ['b', 'd', 'da', 'des', 'ge', 'gem', 'gu', 'ks', 'ksid', 'ksime', 'ksin', 'ksite', 'ma', 'maks', 'mas',
               'mast', 'mata', 'me', 'n', 'neg ge', 'neg gem', 'neg gu', 'neg ks', 'neg nud', 'neg nuks', 'neg o',
               'neg vat', 'nud', 'nuks', 'nuksid', 'nuksime', 'nuksin', 'nuksite', 'nuvat', 'o', 's', 'sid', 'sime',
               'sin', 'site', 'ta', 'tagu', 'taks', 'takse', 'tama', 'tav', 'tavat', 'te', 'ti', 'tud', 'tuks', 'tuvat',
               'v', 'vad', 'vat']
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


# The EKI files include their own bold and emphasis sections - we need to deal with them
def unescape_definition(definition):
    definition = definition.replace('&ema;', '<em>')
    definition = definition.replace('&eml;', '</em>')
    definition = definition.replace('&ba;', '<b>')
    definition = definition.replace('&bl;', '</b>')
    definition = definition.replace('&supa;', '<sup>')
    definition = definition.replace('&supl;', '</sup>')
    return definition


def process_eki_dictionary(file):
    tree = etree.parse(file)
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
                definitionEntry['definitionTexts'].append(unescape_definition(definitionText.text))
            definitionExamples = definition.findall('c:tg/c:ng/c:n', dictionaryXML.nsmap)
            for definitionExample in definitionExamples:
                definitionEntry['definitionExamples'].append(unescape_definition(definitionExample.text))
            entry['definitions'].append(definitionEntry)
        if wordtype is not None:
            entry['forms'] = synthesize_forms(headword, wordtype)
        dictionary.append(entry)
    return dictionary


def build_dictionary(processed_dictionary, destination_file):
    NSMAP = {"mbp": 'https://kindlegen.s3.amazonaws.com/AmazonKindlePublishingGuidelines.pdf',
             "idx": 'http://www.mobipocket.com/idx'}

    page = etree.Element('html', lang="et", nsmap=NSMAP)
    dictionary = etree.ElementTree(page)

    headElt = etree.SubElement(page, 'head')
    bodyElt = etree.SubElement(page, 'body')

    metaElt = etree.SubElement(headElt, 'meta', charset='UTF-8')

    framesetElt = etree.SubElement(bodyElt, '{https://kindlegen.s3.amazonaws.com/AmazonKindlePublishingGuidelines.pdf}frameset')

    for entry in processed_dictionary:
        entryElt = etree.SubElement(framesetElt, '{http://www.mobipocket.com/idx}entry')
        shortElt = etree.SubElement(entryElt, '{http://www.mobipocket.com/idx}short')
        orthElt = etree.SubElement(shortElt, '{http://www.mobipocket.com/idx}orth', value=entry['headword'])
        headwordElt = etree.SubElement(orthElt, 'b')
        headwordElt.text = entry['headword']
        if entry['wordtype'] is not None:
            headwordElt.tail = " (" + entry['wordtype'] + ")"
        if entry['forms']:
            inflElt = etree.SubElement(orthElt, '{http://www.mobipocket.com/idx}infl')
            for form in entry['forms']:
                iformElt = etree.SubElement(inflElt, '{http://www.mobipocket.com/idx}iform', value=form, exact="yes")
        # We load the definitions and examples as strings to get around the issues with the embedded bold / emphasis
        for definition in entry['definitions']:
            divElt = etree.SubElement(shortElt, 'div')
            for definitionText in definition['definitionTexts']:
                definitionString = "<p>" + definitionText + "</p>"
                definitionElt = etree.fromstring(definitionString)
                divElt.append(definitionElt)
            listElt = etree.SubElement(divElt, 'ul')
            for exampleText in definition['definitionExamples']:
                exampleString = "<li>" + exampleText + "</li>"
                exampleElt = etree.fromstring(exampleString)
                listElt.append(exampleElt)
        hrElt = etree.SubElement(framesetElt, 'hr')

    dictionary.write(destination_file)


dictionary = process_eki_dictionary('psv_EKI_CCBY40.xml')
build_dictionary(dictionary, 'dictionary.html')
