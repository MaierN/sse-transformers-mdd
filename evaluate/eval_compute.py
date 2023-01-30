from datasets import load_from_disk, load_metric
from transformers import (
    DataCollatorForSeq2Seq,
    RobertaTokenizer,
    T5ForConditionalGeneration,
)
import torch
from torch.utils.data import DataLoader, SequentialSampler
from tqdm import tqdm
import evaluate
from CodeBLEU.calc_code_bleu import compute_code_bleu
from dotenv import dotenv_values

OUTPUT_PATH = dotenv_values("../.env")["OUTPUT_PATH"]

dataset = load_from_disk(f"{OUTPUT_PATH}/dataset/seq_dataset_filtered_eval")
print(dataset)

metric_exactmatch = evaluate.load("exact_match")

res = metric_exactmatch.compute(
    predictions=dataset["generated_decoded"], references=dataset["seq"]
)
print("Exact match score:", res["exact_match"])

res = compute_code_bleu(
    ref=dataset["seq"],
    hyp=dataset["generated_decoded"],
    lang="json",
    params=[1 / 3, 1 / 3, 1 / 3, 0],  # no dataflow information
)
print("CodeBLEU score:", res["code_bleu_score"])
