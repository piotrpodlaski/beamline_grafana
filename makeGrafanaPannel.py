#!/usr/bin/env python3
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
import json

INKSCAPE_NS = "{http://www.inkscape.org/namespaces/inkscape}"



def get_text_PVs(svg_path):
    try:
        tree = ET.parse(svg_path)
        root = tree.getroot()

        PVs = {}
        for elem in root.iter():
            elem_id = elem.attrib.get("id")
            if elem_id and elem_id.startswith("text-"):
                PVs[int(elem_id[5:])]=elem.attrib.get(INKSCAPE_NS + "label").split(' ')
        return dict(sorted(PVs.items()))
    except Exception as e:
        print(f"Error reading '{svg_path}': {e}")
        return {}


def main():
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print("Usage: python3 script.py <file.svg> [template.json]")
        print()
        print("  <file.svg>      SVG file whose contents will be embedded")
        print("  [template.json] JSON template to use (default: ./json/template.json)")
        sys.exit(1)

    svg_path = Path(sys.argv[1])
    helper_path = Path("js/helpers.js")
    template_path = Path(sys.argv[2]) if len(sys.argv) == 3 else Path("./json/template.json")
    textPVs = get_text_PVs(svg_path)
    print(textPVs);


    if not template_path.is_file():
        print(f"Error: template JSON file not found: {template_path}")
        sys.exit(1)

    print(template_path)

    try:
        with open(template_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error reading JSON template '{template_path}': {e}")
        sys.exit(1)

    with open(svg_path, "r", encoding="utf-8") as f:
        svg_text = f.read()

    with open(helper_path, "r", encoding="utf-8") as f:
        helper_text = f.read()
    
    helper_text+='\n\n'

    mappings = []
    targets = []
    for idx, svg_id in textPVs.items():
        mappings.append({
            "mappedName": str(idx),   # or svg_id if you prefer mappedName == svgId
            "svgId": "text-"+str(idx)	
        })

        targets.append({
        	  "alias": "",
      "aliasPattern": "",
      "datasource": {
        "type": "sasaki77-archiverappliance-datasource",
        "uid": "6ATSoo3Nk"
      },
      "functions": [],
      "hide": False,
      "operator": "last",
      "refId": "E"+str(idx),
      "regex": False,
      "stream": False,
      "strmCap": "",
      "strmInt": "",
      "target": svg_id[0]
        	})
        print(svg_id)
        JSmapper = f"\nmapValue(svgmap, '{idx}', '{svg_id[0]}', '{svg_id[1]}', {svg_id[2]});"
        helper_text+=JSmapper
    # Insert SVG into options.svgSource
    if "options" not in data or not isinstance(data["options"], dict):
        data["options"] = {}
    data["options"]["svgSource"] = svg_text
    data["options"]["eventSource"] = helper_text
    data["options"]["svgMappings"] = mappings
    data["targets"] = targets


    json_output_dir = Path("json")
    output_path = json_output_dir / (svg_path.stem + ".json")


    try:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error writing output file '{output_path}': {e}")
        sys.exit(1)

    print(f"Created: {output_path}")

if __name__ == "__main__":
    main()