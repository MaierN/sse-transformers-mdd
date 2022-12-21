from datasets import load_from_disk
from transformers import (
    DataCollatorForSeq2Seq,
    RobertaTokenizer,
    T5ForConditionalGeneration,
)
import torch
from torch.utils.data import DataLoader, SequentialSampler
from tqdm import tqdm
import numpy as np

tokenizer = RobertaTokenizer.from_pretrained("Salesforce/codet5-small")
model = T5ForConditionalGeneration.from_pretrained("/data/nicolasmaier/model/ended-3")

# device = "cpu"
device = "cuda:0" if torch.cuda.is_available() else "cpu"
print(device)
model_gpu = model.to(device)

dataset_orig = load_from_disk("/data/nicolasmaier/dataset/hf_clean_seq_dataset_3")
dataset = dataset_orig.remove_columns(
    ["code", "contents", "xmi", "originalLine", "seq"]
)
print(dataset)


data_collator = DataCollatorForSeq2Seq(tokenizer)
eval_sampler = SequentialSampler(dataset["test"])
eval_dataloader = DataLoader(
    dataset["test"],
    sampler=eval_sampler,
    batch_size=8,
    num_workers=4,
    pin_memory=True,
    collate_fn=data_collator,
)

gen = []
gen_dec = []

model_gpu.eval()
for batch in tqdm(eval_dataloader, total=len(eval_dataloader)):
    source_ids = batch["input_ids"].to(device)
    # source_mask = batch["attention_mask"].to(device)
    with torch.no_grad():
        outputs = model_gpu.generate(
            source_ids,
            # attention_mask=source_mask,
            num_beams=5,
            max_length=510,
            # do_sample=True,
            temperature=0.3,
            top_k=50,
            top_p=0.8,
        )
        generated = [list(np.trim_zeros(x)) for x in list(outputs.cpu().numpy())]
        gen.extend(generated)
        gen_dec.extend(
            [
                tokenizer.decode(
                    x,
                    skip_special_tokens=True,
                    clean_up_tokenization_spaces=False,
                )
                for x in generated
            ]
        )

print("done generating")

while len(gen) < len(dataset_orig["test"]):
    gen.append([])
    gen_dec.append("")

dataset_eval = dataset_orig["test"].add_column("generated", gen)
dataset_eval = dataset_eval.add_column("generated_decoded", gen_dec)

print("saving")
dataset_eval.save_to_disk("/data/nicolasmaier/dataset/hf_clean_seq_dataset_3_eval")
