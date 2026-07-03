"""
PDF导出服务 - 生成开题报告PDF
使用HTML模板生成，不依赖外部PDF库
"""
import os
from typing import Dict, Optional
from datetime import datetime

class ExportService:
    """导出服务"""

    @staticmethod
    def generate_opening_report(session_data: Dict) -> Dict:
        """
        生成开题报告HTML（可打印为PDF）

        Args:
            session_data: 会话数据，包含选题、研究计划等

        Returns:
            {"success": True, "html": "...", "filename": "..."}
        """
        topic = session_data.get("selected_topic", {})
        plan = session_data.get("research_plan", {})
        major = session_data.get("major", "")
        direction = session_data.get("direction", "")
        dept = session_data.get("dept", "")

        title = topic.get("title", "未命名选题")
        description = topic.get("description", "")
        tags = topic.get("tags", [])
        difficulty = topic.get("difficulty", 3)

        background = plan.get("background", "")
        objectives = plan.get("objectives", [])
        tech_stack = plan.get("tech_stack", [])
        phases = plan.get("phases", [])
        difficulties = plan.get("difficulties", [])
        resources = plan.get("resources", [])

        # 生成HTML报告
        phases_html = ""
        for i, phase in enumerate(phases, 1):
            tasks = "".join(f"<li>{t}</li>" for t in phase.get("tasks", []))
            phases_html += f"""
            <div class="phase">
                <h4>第{i}阶段：{phase.get('name', '')}（{phase.get('duration', '')}）</h4>
                <ul>{tasks}</ul>
            </div>"""

        objectives_html = "".join(f"<li>{obj}</li>" for obj in objectives)
        tech_html = "".join(f"<span class='tag'>{t}</span>" for t in tech_stack)
        tags_html = "".join(f"<span class='tag'>{t}</span>" for t in tags)
        diff_stars = "★" * difficulty + "☆" * (5 - difficulty)

        resources_html = "".join(f"<li>{r}</li>" for r in resources)

        diff_items_html = ""
        for d in difficulties:
            diff_items_html += f"""
            <div class="diff-item">
                <strong>难点：</strong>{d.get('problem', '')}
                <br><strong>解决方案：</strong>{d.get('solution', '')}
            </div>"""

        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>开题报告 - {title}</title>
<style>
@page{{size:A4;margin:2cm}}
body{{font-family:'SimSun','Noto Sans SC',serif;line-height:1.8;color:#333;max-width:800px;margin:0 auto;padding:40px}}
h1{{text-align:center;font-size:22px;margin-bottom:30px;border-bottom:2px solid #333;padding-bottom:10px}}
h2{{font-size:16px;margin:24px 0 12px;color:#1a1a2e;border-left:4px solid #6366f1;padding-left:12px}}
h3{{font-size:14px;margin:16px 0 8px}}
h4{{font-size:13px;margin:12px 0 6px;color:#4f46e5}}
.info-table{{width:100%;border-collapse:collapse;margin-bottom:24px}}
.info-table td{{padding:8px 12px;border:1px solid #ddd;font-size:14px}}
.info-table .label{{background:#f5f5f5;font-weight:bold;width:120px}}
.tag{{display:inline-block;padding:2px 10px;background:#eef2ff;color:#4f46e5;border-radius:12px;font-size:12px;margin:2px}}
.phase{{margin:8px 0;padding:12px;background:#f8f9fa;border-radius:8px}}
.phase ul{{margin:4px 0 0 20px}}
.phase li{{font-size:13px;margin:2px 0}}
.diff-item{{margin:8px 0;padding:10px;background:#fffbeb;border-left:3px solid #f59e0b;border-radius:4px;font-size:13px}}
ul{{margin:8px 0 8px 20px}}
li{{font-size:14px;margin:4px 0}}
.footer{{margin-top:40px;text-align:center;font-size:12px;color:#999;border-top:1px solid #eee;padding-top:16px}}
@media print{{body{{padding:0}}}}
</style>
</head>
<body>
<h1>毕业设计开题报告</h1>
<table class="info-table">
<tr><td class="label">学院</td><td>{dept}</td><td class="label">专业</td><td>{major}</td></tr>
<tr><td class="label">研究方向</td><td>{direction}</td><td class="label">难度</td><td>{diff_stars}</td></tr>
<tr><td class="label">日期</td><td colspan="3">{datetime.now().strftime('%Y年%m月%d日')}</td></tr>
</table>

<h2>一、选题名称</h2>
<h3>{title}</h3>
<p>{description}</p>
<p>技术标签：{tags_html}</p>

<h2>二、研究背景与意义</h2>
<p>{background}</p>

<h2>三、研究目标</h2>
<ul>{objectives_html}</ul>

<h2>四、技术路线</h2>
<p>技术栈：{tech_html}</p>
{phases_html}

<h2>五、预期难点与解决方案</h2>
{diff_items_html}

<h2>六、参考文献与资源</h2>
<ul>{resources_html}</ul>

<div class="footer">
<p>本报告由 AI毕业设计全流程助手 自动生成</p>
<p>生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
</div>
</body>
</html>"""

        filename = f"opening_report_{title[:20]}_{datetime.now().strftime('%Y%m%d')}.html"

        return {
            "success": True,
            "html": html,
            "filename": filename,
            "title": title
        }
