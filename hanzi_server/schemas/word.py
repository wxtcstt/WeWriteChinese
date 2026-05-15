from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional

# ---------- 字库 Schemas ----------
class WordBase(BaseModel):
    character: str
    pinyin: str
    grade: Optional[int] = 5
    unit: Optional[int] = 1
    tts_hint: Optional[str] = None
    common_words: Optional[str] = None
    image_path: Optional[str] = None

class WordCreate(WordBase):
    pass # 创建字库时不需要传 ID

class WordResponse(WordBase):
    id: int
    
    # 告诉 Pydantic 可以从 SQLAlchemy 模型中读取数据
    model_config = ConfigDict(from_attributes=True)


# ---------- 学习记录 Schemas ----------
class UserWordResponse(BaseModel):
    id: int
    word_id: int
    correct_streak: int
    error_count: int
    weight: float
    next_review_time: datetime
    
    # 嵌套一个字库信息，方便前端展示
    word: WordResponse 

    model_config = ConfigDict(from_attributes=True)