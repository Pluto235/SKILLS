#!/usr/bin/env python3
"""Inject a local, file:// friendly annotation layer into a static HTML report."""

from __future__ import annotations

import re
import sys
from pathlib import Path


CSS_START = "<!-- LOCAL_ANNOTATIONS_CSS_START -->"
CSS_END = "<!-- LOCAL_ANNOTATIONS_CSS_END -->"
JS_START = "<!-- LOCAL_ANNOTATIONS_JS_START -->"
JS_END = "<!-- LOCAL_ANNOTATIONS_JS_END -->"


ANNOTATION_CSS = r"""
<style>
.snga-toggle {
  position: fixed;
  right: 18px;
  bottom: 18px;
  z-index: 9998;
  border: 1px solid #d7dce2;
  border-radius: 999px;
  background: #111827;
  color: #fff;
  box-shadow: 0 12px 32px rgba(15, 23, 42, 0.22);
  cursor: pointer;
  font: 600 14px/1.2 ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  padding: 11px 14px;
}
.snga-toggle:hover {
  background: #0f766e;
}
.snga-toggle-count {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 18px;
  height: 18px;
  margin-left: 6px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.18);
  font-size: 12px;
}
.snga-panel {
  position: fixed;
  top: 0;
  right: 0;
  bottom: 0;
  z-index: 9997;
  width: min(390px, calc(100vw - 28px));
  display: flex;
  flex-direction: column;
  background: #fbfbfa;
  border-left: 1px solid #d8dee4;
  box-shadow: -18px 0 44px rgba(15, 23, 42, 0.16);
  transform: translateX(104%);
  transition: transform 180ms ease;
}
body.snga-panel-open .snga-panel {
  transform: translateX(0);
}
.snga-panel-header {
  padding: 16px 16px 12px;
  border-bottom: 1px solid #e5e7eb;
  background: #fff;
}
.snga-panel-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  font-size: 15px;
  font-weight: 750;
  color: #111827;
}
.snga-close {
  border: 0;
  border-radius: 8px;
  background: transparent;
  color: #475569;
  cursor: pointer;
  font-size: 20px;
  line-height: 1;
  padding: 2px 7px 4px;
}
.snga-close:hover {
  background: #f1f5f9;
}
.snga-help {
  margin-top: 8px;
  color: #64748b;
  font-size: 12px;
  line-height: 1.55;
}
.snga-actions {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 8px;
  margin-top: 12px;
}
.snga-action {
  border: 1px solid #d7dce2;
  border-radius: 9px;
  background: #fff;
  color: #334155;
  cursor: pointer;
  font-size: 12px;
  font-weight: 650;
  padding: 7px 8px;
}
.snga-action:hover {
  background: #f8fafc;
  border-color: #94a3b8;
}
.snga-action-danger:hover {
  color: #b91c1c;
  border-color: #fecaca;
  background: #fff7f7;
}
.snga-list {
  flex: 1;
  overflow: auto;
  padding: 12px;
}
.snga-empty {
  border: 1px dashed #cbd5e1;
  border-radius: 12px;
  color: #64748b;
  font-size: 13px;
  line-height: 1.7;
  padding: 14px;
  background: #fff;
}
.snga-card {
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  background: #fff;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
  margin-bottom: 10px;
  padding: 11px;
}
.snga-card-active {
  border-color: #0f766e;
  box-shadow: 0 0 0 2px rgba(15, 118, 110, 0.14);
}
.snga-card-meta {
  color: #64748b;
  font-size: 11px;
  line-height: 1.45;
  margin-bottom: 7px;
}
.snga-card-quote {
  border-left: 3px solid #f59e0b;
  color: #334155;
  font-size: 12px;
  line-height: 1.55;
  margin: 7px 0;
  max-height: 110px;
  overflow: auto;
  padding-left: 8px;
}
.snga-card-note {
  color: #0f172a;
  font-size: 13px;
  line-height: 1.6;
  white-space: pre-wrap;
}
.snga-card-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 9px;
}
.snga-mini {
  border: 1px solid #d7dce2;
  border-radius: 8px;
  background: #fff;
  color: #334155;
  cursor: pointer;
  font-size: 12px;
  padding: 5px 7px;
}
.snga-mini:hover {
  background: #f8fafc;
}
.snga-mini-danger:hover {
  color: #b91c1c;
  border-color: #fecaca;
}
.snga-highlight {
  border-radius: 3px;
  background: linear-gradient(180deg, rgba(254, 240, 138, 0.34), rgba(250, 204, 21, 0.42));
  box-shadow: inset 0 -0.08em 0 rgba(234, 179, 8, 0.55);
  cursor: pointer;
  padding: 0 1px;
}
.snga-highlight-active {
  background: linear-gradient(180deg, rgba(153, 246, 228, 0.58), rgba(45, 212, 191, 0.48));
  box-shadow: 0 0 0 2px rgba(15, 118, 110, 0.22);
}
.snga-selection-toolbar {
  position: fixed;
  z-index: 9999;
  display: none;
  border: 1px solid rgba(15, 23, 42, 0.12);
  border-radius: 999px;
  background: #111827;
  box-shadow: 0 10px 28px rgba(15, 23, 42, 0.24);
  padding: 5px;
}
.snga-selection-toolbar button {
  border: 0;
  border-radius: 999px;
  background: transparent;
  color: #fff;
  cursor: pointer;
  font-size: 13px;
  font-weight: 700;
  padding: 7px 10px;
}
.snga-selection-toolbar button:hover {
  background: rgba(255, 255, 255, 0.16);
}
.snga-composer {
  position: fixed;
  inset: 0;
  z-index: 10000;
  display: none;
  align-items: center;
  justify-content: center;
  background: rgba(15, 23, 42, 0.26);
  padding: 18px;
}
.snga-composer-card {
  width: min(560px, 100%);
  border-radius: 16px;
  background: #fff;
  box-shadow: 0 24px 80px rgba(15, 23, 42, 0.28);
  padding: 16px;
}
.snga-composer-title {
  font-size: 16px;
  font-weight: 750;
  color: #111827;
}
.snga-composer-quote {
  border-left: 3px solid #f59e0b;
  color: #475569;
  font-size: 13px;
  line-height: 1.6;
  margin: 12px 0;
  max-height: 120px;
  overflow: auto;
  padding-left: 10px;
}
.snga-composer textarea {
  width: 100%;
  min-height: 120px;
  box-sizing: border-box;
  border: 1px solid #cbd5e1;
  border-radius: 10px;
  color: #111827;
  font: 14px/1.55 ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  padding: 10px;
  resize: vertical;
}
.snga-composer textarea:focus {
  border-color: #0f766e;
  box-shadow: 0 0 0 3px rgba(15, 118, 110, 0.14);
  outline: none;
}
.snga-composer-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 12px;
}
.snga-primary,
.snga-secondary {
  border: 1px solid #d7dce2;
  border-radius: 9px;
  cursor: pointer;
  font-size: 13px;
  font-weight: 700;
  padding: 8px 11px;
}
.snga-primary {
  border-color: #0f766e;
  background: #0f766e;
  color: #fff;
}
.snga-primary:hover {
  background: #115e59;
}
.snga-secondary {
  background: #fff;
  color: #334155;
}
.snga-secondary:hover {
  background: #f8fafc;
}
.snga-toast {
  position: fixed;
  left: 50%;
  bottom: 24px;
  z-index: 10001;
  display: none;
  transform: translateX(-50%);
  border-radius: 999px;
  background: #111827;
  color: #fff;
  box-shadow: 0 12px 32px rgba(15, 23, 42, 0.22);
  font-size: 13px;
  padding: 9px 13px;
}
@media (max-width: 760px) {
  .snga-panel {
    width: 100vw;
  }
  .snga-actions {
    grid-template-columns: 1fr;
  }
}
@media print {
  .snga-toggle,
  .snga-panel,
  .snga-selection-toolbar,
  .snga-composer,
  .snga-toast {
    display: none !important;
  }
}
</style>
"""


ANNOTATION_JS = r"""
<script>
(() => {
  if (window.__SNGAMMA_LOCAL_ANNOTATIONS__) return;
  window.__SNGAMMA_LOCAL_ANNOTATIONS__ = true;

  const docBody = document.querySelector(".doc-body");
  if (!docBody) return;

  const STORAGE_KEY = "sngamma.localAnnotations:" + location.pathname;
  const BLOCK_SELECTOR = "p, li, td, th, h1, h2, h3, h4, blockquote, pre, figcaption";
  let annotations = loadAnnotations();
  let draftSelection = null;
  let activeId = null;

  const ui = document.createElement("div");
  ui.innerHTML = `
    <button class="snga-toggle" type="button" aria-label="打开本地批注面板">批注 <span class="snga-toggle-count">0</span></button>
    <aside class="snga-panel" aria-label="本地批注面板">
      <div class="snga-panel-header">
        <div class="snga-panel-title">
          <span>本地批注</span>
          <button class="snga-close" type="button" aria-label="关闭批注面板">×</button>
        </div>
        <div class="snga-help">选中正文文字后点击“添加批注”。批注保存在当前浏览器的 localStorage；导出 JSON 后才是可迁移备份。</div>
        <div class="snga-actions">
          <button class="snga-action" type="button" data-action="export">导出 JSON</button>
          <button class="snga-action" type="button" data-action="import">导入 JSON</button>
          <button class="snga-action snga-action-danger" type="button" data-action="clear">清空</button>
        </div>
      </div>
      <div class="snga-list"></div>
      <input class="snga-import-input" type="file" accept="application/json,.json" hidden>
    </aside>
    <div class="snga-selection-toolbar"><button type="button">添加批注</button></div>
    <div class="snga-composer" role="dialog" aria-modal="true" aria-label="添加批注">
      <div class="snga-composer-card">
        <div class="snga-composer-title">添加批注</div>
        <div class="snga-composer-quote"></div>
        <textarea class="snga-note-input" placeholder="写下你的批注、疑问或后续行动..."></textarea>
        <div class="snga-composer-actions">
          <button class="snga-secondary" type="button" data-action="cancel-compose">取消</button>
          <button class="snga-primary" type="button" data-action="save-compose">保存批注</button>
        </div>
      </div>
    </div>
    <div class="snga-toast" role="status" aria-live="polite"></div>
  `;
  document.body.appendChild(ui);

  const toggle = ui.querySelector(".snga-toggle");
  const countEl = ui.querySelector(".snga-toggle-count");
  const panel = ui.querySelector(".snga-panel");
  const closeBtn = ui.querySelector(".snga-close");
  const listEl = ui.querySelector(".snga-list");
  const toolbar = ui.querySelector(".snga-selection-toolbar");
  const toolbarBtn = toolbar.querySelector("button");
  const composer = ui.querySelector(".snga-composer");
  const composerQuote = ui.querySelector(".snga-composer-quote");
  const noteInput = ui.querySelector(".snga-note-input");
  const importInput = ui.querySelector(".snga-import-input");
  const toastEl = ui.querySelector(".snga-toast");

  toggle.addEventListener("click", () => setPanelOpen(!document.body.classList.contains("snga-panel-open")));
  closeBtn.addEventListener("click", () => setPanelOpen(false));
  toolbarBtn.addEventListener("click", () => {
    const info = readCurrentSelection();
    hideToolbar();
    if (info) openComposer(info);
  });

  document.addEventListener("mouseup", () => setTimeout(updateSelectionToolbar, 0));
  document.addEventListener("keyup", (event) => {
    if (event.key === "Escape") {
      hideToolbar();
      closeComposer();
      return;
    }
    updateSelectionToolbar();
  });
  document.addEventListener("selectionchange", () => {
    if (!window.getSelection()?.toString()) hideToolbar();
  });
  window.addEventListener("resize", hideToolbar);
  window.addEventListener("scroll", hideToolbar, true);

  composer.addEventListener("click", (event) => {
    if (event.target === composer) closeComposer();
  });
  composer.querySelector('[data-action="cancel-compose"]').addEventListener("click", closeComposer);
  composer.querySelector('[data-action="save-compose"]').addEventListener("click", saveComposer);
  noteInput.addEventListener("keydown", (event) => {
    if ((event.metaKey || event.ctrlKey) && event.key === "Enter") saveComposer();
  });

  panel.addEventListener("click", (event) => {
    const actionEl = event.target.closest("[data-action]");
    if (!actionEl) return;
    const action = actionEl.dataset.action;
    if (action === "export") exportAnnotations();
    if (action === "import") importInput.click();
    if (action === "clear") clearAnnotations();
    const id = actionEl.closest("[data-id]")?.dataset.id;
    if (action === "locate" && id) locateAnnotation(id);
    if (action === "edit" && id) editAnnotation(id);
    if (action === "delete" && id) deleteAnnotation(id);
  });

  importInput.addEventListener("change", importAnnotations);
  docBody.addEventListener("click", (event) => {
    const mark = event.target.closest(".snga-highlight");
    if (!mark) return;
    selectAnnotation(mark.dataset.annotationId, true);
  });

  renderAll();

  window.SNgammaAnnotations = {
    list: () => [...annotations],
    export: exportAnnotations,
    clear: clearAnnotations,
    rerender: renderAll,
    storageKey: STORAGE_KEY,
  };

  function setPanelOpen(open) {
    document.body.classList.toggle("snga-panel-open", open);
  }

  function loadAnnotations() {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      const parsed = raw ? JSON.parse(raw) : [];
      return Array.isArray(parsed) ? parsed : [];
    } catch (error) {
      console.warn("Failed to load annotations", error);
      return [];
    }
  }

  function saveAnnotations() {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(annotations));
  }

  function normalizeText(value) {
    return String(value || "").replace(/\s+/g, " ").trim();
  }

  function escapeHtml(value) {
    return String(value || "").replace(/[&<>"']/g, (ch) => ({
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      '"': "&quot;",
      "'": "&#39;",
    })[ch]);
  }

  function parentElement(node) {
    return node?.nodeType === Node.ELEMENT_NODE ? node : node?.parentElement;
  }

  function cssPathWithinDoc(element) {
    if (!element || element === docBody) return "";
    const parts = [];
    let current = element;
    while (current && current !== docBody) {
      const tag = current.tagName.toLowerCase();
      const siblings = Array.from(current.parentElement?.children || []).filter((el) => el.tagName === current.tagName);
      const index = siblings.indexOf(current) + 1;
      parts.unshift(`${tag}:nth-of-type(${index})`);
      current = current.parentElement;
    }
    return parts.join(" > ");
  }

  function elementFromPath(path) {
    if (!path) return docBody;
    try {
      return docBody.querySelector(path) || docBody;
    } catch {
      return docBody;
    }
  }

  function previousHeading(element) {
    let current = element;
    while (current && current !== docBody) {
      let sibling = current.previousElementSibling;
      while (sibling) {
        if (/^H[23]$/.test(sibling.tagName)) return sibling;
        const nested = Array.from(sibling.querySelectorAll("h2, h3")).pop();
        if (nested) return nested;
        sibling = sibling.previousElementSibling;
      }
      current = current.parentElement;
    }
    return docBody.querySelector("h2, h3");
  }

  function blockForRange(range) {
    const startEl = parentElement(range.startContainer);
    const endEl = parentElement(range.endContainer);
    let block = startEl?.closest(BLOCK_SELECTOR);
    while (block && endEl && !block.contains(endEl)) {
      block = block.parentElement?.closest(BLOCK_SELECTOR);
    }
    return block && docBody.contains(block) ? block : docBody;
  }

  function countOccurrences(haystack, needle) {
    if (!needle) return 0;
    let count = 0;
    let index = haystack.indexOf(needle);
    while (index !== -1) {
      count += 1;
      index = haystack.indexOf(needle, index + Math.max(needle.length, 1));
    }
    return count;
  }

  function readCurrentSelection() {
    const selection = window.getSelection();
    if (!selection || selection.rangeCount === 0 || selection.isCollapsed) return null;
    const range = selection.getRangeAt(0);
    if (!docBody.contains(range.commonAncestorContainer)) return null;
    const rawText = range.toString();
    const text = normalizeText(rawText);
    if (!text) return null;

    const block = blockForRange(range);
    const heading = previousHeading(block);
    const preRange = document.createRange();
    preRange.selectNodeContents(block);
    try {
      preRange.setEnd(range.startContainer, range.startOffset);
    } catch {
      preRange.setEndBefore(block.firstChild || block);
    }
    const occurrence = countOccurrences(preRange.toString(), rawText);

    return {
      id: "ann-" + Date.now().toString(36) + "-" + Math.random().toString(36).slice(2, 8),
      text: rawText,
      displayText: text,
      note: "",
      blockPath: cssPathWithinDoc(block),
      sectionId: heading?.id || "",
      sectionTitle: normalizeText(heading?.textContent || "未定位章节"),
      occurrence,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      url: location.href,
      title: document.title,
    };
  }

  function updateSelectionToolbar() {
    const selection = window.getSelection();
    if (!selection || selection.rangeCount === 0 || selection.isCollapsed) {
      hideToolbar();
      return;
    }
    const range = selection.getRangeAt(0);
    if (!docBody.contains(range.commonAncestorContainer) || !normalizeText(selection.toString())) {
      hideToolbar();
      return;
    }
    const rect = range.getBoundingClientRect();
    if (!rect || rect.width === 0 || rect.height === 0) {
      hideToolbar();
      return;
    }
    toolbar.style.display = "block";
    const top = Math.max(12, rect.top - toolbar.offsetHeight - 10);
    const left = Math.min(window.innerWidth - toolbar.offsetWidth - 12, Math.max(12, rect.left + rect.width / 2 - toolbar.offsetWidth / 2));
    toolbar.style.top = `${top}px`;
    toolbar.style.left = `${left}px`;
  }

  function hideToolbar() {
    toolbar.style.display = "none";
  }

  function openComposer(info) {
    draftSelection = info;
    composerQuote.textContent = info.displayText;
    noteInput.value = "";
    composer.style.display = "flex";
    setTimeout(() => noteInput.focus(), 0);
  }

  function closeComposer() {
    composer.style.display = "none";
    draftSelection = null;
    noteInput.value = "";
  }

  function saveComposer() {
    if (!draftSelection) return;
    const note = noteInput.value.trim();
    if (!note) {
      showToast("批注内容不能为空。");
      noteInput.focus();
      return;
    }
    draftSelection.note = note;
    draftSelection.updatedAt = new Date().toISOString();
    annotations.unshift(draftSelection);
    saveAnnotations();
    closeComposer();
    window.getSelection()?.removeAllRanges();
    renderAll();
    selectAnnotation(annotations[0].id, true);
    setPanelOpen(true);
    showToast("批注已保存。");
  }

  function clearHighlightSpans() {
    docBody.querySelectorAll(".snga-highlight").forEach((mark) => {
      const parent = mark.parentNode;
      while (mark.firstChild) parent.insertBefore(mark.firstChild, mark);
      parent.removeChild(mark);
      parent.normalize();
    });
  }

  function textRangeFromIndex(root, start, end) {
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, {
      acceptNode(node) {
        const parent = node.parentElement;
        if (!parent) return NodeFilter.FILTER_REJECT;
        if (parent.closest("script, style, .snga-highlight")) return NodeFilter.FILTER_REJECT;
        return NodeFilter.FILTER_ACCEPT;
      },
    });
    let position = 0;
    let startNode = null;
    let startOffset = 0;
    let endNode = null;
    let endOffset = 0;
    let node;
    while ((node = walker.nextNode())) {
      const next = position + node.nodeValue.length;
      if (!startNode && start >= position && start <= next) {
        startNode = node;
        startOffset = start - position;
      }
      if (!endNode && end >= position && end <= next) {
        endNode = node;
        endOffset = end - position;
        break;
      }
      position = next;
    }
    if (!startNode || !endNode) return null;
    const range = document.createRange();
    range.setStart(startNode, startOffset);
    range.setEnd(endNode, endOffset);
    return range;
  }

  function findAnnotationRange(annotation) {
    const root = elementFromPath(annotation.blockPath);
    const text = annotation.text || annotation.displayText;
    if (!text) return null;
    const content = root.textContent || "";
    let from = 0;
    let index = -1;
    const occurrence = Number.isFinite(annotation.occurrence) ? annotation.occurrence : 0;
    for (let i = 0; i <= occurrence; i += 1) {
      index = content.indexOf(text, from);
      if (index === -1) break;
      from = index + Math.max(text.length, 1);
    }
    if (index === -1) {
      index = content.indexOf(text);
    }
    if (index === -1 && annotation.displayText) {
      const compactNeedle = normalizeText(annotation.displayText);
      const compactContent = normalizeText(content);
      const compactIndex = compactContent.indexOf(compactNeedle);
      if (compactIndex === -1) return null;
      return null;
    }
    if (index === -1) return null;
    return textRangeFromIndex(root, index, index + text.length);
  }

  function applyHighlight(annotation) {
    const range = findAnnotationRange(annotation);
    if (!range) return false;
    const mark = document.createElement("mark");
    mark.className = "snga-highlight";
    mark.dataset.annotationId = annotation.id;
    mark.title = annotation.note || "本地批注";
    try {
      const fragment = range.extractContents();
      mark.appendChild(fragment);
      range.insertNode(mark);
      return true;
    } catch (error) {
      console.warn("Failed to apply annotation highlight", annotation, error);
      return false;
    }
  }

  function renderHighlights() {
    clearHighlightSpans();
    [...annotations].reverse().forEach(applyHighlight);
    if (activeId) {
      docBody.querySelectorAll(`.snga-highlight[data-annotation-id="${CSS.escape(activeId)}"]`).forEach((el) => {
        el.classList.add("snga-highlight-active");
      });
    }
  }

  function renderList() {
    countEl.textContent = String(annotations.length);
    if (annotations.length === 0) {
      listEl.innerHTML = `<div class="snga-empty">暂无批注。选中报告正文中的一段文字，会出现“添加批注”按钮。</div>`;
      return;
    }
    listEl.innerHTML = annotations.map((ann) => `
      <article class="snga-card ${ann.id === activeId ? "snga-card-active" : ""}" data-id="${escapeHtml(ann.id)}">
        <div class="snga-card-meta">${escapeHtml(ann.sectionTitle || "未定位章节")} · ${escapeHtml(formatTime(ann.updatedAt || ann.createdAt))}</div>
        <div class="snga-card-quote">${escapeHtml(ann.displayText || ann.text || "")}</div>
        <div class="snga-card-note">${escapeHtml(ann.note || "")}</div>
        <div class="snga-card-actions">
          <button class="snga-mini" type="button" data-action="locate">定位</button>
          <button class="snga-mini" type="button" data-action="edit">编辑</button>
          <button class="snga-mini snga-mini-danger" type="button" data-action="delete">删除</button>
        </div>
      </article>
    `).join("");
  }

  function renderAll() {
    renderHighlights();
    renderList();
  }

  function selectAnnotation(id, openPanel) {
    activeId = id;
    if (openPanel) setPanelOpen(true);
    renderAll();
    const card = listEl.querySelector(`[data-id="${CSS.escape(id)}"]`);
    if (card) card.classList.add("snga-card-active");
  }

  function locateAnnotation(id) {
    selectAnnotation(id, true);
    const mark = docBody.querySelector(`.snga-highlight[data-annotation-id="${CSS.escape(id)}"]`);
    if (mark) {
      mark.scrollIntoView({ behavior: "smooth", block: "center" });
      showToast("已定位到批注位置。");
    } else {
      showToast("未能重新匹配原文。可查看批注卡片中的原始选中文本。");
    }
  }

  function editAnnotation(id) {
    const ann = annotations.find((item) => item.id === id);
    if (!ann) return;
    const next = prompt("编辑批注：", ann.note || "");
    if (next === null) return;
    ann.note = next.trim();
    ann.updatedAt = new Date().toISOString();
    saveAnnotations();
    renderAll();
    showToast("批注已更新。");
  }

  function deleteAnnotation(id) {
    if (!confirm("删除这条批注？")) return;
    annotations = annotations.filter((item) => item.id !== id);
    if (activeId === id) activeId = null;
    saveAnnotations();
    renderAll();
    showToast("批注已删除。");
  }

  function clearAnnotations() {
    if (annotations.length === 0) return;
    if (!confirm("清空当前报告的所有本地批注？建议先导出 JSON 备份。")) return;
    annotations = [];
    activeId = null;
    saveAnnotations();
    renderAll();
    showToast("批注已清空。");
  }

  function exportAnnotations() {
    const payload = {
      schema: "sngamma-local-annotations-v1",
      exportedAt: new Date().toISOString(),
      title: document.title,
      url: location.href,
      storageKey: STORAGE_KEY,
      annotations,
    };
    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    const date = new Date().toISOString().slice(0, 10);
    link.href = url;
    link.download = `sngamma_annotations_${date}.json`;
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
    showToast("批注 JSON 已导出。");
  }

  async function importAnnotations(event) {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (!file) return;
    try {
      const payload = JSON.parse(await file.text());
      const incoming = Array.isArray(payload) ? payload : payload.annotations;
      if (!Array.isArray(incoming)) throw new Error("Invalid annotation JSON");
      const existing = new Set(annotations.map((item) => item.id));
      const cleaned = incoming.filter((item) => item && item.id && !existing.has(item.id));
      annotations = [...cleaned, ...annotations];
      saveAnnotations();
      renderAll();
      showToast(`已导入 ${cleaned.length} 条批注。`);
    } catch (error) {
      console.error(error);
      showToast("导入失败：JSON 格式不符合批注结构。");
    }
  }

  function formatTime(value) {
    if (!value) return "";
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return value;
    return date.toLocaleString("zh-CN", { hour12: false });
  }

  let toastTimer = null;
  function showToast(message) {
    toastEl.textContent = message;
    toastEl.style.display = "block";
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => {
      toastEl.style.display = "none";
    }, 2200);
  }
})();
</script>
"""


def strip_block(text: str, start: str, end: str) -> str:
    pattern = re.compile(re.escape(start) + r".*?" + re.escape(end) + r"\s*", re.S)
    return pattern.sub("", text)


def inject(html_path: Path) -> None:
    text = html_path.read_text(encoding="utf-8")
    text = strip_block(text, CSS_START, CSS_END)
    text = strip_block(text, JS_START, JS_END)

    css_block = f"{CSS_START}\n{ANNOTATION_CSS.strip()}\n{CSS_END}\n"
    js_block = f"{JS_START}\n{ANNOTATION_JS.strip()}\n{JS_END}\n"

    if "</head>" not in text or "</body>" not in text:
        raise SystemExit(f"{html_path} does not look like a complete HTML document")

    text = text.replace("</head>", css_block + "</head>", 1)
    text = text.replace("</body>", js_block + "</body>", 1)
    html_path.write_text(text, encoding="utf-8")


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("Usage: scripts/inject_local_annotations.py REPORT.html")
    inject(Path(sys.argv[1]).resolve())


if __name__ == "__main__":
    main()
