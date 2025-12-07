#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import argparse
import re

INKSCAPE_NS = "http://www.inkscape.org/namespaces/inkscape"
ET.register_namespace("inkscape", INKSCAPE_NS)


def get_child_text(widget, tag, default=""):
    elem = widget.find(tag)
    if elem is None or elem.text is None:
        return default
    return elem.text.strip()


def get_child_int(widget, tag, default=0):
    elem = widget.find(tag)
    if elem is None or elem.text is None:
        return default
    try:
        return int(float(elem.text.strip()))
    except ValueError:
        return default


def get_font_props(widget, default_family="Sans", default_size=12):
    """
    Extract font family and size from nested <font><font ...> element.
    """
    font_outer = widget.find("font")
    if font_outer is not None:
        font_inner = font_outer.find("font")
        if font_inner is not None:
            family = font_inner.get("family", default_family)
            size_attr = font_inner.get("size")
            if size_attr is not None:
                try:
                    size = float(size_attr)
                except ValueError:
                    size = default_size
            else:
                size = default_size
            return family, size
    return default_family, default_size


def get_foreground_color(widget, default=(0, 0, 0)):
    """
    Extract foreground color RGB from <foreground_color><color ...> if present.
    """
    fg = widget.find("foreground_color")
    if fg is not None:
        color = fg.find("color")
        if color is not None:
            try:
                r = int(color.get("red", default[0]))
                g = int(color.get("green", default[1]))
                b = int(color.get("blue", default[2]))
                return (r, g, b)
            except ValueError:
                pass
    return default


def parse_bob(bob_path):
    tree = ET.parse(bob_path)
    root = tree.getroot()

    items = []
    max_x = 0
    max_y = 0

    for widget in root.findall("widget"):
        wtype = widget.get("type", "")
        if wtype not in ("label", "textupdate"):
            continue

        x = get_child_int(widget, "x", 0)
        y = get_child_int(widget, "y", 0)
        width = get_child_int(widget, "width", 80)
        height = get_child_int(widget, "height", 20)

        widget_name = get_child_text(widget, "name", "")

        if wtype == "label":
            visible_text = get_child_text(widget, "text", "")
            pv_name = ""  # not applicable
        else:  # textupdate
            raw_pv = get_child_text(widget, "pv_name", "")
            # Remove "ca://" prefix if present
            pv_name = raw_pv[5:] if raw_pv.startswith("ca://") else raw_pv
            # Visible text is the placeholder you requested
            visible_text = "22.2C"

        font_family, font_size = get_font_props(widget)
        color = get_foreground_color(widget, default=(0, 0, 0))

        max_x = max(max_x, x + width)
        max_y = max(max_y, y + height)

        items.append(
            {
                "type": wtype,
                "widget_name": widget_name,
                "pv_name": pv_name,
                "text": visible_text,
                "x": x,
                "y": y,
                "width": width,
                "height": height,
                "font_family": font_family,
                "font_size": font_size,
                "color": color,
            }
        )

    max_x += 20
    max_y += 20
    return items, max_x, max_y


def items_to_svg(items, width, height):
    """
    Build an SVG with:
      id="text-%d"
      inkscape:label = PV name for textupdate widgets
      text content:
        - labels: label text
        - textupdates: placeholder "22.2C"
    """
    svg = ET.Element(
        "svg",
        attrib={
            "xmlns": "http://www.w3.org/2000/svg",
            "width": str(width),
            "height": str(height),
            "viewBox": f"0 0 {width} {height}",
        },
    )

    text_counter = 1

    for item in items:
        text = item["text"]
        if not text:
            continue

        x = item["x"]
        y = item["y"]
        h = item["height"]
        font_family = item["font_family"]
        font_size = item["font_size"]
        r, g, b = item["color"]
        pv_name = item["pv_name"]
        wtype = item["type"]

        baseline_y = y + 0.75 * h

        elem_id = f"text-{text_counter}"
        text_counter += 1

        text_elem = ET.SubElement(
            svg,
            "text",
            {
                "id": elem_id,
                "x": str(x),
                "y": str(baseline_y),
                "font-family": font_family,
                "font-size": str(font_size),
                "fill": f"rgb({r},{g},{b})",
            },
        )

        # Only textupdate widgets get an inkscape:label, which is the PV
        if wtype == "textupdate" and pv_name:
            text_elem.set(f"{{{INKSCAPE_NS}}}label", pv_name)

        text_elem.text = text

    return svg


def write_svg(svg_element, output_path):
    tree = ET.ElementTree(svg_element)
    tree.write(output_path, encoding="utf-8", xml_declaration=True)


def main():
    parser = argparse.ArgumentParser(
        description="Convert CS-Studio .bob display to an Inkscape-compatible SVG (for your SVG→JSON script)."
    )
    parser.add_argument("input", help="Input .bob XML file")
    parser.add_argument("output", help="Output .svg file")
    args = parser.parse_args()

    items, w, h = parse_bob(args.input)
    svg = items_to_svg(items, w, h)
    write_svg(svg, args.output)


if __name__ == "__main__":
    main()
