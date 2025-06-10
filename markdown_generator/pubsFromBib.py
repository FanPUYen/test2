#!/usr/bin/env python
# coding: utf-8

# # Publications markdown generator for academicpages
# 
# Takes a set of bibtex of publications and converts them for use with [academicpages.github.io](academicpages.github.io). This is an interactive Jupyter notebook ([see more info here](http://jupyter-notebook-beginner-guide.readthedocs.io/en/latest/what_is_jupyter.html)). 
# 
# The core python code is also in `pubsFromBibs.py`. 
# Run either from the `markdown_generator` folder after replacing updating the publist dictionary with:
# * bib file names
# * specific venue keys based on your bib file preferences
# * any specific pre-text for specific files
# * Collection Name (future feature)
# 
# TODO: Make this work with other databases of citations, 
# TODO: Merge this with the existing TSV parsing solution


from time import strptime
import string
import html
import os
import re


def parse_bib_file(filename):
    """Minimal BibTeX parser returning dict keyed by entry id."""
    entries = {}
    current = None
    entry_lines = []
    with open(filename, encoding="utf-8") as fh:
        for line in fh:
            stripped = line.strip()
            if stripped.startswith("@"):
                if current:
                    entries[current] = _process_entry(entry_lines)
                    entry_lines = []
                current = stripped.split("{", 1)[1].split(",", 1)[0].strip()
            if current:
                entry_lines.append(line)
            if stripped.endswith("}") and current and not stripped.startswith("@"):  # end entry
                entries[current] = _process_entry(entry_lines)
                current = None
                entry_lines = []
    if current and entry_lines:
        entries[current] = _process_entry(entry_lines)
    return entries


def _process_entry(lines):
    fields = {}
    body = "".join(lines)
    for field, val in re.findall(r"(\w+)\s*=\s*(\{[^\}]*\}|\"[^\"]*\"|[^,\n]+)", body):
        val = val.strip().rstrip(',')
        if val.startswith("{") and val.endswith("}"):
            val = val[1:-1]
        if val.startswith('"') and val.endswith('"'):
            val = val[1:-1]
        fields[field] = val
    return fields

#todo: incorporate different collection types rather than a catch all publications, requires other changes to template
publist = {
    "proceeding": {
        # use repository sample bib file
        "file" : "../files/bibtex1.bib",
        "venuekey": "booktitle",
        "venue-pretext": "In the proceedings of ",
        "collection" : {"name":"publications",
                        "permalink":"/publication/"}
        
    },
    "journal":{
        # same sample bib file covers journal articles
        "file": "../files/bibtex1.bib",
        "venuekey" : "journal",
        "venue-pretext" : "",
        "collection" : {"name":"publications",
                        "permalink":"/publication/"}
    } 
}

html_escape_table = {
    "&": "&amp;",
    '"': "&quot;",
    "'": "&apos;"
    }

def html_escape(text):
    """Produce entities within text."""
    return "".join(html_escape_table.get(c,c) for c in text)


for pubsource in publist:
    entries = parse_bib_file(publist[pubsource]["file"])

    #loop through the individual references in a given bibtex file
    for bib_id, b in entries.items():
        #reset default date
        pub_year = "1900"
        pub_month = "01"
        pub_day = "01"
        
        try:
            pub_year = f'{b["year"]}'

            #todo: this hack for month and day needs some cleanup
            if "month" in b.keys(): 
                if(len(b["month"])<3):
                    pub_month = "0"+b["month"]
                    pub_month = pub_month[-2:]
                elif(b["month"] not in range(12)):
                    tmnth = strptime(b["month"][:3],'%b').tm_mon   
                    pub_month = "{:02d}".format(tmnth) 
                else:
                    pub_month = str(b["month"])
            if "day" in b.keys(): 
                pub_day = str(b["day"])

                
            pub_date = pub_year+"-"+pub_month+"-"+pub_day
            
            #strip out {} as needed (some bibtex entries that maintain formatting)
            clean_title = b["title"].replace("{", "").replace("}","").replace("\\","").replace(" ","-")    

            url_slug = re.sub("\\[.*\\]|[^a-zA-Z0-9_-]", "", clean_title)
            url_slug = url_slug.replace("--","-")

            md_filename = (str(pub_date) + "-" + url_slug + ".md").replace("--","-")
            html_filename = (str(pub_date) + "-" + url_slug).replace("--","-")

            #Build Citation from text
            citation = ""

            authors = b.get("author", "")
            if authors:
                citation += authors + ", "

            citation += "\"" + html_escape(b["title"].replace("{", "").replace("}", "").replace("\\", "")) + ".\""

            venue_field = b.get(publist[pubsource]["venuekey"], "")
            venue = publist[pubsource]["venue-pretext"] + venue_field.replace("{", "").replace("}", "").replace("\\", "")

            citation = citation + " " + html_escape(venue)
            citation = citation + ", " + pub_year + "."

            
            ## YAML variables
            md = "---\ntitle: \""   + html_escape(b["title"].replace("{", "").replace("}","").replace("\\","")) + '"\n'
            
            md += """collection: """ +  publist[pubsource]["collection"]["name"]

            md += """\npermalink: """ + publist[pubsource]["collection"]["permalink"]  + html_filename
            
            note = False
            if "note" in b.keys():
                if len(str(b["note"])) > 5:
                    md += "\nexcerpt: '" + html_escape(b["note"]) + "'"
                    note = True

            md += "\ndate: " + str(pub_date) 

            md += "\nvenue: '" + html_escape(venue) + "'"
            
            url = False
            if "url" in b.keys():
                if len(str(b["url"])) > 5:
                    md += "\npaperurl: '" + b["url"] + "'"
                    url = True

            md += "\ncitation: '" + html_escape(citation) + "'"

            md += "\n---"

            
            ## Markdown description for individual page
            if note:
                md += "\n" + html_escape(b["note"]) + "\n"

            if url:
                md += "\n[Access paper here](" + b["url"] + "){:target=\"_blank\"}\n" 
            else:
                md += "\nUse [Google Scholar](https://scholar.google.com/scholar?q="+html.escape(clean_title.replace("-","+"))+"){:target=\"_blank\"} for full citation"

            md_filename = os.path.basename(md_filename)

            with open("../_publications/" + md_filename, 'w', encoding="utf-8") as f:
                f.write(md)
            print(f'SUCESSFULLY PARSED {bib_id}: \"', b["title"][:60],"..."*(len(b['title'])>60),"\"")
        # field may not exist for a reference
        except KeyError as e:
            print(f'WARNING Missing Expected Field {e} from entry {bib_id}: \"', b["title"][:30],"..."*(len(b['title'])>30),"\"")
            continue
