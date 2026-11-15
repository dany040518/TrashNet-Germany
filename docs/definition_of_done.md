# Jira Board Governance and Definition of Done

## 1. Hybrid Methodology Overview: CRISP-DM + Scrum

The project combines CRISP-DM's data-mining lifecycle with Scrum's iterative planning and feedback. The six CRISP-DM phases are organized as six project Sprints, scheduled from calendar week (CW) 43 through CW 03:

| Sprint | Planned period | CRISP-DM phase | Main outcome |
| --- | --- | --- | --- |
| Sprint 1 | CW 43–44 | Business Understanding | Define the waste-sorting problem, users, project goals, and success criteria. |
| Sprint 2 | CW 45–46 | Data Understanding | Identify, acquire, describe, and assess candidate datasets. |
| Sprint 3 | CW 47–48 | Data Preparation | Clean, label, transform, and organize data for reproducible experiments. |
| Sprint 4 | CW 49–50 | Modeling | Train and compare suitable baseline and candidate models. |
| Sprint 5 | CW 51–52 | Evaluation | Evaluate models against project goals, analyze errors, and decide whether results are fit for the intended use. |
| Sprint 6 | CW 01–03 | Deployment | Prepare the integrated demonstrator, documentation, and final presentation. |

Sprint Planning selects and estimates Jira work against the phase outcome. Weekly Syncs track progress, dependencies, and blockers. The team gives a 5-minute Sprint Update/Review to communicate progress and demonstrate completed work, followed by a Retrospective to agree on improvements for the next Sprint. The Buddy Group provides continuous review and feedback throughout the project, helping the team refine its work toward the final Shark Tank presentation.

## 2. Jira Board and Workflow Governance

The Jira Scrum board uses these columns, in order:

**To Do → In Progress → Done**

All work is tracked in Jira and associated with its GitHub changes using the exact ticket key:

- **Branch names:** `EDM-<id>-<short-slug>`, for example `EDM-19-1-1-4-configure-jira-board-and-definition-of-done`.
- **Commit messages:** `EDM-<id> <imperative description>`, for example `EDM-19 1.1.4 Configure Jira board and Definition of Done`. Do not put a colon after the Jira key.

A ticket may move to **Done** only when its commit or branch is visible in the Jira **Development** panel and its Pull Request targeting `dev` has been reviewed and approved on GitHub. The change must also satisfy the applicable Definition of Done below.

## 3. Team Definition of Done by Role and Deliverable Type

### General DoD: all tickets

- The ticket is linked to its numeric Jira key (`EDM-xx`) in the branch and commit, and Jira shows the associated development activity.
- The Pull Request is reviewed and approved on GitHub before it is merged into `dev`.
- No sensitive credentials or raw binary datasets are committed. This includes `.env` files and `kaggle.json`.
- The change is documented sufficiently for another team member to understand and reproduce it.

### Data and IoT Infrastructure (DM)

- Python scripts in `/src` and `/iot` are modular and PEP 8 compliant.
- The workflow is reproducible from the command line and uses fixed random seeds (`seed=42`) wherever randomness is involved.
- Relevant sanity checks and unit checks pass.

### Data Analysis and ML Evaluation (NM)

- Notebooks in `/notebooks` are reproducible and include a clear Markdown narrative describing data, methods, and conclusions.
- Evaluation logs Macro F1 (target: **≥ 0.80**), Precision, and Recall.
- Normalized confusion matrices are generated and saved in `/docs`.

### Product and UI/UX Design (LA)

- Interfaces are bilingual (German and English) and accessible.
- Waste guidance aligns with the official German bin categories: *Gelber Sack*, *Restmüll*, *Papier*, *Bioabfall*, and *Altglas*.
- Exported design assets are placed in `/design`.

## 4. AI Coding Agent and Reproducibility Log Policy

The team may use coding assistants, including Copilot and other LLMs, as support tools; team members remain responsible for the correctness, licensing, privacy, and maintainability of all submitted work. AI-generated output is not considered verified until a team member has inspected and tested it.

For each material use of an assistant that contributes to project deliverables, record an entry in the project AI assistance log, linked from the relevant Jira ticket or Pull Request. Each entry must include:

- Date, contributor, Jira key, assistant/tool used, and the task or files involved.
- A concise description of the assistance requested and the suggestions or generated content used.
- What the contributor changed, verified, or rejected, including relevant tests or reproducibility checks and their results.
- Any limitations, errors, or required attribution identified during review.

Do not include credentials, personal data, private datasets, or other restricted content in prompts or logs. Keep the log concise but sufficiently specific for teammates and course staff to audit how AI assistance was used and how the resulting work was validated, satisfying the course rubric's Logs requirement.
