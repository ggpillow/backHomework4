import json
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks

from database import init_db
from crud import StudentCRUD
from schemas import (
    StudentCreate, StudentUpdate, StudentResponse,
    CsvLoadRequest, StudentsDeleteRequest
)
from auth import router as auth_router, get_current_user
from redis_client import redis_client
from tasks import load_students_from_csv_task, delete_students_by_ids_task

app = FastAPI(title="Students API")

init_db()
app.include_router(auth_router)

CACHE_TTL_SECONDS = 60


def cache_key_all_students() -> str:
    return "students:all"


def cache_key_student(student_id: int) -> str:
    return f"students:id:{student_id}"


def cache_key_faculty(faculty: str) -> str:
    return f"students:faculty:{faculty.lower()}"


def invalidate_students_cache() -> None:
    # простой способ: удаляем известные ключи + все faculty ключи
    redis_client.delete(cache_key_all_students())
    # удалим все ключи по шаблонам
    for key in redis_client.scan_iter("students:id:*"):
        redis_client.delete(key)
    for key in redis_client.scan_iter("students:faculty:*"):
        redis_client.delete(key)


@app.post("/students", response_model=StudentResponse)
def create_student(
    data: StudentCreate,
    user=Depends(get_current_user),
):
    crud = StudentCRUD()
    try:
        student = crud.create(
            last_name=data.last_name,
            first_name=data.first_name,
            faculty=data.faculty,
            course=data.course,
            grade=data.grade,
        )
        invalidate_students_cache()
        return student
    finally:
        crud.close()


# Шаг 1: фоновая загрузка из CSV, путь приходит параметром
@app.post("/students/load-csv-bg")
def load_csv_bg(
    body: CsvLoadRequest,
    background_tasks: BackgroundTasks,
    user=Depends(get_current_user),
):
    background_tasks.add_task(load_students_from_csv_task, body.path)
    invalidate_students_cache()
    return {"message": f"Загрузка CSV запущена в фоне: {body.path}"}


# Шаг 2: фоновое удаление по списку id
@app.post("/students/delete-by-ids-bg")
def delete_by_ids_bg(
    body: StudentsDeleteRequest,
    background_tasks: BackgroundTasks,
    user=Depends(get_current_user),
):
    if not body.ids:
        raise HTTPException(status_code=400, detail="Список ids пуст")

    background_tasks.add_task(delete_students_by_ids_task, body.ids)
    invalidate_students_cache()
    return {"message": f"Удаление запущено в фоне. IDs: {body.ids}"}


# Шаг 3: кеширование всех GET эндпоинтов

@app.get("/students", response_model=list[StudentResponse])
def get_all_students(
    user=Depends(get_current_user),
):
    key = cache_key_all_students()
    cached = redis_client.get(key)
    if cached:
        return json.loads(cached)

    crud = StudentCRUD()
    try:
        students = crud.get_all()
        data = [StudentResponse.model_validate(s).model_dump() for s in students]
        redis_client.setex(key, CACHE_TTL_SECONDS, json.dumps(data, ensure_ascii=False))
        return data
    finally:
        crud.close()


@app.get("/students/{student_id}", response_model=StudentResponse)
def get_student(
    student_id: int,
    user=Depends(get_current_user),
):
    key = cache_key_student(student_id)
    cached = redis_client.get(key)
    if cached:
        return json.loads(cached)

    crud = StudentCRUD()
    try:
        student = crud.get_by_id(student_id)
        if not student:
            raise HTTPException(status_code=404, detail="Студент не найден")
        data = StudentResponse.model_validate(student).model_dump()
        redis_client.setex(key, CACHE_TTL_SECONDS, json.dumps(data, ensure_ascii=False))
        return data
    finally:
        crud.close()


@app.get("/students/faculty/{faculty}", response_model=list[StudentResponse])
def get_by_faculty(
    faculty: str,
    user=Depends(get_current_user),
):
    key = cache_key_faculty(faculty)
    cached = redis_client.get(key)
    if cached:
        return json.loads(cached)

    crud = StudentCRUD()
    try:
        students = crud.get_by_faculty(faculty)
        data = [StudentResponse.model_validate(s).model_dump() for s in students]
        redis_client.setex(key, CACHE_TTL_SECONDS, json.dumps(data, ensure_ascii=False))
        return data
    finally:
        crud.close()


@app.put("/students/{student_id}", response_model=StudentResponse)
def update_student(
    student_id: int,
    data: StudentUpdate,
    user=Depends(get_current_user),
):
    crud = StudentCRUD()
    try:
        update_data = data.model_dump(exclude_none=True)
        if not update_data:
            raise HTTPException(status_code=400, detail="Нет данных для обновления")

        student = crud.update(student_id, **update_data)
        if not student:
            raise HTTPException(status_code=404, detail="Студент не найден")

        invalidate_students_cache()
        return student
    finally:
        crud.close()


@app.delete("/students/{student_id}")
def delete_student(
    student_id: int,
    user=Depends(get_current_user),
):
    crud = StudentCRUD()
    try:
        success = crud.delete(student_id)
        if not success:
            raise HTTPException(status_code=404, detail="Студент не найден")
        invalidate_students_cache()
        return {"message": f"Студент {student_id} удалён"}
    finally:
        crud.close()