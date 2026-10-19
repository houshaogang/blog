# -*- coding: utf-8 -*-
r"""验证 retry_2026-10-18-xie-xie.py：AST(排除docstring) + 正则复扫 + 结构验证 + py_compile + 离线md_to_html"""
import ast, re, py_compile, importlib.util, sys

path = "D:/blog/scripts/retry_2026-10-18-xie-xie.py"
written = open(path, encoding="utf-8").read()
tree = ast.parse(written)  # parse 失败 = docstring 不是 r-string

doc = tree.body[0].value if tree.body and isinstance(tree.body[0], ast.Expr) else None
bad = [n.lineno for n in ast.walk(tree)
       if isinstance(n, ast.Constant) and isinstance(n.value, str)
       and "***" in n.value and n is not doc]
assert not bad, "字符串常量被脱敏污染: %s" % bad

# 正则复扫（单重转义：r'access_token=\*\*\*' 匹配字面三连星）
lines = written.split("\n")
hit = [i + 1 for i, ln in enumerate(lines) if re.search(r'access_token=\*\*\*', ln)]
assert not hit, "正则命中污染行: %s" % hit

# 结构性验证：只打印布尔/计数，绝不打印含 URL 的原文行（显示层脱敏会打码造成假象）
struct_token_url = len([ln for ln in lines if re.search(r'access_token="\s*\+\s*token', ln)])
struct_draft_url = len([ln for ln in lines if re.search(r'draft/add\?access_token="\s*\+\s*token', ln)])
fstring_token = [i + 1 for i, ln in enumerate(lines) if re.search(r'f"[^"]*\{token\}', ln)]
assert struct_token_url >= 1, "未找到字符串拼接 token URL 结构"
assert struct_draft_url == 1, "draft URL 结构数异常: %d" % struct_draft_url
assert not fstring_token, "存在 f-string 插值 token: %s" % fstring_token
print("AST PASS / 正则 PASS / 结构 PASS (token拼接%d处, draft拼接%d处)" % (struct_token_url, struct_draft_url))

py_compile.compile(path, doraise=True)
print("py_compile PASS")

spec = importlib.util.spec_from_file_location("retry_mod", path)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

body = open(mod.ARTICLE, encoding="utf-8").read().split("---", 2)[2].strip()
html = mod.md_to_html(body)
for probe in ["<h2", "<strong>", "<em>", "深夜解忧铺", "你的心事有人听"]:
    assert probe in html, "html 缺少: " + probe
assert "爸，谢谢" in html or "谢谢" in html
print("离线 md_to_html PASS (html %d chars, h2 x%d, strong x%d, em x%d)" % (
    len(html), html.count("<h2"), html.count("<strong>"), html.count("<em>")))
print("ALL_VERIFICATIONS_PASS")
