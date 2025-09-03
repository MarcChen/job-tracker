import random
import urllib.parse
from typing import List, Optional

from pydantic import BaseModel, Field, model_validator


class LinkedinUrlGenerate(BaseModel):
    keyword: str
    location: str
    url: str = "https://www.linkedin.com/jobs/search"
    job_types: Optional[List[str]] = Field(default_factory=lambda: ["Full-time"])
    remote_types: Optional[List[str]] = Field(
        default_factory=lambda: ["On-site", "Hybrid"]
    )
    experience_levels: Optional[List[str]] = None
    date_posted: Optional[List[str]] = Field(default_factory=lambda: ["Any Time"])
    salary: Optional[List[str]] = None
    sort: Optional[List[str]] = Field(default_factory=lambda: ["Recent"])

    @model_validator(mode="before")
    @classmethod
    def require_fields(cls, values):
        if not values.get("keyword") or not values.get("location"):
            raise ValueError("keyword, location, and url are required")
        return values

    def generate_url_link(self) -> str:
        """Generate a single LinkedIn job search URL with applied filters."""
        # URL encode keyword and location for safety
        encoded_keyword = urllib.parse.quote_plus(self.keyword)
        encoded_location = urllib.parse.quote_plus(self.location)

        link = (
            self.url
            + f"?keywords={encoded_keyword}"
            + self._build_job_type_filter()
            + self._build_remote_filter()
            + self._build_location_filter(encoded_location)
            + self._build_experience_filter()
            + self._build_date_posted_filter()
            + self._build_salary_filter()
            + self._build_sort_filter()
        )
        return link

    def _build_location_filter(self, location: str) -> str:
        """Build location filter with geo ID mapping."""
        job_loc = f"&location={location}"

        location_mapping = {
            "asia": "&geoId=102393603",
            "europe": "&geoId=100506914",
            "northamerica": "&geoId=102221843",
            "southamerica": "&geoId=104514572",
            "australia": "&geoId=101452733",
            "africa": "&geoId=103537801",
        }

        geo_id = location_mapping.get(self.location.casefold(), "")
        return job_loc + geo_id

    def _build_experience_filter(self) -> str:
        """Build experience level filter."""
        if not self.experience_levels:
            return ""

        experience_mapping = {
            "Internship": "1",
            "Entry level": "2",
            "Associate": "3",
            "Mid-Senior level": "4",
            "Director": "5",
            "Executive": "6",
        }

        experience_codes = []
        for level in self.experience_levels:
            code = experience_mapping.get(level)
            if code:
                experience_codes.append(code)

        if not experience_codes:
            return ""

        first_code = experience_codes[0]
        result = f"&f_E={first_code}"

        for code in experience_codes[1:]:
            result += f"%2C{code}"

        return result

    def _build_date_posted_filter(self) -> str:
        """Build date posted filter."""
        if not self.date_posted:
            return ""

        date_mapping = {
            "Any Time": "",
            "Past Month": "&f_TPR=r2592000",
            "Past Week": "&f_TPR=r604800",
            "Past 24 hours": "&f_TPR=r86400",
        }

        return date_mapping.get(self.date_posted[0], "")

    def _build_job_type_filter(self) -> str:
        """Build job type filter."""
        if not self.job_types:
            return ""

        job_type_mapping = {
            "Full-time": "F",
            "Part-time": "P",
            "Contract": "C",
            "Temporary": "T",
            "Volunteer": "V",
            "Internship": "I",
            "Other": "O",
        }

        job_type_codes = []
        for job_type in self.job_types:
            code = job_type_mapping.get(job_type)
            if code:
                job_type_codes.append(code)

        if not job_type_codes:
            return ""

        first_code = job_type_codes[0]
        result = f"&f_JT={first_code}"

        for code in job_type_codes[1:]:
            result += f"%2C{code}"

        return result + "&"

    def _build_remote_filter(self) -> str:
        """Build remote work filter."""
        if not self.remote_types:
            return ""

        remote_mapping = {"On-site": "1", "Remote": "2", "Hybrid": "3"}

        remote_codes = []
        for remote_type in self.remote_types:
            code = remote_mapping.get(remote_type)
            if code:
                remote_codes.append(code)

        if not remote_codes:
            return ""

        first_code = remote_codes[0]
        result = f"&f_WT={first_code}"

        for code in remote_codes[1:]:
            result += f"%2C{code}"

        return result

    def _build_salary_filter(self) -> str:
        """Build salary filter."""
        if not self.salary:
            return ""

        salary_mapping = {
            "$40,000+": "f_SB2=1&",
            "$60,000+": "f_SB2=2&",
            "$80,000+": "f_SB2=3&",
            "$100,000+": "f_SB2=4&",
            "$120,000+": "f_SB2=5&",
            "$140,000+": "f_SB2=6&",
            "$160,000+": "f_SB2=7&",
            "$180,000+": "f_SB2=8&",
            "$200,000+": "f_SB2=9&",
        }

        return salary_mapping.get(self.salary[0], "")

    def _build_sort_filter(self) -> str:
        """Build sort filter."""
        if not self.sort:
            return ""

        sort_mapping = {"Recent": "sortBy=DD", "Relevant": "sortBy=R"}

        return sort_mapping.get(self.sort[0], "")


if __name__ == "__main__":
    job_filter = LinkedinUrlGenerate(
        keyword="data engineer",
        location="Paris",
        salary=["$100,000+"],
        job_types=["Full-time", "Contract"],
        remote_types=["Remote", "Hybrid"],
        experience_levels=["Mid-Senior level", "Director"],
        date_posted=["Past Week"],
        sort=["Recent"],
    )

    minimal_generator = LinkedinUrlGenerate(
        keyword="ingénieur de données",
        location="Paris et périphérie",
        salary=None,
        job_types=None,
    )

    print("Full filter URLs:")
    full_links = job_filter.generate_url_link()
    print(full_links)

    print("\nMinimal filter URLs:")
    minimal_links = minimal_generator.generate_url_link()
    print(minimal_links)
