package main

import (
	"context"
	"database/sql"
	"encoding/json"
	"errors"
	"os"
	"path/filepath"
	"strings"
	"time"

	"github.com/google/uuid"
	_ "modernc.org/sqlite"
)

type sqliteStore struct {
	db *sql.DB
}

func newSQLiteStore() (*sqliteStore, error) {
	dataDir, err := resolveDataDir()
	if err != nil {
		return nil, err
	}
	if err := os.MkdirAll(dataDir, 0o755); err != nil {
		return nil, err
	}
	db, err := sql.Open("sqlite", filepath.Join(dataDir, "app.db"))
	if err != nil {
		return nil, err
	}
	if _, err := db.Exec(`CREATE TABLE IF NOT EXISTS records (
		id TEXT NOT NULL,
		collection TEXT NOT NULL,
		data TEXT NOT NULL,
		createdAt TEXT NOT NULL,
		updatedAt TEXT NOT NULL,
		PRIMARY KEY (collection, id)
	)`); err != nil {
		return nil, err
	}
	st := &sqliteStore{db: db}
	if err := st.runMigrations(); err != nil {
		return nil, err
	}
	return st, nil
}

func (s *sqliteStore) runMigrations() error {
	migrations := []string{
		// 追加 ALTER TABLE 语句；"duplicate column name" 错误会被忽略。
	}
	for _, stmt := range migrations {
		if _, err := s.db.Exec(stmt); err != nil && !strings.Contains(err.Error(), "duplicate column name") {
			return err
		}
	}
	return nil
}

func (s *sqliteStore) Mode() string { return "sqlite" }

func (s *sqliteStore) GetAll(ctx context.Context, collection string) ([]map[string]any, error) {
	rows, err := s.db.QueryContext(ctx, `SELECT id, data, createdAt, updatedAt FROM records WHERE collection = ? ORDER BY createdAt DESC`, collection)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	items := []map[string]any{}
	for rows.Next() {
		item, err := scanRecord(rows)
		if err != nil {
			return nil, err
		}
		items = append(items, item)
	}
	return items, rows.Err()
}

func (s *sqliteStore) GetByID(ctx context.Context, collection string, id string) (map[string]any, error) {
	row := s.db.QueryRowContext(ctx, `SELECT id, data, createdAt, updatedAt FROM records WHERE collection = ? AND id = ?`, collection, id)
	item, err := scanRecord(row)
	if errors.Is(err, sql.ErrNoRows) {
		return nil, nil
	}
	if err != nil {
		return nil, err
	}
	return item, nil
}

func (s *sqliteStore) Create(ctx context.Context, collection string, data map[string]any) (map[string]any, error) {
	now := time.Now().Format(time.RFC3339)
	id := asString(data["id"])
	if id == "" {
		id = uuid.NewString()
	}
	data["id"] = id
	data["createdAt"] = now
	data["updatedAt"] = now
	payload, err := json.Marshal(data)
	if err != nil {
		return nil, err
	}
	_, err = s.db.ExecContext(ctx, `INSERT INTO records (id, collection, data, createdAt, updatedAt) VALUES (?, ?, ?, ?, ?)`, id, collection, string(payload), now, now)
	if err != nil {
		return nil, err
	}
	return data, nil
}

func (s *sqliteStore) Update(ctx context.Context, collection string, id string, data map[string]any) (map[string]any, error) {
	existing, err := s.GetByID(ctx, collection, id)
	if err != nil {
		return nil, err
	}
	if existing == nil {
		return nil, sql.ErrNoRows
	}
	now := time.Now().Format(time.RFC3339)
	data["id"] = id
	if data["createdAt"] == nil {
		data["createdAt"] = existing["createdAt"]
	}
	data["updatedAt"] = now
	payload, err := json.Marshal(data)
	if err != nil {
		return nil, err
	}
	_, err = s.db.ExecContext(ctx, `UPDATE records SET data = ?, updatedAt = ? WHERE collection = ? AND id = ?`, string(payload), now, collection, id)
	if err != nil {
		return nil, err
	}
	return data, nil
}

func (s *sqliteStore) Delete(ctx context.Context, collection string, id string) error {
	result, err := s.db.ExecContext(ctx, `DELETE FROM records WHERE collection = ? AND id = ?`, collection, id)
	if err != nil {
		return err
	}
	rows, err := result.RowsAffected()
	if err != nil {
		return err
	}
	if rows == 0 {
		return sql.ErrNoRows
	}
	return nil
}

func scanRecord(scanner interface{ Scan(...any) error }) (map[string]any, error) {
	var id, raw, createdAt, updatedAt string
	if err := scanner.Scan(&id, &raw, &createdAt, &updatedAt); err != nil {
		return nil, err
	}
	var data map[string]any
	if err := json.Unmarshal([]byte(raw), &data); err != nil {
		data = map[string]any{}
	}
	data["id"] = id
	data["createdAt"] = createdAt
	data["updatedAt"] = updatedAt
	return data, nil
}
