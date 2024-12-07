import os
import subprocess
from datetime import datetime
from graphviz import Digraph
import pytz
from lxml import etree


def load_config(config_file):
    tree = etree.parse(config_file)
    root = tree.getroot()
    repo_path = root.find("repo_path").text
    output_path = root.find("output_path").text
    start_date = root.find("commit_date").text
    return repo_path, output_path, start_date


config_file = "config.xml"
repo_path, output_path, start_date = load_config(config_file)

start_date = datetime.strptime(start_date, "%Y-%m-%d")
new_timezone = pytz.timezone('Europe/Moscow')
start_date = new_timezone.localize(start_date)

dot = Digraph(comment="Git Commit Dependency Graph")
dot.attr(compound='true')

commit_nodes = set()
file_nodes = set()
folder_nodes = set()

# Команда для выполнения git log
git_log_command = [
    "git", "-C", repo_path, "log", "--name-status", "--pretty=format:%H|%cd", "--date=iso"
]
result = subprocess.run(git_log_command, capture_output=True, text=True)
log_output = result.stdout.split("\n")

current_commit = None
for line in log_output:
    if "|" in line:
        commit_hash, commit_date_str = line.split("|")
        commit_date = datetime.fromisoformat(commit_date_str.strip())
        if commit_date < start_date:
            continue
        if commit_hash not in commit_nodes:
            dot.node(commit_hash, label=f"Commit {commit_hash[:7]}", shape="ellipse", color="blue")
            commit_nodes.add(commit_hash)
        current_commit = commit_hash

    elif line.startswith(("A", "M", "D")) and current_commit:
        status, file_path = line.split("\t", 1)
        folder = os.path.dirname(file_path)
        file = os.path.basename(file_path)
        if folder and folder not in folder_nodes:
            dot.node(folder, label=f"Folder: {folder}", shape="folder", color="grey")
            folder_nodes.add(folder)
        if file_path not in file_nodes:
            dot.node(file_path, label=f"File: {file}", shape="note", color="green")
            file_nodes.add(file_path)
        dot.edge(current_commit, folder)
        dot.edge(folder, file_path)

dot.render(output_path, format="png", cleanup=False)
print(f"Граф зависимостей сохранен как {output_path}.png")