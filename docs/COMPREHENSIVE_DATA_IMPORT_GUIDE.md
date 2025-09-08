# 电网招生系统综合数据导入完整指南

## 🎯 项目概览

本项目提供了一套完整的电网招生数据处理解决方案，能够从Excel文件的9个工作表中提取、清洗、分类和导入所有数据，包括客资记录、话术库、知识库、校招信息等。

### 📊 数据概况

**Excel文件包含的9个工作表:**
1. **客资记录** (1965行) - 客户信息和转化数据
2. **最新电网术库** (143行) - 电网考试相关问答
3. **考研话术库** (13行) - 考研咨询话术  
4. **话术库** (239行) - 销售对话记录
5. **小红书回复话术** (14行) - 社交媒体回复模板
6. **校招信息** (123行) - 各省电网招聘信息
7. **夏蝉销售明细** (51行) - 销售数据
8. **白鸽销售明细** (218行) - 销售跟进记录  
9. **淘宝每日销售额** (79行) - 电商销售数据

## 🔧 技术架构

### 核心组件

1. **ComprehensiveDataProcessor** - 综合数据处理器
2. **DataCompletionTool** - 数据补全优化工具
3. **ExtendedDatabaseManager** - 扩展数据库管理器
4. **分类标签体系** - 智能分类和标签管理

### 数据处理流程

```
Excel多表数据 → 数据提取 → 智能清洗 → 质量评估 → 自动补全 → 分类标签 → 数据库导入
```

## 📋 详细数据处理策略

### 1. 客资记录处理

**原始数据问题:**
- 日期格式混乱(Excel序列号45693、文本"2.5"、"2.6已报")
- 手机号字段包含非手机号内容
- 成交日期包含状态描述

**处理策略:**
```python
# 日期标准化
def _clean_date(self, date_value):
    # Excel序列号 → 2025-02-05
    # 文本"2.5" → 2025-02-05  
    # "2.6已报" → 2025-02-06 (提取状态到备注)

# 状态智能判断
def _determine_status(self, deal_date, add_date, customer_date):
    if deal_date: return '已成交'
    elif add_date: return '跟进中'  
    else: return '潜在'
```

### 2. 电网术库处理

**数据特点:**
- 143条问答，10个分类
- 64.3%缺失分类信息
- 27.3%缺失问题，28.7%缺失答案

**处理方案:**
```python
# 分类继承和问题生成
current_category = None
for row in df.iterrows():
    if pd.notna(row['类型']):
        current_category = row['类型']  # 分类向下继承
    
    if question and answer:
        title = self._generate_title_from_question(question)
        keywords = self._extract_keywords(question, answer, current_category)
```

**分类标准:**
- 考试和复习规划 (8条)
- 课程介绍 (8条)  
- 答疑服务 (7条)
- 网申相关 (5条)
- 小程序功能 (10条)

### 3. 考研话术库处理

**数据结构:**
- 3列无标题结构，需要智能解析
- 层次化分类(主分类-子分类-具体内容)

**处理逻辑:**
```python
# 三级分类解析
主分类: "生源目标院校分类"  
子分类: "本科985/211目标985/211"
内容: "在校成绩只要不是垫底的..."

# 自动生成问题
def _generate_postgrad_question(sub_category, main_category):
    templates = {
        '本科985/211目标985/211': '本科985/211院校，想考研985/211应该如何规划？',
        '本科电校，目标985/211': '电力院校本科生考研985/211有什么优势？'
    }
```

### 4. 话术库对话记录处理

**数据特点:**
- 239条销售对话记录
- 列名是具体内容，需要重新解析
- 包含客户信息和对话内容

**场景分析算法:**
```python
def _analyze_conversation_scenario(self, conversation):
    scenario_keywords = {
        '价格咨询': ['价格', '费用', '多少钱', '收费', '优惠'],
        '课程咨询': ['课程', '内容', '体系', '学习', '教学'],
        '效果咨询': ['效果', '通过率', '成绩', '保障'],
        '回访跟进': ['回访', '体验', '怎么样', '满意'],
        '成交促进': ['报名', '报班', '决定', '考虑']
    }
```

### 5. 小红书回复话术处理

**分类优化:**
```python
def _categorize_xiaohongshu_question(self, question):
    categories = {
        '出路规划': ['出路', '规划', '选择', '未来'],
        '考试对比': ['考研', '考国网', '对比', '还是'],
        '备考指导': ['备考', '复习', '准备', '学习'],
        '政策咨询': ['政策', '要求', '条件', '规定'],
        '院校选择': ['院校', '学校', '专业', '选择']
    }
```

### 6. 校招信息知识库处理

**智能分析:**
```python  
def _analyze_recruitment_info(self, info):
    analysis = {
        'has_interview_process': '面试|笔试|流程' in info,
        'has_requirements': '要求|条件|成绩|学历' in info,  
        'has_results': '给了|签约|录取|通过' in info,
        'difficulty_level': self._assess_difficulty(info)
    }
```

**关键信息提取:**
- 招聘单位和站点
- 面试流程和要求
- 录取结果和难度评估
- 时间节点和注意事项

## 🏷️ 智能标签体系

### 标签分层结构

#### 一级标签 (主分类)
- **考试类别**: 电网考试、考研、校招、其他
- **内容类型**: 政策、技巧、经验、资讯  
- **难度级别**: 基础、中级、高级、专家

#### 二级标签 (细分类)
- **科目标签**: 电路、电机、电分、继保、高压
- **学历标签**: 专科、本科、硕士、博士
- **地区标签**: 华北、华东、华南、西北、西南
- **时效标签**: 2025年、最新、历史、趋势

#### 三级标签 (具体标签)  
- **具体院校**: 华电、西交、上电、哈工大
- **具体专业**: 电气工程、自动化、计算机
- **具体问题**: 网申、面试、笔试、体检

### 自动标签生成算法

```python
def _extract_keywords(self, question, answer, category):
    keywords = set()
    
    # 1. jieba分词提取
    jieba_keywords = jieba.analyse.extract_tags(text, topK=5)
    keywords.update(jieba_keywords)
    
    # 2. 分类相关关键词
    if category in category_keywords:
        for kw in category_keywords[category]:
            if kw in text:
                keywords.add(kw)
    
    # 3. 专业术语提取
    professional_terms = re.findall(r'电\w{1,3}|网\w{1,3}|考\w{1,3}', text)
    keywords.update(professional_terms)
    
    return list(keywords)[:8]
```

## 🔄 数据补全和质量优化

### 质量评估体系 (100分制)

- **标题完整性**: 20分
- **问题完整性**: 25分
- **答案完整性**: 35分  
- **分类准确性**: 10分
- **标签完整性**: 10分

### 质量等级划分

- **A级(90-100分)**: 信息完整、格式规范、内容准确
- **B级(80-89分)**: 基本完整、需要少量优化  
- **C级(60-79分)**: 部分缺失、需要补全优化
- **D级(0-59分)**: 严重缺失、需要重新整理

### 自动补全策略

#### 只有标题的数据
```python
# 智能问题生成
标题: "电网考试备考时间规划"  
生成问题: "电网考试需要多长时间备考？如何制定复习计划？"

# 答案模板匹配
if "备考时间" in title:
    answer_template = "根据个人基础和目标分数，建议备考时间为..."
```

#### 只有问题的数据
```python
# 标题提取  
问题: "大四开始备考电网来得及吗？"
生成标题: "大四备考电网时间规划"

# 分类自动判断
category = auto_categorize(question_content)
```

#### 答案模板生成
```python
answer_templates = {
    '备考规划': '根据个人基础和目标，建议制定分阶段的备考计划：\n1. 基础阶段：...',
    '课程介绍': '我们的{subject}课程包含：\n1. 系统性教学内容...',
    '政策解读': '根据最新政策规定：\n1. {policy_point1}...',
    '效果保障': '我们提供全方位的学习保障：\n1. 专业的课程体系...'
}
```

## 🗄️ 数据库设计

### 核心表结构

#### 1. 扩展话术库表 (scripts_extended)
```sql
CREATE TABLE scripts_extended (
    id INT AUTO_INCREMENT PRIMARY KEY,
    category VARCHAR(100) NOT NULL COMMENT '话术分类',
    title VARCHAR(200) NOT NULL COMMENT '话术标题',
    question TEXT COMMENT '问题',
    answer TEXT NOT NULL COMMENT '答案',
    keywords VARCHAR(500) COMMENT '关键词',
    type ENUM('grid_exam', 'postgrad_consult', 'sales_conversation', 'social_media_reply') NOT NULL,
    source VARCHAR(100) COMMENT '数据来源',
    platform VARCHAR(50) COMMENT '适用平台',
    usage_count INT DEFAULT 0 COMMENT '使用次数',
    effectiveness FLOAT DEFAULT 0 COMMENT '有效性评分',
    quality_score INT COMMENT '数据质量得分',
    quality_level CHAR(1) COMMENT '质量等级A/B/C/D',
    FULLTEXT idx_content (title, question, answer, keywords)
);
```

#### 2. 扩展知识库表 (knowledge_extended)  
```sql
CREATE TABLE knowledge_extended (
    id INT AUTO_INCREMENT PRIMARY KEY,
    type ENUM('电网考试', '考研', '校招', '其他') NOT NULL,
    category VARCHAR(100) COMMENT '知识分类',
    question TEXT COMMENT '问题', 
    answer TEXT COMMENT '答案',
    related_questions TEXT COMMENT '相关问题',
    tags VARCHAR(500) COMMENT '标签',
    source VARCHAR(100) COMMENT '数据来源',
    unit VARCHAR(100) COMMENT '单位/机构',
    site VARCHAR(100) COMMENT '站点/地点',
    metadata JSON COMMENT '扩展元数据',
    view_count INT DEFAULT 0,
    FULLTEXT idx_content (question, answer, tags)
);
```

## 🚀 使用方法

### 1. 环境准备

```bash
# 安装依赖
pip install pandas pymysql numpy openpyxl xlrd jieba

# 确保MySQL服务运行
sudo systemctl start mysql
```

### 2. 数据库配置

```python
# 修改comprehensive_data_processor.py中的配置
db_config = {
    'host': 'localhost',
    'user': 'root', 
    'password': 'your_password',  # 修改为实际密码
    'charset': 'utf8mb4'
}
```

### 3. 执行数据导入

```bash
# 方式1：使用综合处理器（推荐）
python comprehensive_data_processor.py

# 方式2：先测试数据补全工具
python data_completion_tool.py
```

### 4. 数据质量检查

```sql
-- 检查导入结果
SELECT 
    type,
    COUNT(*) as total,
    AVG(usage_count) as avg_usage,
    COUNT(CASE WHEN quality_level = 'A' THEN 1 END) as grade_a,
    COUNT(CASE WHEN quality_level = 'B' THEN 1 END) as grade_b
FROM scripts_extended 
GROUP BY type;

-- 全文搜索测试
SELECT title, category, quality_level 
FROM scripts_extended 
WHERE MATCH(title, question, answer, keywords) AGAINST('备考 复习' IN NATURAL LANGUAGE MODE)
LIMIT 10;
```

## 📊 预期导入结果

### 话术库数据统计
- **电网考试话术**: ~104条 (最新电网术库)
- **考研咨询话术**: ~10条 (考研话术库)  
- **销售对话话术**: ~198条 (话术库)
- **社交媒体话术**: ~12条 (小红书回复话术)
- **总计**: ~324条话术记录

### 知识库数据统计  
- **校招信息**: ~123条 (校招信息表)
- **销售数据**: ~348条 (销售明细表)
- **总计**: ~471条知识记录

### 客户数据统计
- **有效客户记录**: ~1876条
- **转化率**: 约9.4%
- **主要渠道**: 抖音46.2%、小红书39.4%

### 数据质量预期
- **A级数据**: 30-40% (信息完整、格式规范)
- **B级数据**: 35-45% (基本完整、轻微优化)
- **C级数据**: 15-25% (部分缺失、需要补全)
- **D级数据**: 5-10% (严重缺失、需要人工处理)

## 🎯 核心优势

### 1. 全面数据覆盖
✅ 处理9个工作表的所有数据类型  
✅ 客资、话术、知识、校招信息一次性导入  
✅ 支持不同数据格式和结构

### 2. 智能数据处理
✅ 自动识别和修复数据质量问题  
✅ 智能分类和标签生成  
✅ 缺失数据自动补全

### 3. 灵活分类体系
✅ 多层次标签分类系统  
✅ 支持全文搜索和多维度筛选  
✅ 个性化推荐和智能匹配

### 4. 质量保障机制
✅ 完整的数据质量评估体系  
✅ 自动优化和人工审核相结合  
✅ 可追溯的数据处理记录

## 🔍 高级特性

### 智能搜索功能

```python
# 多维度搜索实现
def search_knowledge(query, filters=None):
    # 1. 全文检索
    fulltext_results = full_text_search(query)
    
    # 2. 标签匹配  
    tag_results = tag_based_search(query)
    
    # 3. 语义搜索
    semantic_results = semantic_similarity_search(query)
    
    # 4. 结果融合排序
    final_results = merge_and_rank(fulltext_results, tag_results, semantic_results)
    
    return final_results
```

### 个性化推荐

```python
# 推荐算法
def recommend_content(user_id, content_type):
    user_behavior = get_user_behavior(user_id)
    similar_users = find_similar_users(user_behavior)
    
    # 基于协同过滤的推荐
    collaborative_recommendations = collaborative_filtering(similar_users)
    
    # 基于内容的推荐  
    content_recommendations = content_based_filtering(user_behavior)
    
    # 热门内容推荐
    trending_recommendations = get_trending_content(content_type)
    
    return merge_recommendations(collaborative_recommendations, 
                               content_recommendations, 
                               trending_recommendations)
```

### 数据监控和分析

```python
# 数据质量监控
def monitor_data_quality():
    quality_metrics = {
        'completeness_rate': calculate_completeness_rate(),
        'accuracy_score': calculate_accuracy_score(), 
        'consistency_score': calculate_consistency_score(),
        'timeliness_score': calculate_timeliness_score()
    }
    
    if quality_metrics['completeness_rate'] < 0.8:
        trigger_data_improvement_process()
    
    return quality_metrics
```

## 📈 后续优化建议

### 1. 数据增强
- 定期更新话术库内容  
- 添加用户反馈和评价机制
- 集成更多数据源(官网、论坛等)

### 2. AI能力增强
- 集成大语言模型优化答案质量
- 实现智能对话机器人
- 添加情感分析和用户画像

### 3. 系统集成
- 与CRM系统集成
- 添加数据可视化dashboard  
- 实现移动端应用支持

### 4. 性能优化
- 添加Redis缓存机制
- 实现数据分片和读写分离
- 优化搜索算法和索引结构

这套综合数据处理方案不仅解决了当前的数据导入需求，还为未来的系统扩展和优化奠定了坚实基础。通过智能分类、自动补全和质量评估，确保了数据的高质量和高可用性。