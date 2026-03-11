import os
import subprocess
from rst_prep.main import run as rst_prep_run
from rst_prep.global_knobs import GlobalKnobs
import rst_prep.consts as consts
import re


ALL_RST = 'all.rst'


def collect_all_rsts(path, excluded_files=(ALL_RST,)):
    l = {}
    for directory, folders, files in os.walk(path):
        for _file in files:
            if _file in excluded_files:
                continue
            elif _file.endswith('.rst'):
                l.setdefault(directory, [])
                l[directory].append(_file)

    l = {k: sorted(l[k]) for k in l.keys()}

    return l


def concatenate_all(files, dest=None, sep='\n'):
    if dest is None:
        dest = os.path.abspath(os.path.join(GlobalKnobs.get_out_dir(), ALL_RST))
    sorted_keys = sorted(files.keys(), key=lambda x: re.sub(r'[\- ]', '', x.lower()))
    with open(dest, 'w', encoding="utf-8") as merged_f:
        for key in sorted_keys:
            merged_f.write(make_title(os.path.split(key)[-1]))
            merged_f.write(sep * 2)
            for _file in files[key]:
                with open(os.path.join(key, _file), encoding="utf-8") as f:
                    merged_f.write(f.read() + '\n')
                merged_f.write(sep)


def make_title(title):
    return title + '\n' + len(title) * '='


def generate_docx() -> None:
    dest_file = os.path.abspath(os.path.join(GlobalKnobs.get_out_dir(), ALL_RST))
    p = os.path.abspath(GlobalKnobs.get_out_dir())
    _files = collect_all_rsts(p)
    concatenate_all(_files, dest_file)

    cmd = f'pandoc -f rst {dest_file} -o {dest_file.replace(".rst", ".docx")} -s'
    a = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
    print(a.decode())


if __name__ == '__main__':
    print("Preparing env...")
    if rst_prep_run() != consts.SUCCESS:
        exit(1)
    print("Generating docx...")
    generate_docx()
