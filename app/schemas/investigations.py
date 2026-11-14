from pydantic import BaseModel, Field


class InvestigationSummary(BaseModel):
    id: str = Field(description="e.g. PSI-25")
    name: str = Field(description="Short name, e.g. BASS-II")
    title: str | None
    fuel_type: str | None = Field(description="solid | droplet | gas | smoke | ground")
    hardware_group: str | None
    safety_jobs: list[str] | None = Field(description="prevention / detection / suppression")
    in_space: bool | None
    psi_label: str | None = Field(description="NASA PSI category label")
    summary: str | None = Field(description="Plain-language summary (its sources are on the full card)")
    origin: str = Field(description="psi = NASA PSI; upload = a user report approved by the user")
    tests: int | None = Field(description="Number of fires (tests) in the cleaned tables")
    tests_with_results: int | None
    lunar_air_tests: int | None = Field(description="Tests with O2 >= 30% at <= 70.3 kPa (chamber air)")
    findings: int = Field(description="Number of sourced findings on the card")
