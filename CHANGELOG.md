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

## [1.0.2] - 2024-12-28
- Merged PR #3 by @MarcChen: Feat/enhance workflows
This pull request includes changes to the `.github/workflows/run-container.yml` file to update the workflow triggers and the Docker image version used in the `run-container` job.

Changes to workflow triggers:

* [`.github/workflows/run-container.yml`](diffhunk://#diff-9d8fa071698624d0a009b95095bdbb9802888955407a82532e59666535968260L4-R11): Updated the workflow to trigger on completion of the "Versioning, Tagging, and Docker Image Push" workflow instead of on push to the main branch.

Changes to Docker image version:

* [`.github/workflows/run-container.yml`](diffhunk://#diff-9d8fa071698624d0a009b95095bdbb9802888955407a82532e59666535968260L32-R35): Changed the Docker image version from `0.0.1` to `latest` in the `run-container` job.

## [1.1.0] - 2024-12-28
- Merged PR #4 by @MarcChen: Feat/enhance workflows
# Enhancements to GitHub Actions Workflows for Docker Image Management and Multi-Platform Builds

This pull request introduces improvements to the Docker image handling process and adds support for multi-platform builds in the GitHub Actions workflows. The updates address issues encountered with self-hosted runners and optimize the build and pull processes.

## Key Changes:
### **Improved Docker Image Handling**
- **Workflow:** [`.github/workflows/run-container.yml`](diffhunk://#diff-9d8fa071698624d0a009b95095bdbb9802888955407a82532e59666535968260L21-R34)
  - Added a check to determine if the Docker image exists locally on the self-hosted runner before pulling it, reducing redundant pulls and improving efficiency.

### **Added Multi-Platform Build Support**
- **Workflow:** [`.github/workflows/versioning.yml`](diffhunk://#diff-a939aacba1dba4141eda9eda616ff5e54462b324fbaebe0f8848c06964e67c68L105-R116)
  - Integrated Docker Buildx for multi-platform builds.
  - Updated the build and push steps to target both `linux/amd64` and `linux/arm64` platforms, ensuring broader compatibility and deployment options.

These changes streamline the CI/CD pipeline, enhance support for diverse environments, and improve reliability when using self-hosted runners.

## [1.2.0] - 2025-01-22
- Merged PR #5 by @MarcChen: Feat/update url wider scope
# Pull Request Description

This pull request introduces several key improvements to the functionality and performance of the codebase. The most significant changes include updates to the `main.py` script to enhance job offer processing, modifications to the `Dockerfile` to optimize the container setup, and an adjustment to the workflow schedule.

### Enhancements to Job Offer Processing:

- **Wider Web Query and Local Filtering:**
  - [`main.py`](diffhunk://#diff-b10564ab7d2c520cdd0243874879fb0a782862c3c902ab535faabe57d5a505e1L21-R22): Modified the URL used by the `JobScraper` to search for job offers with a broader query, as the filtering on the webpage was not functioning effectively. Instead, filtering is now handled locally in the `main.py` script.
  - [`main.py`](diffhunk://#diff-b10564ab7d2c520cdd0243874879fb0a782862c3c902ab535faabe57d5a505e1L30-R40): Added a filter to skip job offers that do not contain the word "data" in the title, along with a log message for skipped offers.
  - [`main.py`](diffhunk://#diff-b10564ab7d2c520cdd0243874879fb0a782862c3c902ab535faabe57d5a505e1R55): Introduced a `time.sleep(1)` call after sending an SMS to prevent rate-limiting issues.

### Streamlining Container Setup:

- **Dockerfile Optimization:**
  - [`Dockerfile`](diffhunk://#diff-dd2c0eb6ea5cfc6c4bd4eac30934e2d5746747af48fef6da689e85b752f39557L6-L13): Removed the redundant installation of Python and pip, as the base image now includes Python support. Updated the command to run the Python script using `python3`.

### Workflow Schedule Adjustment:

- **Increased Workflow Frequency:**
  - [`.github/workflows/run-container.yml`](diffhunk://#diff-9d8fa071698624d0a009b95095bdbb9802888955407a82532e59666535968260L9-R9): Changed the schedule to run the workflow daily instead of every two days.

## [1.3.0] - 2025-01-26
- Merged PR #7 by @MarcChen: Feature : Scraping new website
This pull request includes significant changes to the job scraping and notification system, focusing on improving the scraping process, enhancing data handling, and refining the workflow configuration. The most important changes are outlined below.

### Workflow Configuration Updates:
* [`.github/workflows/run-container.yml`](diffhunk://#diff-9d8fa071698624d0a009b95095bdbb9802888955407a82532e59666535968260L9-R9): Adjusted the cron schedule to run every two days instead of daily and simplified the Docker image pulling process by removing the local image check. [[1]](diffhunk://#diff-9d8fa071698624d0a009b95095bdbb9802888955407a82532e59666535968260L9-R9) [[2]](diffhunk://#diff-9d8fa071698624d0a009b95095bdbb9802888955407a82532e59666535968260L21-R21)

### Dockerfile Update:
* [`Dockerfile`](diffhunk://#diff-dd2c0eb6ea5cfc6c4bd4eac30934e2d5746747af48fef6da689e85b752f39557L1-R1): Updated the base image version from `latest` to `132.0` for better stability and reproducibility.

### Main Script Enhancements:
* [`main.py`](diffhunk://#diff-b10564ab7d2c520cdd0243874879fb0a782862c3c902ab535faabe57d5a505e1L1-R3): Introduced multiple scrapers for different job sources, added a unified driver setup, and refined the job offer processing logic to handle multiple sources and improve SMS notifications. [[1]](diffhunk://#diff-b10564ab7d2c520cdd0243874879fb0a782862c3c902ab535faabe57d5a505e1L1-R3) [[2]](diffhunk://#diff-b10564ab7d2c520cdd0243874879fb0a782862c3c902ab535faabe57d5a505e1L22-R75) [[3]](diffhunk://#diff-b10564ab7d2c520cdd0243874879fb0a782862c3c902ab535faabe57d5a505e1L63-R108)

### Notion Client Simplification:
* [`src/notion_client.py`](diffhunk://#diff-7429c4882a1f31205d75db63e2f26239272f5745292b309bada97d138b03e402L69-R69): Simplified the `create_page` method to directly use the provided properties without additional transformation.

### Selenium Script Refactoring:
* [`src/selenium_script.py`](diffhunk://#diff-e8253c08be5d3a0d2d00c1038b0d8459ea66224a0cb76ceb8099f0ccf85aa27eR1-R93): Refactored the job scraper into a base class with common functionalities and specific scrapers for different job sources, improved the offer extraction process, and added better error handling and logging. [[1]](diffhunk://#diff-e8253c08be5d3a0d2d00c1038b0d8459ea66224a0cb76ceb8099f0ccf85aa27eR1-R93) [[2]](diffhunk://#diff-e8253c08be5d3a0d2d00c1038b0d8459ea66224a0cb76ceb8099f0ccf85aa27eL57-R114) [[3]](diffhunk://#diff-e8253c08be5d3a0d2d00c1038b0d8459ea66224a0cb76ceb8099f0ccf85aa27eL73-R129) [[4]](diffhunk://#diff-e8253c08be5d3a0d2d00c1038b0d8459ea66224a0cb76ceb8099f0ccf85aa27eR145) [[5]](diffhunk://#diff-e8253c08be5d3a0d2d00c1038b0d8459ea66224a0cb76ceb8099f0ccf85aa27eL100-R167)

## [1.4.0] - 2025-02-01
- Merged PR #8 by @MarcChen: Feature : Add Apple Job Scraper and Enhance Progress Display
This pull request includes several changes to improve the functionality and readability of the codebase, particularly in the `main.py` file, and updates to the `NotionClient` and `SMSAPI` classes. The most important changes include the addition of new job scrapers, enhancements to the progress display, and refactoring for better code organization and readability.

### Enhancements and New Features:

* [`main.py`](diffhunk://#diff-b10564ab7d2c520cdd0243874879fb0a782862c3c902ab535faabe57d5a505e1L1-L8): Added new job scrapers for Apple and Air France, and included filters for job scraping. Enhanced the progress display with `rich.progress` for better user feedback. [[1]](diffhunk://#diff-b10564ab7d2c520cdd0243874879fb0a782862c3c902ab535faabe57d5a505e1L1-L8) [[2]](diffhunk://#diff-b10564ab7d2c520cdd0243874879fb0a782862c3c902ab535faabe57d5a505e1L18-R120) [[3]](diffhunk://#diff-b10564ab7d2c520cdd0243874879fb0a782862c3c902ab535faabe57d5a505e1L51-R130)

### Code Refactoring:

* [`main.py`](diffhunk://#diff-b10564ab7d2c520cdd0243874879fb0a782862c3c902ab535faabe57d5a505e1L18-R120): Refactored environment variable assertions for better readability and added clipping to job description content to prevent exceeding character limits. [[1]](diffhunk://#diff-b10564ab7d2c520cdd0243874879fb0a782862c3c902ab535faabe57d5a505e1L18-R120) [[2]](diffhunk://#diff-b10564ab7d2c520cdd0243874879fb0a782862c3c902ab535faabe57d5a505e1R175-R181)

### Bug Fixes and Improvements:

* [`src/notion_client.py`](diffhunk://#diff-7429c4882a1f31205d75db63e2f26239272f5745292b309bada97d138b03e402L40-R43): Fixed potential issues with title extraction and page creation by ensuring proper handling of nested dictionary keys. [[1]](diffhunk://#diff-7429c4882a1f31205d75db63e2f26239272f5745292b309bada97d138b03e402L40-R43) [[2]](diffhunk://#diff-7429c4882a1f31205d75db63e2f26239272f5745292b309bada97d138b03e402L57-R79) [[3]](diffhunk://#diff-7429c4882a1f31205d75db63e2f26239272f5745292b309bada97d138b03e402L101-R113)
* [`src/sms_alert.py`](diffhunk://#diff-63ce700dc6ae6fb80952720037c6c9335cf2df7610189b902bb9323771f84afaL63-R71): Improved URL construction and error handling for sending SMS messages. [[1]](diffhunk://#diff-63ce700dc6ae6fb80952720037c6c9335cf2df7610189b902bb9323771f84afaL63-R71) [[2]](diffhunk://#diff-63ce700dc6ae6fb80952720037c6c9335cf2df7610189b902bb9323771f84afaL86-R101)

### Testing Enhancements:

* [`tests/unit/test_notion_client.py`](diffhunk://#diff-0e99ca6211eca238679db98be31f9335359ddd03689c7243cfcadb2edd481431R1-R12): Added and updated unit tests for `NotionClient` to ensure correct functionality after refactoring. [[1]](diffhunk://#diff-0e99ca6211eca238679db98be31f9335359ddd03689c7243cfcadb2edd481431R1-R12) [[2]](diffhunk://#diff-0e99ca6211eca238679db98be31f9335359ddd03689c7243cfcadb2edd481431L18-R26)
* [`tests/unit/test_selenium_script.py`](diffhunk://#diff-73d2dc78a93ae01834049dac82d7c9a37411e0eec34be56bc46650af901f9c49R3-R13): Updated unit tests for `VIEJobScraper` and `AirFranceJobScraper` to reflect new functionalities and improved mocking. [[1]](diffhunk://#diff-73d2dc78a93ae01834049dac82d7c9a37411e0eec34be56bc46650af901f9c49R3-R13) [[2]](diffhunk://#diff-73d2dc78a93ae01834049dac82d7c9a37411e0eec34be56bc46650af901f9c49L45-R74)

### Configuration Changes:

* [`.github/workflows/run-container.yml`](diffhunk://#diff-9d8fa071698624d0a009b95095bdbb9802888955407a82532e59666535968260L9-R9): Updated the cron schedule to run every 4 hours instead of every 2 hours.

## [1.4.1] - 2025-02-01
- Merged PR #9 by @MarcChen: fix : enable headless mode using selenium
This pull request includes a small change to the `main.py` file. The change involves removing the `debug=True` parameter from the `setup_driver` function call.

* [`main.py`](diffhunk://#diff-b10564ab7d2c520cdd0243874879fb0a782862c3c902ab535faabe57d5a505e1L54-R54): Removed the `debug=True` parameter from the `setup_driver` function call.

