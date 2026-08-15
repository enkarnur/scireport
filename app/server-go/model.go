package main

import "time"

// Item 是 demo CRUD 示例的数据模型。如果不使用 items demo，可以安全删除本 struct。
// Store 接口使用 map[string]any，不依赖此定义。
type Item struct {
	ID          string `json:"id"`
	Title       string `json:"title"`
	Description string `json:"description"`
	Status      string `json:"status"`
	CreatedAt   string `json:"createdAt"`
	UpdatedAt   string `json:"updatedAt"`
}

type storeConfig struct {
	Mode string `json:"mode"`
}

type authResult struct {
	Username  string `json:"username"`
	Valid     bool   `json:"valid"`
	HasAccess bool   `json:"has_access"`
}

type authCacheEntry struct {
	Data      authResult
	ExpiresAt time.Time
}
