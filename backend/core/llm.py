"""
LLM核心模块 - 统一的大语言模型接口
支持智谱AI(GLM-4)、OpenAI(GPT-4)、通义千问(Qwen)等模型
"""
import os
import json
import asyncio
from typing import List, Dict, Optional
from dataclasses import dataclass
import aiohttp


@dataclass
class LLMConfig:
    """LLM配置"""
    provider: str = "zhipu"  # zhipu / openai / qwen
    model: str = "glm-4"
    api_key: str = ""
    api_base: str = ""
    temperature: float = 0.7
    max_tokens: int = 2048

    def __post_init__(self):
        # 从环境变量读取配置
        env_provider = os.getenv("LLM_PROVIDER", "zhipu")
        if env_provider in ["zhipu", "openai", "qwen"]:
            self.provider = env_provider

        env_model = os.getenv("LLM_MODEL", "")
        if env_model:
            self.model = env_model

        env_key = os.getenv("LLM_API_KEY", "") or os.getenv("ZHIPU_API_KEY", "")
        if env_key:
            self.api_key = env_key

        # 设置默认模型
        if not self.model:
            if self.provider == "zhipu":
                self.model = "glm-4"
            elif self.provider == "openai":
                self.model = "gpt-4"
            elif self.provider == "qwen":
                self.model = "qwen-turbo"

        # 设置默认API地址（支持LLM_BASE_URL环境变量覆盖）
        base_url = os.getenv("LLM_BASE_URL", "")
        if base_url:
            self.api_base = base_url
        elif not self.api_base:
            if self.provider == "zhipu":
                self.api_base = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
            elif self.provider == "openai":
                self.api_base = "https://api.openai.com/v1/chat/completions"
            elif self.provider == "qwen":
                self.api_base = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"


class LLMClient:
    """LLM客户端"""

    def __init__(self, config: Optional[LLMConfig] = None):
        self.config = config or LLMConfig()
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """获取HTTP会话（带连接池）"""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=60, connect=10)
            conn = aiohttp.TCPConnector(limit=10, limit_per_host=5)
            self._session = aiohttp.ClientSession(
                timeout=timeout,
                connector=conn,
                headers={"Content-Type": "application/json"}
            )
        return self._session

    async def chat(self, messages: List[Dict], system_prompt: str = "",
                   temperature: Optional[float] = None,
                   max_tokens: Optional[int] = None,
                   stream: bool = False) -> str:
        """
        发送聊天请求

        Args:
            messages: 消息列表 [{"role": "user", "content": "..."}]
            system_prompt: 系统提示词
            temperature: 温度（覆盖配置）
            max_tokens: 最大token数（覆盖配置）
            stream: 是否流式输出（暂不支持）

        Returns:
            LLM回复文本
        """
        if not self.config.api_key:
            raise LLMError("API密钥未配置，请设置 LLM_API_KEY 环境变量")

        temp = temperature if temperature is not None else self.config.temperature
        tokens = max_tokens if max_tokens is not None else self.config.max_tokens

        # 根据provider选择调用方式
        if self.config.provider == "zhipu":
            return await self._call_zhipu(messages, system_prompt, temp, tokens)
        elif self.config.provider == "openai":
            return await self._call_openai(messages, system_prompt, temp, tokens)
        elif self.config.provider == "qwen":
            return await self._call_qwen(messages, system_prompt, temp, tokens)
        else:
            raise LLMError(f"不支持的provider: {self.config.provider}")

    async def _call_api(self, url: str, headers: Dict, payload: Dict,
                        extract_response: callable) -> str:
        """通用API调用（带重试）"""
        session = await self._get_session()

        last_error = None
        for attempt in range(3):  # 最多重试3次
            try:
                async with session.post(url, headers=headers, json=payload) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return extract_response(data)
                    elif resp.status == 401:
                        raise LLMError("API密钥无效或已过期")
                    elif resp.status == 429:
                        raise LLMError("请求过于频繁，请稍后再试")
                    elif resp.status >= 500:
                        error_text = await resp.text()
                        raise LLMError(f"服务器错误 ({resp.status}): {error_text[:200]}")
                    else:
                        error_text = await resp.text()
                        raise LLMError(f"API错误 ({resp.status}): {error_text[:200]}")
            except LLMError:
                raise
            except asyncio.TimeoutError:
                last_error = LLMError(f"请求超时 (尝试 {attempt + 1}/3)")
                if attempt < 2:
                    await asyncio.sleep(2 ** attempt)  # 指数退避
            except Exception as e:
                last_error = LLMError(f"请求失败: {str(e)}")
                if attempt < 2:
                    await asyncio.sleep(2 ** attempt)

        raise last_error or LLMError("未知错误")

    async def _call_zhipu(self, messages: List[Dict], system_prompt: str,
                          temperature: float, max_tokens: int) -> str:
        """调用智谱AI"""
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json"
        }

        all_messages = []
        if system_prompt:
            all_messages.append({"role": "system", "content": system_prompt})
        all_messages.extend(messages)

        payload = {
            "model": self.config.model,
            "messages": all_messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        return await self._call_api(
            self.config.api_base,
            headers,
            payload,
            lambda d: d["choices"][0]["message"]["content"]
        )

    async def _call_openai(self, messages: List[Dict], system_prompt: str,
                           temperature: float, max_tokens: int) -> str:
        """调用OpenAI"""
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json"
        }

        all_messages = []
        if system_prompt:
            all_messages.append({"role": "system", "content": system_prompt})
        all_messages.extend(messages)

        payload = {
            "model": self.config.model,
            "messages": all_messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        return await self._call_api(
            self.config.api_base,
            headers,
            payload,
            lambda d: d["choices"][0]["message"]["content"]
        )

    async def _call_qwen(self, messages: List[Dict], system_prompt: str,
                         temperature: float, max_tokens: int) -> str:
        """调用通义千问"""
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json"
        }

        # 千问的message格式
        all_messages = []
        if system_prompt:
            all_messages.append({"role": "system", "content": system_prompt})
        all_messages.extend(messages)

        payload = {
            "model": self.config.model,
            "input": {
                "messages": all_messages
            },
            "parameters": {
                "temperature": temperature,
                "max_tokens": max_tokens,
                "result_format": "message"
            }
        }

        return await self._call_api(
            self.config.api_base,
            headers,
            payload,
            lambda d: d["output"]["choices"][0]["message"]["content"]
        )

    async def generate_topics(self, major: str, direction: str,
                            count: int = 4) -> List[Dict]:
        """生成选题"""
        system_prompt = f"""你是一位资深的毕业设计指导老师，专注于{major}领域。
请根据学生的专业和研究方向，生成具体、有深度的毕业设计选题。

要求：
1. 每个选题必须包含：title(标题)、desc(描述)、diff(难度1-5)、tags(技术标签数组)
2. 选题要贴合实际，有具体的技术栈
3. 难度合理：本科生以2-4为主
4. 返回JSON数组格式

示例：
[
  {{"title": "基于深度学习的图像分类系统", "desc": "使用CNN实现图像分类", "diff": 3, "tags": ["Python", "PyTorch", "CNN"]}},
  ...
]"""

        user_prompt = f"专业：{major}，研究方向：{direction}，请生成{count}个毕业设计选题。"

        try:
            response = await self.chat(
                messages=[{"role": "user", "content": user_prompt}],
                system_prompt=system_prompt,
                temperature=0.8
            )

            import re
            try:
                json_match = re.search(r'\[.*\]', response, re.DOTALL)
                if json_match:
                    topics = json.loads(json_match.group())
                else:
                    topics = json.loads(response)
                return topics[:count]
            except Exception:
                return self._default_topics(major, direction, count)
        except LLMError:
            return self._default_topics(major, direction, count)

    async def evaluate_defense(self, question: str, answer: str,
                              topic: str = "") -> Dict:
        """评估答辩回答"""
        system_prompt = """你是一位严格的毕业设计答辩评委。请对学生的回答进行专业评估。

评估维度（每个维度满分10分）：
1. innovation（创新性）：是否有独特见解或创新点
2. technique（技术深度）：技术方案是否清晰、合理
3. logic（逻辑性）：论述是否有条理、逻辑严密
4. presentation（展示能力）：表达是否清晰、专业

返回JSON格式：
{
  "score": {"innovation": x, "technique": x, "logic": x, "presentation": x},
  "feedback": "总体评价（100字以内）",
  "level": "优秀/良好/一般/需改进",
  "highlights": ["亮点1", "亮点2"],
  "suggestions": ["改进建议1", "改进建议2"]
}"""

        user_prompt = f"""选题：{topic}
问题：{question}
学生回答：{answer}

请进行评估。"""

        try:
            response = await self.chat(
                messages=[{"role": "user", "content": user_prompt}],
                system_prompt=system_prompt,
                temperature=0.5
            )

            import re
            try:
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    evaluation = json.loads(json_match.group())
                else:
                    evaluation = json.loads(response)

                # 验证评分结构
                score = evaluation.get("score", {})
                for key in ["innovation", "technique", "logic", "presentation"]:
                    if key not in score:
                        score[key] = 5
                    score[key] = max(1, min(10, int(score[key])))

                evaluation["score"] = score
                evaluation["level"] = evaluation.get("level", "一般")
                evaluation["feedback"] = evaluation.get("feedback", "评估完成")

                return evaluation
            except Exception:
                return self._default_evaluation(answer)
        except LLMError:
            return self._default_evaluation(answer)

    def _default_topics(self, major: str, direction: str, count: int) -> List[Dict]:
        """默认选题（LLM失败时）"""
        defaults = [
            {"title": f"基于{direction}的{major}系统", "desc": f"针对{major}领域的{direction}方向进行深度研究，构建完整的系统解决方案。", "diff": 3, "tags": [direction, major, "Python"]},
            {"title": f"{major}领域数据分析平台", "desc": f"使用大数据技术对{major}领域的数据进行采集、清洗、分析和可视化。", "diff": 3, "tags": ["数据分析", "可视化", "Python"]},
            {"title": f"基于机器学习的{direction}预测模型", "desc": f"利用机器学习算法构建{direction}的预测模型，并进行性能优化。", "diff": 4, "tags": ["机器学习", "预测", "Python"]},
            {"title": f"{major}智能推荐系统", "desc": f"设计并实现基于协同过滤和深度学习的推荐系统。", "diff": 3, "tags": ["推荐系统", "深度学习", "Python"]}
        ]
        return defaults[:count]

    def _default_evaluation(self, answer: str) -> Dict:
        """默认评估（LLM失败时）"""
        length = len(answer)
        if length > 200:
            score = {"innovation": 7, "technique": 7, "logic": 7, "presentation": 8}
            level = "良好"
        elif length > 100:
            score = {"innovation": 6, "technique": 6, "logic": 6, "presentation": 7}
            level = "一般"
        else:
            score = {"innovation": 4, "technique": 4, "logic": 4, "presentation": 5}
            level = "需改进"

        return {
            "score": score,
            "feedback": f"回答长度{length}字，总体表现{level}。",
            "level": level,
            "highlights": ["回答完整" if length > 50 else "回答简洁"],
            "suggestions": ["建议增加更多技术细节"]
        }

    async def close(self):
        """关闭HTTP会话"""
        if self._session and not self._session.closed:
            await self._session.close()


class LLMError(Exception):
    """LLM调用错误"""
    pass


# 全局实例
_llm_client: Optional[LLMClient] = None


def get_llm_client() -> LLMClient:
    """获取LLM客户端（单例）"""
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client
