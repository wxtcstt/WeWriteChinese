from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from typing import List,Optional
import csv
import io

from api.dependencies import get_db
from models.word import Word
from schemas.word import WordCreate, WordResponse
from services.review_cache import memory_cache

router = APIRouter()

@router.get("/", response_model=List[WordResponse])
def get_words(
    skip: int = 0, 
    limit: int = 100, 
    search: Optional[str] = None, # ⭐️ 新增搜索参数
    db: Session = Depends(get_db)
):
    """
    获取字库列表，支持分页和汉字模糊搜索
    """
    query = db.query(Word)
    
    if search:
        # 如果传了 search 参数，就进行模糊匹配
        query = query.filter(Word.character.like(f"%{search}%"))
        
    words = query.offset(skip).limit(limit).all()
    return words

@router.put("/{word_id}", response_model=WordResponse)
def update_word(word_id: int, word_in: WordCreate, db: Session = Depends(get_db)):
    """
    修改生字信息
    """
    word = db.query(Word).filter(Word.id == word_id).first()
    if not word:
        raise HTTPException(status_code=404, detail="生字不存在")
        
    # 检查如果修改了汉字本身，是否与其他现有的字冲突
    if word.character != word_in.character:
        conflict = db.query(Word).filter(Word.character == word_in.character).first()
        if conflict:
            raise HTTPException(status_code=400, detail=f"汉字 '{word_in.character}' 已存在，不能修改为该字")

    # 更新字段
    word.character = word_in.character
    word.pinyin = word_in.pinyin
    word.grade = word_in.grade
    word.unit = word_in.unit
    word.tts_hint = word_in.tts_hint
    word.common_words = word_in.common_words
    word.image_path = word_in.image_path
    
    db.commit()
    db.refresh(word)
    
    # 清理缓存，强制重载
    memory_cache.is_loaded = False
    
    return word

@router.post("/", response_model=WordResponse)
def create_word(word_in: WordCreate, db: Session = Depends(get_db)):
    """
    添加单个生字到字库
    """
    # 检查字是否已存在
    existing_word = db.query(Word).filter(Word.character == word_in.character).first()
    if existing_word:
        raise HTTPException(status_code=400, detail=f"汉字 '{word_in.character}' 已存在于字库中")
        
    new_word = Word(
        character=word_in.character,
        pinyin=word_in.pinyin,
        grade=word_in.grade,
        unit=word_in.unit,
        tts_hint=word_in.tts_hint,
        common_words=word_in.common_words,
        image_path=word_in.image_path
    )
    db.add(new_word)
    db.commit()
    db.refresh(new_word)
    
    # 清理缓存，强制下次抽词时重新加载数据库
    memory_cache.is_loaded = False 
    
    return new_word

@router.delete("/{word_id}")
def delete_word(word_id: int, db: Session = Depends(get_db)):
    """
    从字库中删除生字
    """
    word = db.query(Word).filter(Word.id == word_id).first()
    if not word:
        raise HTTPException(status_code=404, detail="生字不存在")
        
    db.delete(word)
    db.commit()
    
    # 清理缓存
    memory_cache.is_loaded = False
    
    return {"message": "删除成功"}

@router.post("/import")
async def import_words_from_csv(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    上传 CSV 文件，将生字批量导入数据库。
    自动跳过数据库中已经存在的汉字。
    """
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="必须上传 .csv 格式的文件")
    
    # 读取文件内容
    contents = await file.read()
    # 之前我们保存时用了 utf-8-sig，这里也要对应解码
    decoded_content = contents.decode('utf-8-sig')
    
    # 使用 Python 内置的 csv 模块读取
    reader = csv.DictReader(io.StringIO(decoded_content))
    
    # 先查询数据库中已经存在哪些字，防止重复插入报错
    existing_words = {w[0] for w in db.query(Word.character).all()}
    
    words_to_insert = []
    skipped_count = 0

    for row in reader:
        char = row.get('character', '').strip()
        if not char:
            continue
            
        if char in existing_words:
            skipped_count += 1
            continue
            
        # 组装数据，兼容空值
        word = Word(
            character=char,
            pinyin=row.get('pinyin', '').strip(),
            grade=int(row.get('grade') or 5),
            unit=int(row.get('unit') or 1),
            tts_hint=row.get('tts_hint', '').strip(),
            common_words=row.get('common_words', '').strip(),
            image_path=row.get('image_path', '').strip()
        )
        words_to_insert.append(word)
        existing_words.add(char) # 更新缓存，防止 CSV 内部有重复字

    # 批量保存到数据库（性能更好）
    if words_to_insert:
        db.bulk_save_objects(words_to_insert)
        db.commit()
        memory_cache.is_loaded = False

    return {
        "message": "CSV 数据处理完毕",
        "imported_count": len(words_to_insert),
        "skipped_count": skipped_count
    }