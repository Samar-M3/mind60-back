from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from core.config import settings
from core.firebase import init_firebase
from middleware.rate_limiter import RateLimiterMiddleware
from routers import auth, posts, reactions, comments, feed, chat, users, games

load_dotenv()
init_firebase()

API_PREFIX = "/api"

app = FastAPI(
    title="MindSathi API",
    description="Mental health community platform API",
    version="1.1.0",
)

# CORS Middleware
allowed_origins = settings.allowed_origins
if settings.frontend_url and settings.frontend_url not in allowed_origins:
    allowed_origins.append(settings.frontend_url)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Basic rate limit for dev to avoid accidental hammering
app.add_middleware(RateLimiterMiddleware, max_requests=240, window_seconds=60)

# Routers
app.include_router(auth.router, prefix=API_PREFIX)
app.include_router(posts.router, prefix=API_PREFIX)
app.include_router(reactions.router, prefix=API_PREFIX)
app.include_router(comments.router, prefix=API_PREFIX)
app.include_router(feed.router, prefix=API_PREFIX)
app.include_router(chat.router, prefix=API_PREFIX)
app.include_router(users.router, prefix=API_PREFIX)
app.include_router(games.router, prefix=API_PREFIX)


@app.get("/")
def read_root():
    return {"message": "MindSathi API", "version": "1.1.0"}


@app.get("/health")
def health_check():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
