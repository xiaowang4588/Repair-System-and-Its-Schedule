"""
空教室查询模块

本文件负责：
  1. 从课表数据构建教室使用索引（哪间教室在哪天哪节课有课）
  2. 根据条件查询空教室（按星期、节次、楼栋、类型筛选）
  3. 提供楼栋列表、教室统计等辅助功能

被 cache_manager.py 和 app.py 调用。
"""
import pandas as pd
from typing import List, Dict, Set, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import re

class ClassroomType(Enum):
    REGULAR = "regular"  # 普通教室
    LAB = "lab"  # 实验室
    LIBRARY = "library"  # 图书馆
    SPECIAL = "special"  # 特殊地点
    ALL = "all"  # 所有类型

@dataclass
class QueryCondition:
    weekday: int  # 1-7
    sections: List[int]  # 节次列表
    building: Optional[str] = None  # 楼栋筛选
    classroom_type: ClassroomType = ClassroomType.ALL  # 教室类型
    keyword: Optional[str] = None  # 关键词搜索
    exclude_special: bool = True  # 是否排除特殊地点

@dataclass
class ClassroomInfo:
    classroom: str
    building: str
    classroom_type: ClassroomType
    sections_available: List[int]  # 可用的节次
    sections_occupied: List[int]  # 已占用的节次

class EmptyClassroomQuery:
    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.classroom_index = {}  # {weekday: {classroom: set(sections)}}
        self.buildings = {}  # {building: set(classrooms)}
        self.all_classrooms = set()
        self._build_index()
    
    def _build_index(self):
        """构建教室使用索引"""
        # 重置索引
        self.classroom_index = {}
        self.buildings = {}
        self.all_classrooms = set()
        
        for _, row in self.df.iterrows():
            weekday = row['weekday']
            sections = row['section_list']
            classrooms = row['classroom_list']
            buildings = row['building_list']
            
            if weekday not in self.classroom_index:
                self.classroom_index[weekday] = {}
            
            # 更新教室使用索引
            for i, classroom in enumerate(classrooms):
                if classroom not in self.classroom_index[weekday]:
                    self.classroom_index[weekday][classroom] = set()
                self.classroom_index[weekday][classroom].update(sections)
                
                # 更新所有教室集合
                self.all_classrooms.add(classroom)
                
                # 更新楼栋映射
                if i < len(buildings):
                    building = buildings[i]
                    if building not in self.buildings:
                        self.buildings[building] = set()
                    self.buildings[building].add(classroom)
    
    def _classify_classroom(self, classroom: str) -> ClassroomType:
        """分类教室类型"""
        classroom_lower = classroom.lower()
        
        # 实验室关键词
        lab_keywords = ['实验室', 'lab', '实训', '实操']
        if any(keyword in classroom_lower for keyword in lab_keywords):
            return ClassroomType.LAB
        
        # 图书馆关键词
        library_keywords = ['图书馆', 'library']
        if any(keyword in classroom_lower for keyword in library_keywords):
            return ClassroomType.LIBRARY
        
        # 特殊地点关键词
        special_keywords = ['运动场', '游泳馆', '电影院', '通知', '非物质文化遗产馆']
        if any(keyword in classroom for keyword in special_keywords):
            return ClassroomType.SPECIAL
        
        # 默认为普通教室
        return ClassroomType.REGULAR
    
    def _is_classroom_available(self, classroom: str, weekday: int, sections: List[int]) -> bool:
        """检查教室在指定时间段是否完全可用（所有查询节次都必须空闲）"""
        if weekday not in self.classroom_index:
            return True
        
        if classroom not in self.classroom_index[weekday]:
            return True
        
        occupied_sections = self.classroom_index[weekday][classroom]
        # 检查所有查询节次是否都空闲（任何一个被占用就返回False）
        return not any(section in occupied_sections for section in sections)
    
    def query_empty_classrooms(self, condition: QueryCondition) -> List[ClassroomInfo]:
        """查询空教室"""
        results = []
        
        # 获取所有候选教室
        candidate_classrooms = self.all_classrooms.copy()
        
        # 按楼栋筛选
        if condition.building and condition.building in self.buildings:
            candidate_classrooms = self.buildings[condition.building].intersection(candidate_classrooms)
        
        # 按关键词筛选
        if condition.keyword:
            keyword_lower = condition.keyword.lower()
            candidate_classrooms = {
                c for c in candidate_classrooms 
                if keyword_lower in c.lower()
            }
        
        # 检查每个教室
        for classroom in candidate_classrooms:
            # 分类教室
            classroom_type = self._classify_classroom(classroom)
            
            # 按类型筛选
            if condition.classroom_type != ClassroomType.ALL:
                if classroom_type != condition.classroom_type:
                    continue
            
            # 排除特殊地点
            if condition.exclude_special and classroom_type == ClassroomType.SPECIAL:
                continue
            
            # 检查可用性
            if self._is_classroom_available(classroom, condition.weekday, condition.sections):
                # 获取占用的节次（确保类型正确）
                occupied_sections: Set[int] = set()
                if condition.weekday in self.classroom_index:
                    if classroom in self.classroom_index[condition.weekday]:
                        occupied_sections = self.classroom_index[condition.weekday][classroom]
                
                # 计算可用的节次（所有1-12节中空闲的）
                available_sections = [s for s in range(1, 13) if s not in occupied_sections]
                
                # 提取楼栋名称
                building_match = re.match(r'([^\d]+)', classroom)
                building = building_match.group(1).strip() if building_match else "未知"
                
                results.append(ClassroomInfo(
                    classroom=classroom,
                    building=building,
                    classroom_type=classroom_type,
                    sections_available=available_sections,
                    sections_occupied=sorted(list(occupied_sections))
                ))
        
        # 按楼栋和教室名称排序
        results.sort(key=lambda x: (x.building, x.classroom))
        return results
    
    def get_query_result_details(self, classroom: str, weekday: int, query_sections: List[int]) -> Dict:
        """获取查询结果的详细信息，包括查询条件中每个节次的状态"""
        occupied_sections: Set[int] = set()
        if weekday in self.classroom_index:
            if classroom in self.classroom_index[weekday]:
                occupied_sections = self.classroom_index[weekday][classroom]
        
        section_status = {}
        for section in query_sections:
            section_status[section] = section not in occupied_sections
        
        return {
            'classroom': classroom,
            'query_sections': query_sections,
            'occupied_sections': sorted(list(occupied_sections)),
            'section_status': section_status,
            'is_available': all(status for status in section_status.values())
        }
    
    def get_available_sections(self, classroom: str, weekday: int) -> List[int]:
        """获取教室在指定星期几的可用节次"""
        if weekday not in self.classroom_index:
            return list(range(1, 13))
        
        if classroom not in self.classroom_index[weekday]:
            return list(range(1, 13))
        
        occupied_sections = self.classroom_index[weekday][classroom]
        return [s for s in range(1, 13) if s not in occupied_sections]
    
    def get_buildings(self) -> List[str]:
        """获取所有楼栋列表"""
        return sorted(list(self.buildings.keys()))
    
    def get_building_classrooms(self, building: str) -> List[str]:
        """获取指定楼栋的所有教室"""
        if building in self.buildings:
            return sorted(list(self.buildings[building]))
        return []
    
    def get_statistics(self) -> Dict:
        """获取统计信息"""
        stats = {
            'total_classrooms': len(self.all_classrooms),
            'total_buildings': len(self.buildings),
            'weekday_stats': {},
            'building_stats': {}
        }
        
        # 每天统计
        for weekday in range(1, 8):
            if weekday in self.classroom_index:
                stats['weekday_stats'][weekday] = {
                    'total_classrooms': len(self.all_classrooms),
                    'occupied_classrooms': len(self.classroom_index[weekday]),
                    'available_classrooms': len(self.all_classrooms) - len(self.classroom_index[weekday])
                }
        
        # 楼栋统计
        for building, classrooms in self.buildings.items():
            stats['building_stats'][building] = len(classrooms)
        
        return stats

def create_query_system(df: pd.DataFrame) -> EmptyClassroomQuery:
    """创建查询系统"""
    # 清洗数据
    from data_cleaning import clean_and_normalize_data
    cleaned_df = clean_and_normalize_data(df)
    
    # 创建查询系统
    query_system = EmptyClassroomQuery(cleaned_df)
    return query_system

if __name__ == "__main__":
    # 测试查询系统
    EXCEL_PATH = "全校课表8.31导出.xlsx"
    SHEET_NAME = "sheet1"
    
    df = pd.read_excel(EXCEL_PATH, sheet_name=SHEET_NAME)
    query_system = create_query_system(df)
    
    print("=== 查询系统测试 ===")
    
    # 测试1：查询周一第1-2节的空教室
    condition = QueryCondition(
        weekday=1,
        sections=[1, 2],
        exclude_special=True
    )
    
    results = query_system.query_empty_classrooms(condition)
    print(f"\n周一第1-2节空教室数量: {len(results)}")
    print("前5个空教室:")
    for i, classroom in enumerate(results[:5]):
        print(f"{i+1}. {classroom.classroom} ({classroom.building}) - 类型: {classroom.classroom_type.value}")
    
    # 测试2：查询贤者楼的空教室
    condition = QueryCondition(
        weekday=2,
        sections=[3, 4],
        building="贤者楼",
        exclude_special=True
    )
    
    results = query_system.query_empty_classrooms(condition)
    print(f"\n周二第3-4节贤者楼空教室数量: {len(results)}")
    print("前5个空教室:")
    for i, classroom in enumerate(results[:5]):
        print(f"{i+1}. {classroom.classroom} - 可用节次: {classroom.sections_available}")
    
    # 测试3：获取统计信息
    stats = query_system.get_statistics()
    print(f"\n=== 统计信息 ===")
    print(f"总教室数: {stats['total_classrooms']}")
    print(f"总楼栋数: {stats['total_buildings']}")
    print("\n各楼栋教室数:")
    for building, count in sorted(stats['building_stats'].items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"  {building}: {count}个")