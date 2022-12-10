import json
from playwright.sync_api import sync_playwright
import time


# https://sequencediagram.org/


THIS_NAME = "this"


def draw_sequence_diagram(seq_data):
    out = ""

    out += "title Sequence Diagram\n"
    out += f'participant "**{THIS_NAME}**" as {THIS_NAME}\n'
    out += draw_elements(seq_data)

    return out


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
                append(f"{THIS_NAME}->{'.'.join(elt['to'])}:{elt['method']}")

            elif elt_type == "newInstance":
                pass  # TODO maybe need to get the variable "to"

            elif elt_type == "scopedVariable":
                if is_used(elt["name"], elements):
                    append(f"{THIS_NAME}->>*{elt['name']}://new//")

            elif elt_type == "return":
                append(
                    f"aboxleft over {THIS_NAME}:**return**"
                    + (f" {elt['value']}" if elt["value"] else "")
                )

            elif elt_type == "controlFlow":
                append(f"aboxleft over {THIS_NAME}:**{elt['name']}**")

            elif elt_type == "blocks":
                blocks = elt["blocks"]
                # TODO find solution for multiple blocks

                blocks = [
                    block
                    for block in blocks
                    if block["guard"] or draw_elements(block["contents"])
                ]

                if len(blocks) > 1:
                    append("group -")

                for block in blocks:
                    contents = draw_elements(block["contents"])

                    if block["guard"] or contents:
                        append(
                            f"group {block['name']} "
                            + (f" [{block['guard']}]" if block["guard"] else "")
                        )
                        append(draw_elements(block["contents"]))
                        append("end")

                if len(blocks) > 1:
                    append("end")

        except Exception:
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
        page.evaluate(f"SEQ.main.getSourceValue = () => `{seq_text}`")
        page.keyboard.press("a")
        time.sleep(0.3)
        svg = page.evaluate("SEQ.saveAndOpen.generateSvgData()")

        browser.close()

    return svg


def draw_svg(seq):
    seq_text = draw_sequence_diagram(seq)
    return render_sequence_diagram(seq_text)


def main():

    with open("test_xmi.xml", encoding="utf-8") as f:
        xmi = f.read()

    seq = generate_sequence(xmi)
    print(json.dumps(seq, indent=2))

    seq_text = draw_sequence_diagram(seq)
    print(seq_text)

    seq_svg = render_sequence_diagram(seq_text)

    with open("out/out.svg", "w", encoding="utf-8") as f:
        f.write(seq_svg)


if __name__ == "__main__":
    from process_java_model import *

    main()
