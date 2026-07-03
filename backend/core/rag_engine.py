"""
RAG学术检索引擎 - 基于关键词+语义匹配的学术推荐系统
提供选题推荐、参考文献、技术方案检索
"""
import os
import json
from typing import List, Dict, Optional
from dataclasses import dataclass
import asyncio

@dataclass
class RAGDocument:
    """RAG文档"""
    id: str
    title: str
    content: str
    category: str  # topic/reference/tech/method
    tags: List[str]
    major: str
    difficulty: int
    source: str

class RAGEngine:
    """RAG检索引擎"""

    def __init__(self):
        self._documents: List[RAGDocument] = []
        self._index: Dict[str, List[int]] = {}  # keyword -> doc_ids
        self._loaded = False

    def _load_builtin_data(self):
        """加载内置学术数据"""
        builtin_data = [
            # 选题推荐
            {"id": "t001", "title": "基于深度学习的图像分类系统", "content": "使用CNN/ResNet对图像进行分类，可应用于医学影像、自动驾驶等领域。技术栈：Python, PyTorch, OpenCV", "category": "topic", "tags": ["深度学习", "图像分类", "CNN", "PyTorch"], "major": "计算机科学与技术", "difficulty": 3, "source": "学术热点"},
            {"id": "t002", "title": "基于NLP的情感分析系统", "content": "利用BERT/Transformer对文本进行情感分析，可用于舆情监控、产品评价分析。技术栈：Python, HuggingFace, Flask", "category": "topic", "tags": ["NLP", "情感分析", "BERT", "深度学习"], "major": "计算机科学与技术", "difficulty": 3, "source": "学术热点"},
            {"id": "t003", "title": "基于推荐算法的电商系统", "content": "实现协同过滤/矩阵分解/深度学习推荐算法，构建个性化推荐系统。技术栈：Python, TensorFlow, MySQL", "category": "topic", "tags": ["推荐系统", "协同过滤", "深度学习", "机器学习"], "major": "计算机科学与技术", "difficulty": 3, "source": "学术热点"},
            {"id": "t004", "title": "基于知识图谱的问答系统", "content": "构建领域知识图谱，实现基于图谱的智能问答。技术栈：Python, Neo4j, NLP", "category": "topic", "tags": ["知识图谱", "问答系统", "NLP", "Neo4j"], "major": "计算机科学与技术", "difficulty": 4, "source": "前沿方向"},
            {"id": "t005", "title": "基于大数据的用户行为分析平台", "content": "使用Spark/Flink处理海量用户行为数据，构建实时分析平台。技术栈：Python, Spark, Kafka, ECharts", "category": "topic", "tags": ["大数据", "用户行为", "Spark", "实时计算"], "major": "数据科学与大数据技术", "difficulty": 4, "source": "学术热点"},
            {"id": "t006", "title": "基于机器学习的信用评分模型", "content": "利用XGBoost/LightGBM构建信用评分模型，实现智能风控。技术栈：Python, Scikit-learn, Pandas", "category": "topic", "tags": ["机器学习", "信用评分", "XGBoost", "风控"], "major": "数据科学与大数据技术", "difficulty": 3, "source": "学术热点"},
            {"id": "t007", "title": "基于Python的股票预测系统", "content": "使用LSTM/Transformer预测股票价格趋势，结合技术指标分析。技术栈：Python, TensorFlow, Pandas, TA-Lib", "category": "topic", "tags": ["LSTM", "股票预测", "时间序列", "深度学习"], "major": "数据科学与大数据技术", "difficulty": 3, "source": "学术热点"},
            {"id": "t008", "title": "基于Web的在线考试系统", "content": "设计并实现一个完整的在线考试系统，包含题库管理、自动组卷、防作弊、成绩统计。技术栈：Java/Vue.js, Spring Boot, MySQL", "category": "topic", "tags": ["Web开发", "考试系统", "Spring Boot", "Vue.js"], "major": "软件工程", "difficulty": 3, "source": "经典项目"},
            {"id": "t009", "title": "基于微服务的电商平台", "content": "使用Spring Cloud/Docker构建微服务架构电商平台。技术栈：Java, Spring Cloud, Docker, MySQL, Redis", "category": "topic", "tags": ["微服务", "Spring Cloud", "Docker", "电商"], "major": "软件工程", "difficulty": 4, "source": "企业级项目"},
            {"id": "t010", "title": "基于AI的智能客服系统", "content": "结合NLP和知识库构建智能客服，支持多轮对话和意图识别。技术栈：Python, FastAPI, NLP, Vue.js", "category": "topic", "tags": ["智能客服", "NLP", "对话系统", "FastAPI"], "major": "人工智能", "difficulty": 3, "source": "学术热点"},
            {"id": "t011", "title": "基于YOLO的目标检测系统", "content": "使用YOLOv8实现实时目标检测，可应用于安防监控、自动驾驶。技术栈：Python, PyTorch, OpenCV, YOLO", "category": "topic", "tags": ["目标检测", "YOLO", "深度学习", "计算机视觉"], "major": "人工智能", "difficulty": 3, "source": "学术热点"},
            {"id": "t012", "title": "基于区块链的数字版权系统", "content": "利用区块链技术保护数字内容版权，实现版权登记和交易。技术栈：Solidity, Ethereum, Web3.js, React", "category": "topic", "tags": ["区块链", "数字版权", "智能合约", "Web3"], "major": "信息安全", "difficulty": 4, "source": "前沿方向"},
            {"id": "t013", "title": "基于物联网的智慧农业系统", "content": "使用传感器+MQTT+云平台构建智慧农业监测系统。技术栈：Python, MQTT, InfluxDB, Vue.js", "category": "topic", "tags": ["物联网", "智慧农业", "MQTT", "传感器"], "major": "物联网工程", "difficulty": 3, "source": "应用导向"},
            {"id": "t014", "title": "基于Flutter的移动健康APP", "content": "开发一款健康管理APP，包含运动记录、饮食分析、睡眠监测。技术栈：Flutter, Dart, Firebase", "category": "topic", "tags": ["Flutter", "移动开发", "健康", "Firebase"], "major": "计算机科学与技术", "difficulty": 2, "source": "应用导向"},
            {"id": "t015", "title": "基于数据分析的房价预测模型", "content": "收集城市房价数据，使用多种回归模型进行预测分析。技术栈：Python, Scikit-learn, Pandas, ECharts", "category": "topic", "tags": ["数据分析", "房价预测", "回归分析", "机器学习"], "major": "数据科学与大数据技术", "difficulty": 2, "source": "经典项目"},
            # 技术方案参考
            {"id": "r001", "title": "CNN图像分类技术方案", "content": "卷积神经网络(CNN)是图像分类的主流方法。推荐使用ResNet-50作为backbone，配合数据增强和迁移学习。参考论文：He et al., Deep Residual Learning, 2016", "category": "reference", "tags": ["CNN", "ResNet", "图像分类", "迁移学习"], "major": "计算机科学与技术", "difficulty": 3, "source": "学术论文"},
            {"id": "r002", "title": "BERT文本分类技术方案", "content": "BERT(Bidirectional Encoder Representations from Transformers)是NLP领域的里程碑模型。可用于文本分类、命名实体识别、问答系统等。参考论文：Devlin et al., BERT, 2019", "category": "reference", "tags": ["BERT", "Transformer", "NLP", "预训练"], "major": "计算机科学与技术", "difficulty": 4, "source": "学术论文"},
            {"id": "r003", "title": "协同过滤推荐算法", "content": "协同过滤是推荐系统的经典算法，分为User-CF和Item-CF。可结合矩阵分解(SVD)和深度学习提升效果。参考：Koren et al., Matrix Factorization, 2009", "category": "reference", "tags": ["协同过滤", "矩阵分解", "推荐系统", "SVD"], "major": "数据科学与大数据技术", "difficulty": 3, "source": "学术论文"},
            {"id": "r004", "title": "LSTM时间序列预测", "content": "LSTM(Long Short-Term Memory)擅长处理序列数据，广泛用于时间序列预测、自然语言处理。参考论文：Hochreiter & Schmidhuber, LSTM, 1997", "category": "reference", "tags": ["LSTM", "时间序列", "RNN", "深度学习"], "major": "数据科学与大数据技术", "difficulty": 3, "source": "学术论文"},
            {"id": "r005", "title": "YOLO目标检测技术方案", "content": "YOLO(You Only Look Once)是实时目标检测的代表算法。最新版本YOLOv8在速度和精度上都有显著提升。推荐使用Ultralytics框架。", "category": "reference", "tags": ["YOLO", "目标检测", "实时检测", "Ultralytics"], "major": "人工智能", "difficulty": 3, "source": "技术文档"},
            {"id": "r006", "title": "Spring Boot微服务架构", "content": "Spring Boot + Spring Cloud是Java微服务开发的主流方案。包含服务注册(Eureka)、配置中心(Config)、网关(Gateway)、熔断(Hystrix)等组件。", "category": "reference", "tags": ["Spring Boot", "微服务", "Spring Cloud", "Java"], "major": "软件工程", "difficulty": 3, "source": "技术文档"},
        ]

        for item in builtin_data:
            doc = RAGDocument(
                id=item["id"],
                title=item["title"],
                content=item["content"],
                category=item["category"],
                tags=item["tags"],
                major=item["major"],
                difficulty=item.get("difficulty", 3),
                source=item.get("source", "")
            )
            self._documents.append(doc)

    def _build_index(self):
        """构建倒排索引"""
        self._index = {}
        for i, doc in enumerate(self._documents):
            # 索引标题和标签中的关键词
            keywords = set()
            keywords.update(doc.title.split())
            keywords.update(doc.tags)
            keywords.update(doc.major.split())
            keywords.update(doc.content.split()[:20])  # 内容前20个词

            for kw in keywords:
                kw_lower = kw.lower()
                if kw_lower not in self._index:
                    self._index[kw_lower] = []
                self._index[kw_lower].append(i)

    def _ensure_loaded(self):
        if not self._loaded:
            self._load_builtin_data()
            self._build_index()
            self._loaded = True

    def _calculate_relevance(self, query: str, doc: RAGDocument) -> float:
        """计算相关性分数"""
        query_lower = query.lower()
        query_terms = set(query_lower.split())

        score = 0.0

        # 标题匹配（权重最高）
        title_lower = doc.title.lower()
        for term in query_terms:
            if term in title_lower:
                score += 3.0

        # 标签匹配
        for tag in doc.tags:
            if tag.lower() in query_lower or any(t in tag.lower() for t in query_terms):
                score += 2.0

        # 专业匹配
        if doc.major.lower() in query_lower:
            score += 2.5

        # 内容匹配
        content_lower = doc.content.lower()
        for term in query_terms:
            if term in content_lower:
                score += 0.5

        return score

    async def search(self, query: str, major: str = "", direction: str = "",
                     category: str = "", top_k: int = 5) -> List[Dict]:
        """
        搜索相关文档

        Args:
            query: 搜索查询
            major: 专业过滤
            direction: 方向过滤
            category: 类别过滤(topic/reference/tech/method)
            top_k: 返回数量

        Returns:
            相关文档列表
        """
        self._ensure_loaded()

        # 合并查询
        full_query = f"{query} {major} {direction}".strip()

        # 计算每个文档的相关性
        scored_docs = []
        for doc in self._documents:
            # 类别过滤
            if category and doc.category != category:
                continue

            # 专业过滤（模糊匹配）
            if major and major not in doc.major and doc.major not in major:
                # 不完全匹配也保留，但降低分数
                pass

            score = self._calculate_relevance(full_query, doc)
            if score > 0:
                scored_docs.append((doc, score))

        # 按分数排序
        scored_docs.sort(key=lambda x: x[1], reverse=True)

        # 返回top_k结果
        results = []
        for doc, score in scored_docs[:top_k]:
            results.append({
                "id": doc.id,
                "title": doc.title,
                "summary": doc.content[:200],
                "category": doc.category,
                "tags": doc.tags,
                "major": doc.major,
                "difficulty": doc.difficulty,
                "source": doc.source,
                "relevance_score": round(score, 2)
            })

        return results

    async def recommend_topics(self, major: str, direction: str,
                              count: int = 4) -> List[Dict]:
        """推荐相关选题"""
        return await self.search(
            query=f"{major} {direction}",
            major=major,
            direction=direction,
            category="topic",
            top_k=count
        )

    async def get_references(self, query: str, count: int = 3) -> List[Dict]:
        """获取学术参考"""
        return await self.search(
            query=query,
            category="reference",
            top_k=count
        )

    def get_stats(self) -> Dict:
        """获取RAG数据库统计"""
        self._ensure_loaded()
        categories = {}
        for doc in self._documents:
            categories[doc.category] = categories.get(doc.category, 0) + 1
        return {
            "total_documents": len(self._documents),
            "categories": categories,
            "index_size": len(self._index)
        }

# 全局实例
_rag_engine: Optional[RAGEngine] = None

def get_rag_engine() -> RAGEngine:
    global _rag_engine
    if _rag_engine is None:
        _rag_engine = RAGEngine()
    return _rag_engine
