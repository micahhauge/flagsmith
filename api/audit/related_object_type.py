import enum


class RelatedObjectType(enum.Enum):
    FEATURE = "Feature"
    FEATURE_STATE = "Feature state"
    SEGMENT = "Segment"
    SEGMENT_CONDITION = "Segment condition"
    ENVIRONMENT = "Environment"
    CHANGE_REQUEST = "Change request"
