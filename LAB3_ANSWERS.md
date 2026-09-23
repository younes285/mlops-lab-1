
Today 4:53 PM

Pasted text.txt
Document
C:\Users\mosta\OneDrive\Desktop\MLOPS> docker images food11-api
REPOSITORY   TAG       IMAGE ID       CREATED       SIZE
food11-api   latest    32192043cbe4   4 hours ago   9.64GB
PS C:\Users\mosta\OneDrive\Desktop\MLOPS> 

what next 


Pasted text(1).txt
Document

Yes—run:

git push origin main
If it finishes with something like:

main -> main
then Lab 3 code is pushed successfully.

Send me the output, and next we'll do the Q1–Q9 answers using the exact results we obtained, including the Docker/MLflow issues we actually encountered.


(mlops) PS C:\Users\mosta\OneDrive\Desktop\MLOPS> git push origin main

Enumerating objects: 13, done.

Counting objects: 100% (13/13), done.

Delta compression using up to 16 threads

Compressing objects: 100% (9/9), done.

Writing objects: 100% (9/9), 182.71 KiB | 3.58 MiB/s, done.

Total 9 (delta 2), reused 0 (delta 0), pack-reused 0

remote: Resolving deltas: 100% (2/2), completed with 2 local objects.

To younes285/mlops-lab-1.git

8adfc42..79a74a6  main -> main

(mlops) PS C:\Users\mosta\OneDrive\Desktop\MLOPS> ^C

(mlops) PS C:\Users\mosta\OneDrive\Desktop\MLOPS> ^C

(mlops) PS C:\Users\mosta\OneDrive\Desktop\MLOPS>

Perfect — the push succeeded. ✅

Your Lab 3 commit is now on GitHub:

79a74a6
and main moved from:

8adfc42 → 79a74a6
So the code part of Lab 3 is submitted to the repository.

Next, we should write the Q1–Q9 answers based strictly on what we actually did and observed, especially:

registered model version 1

alias champion

Dockerized FastAPI serving

host.docker.internal

Windows MLflow artifact-path issue and bind mount

successful /health and /predict

fresh-container restart test

Docker layer/cache observations

If you want, send me Q1 and we’ll answer them one by one, short and submission-ready.


# Lab 3 - Containerizing the model with Docker

This lab continues the project from Lab 1 (git+dvc data) and Lab 2 (training + mlflow tracking). You now have a trained model and a run ID for your best experiment. In this lab you will register that model in the mlflow Model Registry, write a small serving API around it, and package everything into a Docker image so it can run anywhere without a local Python setup.

> What you need to know:
> - a Docker **image** is a built, immutable set of layers (filesystem + metadata); a **container** is a running instance of an image
> - a Dockerfile describes how to build an image, one instruction (layer) at a time; Docker caches layers, so ordering instructions from least-to-most-frequently-changed speeds up rebuilds
> - a **multi-stage build** uses one stage to install/build dependencies and a second, smaller stage to run the app, so build tools don't bloat the final image
> - the mlflow **Model Registry** lets you name and version a model (e.g. food11) independently of the run that produced it; instead of the old (deprecated) stages like Staging/Production, current mlflow uses **aliases** — mutable pointers like champion that you can reassign to any version — plus free-form **tags** for anything else you want to track
> - a container is isolated from the host network by default; reaching a service running on your host machine (like the mlflow tracking server from Lab 2) requires extra configuration

## Before You Start: What You Need Installed

- **Docker** — Docker Desktop (Mac/Windows) or Docker Engine (Linux). Confirm with docker --version and docker run hello-word.
- Your Lab 2 project, with at least one completed training run and its run ID noted.

## Register your best model

### Promote a run to the Model Registry

Using the run ID you noted at the end of Lab 2 (the run with the best val_accuracy), register its model artifact under a shared name. You can do this either from the mlflow UI or from code — pick whichever you prefer:

**Option A — from the UI:**

1. Open the food11 experiment, sort the runs table by val_accuracy descending, and open your best run.
2. In the run page, open the "Artifacts" tab, select the model folder, and click "Register Model".
3. Choose "Create New Model", name it food11, and confirm.

**Option B — from code:**

bash
uv run python -c "
import mlflow
mlflow.set_tracking_uri('http://127.0.0.1:5000')
mlflow.register_model('runs:/<your-run-id>/model', 'food11')
"


> Question 1: Open the "Models" tab in the mlflow UI. What version number was your model given? What's the difference between a run's logged model artifact and a registered model?

### Assign it the champion alias

Model Registry stages (Staging/Production) are deprecated in current mlflow versions. The replacement is **aliases**: named, mutable pointers to a specific model version (e.g. champion, challenger) that you can reassign at any time without changing the version number itself.

**Option A — from the UI:**

In the mlflow UI, open the food11 registered model, select the version you just created, and add the alias champion to it.

**Option B — from code:**

bash
uv run python -c "
import mlflow
mlflow.set_tracking_uri('http://127.0.0.1:5000')
client = mlflow.MlflowClient()
client.set_registered_model_alias('food11', 'champion', <your-version-number>)
"


> Question 2: What aliases replaced the old built-in stages in mlflow? Why version a model separately from the run that produced it, and why is an alias more flexible than a fixed stage name?

## Write a serving script

Create ./src/food11/serve.py. It should:

1. Use **FastAPI** to expose:
   - GET /health — returns {"status": "ok"}
   - POST /predict — accepts an uploaded image file, runs it through the model, and returns the predicted category and confidence score
2. Load the model once at startup with mlflow.pyfunc.load_model("models:/food11@champion"), not by loading a .pth file directly.
3. Read the mlflow tracking URI from an environment variable (e.g. MLFLOW_TRACKING_URI), defaulting to http://127.0.0.1:5000, so the value can be overridden from inside a container.

bash
uv add fastapi uvicorn python-multipart


Run it locally first, before containerizing anything:

bash
uv run uvicorn src.food11.serve:app --host 0.0.0.0 --port 8000


Test it with an image from your mini dataset:

bash
curl -X POST -F "file=@data/food11_processed_mini/validation/Bread/<some-file>.jpg" http://127.0.0.1:8000/predict


> Question 3: Why load the model through an mlflow model URI (models:/food11@champion) instead of pointing directly at the .pth file on disk? What would you have to change to serve a newer model version?

## Write the Dockerfile

Create a Dockerfile at the root of the repo using a multi-stage build:

- **Stage 1 (builder):** start from a Python base image, install uv, copy only pyproject.toml and uv.lock, then run uv sync --frozen --no-dev to build the virtual environment.
- **Stage 2 (runtime):** start from a slim Python base image, copy the built virtual environment from Stage 1, copy your src/ folder, expose port 8000, and set the container's entrypoint to run uvicorn.

> Question 4: Why copy pyproject.toml/uv.lock and run uv sync *before* copying the rest of the source code, instead of copying everything at once? What happens to the build cache when you only change a line in serve.py?

> Question 5: What's the size difference between a naive single-stage image and your multi-stage one? Use docker history <image> to see which layers are the biggest.

## Add a .dockerignore

Exclude everything the image build doesn't need: .venv/, data/, mlruns/, mlflow.db, .git/, __pycache__/, etc.

> Question 6: What happens to build speed and image size if you forget the .dockerignore? Which of the excluded folders would actually break the build if they were sent to the Docker daemon?

## Build and run the image

bash
docker build -t food11-api:latest .


Your mlflow tracking server is running on the host machine, not inside the container, so the container needs a way to reach it:

- **Linux:** docker run --network host -e MLFLOW_TRACKING_URI=http://127.0.0.1:5000 food11-api:latest
- **Mac/Windows:** docker run -p 8000:8000 -e MLFLOW_TRACKING_URI=http://host.docker.internal:5000 food11-api:latest

> Question 7: Why can't the container simply use 127.0.0.1:5000 to reach the mlflow server on your host? What does host.docker.internal resolve to?

Test the containerized API the same way you tested it locally:

bash
curl -X POST -F "file=@data/food11_processed_mini/validation/Bread/<some-file>.jpg" http://127.0.0.1:8000/predict


> Question 8: Stop the container and start a new one from the same image. Does the model still load correctly without you rebuilding? What does that tell you about what's baked into the image versus fetched at runtime?

## Commit your work

bash
git add Dockerfile .dockerignore src/food11/serve.py pyproject.toml uv.lock
git commit -m "Containerize model serving with Docker"
git push


> Question 9: The Dockerfile and image are versioned differently — one lives in git, the other doesn't (yet). What's still missing before another machine (like a CI runner or a Kubernetes cluster) could reliably pull and run the exact image you just built?


give me 1 file answers for these questions 

Done. I created one file containing the Q1–Q9 Lab 3 answers, based on the actual results from your lab.

Download LAB3_ANSWERS.md 


LAB3_ANSWERS.md
Document


Turn an idea into a website
Build a site for a project, portfolio, or idea.

Explore Sites


Library
/
YOYO_MLOPS
/
LAB3_ANSWERS.md



Lab 3 --- Containerizing the Model with Docker
Question 1
My registered food11 model was given Version 1.

A logged model artifact belongs to one specific MLflow training run. A
registered model gives that model a stable name (food11) and lets
MLflow manage multiple versions independently of the runs that produced
them. This makes deployment and model management easier.

Question 2
The old built-in stages such as Staging and Production were replaced
by aliases, for example champion and challenger.

Versioning the model separately from the run gives each deployable model
a permanent version while preserving the training run that produced it.
An alias is more flexible because it is a mutable pointer: I can move
champion from Version 1 to a newer version without changing the
serving code or the version numbers.

In this lab, I assigned the alias champion to Version 1.

Question 3
I loaded the model using:

models:/food11@champion

instead of directly loading a .pth file because the MLflow URI uses
the Model Registry. MLflow resolves the registered model, its
version/alias, metadata, and packaged model instead of depending on a
hard-coded local model file.

To serve a newer model, I can register the new version and move the
champion alias to it. The serving code can remain unchanged because it
still loads models:/food11@champion.

Question 4
I copied pyproject.toml and uv.lock before the source code so Docker
can cache the expensive dependency-installation layer.

If I only change a line in serve.py, the dependency files have not
changed, so Docker can reuse the cached uv sync layer. It only needs
to rebuild the source-copy layer and the layers after it. If everything
were copied before installing dependencies, a source-code change could
invalidate the dependency layer and make the build much slower.

Question 5
My successfully built multi-stage image food11-api:latest had a
reported size of 9.64 GB.

docker history food11-api:latest showed that the largest application
layer was:

COPY /app/.venv /app/.venv → 6.24 GB

The environment is very large mainly because the installed PyTorch
environment includes large Linux/CUDA-related dependencies.

I also attempted a naive single-stage build. Docker temporarily
displayed it as 3.69 GB, but the build actually failed during the
final image export with a missing Docker snapshot. Running
docker history food11-api:naive also failed because that snapshot did
not exist. Therefore, 3.69 GB is not a valid completed-image
comparison, and I removed the corrupted naive image.

The experiment still showed that multi-stage builds do not automatically
guarantee a small image: the contents copied into the runtime stage
matter. In my image, the 6.24 GB virtual environment dominates the final
size.

Question 6
Without a .dockerignore, Docker sends unnecessary files to the build
context. This makes the context larger, slows builds, wastes storage,
and can invalidate the cache when irrelevant files change. If a
Dockerfile uses broad COPY instructions, these files can also increase
the final image size.

Folders such as data/, mlruns/, .git/, and DVC cache mainly cause
unnecessary size and transfer overhead. The most dangerous excluded
folder is the host .venv/: on Windows it contains Windows-specific
executables and packages, which should not overwrite or interfere with
the Linux virtual environment inside the Docker image. __pycache__/
and .pyc files are also unnecessary platform/runtime artifacts.

My .dockerignore excludes the local environment, datasets, MLflow
artifacts/database, Git files, Python caches, and DVC cache.

Question 7
Inside a container, 127.0.0.1 refers to the container itself, not
the Windows host. Therefore, using 127.0.0.1:5000 inside the API
container would look for an MLflow server inside that same container.

On Docker Desktop, host.docker.internal is a special hostname that
resolves to the host machine from inside the container. I therefore
used:

MLFLOW_TRACKING_URI=http://host.docker.internal:5000

I also had to make the MLflow server listen on 0.0.0.0:5000 and allow
host.docker.internal:5000.

Question 8
Yes. I stopped and removed the original container, then created a
completely new container from the same food11-api:latest image. The
new container started successfully, and:

GET /health returned {"status":"ok"}.

The model was not copied directly into the Docker image. At startup, the
application resolves models:/food11@champion through the MLflow
server. In my local setup, the registered artifact URI was a Windows
file: path, so I also bind-mounted the host mlruns directory into
the Linux container at the path MLflow expected.

This shows that the application code and Python environment are baked
into the image, while the registered model is resolved/loaded at
runtime. It also means the required MLflow registry/artifact storage
must remain accessible to a newly started container.

The containerized prediction endpoint also worked and returned:

{"category":"Fried food","confidence":0.8927886486053467}

for the Bread test image. The incorrect category is a model prediction
issue, not a Docker/API failure.

Question 9
The missing step is to publish the built Docker image to an image
registry, such as Docker Hub, GitHub Container Registry, or another
container registry.

The Dockerfile in Git describes how to build the image, but another
machine cannot pull my local Docker image from Git. For reliable
deployment, I should tag and push the image to a registry and use an
immutable version tag or, preferably, an image digest. Then a CI runner
or Kubernetes deployment can pull the exact same built image instead of
rebuilding it and potentially getting different dependencies or
base-image contents.

Lab 3 Git commit: 79a74a6

Registered model: food11 Version 1
Alias: champion
Best run ID: 4642609a5ec7421e8589cdd6dd484160
