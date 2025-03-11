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

## [1.4.2] - 2025-02-01
- Merged PR #10 by @MarcChen: Fix: Restore SMS Sending Functionality
This pull request includes a small change to the `main.py` file. The change re-enables the sending of SMS messages by uncommenting the `sms_client.send_sms(sms_message)` and `time.sleep(1)` lines.

## [1.4.3] - 2025-02-11
- Merged PR #11 by @MarcChen: fixing not raising errors, missing dep, and apple job not correctly formated
This pull request includes several changes to the `main.py` and `src/selenium_script.py` files to improve error handling, add new keywords, and enhance the data validation process. The most important changes are grouped by their themes below:

### Error Handling Improvements:

* Changed error messages to raise `ValueError` instead of printing them in `main.py` and `src/selenium_script.py` for better exception management. [[1]](diffhunk://#diff-b10564ab7d2c520cdd0243874879fb0a782862c3c902ab535faabe57d5a505e1L188-R190) [[2]](diffhunk://#diff-e8253c08be5d3a0d2d00c1038b0d8459ea66224a0cb76ceb8099f0ccf85aa27eL395-R400) [[3]](diffhunk://#diff-e8253c08be5d3a0d2d00c1038b0d8459ea66224a0cb76ceb8099f0ccf85aa27eL489-R494) [[4]](diffhunk://#diff-e8253c08be5d3a0d2d00c1038b0d8459ea66224a0cb76ceb8099f0ccf85aa27eL642-R647) [[5]](diffhunk://#diff-e8253c08be5d3a0d2d00c1038b0d8459ea66224a0cb76ceb8099f0ccf85aa27eR714-R720)

### Data Validation Enhancements:

* Updated the `validate_offer` method in `src/selenium_script.py` to warn about missing fields and return `False` if any required fields are missing.

### Keyword Additions:

* Added new keywords "software" and "developer" to the list in `main.py` to improve search relevance.

### Code Import Updates:

* Added missing imports in `main.py` and `src/selenium_script.py` to ensure all necessary modules are included. [[1]](diffhunk://#diff-b10564ab7d2c520cdd0243874879fb0a782862c3c902ab535faabe57d5a505e1R2) [[2]](diffhunk://#diff-e8253c08be5d3a0d2d00c1038b0d8459ea66224a0cb76ceb8099f0ccf85aa27eR1-R4)

### Minor Code Cleanups:

* Removed an unnecessary method call in `main.py` to streamline the scraping process.
* Added warnings for errors encountered during data extraction in `src/selenium_script.py` to provide better debugging information. [[1]](diffhunk://#diff-e8253c08be5d3a0d2d00c1038b0d8459ea66224a0cb76ceb8099f0ccf85aa27eL242-R247) [[2]](diffhunk://#diff-e8253c08be5d3a0d2d00c1038b0d8459ea66224a0cb76ceb8099f0ccf85aa27eR428)This pull request includes several changes to improve error handling and logging in `main.py` and `src/selenium_script.py`. The most important changes involve replacing print statements with exceptions and warnings for better error management.

Error handling improvements:

* [`main.py`](diffhunk://#diff-b10564ab7d2c520cdd0243874879fb0a782862c3c902ab535faabe57d5a505e1L188-R189): Changed the error message handling in the job offers processing section to raise a `ValueError` instead of printing the error message.
* [`src/selenium_script.py`](diffhunk://#diff-e8253c08be5d3a0d2d00c1038b0d8459ea66224a0cb76ceb8099f0ccf85aa27eR3): Added `warnings` import and replaced print statements with `warnings.warn` for non-critical errors during data extraction. [[1]](diffhunk://#diff-e8253c08be5d3a0d2d00c1038b0d8459ea66224a0cb76ceb8099f0ccf85aa27eR3) [[2]](diffhunk://#diff-e8253c08be5d3a0d2d00c1038b0d8459ea66224a0cb76ceb8099f0ccf85aa27eL242-R243) [[3]](diffhunk://#diff-e8253c08be5d3a0d2d00c1038b0d8459ea66224a0cb76ceb8099f0ccf85aa27eR424)
* [`src/selenium_script.py`](diffhunk://#diff-e8253c08be5d3a0d2d00c1038b0d8459ea66224a0cb76ceb8099f0ccf85aa27eL395-R396): Replaced print statements with `ValueError` exceptions for critical errors during the loading of offers. [[1]](diffhunk://#diff-e8253c08be5d3a0d2d00c1038b0d8459ea66224a0cb76ceb8099f0ccf85aa27eL395-R396) [[2]](diffhunk://#diff-e8253c08be5d3a0d2d00c1038b0d8459ea66224a0cb76ceb8099f0ccf85aa27eL642-R643) [[3]](diffhunk://#diff-e8253c08be5d3a0d2d00c1038b0d8459ea66224a0cb76ceb8099f0ccf85aa27eL715-R715)

Additionally, minor improvements include importing necessary modules:

* [`main.py`](diffhunk://#diff-b10564ab7d2c520cdd0243874879fb0a782862c3c902ab535faabe57d5a505e1R2): Added `time` import.
* [`src/selenium_script.py`](diffhunk://#diff-e8253c08be5d3a0d2d00c1038b0d8459ea66224a0cb76ceb8099f0ccf85aa27eR3): Added `warnings` import.

## [1.5.0] - 2025-02-11
- Merged PR #12 by @MarcChen: Feature : Code refacto 
This pull request introduces several significant changes to the codebase, focusing on improving the testing workflows, refactoring the main application logic, and enhancing the Docker setup. Below are the most important changes grouped by their themes:

### Workflow and Testing Improvements:
* [`.github/workflows/validate-PR.yml`](diffhunk://#diff-14b4ce75de35f234703c58969492cd5f2871cb68be1344d95b431882c5426e1dR1-R70): Added a new workflow to validate PR labels and run unit tests, replacing the old `test.yml`. The new workflow includes steps for checking PR labels and running unit tests with Poetry.
* [`.flake8`](diffhunk://#diff-6951dbb399883798a226c1fb496fdb4183b1ab48865e75eddecf6ceb6cf46442R1-R11): Added a new configuration file for Flake8 to enforce code style standards, including setting the maximum line length and ignoring specific errors.

### Refactoring and Code Simplification:
* [`main.py`](diffhunk://#diff-b10564ab7d2c520cdd0243874879fb0a782862c3c902ab535faabe57d5a505e1L1-L28): Refactored the main script to use a new `OfferProcessor` class and a `scrape_all_offers` function, significantly simplifying the main logic. Removed direct handling of environment variables and job scrapers. [[1]](diffhunk://#diff-b10564ab7d2c520cdd0243874879fb0a782862c3c902ab535faabe57d5a505e1L1-L28) [[2]](diffhunk://#diff-b10564ab7d2c520cdd0243874879fb0a782862c3c902ab535faabe57d5a505e1L56-R42)
* `src/job_scrapers/`Splited all the existing Scraper Class to singles files in a dedicated subfolder `src/job_scrapers/`

### Docker and Build Enhancements:
* [`Dockerfile`](diffhunk://#diff-dd2c0eb6ea5cfc6c4bd4eac30934e2d5746747af48fef6da689e85b752f39557L3-R22): Updated the Dockerfile to use Poetry for dependency management instead of pip, and adjusted the setup commands accordingly.
* [`Makefile`](diffhunk://#diff-76ed074a9305c04054cdebb9e9aad2d818052b07091de1f20cad0bbac34ffb52R1-R14): Added new targets for launching, stopping, and restarting the Chromium container, as well as building and launching the Docker image.

### Configuration and Dependency Management:
* [`pyproject.toml`](diffhunk://#diff-50c86b7ed8ac2cf95bd48334961bf0530cdc77b5a56f852c5c61b89d735fd711R1-R29): Introduced a new `pyproject.toml` file for managing project dependencies using Poetry, including both main and development dependencies.

### Script Enhancements:
* [`scripts/launch_chromium.sh`](diffhunk://#diff-6470d7917b15538a9fed2f1ba28e996f4a1572b25aa701b406500d0db54c7b12R1-R35): Added a script to launch a Selenium Chromium container and set up the environment variables from a `.env` file.
* [`scripts/restart_chromium.sh`](diffhunk://#diff-b1b60e635feddf90fa48ece2dcaea537506d755241cc8a1a901160939cda08b6R1-R8): Added a script to restart the Selenium Chromium container.
* [`scripts/stop_chromium.sh`](diffhunk://#diff-169a1615846ababcce29b6e5287af016aed54c54d17671494181445b46a1933fR1-R9): Added a script to stop the Selenium Chromium container.

## [1.6.0] - 2025-02-12
- Merged PR #13 by @MarcChen: Feature : Added Welcome to the Jungle Website
This pull request introduces a new job scraper for "Welcome to the Jungle" and includes several enhancements and refactoring across various files. The most important changes include the addition of the new scraper, updates to the base scraper class, and modifications to the scraper orchestration and testing.

### New Scraper Addition:
* [`src/job_scrapers/welcome_to_the_jungle.py`](diffhunk://#diff-dc19ee754afa8db50121eb04ed34a9287b7c872332c116bacd113d661596affdR1-R280): Added a new class `WelcomeToTheJungleJobScraper` to scrape job listings from the "Welcome to the Jungle" website. This includes methods to load all offers and extract detailed data from each job offer page.

### Base Scraper Enhancements:
* [`src/job_scrapers/job_scraper_base.py`](diffhunk://#diff-7f338ed0671888035a42ac05559e67dde300fa1ca4b1cd9b706b64b2a8b50c66R32-R33): Updated the `_init_offer_dict` method to include new fields "Experience Level" and "Salary" in the job offer dictionary.

### Scraper Orchestration:
* [`src/scraper.py`](diffhunk://#diff-0e4337d858599ae81588070897d6d27bb45de76e0e4dd92ad2ae2e55f575ca0eR9): Integrated the new `WelcomeToTheJungleJobScraper` into the main scraping workflow. Added URLs and instances for scraping data engineer and AI job offers, and updated the merging of scraped data. [[1]](diffhunk://#diff-0e4337d858599ae81588070897d6d27bb45de76e0e4dd92ad2ae2e55f575ca0eR9) [[2]](diffhunk://#diff-0e4337d858599ae81588070897d6d27bb45de76e0e4dd92ad2ae2e55f575ca0eR31) [[3]](diffhunk://#diff-0e4337d858599ae81588070897d6d27bb45de76e0e4dd92ad2ae2e55f575ca0eR57-R76) [[4]](diffhunk://#diff-0e4337d858599ae81588070897d6d27bb45de76e0e4dd92ad2ae2e55f575ca0eR94-L78)

### Debugging and Logging:
* `src/job_scrapers/airfrance.py` and `src/job_scrapers/apple.py`: Replaced conditional print statements with the `rich` library for better debug output formatting. [[1]](diffhunk://#diff-49f2494f9f1ecc85b6df5db47e3d9b63f0d5d44c5908657e225b3335788c15c6L224-R227) [[2]](diffhunk://#diff-0cf6b1646f0fb50435686901fc8ab3d3c4d329fe4bed0ef6b66a9d1ff3427318L211-R214)

### Unit Testing:
* [`tests/unit/test_wtj_scraper.py`](diffhunk://#diff-d443dbcfd56c1a71634c169759cf479577397680d64c1af0f0588cd8c2db64b8R1-R70): Added unit tests for the `WelcomeToTheJungleJobScraper` to verify the extraction of total offers and detailed job offers using dummy elements and a mock driver.

## [1.6.1] - 2025-02-12
- Merged PR #14 by @MarcChen: fix  : intercepted element
This pull request includes an important change to the `load_all_offers` method in the `src/job_scrapers/welcome_to_the_jungle.py` file to improve the reliability of the web scraping process.

Improvements to web scraping process:

* [`src/job_scrapers/welcome_to_the_jungle.py`](diffhunk://#diff-dc19ee754afa8db50121eb04ed34a9287b7c872332c116bacd113d661596affdR77-R81): Added a wait condition to ensure the invisibility of an element with a high z-index before clicking the clear button. This change helps to avoid potential issues caused by overlapping elements during the interaction.

## [1.6.2] - 2025-02-12
- Merged PR #15 by @MarcChen: fixing intercepted click - 2 
This pull request includes changes to the `load_all_offers` method in the `src/job_scrapers/welcome_to_the_jungle.py` file to improve the functionality of interacting with the web page elements.

Enhancements to web element interaction:

* Added a step to click the French button if it appears, ensuring the page is in the correct language.
* Removed the wait for the invisibility of an element with high z-index, streamlining the process of clearing the location input field.

## [1.7.0] - 2025-02-13
- Merged PR #16 by @MarcChen: Feature : enhance workflow
# Overview

This PR addresses performance issues and duplicate detection in our Notion integration for job offers. Previously, we queried Notion for each offer by title, which led to two major problems:

- **Duplicate Offers**: Offers with the same title were not being correctly identified as duplicates.
- **API Limitations**: Notion’s query returns are capped at 100 pages, causing some existing offers to be missed.

## Key Changes

### 1. Enhanced Duplicate Checking
- **Problem**: Relying solely on the title allowed duplicate entries when different offers shared the same title.
- **Solution**: We now use a composite key (multiple attributes) to ensure each offer is uniquely identified.

### 2. Performance Optimization
- **Problem**: Multiple queries to Notion’s API were both slow and incomplete due to the 100-page limit.
- **Solution**: Refactored to use a dedicated PyPI package that loads all stored pages from Notion into memory. This allows us to perform a single query at initialization and only append offers that are truly new, significantly speeding up the scraping process.

### 3. Additional Improvements
- **Filter Handling**: Added a centralized `should_skip_offer` method in the job scraper base class to streamline include/exclude filter logic.
- **Docker Setup**: Updated the `Makefile` to use a test image (`scraper:test`) and added commands for stopping and removing the Docker container.
- **Dependency Management**: Added the `notion-client` dependency in `pyproject.toml` to support the new Notion integration.
- **Code Cleanup**: Removed redundant methods and streamlined the scraping process across various job scrapers.

---

This refactor not only resolves the issues with duplicate detection and inefficient querying but also improves the overall maintainability and speed of the job scraping process.

## [1.7.1] - 2025-03-11
- Merged PR #17 by @MarcChen: fix : Welcome to the Jungle Issue
This pull request includes several improvements and bug fixes to the `load_all_offers` and `extract_element` functions in the `src/job_scrapers/welcome_to_the_jungle.py` file. The changes aim to enhance error handling and make the code more robust by using more reliable selectors.

Error handling improvements:

* Added `try-except` blocks to handle `NoSuchElementException` for finding job links and job titles in the `load_all_offers` method. This ensures that the script continues running even if some elements are not found.

Robustness improvements:

* Changed the selector for the pagination navigation element to use the `aria-label` attribute instead of class names, making it more robust to changes in the HTML structure.
* Updated the `extract_element` function to use more specific and reliable XPath selectors for extracting job metadata such as title, location, salary, experience level, contract type, and company. This improves the accuracy of data extraction. [[1]](diffhunk://#diff-dc19ee754afa8db50121eb04ed34a9287b7c872332c116bacd113d661596affdL235-R277) [[2]](diffhunk://#diff-dc19ee754afa8db50121eb04ed34a9287b7c872332c116bacd113d661596affdL261-R298)

