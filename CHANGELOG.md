## [1.0.0] - 2024-12-28
- Merged PR #1 by @MarcChen: Feat/scrapping img
This pull request introduces significant changes to the repository, including new workflows, a Dockerfile, and updates to the main application logic. The changes are aimed at automating the job scraping process, integrating with Notion, and sending real-time alerts. Here are the most important changes:

### CI/CD Workflow Enhancements:
* [`.github/workflows/run-container.yml`](diffhunk://#diff-9d8fa071698624d0a009b95095bdbb9802888955407a82532e59666535968260R1-R32): Added a new workflow to run the Selenium Python app on push to the main branch and on a schedule. This workflow logs into the GitHub Container Registry, pulls a Docker image, and runs the container with the necessary environment variables.
* [`.github/workflows/test.yml`](diffhunk://#diff-faff1af3d8ff408964a57b2e475f69a6b7c7b71c9978cccc8f471798caac2c88R1-R27): Introduced a new workflow to run tests on pull requests. This workflow sets up Python, installs dependencies, and runs pytest.
* [`.github/workflows/versioning.yml`](diffhunk://#diff-a939aacba1dba4141eda9eda616ff5e54462b324fbaebe0f8848c06964e67c68L1-R1): Updated the versioning workflow to include tagging and pushing Docker images to the GitHub Container Registry. [[1]](diffhunk://#diff-a939aacba1dba4141eda9eda616ff5e54462b324fbaebe0f8848c06964e67c68L1-R1) [[2]](diffhunk://#diff-a939aacba1dba4141eda9eda616ff5e54462b324fbaebe0f8848c06964e67c68R100-R111)

### Application Logic and Dockerfile:
* [`Dockerfile`](diffhunk://#diff-dd2c0eb6ea5cfc6c4bd4eac30934e2d5746747af48fef6da689e85b752f39557R1-R36): Added a Dockerfile to set up the environment, including installing Python and dependencies, copying the application code, and running the main Python script.
* [`main.py`](diffhunk://#diff-b10564ab7d2c520cdd0243874879fb0a782862c3c902ab535faabe57d5a505e1R1-R70): Added the main application logic to scrape job offers, integrate with Notion, and send SMS alerts.

### Documentation:
* [`README.md`](diffhunk://#diff-b335630551682c19a781afebcf4d07bf978fb1f8ac04c6bf87428ed5106870f5L1-R113): Updated the README to reflect the new project name "VIE-Tracker," provide an overview of the project, and include setup and usage instructions.

## [1.0.1] - 2024-12-28
- Merged PR #2 by @MarcChen: update versioning workflow with new PAT
This pull request includes a small change to the `.github/workflows/versioning.yml` file. The change updates the secret used for logging into the GitHub Container Registry to use `GHCR_PAT_WRITE_PACKAGE` instead of `GHCR_PAT`.

* [`.github/workflows/versioning.yml`](diffhunk://#diff-a939aacba1dba4141eda9eda616ff5e54462b324fbaebe0f8848c06964e67c68L103-R103): Updated the secret for Docker login to `GHCR_PAT_WRITE_PACKAGE` for improved security.

