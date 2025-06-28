# job-tracker

A project in construction for tracking job offers and various activities, leveraging web scraping and integration with Notion for seamless data management.

<p align="center">
  <img src="./demo.gif" alt="Project Demo GIF" width="600">
</p>

## Overview

### What Does This Project Do?

**job-tracker** automates the process of tracking job offers on a specific platform and integrates the data into a Notion database. It uses Selenium for scraping and has a robust Python backend built on top of the Selenium standalone Docker image. Key features include:

1. **Automated Job Scraping:**
   - Dynamically loads and extracts job offers from the website.
   - Captures key details like job title, company, location, contract type, duration, number of views, and candidate count.
2. **Notion Integration:**
   - Syncs extracted job offers to a Notion database.
   - Skips duplicates and ensures seamless record management.
3. **Real-Time Alerts:**
   - Sends SMS notifications for new job offers using Free Mobile's API.


## Why Use This Project?

This project simplifies web scraping by providing:

1. **Complete Environment:**
   - The Dockerfile offers a fully configured environment, including Chromium, ready for scraping tasks. No manual setup required.
   - Optimized for scraping by using the Selenium standalone image as the base, which saves setup time and ensures stability.

2. **Custom Python Scripts:**
   - Scripts are pre-built to perform common scraping tasks out of the box, such as loading all offers dynamically and extracting structured data.
   - Modular and extensible design allows easy customization for other scraping tasks.


## How the Scraping Works

### Step 1: Load All Offers
The scraper dynamically loads job offers by interacting with the "Voir Plus d'Offres" button until all offers are visible on the page.

### Step 2: Extract Offers
The scraper gathers data for each job offer, including:
- **Title**: The job's title.
- **Company**: Name of the hiring company.
- **Location**: Job location.
- **Contract Type**: Type of contract (e.g., CDI, CDD).
- **Duration**: Duration of the position, if available.
- **Views**: Number of views the job listing has received.
- **Candidates**: Number of candidates who have applied.

### Step 3: Save Data
Extracted data is processed and:
- Stored in a Notion database.
- Sent as SMS notifications for new offers.



## Database Example
The database contains the following fields:
- **Title**: The job's title.
- **Company**: Name of the hiring company.
- **Location**: Job location.
- **Contract Type**: Type of contract (e.g., CDI, CDD).
- **Duration**: Duration of the position.
- **Views**: Number of views the job listing has received.
- **Candidates**: Number of candidates who have applied.

### Example Record:
| Title              | Company       | Location     | Contract Type | Duration  | Views | Candidates |
|--------------------|---------------|--------------|---------------|-----------|-------|------------|
| Software Engineer | TechCorp      | Paris, France| CDI           | 12 months | 1234  | 56         |


## How to Use

### Prerequisites
- Docker installed on your system.
- Python environment with necessary libraries if not using Docker.

### Setup

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/your-username/job-tracker.git
   cd job-tracker
   ```

2. **Build the Docker Image:**
   ```bash
   docker build -t job-tracker .
   ```

3. **Run the Application:**
   ```bash
   docker run --rm -it job-tracker
   ```

4. **Configure Environment Variables:**
   Set the following environment variables before running:
   - `DATABASE_ID`: Your Notion database ID.
   - `NOTION_API`: Your Notion API key.
   - `FREE_MOBILE_USER_ID`: Your Free Mobile user ID.
   - `FREE_MOBILE_API_KEY`: Your Free Mobile API key.



## Link to the Database
You can access the Notion database [here](https://kemar.notion.site/16919fda9f9d8098b983e48bbb2b6feb?v=107c3db306694b03b3f844efffeb6947&pvs=4).



## Contributing
Contributions are welcome! Please fork the repository and submit a pull request.
