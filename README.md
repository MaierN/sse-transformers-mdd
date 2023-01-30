
# MBE using an AI Language Model

Seminar Software Engineering, University of Bern & University of Fribourg, Fall 2022

*Project by:* Nicolas Maier\
*Supervised by:* Sandra Greiner\
*Course professor:* Timo Kehrer

# Steps to reproduce

## 1. Preparing the environment

*Note: Python 3.8.10 was used*

### Install python dependencies

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Configure output directory

Edit the `.env` file, and set the `OUTPUT_PATH` variable to an arbitrary path where the dataset and model will be stored

### Other config

You can also change the default cache directory for the HF datasets library (it will become huge):

```bash
export HF_DATASETS_CACHE="/<path-to-cache-directory>"
```

## 2. Getting the CodeSearchNet dataset

### Download and unzip

```bash
wget -O dataset/java.zip https://s3.amazonaws.com/code-search-net/CodeSearchNet/v2/java.zip

unzip -d dataset dataset/java.zip
```

*The collection of Java methods from CodeSearchNet is downloaded; the raw compressed data is available in `dataset/java/final/jsonl/<split>/java_<split>_<part>.jsonl.gz`*

### Extract the jsonl data

```bash
cd dataset
python decompress.py
cd ..
```

*The dataset is decompressed, and the resulting jsonl files are available in `dataset/codesearchnet-java-decompressed/java_<split>_<part>.jsonl`*

## 3. Discovery of Java methods using MoDisco

**This step was performed on a local computer in order to use Eclipse's GUI; resulting files were then transferred on the server**

*Note: Eclipse Modeling Tools 2022-09 was used*

### Prepare Eclipse

*2 Eclipse Workspaces are provided:*

Target workspace
- Open the `eclipse_workspaces/workspace_target` workspace in Eclipse
- Use `File > Open Projects from File System...` to open the `TargetProject` project
- Close this instance of Eclipse

Plugin workspace
- In `Help > Install New Software...` install the `MoDisco SDK` plugin
- Use `File > Open Projects from File System...` to open the `DiscoverDataset` project

### Run the application

Use the provided launch configuration (`discover_dataset`) to perform the discovery

*The resulting XMI is available in `dataset/codesearchnet-java-discovered/java_<split>_<part>.jsonl`*

## 4.Preparing the dataset

```bash
cd prepare_dataset
python prepare_dataset.py
cd ..
```

*The HF dataset is now available in the `<OUTPUT_PATH>/dataset/seq_dataset_filtered` directory*

## 5. Training the model

```bash
cd train_model
python finetune_codet5.py
cd ..
```

*The model is now available in the `<OUTPUT_PATH>/model` directory*

## 6. Evaluating the model

```bash
cd evaluate
python eval_generate.py
python eval_compute.py
cd ..
```

**Results:**\
Exact match score: 0.9825...\
CodeBLEU score: 0.9988...

## 7. Visualizing results

### Input code

You can edit the `visualization/test_code.txt` file to change the code that will be sent to the model

**Example code:**

```java
public void test(int x, String y) {
        A a = new A();
        
        a.foo1();
        a.foo2(42);
        
        while (a.foo3()) {
            B b = new B();
            
            b.bar1();
            
            if (b.bar2() && xyz) {
                b.bar3(42);
            } else {
                b.bar4();
            }
        }
    }
```

### Run the script

```bash
cd visualization
python generate_seq_diagram.py
cd ..
```

### See the result

Open the generated sequence diagram (`visualization/test_output.svg` file)

**Example output diagram:**

![Generated sequence diagram](./visualization/test_output.svg)
