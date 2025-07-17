import os

def get_password_tree(base_path, current_path=""):
    tree = {}
    full_path = os.path.join(base_path, current_path)

    if not full_path.startswith(base_path) or not os.path.isdir(full_path):
        return {}

    for item in sorted(os.listdir(full_path)):
        if item.startswith('.') or item.lower() == "readme.md":
            continue
        path = os.path.join(full_path, item)
        rel_path = os.path.join(current_path, item)
        if os.path.isdir(path):
            tree[item] = get_password_tree(base_path, rel_path)
        elif item.endswith(".gpg"):
            tree[item[:-4]] = rel_path[:-4]

    return tree

def sanitize_filepath_input(path_str):
    path = os.path.normpath(path_str).lstrip('/\\').rstrip('/\\')
    return path
