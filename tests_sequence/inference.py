import json
from datasets import load_from_disk
from transformers import (
    RobertaTokenizer,
    T5ForConditionalGeneration,
)
import torch
from draw_svg import *

torch.set_num_threads(16)

tokenizer = RobertaTokenizer.from_pretrained("Salesforce/codet5-small")
model = T5ForConditionalGeneration.from_pretrained("/data/nicolasmaier/model/ended-3")

# device = "cpu"
device = "cuda:0" if torch.cuda.is_available() else "cpu"
print(device)
model_gpu = model.to(device)

dataset = load_from_disk("/data/nicolasmaier/dataset/hf_clean_seq_dataset_3")
print(dataset)


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
    with open("test_code.txt", "r", encoding="utf-8") as f:
        code = f.read()
        seq_text = model_generate(code)
        print(seq_text)
        svg = draw_svg(seq_text)
        with open("out/model.svg", "wb") as f:
            f.write(svg)

    for i in range(10):
        example_orig = dataset["test"][i * 1000]

        print(i)
        print(example_orig["originalLine"])
        # print(example_orig["code"])

        with open(f"out/code{i}.txt", "w", encoding="utf-8") as f:
            f.write(example_orig["code"])

        with open(f"out/real{i}.svg", "wb") as f:
            ground_truth = tokenizer.decode(example_orig["labels"][1:-1])
            f.write(draw_svg(json.loads(ground_truth)))

        seq_text = model_generate(example_orig["code"])

        # print(seq_text)
        print("drawing...")
        svg = draw_svg(seq_text)

        with open(f"out/model{i}.svg", "wb") as f:
            f.write(svg)

        print("done")


if __name__ == "__main__":
    main()
