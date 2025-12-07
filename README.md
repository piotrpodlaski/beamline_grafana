## Overview

This repository contains the tooling, SVG assets, and JSON templates used to generate Grafana panels that rely on the **ACE SVG panel plugin**.  The workflow is:

1. Draw the control-system display in CS-Studio as a `.bob` file.
2. Convert the `.bob` widgets to a lightweight SVG that preserves the text positions.
3. Polish the SVG in Inkscape (background art, colors, units, precision metadata).
4. Run the generator to combine the SVG, helper JavaScript, and a Grafana panel template into an importable JSON model.

Key directories:

| Path        | Description |
| ----------- | ----------- |
| `bob/`      | Original CS-Studio displays (`.bob`). |
| `svg/`      | Finished SVGs used as the visual layer in Grafana. |
| `json/`     | Panel exports generated for Grafana (plus `template.json`). |
| `js/`       | Helper code injected into the ACE SVG panel (`helpers.js`). |
| `bobToSvg.py` | Converts `.bob` files into minimal SVGs that retain widget text. |
| `makeGrafanaPannel.py` | Embeds an SVG into the ACE panel JSON and wires PV mappings. |

## Creating an SVG from a BOB display

1. **Model the layout in CS-Studio**  
   Use labels for static text and `textupdate` widgets for PV readbacks.  Provide meaningful widget names—the script keeps the ordering stable and extends the SVG canvas slightly to fit all widgets.

2. **Convert `.bob` → `.svg`**  
   Run:
   ```bash
   python3 bobToSvg.py bob/<display>.bob svg/<display>.svg
   ```
   The converter:
   - reads the `.bob` XML,
   - keeps only text-bearing widgets,
   - emits `<text>` nodes with ids like `text-1`, `text-2`, …,
   - stores the PV name inside the `inkscape:label` so Inkscape and the JSON generator can access it later.

3. **Finalize the SVG in Inkscape**  
   Open the generated SVG and:  
   - Add background artwork (e.g., exported PNGs) and align the text placeholders.  
   - For every `text-*` element, edit the `Object Properties → Label` (`inkscape:label`) to follow `PV_NAME UNIT PRECISION`, e.g. `NUTSBW:HECIRC:P_HE_RET MPa 3`. The generator will interpret these three space-separated fields.  
   - Adjust fonts, colors, or additional static annotations as needed.  
   - Keep the `text-*` ids intact—the scripts depend on them.

Already have an SVG that meets those requirements? Start at the next section and run the generator directly.

## Building a Grafana panel JSON from an SVG

1. **Prepare the template**  
   `json/template.json` already targets the `aceiot-svg-panel` plugin and references the default datasource (`sasaki77-archiverappliance-datasource`).  Update it if you need a different datasource or baseline panel options.  
   **Important:** the generated JSON only describes the panel body; Grafana dashboard placement (grid position, span, etc.) must be copied from an existing dashboard export and merged manually after generation.

2. **Generate the panel JSON**  
   ```bash
   python3 makeGrafanaPannel.py svg/<display>.svg json/template.json
   ```
   If the template argument is omitted, the script falls back to `json/template.json`.

   The script will:
   - Parse all `text-*` nodes, read the `inkscape:label`, and build the SVG ↔ PV mapping.
   - Append helper logic from `js/helpers.js` to the panel `eventSource`.  The helper expects the label format described above and calls `mapValue` with the PV name, unit, and numeric precision.
   - Embed the SVG markup directly into `options.svgSource`.
   - Emit the final panel description into `json/<display>.json`.

3. **Import into Grafana**  
   - Ensure the ACE SVG panel plugin is installed on your Grafana instance.  
   - Import the generated JSON (Dashboard → New → Import) and select the proper datasource if Grafana asks for confirmation.  
   - Verify that each mapped text element updates; tweak `helpers.js` or the SVG labels if any PV needs custom formatting.

## Tips

- Keep PV names free of spaces so the label parser can reliably split `PV`, `unit`, and `precision`. Use `°C` or similar symbols directly; the JSON generator preserves UTF-8.
- You can customize the update logic (color thresholds, alarm states, etc.) by editing `js/helpers.js` and re-running `makeGrafanaPannel.py`.
- When a new panel is needed, duplicate the template JSON to capture plugin-level options (panel size, repeat settings) before running the generator.
