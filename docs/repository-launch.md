# Put Catfish Lab on GitHub

This is the release path for the repository—not a hosting substitute. Catfish does not require
GitHub Pages. The local MkDocs handbook remains a build artifact, while GitHub hosts the source,
issues, pull requests, and CI.

## 1. Install the real prerequisites

On Arch Linux, install the repository tools from the official package repositories
([GitHub CLI](https://archlinux.org/packages/extra/x86_64/github-cli/),
[Docker](https://archlinux.org/packages/extra/x86_64/docker/),
[Compose](https://archlinux.org/packages/extra/x86_64/docker-compose/), and the
[Buildx plugin](https://archlinux.org/packages/extra/x86_64/docker-buildx/)):

```bash
sudo pacman -S --needed github-cli docker docker-compose docker-buildx
sudo systemctl enable --now docker.service
sudo usermod -aG docker "$USER"
```

Sign out and back in after the group change. Then prove the installation instead of assuming it:

```bash
gh --version
docker info
docker compose version
docker buildx version
```

Membership in the `docker` group grants substantial host authority. Use
[Arch's documented rootless Docker setup](https://wiki.archlinux.org/title/Docker#Rootless_Docker_daemon)
instead if that is your security policy; do not alias another container runtime and claim Docker
was tested.

## 2. Prove the checkout

From the Catfish project directory:

```bash
uv sync --locked --extra docs --group dev
uv run ruff check .
uv run pytest -q
uv run lab doctor
uv run mkdocs build --strict
docker compose config
docker compose build
docker compose run --rm lab doctor
docker compose run --rm lab logbook --snapshot
```

Do not commit `site/`, `dist/`, virtual environments, test caches, provider credentials, or private
prompt material. Inspect `git status` before every commit.

## 3. Create local history

The repository root is the directory containing this file's parent `docs/`, `pyproject.toml`, and
`README.md`:

```bash
git init -b main
git config user.name "YOUR NAME"
git config user.email "YOUR VERIFIED GITHUB EMAIL"
git add .
git status --short
git diff --cached --check
git commit -m "Initial public release of Catfish Lab"
```

Review the staged file list before committing. The user name and email are authorship decisions;
Catfish must not invent them.

## 4. Authenticate and publish

Use GitHub CLI's documented [browser/device authentication](https://cli.github.com/manual/gh_auth_login)
and verify the resulting account:

```bash
gh auth login --hostname github.com --git-protocol https --web
gh auth status
```

After choosing the owner, repository name, and visibility, use
[`gh repo create`](https://cli.github.com/manual/gh_repo_create) to create the remote from the
existing local repository and push the commit:

```bash
gh repo create OWNER/catfish-lab \
  --public \
  --source=. \
  --remote=origin \
  --push \
  --description "A quality-control room for AI-assisted work"
```

Use `--private` instead of `--public` only if that is the deliberate launch decision. Do not add a
README, license, or `.gitignore` through GitHub because this repository already owns those files.

## 5. Verify the remote result

```bash
git remote -v
git status --short --branch
gh repo view OWNER/catfish-lab
gh run list --repo OWNER/catfish-lab
```

The launch is complete only when `origin` points to the intended repository, `main` is pushed, the
README renders, and the **Lab quality gate** workflow succeeds. A failing Actions job is release
evidence to investigate, not a reason to disable the check.
