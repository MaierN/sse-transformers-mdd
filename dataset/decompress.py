import gzip
import os

IN_DIR = 'java/final/jsonl'
OUT_DIR = 'codesearchnet-java-decompressed'
DISCO_DIR = 'codesearchnet-java-discovered'

if __name__ == '__main__':
    os.makedirs(OUT_DIR, exist_ok=True)
    os.makedirs(DISCO_DIR, exist_ok=True)

    for directory in os.listdir(IN_DIR):
        if not os.path.isdir(IN_DIR + '/' + directory):
            continue
        print(f'directory {directory}')

        for file in os.listdir(IN_DIR + '/' + directory):
            if not file.endswith('.gz'):
                continue
            print(f'  file {file}')

            with gzip.open(IN_DIR + '/' + directory + '/' + file, 'rb') as f_in:
                with open(OUT_DIR + '/' + file[:-3], 'wb') as f_out:
                    f_out.write(f_in.read())
