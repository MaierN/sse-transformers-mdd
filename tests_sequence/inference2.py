from datasets import load_from_disk
from process_java_model import *
from draw_svg import *

dataset = load_from_disk("/data/nicolasmaier/dataset/hf_clean_seq_dataset_2")

idx = 22008
example = dataset["test"][idx]

print(example["code"])

xmi = example["xmi"]
with open("test_xmi.xml", "r") as f:
    xmi = f.read()

seq = generate_sequence(xmi)

svg = draw_svg(seq)

with open("out/out.svg", "wb") as f:
    f.write(svg)
