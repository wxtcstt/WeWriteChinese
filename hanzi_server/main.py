from dotenv import load_dotenv
load_dotenv()
from fastapi import FastAPI
from db.session import engine
from db.base import Base
from api.v1.endpoints import words,review
import uvicorn
from fastapi.middleware.cors import CORSMiddleware  # 导入 CORS 中间件
import os
from fastapi.staticfiles import StaticFiles
from starlette.responses import FileResponse

class CORSStaticFiles(StaticFiles):
    async def get_response(self, path: str, scope) -> FileResponse:
        response = await super().get_response(path, scope)
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Expose-Headers"] = "Content-Disposition"
        return response
    
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
# 创建所有数据库表（首次运行时自动创建 SQLite 数据库文件）
Base.metadata.create_all(bind=engine)

# 1. 确保目录存在
os.makedirs(STATIC_DIR, exist_ok=True)

# 初始化 FastAPI 应用
app = FastAPI(
    title="汉字听写通关系统 API",
    description="API 接口文档",
    version="1.0.0",
   
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源（本地调试），生产环境改为 ["http://your-frontend-domain.com"]
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有 HTTP 方法（GET、POST 等）
    allow_headers=["*"],  # 允许所有请求头
    expose_headers=["Content-Disposition"]
)

# 注册路由
app.include_router(words.router, prefix="/api/v1/words", tags=["生字管理"])
app.include_router(review.router, prefix="/api/v1/review", tags=["生字管理"])

app.mount("/", CORSStaticFiles(directory=STATIC_DIR), name="static")
@app.get("/")
async def root():
    return FileResponse("static/index.html")


if __name__== "__main__":
   
    # 配置启动参数（等同于 uvicorn app.main:app --reload --host 0.0.0.0 --port 8000）
    uvicorn.run(
        "main:app",  # 指定应用入口
        host="0.0.0.0",  # 允许外部访问（仅开发环境）
        port=9000,       # 端口号
        reload=True,     # 热重载（开发模式必备）
        log_level="info" # 日志级别
    )




