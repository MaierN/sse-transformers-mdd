import json
from transformers import (
    RobertaTokenizer,
    T5ForConditionalGeneration,
)
import torch
from draw_svg import *
from dotenv import dotenv_values

OUTPUT_PATH = dotenv_values("../.env")["OUTPUT_PATH"]

torch.set_num_threads(16)

tokenizer = RobertaTokenizer.from_pretrained("Salesforce/codet5-small")
model = T5ForConditionalGeneration.from_pretrained(
    f"{OUTPUT_PATH}/model/seq_codet5_finetuned"
)

# device = "cpu"
device = "cuda:0" if torch.cuda.is_available() else "cpu"
print(device)
model_gpu = model.to(device)


def fix_json(s):
    stack = []
    skip_next = False
    for i, c in enumerate(s):
        if skip_next:
            skip_next = False
            continue

        if c == "\\":
            skip_next = True
        elif c == "[":
            stack.append("[")
        elif c == "]":
            if stack[-1] != "[":
                print("warning: ] without [")
                s = s[:i] + " " + s[i + 1 :]
            else:
                stack.pop()
        elif c == "{":
            stack.append("{")
        elif c == "}":
            if stack[-1] != "{":
                print("warning: } without {")
                s = s[:i] + " " + s[i + 1 :]
            else:
                stack.pop()

    for c in stack[::-1]:
        if c == "[":
            print("warning: [ without ]")
            s += "]"
        elif c == "{":
            print("warning: { without }")
            s += "}"

    return s


def model_generate(code):
    model_input = tokenizer(code, return_tensors="pt").to(device)

    outputs = model_gpu.generate(
        model_input.input_ids,
        num_beams=10,
        max_length=510,
        # do_sample=True,
        temperature=0.3,
        top_k=50,
        top_p=0.8,
    )
    model_output = tokenizer.decode(outputs[0][2:-1])

    print("input:", code)
    print("output:", model_output)

    seq_text = None
    while seq_text is None:
        try:
            seq_text = json.loads(fix_json(model_output))
        except json.decoder.JSONDecodeError as e:
            if e.msg == "Extra data":
                print("warning: extra data in", model_output)
                model_output = model_output[: e.pos]
            else:
                print("error:")
                print(model_output)
                raise e

    return seq_text


def main():
    with open("test_input.txt", "r", encoding="utf-8") as f:
        code = f.read()
        seq_text = model_generate(code)
        print(seq_text)
        svg = draw_svg(seq_text)
        with open("test_output.svg", "wb") as f:
            f.write(svg)

        print("saved .svg to test_output.svg")


if __name__ == "__main__":
    main()
