from pydantic import BaseModel, ConfigDict


class NoteBase(BaseModel):
    title: str
    content: str | None = None


class NoteCreate(NoteBase):
    author_id: int


class Note(NoteBase):
    id: int
    author_id: int

    model_config = ConfigDict(from_attributes=True)


class User(BaseModel):
    id: int
    username: str
    email: str

    model_config = ConfigDict(from_attributes=True)
