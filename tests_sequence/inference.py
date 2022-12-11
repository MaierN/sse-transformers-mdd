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

for i in range(10):
    example_orig = dataset["test"][i * 1000]

    print(i)
    print(example_orig["originalLine"])
    # print(example_orig["code"])

    with open(f"out/real{i}.svg", "wb") as f:
        ground_truth = tokenizer.decode(example_orig["labels"][1:-1])
        f.write(draw_svg(json.loads(ground_truth)))

    model_input = tokenizer(example_orig["code"], return_tensors="pt").to(device)

    print("generating...")
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

    seq_text = None
    while seq_text is None:
        try:
            seq_text = json.loads(model_output)
        except json.decoder.JSONDecodeError as e:
            if e.msg == "Extra data":
                print("warning: extra data in", model_output)
                model_output = model_output[: e.pos]
            else:
                print("error:")
                print(model_output)
                raise e

    # print(seq_text)
    print("drawing...")
    svg = draw_svg(seq_text)

    with open(f"out/model{i}.svg", "wb") as f:
        f.write(svg)

    print("done")
