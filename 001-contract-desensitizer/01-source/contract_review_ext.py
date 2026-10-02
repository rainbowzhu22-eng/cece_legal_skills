"""Exact user terms, case numbering, and fail-closed DOCX export for external review."""
from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
import zipfile
from lxml import etree as ET

import contract_sensitive_detector as D


def validate_term(raw):
    if not isinstance(raw, dict):
        raise ValueError("自选字段格式无效")
    label = str(raw.get("label", "")).strip()
    values = raw.get("values", [])
    if not 1 <= len(label) <= 12 or any(c in label for c in "[]#<>\n\r"):
        raise ValueError("字段名称须为 1–12 个字符，且不能包含括号或 #")
    if not isinstance(values, list) or not 1 <= len(values) <= 12:
        raise ValueError("每个字段须填写原文，可另加至多 11 个别名")
    clean = []
    for value in values:
        if not isinstance(value, str) or not 2 <= len(value.strip()) <= 120 or "\n" in value:
            raise ValueError("原文及别名须为 2–120 个字符，且不能跨段")
        value = value.strip()
        if D.is_placeholder(value):
            raise ValueError("不能把占位符作为自选原文")
        if value not in clean:
            clean.append(value)
    return {"id": hashlib.sha256((label + "\0" + clean[0]).encode()).hexdigest()[:16],
            "label": label, "values": clean}


def _custom_type(label):
    for tid, meta in D.TYPE_META.items():
        if meta.label == label:
            return tid
    return "USER_" + hashlib.sha256(label.encode()).hexdigest()[:12].upper()


def litigation_specs():
    """Additional suggestions for litigation review; each remains user-selectable."""
    for tid, label in (("CASE_NUMBER", "案号"), ("COURT_NAME", "法院名称")):
        if tid not in D.TYPE_META:
            D.TYPE_META[tid] = D.TypeMeta(tid, label, "诉讼信息", "high", priority=80)
    return [
        D.RegexSpec("CASE_NUMBER", r"[（(]\d{4}[）)][\u4e00-\u9fff]{1,8}\d{0,8}(?:民|刑|行|执|知|破|赔|特|申)[\u4e00-\u9fff]{0,4}\d{1,9}号", 0.94),
        D.RegexSpec("COURT_NAME", r"[\u4e00-\u9fff]{2,20}(?:人民法院|知识产权法院|互联网法院)", 0.84),
    ]


def add_exact_terms(doc, candidates, terms):
    """User literals take precedence over automatic guesses at the same position."""
    full = "\n".join(b.text.rstrip("\n") for b in doc.blocks)
    spans = []
    pos = 0
    for block in doc.blocks:
        value = block.text.rstrip("\n")
        spans.append((pos, value, block))
        pos += len(value) + 1
    occupied = []
    manual = {}
    for term in sorted(terms, key=lambda t: max((len(v) for v in t.get("values", [])), default=0), reverse=True):
        item = validate_term(term)
        label, canonical = item["label"], item["values"][0]
        tid = _custom_type(label)
        if tid not in D.TYPE_META:
            D.TYPE_META[tid] = D.TypeMeta(tid, label, "用户自选", "high", 2, 2, priority=100)
        candidate = D.Candidate(0, tid, label, "用户自选", "high", canonical,
                                "[已脱敏]", 0.99, ["用户指定的原文或别名"])
        for bi, (start, block_text, block) in enumerate(spans):
            for literal in sorted(item["values"], key=len, reverse=True):
                for match in re.finditer(re.escape(literal), block_text, re.I if literal.isascii() else 0):
                    ls, le = match.span()
                    if literal.isascii() and ((ls and block_text[ls - 1].isalnum()) or
                                              (le < len(block_text) and block_text[le].isalnum())):
                        continue
                    s, e = start + ls, start + le
                    if any(s < oe and os_ < e for os_, oe in occupied):
                        continue
                    occupied.append((s, e))
                    candidate.occurrences.append(D.Occurrence(
                        page=block.page, location=block.location, block_type=block.block_type,
                        start=s, end=e, context=full[max(0, s - 25):min(len(full), e + 25)],
                        text=full[s:e], block_index=bi, local_start=ls, local_end=le,
                        bbox=block.bbox_for_range(ls, le)))
        if candidate.occurrences:
            manual[(tid, canonical)] = candidate
    kept = []
    for candidate in candidates:
        candidate.occurrences = [o for o in candidate.occurrences
                                 if not any(o.start < e and s < o.end for s, e in occupied)]
        if candidate.occurrences:
            kept.append(candidate)
    result = list(manual.values()) + kept
    for i, candidate in enumerate(result, 1):
        candidate.cid = i
    return result


def assign_case_numbers(report, stored):
    """Keep the same exact entity number across documents in one named case."""
    numbers = {(row["type"], row["value"]): row["number"] for row in stored}
    next_by_type = {}
    for (tid, _), n in numbers.items():
        next_by_type[tid] = max(next_by_type.get(tid, 0), n)
    local = D.build_entity_number_map(report["items"])
    groups = {}
    for item in report["items"]:
        tid, value = item["type"], item["value"]
        local_n = local[(tid, D._norm_key(value))]
        group = groups.setdefault((tid, local_n), [])
        group.append(item)
    ordered = sorted(groups.items(), key=lambda pair: min(
        o["offset"][0] for item in pair[1] for o in item["occurrences"]))
    for (tid, _local_n), items in ordered:
        existing = [numbers[(tid, it["value"])] for it in items if (tid, it["value"]) in numbers]
        if not existing and tid == "ORG_NAME":
            related = {n for (stored_type, stored_value), n in numbers.items()
                       if stored_type == tid and any(D._org_same_entity(stored_value, it["value"]) for it in items)}
            if len(related) == 1:
                existing = list(related)
        if existing:
            number = existing[0]
        else:
            next_by_type[tid] = next_by_type.get(tid, 0) + 1
            number = next_by_type[tid]
        for item in items:
            numbers[(tid, item["value"])] = number
    rows = [{"type": t, "value": v, "number": n} for (t, v), n in numbers.items()]
    return rows, numbers


_W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
_MC = "{http://schemas.openxmlformats.org/markup-compatibility/2006}"
_COMMENT_TAGS = {_W + name for name in ("commentReference", "commentRangeStart", "commentRangeEnd")}
_BAD_TAGS = {"ins", "del", "delText", "moveFrom", "moveTo", "moveFromRangeStart", "moveToRangeStart",
             "vanish", "webHidden", "specVanish",
             "footnoteReference", "endnoteReference", "altChunk", "object", "drawing", "pict",
             "fldSimple", "instrText", "sdt", "hyperlink", "customXml", "smartTag",
             "bookmarkStart", "bookmarkEnd"}
_ALLOWED_WORD = re.compile(r"word/(?:document|header\d+|footer\d+|styles|numbering|settings|fontTable|webSettings)\.xml$|word/theme/theme\d+\.xml$")
_REL_NS = "{http://schemas.openxmlformats.org/package/2006/relationships}"
_CT_NS = "{http://schemas.openxmlformats.org/package/2006/content-types}"


def clean_docx(path, originals):
    """Export a plain OOXML subset; reject content we cannot confidently inspect."""
    from docx import Document

    with zipfile.ZipFile(path) as source:
        names = set(source.namelist())
        if "word/document.xml" not in names or "[Content_Types].xml" not in names:
            raise ValueError("DOCX 结构不完整")
        if sum(i.file_size for i in source.infolist()) > 150 * 1024 * 1024:
            raise ValueError("DOCX 解压后过大，不能安全导出")
        allowed = {n for n in names if _ALLOWED_WORD.fullmatch(n)}
        allowed.add("[Content_Types].xml")
        if "_rels/.rels" in names:
            allowed.add("_rels/.rels")
        if "word/_rels/document.xml.rels" in names:
            allowed.add("word/_rels/document.xml.rels")
        payload = {}
        for name in allowed:
            data = source.read(name)
            if name.startswith("word/") and name.endswith(".xml"):
                root = ET.fromstring(data)
                if name in ("word/styles.xml", "word/settings.xml"):
                    if any(e.tag in {_W + "vanish", _W + "webHidden", _W + "specVanish",
                                      _W + "rPrChange", _W + "pPrChange"}
                           for e in root.iter()):
                        raise ValueError("文档样式或设置含隐藏文字或未接受的修订，需先在 Word 中处理")
                if name == "word/document.xml" or re.fullmatch(r"word/(?:header|footer)\d+\.xml", name):
                    for parent in root.iter():
                        for child in list(parent):
                            if child.tag in _COMMENT_TAGS:
                                parent.remove(child)
                    bad = [e.tag.rsplit("}", 1)[-1] for e in root.iter()
                           if (e.tag.startswith(_W) and e.tag.rsplit("}", 1)[-1] in _BAD_TAGS)
                           or e.tag.startswith(_MC)]
                    if bad:
                        raise ValueError("文档含批注、修订、隐藏文字、图片或复杂对象（%s）；请在 Word 中处理后重试" % bad[0])
                    for element in root.iter():
                        if element.tag != _W + "t" and element.text:
                            if any(value and value in element.text for value in originals):
                                raise ValueError("已选原文仍存在于非正文 XML 中")
                        if any(value and value in attr for attr in element.attrib.values() for value in originals):
                            raise ValueError("已选原文仍存在于 XML 属性中")
                data = ET.tostring(root, encoding="utf-8", xml_declaration=True)
            payload[name] = data
        for rel_name in ("_rels/.rels", "word/_rels/document.xml.rels"):
            if rel_name not in payload:
                continue
            root = ET.fromstring(payload[rel_name])
            for rel in list(root):
                target = rel.get("Target", "")
                if rel.get("TargetMode") == "External":
                    raise ValueError("文档含外部链接，需先移除")
                base = "word" if rel_name.startswith("word/") else ""
                resolved = os.path.normpath(os.path.join(base, target.lstrip("/"))).replace("\\", "/")
                if resolved.startswith("../"):
                    raise ValueError("DOCX 关系路径无效")
                if resolved not in allowed:
                    root.remove(rel)  # detached metadata/unsupported part is excluded from clean copy
            payload[rel_name] = ET.tostring(root, encoding="utf-8", xml_declaration=True)
        root = ET.fromstring(payload["[Content_Types].xml"])
        for child in list(root):
            if child.tag == _CT_NS + "Override" and child.get("PartName", "").lstrip("/") not in allowed:
                root.remove(child)
        payload["[Content_Types].xml"] = ET.tostring(root, encoding="utf-8", xml_declaration=True)
        # Inspect visible XML, style/setting attributes, and every retained part.
        for name, data in payload.items():
            if name == "word/document.xml" or re.fullmatch(r"word/(?:header|footer)\d+\.xml", name):
                continue  # visible text is controlled by the user's per-occurrence review
            decoded = data.decode("utf-8", "ignore")
            for value in originals:
                if value and value in decoded:
                    raise ValueError("导出件仍含已选原文：%s" % name)
        fd, tmp = tempfile.mkstemp(suffix=".docx", dir=os.path.dirname(path))
        os.close(fd)
        try:
            with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as target:
                for name, data in payload.items():
                    target.writestr(name, data)
            Document(tmp)  # fail before replacing the redacted result
            os.replace(tmp, path)
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)
