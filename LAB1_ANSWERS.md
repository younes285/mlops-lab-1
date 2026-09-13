Lab 1 - Git/DVC and Data Preparation

Question 1

Observe the files created by uv init. What do you think they contain?

Running uv init creates the basic structure of a Python project.

The main files are:

pyproject.toml: contains information about the Python project, such as the project name, Python version, and dependencies.

README.md: contains documentation and information about the project.

src/: contains the Python source code of the project.

uv.lock: created when dependencies are installed. It stores the exact versions of dependencies to make the environment reproducible.

For example, after installing Pillow using:

uv add pillow

Pillow was added as a dependency of the project.

Question 2

What files are created by dvc init? What are they used for? Which ones should be pushed to Git?

Running:

dvc init

creates the .dvc directory and .dvcignore.

The important files/directories are:

.dvc/config: contains the DVC project configuration, such as the configured remote storage.

.dvcignore: works similarly to .gitignore and tells DVC which files or folders it should ignore.

.dvc/cache: stores local copies of data managed by DVC.

.dvc/tmp: contains temporary DVC files.

Configuration files such as .dvc/config and .dvcignore should be tracked by Git.

The DVC cache and temporary files should not be pushed to Git because they may contain large data files and are managed automatically by DVC.

Question 3

Where are the credentials stored? What are the options other than --global? Should the credentials be pushed to GitHub?

When using:

dvc remote modify origin --global ...

the credentials are stored in the user's global DVC configuration, outside the Git repository.

This allows the credentials to be used locally without adding them to the project repository.

Other configuration levels include:

Repository configuration: stored in .dvc/config

Local configuration using --local: stored in .dvc/config.local

System-level configuration is also possible

Sensitive information such as usernames, passwords, or access tokens should not be pushed to GitHub.

For authentication with DagsHub, an access token can be used as the password.

Question 4

Take a look at the .gitignore file. Explain what happened.

After running:

dvc add data

DVC automatically added the data directory to .gitignore.

This prevents Git from tracking and uploading the actual dataset.

The data is instead managed by DVC, while Git only tracks the small DVC pointer file.

Therefore:

Git tracks the code and data.dvc

DVC tracks the actual dataset

Question 5

Do you see a .dvc file? What does it contain?

Yes. After running:

dvc add data

a file named:

data.dvc

was created.

This file does not contain the actual images.

It contains metadata describing the dataset, such as:

A hash/checksum identifying the version of the data

The path of the tracked directory

Information about the number and size of files

An example structure is similar to:

outs:
- md5: <hash>.dir
  size: <size>
  nfiles: <number>
  path: data

The hash allows DVC to identify exactly which version of the dataset should be used.

The data.dvc file is small and should be committed to Git.

Question 6

Is the code on GitHub? Is the data there? Is there a file pointing to the data? What about DagsHub?

The code and DVC metadata are stored on GitHub.

For example, GitHub contains:

Python source code

pyproject.toml

.dvc/config

.gitignore

data.dvc

The actual Food-11 images are not stored directly in GitHub.

The file:

data.dvc

acts as the pointer describing the version of the dataset.

The actual dataset is stored in the DVC remote on DagsHub after running:

dvc push

Therefore the project is separated as follows:

GitHub
    Code + DVC pointer files

DagsHub
    Actual dataset

After the final dvc push, DVC reported:

Everything is up to date.

which confirms that the local DVC data and DagsHub remote are synchronized.

Question 7

In a completely new temporary folder, clone the GitHub repository. Do you see the data folder? What DVC command is needed to get it?

After cloning the GitHub repository into a new directory using:

git clone https://github.com/younes285/mlops-lab-1.git

the actual data directory was not initially available.

Only the Git-tracked files were downloaded, including:

data.dvc

To retrieve the actual dataset from DagsHub, the required command is:

dvc pull

dvc pull reads the information stored in data.dvc and downloads the corresponding data from the configured DVC remote.

Therefore:

git clone
    ↓
Downloads code and DVC pointers

dvc pull
    ↓
Downloads the actual dataset

Question 8

After checking out the old commit and running dvc checkout, do you still see food11_processed and food11_processed_mini?

First, the commits affecting data.dvc were displayed using:

git log --oneline -- data.dvc

The result was:

0299f5c Add food11_processed and food11_processed_mini
6f0232b Tack data folder with dvc

The older version was then checked out:

git checkout 6f0232b

followed by:

dvc checkout

After the DVC checkout, the following folders were no longer present:

food11_processed
food11_processed_mini

Only the original raw dataset remained.

This demonstrates that DVC can restore the version of the dataset associated with a specific Git commit.

When returning to the latest Git version and running dvc checkout again, the latest data version can be restored.

This shows how Git and DVC work together:

Git versions the code and DVC pointer files.

DVC versions the actual datasets.

Checking out a Git commit and then running dvc checkout restores the matching version of the data.