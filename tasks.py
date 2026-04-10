from crud import StudentCRUD

def load_students_from_csv_task(path: str) -> None:
    crud = StudentCRUD()
    try:
        crud.load_from_csv(path)
    finally:
        crud.close()


def delete_students_by_ids_task(ids: list[int]) -> int:
    crud = StudentCRUD()
    try:
        deleted = 0
        for student_id in ids:
            if crud.delete(student_id):
                deleted += 1
        return deleted
    finally:
        crud.close()