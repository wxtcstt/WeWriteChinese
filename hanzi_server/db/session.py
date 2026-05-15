from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# SQLite 数据库文件将存放在项目根目录下的 hanzi.db
SQLALCHEMY_DATABASE_URL = "sqlite:///./hanzi.db"

# connect_args={"check_same_thread": False} 是 SQLite 在 FastAPI 中特有的必备配置
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)