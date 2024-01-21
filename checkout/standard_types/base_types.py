import pydantic


class Aggregate(pydantic.BaseModel):
    ...


class ValueObjet(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(frozen=True)
