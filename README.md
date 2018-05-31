# eki2kindle
Turn XML downloads from the Eesti Keele Instituut (https://www.eki.ee/litsents/) into usable Kindle dictionaries

It requires EstNLKT (https://github.com/estnltk/estnltk) to generate inflected forms for headwords,
and uses lxml for XML processing.

For using, create a dic.opf file based on the existing dic.opf.sample file. Run eki2kindle on an EKI XML file and then
run KindleGen with

    kindlegen dic.opf -c2 -verbose -dont_append_source