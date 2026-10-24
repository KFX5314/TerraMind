# TerraMind

Our project for the Certivity challenge at the Industrial Agents Hackathon.

The implementation specification is in [CODING_AGENT_HANDOFF.md](CODING_AGENT_HANDOFF.md). The application has not been scaffolded yet.

## Repository layout

- This repository contains our project code, documentation, and tests.
- `industrial-ai-hackathon/` is a separate, ignored checkout of the organizer's repository. Its `origin` remains `https://github.com/Certivity/industrial-ai-hackathon.git`.
- Local datasets, generated artifacts, credentials, and temporary files are excluded from this repository.

## Get the challenge package

After cloning this project, run the following from its root if the organizer checkout is not already present:

```powershell
git clone https://github.com/Certivity/industrial-ai-hackathon.git
```

Refresh the organizer package, including released held-out inputs, with:

```powershell
git -C industrial-ai-hackathon pull --ff-only
```

Download the provided regulation PDFs using the organizer's tool:

```powershell
python industrial-ai-hackathon/tools/fetch_regulations.py
```

Follow the organizer's README for setup, evaluation, and submission details. Its participant data is restricted to hackathon use and may not be redistributed without written permission; it is deliberately not included in this repository. The organizer checkout remains independently updateable.
