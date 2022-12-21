from datasets import load_metric, load_from_disk


metric_bleu = load_metric("bleu")
print(metric_bleu.input_description)

dataset_test = load_from_disk("/data/nicolasmaier/dataset/hf_merged_test_1")
print("test:", dataset_test)
