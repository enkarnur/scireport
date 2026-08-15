package main

import (
	"bytes"
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"net/http"
	"strings"
	"time"
)

type aiSettings struct {
	Provider  string
	BaseURL   string
	Model     string
	APIKey    string
	UpdatedAt string
}

func defaultAISettings() aiSettings {
	return aiSettings{Provider: "openai-compatible", BaseURL: "https://api.openai.com/v1", Model: "gpt-4o-mini"}
}

func findAISettings(ctx context.Context) (map[string]any, error) {
	items, err := store.GetAll(ctx, settingsCollection)
	if err != nil {
		return nil, err
	}
	for _, item := range items {
		if mapString(item, "key") == "ai" {
			return item, nil
		}
	}
	return nil, nil
}

func loadAISettings(ctx context.Context) (aiSettings, error) {
	cfg := defaultAISettings()
	item, err := findAISettings(ctx)
	if err != nil || item == nil {
		return cfg, err
	}
	if v := mapString(item, "provider"); v != "" {
		cfg.Provider = v
	}
	if v := mapString(item, "baseUrl"); v != "" {
		cfg.BaseURL = v
	}
	if v := mapString(item, "model"); v != "" {
		cfg.Model = v
	}
	cfg.APIKey = mapString(item, "apiKey")
	cfg.UpdatedAt = mapString(item, "updatedAt")
	return cfg, nil
}

func requireAISettings(ctx context.Context) (aiSettings, error) {
	cfg, err := loadAISettings(ctx)
	if err != nil {
		return cfg, err
	}
	if strings.TrimSpace(cfg.APIKey) == "" {
		return cfg, errors.New("请先在设置页填写你自己的 AI API Key")
	}
	if strings.TrimSpace(cfg.BaseURL) == "" || strings.TrimSpace(cfg.Model) == "" {
		return cfg, errors.New("请先在设置页填写 AI API Base URL 和模型名称")
	}
	return cfg, nil
}

func publicAISettings(cfg aiSettings) map[string]any {
	return map[string]any{"provider": cfg.Provider, "baseUrl": cfg.BaseURL, "model": cfg.Model, "hasApiKey": strings.TrimSpace(cfg.APIKey) != "", "maskedApiKey": maskSecret(cfg.APIKey), "updatedAt": cfg.UpdatedAt}
}

func maskSecret(secret string) string {
	secret = strings.TrimSpace(secret)
	r := []rune(secret)
	if len(r) == 0 {
		return ""
	}
	if len(r) <= 8 {
		return string(r[:1]) + "…" + string(r[len(r)-1:])
	}
	return string(r[:4]) + "…" + string(r[len(r)-4:])
}

func callUserAI(ctx context.Context, cfg aiSettings, systemPrompt, userPrompt string, maxTokens int) (string, error) {
	endpoint := strings.TrimRight(cfg.BaseURL, "/") + "/chat/completions"
	payload := map[string]any{"model": cfg.Model, "temperature": 0.2, "max_tokens": maxTokens, "messages": []map[string]string{{"role": "system", "content": systemPrompt}, {"role": "user", "content": userPrompt}}}
	body, _ := json.Marshal(payload)
	req, err := http.NewRequestWithContext(ctx, http.MethodPost, endpoint, bytes.NewReader(body))
	if err != nil {
		return "", err
	}
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Authorization", "Bearer "+cfg.APIKey)
	client := &http.Client{Timeout: 45 * time.Second}
	resp, err := client.Do(req)
	if err != nil {
		return "", err
	}
	defer resp.Body.Close()
	respBody, _ := io.ReadAll(io.LimitReader(resp.Body, 2<<20))
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return "", fmt.Errorf("AI API 调用失败，HTTP %d", resp.StatusCode)
	}
	var parsed struct {
		Choices []struct {
			Message struct {
				Content string `json:"content"`
			} `json:"message"`
		} `json:"choices"`
		Error any `json:"error"`
	}
	if err := json.Unmarshal(respBody, &parsed); err != nil {
		return "", errors.New("AI API 返回不是有效 JSON")
	}
	if len(parsed.Choices) == 0 || strings.TrimSpace(parsed.Choices[0].Message.Content) == "" {
		return "", errors.New("AI API 未返回内容")
	}
	return strings.TrimSpace(parsed.Choices[0].Message.Content), nil
}

func extractJSONObject(text string) (map[string]any, error) {
	text = strings.TrimSpace(text)
	start, end := strings.Index(text, "{"), strings.LastIndex(text, "}")
	if start < 0 || end <= start {
		return nil, errors.New("AI 返回内容中没有 JSON 对象")
	}
	var out map[string]any
	if err := json.Unmarshal([]byte(text[start:end+1]), &out); err != nil {
		return nil, err
	}
	return out, nil
}

func aiAnalyzePaper(ctx context.Context, cfg aiSettings, title, fullText string) (map[string]string, error) {
	prompt := "请研读下面论文文本，返回严格 JSON，不要 Markdown。字段必须是 abstract、background、methods、results、discussion，值使用中文总结；如果原文是英文，也要翻译和归纳成中文。不要编造原文没有的结论。\n标题：" + title + "\n论文文本：\n" + compactText(fullText, 12000)
	content, err := callUserAI(ctx, cfg, "你是严谨的学术文献分析助手，只输出合法 JSON。", prompt, 1800)
	if err != nil {
		return nil, err
	}
	obj, err := extractJSONObject(content)
	if err != nil {
		return nil, err
	}
	return map[string]string{"abstract": mapString(obj, "abstract"), "background": mapString(obj, "background"), "methods": mapString(obj, "methods"), "results": mapString(obj, "results"), "discussion": mapString(obj, "discussion")}, nil
}

func aiAnswerQuestion(ctx context.Context, cfg aiSettings, question string, evidences []evidence) (string, error) {
	chunks := []string{}
	for i, ev := range evidences {
		chunks = append(chunks, fmt.Sprintf("[%d] 论文：%s；页码：%d；章节：%s；原文：%s", i+1, ev.PaperTitle, ev.PageNumber, ev.Section, ev.Quote))
	}
	prompt := "问题：" + question + "\n\n请只基于以下文献证据回答，使用中文。回答要直接、结构化，并在句末用 [1] 这样的编号引用证据；不要使用证据之外的信息。\n\n证据：\n" + strings.Join(chunks, "\n")
	return callUserAI(ctx, cfg, "你是文献库问答助手。必须基于给定证据回答，不得编造引用。", prompt, 1600)
}

func aiGenerateReportSections(ctx context.Context, cfg aiSettings, template, question, language string, papers []map[string]any, annotations []map[string]any) ([]any, error) {
	items := []string{}
	for _, p := range papers {
		items = append(items, fmt.Sprintf("论文：%s\n摘要：%s\n背景：%s\n方法：%s\n结果：%s\n讨论：%s", mapString(p, "title"), compactText(mapString(p, "abstract"), 900), compactText(mapString(p, "background"), 900), compactText(mapString(p, "methods"), 900), compactText(mapString(p, "results"), 900), compactText(mapString(p, "discussion"), 900)))
	}
	if len(annotations) > 0 {
		items = append(items, "用户批注：")
	}
	for _, a := range annotations {
		items = append(items, compactText(mapString(a, "content"), 500))
	}
	lang := "中文"
	if !isChineseReport(language) {
		lang = "English"
	}
	prompt := fmt.Sprintf("请生成%s文献报告。模板：%s。研究问题：%s。必须返回严格 JSON：{\"sections\":[{\"key\":\"research-question\",\"title\":\"研究问题\",\"content\":\"...\"}, ...]}。不要 Markdown。中文报告必须用中文分析，不要只是粘贴英文原文。\n\n材料：\n%s", lang, template, question, strings.Join(items, "\n\n"))
	content, err := callUserAI(ctx, cfg, "你是严谨的系统文献报告写作助手，只输出合法 JSON。", prompt, 3000)
	if err != nil {
		return nil, err
	}
	obj, err := extractJSONObject(content)
	if err != nil {
		return nil, err
	}
	sections, ok := obj["sections"].([]any)
	if !ok || len(sections) == 0 {
		return nil, errors.New("AI 返回的报告缺少 sections")
	}
	return sections, nil
}
