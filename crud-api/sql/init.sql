-- Runs automatically the first time the Postgres container starts with an
-- empty data volume (Postgres's docker image scans /docker-entrypoint-initdb.d).
-- If you already have a volume, this will NOT re-run -- drop the volume to reset.

CREATE TABLE IF NOT EXISTS tasks (
    id    SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    done  BOOLEAN NOT NULL DEFAULT FALSE
);

INSERT INTO tasks (title, done) VALUES
    ('Buy milk', FALSE),
    ('Write README', FALSE),
    ('Learn FastAPI', TRUE);
