"""Contract tests for the Lanhu development workflow rules."""

import asyncio
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from lanhu_mcp_server import (  # noqa: E402
    DevelopmentRulesError,
    _format_development_rules_context,
    _get_development_rules_path,
    _load_development_rules,
    _prepare_design_html_for_development,
    mcp,
)


class DevelopmentRulesTests(unittest.TestCase):
    def test_external_rules_path_overrides_default(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            rules_path = Path(temp_dir) / "team-rules.md"
            with patch.dict(
                os.environ,
                {"LANHU_DEVELOPMENT_RULES_PATH": str(rules_path)},
            ):
                self.assertEqual(_get_development_rules_path(), rules_path)

    def test_relative_external_rules_path_is_resolved_from_server_directory(self):
        with patch.dict(
            os.environ,
            {"LANHU_DEVELOPMENT_RULES_PATH": "rules/team.md"},
        ):
            self.assertEqual(
                _get_development_rules_path(),
                project_root / "rules" / "team.md",
            )

    def test_load_rules_returns_current_file_content_and_digest(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            rules_path = Path(temp_dir) / "rules.md"
            rules_path.write_text("# Team rules\n\nUse exact spacing.\n", encoding="utf-8")

            result = _load_development_rules(rules_path)

            self.assertEqual(result["content"], "# Team rules\n\nUse exact spacing.\n")
            self.assertEqual(result["source"], str(rules_path))
            self.assertEqual(len(result["sha256"]), 64)

    def test_missing_or_empty_rules_block_development_analysis(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            missing_path = Path(temp_dir) / "missing.md"
            with self.assertRaises(DevelopmentRulesError):
                _load_development_rules(missing_path)

            empty_path = Path(temp_dir) / "empty.md"
            empty_path.write_text("  \n", encoding="utf-8")
            with self.assertRaises(DevelopmentRulesError):
                _load_development_rules(empty_path)

    def test_invalid_utf8_or_oversized_rules_are_rejected_cleanly(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            invalid_path = Path(temp_dir) / "invalid.md"
            invalid_path.write_bytes(b"\xff\xfe")
            with self.assertRaises(DevelopmentRulesError):
                _load_development_rules(invalid_path)

            oversized_path = Path(temp_dir) / "oversized.md"
            oversized_path.write_bytes(b"a" * (256 * 1024 + 1))
            with self.assertRaises(DevelopmentRulesError):
                _load_development_rules(oversized_path)

    def test_default_rules_cover_required_development_constraints(self):
        content = _load_development_rules()["content"]

        required_phrases = (
            "手机状态栏",
            "模块化分析的目的是组件化",
            "文件结构",
            "<业务名称>/",
            "components/",
            "type.ts",
            "database.js",
            "database.ts",
            "hooks/",
            "useTime",
            "带 Tab 的界面结构",
            "Tab 总入口",
            "公共背景",
            "<tab1业务名称>/",
            "<tab2业务名称>/",
            "发现 Tab 后立即创建",
            "即使尚未完成组件分析",
            "每个 Tab 至少创建 index",
            "框架原生最小模板",
            "Vue 的 index.vue",
            "React 的最小 JSX",
            "其他框架的原生页面入口",
            "占位入口",
            "禁止使用 `gap`",
            "首项和末项",
            "尺寸",
            "间距",
            "颜色",
            "模拟数据",
            "列表、表格、网格",
            "一个 Item",
            "循环渲染",
            "固定硬文案",
            "画板坐标",
            "`position: fixed`",
            "`position: sticky`",
            "普通内容流",
            "业务语义",
            "中性名称",
            "额外 DOM",
            "设计基准尺寸",
            "单张设计图",
            "响应式",
            "视觉变体",
            "可见数量",
            "文案长度",
            "安全区",
            "蓝湖图片 URL",
            "资源迁移",
            "不能擅自改用其他图片",
            "界面行为分析",
            "行为标记",
            "Tab 切换",
            "进度条",
            "按钮点击",
            "列表滚动",
            "横向滚动",
            "静态交互逻辑",
            "项目现有编码习惯",
            "不新增依赖",
            "待确认",
        )
        for phrase in required_phrases:
            self.assertIn(phrase, content)

        checklist = content.split("## 9. 开发前检查清单", 1)[1]
        self.assertNotIn("gap", checklist)
        self.assertNotIn("database", checklist)

    def test_design_tool_guidance_blocks_geometry_based_semantic_inference(self):
        tools = {
            tool.name: tool
            for tool in asyncio.run(mcp.list_tools())
        }
        description = tools["lanhu_get_ai_analyze_design_result"].description

        self.assertIn("ARTBOARD POSITION IS NOT RUNTIME POSITIONING", description)
        self.assertIn("fixed/sticky", description)
        self.assertIn("界面行为分析", description)
        self.assertIn("静态交互逻辑", description)
        self.assertIn("行为证据", description)
        self.assertIn("不新增依赖", description)
        self.assertIn("即使尚未完成组件分析", description)
        self.assertIn("框架原生最小模板", description)
        self.assertIn("Vue 的 index.vue", description)
        self.assertNotIn(
            "absolute positioning: left/top values must map to exact offsets",
            description,
        )

        server_source = (project_root / "lanhu_mcp_server.py").read_text(encoding="utf-8")
        self.assertIn("画板坐标", server_source)
        self.assertIn("普通内容流", server_source)
        self.assertIn("STEP 2 - 界面行为分析与行为标记", server_source)
        self.assertIn("静态交互逻辑", server_source)
        self.assertIn("框架原生最小模板", server_source)
        self.assertIn("Vue 的 index.vue", server_source)
        self.assertNotIn("⑤ 绝对定位：left/top 坐标值必须原样映射", server_source)
        self.assertNotIn("如 HTML+CSS 与此处冲突，以此处为准", server_source)

    def test_design_analysis_keeps_lanhu_assets_without_delta_upload_mode(self):
        tools = {
            tool.name: tool
            for tool in asyncio.run(mcp.list_tools())
        }
        analysis_tool = tools["lanhu_get_ai_analyze_design_result"]

        properties = analysis_tool.parameters.get("properties", {})
        self.assertFalse(any("delta" in name.lower() for name in properties))
        self.assertIn("蓝湖", analysis_tool.description)
        self.assertIn("资源", analysis_tool.description)

    def test_rules_context_is_prepended_before_design_analysis(self):
        rules = {
            "source": "/tmp/rules.md",
            "sha256": "a" * 64,
            "content": "# Rules\n\nPlan modules before coding.",
        }

        result = _format_development_rules_context(rules)

        self.assertLess(result.index("# Rules"), result.index("设计分析必须在读取并遵守以上规则后进行"))
        self.assertIn("/tmp/rules.md", result)

    def test_design_html_preserves_source_urls_for_visual_fidelity(self):
        html = (
            '<div><img src="https://cdn.lanhuapp.com/assets/card.png">'
            '<span style="background-image:url(https://lanhu-oss.lanhuapp.com/bg.png)"></span></div>'
        )

        remote_html, future_local_mapping = _prepare_design_html_for_development(
            html,
            "Home",
        )

        self.assertEqual(remote_html, html)
        self.assertIn("https://cdn.lanhuapp.com/assets/card.png", remote_html)
        self.assertIn("https://lanhu-oss.lanhuapp.com/bg.png", remote_html)
        self.assertEqual(
            set(future_local_mapping.values()),
            {
                "https://cdn.lanhuapp.com/assets/card.png",
                "https://lanhu-oss.lanhuapp.com/bg.png",
            },
        )

    def test_mcp_exposes_rules_tool_and_ui_tools_require_it_for_development(self):
        tools = {
            tool.name: tool
            for tool in asyncio.run(mcp.list_tools())
        }

        self.assertIn("lanhu_get_development_rules", tools)
        self.assertIn("开发意图", tools["lanhu_get_development_rules"].description)

        for tool_name in (
            "lanhu_get_designs",
            "lanhu_get_ai_analyze_design_result",
            "lanhu_get_design_slices",
        ):
            description = tools[tool_name].description
            self.assertIn("lanhu_get_development_rules", description)
            self.assertIn("开发", description)

    def test_design_analysis_stops_before_network_when_rules_are_unavailable(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            missing_path = Path(temp_dir) / "missing-rules.md"
            with patch.dict(
                os.environ,
                {"LANHU_DEVELOPMENT_RULES_PATH": str(missing_path)},
            ):
                result = asyncio.run(
                    mcp.call_tool(
                        "lanhu_get_ai_analyze_design_result",
                        {
                            "url": "https://lanhuapp.com/web/#/item/project/stage?pid=never-requested",
                            "design_names": "all",
                        },
                    )
                )

        response_text = result.content[0].text
        self.assertIn("已阻止设计分析", response_text)
        self.assertIn("missing-rules.md", response_text)


if __name__ == "__main__":
    unittest.main()
