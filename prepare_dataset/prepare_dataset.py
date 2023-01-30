import json
from datasets import load_from_disk, load_dataset
from transformers import RobertaTokenizer
from process_java_model import *
import os
from dotenv import dotenv_values

OUTPUT_PATH = dotenv_values("../.env")["OUTPUT_PATH"]
DATASET_PATH = "../dataset/codesearchnet-java-discovered/"

tokenizer = RobertaTokenizer.from_pretrained("Salesforce/codet5-small")

data_files = {"train": [], "valid": [], "test": []}

for file in os.listdir(DATASET_PATH):
    file_path = os.path.join(DATASET_PATH, file)
    if "train" in file:
        data_files["train"].append(file_path)
    elif "valid" in file:
        data_files["valid"].append(file_path)
    elif "test" in file:
        data_files["test"].append(file_path)

print(data_files)

dataset = load_dataset("json", data_files=data_files)
print(dataset)


def preprocess_examples(examples):
    contents = examples["code"]
    model_inputs = tokenizer(contents)
    return model_inputs


dataset_with_input = dataset.map(
    preprocess_examples,
    batched=True,
    batch_size=100,
    num_proc=64,
)


def preprocess_examples(examples):
    xmi = examples["xmi"]

    seqs = [generate_sequence(xmi_string) for xmi_string in xmi]
    seqs = [json.dumps(seq) for seq in seqs]

    labels = tokenizer(seqs).input_ids

    return {"seq": seqs, "labels": labels}


dataset_with_output = dataset_with_input.map(
    preprocess_examples,
    batched=True,
    batch_size=10,
    num_proc=64,
)

print(dataset_with_output)
dataset_with_output.save_to_disk(f"{OUTPUT_PATH}/dataset/seq_dataset")

MAX_LENGTH = 505

dataset_filtered = dataset_with_output.filter(
    lambda example: len(example["input_ids"]) <= MAX_LENGTH, num_proc=64
)
print(dataset_filtered)
dataset_filtered = dataset_filtered.filter(
    lambda example: len(example["labels"]) <= MAX_LENGTH,
    num_proc=64,
)
print(dataset_filtered)
dataset_filtered = dataset_filtered.filter(
    lambda example: len(example["seq"]) > 10,
    num_proc=64,
)
print(dataset_filtered)

print(dataset_filtered)
dataset_filtered.save_to_disk(f"{OUTPUT_PATH}/dataset/seq_dataset_filtered")
