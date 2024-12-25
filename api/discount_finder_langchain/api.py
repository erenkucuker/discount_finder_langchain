from fastapi import FastAPI
import uvicorn
from discount_finder_langchain.routes import router


app = FastAPI()
app.include_router(router)


def main():
    uvicorn.run("discount_finder_langchain.api:app",
                host="0.0.0.0", port=8000, workers=4, loop="asyncio")


if __name__ == "__main__":
    main()
