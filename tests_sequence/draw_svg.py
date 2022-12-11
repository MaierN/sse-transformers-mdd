import time
import json
import xml.etree.ElementTree as ET
from playwright.sync_api import sync_playwright
import re


# https://sequencediagram.org/


THIS_NAME = "this"


def san(s):
    escape = ["\\", "*", "/", "+", "-", '"']
    for c in escape:
        s = s.replace(c, f"\\{c}")
    return s


def draw_sequence_diagram(seq_data):
    draw_sequence_diagram.unk_count = 0

    out = ""

    out += f"title {seq_data['title']}\n"
    out += f'participant "**{THIS_NAME}**" as {THIS_NAME}\n'
    out += draw_elements(seq_data["sequence"])

    return out


draw_sequence_diagram.unk_count = 0


def draw_elements(elements):
    out = ""

    def append(s):
        nonlocal out
        if out:
            out += "\n"
        out += s

    for elt in elements:
        try:

            elt_type = elt["type"]

            if elt_type == "methodInvocation":
                to = elt["to"]
                if to == "### unk":
                    to = f"_{draw_sequence_diagram.unk_count}"
                    draw_sequence_diagram.unk_count += 1
                    append(f"participant \"//[...]//\" as {to}")
                elif len(to) > 0:
                    to = san('.'.join(to))
                else:
                    to = THIS_NAME
                append(
                    f"{THIS_NAME}->{to}:"
                    f"{san(elt['method'])}"
                )

            elif elt_type == "newInstance":
                pass  # TODO maybe need to get the variable "to"

            elif elt_type == "scopedVariable":
                if is_used(elt["name"], elements):
                    append(f"{THIS_NAME}->>*{san(elt['name'])}://create//")

            elif elt_type == "controlFlow":
                append(
                    f"aboxleft over {THIS_NAME}:**{san(elt['name'])}**"
                    + (f" {san(elt['value'])}" if elt["value"] else "")
                )

            elif elt_type == "blocks":
                blocks = elt["blocks"]
                name = elt["name"]

                for idx, block in enumerate(blocks):
                    append(
                        f"{f'alt _{name}_' if idx == 0 else 'else '}"
                        + (f"{block['guard']}" if block["guard"] else "")
                    )
                    append(draw_elements(block["contents"]))

                append("end")

            else:
                raise Exception("unknown type", elt_type)

        except Exception as e:
            print("draw exception:", e)
            continue

    return out


def is_used(name, elements):
    for elt in elements:
        elt_type = elt["type"]
        if elt_type == "methodInvocation":
            if ".".join(elt["to"]) == name:
                return True

        elif elt_type == "blocks":
            for block in elt["blocks"]:
                if is_used(name, block["contents"]):
                    return True

    return False


def render_sequence_diagram(seq_text):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto("https://sequencediagram.org/")

        page.click(".CodeMirror-line")
        page.evaluate(f"SEQ.main.getSourceValue = () => {json.dumps(seq_text)}")
        page.keyboard.press("a")
        time.sleep(0.3)
        svg = page.evaluate("SEQ.saveAndOpen.generateSvgData()")

        browser.close()

    elt = ET.fromstring(svg)
    replace_alt(elt)
    svg = ET.tostring(elt, encoding="utf-8")

    return svg


def replace_alt(elt):
    prev_alt = None
    for child in elt:
        if prev_alt is not None:
            if child.tag == "{http://www.w3.org/2000/svg}text":
                m = re.search(r"\[_([^_]*)_(.*)\]", child.text)
                child.text = f"[{m.group(2)}]"
                prev_alt.text = m.group(1)
            else:
                continue

        if child.tag == "{http://www.w3.org/2000/svg}text" and child.text == "alt":
            prev_alt = child
        else:
            prev_alt = None

        replace_alt(child)


def draw_svg(seq):
    seq_text = draw_sequence_diagram(seq)
    return render_sequence_diagram(seq_text)
