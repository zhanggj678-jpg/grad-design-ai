"""
数据分析服务 - CSV数据处理、统计分析、图表生成
使用Pandas + 自定义统计，不依赖Scikit-learn（减少依赖）
"""
import io
import json
from typing import Dict, List, Optional, Any

from core.agent import get_agent
from database.crud import (
    SessionCRUD, AnalysisCRUD, LogCRUD
)


class AnalysisService:
    """数据分析服务"""

    @staticmethod
    def analyze_csv(session_id: str, filename: str, csv_content: str) -> Dict:
        """
        分析CSV文件

        Args:
            session_id: 会话ID
            filename: 文件名
            csv_content: CSV文本内容

        Returns:
            分析结果字典
        """
        try:
            import pandas as pd
            import numpy as np
        except ImportError:
            return {
                "success": False,
                "error": "缺少pandas依赖，请安装: pip install pandas numpy"
            }

        # 读取CSV
        try:
            df = pd.read_csv(io.StringIO(csv_content))
        except Exception as e:
            return {"success": False, "error": f"CSV解析失败: {str(e)}"}

        row_count = len(df)
        column_count = len(df.columns)

        # 基础统计
        summary = {
            "filename": filename,
            "row_count": row_count,
            "column_count": column_count,
            "columns": []
        }

        numeric_cols = []
        categorical_cols = []

        for col in df.columns:
            col_info = {"name": col, "type": str(df[col].dtype)}

            if pd.api.types.is_numeric_dtype(df[col]):
                numeric_cols.append(col)
                col_info.update({
                    "mean": round(float(df[col].mean()), 2) if not df[col].isna().all() else None,
                    "std": round(float(df[col].std()), 2) if not df[col].isna().all() else None,
                    "min": round(float(df[col].min()), 2) if not df[col].isna().all() else None,
                    "max": round(float(df[col].max()), 2) if not df[col].isna().all() else None,
                    "median": round(float(df[col].median()), 2) if not df[col].isna().all() else None,
                    "null_count": int(df[col].isna().sum())
                })
            else:
                categorical_cols.append(col)
                col_info.update({
                    "unique_count": int(df[col].nunique()),
                    "most_common": df[col].value_counts().head(3).to_dict() if len(df[col].dropna()) > 0 else {},
                    "null_count": int(df[col].isna().sum())
                })

            summary["columns"].append(col_info)

        # 相关性分析（数值列之间）
        correlation = {}
        if len(numeric_cols) >= 2:
            corr_matrix = df[numeric_cols].corr()
            for i, col1 in enumerate(numeric_cols):
                for j, col2 in enumerate(numeric_cols):
                    if i < j:
                        corr_val = corr_matrix.loc[col1, col2]
                        if not pd.isna(corr_val) and abs(corr_val) > 0.3:
                            correlation[f"{col1} vs {col2}"] = round(float(corr_val), 3)

        summary["correlation"] = correlation

        # 生成图表数据
        charts = []

        # 1. 数值列分布直方图数据
        for col in numeric_cols[:3]:  # 最多3个数值列
            hist, bins = np.histogram(df[col].dropna(), bins=10)
            charts.append({
                "type": "histogram",
                "title": f"{col} 分布",
                "xAxis": [round(float(b), 2) for b in bins[:-1]],
                "series": [{"name": col, "data": hist.tolist()}]
            })

        # 2. 分类列饼图数据
        for col in categorical_cols[:2]:  # 最多2个分类列
            if df[col].nunique() <= 10:
                value_counts = df[col].value_counts().head(8)
                charts.append({
                    "type": "pie",
                    "title": f"{col} 分布",
                    "data": [
                        {"name": str(k), "value": int(v)}
                        for k, v in value_counts.items()
                    ]
                })

        # 3. 散点图数据（前两个数值列）
        if len(numeric_cols) >= 2:
            col1, col2 = numeric_cols[0], numeric_cols[1]
            sample_data = df[[col1, col2]].dropna().head(100)  # 最多100个点
            charts.append({
                "type": "scatter",
                "title": f"{col1} vs {col2}",
                "xAxis": col1,
                "yAxis": col2,
                "data": sample_data.values.tolist()
            })

        # 生成洞察
        insights = []

        # 数据质量洞察
        null_cols = [c for c in summary["columns"] if c.get("null_count", 0) > 0]
        if null_cols:
            insights.append({
                "type": "warning",
                "title": "数据缺失",
                "content": f"{len(null_cols)}个列存在缺失值，建议进行数据清洗"
            })

        # 相关性洞察
        if correlation:
            strongest = max(correlation.items(), key=lambda x: abs(x[1]))
            insights.append({
                "type": "info",
                "title": "强相关性发现",
                "content": f"{strongest[0]} 的相关系数为 {strongest[1]}，可能存在关联"
            })

        # 分布洞察
        for col in numeric_cols:
            col_data = df[col].dropna()
            skewness = float(col_data.skew())
            if abs(skewness) > 1:
                insights.append({
                    "type": "info",
                    "title": f"{col} 分布偏斜",
                    "content": f"偏度为 {round(skewness, 2)}，数据分布不均匀"
                })

        # 总体评价
        insights.append({
            "type": "success",
            "title": "数据概览",
            "content": f"数据集包含 {row_count} 行 {column_count} 列，其中数值列 {len(numeric_cols)} 个，分类列 {len(categorical_cols)} 个"
        })

        # 保存结果
        result = {
            "summary": summary,
            "charts": charts,
            "insights": insights
        }

        # 更新Agent和数据库
        agent = get_agent()
        agent.upload_data(session_id, {"filename": filename, "row_count": row_count})
        agent.set_analysis_result(session_id, result)

        SessionCRUD.update_csv_data(session_id, {"filename": filename, "row_count": row_count})
        SessionCRUD.update_analysis_result(session_id, result)

        AnalysisCRUD.create(
            session_id=session_id,
            filename=filename,
            row_count=row_count,
            column_count=column_count,
            summary=summary,
            charts=charts,
            insights=insights
        )

        LogCRUD.create(session_id, None, "csv_analyzed",
                       f"分析了CSV: {filename}, {row_count}行 x {column_count}列")

        return {
            "success": True,
            "session_id": session_id,
            "filename": filename,
            "row_count": row_count,
            "column_count": column_count,
            "summary": summary,
            "charts": charts,
            "insights": insights
        }

    @staticmethod
    def get_analysis(session_id: str) -> Optional[Dict]:
        """获取分析结果"""
        return AnalysisCRUD.get_by_session(session_id)

    @staticmethod
    async def review_report(session_id: str, title: str, content: str) -> Dict:
        """
        AI论文评审
        
        调用LLM对论文进行深度评审
        """
        try:
            from core.llm import get_llm_client
            llm = get_llm_client()
            
            system_prompt = """你是一位严格的学术论文评审专家。请对论文进行专业评审。

评审维度（每个维度满分10分）：
1. structure（结构完整性）：摘要、引言、方法、实验、结论是否齐全
2. method（研究方法）：技术路线是否清晰、合理
3. innovation（创新性）：是否有独特见解或创新点
4. data（数据分析）：数据处理、统计分析是否充分
5. reference（参考文献）：引用是否规范、全面

返回JSON格式：
{
  "scores": {"structure": x, "method": x, "innovation": x, "data": x, "reference": x},
  "feedback": "总体评价（200字以内）",
  "highlights": ["亮点1", "亮点2"],
  "suggestions": ["改进建议1", "改进建议2"]
}"""

            user_prompt = f"""论文标题：{title}

论文内容：
{content[:8000]}

请进行专业评审。"""

            response = await llm.chat(
                messages=[{"role": "user", "content": user_prompt}],
                system_prompt=system_prompt,
                temperature=0.3
            )
            
            import re
            import json
            try:
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    review = json.loads(json_match.group())
                else:
                    review = json.loads(response)
                
                # 验证评分结构
                scores = review.get("scores", {})
                for key in ["structure", "method", "innovation", "data", "reference"]:
                    if key not in scores:
                        scores[key] = 5.0
                    scores[key] = max(1.0, min(10.0, float(scores[key])))
                
                review["scores"] = scores
                review["feedback"] = review.get("feedback", "评审完成")
                review["highlights"] = review.get("highlights", [])
                review["suggestions"] = review.get("suggestions", [])
                
                return {
                    "success": True,
                    "session_id": session_id,
                    "review": review
                }
            except Exception as e:
                return {
                    "success": False,
                    "error": f"解析评审结果失败: {str(e)}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"评审失败: {str(e)}"
            }
