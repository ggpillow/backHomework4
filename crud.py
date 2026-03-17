import csv
from sqlalchemy import func, distinct
from database import SessionLocal
from models import Student


class StudentCRUD:
    def __init__(self):
        self.session = SessionLocal()

    def close(self):
        self.session.close()

    def create(self, last_name: str, first_name: str, faculty: str, course: str, grade: int):
        student = Student(
            last_name=last_name,
            first_name=first_name,
            faculty=faculty,
            course=course,
            grade=grade,
        )
        self.session.add(student)
        self.session.commit()
        self.session.refresh(student)
        return student

    def load_from_csv(self, filepath: str):
        with open(filepath, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                student = Student(
                    last_name=row["Фамилия"],
                    first_name=row["Имя"],
                    faculty=row["Факультет"],
                    course=row["Курс"],
                    grade=int(row["Оценка"]),
                )
                self.session.add(student)
        self.session.commit()

    
    def get_all(self):
        return self.session.query(Student).all()

    
    def get_by_faculty(self, faculty: str):
        return self.session.query(Student).filter(Student.faculty == faculty).all()

    
    def get_unique_courses(self):
        results = self.session.query(distinct(Student.course)).all()
        return [row[0] for row in results]

    
    def get_avg_grade_by_faculty(self, faculty: str):
        result = (
            self.session.query(func.avg(Student.grade))
            .filter(Student.faculty == faculty)
            .scalar()
        )
        return round(result, 2) if result else None

    
    def get_low_grade_by_course(self, course: str):
        return (
            self.session.query(Student)
            .filter(Student.course == course, Student.grade < 30)
            .all()
        )
    
    def delete(self, student_id: int):
        student = self.get_by_id(student_id)
        if not student:
            return False
        self.session.delete(student)
        self.session.commit()
        return True