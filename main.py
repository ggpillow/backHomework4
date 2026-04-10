from fastapi import FastAPI, HTTPException, Depends
from database import init_db
from crud import StudentCRUD
from schemas import StudentCreate, StudentUpdate, StudentResponse
from auth import router as auth_router, get_current_user

app = FastAPI(title="Students API")

# создаём таблицы (students/users/sessions)
init_db()

# подключаем /auth (register/login/logout)
app.include_router(auth_router)


@app.post("/students", response_model=StudentResponse)
def create_student(
    data: StudentCreate,
    user=Depends(get_current_user),  # защита
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
        return student
    finally:
        crud.close()


@app.post("/students/load-csv")
def load_csv(
    user=Depends(get_current_user),  # защита
):
    crud = StudentCRUD()
    try:
        crud.load_from_csv("students.csv")
        return {"message": "Данные из CSV загружены"}
    finally:
        crud.close()


@app.get("/students", response_model=list[StudentResponse])
def get_all_students(
    user=Depends(get_current_user),  # защита
):
    crud = StudentCRUD()
    try:
        return crud.get_all()
    finally:
        crud.close()


@app.get("/students/{student_id}", response_model=StudentResponse)
def get_student(
    student_id: int,
    user=Depends(get_current_user),  # защита
):
    crud = StudentCRUD()
    try:
        student = crud.get_by_id(student_id)
        if not student:
            raise HTTPException(status_code=404, detail="Студент не найден")
        return student
    finally:
        crud.close()


@app.get("/students/faculty/{faculty}", response_model=list[StudentResponse])
def get_by_faculty(
    faculty: str,
    user=Depends(get_current_user),  # защита
):
    crud = StudentCRUD()
    try:
        return crud.get_by_faculty(faculty)
    finally:
        crud.close()


@app.put("/students/{student_id}", response_model=StudentResponse)
def update_student(
    student_id: int,
    data: StudentUpdate,
    user=Depends(get_current_user),  # защита
):
    crud = StudentCRUD()
    try:
        update_data = data.model_dump(exclude_none=True)
        if not update_data:
            raise HTTPException(status_code=400, detail="Нет данных для обновления")

        student = crud.update(student_id, **update_data)
        if not student:
            raise HTTPException(status_code=404, detail="Студент не найден")
        return student
    finally:
        crud.close()


@app.delete("/students/{student_id}")
def delete_student(
    student_id: int,
    user=Depends(get_current_user),  # защита
):
    crud = StudentCRUD()
    try:
        success = crud.delete(student_id)
        if not success:
            raise HTTPException(status_code=404, detail="Студент не найден")
        return {"message": f"Студент {student_id} удалён"}
    finally:
        crud.close()