// WebSocket Relay：让 Agent（通过 Skill CLI/HTTP）和前端页面交换通用消息；page-control 是首个业务通道。
//
// 架构：
//
//	Agent CLI  ──HTTP──▶  Relay (本模块)  ──WebSocket envelope──▶  Page Runtime (浏览器)
//
// 传输层：
//   - WebSocket /ws/page-control：前端唯一长链传输通道，握手 query 传 access_token。
//   - 消息统一使用 envelope：type=request/response/event + channel + method/event + payload。
//
// CLI 侧（HTTP）：
//   - GET  /api/page-control/sessions
//   - GET  /api/page-control/wait?timeout=
//   - POST /api/page-control/action    {action, args, timeout}
//   - POST /api/page-control/describe
//   - POST /api/page-control/state
//
// 寻址：session_id 由后端从 JWT.username + AIME_ASSISTANT_ID 拼出，调用方无需传入。
package main

import (
	"bufio"
	"crypto/sha1"
	"encoding/base64"
	"encoding/binary"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"net"
	"net/http"
	"os"
	"strconv"
	"strings"
	"sync"
	"time"

	"github.com/google/uuid"
)

func init() {
	Register(Route{Method: http.MethodGet, Path: "/api/aime/config", Summary: "返回当前 AIME 应用页面控制所需的 assistant/user/session 配置", Handler: aimeConfigHandler, Tags: []string{"page-control"}})
	Register(Route{Method: http.MethodGet, Path: "/api/page-control/sessions", Summary: "查询当前用户已连接的页面控制 WebSocket session", Handler: pageControlSessionsHandler, Tags: []string{"page-control"}})
	Register(Route{Method: http.MethodGet, Path: "/api/page-control/wait", Summary: "等待当前用户页面控制 WebSocket session 就绪", Handler: pageControlWaitHandler, Tags: []string{"page-control"}, QueryParams: []Param{{Name: "timeout", Type: "number", Description: "最多等待秒数，默认 3，最大 120"}}})
	Register(Route{Method: http.MethodPost, Path: "/api/page-control/action", Summary: "向当前页面下发一个 page-control action 并同步等待前端 response", Handler: pageControlActionHandler, Tags: []string{"page-control"}, BodyParams: []Param{{Name: "action", Type: "string", Required: true, Description: "前端 action 名，例如 dom.click/nav.goto/__state__"}, {Name: "args", Type: "object", Description: "传给前端 action 的参数对象"}, {Name: "timeout", Type: "number", Description: "最多等待秒数，默认 15，最大 120"}}, RequestExample: map[string]any{"action": "__state__", "args": map[string]any{}, "timeout": 15}})
	Register(Route{Method: http.MethodPost, Path: "/api/page-control/describe", Summary: "查询当前页面已注册的 page-control action 列表", Handler: pageControlDescribeHandler, Tags: []string{"page-control"}})
	Register(Route{Method: http.MethodPost, Path: "/api/page-control/state", Summary: "读取当前页面结构化状态快照", Handler: pageControlStateHandler, Tags: []string{"page-control"}})
	Register(Route{Method: http.MethodGet, Path: "/ws/page-control", Summary: "浏览器页面 runtime 建立 page-control WebSocket 长连接", Handler: pageControlWSHandler, Public: true, Tags: []string{"page-control"}})
	Register(Route{Method: http.MethodPost, Path: "/api/_internal/notify-refresh", Summary: "通知前端数据已变更，触发页面自动刷新", Handler: notifyRefreshHandler, Tags: []string{"internal"}, BodyParams: []Param{{Name: "resource", Type: "string", Description: "变更的资源标识，如 items；前端可据此做精细刷新"}}})
}

// NotifyDataChanged 向当前请求用户的所有已连接 page-control session 推送 data-changed 事件。
// 在 handler 写操作成功后调用，前端收到后自动 re-fetch。resource 为可选的资源标识。
func NotifyDataChanged(r *http.Request, resource string) {
	sid := deriveSessionIDFromCtx(r)
	if sid == "" {
		return
	}
	sess := pageControlRegistry.get(sid)
	if sess == nil {
		return
	}
	payload := map[string]any{"resource": resource, "at": time.Now().Unix()}
	envelope := wsEnvelope{Type: wsTypeEvent, Channel: wsChannelPageControl, Event: "data-changed", Payload: payload}
	sess.enqueue(mustJSON(envelope))
}

func notifyRefreshHandler(w http.ResponseWriter, r *http.Request) {
	var body struct {
		Resource string `json:"resource"`
	}
	if r.Body != nil {
		_ = json.NewDecoder(r.Body).Decode(&body)
	}
	NotifyDataChanged(r, body.Resource)
	writeJSON(w, http.StatusOK, map[string]any{"ok": true})
}

type pageSession struct {
	sessionID string
	transport string // always "ws"
	out       chan string

	mu       sync.Mutex
	pending  map[string]chan map[string]any
	closed   bool
	lastSeen time.Time
	ws       *pageWSConn
	wsStop   chan struct{}
	initTime int64
}

func newPageSession(sid string) *pageSession {
	return &pageSession{
		sessionID: sid,
		transport: "ws",
		out:       make(chan string, 64),
		pending:   map[string]chan map[string]any{},
		lastSeen:  time.Now(),
	}
}

func (s *pageSession) touch() {
	s.mu.Lock()
	s.lastSeen = time.Now()
	s.mu.Unlock()
}

func (s *pageSession) close() {
	s.mu.Lock()
	if s.closed {
		s.mu.Unlock()
		return
	}
	s.closed = true
	s.resolveAllLocked("session closed")
	stopCh := s.wsStop
	s.wsStop = nil
	ws := s.ws
	s.ws = nil
	s.mu.Unlock()

	closePageControlStop(stopCh)
	closePageControlOut(s.out)
	if ws != nil {
		_ = ws.close()
	}
}

func (s *pageSession) resolveAllLocked(errMsg string) {
	for id, ch := range s.pending {
		select {
		case ch <- map[string]any{"ok": false, "error": errMsg}:
		default:
		}
		delete(s.pending, id)
	}
}

func closePageControlStop(ch chan struct{}) {
	if ch == nil {
		return
	}
	func() {
		defer func() { _ = recover() }()
		close(ch)
	}()
}

func closePageControlOut(ch chan string) {
	if ch == nil {
		return
	}
	func() {
		defer func() { _ = recover() }()
		close(ch)
	}()
}

func (s *pageSession) enqueue(payload string) bool {
	defer func() { _ = recover() }()
	s.mu.Lock()
	closed := s.closed
	s.mu.Unlock()
	if closed {
		return false
	}
	select {
	case s.out <- payload:
		return true
	case <-time.After(2 * time.Second):
		return false
	}
}

func (s *pageSession) resolve(reqID string, result map[string]any) {
	if reqID == "" {
		return
	}
	s.mu.Lock()
	ch, ok := s.pending[reqID]
	if ok {
		delete(s.pending, reqID)
	}
	s.mu.Unlock()
	if ok {
		select {
		case ch <- result:
		default:
		}
	}
}

type wsEnvelope struct {
	Type    string `json:"type"`
	ID      string `json:"id,omitempty"`
	Channel string `json:"channel,omitempty"`
	Method  string `json:"method,omitempty"`
	Event   string `json:"event,omitempty"`
	OK      *bool  `json:"ok,omitempty"`
	Payload any    `json:"payload,omitempty"`
	Error   string `json:"error,omitempty"`
	T       int64  `json:"t,omitempty"`
}

const (
	wsTypeHello    = "hello"
	wsTypeRequest  = "request"
	wsTypeResponse = "response"
	wsTypeEvent    = "event"
	wsTypeError    = "error"
	wsTypePing     = "ping"
	wsTypePong     = "pong"

	wsChannelPageControl = "page-control"
	wsMethodPageAction   = "page.action"
	wsMethodPageDescribe = "page.describe"
	wsMethodPageState    = "page.state"
)

func pageActionPayload(name string, args any) map[string]any {
	payload := map[string]any{"action": name}
	if args != nil {
		payload["args"] = args
	}
	return payload
}

func normalizeWSResponse(msg map[string]any) (string, map[string]any, bool) {
	mtype, _ := msg["type"].(string)
	id, _ := msg["id"].(string)
	switch mtype {
	case wsTypeResponse:
		res := map[string]any{"ok": true}
		if payload, exists := msg["payload"]; exists {
			if payloadMap, ok := payload.(map[string]any); ok {
				for k, v := range payloadMap {
					res[k] = v
				}
			} else {
				res["data"] = payload
			}
		}
		// Envelope-level ok/error is authoritative over payload fields.
		if ok, exists := msg["ok"].(bool); exists {
			res["ok"] = ok
		}
		if errMsg, _ := msg["error"].(string); errMsg != "" {
			res["ok"] = false
			res["error"] = errMsg
		}
		return id, res, true
	case wsTypeError:
		errMsg, _ := msg["error"].(string)
		if errMsg == "" {
			errMsg = "websocket request failed"
		}
		return id, map[string]any{"ok": false, "error": errMsg}, true
	}
	return "", nil, false
}

func (s *pageSession) sendRequest(channel, method string, payload any, timeout time.Duration) map[string]any {
	reqID := uuid.NewString()[:12]
	ch := make(chan map[string]any, 1)
	s.mu.Lock()
	if s.closed || s.ws == nil {
		s.mu.Unlock()
		return map[string]any{"ok": false, "error": "session not connected"}
	}
	s.pending[reqID] = ch
	s.mu.Unlock()

	envelope := wsEnvelope{Type: wsTypeRequest, ID: reqID, Channel: channel, Method: method, Payload: payload}
	raw, _ := json.Marshal(envelope)
	logMsg(fmt.Sprintf("[ws-relay] queue channel=%s method=%s id=%s sid=%s", channel, method, reqID, s.sessionID), "plugin")
	if !s.enqueue(string(raw)) {
		s.mu.Lock()
		delete(s.pending, reqID)
		s.mu.Unlock()
		return map[string]any{"ok": false, "error": "enqueue failed"}
	}

	select {
	case res := <-ch:
		if res == nil {
			return map[string]any{"ok": false, "error": "empty response"}
		}
		return res
	case <-time.After(timeout):
		s.mu.Lock()
		delete(s.pending, reqID)
		s.mu.Unlock()
		return map[string]any{"ok": false, "error": fmt.Sprintf("websocket request timeout after %.0fs (channel=%s method=%s)", timeout.Seconds(), channel, method)}
	}
}

func (s *pageSession) sendPageAction(name string, args any, timeout time.Duration) map[string]any {
	return s.sendRequest(wsChannelPageControl, wsMethodPageAction, pageActionPayload(name, args), timeout)
}

func (s *pageSession) sendPageMethod(method string, timeout time.Duration) map[string]any {
	return s.sendRequest(wsChannelPageControl, method, nil, timeout)
}

type pageRegistry struct {
	mu        sync.Mutex
	sessions  map[string]*pageSession
	newSessCh chan struct{}
}

var pageControlRegistry = &pageRegistry{
	sessions:  map[string]*pageSession{},
	newSessCh: make(chan struct{}, 1),
}

func (r *pageRegistry) notifyNew() {
	select {
	case r.newSessCh <- struct{}{}:
	default:
	}
}

func (r *pageRegistry) register(sess *pageSession) {
	r.mu.Lock()
	old := r.sessions[sess.sessionID]
	r.sessions[sess.sessionID] = sess
	r.mu.Unlock()
	if old != nil && old != sess {
		logMsg("[page-control] session replaced: "+sess.sessionID, "plugin")
		go old.close()
	} else {
		logMsg("[page-control] session registered: "+sess.sessionID+" (ws)", "plugin")
	}
	r.notifyNew()
}

func (r *pageRegistry) unregister(sess *pageSession) {
	r.mu.Lock()
	cur := r.sessions[sess.sessionID]
	if cur == sess {
		delete(r.sessions, sess.sessionID)
		logMsg("[page-control] session unregistered: "+sess.sessionID, "plugin")
	}
	r.mu.Unlock()
}

func (r *pageRegistry) get(sid string) *pageSession {
	r.mu.Lock()
	defer r.mu.Unlock()
	return r.sessions[sid]
}

func (r *pageRegistry) waitFor(sid string, timeout time.Duration) *pageSession {
	deadline := time.Now().Add(timeout)
	for {
		if s := r.get(sid); s != nil && s.isConnected() {
			return s
		}
		remain := time.Until(deadline)
		if remain <= 0 {
			return nil
		}
		select {
		case <-r.newSessCh:
		case <-time.After(minDur(remain, 500*time.Millisecond)):
		}
	}
}

func (s *pageSession) isConnected() bool {
	s.mu.Lock()
	defer s.mu.Unlock()
	return !s.closed && s.ws != nil
}

func minDur(a, b time.Duration) time.Duration {
	if a < b {
		return a
	}
	return b
}

func readJSONBody(r *http.Request) map[string]any {
	body := map[string]any{}
	if r.Body == nil {
		return body
	}
	data, err := io.ReadAll(io.LimitReader(r.Body, 1<<20))
	if err != nil || len(data) == 0 {
		return body
	}
	_ = json.Unmarshal(data, &body)
	return body
}

func deriveSessionIDFromUsername(username string) string {
	assistantID := strings.TrimSpace(os.Getenv("AIME_ASSISTANT_ID"))
	username = strings.TrimSpace(username)
	if assistantID == "" || username == "" {
		return ""
	}
	return assistantID + "_" + username
}

func deriveSessionIDFromCtx(r *http.Request) string {
	user, _ := r.Context().Value(ctxKeyUser).(authResult)
	return deriveSessionIDFromUsername(user.Username)
}

func extractUsernameFromSessionID(sid string) string {
	sid = strings.TrimSpace(sid)
	if sid == "" {
		return ""
	}
	assistantID := strings.TrimSpace(os.Getenv("AIME_ASSISTANT_ID"))
	if assistantID != "" {
		prefix := assistantID + "_"
		if strings.HasPrefix(sid, prefix) {
			return strings.TrimSpace(sid[len(prefix):])
		}
		return ""
	}
	if i := strings.LastIndex(sid, "_"); i >= 0 && i+1 < len(sid) {
		return strings.TrimSpace(sid[i+1:])
	}
	return ""
}

func authorizeRelayRequest(w http.ResponseWriter, r *http.Request, body map[string]any) (string, bool) {
	user, _ := r.Context().Value(ctxKeyUser).(authResult)
	username := strings.TrimSpace(user.Username)
	sid := deriveSessionIDFromUsername(username)
	if sid == "" {
		writeJSON(w, http.StatusBadRequest, map[string]any{"ok": false, "error": "cannot derive session_id: missing user or AIME_ASSISTANT_ID"})
		return "", false
	}
	inbound := strings.TrimSpace(r.URL.Query().Get("session_id"))
	if inbound == "" && body != nil {
		if v, ok := body["session_id"].(string); ok {
			inbound = strings.TrimSpace(v)
		}
	}
	if !validateInboundSessionID(w, inbound, username) {
		return "", false
	}
	return sid, true
}

func validateInboundSessionID(w http.ResponseWriter, inboundSID, expectedUsername string) bool {
	inboundSID = strings.TrimSpace(inboundSID)
	if inboundSID == "" {
		return true
	}
	gotUser := extractUsernameFromSessionID(inboundSID)
	if gotUser != "" && gotUser == strings.TrimSpace(expectedUsername) {
		return true
	}
	logMsg(fmt.Sprintf("[page-control] session_id/jwt mismatch: inbound_sid=%q inbound_user=%q jwt_user=%q", inboundSID, gotUser, expectedUsername), "plugin")
	writeJSON(w, http.StatusForbidden, map[string]any{"ok": false, "error": "session_id does not match authenticated user"})
	return false
}

func floatFrom(v any, fallback float64) float64 {
	switch x := v.(type) {
	case float64:
		return x
	case int:
		return float64(x)
	case string:
		if f, err := strconv.ParseFloat(x, 64); err == nil {
			return f
		}
	}
	return fallback
}

func pageControlSessionsHandler(w http.ResponseWriter, r *http.Request) {
	sid := deriveSessionIDFromCtx(r)
	data := []map[string]any{}
	if sid != "" {
		if sess := pageControlRegistry.get(sid); sess != nil {
			sess.mu.Lock()
			data = append(data, map[string]any{
				"session_id": sid,
				"transport":  sess.transport,
				"connected":  sess.ws != nil && !sess.closed,
				"last_seen":  sess.lastSeen.Format(time.RFC3339),
				"init_time":  sess.initTime,
			})
			sess.mu.Unlock()
		}
	}
	writeJSON(w, http.StatusOK, map[string]any{"ok": true, "data": data})
}

func pageControlWaitHandler(w http.ResponseWriter, r *http.Request) {
	sid, ok := authorizeRelayRequest(w, r, nil)
	if !ok {
		return
	}
	timeout, _ := strconv.ParseFloat(r.URL.Query().Get("timeout"), 64)
	if timeout <= 0 {
		timeout = 3
	}
	if timeout > 120 {
		timeout = 120
	}
	sess := pageControlRegistry.waitFor(sid, time.Duration(timeout*float64(time.Second)))
	if sess == nil {
		writeJSON(w, http.StatusGatewayTimeout, map[string]any{"ok": false, "error": "timeout waiting for page", "session_id": sid})
		return
	}
	writeJSON(w, http.StatusOK, map[string]any{"ok": true, "session_id": sid, "transport": sess.transport})
}

func pageControlActionHandler(w http.ResponseWriter, r *http.Request) {
	body := readJSONBody(r)
	sid, ok := authorizeRelayRequest(w, r, body)
	if !ok {
		return
	}
	action, _ := body["action"].(string)
	action = strings.TrimSpace(action)
	timeout := floatFrom(body["timeout"], 15)
	if timeout <= 0 {
		timeout = 15
	}
	if timeout > 120 {
		timeout = 120
	}
	if action == "" {
		writeJSON(w, http.StatusBadRequest, map[string]any{"ok": false, "error": "action required"})
		return
	}
	sess := pageControlRegistry.get(sid)
	if sess == nil || !sess.isConnected() {
		sess = pageControlRegistry.waitFor(sid, 3*time.Second)
	}
	if sess == nil {
		writeJSON(w, http.StatusNotFound, map[string]any{"ok": false, "error": "no page connected for this session", "session_id": sid, "hint": "先打开 AIME app 页面，或调用 /api/page-control/wait 等待连接"})
		return
	}
	logMsg("[page-control] dispatch action="+action+" sid="+sid, "plugin")
	writeJSON(w, http.StatusOK, sess.sendPageAction(action, body["args"], time.Duration(timeout*float64(time.Second))))
}

func pageControlDescribeHandler(w http.ResponseWriter, r *http.Request) {
	var body map[string]any
	if r.Method == http.MethodPost {
		body = readJSONBody(r)
	}
	sid, ok := authorizeRelayRequest(w, r, body)
	if !ok {
		return
	}
	sess := pageControlRegistry.get(sid)
	if sess == nil || !sess.isConnected() {
		sess = pageControlRegistry.waitFor(sid, 3*time.Second)
	}
	if sess == nil {
		writeJSON(w, http.StatusNotFound, map[string]any{"ok": false, "error": "no page connected", "session_id": sid})
		return
	}
	writeJSON(w, http.StatusOK, sess.sendPageMethod(wsMethodPageDescribe, 10*time.Second))
}

func pageControlStateHandler(w http.ResponseWriter, r *http.Request) {
	var body map[string]any
	if r.Method == http.MethodPost {
		body = readJSONBody(r)
	}
	sid, ok := authorizeRelayRequest(w, r, body)
	if !ok {
		return
	}
	sess := pageControlRegistry.get(sid)
	if sess == nil || !sess.isConnected() {
		sess = pageControlRegistry.waitFor(sid, 3*time.Second)
	}
	if sess == nil {
		writeJSON(w, http.StatusNotFound, map[string]any{"ok": false, "error": "no page connected", "session_id": sid})
		return
	}
	writeJSON(w, http.StatusOK, sess.sendPageMethod(wsMethodPageState, 10*time.Second))
}

func mustJSON(v any) string {
	b, _ := json.Marshal(v)
	return string(b)
}

func aimeConfigHandler(w http.ResponseWriter, r *http.Request) {
	user, _ := r.Context().Value(ctxKeyUser).(authResult)
	username := strings.TrimSpace(user.Username)
	assistantID := strings.TrimSpace(os.Getenv("AIME_ASSISTANT_ID"))
	pluginName := strings.TrimSpace(os.Getenv("AIME_PLUGIN_NAME"))
	if pluginName == "" {
		pluginName = "AIME app"
	}
	sessionID := ""
	if assistantID != "" && username != "" {
		sessionID = assistantID + "_" + username
	}
	writeJSON(w, http.StatusOK, map[string]any{"assistant_id": assistantID, "username": username, "plugin_name": pluginName, "session_id": sessionID})
}

const wsGUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"

type pageWSConn struct {
	conn net.Conn
	rw   *bufio.ReadWriter
	mu   sync.Mutex
}

func (c *pageWSConn) writeText(msg string) error {
	c.mu.Lock()
	defer c.mu.Unlock()
	return writeWSFrame(c.conn, 0x1, []byte(msg))
}

func (c *pageWSConn) writeClose() error {
	c.mu.Lock()
	defer c.mu.Unlock()
	return writeWSFrame(c.conn, 0x8, nil)
}

func (c *pageWSConn) close() error {
	_ = c.writeClose()
	return c.conn.Close()
}

func writeWSFrame(w io.Writer, opcode byte, payload []byte) error {
	buf := make([]byte, 0, 10+len(payload))
	buf = append(buf, 0x80|opcode)
	n := len(payload)
	switch {
	case n < 126:
		buf = append(buf, byte(n))
	case n < 65536:
		buf = append(buf, 126, byte(n>>8), byte(n))
	default:
		var ext [8]byte
		binary.BigEndian.PutUint64(ext[:], uint64(n))
		buf = append(buf, 127)
		buf = append(buf, ext[:]...)
	}
	buf = append(buf, payload...)
	_, err := w.Write(buf)
	return err
}

func readWSFrame(r *bufio.Reader) (byte, []byte, error) {
	var hdr [2]byte
	if _, err := io.ReadFull(r, hdr[:]); err != nil {
		return 0, nil, err
	}
	opcode := hdr[0] & 0x0F
	masked := hdr[1]&0x80 != 0
	payloadLen := uint64(hdr[1] & 0x7F)
	switch payloadLen {
	case 126:
		var ext [2]byte
		if _, err := io.ReadFull(r, ext[:]); err != nil {
			return 0, nil, err
		}
		payloadLen = uint64(binary.BigEndian.Uint16(ext[:]))
	case 127:
		var ext [8]byte
		if _, err := io.ReadFull(r, ext[:]); err != nil {
			return 0, nil, err
		}
		payloadLen = binary.BigEndian.Uint64(ext[:])
	}
	if payloadLen > (1 << 20) {
		return 0, nil, errors.New("frame too large")
	}
	payLen := int64(payloadLen)
	var mask [4]byte
	if masked {
		if _, err := io.ReadFull(r, mask[:]); err != nil {
			return 0, nil, err
		}
	}
	payload := make([]byte, payLen)
	if payLen > 0 {
		if _, err := io.ReadFull(r, payload); err != nil {
			return 0, nil, err
		}
	}
	if masked {
		for i := range payload {
			payload[i] ^= mask[i%4]
		}
	}
	return opcode, payload, nil
}

func pageControlWSHandler(w http.ResponseWriter, r *http.Request) {
	upgrade := strings.ToLower(r.Header.Get("Upgrade"))
	conn := strings.ToLower(r.Header.Get("Connection"))
	key := r.Header.Get("Sec-WebSocket-Key")
	if upgrade != "websocket" || !strings.Contains(conn, "upgrade") || key == "" {
		logMsg("[page-control] ws upgrade missed; upgrade="+upgrade+" connection="+conn, "plugin")
		writeJSON(w, http.StatusBadRequest, map[string]any{"error": "expected websocket upgrade"})
		return
	}
	result, authErr := authenticate(r, true)
	if authErr != nil {
		logMsg("[page-control] ws auth failed: "+authErr.Error(), "plugin")
		writeJSON(w, http.StatusUnauthorized, map[string]any{"error": "unauthorized: " + authErr.Error()})
		return
	}
	if inboundSID := strings.TrimSpace(r.URL.Query().Get("session_id")); inboundSID != "" {
		if !validateInboundSessionID(w, inboundSID, result.Username) {
			return
		}
	}
	sid := deriveSessionIDFromUsername(result.Username)
	if sid == "" {
		writeJSON(w, http.StatusBadRequest, map[string]any{"error": "cannot derive session_id: missing user or AIME_ASSISTANT_ID"})
		return
	}
	var incomingInitTime int64
	if s := strings.TrimSpace(r.URL.Query().Get("init_time")); s != "" {
		if v, err := strconv.ParseInt(s, 10, 64); err == nil {
			incomingInitTime = v
		}
	}

	hj, ok := w.(http.Hijacker)
	if !ok {
		writeJSON(w, http.StatusInternalServerError, map[string]any{"error": "hijack not supported"})
		return
	}
	nc, brw, err := hj.Hijack()
	if err != nil {
		logMsg("[page-control] ws hijack failed: "+err.Error(), "plugin")
		return
	}
	h := sha1.New()
	_, _ = io.WriteString(h, strings.TrimSpace(key)+wsGUID)
	accept := base64.StdEncoding.EncodeToString(h.Sum(nil))
	resp := "HTTP/1.1 101 Switching Protocols\r\n" +
		"Upgrade: websocket\r\n" +
		"Connection: Upgrade\r\n" +
		"Sec-WebSocket-Accept: " + accept + "\r\n\r\n"
	if _, err := brw.WriteString(resp); err != nil {
		_ = nc.Close()
		return
	}
	if err := brw.Flush(); err != nil {
		_ = nc.Close()
		return
	}

	wsc := &pageWSConn{conn: nc, rw: brw}
	if oldSess := pageControlRegistry.get(sid); oldSess != nil {
		oldSess.mu.Lock()
		currentInitTime := oldSess.initTime
		oldSess.mu.Unlock()
		if incomingInitTime < currentInitTime {
			logMsg(fmt.Sprintf("[page-control] ws takeover rejected (incoming=%d < current=%d) sid=%s", incomingInitTime, currentInitTime, sid), "plugin")
			_ = wsc.writeClose()
			_ = nc.Close()
			return
		}
	}
	sess := newPageSession(sid)
	stopCh := make(chan struct{})
	sess.ws = wsc
	sess.wsStop = stopCh
	sess.initTime = incomingInitTime
	pageControlRegistry.register(sess)

	go func(stopCh chan struct{}) {
		_ = wsc.writeText(mustJSON(wsEnvelope{Type: wsTypeHello, Channel: wsChannelPageControl, Payload: map[string]any{"session_id": sid, "server_time": time.Now().Unix()}}))
		for {
			select {
			case <-stopCh:
				return
			case payload, ok := <-sess.out:
				if !ok {
					return
				}
				if err := wsc.writeText(payload); err != nil {
					return
				}
			}
		}
	}(stopCh)

	defer func() {
		sess.mu.Lock()
		isCurrent := sess.ws == wsc
		if isCurrent {
			sess.ws = nil
			sess.wsStop = nil
			sess.closed = true
			sess.resolveAllLocked("session closed")
		}
		sess.mu.Unlock()
		if isCurrent {
			closePageControlStop(stopCh)
			pageControlRegistry.unregister(sess)
			closePageControlOut(sess.out)
		}
	}()

	_ = nc.SetReadDeadline(time.Time{})
	for {
		opcode, data, err := readWSFrame(brw.Reader)
		if err != nil {
			return
		}
		switch opcode {
		case 0x8:
			return
		case 0x9:
			wsc.mu.Lock()
			_ = writeWSFrame(nc, 0xA, data)
			wsc.mu.Unlock()
		case 0x1, 0x2:
			var msg map[string]any
			if err := json.Unmarshal(data, &msg); err != nil {
				continue
			}
			switch mtype, _ := msg["type"].(string); mtype {
			case wsTypeResponse, wsTypeError:
				if id, res, ok := normalizeWSResponse(msg); ok {
					sess.resolve(id, res)
				}
			case wsTypeEvent:
				eventName, _ := msg["event"].(string)
				channel, _ := msg["channel"].(string)
				logMsg(fmt.Sprintf("[ws-relay] event channel=%s event=%s sid=%s", channel, eventName, sid), "plugin")
			case wsTypePing:
				wsc.mu.Lock()
				_ = writeWSFrame(nc, 0x1, []byte(mustJSON(wsEnvelope{Type: wsTypePong, T: time.Now().Unix()})))
				wsc.mu.Unlock()
			}
			sess.touch()
		}
	}
}
