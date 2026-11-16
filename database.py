
import os
import pg8000.dbapi

from urllib.parse import urlparse, unquote
from collections.abc import Mapping
from datetime import datetime, date


class DatabaseRow(Mapping):

    def __init__(self, columns, values):
        self._data = dict(zip(columns, values))
        self._values = values

    def __getitem__(self, key):
        if isinstance(key, int):
            return self._values[key]
        return self._data[key]

    def __iter__(self):
        return iter(self._data)

    def __len__(self):
        return len(self._data)


class DatabaseCursor:

    def __init__(self, cursor):
        self.cursor = cursor

    def _convert_row(self, row):
        if row is None:
            return None

        columns = [column[0] for column in self.cursor.description]

        values = tuple(
            value.isoformat()
            if isinstance(value, (datetime, date))
            else value
            for value in row
        )

        return DatabaseRow(columns, values)

    def fetchone(self):
        return self._convert_row(self.cursor.fetchone())

    def fetchall(self):
        return [
            self._convert_row(row)
            for row in self.cursor.fetchall()
        ]

    @property
    def rowcount(self):
        return self.cursor.rowcount


class DatabaseConnection:

    def __init__(self):
        database_url = os.environ.get("DATABASE_URL")

        if not database_url:
            raise ValueError("DATABASE_URL is not set.")

        url = urlparse(database_url)

        self.connection = pg8000.dbapi.connect(
            user=unquote(url.username),
            password=unquote(url.password),
            host=url.hostname,
            port=url.port or 5432,
            database=url.path.lstrip("/"),
            ssl_context=True
        )

    def execute(self, query, parameters=()):
        query = query.replace("?", "%s")

        if query.strip().upper() == "BEGIN IMMEDIATE":
            query = "BEGIN"

        cursor = self.connection.cursor()
        cursor.execute(query, parameters)

        return DatabaseCursor(cursor)

    def commit(self):
        self.connection.commit()

    def rollback(self):
        self.connection.rollback()

    def close(self):
        self.connection.close()


def get_db_connection():
    return DatabaseConnection()
