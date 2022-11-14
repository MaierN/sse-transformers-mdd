from transformers import RobertaTokenizer, T5ForConditionalGeneration
from datasets import load_dataset
import os

tokenizer = RobertaTokenizer.from_pretrained("Salesforce/codet5-small")
model = T5ForConditionalGeneration.from_pretrained("Salesforce/codet5-small")

if __name__ == "__main__":

    DATASET_PATH = "../dataset/codesearchnet-java-discovered/"

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

    MAX_INPUT_LENGTH = 512

    def preprocess_examples(examples):
        contents = examples["contents"]
        xmi = examples["xmi"]

        model_inputs = tokenizer(contents, padding="max_length")

        """ labels = tokenizer(xmi, padding="longest").input_ids
        # -100 is a special value that the loss function will ignore
        labels = [
            [-100 if token == tokenizer.pad_token_id else token for token in label]
            for label in labels
        ] """
        labels = tokenizer(xmi).input_ids

        model_inputs["labels"] = labels

        return model_inputs

    tokenized_dataset = dataset.map(preprocess_examples, batched=True, batch_size=100, num_proc=8)

    print(tokenized_dataset)
