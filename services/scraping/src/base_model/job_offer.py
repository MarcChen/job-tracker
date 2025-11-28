"""
Pydantic models for job offers with validation and serialization.
"""

import hashlib
from datetime import datetime
from enum import Enum, auto
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


def generate_job_offer_id(company: str, title: str, url: Optional[str] = None) -> str:
    """
    Generate a unique 5-digit ID for a job offer based on company, title, and URL.

    Args:
        company: Company name
        title: Job title
        url: Job posting URL (optional, defaults to empty string if None)

    Returns:
        5-digit string ID
    """
    # Normalize inputs by stripping whitespace and converting to lowercase
    normalized_company = company.strip().lower()
    normalized_title = title.strip().lower()
    normalized_url = (url or "").strip().lower()

    # Create a combined string for hashing
    combined_string = f"{normalized_company}|{normalized_title}|{normalized_url}"

    # Generate SHA256 hash
    hash_object = hashlib.sha256(combined_string.encode("utf-8"))
    hash_hex = hash_object.hexdigest()

    # Convert first 20 bits (5 hex chars) to integer and then to 5-digit string
    # This ensures we get exactly 5 digits with leading zeros if necessary
    hash_int = int(hash_hex[:5], 16)
    offer_id = f"{hash_int % 100000:05d}"

    return offer_id


def pre_process_url(url: str) -> str:
    if "?" in url:
        url = url.split("?")[0]
    return url


class JobSource(str, Enum):
    """Enumeration of job sources."""

    BUSINESS_FRANCE = auto()
    AIR_FRANCE = auto()
    APPLE = auto()
    WELCOME_TO_THE_JUNGLE = auto()
    LINKEDIN = auto()
    UNKNOWN = auto()


class JobURL(str, Enum):
    """Enumeration of job source URLs."""

    BUSINESS_FRANCE = (
        "https://mon-vie-via.businessfrance.fr/offres/recherche?query=Data"
    )
    AIR_FRANCE = "https://recrutement.airfrance.com/offre-de-emploi/liste-offres.aspx"
    # APPLE = "https://jobs.apple.com/fr-fr/search?sort=relevance&location=france-FRAC+singapore-SGP+hong-kong-HKGC+taiwan-TWN"
    APPLE = "https://jobs.apple.com/fr-fr/search?sort=relevance&location=france-FRAC"
    WELCOME_TO_THE_JUNGLE = "https://www.welcometothejungle.com/fr/jobs?&refinementList%5Bcontract_type%5D%5B%5D=full_time&refinementList%5Bcontract_type%5D%5B%5D=temporary&refinementList%5Bcontract_type%5D%5B%5D=freelance"
    LINKEDIN = "https://www.linkedin.com/jobs/"


class ContractType(str, Enum):
    """Enumeration of contract types."""

    CDI = "CDI"
    CDD = "CDD"
    INTERNSHIP = "Stage"
    FREELANCE = "Freelance"
    TEMPORARY = "Temporary"
    FULL_TIME = "Full time"
    PART_TIME = "Part time"
    VIE = "VIE"
    OTHER = "Other"


class JobOffer(BaseModel):
    """
    Pydantic model for job offers with comprehensive validation.

    This model defines the structure and validation rules for job offers
    scraped from various job portals.
    """

    model_config = ConfigDict(
        str_strip_whitespace=True,  # Automatically strip whitespace from strings
        validate_assignment=True,  # Validate on assignment
        use_enum_values=True,  # Use enum values in serialization
        extra="ignore",  # Ignore extra fields during validation
    )

    # Core required fields
    title: str = Field(..., min_length=1, max_length=500, description="Job title")

    company: str = Field(..., min_length=1, max_length=200, description="Company name")

    location: str = Field(..., min_length=1, max_length=200, description="Job location")

    source: JobSource = Field(
        ..., description="Source platform where the job was found"
    )

    url: str = Field(..., description="URL to the job posting")

    scraped_at: datetime = Field(
        default_factory=datetime.now, description="Timestamp when the job was scraped"
    )

    # Auto-generated ID field
    offer_id: str = Field(
        default="", max_length=5, description="Auto-generated 5-digit unique identifier"
    )

    # Optional fields
    contract_type: Optional[ContractType] = Field(
        default=None, description="Type of employment contract"
    )

    salary: Optional[str] = Field(
        default=None, max_length=100, description="Salary information"
    )

    duration: Optional[str] = Field(
        default=None, max_length=100, description="Contract duration"
    )

    reference: Optional[str] = Field(
        default=None, max_length=100, description="Job reference number"
    )

    schedule_type: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Schedule type (full-time, part-time, etc.)",
    )

    job_content_description: Optional[str] = Field(
        default=None, description="Job content description"
    )

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Validate URL format and clean query parameters."""
        if not v.startswith(("http://", "https://")):
            raise ValueError("URL must start with http:// or https://")

        # Remove query parameters (everything after ?) to ensure consistent ID generation
        return pre_process_url(v)

    @field_validator("title", "company", "location")
    @classmethod
    def validate_not_na(cls, v: str) -> str:
        """Ensure required fields are not 'N/A'."""
        if v.upper() == "N/A":
            raise ValueError('Field cannot be "N/A"')
        return v

    @field_validator(
        "company",
        "location",
        "source",
        "contract_type",
        "salary",
        "duration",
        "reference",
        "schedule_type",
    )
    @classmethod
    def clean_notion_select_fields(cls, v: Optional[str]) -> Optional[str]:
        """Remove problematic characters (-,.) from fields used with notion_select."""
        if v is None:
            return v
        # Remove hyphens, commas, and periods
        cleaned = v.replace("-", " ").replace(",", " ").replace(".", " ")
        # Replace multiple spaces with single space and strip
        cleaned = " ".join(cleaned.split())
        return cleaned

    @field_validator("company", "location", "salary", "reference")
    @classmethod
    def normalize_fields(cls, v: str) -> str:
        """Normalize company and location: strip, lowercase, collapse spaces."""
        if v is None:
            return v
        return " ".join(v.strip().lower().split())

    @model_validator(mode="after")
    def generate_offer_id(self) -> "JobOffer":
        """Auto-generate offer_id if not provided and validate it's 5 digits."""
        if not self.offer_id:
            self.offer_id = generate_job_offer_id(self.company, self.title, self.url)

        # Validate the offer_id is exactly 5 digits
        if len(self.offer_id) != 5 or not self.offer_id.isdigit():
            raise ValueError("offer_id must be exactly 5 digits")

        return self

    def regenerate_id(self) -> str:
        """
        Regenerate the offer ID based on current company, title, and URL.

        Returns:
            The newly generated 5-digit ID
        """
        new_id = generate_job_offer_id(self.company, self.title, self.url)
        self.offer_id = new_id
        return new_id

    def to_notion_format(self) -> Dict[str, Any]:
        """
        Convert the job offer to Notion page properties format.

        Returns:
            Dict containing Notion-compatible page properties
        """

        # Helper to map a value to a Notion select option (by name)
        def notion_select(name):
            return {"select": {"name": name if name else "N/A"}}

        # Helper to map a value to a Notion rich_text property
        def notion_rich_text(content):
            return {
                "rich_text": [
                    {"text": {"content": content[:2000] if content else "N/A"}}
                ]
            }

        # Truncate Job Content Description to 1950 chars to avoid Notion API limit
        job_content = self.job_content_description or ""
        if len(job_content) > 1950:
            job_content = job_content[:1950] + "..."

        return {
            "Title": {"title": [{"text": {"content": self.title}}]},
            "Company": notion_select(self.company),
            "Location": notion_select(self.location),
            "Source": notion_select(self.source),
            "URL": {"url": self.url},
            "Offer ID": notion_rich_text(self.offer_id),
            "Contract Type": notion_select(
                self.contract_type if self.contract_type else "N/A"
            ),
            "Salary": notion_select(self.salary if self.salary else "Non spécifié"),
            "Duration": notion_select(self.duration if self.duration else "N/A"),
            "Reference": notion_select(self.reference if self.reference else "N/A"),
            "Schedule Type": notion_select(
                self.schedule_type if self.schedule_type else "N/A"
            ),
            "Job Content Description": notion_rich_text(job_content),
        }

    def to_legacy_dict(self) -> Dict[str, Any]:
        """
        Convert to legacy dictionary format for backward compatibility.

        Returns:
            Dict in the old format used by the existing codebase
        """
        return {
            "Title": self.title,
            "Company": self.company,
            "Location": self.location,
            "Source": self.source,
            "URL": self.url,
            "Offer ID": self.offer_id,
            "Contract Type": self.contract_type.value if self.contract_type else "N/A",
            "Salary": self.salary or "N/A",
            "Duration": self.duration or "N/A",
            "Reference": self.reference or "N/A",
            "Schedule Type": self.schedule_type or "N/A",
            "Job Content Description": self.job_content_description or "N/A",
        }


class JobOfferInput(BaseModel):
    """
    Input model for creating job offers from scraped data.
    This model is more lenient and handles conversion from raw scraped data.
    """

    model_config = ConfigDict(str_strip_whitespace=True, extra="ignore")

    title: str
    company: str
    location: str
    source: JobSource
    url: str
    scraped_at: datetime
    contract_type: Optional[ContractType] = None
    salary: Optional[str] = None
    duration: Optional[str] = None
    reference: Optional[str] = None
    schedule_type: Optional[str] = None
    job_content_description: Optional[str] = None
    offer_id: Optional[str] = (
        None  # Optional since it will be auto-generated if not provided
    )

    # TODO : Implement property to automatically generate ID after model instanciation

    @field_validator("source")
    @classmethod
    def normalize_source(cls, v: str) -> str:
        """Normalize source names to match enum values."""
        source_mapping = {
            "business france": JobSource.BUSINESS_FRANCE,
            "air france": JobSource.AIR_FRANCE,
            "apple": JobSource.APPLE,
            "welcome to the jungle": JobSource.WELCOME_TO_THE_JUNGLE,
        }
        return source_mapping.get(v.lower(), v)

    def determine_contract_type(self) -> Optional[ContractType]:  # noqa: C901
        """
        Determine contract type from raw contract_type string.

        Returns:
            ContractType enum value or None if contract_type is None or "N/A"
        """
        if not self.contract_type or self.contract_type == "N/A":
            return None

        try:
            # First, try direct enum value match
            return ContractType(self.contract_type)
        except ValueError:
            # Try to match common contract type patterns
            ct_lower = self.contract_type.lower()
            if "cdi" in ct_lower or "permanent" in ct_lower:
                return ContractType.CDI
            elif "cdd" in ct_lower or "temporary" in ct_lower:
                return ContractType.CDD
            elif "stage" in ct_lower or "intern" in ct_lower:
                return ContractType.INTERNSHIP
            elif "freelance" in ct_lower:
                return ContractType.FREELANCE
            elif "full" in ct_lower:
                return ContractType.FULL_TIME
            elif "part" in ct_lower:
                return ContractType.PART_TIME
            elif "vie" in ct_lower:
                return ContractType.VIE
            else:
                return ContractType.OTHER

    def to_job_offer(self) -> JobOffer:
        """Convert input model to validated JobOffer."""
        contract_type = self.determine_contract_type()

        return JobOffer(
            title=self.title,
            company=self.company,
            location=self.location,
            source=JobSource(self.source),
            url=self.url,
            scraped_at=self.scraped_at,
            offer_id=self.offer_id or "",  # Will be auto-generated if empty
            contract_type=contract_type,
            salary=self.salary if self.salary != "N/A" else None,
            duration=self.duration if self.duration != "N/A" else None,
            reference=self.reference if self.reference != "N/A" else None,
            schedule_type=self.schedule_type if self.schedule_type != "N/A" else None,
            job_content_description=(
                self.job_content_description
                if self.job_content_description != "N/A"
                else None
            ),
        )
