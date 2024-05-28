import datetime
import json
import os
import sys
import random
import math
import shutil

def create_pack(root=None):
    if root is None:
        root = f"Randomized Textures {datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}"

    try:
        os.mkdir(root)
    except:
        print("error: failed to create root directory")

    with open(os.path.join(root, "pack.mcmeta"), "w") as f:
        json.dump({"pack": {"pack_format": 15, "description": ""}}, f, indent=4)

    os.mkdir(os.path.join(root, "assets"))
    os.mkdir(os.path.join(root, "assets", "minecraft"))
    os.mkdir(os.path.join(root, "assets", "minecraft", "textures"))

    return os.path.join(root, "assets", "minecraft", "textures")

def create_parents(path):
    parents = os.path.normpath(path).split(os.sep)[:-1]
    current = None
    for parent in parents:
        dp = None
        if current is None:
            dp = parent
        else:
            dp = os.path.join(current, parent)

        if not os.path.exists(dp):
            os.mkdir(dp)

        current = dp

def join_config_path(obj):
    if type(obj) is str:
        return obj
    elif type(obj) is list:
        return os.path.join(*obj)
    else:
        raise TypeError

def determine_compatibility_group(dp, groups):
    for i, group in enumerate(groups):
        if os.path.normpath(dp) in group:
            return i
    return None

def main():
    config = json.load(open("config.json"))

    seed = None
    if len(sys.argv) > 1:
        seed = int(sys.argv[1])
    else:
        seed = math.floor(datetime.datetime.now().timestamp() * 1000)

    random.seed(seed)
    print(f"random seed: {seed}")

    if not os.path.exists("pack"):
        print("error: source directory must exist")
        sys.exit(1)

    SRC_TEXTURES_PATH = os.path.join("pack", "assets", "minecraft", "textures")

    excluded_dirs = [os.path.normpath(os.path.join(".", join_config_path(dp))) for dp in config["excludedDirs"]]
    compatibility_groups = [[os.path.normpath(os.path.join(".", join_config_path(dp))) for dp in group] for group in config["compatibilityGroups"]]

    print("shuffling filepaths...", end="", flush=True)

    filepath_groups = [list() for _ in range(len(compatibility_groups))]

    original_cwd = os.getcwd()
    os.chdir(SRC_TEXTURES_PATH)

    for (root, dirnames, filenames) in os.walk("."):
        dirnames_to_remove = list()
        for dn in dirnames:
            dp = os.path.normpath(os.path.join(root, dn))
            if dp in excluded_dirs:
                dirnames_to_remove.append(dn)
        for dn in dirnames_to_remove:
            dirnames.remove(dn)

        filenames_to_remove = list()
        for fn in filenames:
            if os.path.splitext(fn)[1] != ".png":
                filenames_to_remove.append(fn)
        for fn in filenames_to_remove:
            filenames.remove(fn)

        filepaths = [os.path.join(root, fn) for fn in filenames]

        compatibility_group = determine_compatibility_group(os.path.normpath(root), compatibility_groups)
        if compatibility_group is not None:
            filepath_groups[compatibility_group].extend(filepaths)
        else:
            filepath_groups.append(filepaths)

    os.chdir(original_cwd)

    filepath_pairs = list()
    for filepaths in filepath_groups:
        filepaths_shuffled = filepaths.copy()
        random.shuffle(filepaths_shuffled)

        pairs = zip(filepaths, filepaths_shuffled)
        filepath_pairs.extend(pairs)

    print("\rshuffling filepaths... done")

    pack_name = f"Randomized Textures ({datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")})"

    print("creating resource pack...", end="", flush=True)
    DEST_TEXTURES_PATH = create_pack(pack_name)
    print("\rcreating resource pack... done")

    print("copying textures... 0%", end="", flush=True)
    num_pairs = len(filepath_pairs)
    for i, (src_fp, dest_fp) in enumerate(filepath_pairs):
        percent_complete = math.floor((i / num_pairs) * 100)
        print(f"\rcopying textures... {percent_complete}%", end="")

        src_fp = os.path.normpath(os.path.join(SRC_TEXTURES_PATH, src_fp))
        dest_fp = os.path.normpath(os.path.join(DEST_TEXTURES_PATH, dest_fp))

        create_parents(dest_fp)

        shutil.copyfile(src_fp, dest_fp)
    print("\rcopying textures... done")

    print("compressing...", end="", flush=True)
    shutil.make_archive(pack_name, "zip", pack_name)
    print("\rcompressing... done")

    print("cleaning up...", end="", flush=True)
    shutil.rmtree(pack_name)
    print("\rcleaning up... done")

if __name__ == "__main__":
    main()
