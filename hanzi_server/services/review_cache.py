import random
import datetime
from sqlalchemy.orm import Session
from models.word import Word
from models.user_word import UserWord

DAILY_LIMIT = 50  # ⭐️ 设定每天只考 50 个常规字

class ReviewCache:
    def __init__(self):
        self.words = {}
        self.user_records = {} 
        # ⭐️ 新增：用户当天的 Session 状态，纯内存管理，速度极快
        self.user_sessions = {} # 格式: { user_id: { "date": date, "regular_count": int, "wrong_pool": { word_id: cooldown } } }
        self.is_loaded = False

    def load_from_db(self, db: Session):
        print("⚡️ 正在加载艾宾浩斯记忆引擎...")
        self.words.clear()
        words_db = db.query(Word).all()
        for w in words_db:
            self.words[w.id] = {
                "id": w.id, "character": w.character, "pinyin": w.pinyin,
                "tts_hint": w.tts_hint, "common_words": w.common_words,
                "image_path": w.image_path, "grade": w.grade
            }

        self.user_records.clear()
        records_db = db.query(UserWord).all()
        for r in records_db:
            if r.user_id not in self.user_records:
                self.user_records[r.user_id] = {}
            self.user_records[r.user_id][r.word_id] = {
                "level": r.level,
                "next_review_date": r.next_review_date,
                "last_review_date": r.last_review_date
            }
        self.is_loaded = True

    def _get_or_create_session(self, user_id: str, today: datetime.date):
        """管理每日进度与错题池"""
        if user_id not in self.user_sessions or self.user_sessions[user_id]["date"] != today:
            self.user_sessions[user_id] = {
                "date": today,
                "regular_count": 0,    # 今天抽了多少个常规题
                "wrong_pool": {}       # 临时错题池 {word_id: 冷却倒数}
            }
        return self.user_sessions[user_id]

    def get_next_word(self, user_id: str, max_grade: int = 6):
        today = datetime.date.today()
        session = self._get_or_create_session(user_id, today)
        user_data = self.user_records.get(user_id, {})

        regular_candidates = []
        ready_wrong_candidates = []
        
        learned_count = 0
        total_count = 0

        # 1. 扫描字库，分配卡牌
        for word_id, word_data in self.words.items():
            if word_data["grade"] > max_grade:
                continue
            
            total_count += 1
            record = user_data.get(word_id)
            level = record["level"] if record else 0
            
            # 达到层级 4，彻底出师
            if level >= 4:
                learned_count += 1
                continue

            # 错题池判定 (如果在错题池里，检查是否冷却完毕)
            if word_id in session["wrong_pool"]:
                if session["wrong_pool"][word_id] <= 0:
                    ready_wrong_candidates.append(word_data)
                continue 
                
            # 常规池判定 (没复习过，或者到了复习日期且今天没做过)
            next_date = record["next_review_date"] if record else today
            last_date = record["last_review_date"] if record else None
            
            if next_date <= today and last_date != today:
                regular_candidates.append(word_data)

        # 2. 冷却期集体倒数 1 个字
        for wid in session["wrong_pool"]:
            if session["wrong_pool"][wid] > 0:
                session["wrong_pool"][wid] -= 1

        # 3. ⭐️ 盲盒抽签逻辑 
        limit_reached = session["regular_count"] >= DAILY_LIMIT
        temp_pool_empty = len(session["wrong_pool"]) == 0
        
        next_word = None
        
        if limit_reached or not regular_candidates:
            # 场景 A：常规题做完了/没题了 -> 强行清算错题池 (就算在冷却期也要拽出来做)
            if ready_wrong_candidates:
                next_word = random.choice(ready_wrong_candidates)
            elif not temp_pool_empty:
                #虽然冷却不够但是没有复习的了，仍然抽题
                all_wrong = [self.words[wid] for wid in session["wrong_pool"].keys()] 
                next_word = random.choice(all_wrong)
        else:
            # 场景 B：正常听写中 -> 30% 概率触发盲盒错题复现
            if ready_wrong_candidates and random.random() < 0.3:
                next_word = random.choice(ready_wrong_candidates)
            else:
                next_word = random.choice(regular_candidates)
                

        return next_word, learned_count, total_count, session["regular_count"]

    def update_user_record(self, user_id: str, word_id: int, level: int, next_date: datetime.date, last_date: datetime.date, is_correct: bool, is_temp_pool: bool):
        today = datetime.date.today()
        session = self._get_or_create_session(user_id, today)
        
        if user_id not in self.user_records:
            self.user_records[user_id] = {}
            
        self.user_records[user_id][word_id] = {
            "level": level,
            "next_review_date": next_date,
            "last_review_date": last_date
        }
        if not is_temp_pool:
            session["regular_count"] += 1
        
        # ⭐️ 错题池的增减逻辑
        if not is_correct:
            session["wrong_pool"][word_id] = 3 # 扔进错题池，并强制冷却 3 个字后才能被抽到
        elif is_temp_pool and is_correct:
            # 临时复习答对了，从池子里踢出
            if word_id in session["wrong_pool"]:
                del session["wrong_pool"][word_id]

memory_cache = ReviewCache()