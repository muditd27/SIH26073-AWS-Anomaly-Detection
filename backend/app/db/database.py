import psycopg2

DATABASE_NAME = "sih26073"


def get_connection():
    return psycopg2.connect(
        dbname=DATABASE_NAME
    )
