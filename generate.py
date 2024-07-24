import json
import os
import zipfile
import git
import stat
from git import Git
import shutil
from pathlib import Path

def readonly_to_writable(foo, file, err):
  if Path(file).suffix in ['.idx', '.pack'] and 'PermissionError' == err[0].__name__:
    os.chmod(file, stat.S_IWRITE)
    foo(file)

config_path = "./example_config.json"

f = open(config_path)
data = json.load(f)

if data:
    repo_url = data["git_repo_url"]
    repo_dir = data["destination_dir"]
    versions = data["versions"]
    git_ssh_identity_file = data["ssh_path"]
    git_ssh_cmd = 'ssh -i %s' % git_ssh_identity_file
    with Git().custom_environment(GIT_SSH_COMMAND=git_ssh_cmd):
        print("Cloning {git_clone_url}".format(git_clone_url=repo_url))
        repo = git.Repo.clone_from(repo_url, repo_dir  + data["name"], env={"GIT_SSH_COMMAND": 'ssh -i ' + data["ssh_path"]})
        for i in versions:
            branch = i["branch"]
            version = i["version"]

            #Checkout new branch
            repo.git.checkout(branch)
            print("Checking out {branch_name}".format(branch_name=branch))

            #Create new directory
            new_directory = repo_dir + "\\" + version + "\\"

            if os.path.exists(new_directory):
                print("Deleting. {new_dir}".format(new_dir=new_directory))
                shutil.rmtree(new_directory, onerror=readonly_to_writable)

            os.mkdir(new_directory)
            new_directory += data["name"]

            #zip up folder
            folder_path = os.path.abspath(os.path.join(repo_dir, data["name"]))  # Get absolute path of the folder to zip
            folder_dir = os.path.dirname(folder_path)
            folder_name = os.path.basename(folder_path)

            # Create a ZipFile object
            with zipfile.ZipFile(new_directory + ".zip", "w", zipfile.ZIP_DEFLATED) as zf:
                if data["log_file_names"]:
                    print(folder_dir)
                for root, subdirs, files in os.walk(folder_path):
                    # Exclude specified directories
                    subdirs[:] = [d for d in subdirs if d not in data["excluded_directories"]]
                    # Write the directory (empty folders)
                    for dirname in subdirs:
                        dirpath = os.path.join(root, dirname)
                        arcname = os.path.relpath(dirpath, folder_dir)
                        zf.write(dirpath, arcname)
                        if data["log_file_names"]:
                            print(dirpath)
                    # Write the files
                    for filename in files:
                        if filename not in data["excluded_files"]:
                            full_path = os.path.join(root, filename)
                            arcname = os.path.relpath(full_path, folder_dir)
                            zf.write(full_path, arcname)
                            if data["log_file_names"]:
                                print(full_path)

            print("Created {zipname}".format(zipname=data["name"] + ".zip"))
        
        print("Deleting {repo_dir_name}".format(repo_dir_name=repo_dir  + data["name"]))
        shutil.rmtree(repo_dir  + data["name"], onerror=readonly_to_writable)

    print("Finished Packaging")
