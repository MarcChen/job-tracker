# JobOffer Model Documentation

## Overview

The JobOffer model system provides a clean, validated way to handle job offer data in the VIE-Tracker application. Built with Pydantic, it ensures data consistency and provides seamless integration with Notion and other external systems.

## Key Features

- **Type Safety**: Strong typing with Pydantic validation
- **Data Cleaning**: Automatic whitespace stripping and "N/A" handling
- **Flexible Input**: Handles messy scraped data through the `JobOfferInput` model
- **Multiple Outputs**: Converts to Notion format and legacy dictionary format
- **Enum Validation**: Ensures consistent source and contract type values

## Model Architecture

### JobSource Enum

Defines the supported job posting sources:

```python
class JobSource(str, Enum):
    BUSINESS_FRANCE = "Business France"
    AIR_FRANCE = "Air France"
    APPLE = "Apple"
    WELCOME_TO_THE_JUNGLE = "Welcome to the Jungle"
```

### ContractType Enum

Defines the supported employment contract types:

```python
class ContractType(str, Enum):
    CDI = "CDI"
    CDD = "CDD"
    INTERNSHIP = "Stage"
    FREELANCE = "Freelance"
    TEMPORARY = "Temporary"
    FULL_TIME = "Full-time"
    PART_TIME = "Part-time"
    VIE = "VIE"
    OTHER = "Other"
```

## Core Models

### JobOffer (Main Model)

The primary validated model for job offers with the following schema:

| Field | Type | Required | Validation | Description |
|-------|------|----------|------------|-------------|
| `title` | `str` | ✅ | 1-500 chars, not "N/A" | Job title |
| `company` | `str` | ✅ | 1-200 chars, not "N/A" | Company name |
| `location` | `str` | ✅ | 1-200 chars, not "N/A" | Job location |
| `source` | `JobSource` | ✅ | Must be valid enum | Source platform |
| `url` | `str` | ✅ | Must start with http/https | Job posting URL |
| `scraped_at` | `datetime` | ✅ | Auto-generated | Scraping timestamp |
| `contract_type` | `ContractType?` | ❌ | Must be valid enum if provided | Employment contract type |
| `salary` | `str?` | ❌ | Max 100 chars | Salary information |
| `duration` | `str?` | ❌ | Max 100 chars | Contract duration |
| `reference` | `str?` | ❌ | Max 100 chars | Job reference number |
| `schedule_type` | `str?` | ❌ | Max 100 chars | Schedule type |
| `job_content_description` | `str?` | ❌ | No limit | Job description |

### JobOfferInput (Input Model)

A more lenient model for processing raw scraped data. Has the same fields as `JobOffer` but with more flexible validation and automatic data normalization.

## Usage Examples

### Creating a Validated Job Offer

```python
from datetime import datetime
from job_offer import JobOffer, JobSource, ContractType

# Create a job offer directly
job = JobOffer(
    title="Senior Developer",
    company="TechCorp",
    location="Paris, France",
    source=JobSource.BUSINESS_FRANCE,
    url="https://example.com/job/123",
    contract_type=ContractType.CDI,
    salary="50k-60k EUR",
    duration="Permanent"
)

print(job.title)  # "Senior Developer"
print(job.scraped_at)  # Current timestamp
```

### Processing Raw Scraped Data

```python
from job_offer import JobOfferInput, JobSource

# Raw data from scraper (with messy values)
raw_data = {
    "title": "  Software Engineer  ",
    "company": "Apple Inc.",
    "location": "Cupertino",
    "source": "apple",  # Will be normalized
    "url": "https://jobs.apple.com/123",
    "scraped_at": datetime.now(),
    "contract_type": "full-time",  # Will be converted to ContractType.FULL_TIME
    "salary": "N/A",  # Will be converted to None
    "job_content_description": "Great opportunity..."
}

# Process through input model
input_job = JobOfferInput(**raw_data)
validated_job = input_job.to_job_offer()

print(validated_job.title)  # "Software Engineer" (whitespace stripped)
print(validated_job.salary)  # None (converted from "N/A")
```

### Converting to Different Formats

```python
# Convert to Notion format
notion_data = job.to_notion_format()
print(notion_data["Title"]["title"][0]["text"]["content"])  # "Senior Developer"

# Convert to legacy dictionary format
legacy_data = job.to_legacy_dict()
print(legacy_data["Title"])  # "Senior Developer"
```

## Validation Rules

### Automatic Validations

- **Whitespace Stripping**: All string fields automatically strip leading/trailing whitespace
- **URL Validation**: URLs must start with `http://` or `https://`
- **"N/A" Rejection**: Required fields (`title`, `company`, `location`) cannot be "N/A"
- **Length Limits**: String fields have maximum length constraints
- **Enum Validation**: Source and contract type must be valid enum values

### Data Normalization

The `JobOfferInput` model automatically normalizes data:

- **Source Names**: Maps common source name variations to enum values
- **Contract Types**: Intelligently matches contract type strings to enum values
- **"N/A" Handling**: Converts "N/A" strings to `None` for optional fields

## Integration

### Notion API

The `to_notion_format()` method converts job offers to Notion page properties format:

```python
notion_properties = job.to_notion_format()
# Ready to use with Notion API
```

### Legacy Systems

The `to_legacy_dict()` method provides backward compatibility:

```python
legacy_format = job.to_legacy_dict()
# Compatible with existing dictionary-based code
```

## Error Handling

Common validation errors and their causes:

```python
# ValidationError: URL must start with http:// or https://
JobOffer(url="invalid-url", ...)

# ValidationError: Field cannot be "N/A"
JobOffer(title="N/A", ...)

# ValidationError: String too long
JobOffer(title="x" * 501, ...)

# ValueError: Invalid enum value
JobOffer(source="unknown-source", ...)
```

## Best Practices

1. **Use JobOfferInput for scraped data**: Always process raw scraped data through `JobOfferInput` first
2. **Handle validation errors**: Wrap model creation in try-except blocks
3. **Leverage automatic timestamps**: The `scraped_at` field is automatically set to current time
4. **Validate early**: Create `JobOffer` instances as soon as possible to catch validation errors
5. **Use enum values**: Always use the enum classes rather than raw strings for `source` and `contract_type`

## Configuration

The model uses the following Pydantic configuration:

- `str_strip_whitespace=True`: Automatic whitespace stripping
- `validate_assignment=True`: Validation on field assignment
- `use_enum_values=True`: Use enum values in serialization
- `extra='ignore'`: Ignore extra fields during validation

This ensures clean, consistent data throughout the application.
