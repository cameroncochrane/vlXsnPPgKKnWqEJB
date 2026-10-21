"""Create and access the SQLite database used by the trading agent."""

from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from pathlib import Path

import sqlalchemy
from sqlalchemy.engine import Engine
from sqlalchemy.engine.reflection import Inspector


APP_ROOT = Path(__file__).resolve().parents[2]
DB_DIR = APP_ROOT / "databases"
DB_PATH = DB_DIR / "trading.db"


metadata = sqlalchemy.MetaData()

portfolio_table = sqlalchemy.Table( # These can be imported by another script
    "portfolio",
    metadata,
    sqlalchemy.Column("position_id", sqlalchemy.String, primary_key=True),
    sqlalchemy.Column("btc_amnt", sqlalchemy.Float, nullable=False),
    sqlalchemy.Column("open_price", sqlalchemy.Float, nullable=False),
    sqlalchemy.Column("current_price", sqlalchemy.Float, nullable=False),
    sqlalchemy.Column("current_value", sqlalchemy.Float, nullable=False),
    sqlalchemy.Column("pnl", sqlalchemy.Float, nullable=False),
    sqlalchemy.Column("date_time", sqlalchemy.DateTime, nullable=False),
)

trades_table = sqlalchemy.Table( # These can be imported by another script
    "trades",
    metadata,
    sqlalchemy.Column("trade_id", sqlalchemy.String, primary_key=True),
    sqlalchemy.Column("type", sqlalchemy.String, nullable=False),
    # Links each trade (T_n) to its position (P_n). Not a foreign key: closed positions are removed from the portfolio table, but their trades are kept
    sqlalchemy.Column("position_id", sqlalchemy.String, nullable=False, index=True),
    sqlalchemy.Column("date_time", sqlalchemy.DateTime, nullable=False),
    sqlalchemy.Column("btc_amnt", sqlalchemy.Float, nullable=False),
    sqlalchemy.Column("price", sqlalchemy.Float, nullable=False),
    sqlalchemy.Column("value", sqlalchemy.Float, nullable=False),
    sqlalchemy.Column("realized_pnl", sqlalchemy.Float, nullable=False),
)

CASH_ROW_ID = 1 # The cash table holds a single row (the current cash balance), always stored under this id

cash_table = sqlalchemy.Table( # These can be imported by another script
    "cash",
    metadata,
    sqlalchemy.Column("cash_id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("cash", sqlalchemy.Float, nullable=False),
    sqlalchemy.Column("date_time", sqlalchemy.DateTime, nullable=False),
)

def get_engine(db_dir: Path = DB_DIR, db_path: Path = DB_PATH) -> sqlalchemy.Engine:
    """Return an engine for the trading database and ensure its tables exist.

    This function can be imported and called by another script without
    separately creating the directory or tables.

    Example:
        >>> from database.database import get_engine, portfolio
        >>> engine = get_engine()
        >>> with engine.connect() as connection:
        ...     connection.execute(sqlalchemy.select(portfolio))
    """
    db_dir.mkdir(parents=True, exist_ok=True)
    engine = sqlalchemy.create_engine(f"sqlite:///{db_path}")
    create_tables(engine)
    return engine


def create_database(db_dir: Path = DB_DIR, db_path: Path = DB_PATH) -> sqlalchemy.Engine:
    """Create or open the trading database and return its ready-to-use engine.

    Example:
        >>> engine = create_database()
    """
    return get_engine(db_dir, db_path)


def create_tables(engine: sqlalchemy.Engine) -> None:
    """Create the ``portfolio`` and ``trades`` tables for ``engine``.

    Calling this function repeatedly is safe because existing tables are
    preserved.

    Example:
        >>> engine = sqlalchemy.create_engine("sqlite:///trading.db")
        >>> create_tables(engine)
    """
    metadata.create_all(engine)


@contextmanager
def _connection(bind: sqlalchemy.Engine | sqlalchemy.Connection, write: bool = True) -> Iterator[sqlalchemy.Connection]:
    """Yield a connection for ``bind``, so the row helpers work with an engine or inside a caller's transaction.

    Given an Engine, a write opens its own transaction (committed on success, rolled back on error) and a read opens a
    plain connection. Given a Connection, it is used as is, so several helper calls share the caller's transaction and
    commit or roll back together.

    Example:
        >>> with engine.begin() as connection:  # both rows are written, or neither
        ...     add_row(connection, trades_table, trade)
        ...     modify_row(connection, cash_table, cash)
    """
    if isinstance(bind, sqlalchemy.Connection):
        yield bind
    else:
        with (bind.begin() if write else bind.connect()) as connection:
            yield connection


def fetch_table_data(bind: sqlalchemy.Engine | sqlalchemy.Connection, table: sqlalchemy.Table) -> list[dict[str, object]]:
    """Return all rows from ``table`` as dictionaries keyed by column name.

    Example:
        >>> portfolio_data = fetch_table_data(engine, portfolio_table)
        >>> process_portfolio(portfolio_data)
    """
    with _connection(bind, write=False) as connection:
        rows = connection.execute(sqlalchemy.select(table)).mappings()
        return [dict(row) for row in rows]


def print_engine_info(engine: Engine) -> None:
    """Print connection details and the schema discovered through ``engine``.

    Example:
        >>> engine = get_engine()
        >>> print_engine_info(engine)
        Engine: sqlite:///.../trading.db
        Table: portfolio
          - position_id (VARCHAR, nullable=False, primary_key=True)
    """
    inspector: Inspector = sqlalchemy.inspect(engine)
    print(f"Engine: {engine.url}")

    table_names = inspector.get_table_names()
    if not table_names:
        print("Tables: none")
        return

    print("Tables:")
    for table_name in table_names:
        print(f"Table: {table_name}")
        primary_key_columns = set(
            inspector.get_pk_constraint(table_name)["constrained_columns"]
        )
        for column in inspector.get_columns(table_name):
            nullable = column["nullable"]
            primary_key = column["name"] in primary_key_columns
            print(
                f"  - {column['name']} ({column['type']}, "
                f"nullable={nullable}, primary_key={primary_key})"
            )


def add_row(bind: sqlalchemy.Engine | sqlalchemy.Connection, table: sqlalchemy.Table, data: Mapping[str, object]) -> None:
    """Insert one dictionary of values into ``table`` and commit the transaction.

    Example:
        >>> add_row(engine, portfolio_table, {
        ...     "position_id": "P_1", "btc_amnt": 0.5, "open_price": 40000,
        ...     "current_price": 41000, "current_value": 20500, "pnl": 500,
        ... })
    """
    unknown_columns = set(data) - set(table.c.keys())
    if unknown_columns:
        raise ValueError(f"Unknown columns for {table.name}: {sorted(unknown_columns)}")

    with _connection(bind) as connection:
        connection.execute(table.insert().values(dict(data)))


def modify_row(bind: sqlalchemy.Engine | sqlalchemy.Connection, table: sqlalchemy.Table, data: Mapping[str, object]) -> None:
    """Update one row using its primary key and commit the transaction.

    The dictionary must contain the table's primary key. All other supplied
    keys are updated, so omitted columns retain their current values.

    Example:
        >>> modify_row(engine, portfolio_table, {"position_id": "P_1", "pnl": 750})
        >>> modify_row(engine, trades_table, {"trade_id": "T_1", "value": 21000})
    """
    primary_key_columns = list(table.primary_key.columns)
    if len(primary_key_columns) != 1:
        raise ValueError(f"{table.name} must have exactly one primary-key column")

    primary_key = primary_key_columns[0].name
    if primary_key not in data:
        raise ValueError(f"Missing primary-key column for {table.name}: {primary_key}")

    updates = {key: value for key, value in data.items() if key != primary_key}
    unknown_columns = set(updates) - set(table.c.keys())
    if unknown_columns:
        raise ValueError(f"Unknown columns for {table.name}: {sorted(unknown_columns)}")
    if not updates:
        raise ValueError("At least one non-primary-key value is required for an update")

    with _connection(bind) as connection:
        result = connection.execute(
            table.update()
            .where(table.c[primary_key] == data[primary_key])
            .values(updates)
        )
        if result.rowcount == 0:
            raise LookupError(
                f"No row found in {table.name} with {primary_key}={data[primary_key]!r}"
            )


def remove_row(bind: sqlalchemy.Engine | sqlalchemy.Connection, table: sqlalchemy.Table, data: Mapping[str, object]) -> None:
    """Delete one row using its primary key and commit the transaction.

    Example:
        >>> remove_row(engine, portfolio_table, {"position_id": "P_1"})
        >>> remove_row(engine, trades_table, {"trade_id": "T_1"})
    """
    primary_key_columns = list(table.primary_key.columns)
    if len(primary_key_columns) != 1:
        raise ValueError(f"{table.name} must have exactly one primary-key column")

    primary_key = primary_key_columns[0].name
    if primary_key not in data:
        raise ValueError(f"Missing primary-key column for {table.name}: {primary_key}")

    with _connection(bind) as connection:
        result = connection.execute(
            table.delete().where(table.c[primary_key] == data[primary_key])
        )
        if result.rowcount == 0:
            raise LookupError(
                f"No row found in {table.name} with {primary_key}={data[primary_key]!r}"
            )


