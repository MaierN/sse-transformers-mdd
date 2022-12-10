from datasets import load_from_disk
from transformers import (
    DataCollatorForSeq2Seq,
    RobertaTokenizer,
    Seq2SeqTrainer,
    Seq2SeqTrainingArguments,
    T5ForConditionalGeneration,
)
import torch

SEED = 42

print(torch.cuda.is_available())

tokenizer = RobertaTokenizer.from_pretrained("Salesforce/codet5-small")
model = T5ForConditionalGeneration.from_pretrained("Salesforce/codet5-small")

dataset = load_from_disk("/data/nicolasmaier/dataset/hf_clean_seq_dataset_2")
dataset = dataset.remove_columns(["code", "contents", "xmi", "originalLine", "seq"])
print(dataset)

BATCH_SIZE = 10

args = Seq2SeqTrainingArguments(
    output_dir="/data/nicolasmaier/model/codet5-finetuned-seq-4",
    evaluation_strategy="steps",
    eval_steps=1000,
    logging_strategy="steps",
    logging_steps=1000,
    save_strategy="steps",
    save_steps=1000,
    learning_rate=5e-5,
    weight_decay=0.0,
    per_device_train_batch_size=BATCH_SIZE,
    per_device_eval_batch_size=BATCH_SIZE,
    #gradient_accumulation_steps=2,
    warmup_steps=1000,
    save_total_limit=1000,
    num_train_epochs=5, # 100?
    predict_with_generate=True,
    # load_best_model_at_end=True,
    # metric_for_best_model="EM", # or BLEU?
    seed=SEED,
    report_to="tensorboard",
    fp16=True,  # train faster
)

data_collator = DataCollatorForSeq2Seq(tokenizer)

trainer = Seq2SeqTrainer(
    model,
    args,
    train_dataset=dataset["train"].shuffle(seed=SEED).select(range(300_000)),
    eval_dataset=dataset["valid"].shuffle(seed=SEED).select(range(1000)),
    data_collator=data_collator,
    tokenizer=tokenizer,
)

print("starting training")
trainer.train()
