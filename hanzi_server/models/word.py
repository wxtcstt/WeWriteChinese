from sqlalchemy import Column, Integer, String
from db.base import Base

class Word(Base):
    __tablename__ = "words"

    id = Column(Integer, primary_key=True, index=True)
    character = Column(String(10), unique=True, index=True, nullable=False)
    pinyin = Column(String(50), nullable=False)
    grade = Column(Integer, default=5)
    unit = Column(Integer, default=1)
    
    # --- 新增的三个字段 ---
    tts_hint = Column(String(50))      # 语音提示，例如："专心的专"
    common_words = Column(String(100)) # 常用词语，例如："专心,专家,专业" (用逗号分隔)
    image_path = Column(String(255))   # 图片路径，例如："/static/images/words/专.png"
    