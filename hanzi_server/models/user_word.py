from sqlalchemy import Column, Integer, ForeignKey,String, Index,Date
from sqlalchemy.orm import relationship
import datetime
from db.base import Base

class UserWord(Base):
    __tablename__ = "user_words"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(64), index=True, nullable=False) 
    word_id = Column(Integer, ForeignKey("words.id"), nullable=False)
    
    # ================= ⭐️ 艾宾浩斯记忆引擎核心字段 =================
    
    # 掌握层级：0=初学/写错打回，1=隔1天，2=隔2天，3=隔4天，4=彻底掌握
    level = Column(Integer, default=0) 
    
    # 下次该复习的日期 (默认是今天，意味着没写过的字随时可以被抽到)
    next_review_date = Column(Date, default=datetime.date.today)
    
    # 最后一次复习的日期 (用来拦截“今天刚写过/错过的字不能马上在常规池里出”)
    last_review_date = Column(Date, nullable=True)

    # 统计辅助：只保留错误次数，以后可以用来给家长展示“孩子的易错字榜单”
    error_count = Column(Integer, default=0)

    # ================= 🚀 数据库性能外挂 (联合索引) =================
    __table_args__ = (
        # 极速查询某个用户某个字的记录
        Index('ix_user_word_user_id_word_id', 'user_id', 'word_id'),
        # ⭐️ 新增：极速查询某个用户今天该背哪些字
        Index('ix_user_word_user_next_date', 'user_id', 'next_review_date'),
    )