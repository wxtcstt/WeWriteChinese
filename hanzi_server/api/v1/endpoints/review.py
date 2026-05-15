import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, Header
from sqlalchemy.orm import Session
from pydantic import BaseModel

from api.dependencies import get_db
from models.user_word import UserWord
from services.review_cache import memory_cache 

router = APIRouter()

class ReviewSubmit(BaseModel):
    word_id: int
    is_correct: bool

def get_current_user_id(x_user_id: str = Header(None, description="用户的唯一ID")):
    if not x_user_id:
        raise HTTPException(status_code=401, detail="未授权：请先登录")
    return x_user_id

@router.get("/next_word")
def get_next_word(
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
    max_grade: int = Query(6, description="用户设置的最高学习年级")
):
    if not memory_cache.is_loaded:
        memory_cache.load_from_db(db)
        
    if not memory_cache.words:
        raise HTTPException(status_code=404, detail="字库为空")

    # 获取盲盒抽签结果
    next_word_data, learned_count, total_count, daily_count = memory_cache.get_next_word(
        user_id=user_id, 
        max_grade=max_grade
    )
    
    if not next_word_data:
        return {
            "status": "finished", 
            "message": "太棒了！今日听写通关啦！", # 文案变为今日通关
            "learned_count": learned_count,
            "total_count": total_count,
            "daily_count": daily_count  # 顺便返回今天已写字数，前端备用
        }

    return {
        "status": "success",
        "word": next_word_data,
        "learned_count": learned_count,
        "total_count": total_count,
        "daily_count": daily_count  # 顺便返回今天已写字数，前端备用
    }

@router.post("/submit")
def submit_review(
    data: ReviewSubmit, 
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    record = db.query(UserWord).filter(
        UserWord.word_id == data.word_id,
        UserWord.user_id == user_id
    ).first()
    
    today = datetime.date.today()
    is_temp_pool = False
    
    # 新字初始化
    if not record:
        record = UserWord(
            user_id=user_id, 
            word_id=data.word_id, 
            level=0, 
            next_review_date=today,
            error_count=0
        )
        db.add(record)

    # ================= ⭐️ SRS 记忆引擎核心逻辑 =================
    
    # 判断：如果是今天已经复习过的字，说明它必然是处于“临时错题池”的复习
    if record.last_review_date == today:
        is_temp_pool = True
        if not data.is_correct:
            record.error_count += 1
            # 如果错题重做又错了，依然在池子里，级别不动
    else:
        # 这是常规池的新一天复习
        record.last_review_date = today # 标记为今天已复习
        
        if data.is_correct:
            # ✅ 写对：打怪升级
            record.level += 1
            # 艾宾浩斯间隔：1天, 2天, 4天, 999天(彻底掌握)
            intervals = {1: 1, 2: 2, 3: 4, 4: 999} 
            days_to_add = intervals.get(record.level, 999)
            record.next_review_date = today + datetime.timedelta(days=days_to_add)
        else:
            # ❌ 写错：打回原形，明天重新开始
            record.level = 0
            record.next_review_date = today + datetime.timedelta(days=1)
            record.error_count += 1

    # =========================================================

    db.commit()
    db.refresh(record)
    
    # ⭐️ 同步给内存缓存
    memory_cache.update_user_record(
        user_id=user_id,
        word_id=data.word_id,
        level=record.level,
        next_date=record.next_review_date,
        last_date=record.last_review_date,
        is_correct=data.is_correct,
        is_temp_pool=is_temp_pool
    )
    
    return {
        "message": "反馈记录成功", 
        "word_id": data.word_id,
        "new_level": record.level
    }