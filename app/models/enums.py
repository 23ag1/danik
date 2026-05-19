import enum


class Severity(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"


class IncidentStatus(str, enum.Enum):
    new = "new"
    investigating = "investigating"
    confirmed = "confirmed"
    rejected = "rejected"
