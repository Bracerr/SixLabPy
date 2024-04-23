from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from datetime import datetime, timedelta
from pydantic import BaseModel
import jwt
from passlib.context import CryptContext
from pymongo import MongoClient
import logging

SECRET_KEY = "your-secret-key"  # Замените это на ваш секретный ключ
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

app = FastAPI()

client = MongoClient("mongodb://localhost:27017/")
db = client["isio"]  # Название вашей базы данных
users_collection = db["users"]  # Название вашей коллекции пользователей

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

token_blacklist = set()

logging.basicConfig(filename='security.log', level=logging.INFO)


# Модель пользователя
class User(BaseModel):
    username: str
    password: str
    role: str
    logged: bool


# Генерация JWT-токена
def create_access_token(data: dict, expires_delta: timedelta):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# Метод создания пользователя
@app.post("/users/signup")
async def create_user(user: User):
    if users_collection.find_one({"username": user.username}):
        raise HTTPException(status_code=400, detail="Пользователь с таким никнеймом уже существует")

    hashed_password = pwd_context.hash(user.password)

    user_data = {"username": user.username, "password": hashed_password, "role": user.role, "logged": False}
    users_collection.insert_one(user_data)

    return {"message": "Пользователь успешно создан"}


@app.post("/users/signin")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user_data = users_collection.find_one({"username": form_data.username})
    if user_data is None or not pwd_context.verify(form_data.password, user_data.get("password")) or user_data.get(
            "logged") is True:
        raise HTTPException(status_code=400, detail="Неверный логин или пароль")

    users_collection.update_one({"username": form_data.username}, {"$set": {"logged": True}})

    return {"message": "Вы успешно авторизовались"}


# Метод авторизации и выдачи токена
@app.post("/users/admin")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user_data = users_collection.find_one({"username": form_data.username})
    if user_data is None or not pwd_context.verify(form_data.password, user_data.get("password")):
        raise HTTPException(status_code=400, detail="Неверный логин или пароль")

    # Генерация токена
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user_data["username"], "scopes": form_data.scopes},
        expires_delta=access_token_expires
    )

    users_collection.update_one({"username": form_data.username}, {"$set": {"logged": True}})

    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/logout")
async def logout(token: str = Depends(oauth2_scheme)):
    token_blacklist.add(token)
    return {"message": "Вы успешно вышли из аккаунта"}


# Защищенный маршрут для тестирования
@app.get("/users/me")
async def read_users_me(token: str = Depends(oauth2_scheme)):
    try:
        if token in token_blacklist:
            return {"message": "Необходима авторизация"}
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Необходима авторизация")
        return {"username": username}
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Необходима авторизация")
