package main

import (
	"archive/zip"
	"bytes"
	"database/sql"
	"encoding/base64"
	"encoding/json"
	"errors"
	"fmt"
	"html"
	"io"
	"math"
	"net/http"
	"path/filepath"
	"regexp"
	"sort"
	"strconv"
	"strings"
	"unicode"
	"unicode/utf8"
)

const (
	papersCollection      = "papers"
	annotationsCollection = "annotations"
	qaCollection          = "qa"
	reportsCollection     = "reports"
	maxRequestBody        = 16 << 20
)

var headingPattern = regexp.MustCompile(`(?i)^\s*(?:\d+(?:\.\d+)*[\s.、)）-]*)?(abstract|summary|摘要|背景|引言|绪论|introduction|background|相关工作|related work|方法|研究方法|methodology|methods?|实验|experiments?|结果|results?|讨论|discussion|结论|conclusion|局限|limitations?)\s*[:：]?\s*$`)

func decodeObject(r *http.Request) (map[string]any, error) {
	dec := json.NewDecoder(io.LimitReader(r.Body, maxRequestBody+1))
	dec.UseNumber()
	var body map[string]any
	if err := dec.Decode(&body); err != nil {
		return nil, errors.New("请求体必须是有效的 JSON 对象")
	}
	if body == nil {
		return nil, errors.New("请求体不能为空")
	}
	var extra any
	if err := dec.Decode(&extra); err != io.EOF {
		return nil, errors.New("请求体只能包含一个 JSON 对象")
	}
	return body, nil
}

func decodeOptionalObject(r *http.Request) (map[string]any, error) {
	if r.Body == nil || r.ContentLength == 0 {
		return map[string]any{}, nil
	}
	body, err := decodeObject(r)
	if err != nil && strings.Contains(err.Error(), "请求体必须是有效的 JSON 对象") {
		return nil, err
	}
	return body, err
}

func badRequest(w http.ResponseWriter, message string) {
	writeJSON(w, http.StatusBadRequest, map[string]any{"error": message})
}
func notFound(w http.ResponseWriter, object string) {
	writeJSON(w, http.StatusNotFound, map[string]any{"error": object + "不存在"})
}
func internalError(w http.ResponseWriter) {
	writeJSON(w, http.StatusInternalServerError, map[string]any{"error": "服务暂时无法完成请求，请稍后重试"})
}

func requiredString(body map[string]any, key, label string) (string, error) {
	value, ok := body[key].(string)
	value = strings.TrimSpace(value)
	if !ok || value == "" {
		return "", fmt.Errorf("%s不能为空", label)
	}
	return value, nil
}

func optionalString(body map[string]any, key string) (string, error) {
	v, exists := body[key]
	if !exists || v == nil {
		return "", nil
	}
	s, ok := v.(string)
	if !ok {
		return "", fmt.Errorf("%s必须是字符串", key)
	}
	return strings.TrimSpace(s), nil
}

func numberValue(v any) (float64, bool) {
	switch n := v.(type) {
	case json.Number:
		f, err := n.Float64()
		return f, err == nil
	case float64:
		return n, true
	case int:
		return float64(n), true
	case int64:
		return float64(n), true
	default:
		return 0, false
	}
}

func intField(body map[string]any, key string, required bool) (int, error) {
	v, exists := body[key]
	if !exists || v == nil {
		if required {
			return 0, fmt.Errorf("%s不能为空", key)
		}
		return 0, nil
	}
	f, ok := numberValue(v)
	if !ok || math.Trunc(f) != f {
		return 0, fmt.Errorf("%s必须是整数", key)
	}
	return int(f), nil
}

func stringArray(body map[string]any, key string, required bool) ([]string, error) {
	v, exists := body[key]
	if !exists || v == nil {
		if required {
			return nil, fmt.Errorf("%s不能为空", key)
		}
		return []string{}, nil
	}
	raw, ok := v.([]any)
	if !ok {
		if vals, yes := v.([]string); yes {
			return vals, nil
		}
		return nil, fmt.Errorf("%s必须是字符串数组", key)
	}
	out := make([]string, 0, len(raw))
	seen := map[string]bool{}
	for _, item := range raw {
		s, ok := item.(string)
		s = strings.TrimSpace(s)
		if !ok || s == "" {
			return nil, fmt.Errorf("%s只能包含非空字符串", key)
		}
		if !seen[s] {
			seen[s] = true
			out = append(out, s)
		}
	}
	return out, nil
}

func boolField(body map[string]any, key string, fallback bool) (bool, error) {
	v, exists := body[key]
	if !exists || v == nil {
		return fallback, nil
	}
	b, ok := v.(bool)
	if !ok {
		return false, fmt.Errorf("%s必须是布尔值", key)
	}
	return b, nil
}

func pagination(r *http.Request, defaultLimit, maxLimit int) (int, int, error) {
	limit, offset := defaultLimit, 0
	if raw := r.URL.Query().Get("limit"); raw != "" {
		n, err := strconv.Atoi(raw)
		if err != nil || n < 1 || n > maxLimit {
			return 0, 0, fmt.Errorf("limit 必须在 1 到 %d 之间", maxLimit)
		}
		limit = n
	}
	if raw := r.URL.Query().Get("offset"); raw != "" {
		n, err := strconv.Atoi(raw)
		if err != nil || n < 0 {
			return 0, 0, errors.New("offset 必须是非负整数")
		}
		offset = n
	}
	return limit, offset, nil
}

func pageSlice(items []map[string]any, offset, limit int) []map[string]any {
	if offset >= len(items) {
		return []map[string]any{}
	}
	end := offset + limit
	if end > len(items) {
		end = len(items)
	}
	return items[offset:end]
}

func mapInt(item map[string]any, key string) int       { f, _ := numberValue(item[key]); return int(f) }
func mapString(item map[string]any, key string) string { s, _ := item[key].(string); return s }
func containsFold(haystack, needle string) bool {
	return strings.Contains(strings.ToLower(haystack), strings.ToLower(strings.TrimSpace(needle)))
}

func publicPaper(item map[string]any, detail bool) map[string]any {
	keys := []string{"id", "title", "authors", "year", "venue", "doi", "abstract", "background", "methods", "results", "discussion", "processingStatus", "processingError", "pageCount", "sourceFileName", "createdAt", "updatedAt"}
	if detail {
		keys = append(keys, "fullText", "pages", "sections")
	}
	out := map[string]any{}
	for _, key := range keys {
		if v, ok := item[key]; ok {
			out[key] = v
		}
	}
	return out
}

func normalizePages(raw any, pageCount int, fullText string) ([]any, error) {
	values, ok := raw.([]any)
	if !ok || len(values) == 0 {
		return nil, errors.New("pages 必须是非空数组")
	}
	if pageCount != len(values) {
		return nil, errors.New("pageCount 必须与 pages 数量一致")
	}
	pages := make([]any, 0, len(values))
	cursor := 0
	for index, value := range values {
		obj, ok := value.(map[string]any)
		if !ok {
			return nil, fmt.Errorf("pages[%d] 必须是对象", index)
		}
		number, err := intField(obj, "pageNumber", true)
		if err != nil || number != index+1 {
			return nil, errors.New("pages 的 pageNumber 必须从 1 开始并连续递增")
		}
		text, ok := obj["text"].(string)
		if !ok {
			return nil, fmt.Errorf("pages[%d].text 必须是字符串", index)
		}
		if cursor > len(fullText) {
			cursor = len(fullText)
		}
		start := cursor
		if pos := strings.Index(fullText[cursor:], text); pos >= 0 {
			start = cursor + pos
		} else if text != "" {
			return nil, fmt.Errorf("pages[%d].text 无法在 fullText 中定位", index)
		}
		end := start + len(text)
		if end > len(fullText) {
			return nil, fmt.Errorf("pages[%d].text 超出 fullText 范围", index)
		}
		cursor = end
		pages = append(pages, map[string]any{"pageNumber": number, "text": text, "startOffset": start, "endOffset": end})
	}
	return pages, nil
}

func sectionKey(heading string) string {
	h := strings.ToLower(strings.TrimSpace(heading))
	switch {
	case strings.Contains(h, "abstract") || strings.Contains(h, "summary") || strings.Contains(h, "摘要"):
		return "abstract"
	case strings.Contains(h, "background") || strings.Contains(h, "introduction") || strings.Contains(h, "背景") || strings.Contains(h, "引言") || strings.Contains(h, "绪论") || strings.Contains(h, "相关工作") || strings.Contains(h, "related"):
		return "background"
	case strings.Contains(h, "method") || strings.Contains(h, "方法") || strings.Contains(h, "实验") || strings.Contains(h, "experiment"):
		return "methods"
	case strings.Contains(h, "result") || strings.Contains(h, "结果"):
		return "results"
	case strings.Contains(h, "discussion") || strings.Contains(h, "conclusion") || strings.Contains(h, "讨论") || strings.Contains(h, "结论") || strings.Contains(h, "局限") || strings.Contains(h, "limitation"):
		return "discussion"
	default:
		return ""
	}
}

func compactText(text string, maxRunes int) string {
	text = strings.Join(strings.Fields(text), " ")
	r := []rune(text)
	if len(r) > maxRunes {
		return string(r[:maxRunes]) + "…"
	}
	return text
}

func splitSentences(text string) []string {
	parts := strings.FieldsFunc(text, func(r rune) bool {
		return r == '。' || r == '！' || r == '？' || r == '.' || r == '!' || r == '?' || r == '\n' || r == '\r'
	})
	out := []string{}
	for _, p := range parts {
		p = strings.TrimSpace(p)
		if utf8.RuneCountInString(p) >= 8 {
			out = append(out, p)
		}
	}
	return out
}

func keywordExtract(text string, words []string, limit int) string {
	matches := []string{}
	for _, sentence := range splitSentences(text) {
		lower := strings.ToLower(sentence)
		for _, word := range words {
			if strings.Contains(lower, word) {
				matches = append(matches, sentence)
				break
			}
		}
		if len(matches) >= limit {
			break
		}
	}
	return compactText(strings.Join(matches, "。"), 1000)
}

func structurePaper(title, text string) (map[string]string, []any) {
	result := map[string]string{"abstract": "", "background": "", "methods": "", "results": "", "discussion": ""}
	sections := []any{}
	lines := strings.Split(strings.ReplaceAll(text, "\r\n", "\n"), "\n")
	current, heading := "", ""
	buffer := []string{}
	offset := 0
	flush := func() {
		content := strings.TrimSpace(strings.Join(buffer, "\n"))
		if current != "" && content != "" {
			if result[current] == "" {
				result[current] = compactText(content, 1800)
			}
			sections = append(sections, map[string]any{"key": current, "title": heading, "content": compactText(content, 4000), "startOffset": offset - len(strings.Join(buffer, "\n"))})
		}
		buffer = nil
	}
	for _, line := range lines {
		trimmed := strings.TrimSpace(line)
		if headingPattern.MatchString(trimmed) {
			flush()
			current, heading, offset = sectionKey(trimmed), trimmed, offset+len(line)+1
			continue
		}
		if current != "" {
			buffer = append(buffer, line)
		}
		offset += len(line) + 1
	}
	flush()
	if result["abstract"] == "" {
		result["abstract"] = keywordExtract(text, []string{"本文", "本研究", "we present", "we propose", "this paper", "objective", "目的"}, 3)
	}
	if result["abstract"] == "" {
		sentences := splitSentences(text)
		if len(sentences) > 0 {
			result["abstract"] = compactText(strings.Join(sentences[:min(3, len(sentences))], "。"), 700)
		}
	}
	if result["background"] == "" {
		result["background"] = keywordExtract(text, []string{"背景", "问题", "挑战", "现有", "however", "challenge", "background", "motivation"}, 5)
	}
	if result["methods"] == "" {
		result["methods"] = keywordExtract(text, []string{"方法", "模型", "算法", "数据集", "实验设计", "we use", "method", "approach", "dataset"}, 6)
	}
	if result["results"] == "" {
		result["results"] = keywordExtract(text, []string{"结果", "提升", "降低", "显著", "准确率", "result", "improve", "outperform", "%"}, 6)
	}
	if result["discussion"] == "" {
		result["discussion"] = keywordExtract(text, []string{"讨论", "结论", "局限", "未来", "表明", "conclusion", "limitation", "future"}, 6)
	}
	_ = title
	return result, sections
}

func textTokens(text string) map[string]float64 {
	text = strings.ToLower(text)
	tokens := map[string]float64{}
	var word []rune
	var han []rune
	flushWord := func() {
		if len(word) >= 2 {
			tokens[string(word)] = 1
		}
		word = nil
	}
	flushHan := func() {
		if len(han) > 0 {
			if len(han) <= 4 {
				tokens[string(han)] = 1.5
			}
			for n := 2; n <= 3; n++ {
				for i := 0; i+n <= len(han); i++ {
					tokens[string(han[i:i+n])] = 1
				}
			}
		}
		han = nil
	}
	for _, r := range text {
		switch {
		case unicode.Is(unicode.Han, r):
			flushWord()
			han = append(han, r)
		case unicode.IsLetter(r) || unicode.IsDigit(r):
			flushHan()
			word = append(word, r)
		default:
			flushWord()
			flushHan()
		}
	}
	flushWord()
	flushHan()
	return tokens
}

func relevance(query, text string) float64 {
	q, d := textTokens(query), textTokens(text)
	if len(q) == 0 {
		return 0
	}
	stop := map[string]bool{"什么": true, "哪些": true, "如何": true, "是否": true, "采用": true, "方法": true, "研究": true, "论文": true, "结果": true}
	score, total, meaningfulMatches := 0.0, 0.0, 0
	lower := strings.ToLower(text)
	for token, weight := range q {
		if stop[token] {
			continue
		}
		total += weight
		if _, ok := d[token]; ok {
			score += weight
			if utf8.RuneCountInString(token) >= 2 {
				meaningfulMatches++
			}
		}
		if utf8.RuneCountInString(token) >= 3 && strings.Contains(lower, token) {
			score += .5 * weight
		}
	}
	if total == 0 {
		return 0
	}
	value := score / (total * 1.25)
	if meaningfulMatches > 0 && value < .2 {
		value = .2
	}
	return math.Min(1, value)
}

type evidence struct {
	PaperID, PaperTitle, Section, Quote string
	PageNumber, StartOffset, EndOffset  int
	Score                               float64
}

func pageEvidence(paper map[string]any, query string) []evidence {
	out := []evidence{}
	pages, _ := paper["pages"].([]any)
	for _, raw := range pages {
		page, ok := raw.(map[string]any)
		if !ok {
			continue
		}
		text := mapString(page, "text")
		base := mapInt(page, "startOffset")
		for _, sentence := range splitSentences(text) {
			score := relevance(query, sentence)
			if score < .12 {
				continue
			}
			local := strings.Index(text, sentence)
			if local < 0 {
				local = 0
			}
			section := inferSection(sentence, paper)
			out = append(out, evidence{mapString(paper, "id"), mapString(paper, "title"), section, compactText(sentence, 240), mapInt(page, "pageNumber"), base + local, base + local + len(sentence), score})
		}
	}
	sort.SliceStable(out, func(i, j int) bool { return out[i].Score > out[j].Score })
	return out
}

func inferSection(text string, paper map[string]any) string {
	best, score := "正文", 0.0
	for _, pair := range []struct{ k, t string }{{"abstract", "摘要"}, {"background", "背景"}, {"methods", "方法"}, {"results", "结果"}, {"discussion", "讨论"}} {
		s := relevance(text, mapString(paper, pair.k))
		if s > score {
			best, score = pair.t, s
		}
	}
	return best
}

func evidenceMap(e evidence) map[string]any {
	return map[string]any{"paperId": e.PaperID, "paperTitle": e.PaperTitle, "pageNumber": e.PageNumber, "section": e.Section, "quote": e.Quote, "startOffset": e.StartOffset, "endOffset": e.EndOffset}
}

func isNotFoundError(err error) bool { return errors.Is(err, sql.ErrNoRows) }

func safeFileName(name, fallback string) (string, error) {
	name = strings.TrimSpace(name)
	if name == "" {
		name = fallback
	}
	if filepath.Base(name) != name || strings.ContainsAny(name, `/\\`) {
		return "", errors.New("fileName 只能是文件名，不能包含路径")
	}
	if !strings.HasSuffix(strings.ToLower(name), ".docx") {
		name += ".docx"
	}
	if utf8.RuneCountInString(name) > 180 {
		return "", errors.New("fileName 过长")
	}
	return name, nil
}

func buildDOCX(report map[string]any) (string, error) {
	var buf bytes.Buffer
	zw := zip.NewWriter(&buf)
	files := map[string]string{
		"[Content_Types].xml": `<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/></Types>`,
		"_rels/.rels":         `<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>`,
	}
	paragraphs := []string{mapString(report, "title")}
	if q := mapString(report, "researchQuestion"); q != "" {
		paragraphs = append(paragraphs, "研究问题："+q)
	}
	if sections, ok := report["sections"].([]any); ok {
		for _, raw := range sections {
			if section, yes := raw.(map[string]any); yes {
				paragraphs = append(paragraphs, mapString(section, "title"), mapString(section, "content"))
			}
		}
	}
	var body strings.Builder
	for _, p := range paragraphs {
		body.WriteString(`<w:p><w:r><w:t xml:space="preserve">` + html.EscapeString(p) + `</w:t></w:r></w:p>`)
	}
	files["word/document.xml"] = `<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body>` + body.String() + `<w:sectPr/></w:body></w:document>`
	for name, content := range files {
		f, err := zw.Create(name)
		if err != nil {
			return "", err
		}
		if _, err = f.Write([]byte(content)); err != nil {
			return "", err
		}
	}
	if err := zw.Close(); err != nil {
		return "", err
	}
	return base64.StdEncoding.EncodeToString(buf.Bytes()), nil
}
