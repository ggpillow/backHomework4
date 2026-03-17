from fastapi import FastAPI, HTTPException
from database import init_db
from crud import StudentCRUD
from schemas import StudentCreate, StudentUpdate, StudentResponse

app = FastAPI(title="Students API")

init_db()

@app.post("/students", response_model=StudentResponse)
def create_student(data: StudentCreate):
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
def load_csv():
    crud = StudentCRUD()
    try:
        crud.load_from_csv("students.csv")
        return {"message": "Данные из CSV загружены"}
    finally:
        crud.close()


@app.get("/students", response_model=list[StudentResponse])
def get_all_students():
    crud = StudentCRUD()
    try:
        return crud.get_all()
    finally:
        crud.close()


@app.get("/students/{student_id}", response_model=StudentResponse)
def get_student(student_id: int):
    crud = StudentCRUD()
    try:
        student = crud.get_by_id(student_id)
        if not student:
            raise HTTPException(status_code=404, detail="Студент не найден")
        return student
    finally:
        crud.close()


@app.get("/students/faculty/{faculty}", response_model=list[StudentResponse])
def get_by_faculty(faculty: str):
    crud = StudentCRUD()
    try:
        return crud.get_by_faculty(faculty)
    finally:
        crud.close()

@app.put("/students/{student_id}", response_model=StudentResponse)
def update_student(student_id: int, data: StudentUpdate):
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
def delete_student(student_id: int):
    crud = StudentCRUD()
    try:
        success = crud.delete(student_id)
        if not success:
            raise HTTPException(status_code=404, detail="Студент не найден")
        return {"message": f"Студент {student_id} удалён"}
    finally:
        crud.close()