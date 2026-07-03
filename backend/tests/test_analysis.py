"""数据分析服务单元测试"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_csv_analysis():
    """测试CSV分析"""
    from service.analysis_service import AnalysisService

    csv_content = """name,age,score,grade
Alice,22,85,A
Bob,23,92,A
Charlie,21,78,B
Diana,22,88,A
Eve,23,65,C"""

    result = AnalysisService.analyze_csv(
        session_id="test_session",
        filename="test.csv",
        csv_content=csv_content
    )

    assert result["success"] == True
    assert result["row_count"] == 5
    assert result["column_count"] == 4
    assert len(result["summary"]["columns"]) == 4
    assert len(result["charts"]) > 0

if __name__ == "__main__":
    test_csv_analysis()
    print("All analysis tests passed!")
