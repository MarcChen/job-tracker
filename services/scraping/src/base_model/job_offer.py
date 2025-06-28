"""
Pydantic models for job offers with validation and serialization.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class JobSource(str, Enum):
    """Enumeration of job sources."""

    BUSINESS_FRANCE = "Business France"
    AIR_FRANCE = "Air France"
    APPLE = "Apple"
    WELCOME_TO_THE_JUNGLE = "Welcome to the Jungle"


class JobURL(str, Enum):
    """Enumeration of job source URLs."""

    BUSINESS_FRANCE = (
        "https://mon-vie-via.businessfrance.fr/offres/recherche?query=Data"
    )
    AIR_FRANCE = "https://recrutement.airfrance.com/offre-de-emploi/liste-offres.aspx"
    # APPLE = "https://jobs.apple.com/fr-fr/search?sort=relevance&location=france-FRAC+singapore-SGP+hong-kong-HKGC+taiwan-TWN"
    APPLE = "https://jobs.apple.com/fr-fr/search?sort=relevance&location=france-FRAC"
    WELCOME_TO_THE_JUNGLE = "https://www.welcometothejungle.com/fr/jobs?&refinementList%5Bcontract_type%5D%5B%5D=full_time&refinementList%5Bcontract_type%5D%5B%5D=temporary&refinementList%5Bcontract_type%5D%5B%5D=freelance"


class ContractType(str, Enum):
    """Enumeration of contract types."""

    CDI = "CDI"
    CDD = "CDD"
    INTERNSHIP = "Stage"
    FREELANCE = "Freelance"
    TEMPORARY = "Temporary"
    FULL_TIME = "Full-time"
    PART_TIME = "Part-time"
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
        """Validate URL format."""
        if not v.startswith(("http://", "https://")):
            raise ValueError("URL must start with http:// or https://")
        return v

    @field_validator("title", "company", "location")
    @classmethod
    def validate_not_na(cls, v: str) -> str:
        """Ensure required fields are not 'N/A'."""
        if v.upper() == "N/A":
            raise ValueError('Field cannot be "N/A"')
        return v

    def to_notion_format(self) -> Dict[str, Any]:
        """
        Convert the job offer to Notion page properties format.

        Returns:
            Dict containing Notion-compatible page properties
        """
        return {
            "Title": {"title": [{"text": {"content": self.title}}]},
            "Company": {"select": {"name": self.company}},
            "Location": {"select": {"name": self.location}},
            "Source": {"select": {"name": self.source.value}},
            "URL": {"url": self.url},
            "Contract Type": {
                "select": {
                    "name": self.contract_type.value if self.contract_type else "N/A"
                }
            },
            "Salary": {"rich_text": [{"text": {"content": self.salary or "N/A"}}]},
            "Duration": {"rich_text": [{"text": {"content": self.duration or "N/A"}}]},
            "Reference": {
                "rich_text": [{"text": {"content": self.reference or "N/A"}}]
            },
            "Schedule Type": {"select": {"name": self.schedule_type or "N/A"}},
            "Job Content Description": {
                "rich_text": [
                    {
                        "text": {
                            "content": (self.job_content_description or "N/A")[
                                :2000
                            ]  # Notion has a limit
                        }
                    }
                ]
            },
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
            "Source": self.source.value,
            "URL": self.url,
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
