"""
数据清洗模块

本文件负责：
  1. 解析教室字符串（如 "贤者楼405;贤者楼404" → ["贤者楼405", "贤者楼404"]）
  2. 解析节次字符串（如 "1-2节" → ["1", "2"]）
  3. 提取楼栋名称（如 "仁者楼402" → "仁者楼"）
  4. 标记常规教室（排除运动场、游泳馆等特殊场地）

被 empty_classroom_query.py 调用。
"""
import pandas as pd
import re
from typing import List, Dict, Tuple, Set

def parse_classroom_string(classroom_str: str) -> List[str]:
    """
    解析教室字符串，返回标准化的教室列表
    处理格式：贤者楼405;贤者楼405;贤者楼405;贤者楼404
    """
    if not classroom_str or pd.isna(classroom_str):
        return []
    
    classroom_str = str(classroom_str).strip()
    if not classroom_str:
        return []
    
    # 分割多个教室
    classrooms = [c.strip() for c in classroom_str.split(';') if c.strip()]
    
    # 去重并保持顺序
    seen = set()
    unique_classrooms = []
    for classroom in classrooms:
        if classroom not in seen:
            seen.add(classroom)
            unique_classrooms.append(classroom)
    
    return unique_classrooms

def parse_section_string(section_str: str) -> List[int]:
    """
    解析上课节次字符串，返回节次列表
    处理格式：1-2节, 3-4节, 1-4节, 9-9节
    """
    if not section_str or pd.isna(section_str):
        return []
    
    section_str = str(section_str).strip()
    if not section_str:
        return []
    
    sections = []
    
    # 分割多个节次范围
    parts = [p.strip() for p in section_str.split(',') if p.strip()]
    
    for part in parts:
        # 匹配格式：数字-数字节 或 数字-数字
        match = re.match(r'(\d+)-(\d+)节?', part)
        if match:
            start = int(match.group(1))
            end = int(match.group(2))
            # 确保范围合理
            if start <= end and 1 <= start <= 12 and 1 <= end <= 12:
                sections.extend(range(start, end + 1))
        else:
            # 尝试匹配单个数字
            single_match = re.match(r'(\d+)节?', part)
            if single_match:
                num = int(single_match.group(1))
                if 1 <= num <= 12:
                    sections.append(num)
    
    return sorted(list(set(sections)))

def is_regular_classroom(classroom: str) -> bool:
    """
    判断是否是常规教室（排除运动场、游泳馆等特殊地点）
    """
    special_keywords = ['运动场', '游泳馆', '电影院', '通知', '非物质文化遗产馆']
    for keyword in special_keywords:
        if keyword in classroom:
            return False
    return True

def extract_building_name(classroom: str) -> str:
    """
    提取楼栋名称（如：贤者楼、勤者楼、仁者楼等）
    """
    match = re.match(r'([^\d]+)', classroom)
    if match:
        return match.group(1).strip()
    return classroom

def clean_and_normalize_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    清洗和标准化数据
    """
    # 创建清洗后的数据副本
    cleaned_df = df.copy()
    
    # 1. 解析教室信息
    cleaned_df['classroom_list'] = cleaned_df['上课地点'].apply(parse_classroom_string)
    cleaned_df['has_classroom'] = cleaned_df['classroom_list'].apply(lambda x: len(x) > 0)
    
    # 2. 解析节次信息
    cleaned_df['section_list'] = cleaned_df['上课节次'].apply(parse_section_string)
    cleaned_df['has_sections'] = cleaned_df['section_list'].apply(lambda x: len(x) > 0)
    
    # 3. 标准化星期几（容错处理非数字值）
    cleaned_df['weekday'] = pd.to_numeric(cleaned_df['星期几'], errors='coerce').fillna(0).astype(int)
    
    # 4. 提取楼栋信息
    cleaned_df['building_list'] = cleaned_df['classroom_list'].apply(
        lambda classrooms: [extract_building_name(c) for c in classrooms if c]
    )
    
    # 5. 标记常规教室
    cleaned_df['is_regular'] = cleaned_df['classroom_list'].apply(
        lambda classrooms: any(is_regular_classroom(c) for c in classrooms)
    )
    
    return cleaned_df

def create_classroom_index(cleaned_df: pd.DataFrame) -> Dict[str, Dict[str, Set[int]]]:
    """
    创建教室使用索引
    返回格式：{weekday: {classroom: set(sections)}}
    """
    classroom_index = {}
    
    for _, row in cleaned_df.iterrows():
        weekday = row['weekday']
        sections = row['section_list']
        classrooms = row['classroom_list']
        
        if weekday not in classroom_index:
            classroom_index[weekday] = {}
        
        for classroom in classrooms:
            if classroom not in classroom_index[weekday]:
                classroom_index[weekday][classroom] = set()
            
            classroom_index[weekday][classroom].update(sections)
    
    return classroom_index

def get_all_classrooms(cleaned_df: pd.DataFrame) -> Set[str]:
    """
    获取所有教室的集合
    """
    all_classrooms = set()
    for classrooms in cleaned_df['classroom_list']:
        all_classrooms.update(classrooms)
    return all_classrooms

def get_buildings(cleaned_df: pd.DataFrame) -> Dict[str, Set[str]]:
    """
    获取楼栋和教室的映射关系
    """
    buildings = {}
    for _, row in cleaned_df.iterrows():
        for i, classroom in enumerate(row['classroom_list']):
            if i < len(row['building_list']):
                building = row['building_list'][i]
                if building not in buildings:
                    buildings[building] = set()
                buildings[building].add(classroom)
    return buildings

if __name__ == "__main__":
    # 测试数据清洗
    EXCEL_PATH = "全校课表8.31导出.xlsx"
    SHEET_NAME = "sheet1"
    
    df = pd.read_excel(EXCEL_PATH, sheet_name=SHEET_NAME)
    cleaned_df = clean_and_normalize_data(df)
    
    print("=== 清洗后数据预览 ===")
    print(cleaned_df[['上课地点', 'classroom_list', '上课节次', 'section_list', 'weekday']].head(10))
    
    print("\n=== 教室使用索引示例 ===")
    classroom_index = create_classroom_index(cleaned_df)
    
    # 查看周一第1-2节的使用情况
    weekday = 1
    section = 1
    if weekday in classroom_index:
        occupied_classrooms = set()
        for classroom, sections in classroom_index[weekday].items():
            if section in sections:
                occupied_classrooms.add(classroom)
        
        print(f"周{weekday}第{section}节有课的教室: {len(occupied_classrooms)}个")
        print("示例:", list(occupied_classrooms)[:5])
    
    print("\n=== 所有教室统计 ===")
    all_classrooms = get_all_classrooms(cleaned_df)
    print(f"总教室数: {len(all_classrooms)}")
    
    print("\n=== 楼栋统计 ===")
    buildings = get_buildings(cleaned_df)
    for building, classrooms in sorted(buildings.items()):
        print(f"{building}: {len(classrooms)}个教室")