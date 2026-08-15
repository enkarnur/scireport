// handler_items.go — items 资源的业务逻辑（完整 CRUD 示例）。
//
// 路由契约在 handler_items.gen.go（由 app/api IDL 生成，勿改）：它负责 init() 里的
// Register(Route{...})，并把每条路由指向下面的 handler 函数。此文件只写业务实现。
//
// 新增接口的正确姿势：先在 app/api/api.yaml 里加一条 route，跑 tools/gen_api.py，
// 生成器会更新 .gen.go 的注册并（首次）补一个 stub；随后在此文件填实现即可。
//
// 注意：本文件是 demo 示例，可安全删除。删除后同时删除 handler_items.gen.go 和
// api.yaml 中 items 资源定义即可，不影响 store 和其他模块编译。
package main

import (
	"database/sql"
	"encoding/json"
	"errors"
	"net/http"
	"strings"
)

const itemsCollection = "items"

func itemsList(w http.ResponseWriter, r *http.Request) {
	items, err := store.GetAll(r.Context(), itemsCollection)
	if err != nil {
		writeJSON(w, http.StatusInternalServerError, map[string]any{"error": err.Error()})
		return
	}
	writeJSON(w, http.StatusOK, map[string]any{"data": items, "total": len(items), "backend": store.Mode()})
}

func itemsCreate(w http.ResponseWriter, r *http.Request) {
	var body map[string]any
	if err := json.NewDecoder(r.Body).Decode(&body); err != nil {
		writeJSON(w, http.StatusBadRequest, map[string]any{"error": "Invalid JSON body"})
		return
	}
	title := strings.TrimSpace(asString(body["title"]))
	if title == "" {
		writeJSON(w, http.StatusBadRequest, map[string]any{"error": "Title is required"})
		return
	}
	created, err := store.Create(r.Context(), itemsCollection, body)
	if err != nil {
		writeJSON(w, http.StatusInternalServerError, map[string]any{"error": err.Error()})
		return
	}
	writeJSON(w, http.StatusCreated, map[string]any{"data": created, "backend": store.Mode()})
}

func itemsByIdGet(w http.ResponseWriter, r *http.Request) {
	itemID := r.PathValue("id")
	if itemID == "" {
		writeJSON(w, http.StatusNotFound, map[string]any{"error": "Item not found"})
		return
	}
	item, err := store.GetByID(r.Context(), itemsCollection, itemID)
	if err != nil {
		writeJSON(w, http.StatusInternalServerError, map[string]any{"error": err.Error()})
		return
	}
	if item == nil {
		writeJSON(w, http.StatusNotFound, map[string]any{"error": "Item not found"})
		return
	}
	writeJSON(w, http.StatusOK, map[string]any{"data": item, "backend": store.Mode()})
}

func itemsByIdUpdate(w http.ResponseWriter, r *http.Request) {
	itemID := r.PathValue("id")
	if itemID == "" {
		writeJSON(w, http.StatusNotFound, map[string]any{"error": "Item not found"})
		return
	}
	var body map[string]any
	if err := json.NewDecoder(r.Body).Decode(&body); err != nil {
		writeJSON(w, http.StatusBadRequest, map[string]any{"error": "Invalid JSON body"})
		return
	}
	updated, err := store.Update(r.Context(), itemsCollection, itemID, body)
	if err != nil {
		if errors.Is(err, sql.ErrNoRows) {
			writeJSON(w, http.StatusNotFound, map[string]any{"error": "Item not found"})
			return
		}
		writeJSON(w, http.StatusInternalServerError, map[string]any{"error": err.Error()})
		return
	}
	writeJSON(w, http.StatusOK, map[string]any{"data": updated, "backend": store.Mode()})
}

func itemsByIdDelete(w http.ResponseWriter, r *http.Request) {
	itemID := r.PathValue("id")
	if itemID == "" {
		writeJSON(w, http.StatusNotFound, map[string]any{"error": "Item not found"})
		return
	}
	err := store.Delete(r.Context(), itemsCollection, itemID)
	if err != nil {
		if errors.Is(err, sql.ErrNoRows) {
			writeJSON(w, http.StatusNotFound, map[string]any{"error": "Item not found"})
			return
		}
		writeJSON(w, http.StatusInternalServerError, map[string]any{"error": err.Error()})
		return
	}
	writeJSON(w, http.StatusOK, map[string]any{"success": true, "backend": store.Mode()})
}
