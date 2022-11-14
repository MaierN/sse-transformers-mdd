import gzip
import os

IN_DIR = 'codesearchnet-java'
OUT_DIR = 'codesearchnet-java-decompressed'

if __name__ == '__main__':
    for directory in os.listdir(IN_DIR):
        if not os.path.isdir(IN_DIR + '/' + directory):
            continue
        print(f'directory {directory}')

        os.makedirs(OUT_DIR, exist_ok=True)

        for file in os.listdir(IN_DIR + '/' + directory):
            if not file.endswith('.gz'):
                continue
            print(f'  file {file}')

            with gzip.open(IN_DIR + '/' + directory + '/' + file, 'rb') as f_in:
                with open(OUT_DIR + '/' + file[:-3], 'wb') as f_out:
                    f_out.write(f_in.read())
