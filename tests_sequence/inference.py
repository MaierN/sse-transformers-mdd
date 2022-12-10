from datasets import load_from_disk
from transformers import (
    RobertaTokenizer,
    T5ForConditionalGeneration,
)
import torch
import random
import json
from draw_svg import *

torch.set_num_threads(16)

tokenizer = RobertaTokenizer.from_pretrained("Salesforce/codet5-small")
model = T5ForConditionalGeneration.from_pretrained(
    "/data/nicolasmaier/model/codet5-finetuned-seq-4/checkpoint-27000"
)

device = "cpu"  # 'cuda:0' if torch.cuda.is_available() else 'cpu'
print(device)
model_gpu = model.to(device)

dataset = load_from_disk("/data/nicolasmaier/dataset/hf_clean_seq_dataset_2")
print(dataset)

for i in range(10):
    example_orig = dataset["test"][i * 1000]

    print(example_orig["originalLine"])
    print(example_orig["contents"])

    model_input = tokenizer(example_orig["contents"], return_tensors="pt").to(device)

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
        except json.decoder.JSONDecodeError:
            model_output = model_output[:-1]

    print(seq_text)
    print("drawing...")
    svg = draw_svg(seq_text)

    with open(f"out/example{i}.svg", "w", encoding="utf-8") as f:
        f.write(svg)

    print("done")
