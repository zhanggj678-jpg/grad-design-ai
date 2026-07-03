"""选题服务单元测试"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.agent import WorkflowStage, get_agent

def test_agent_session():
    """测试Agent会话管理"""
    agent = get_agent()
    session = agent.create_session()

    assert session.session_id is not None
    assert session.current_stage == WorkflowStage.INIT

    # 测试阶段转换
    agent.select_major(session.session_id, "信息工程学院", "计算机科学与技术", "数据分析")
    updated = agent.get_session(session.session_id)
    assert updated.current_stage == WorkflowStage.MAJOR_SELECTED
    assert updated.major == "计算机科学与技术"

def test_multi_agent():
    """测试多智能体系统"""
    from core.multi_agent import get_multi_agent, AgentRole

    ma = get_multi_agent()
    assert ma is not None
    assert AgentRole.TOPIC_ANALYST in ma.agents

def test_rag_engine():
    """测试RAG引擎"""
    import asyncio
    from core.rag_engine import get_rag_engine

    rag = get_rag_engine()
    stats = rag.get_stats()
    assert stats["total_documents"] > 0

    # 测试搜索
    results = asyncio.run(rag.search("深度学习 图像", top_k=3))
    assert len(results) > 0
    assert "title" in results[0]

if __name__ == "__main__":
    test_agent_session()
    test_multi_agent()
    test_rag_engine()
    print("All topic tests passed!")
