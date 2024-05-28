import datetime
import json
import os
import sys
import random
import math
import shutil

def create_pack(root=None):
    """
    Create a Minecraft texture pack with the specified root directory.

    Args:
        root (str): The root directory for the texture pack. If not provided, a default directory name will be generated.

    Returns:
        str: The path to the textures directory within the created texture pack.
    """

    # If root is not provided, generate a default directory name based on the current date and time
    if root is None:
        root = f"Randomized Textures {datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}"

    # Create the root directory
    try:
        os.mkdir(root)
    except:
        print("error: failed to create root directory")

    # Create the pack.mcmeta file with the pack format and description
    with open(os.path.join(root, "pack.mcmeta"), "w") as f:
        json.dump({"pack": {"pack_format": 15, "description": ""}}, f, indent=4)

    # Create the assets directory and the necessary subdirectories
    os.mkdir(os.path.join(root, "assets"))
    os.mkdir(os.path.join(root, "assets", "minecraft"))
    os.mkdir(os.path.join(root, "assets", "minecraft", "textures"))

    # Return the path to the textures directory
    return os.path.join(root, "assets", "minecraft", "textures")

def create_parents(path):
    """
    Create parent directories for the given path if they don't exist.

    Args:
        path (str): The path for which to create parent directories.

    Returns:
        None
    """

    # Split the path into parent directories
    parents = os.path.normpath(path).split(os.sep)[:-1]
    current = None
    
    # Iterate over the parent directories
    for parent in parents:
        dp = None
        if current is None:
            dp = parent
        else:
            dp = os.path.join(current, parent)

        # Create the parent directory if it doesn't exist
        if not os.path.exists(dp):
            os.mkdir(dp)

        current = dp

def join_config_path(obj):
    """
    Joins the elements of a given list using the `os.path.join` function,
    or returns the input string as is if it is not a list.

    Args:
        obj: A string or a list of strings representing the path elements.

    Returns:
        A string representing the joined path.

    Raises:
        TypeError: If the input is neither a string nor a list.
    """

    if type(obj) is str:
        return obj
    elif type(obj) is list:
        return os.path.join(*obj)
    else:
        raise TypeError

def determine_compatibility_group(dp, groups):
    """
    Determines the compatibility group of a given directory path.

    Args:
        dp (str): The directory path to determine the compatibility group for.
        groups (list): A list of groups, where each group is a list of directory paths.

    Returns:
        int or None: The index of the compatibility group if found, None otherwise.
    """

    for i, group in enumerate(groups):
        # Normalize the directory path for comparison with the group
        if os.path.normpath(dp) in group:
            return i

    return None

def main():
    """
    Randomizes Minecraft textures based on the provided configuration.

    This function reads the configuration from a JSON file, shuffles the filepaths of the textures,
    creates a resource pack with the shuffled textures, copies the textures to the resource pack,
    compresses the resource pack into a zip file, and cleans up the temporary files.

    The function takes no arguments and returns nothing. It is the entry point of the program.

    Example usage:
        main()
    """

    config = json.load(open("config.json"))

    # Use the seed provided as a command-line argument, or generate a seed
    seed = None
    if len(sys.argv) > 1:
        seed = int(sys.argv[1])
    else:
        seed = math.floor(datetime.datetime.now().timestamp() * 1000)

    random.seed(seed)
    print(f"random seed: {seed}")

    # Check if the source directory exists
    if not os.path.exists("pack"):
        print("error: source directory must exist")
        sys.exit(1)

    SRC_TEXTURES_PATH = os.path.join("pack", "assets", "minecraft", "textures")

    # Create a list of excluded directories based on the configuration
    excluded_dirs = [os.path.normpath(os.path.join(".", join_config_path(dp))) for dp in config["excludedDirs"]]
    # Create a list of compatibility groups, where each group is a list of directory paths based on the configuration
    compatibility_groups = [[os.path.normpath(os.path.join(".", join_config_path(dp))) for dp in group] for group in config["compatibilityGroups"]]

    print("shuffling filepaths...", end="", flush=True)

    filepath_groups = [list() for _ in range(len(compatibility_groups))]

    # Walk through the source directory and group the filepaths based on compatibility groups
    original_cwd = os.getcwd()
    os.chdir(SRC_TEXTURES_PATH)

    for (root, dirnames, filenames) in os.walk("."):
        # Remove excluded directories from the list of directories
        dirnames_to_remove = list()
        for dn in dirnames:
            dp = os.path.normpath(os.path.join(root, dn))
            if dp in excluded_dirs:
                dirnames_to_remove.append(dn)
        for dn in dirnames_to_remove:
            dirnames.remove(dn)

        # Remove non-PNG files from the list of filenames
        filenames_to_remove = list()
        for fn in filenames:
            if os.path.splitext(fn)[1] != ".png":
                filenames_to_remove.append(fn)
        for fn in filenames_to_remove:
            filenames.remove(fn)

        # Create a list of filepaths for the current directory
        filepaths = [os.path.join(root, fn) for fn in filenames]

        # Determine the compatibility group of the current directory
        compatibility_group = determine_compatibility_group(os.path.normpath(root), compatibility_groups)
        if compatibility_group is not None:
            filepath_groups[compatibility_group].extend(filepaths)
        else:
            filepath_groups.append(filepaths)

    os.chdir(original_cwd)

    # Shuffle the filepaths within each compatibility group
    filepath_pairs = list()
    for filepaths in filepath_groups:
        filepaths_shuffled = filepaths.copy()
        random.shuffle(filepaths_shuffled)

        pairs = zip(filepaths, filepaths_shuffled)
        filepath_pairs.extend(pairs)

    print("\rshuffling filepaths... done")

    # Create the resource pack and copy the textures
    pack_name = f"Randomized Textures ({datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")})"

    print("creating resource pack...", end="", flush=True)
    DEST_TEXTURES_PATH = create_pack(pack_name)
    print("\rcreating resource pack... done")

    print("copying textures... 0%", end="", flush=True)
    num_pairs = len(filepath_pairs)
    for i, (src_fp, dest_fp) in enumerate(filepath_pairs):
        # Calculate and display the completion percentage
        percent_complete = math.floor((i / num_pairs) * 100)
        print(f"\rcopying textures... {percent_complete}%", end="")

        # Copy the texture from the source directory to the destination directory
        src_fp = os.path.normpath(os.path.join(SRC_TEXTURES_PATH, src_fp))
        dest_fp = os.path.normpath(os.path.join(DEST_TEXTURES_PATH, dest_fp))

        create_parents(dest_fp)

        shutil.copyfile(src_fp, dest_fp)
    print("\rcopying textures... done")

    print("compressing...", end="", flush=True)
    # Compress the resource pack into a zip file
    shutil.make_archive(pack_name, "zip", pack_name)
    print("\rcompressing... done")

    print("cleaning up...", end="", flush=True)
    # Remove the resource pack directory
    shutil.rmtree(pack_name)
    print("\rcleaning up... done")


if __name__ == "__main__":
    main()
