from sqlmodel import Session

from app.db.session import create_db_and_tables, engine
from app.services.uploads import cleanup_uploaded_files


def main() -> None:
    create_db_and_tables()
    with Session(engine) as session:
        result = cleanup_uploaded_files(session)

    print(f"Deleted upload metadata records: {result.records_deleted}")
    print(f"Deleted upload files: {result.files_deleted}")


if __name__ == "__main__":
    main()
