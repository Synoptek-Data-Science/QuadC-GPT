import os

def generate_tree(start_path, prefix=""):
    tree_lines = []
    files = sorted(os.listdir(start_path))
    for idx, file in enumerate(files):
        if file == ".git":  # skip .git
            continue
        path = os.path.join(start_path, file)
        connector = "└── " if idx == len(files) - 1 else "├── "
        tree_lines.append(f"{prefix}{connector}{file}")
        if os.path.isdir(path):
            extension = "    " if idx == len(files) - 1 else "│   "
            tree_lines.extend(generate_tree(path, prefix + extension))
    return tree_lines

repo_path = "D:/OneDrive - Synoptek, Inc/Technical/Upgraded_open_weUI/openwebui_updated/static"  # current folder
tree_output = ["static/"]
tree_output.extend(generate_tree(repo_path))

with open("project_tree.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(tree_output))

print("Project structure saved in project_tree.txt")
