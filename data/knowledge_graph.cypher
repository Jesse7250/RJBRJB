// ============================================================
// 智学蜂巢 - Python 程序设计课程知识图谱种子数据
// 节点数：约 40 个核心知识点
// ============================================================

// 清除已有数据
MATCH (n) DETACH DELETE n;

// ==================== 基础语法模块 ====================
CREATE (:Concept {
    name: 'Python简介',
    module: '基础语法',
    difficulty: 1,
    category: 'theory',
    estimated_time: 15,
    description: 'Python语言的特点、应用领域和开发环境',
    common_pitfalls: ['混淆Python2和Python3语法'],
    learning_objectives: ['了解Python特点', '能运行第一个Python程序']
});

CREATE (:Concept {
    name: '变量与赋值',
    module: '基础语法',
    difficulty: 1,
    category: 'theory',
    estimated_time: 20,
    description: 'Python中变量的概念、命名规则和赋值操作',
    common_pitfalls: ['变量名与关键字冲突', '赋值与比较混淆'],
    learning_objectives: ['理解变量是内存引用', '掌握合法命名规则', '区分=和=='],
    allowed_modules: []
});

CREATE (:Concept {
    name: '基本数据类型',
    module: '基础语法',
    difficulty: 1,
    category: 'theory',
    estimated_time: 30,
    description: '整数、浮点数、字符串、布尔型、空值',
    common_pitfalls: ['字符串和数字直接拼接报错', '浮点数精度问题'],
    learning_objectives: ['掌握int/float/str/bool/NoneType', '能进行类型转换'],
    allowed_modules: []
});

CREATE (:Concept {
    name: '运算符',
    module: '基础语法',
    difficulty: 1,
    category: 'theory',
    estimated_time: 20,
    description: '算术运算符、比较运算符、逻辑运算符、赋值运算符',
    common_pitfalls: ['== 和 = 混淆', 'and/or 短路求值不理解'],
    learning_objectives: ['熟练使用各类运算符', '理解运算符优先级'],
    allowed_modules: []
});

CREATE (:Concept {
    name: '输入与输出',
    module: '基础语法',
    difficulty: 1,
    category: 'practical',
    estimated_time: 20,
    description: 'print函数和input函数的使用',
    common_pitfalls: ['input返回的是字符串', 'print多个参数格式错误'],
    learning_objectives: ['掌握print格式化输出', '掌握input获取用户输入'],
    allowed_modules: []
});

// ==================== 控制流模块 ====================
CREATE (:Concept {
    name: '条件语句',
    module: '控制流',
    difficulty: 2,
    category: 'practical',
    estimated_time: 30,
    description: 'if、elif、else条件判断语句',
    common_pitfalls: ['忘记冒号', '缩进错误', '条件判断范围重叠'],
    learning_objectives: ['掌握if-elif-else结构', '能写多分支程序'],
    allowed_modules: []
});

CREATE (:Concept {
    name: 'for循环',
    module: '控制流',
    difficulty: 2,
    category: 'practical',
    estimated_time: 35,
    description: 'for循环遍历可迭代对象',
    common_pitfalls: ['循环变量修改导致混乱', '忘记range是左闭右开'],
    learning_objectives: ['掌握for循环遍历列表/字符串', '掌握range函数'],
    allowed_modules: []
});

CREATE (:Concept {
    name: 'while循环',
    module: '控制流',
    difficulty: 2,
    category: 'practical',
    estimated_time: 30,
    description: 'while循环和循环控制语句',
    common_pitfalls: ['死循环', '循环条件更新位置错误'],
    learning_objectives: ['掌握while循环', '掌握break和continue'],
    allowed_modules: []
});

CREATE (:Concept {
    name: '嵌套循环',
    module: '控制流',
    difficulty: 3,
    category: 'practical',
    estimated_time: 35,
    description: '循环语句的嵌套使用',
    common_pitfalls: ['内外层循环变量混淆', '缩进层级混乱'],
    learning_objectives: ['能写二维遍历', '理解循环嵌套复杂度'],
    allowed_modules: []
});

// ==================== 数据结构模块 ====================
CREATE (:Concept {
    name: '列表',
    module: '数据结构',
    difficulty: 2,
    category: 'practical',
    estimated_time: 40,
    description: '列表的创建、索引、切片、常用方法',
    common_pitfalls: ['切片超出范围不报错', '赋值是引用而非复制', 'append和extend混淆'],
    learning_objectives: ['掌握列表增删改查', '掌握列表推导式基础'],
    allowed_modules: []
});

CREATE (:Concept {
    name: '字典',
    module: '数据结构',
    difficulty: 2,
    category: 'practical',
    estimated_time: 40,
    description: '字典的创建、访问、修改和遍历',
    common_pitfalls: ['访问不存在的键报错', 'keys()/values()/items()混淆'],
    learning_objectives: ['掌握字典基本操作', '能处理键值对数据'],
    allowed_modules: []
});

CREATE (:Concept {
    name: '元组',
    module: '数据结构',
    difficulty: 2,
    category: 'theory',
    estimated_time: 20,
    description: '不可变序列元组的特点和使用场景',
    common_pitfalls: ['试图修改元组元素', '单元素元组逗号遗漏'],
    learning_objectives: ['理解元组不可变性', '掌握元组解包'],
    allowed_modules: []
});

CREATE (:Concept {
    name: '集合',
    module: '数据结构',
    difficulty: 3,
    category: 'theory',
    estimated_time: 25,
    description: '集合的去重、交集、并集、差集',
    common_pitfalls: ['集合是无序的', '集合元素必须可哈希'],
    learning_objectives: ['掌握集合基本运算', '能用集合去重'],
    allowed_modules: []
});

CREATE (:Concept {
    name: '字符串操作',
    module: '数据结构',
    difficulty: 2,
    category: 'practical',
    estimated_time: 35,
    description: '字符串索引、切片、格式化、常用方法',
    common_pitfalls: ['字符串不可变', 'split返回列表', 'replace不改变原字符串'],
    learning_objectives: ['熟练使用字符串方法', '掌握f-string格式化'],
    allowed_modules: []
});

// ==================== 函数模块 ====================
CREATE (:Concept {
    name: '函数定义与调用',
    module: '函数',
    difficulty: 2,
    category: 'practical',
    estimated_time: 35,
    description: 'def定义函数、参数、返回值',
    common_pitfalls: ['定义和调用混淆', 'return位置错误', '局部变量和全局变量混淆'],
    learning_objectives: ['能定义和调用函数', '理解参数和返回值'],
    allowed_modules: []
});

CREATE (:Concept {
    name: '函数参数',
    module: '函数',
    difficulty: 3,
    category: 'theory',
    estimated_time: 40,
    description: '位置参数、关键字参数、默认参数、可变参数',
    common_pitfalls: ['默认参数是可变对象', '*args和**kwargs混淆', '参数顺序错误'],
    learning_objectives: ['掌握各种参数形式', '能编写灵活函数'],
    allowed_modules: []
});

CREATE (:Concept {
    name: '变量作用域',
    module: '函数',
    difficulty: 3,
    category: 'theory',
    estimated_time: 30,
    description: '局部变量、全局变量、LEGB规则',
    common_pitfalls: ['函数内修改全局变量未加global', '闭包变量绑定时机'],
    learning_objectives: ['理解LEGB规则', '能正确处理作用域问题'],
    allowed_modules: []
});

CREATE (:Concept {
    name: '递归函数',
    module: '函数',
    difficulty: 4,
    category: 'practical',
    estimated_time: 40,
    description: '函数调用自身的思想和经典案例',
    common_pitfalls: ['缺少终止条件导致栈溢出', '递归效率低'],
    learning_objectives: ['理解递归思想', '能写简单递归函数'],
    allowed_modules: []
});

// ==================== 文件操作模块 ====================
CREATE (:Concept {
    name: '文件操作',
    module: '文件IO',
    difficulty: 3,
    category: 'practical',
    estimated_time: 35,
    description: '文件的打开、读取、写入和关闭',
    common_pitfalls: ['忘记close文件', '编码错误导致乱码', '模式选择错误'],
    learning_objectives: ['掌握open()函数', '理解with语句', '能读写文本文件'],
    allowed_modules: []
});

CREATE (:Concept {
    name: 'CSV文件处理',
    module: '文件IO',
    difficulty: 3,
    category: 'practical',
    estimated_time: 30,
    description: '使用csv模块读写CSV文件',
    common_pitfalls: ['CSV写入需要newline参数', '编码问题'],
    learning_objectives: ['掌握csv.reader/csv.writer', '能处理表格数据'],
    allowed_modules: ['csv']
});

CREATE (:Concept {
    name: 'JSON文件处理',
    module: '文件IO',
    difficulty: 3,
    category: 'practical',
    estimated_time: 30,
    description: '使用json模块读写JSON文件',
    common_pitfalls: ['JSON键必须是字符串', '中文字符编码'],
    learning_objectives: ['掌握json.load/json.dump', '能处理JSON数据'],
    allowed_modules: ['json']
});

// ==================== 异常处理模块 ====================
CREATE (:Concept {
    name: '异常处理',
    module: '异常处理',
    difficulty: 3,
    category: 'practical',
    estimated_time: 35,
    description: 'try/except/else/finally异常处理机制',
    common_pitfalls: ['捕获所有异常', '异常类型判断错误', 'finally中return'],
    learning_objectives: ['掌握try-except结构', '能捕获特定异常'],
    allowed_modules: []
});

CREATE (:Concept {
    name: '常见异常类型',
    module: '异常处理',
    difficulty: 2,
    category: 'theory',
    estimated_time: 25,
    description: 'ValueError、TypeError、IndexError等常见异常',
    common_pitfalls: ['异常类型混淆', '不知道查看traceback'],
    learning_objectives: ['认识常见异常', '能读懂报错信息'],
    allowed_modules: []
});

// ==================== 面向对象模块 ====================
CREATE (:Concept {
    name: '类与对象',
    module: '面向对象',
    difficulty: 3,
    category: 'theory',
    estimated_time: 45,
    description: '类的定义、属性、方法、对象创建',
    common_pitfalls: ['self忘记写', '实例属性和类属性混淆', '方法调用方式错误'],
    learning_objectives: ['理解面向对象思想', '能定义简单类'],
    allowed_modules: []
});

CREATE (:Concept {
    name: '构造方法与魔术方法',
    module: '面向对象',
    difficulty: 3,
    category: 'theory',
    estimated_time: 35,
    description: '__init__、__str__、__repr__等魔术方法',
    common_pitfalls: ['__init__拼写错误', '魔术方法返回值类型错误'],
    learning_objectives: ['掌握__init__', '了解常用魔术方法'],
    allowed_modules: []
});

CREATE (:Concept {
    name: '继承与多态',
    module: '面向对象',
    difficulty: 4,
    category: 'theory',
    estimated_time: 45,
    description: '类的继承、方法重写、多态',
    common_pitfalls: ['super()用法错误', '多重继承的MRO问题'],
    learning_objectives: ['理解继承', '能写简单继承体系'],
    allowed_modules: []
});

// ==================== 常用标准库模块 ====================
CREATE (:Concept {
    name: 'math模块',
    module: '标准库',
    difficulty: 2,
    category: 'practical',
    estimated_time: 20,
    description: '数学函数库的基本使用',
    common_pitfalls: ['math.sin参数是弧度', '整数除法和浮点除法混淆'],
    learning_objectives: ['掌握常用math函数', '能进行数学计算'],
    allowed_modules: ['math']
});

CREATE (:Concept {
    name: 'random模块',
    module: '标准库',
    difficulty: 2,
    category: 'practical',
    estimated_time: 20,
    description: '随机数生成',
    common_pitfalls: ['randint边界包含', 'random.seed作用'],
    learning_objectives: ['掌握random常用函数', '能生成随机数据'],
    allowed_modules: ['random']
});

CREATE (:Concept {
    name: 'datetime模块',
    module: '标准库',
    difficulty: 3,
    category: 'practical',
    estimated_time: 30,
    description: '日期时间处理',
    common_pitfalls: ['strftime和strptime混淆', '时区问题'],
    learning_objectives: ['掌握datetime基本操作', '能格式化日期时间'],
    allowed_modules: ['datetime']
});

CREATE (:Concept {
    name: 'os模块',
    module: '标准库',
    difficulty: 3,
    category: 'practical',
    estimated_time: 25,
    description: '操作系统接口，文件路径处理',
    common_pitfalls: ['路径分隔符问题', '相对路径和绝对路径混淆'],
    learning_objectives: ['掌握os.path常用方法', '能处理文件路径'],
    allowed_modules: ['os']
});

// ==================== 高级主题模块 ====================
CREATE (:Concept {
    name: '列表推导式',
    module: '高级语法',
    difficulty: 3,
    category: 'practical',
    estimated_time: 30,
    description: '列表推导式的语法和应用',
    common_pitfalls: ['嵌套推导式可读性差', '条件位置错误'],
    learning_objectives: ['掌握列表推导式', '能用推导式简化代码'],
    allowed_modules: []
});

CREATE (:Concept {
    name: '生成器',
    module: '高级语法',
    difficulty: 4,
    category: 'theory',
    estimated_time: 35,
    description: 'yield生成器和生成器表达式',
    common_pitfalls: ['生成器只能迭代一次', 'yield和return混淆'],
    learning_objectives: ['理解惰性求值', '能写简单生成器'],
    allowed_modules: []
});

CREATE (:Concept {
    name: '装饰器',
    module: '高级语法',
    difficulty: 5,
    category: 'theory',
    estimated_time: 45,
    description: '函数装饰器的基本原理和使用',
    common_pitfalls: ['装饰器返回的是新函数', '带参数装饰器层级混乱'],
    learning_objectives: ['理解装饰器原理', '能使用内置装饰器'],
    allowed_modules: []
});

// ==================== 依赖关系 ====================
// 基础语法 -> 控制流
MATCH (a:Concept {name: '变量与赋值'}), (b:Concept {name: '基本数据类型'})
CREATE (a)-[:PREREQUISITE_OF {strength: 0.9}]->(b);

MATCH (a:Concept {name: '基本数据类型'}), (b:Concept {name: '运算符'})
CREATE (a)-[:PREREQUISITE_OF {strength: 0.9}]->(b);

MATCH (a:Concept {name: '运算符'}), (b:Concept {name: '输入与输出'})
CREATE (a)-[:PREREQUISITE_OF {strength: 0.8}]->(b);

MATCH (a:Concept {name: '基本数据类型'}), (b:Concept {name: '条件语句'})
CREATE (a)-[:PREREQUISITE_OF {strength: 0.9}]->(b);

MATCH (a:Concept {name: '运算符'}), (b:Concept {name: '条件语句'})
CREATE (a)-[:PREREQUISITE_OF {strength: 0.9}]->(b);

MATCH (a:Concept {name: '条件语句'}), (b:Concept {name: 'for循环'})
CREATE (a)-[:PREREQUISITE_OF {strength: 0.8}]->(b);

MATCH (a:Concept {name: '条件语句'}), (b:Concept {name: 'while循环'})
CREATE (a)-[:PREREQUISITE_OF {strength: 0.8}]->(b);

MATCH (a:Concept {name: 'for循环'}), (b:Concept {name: '嵌套循环'})
CREATE (a)-[:PREREQUISITE_OF {strength: 0.9}]->(b);

MATCH (a:Concept {name: 'while循环'}), (b:Concept {name: '嵌套循环'})
CREATE (a)-[:PREREQUISITE_OF {strength: 0.8}]->(b);

// 控制流 -> 数据结构
MATCH (a:Concept {name: 'for循环'}), (b:Concept {name: '列表'})
CREATE (a)-[:PREREQUISITE_OF {strength: 0.8}]->(b);

MATCH (a:Concept {name: '基本数据类型'}), (b:Concept {name: '字符串操作'})
CREATE (a)-[:PREREQUISITE_OF {strength: 0.9}]->(b);

MATCH (a:Concept {name: '列表'}), (b:Concept {name: '字典'})
CREATE (a)-[:PREREQUISITE_OF {strength: 0.7}]->(b);

MATCH (a:Concept {name: '列表'}), (b:Concept {name: '元组'})
CREATE (a)-[:PREREQUISITE_OF {strength: 0.8}]->(b);

MATCH (a:Concept {name: '列表'}), (b:Concept {name: '集合'})
CREATE (a)-[:PREREQUISITE_OF {strength: 0.7}]->(b);

// 数据结构 -> 函数
MATCH (a:Concept {name: '条件语句'}), (b:Concept {name: '函数定义与调用'})
CREATE (a)-[:PREREQUISITE_OF {strength: 0.8}]->(b);

MATCH (a:Concept {name: '基本数据类型'}), (b:Concept {name: '函数定义与调用'})
CREATE (a)-[:PREREQUISITE_OF {strength: 0.7}]->(b);

MATCH (a:Concept {name: '函数定义与调用'}), (b:Concept {name: '函数参数'})
CREATE (a)-[:PREREQUISITE_OF {strength: 0.9}]->(b);

MATCH (a:Concept {name: '函数定义与调用'}), (b:Concept {name: '变量作用域'})
CREATE (a)-[:PREREQUISITE_OF {strength: 0.8}]->(b);

MATCH (a:Concept {name: '函数定义与调用'}), (b:Concept {name: '递归函数'})
CREATE (a)-[:PREREQUISITE_OF {strength: 0.9}]->(b);

// 函数 -> 文件与异常
MATCH (a:Concept {name: '函数定义与调用'}), (b:Concept {name: '文件操作'})
CREATE (a)-[:PREREQUISITE_OF {strength: 0.7}]->(b);

MATCH (a:Concept {name: '字符串操作'}), (b:Concept {name: '文件操作'})
CREATE (a)-[:PREREQUISITE_OF {strength: 0.7}]->(b);

MATCH (a:Concept {name: '文件操作'}), (b:Concept {name: 'CSV文件处理'})
CREATE (a)-[:PREREQUISITE_OF {strength: 0.9}]->(b);

MATCH (a:Concept {name: '文件操作'}), (b:Concept {name: 'JSON文件处理'})
CREATE (a)-[:PREREQUISITE_OF {strength: 0.9}]->(b);

MATCH (a:Concept {name: '常见异常类型'}), (b:Concept {name: '异常处理'})
CREATE (a)-[:PREREQUISITE_OF {strength: 0.9}]->(b);

MATCH (a:Concept {name: '条件语句'}), (b:Concept {name: '常见异常类型'})
CREATE (a)-[:PREREQUISITE_OF {strength: 0.6}]->(b);

// 函数 -> 面向对象
MATCH (a:Concept {name: '函数定义与调用'}), (b:Concept {name: '类与对象'})
CREATE (a)-[:PREREQUISITE_OF {strength: 0.8}]->(b);

MATCH (a:Concept {name: '变量作用域'}), (b:Concept {name: '类与对象'})
CREATE (a)-[:PREREQUISITE_OF {strength: 0.6}]->(b);

MATCH (a:Concept {name: '类与对象'}), (b:Concept {name: '构造方法与魔术方法'})
CREATE (a)-[:PREREQUISITE_OF {strength: 0.9}]->(b);

MATCH (a:Concept {name: '类与对象'}), (b:Concept {name: '继承与多态'})
CREATE (a)-[:PREREQUISITE_OF {strength: 0.9}]->(b);

// 基础 -> 标准库
MATCH (a:Concept {name: '基本数据类型'}), (b:Concept {name: 'math模块'})
CREATE (a)-[:PREREQUISITE_OF {strength: 0.6}]->(b);

MATCH (a:Concept {name: '基本数据类型'}), (b:Concept {name: 'random模块'})
CREATE (a)-[:PREREQUISITE_OF {strength: 0.6}]->(b);

MATCH (a:Concept {name: '字符串操作'}), (b:Concept {name: 'datetime模块'})
CREATE (a)-[:PREREQUISITE_OF {strength: 0.7}]->(b);

MATCH (a:Concept {name: '文件操作'}), (b:Concept {name: 'os模块'})
CREATE (a)-[:PREREQUISITE_OF {strength: 0.8}]->(b);

// 数据结构 -> 高级语法
MATCH (a:Concept {name: 'for循环'}), (b:Concept {name: '列表推导式'})
CREATE (a)-[:PREREQUISITE_OF {strength: 0.9}]->(b);

MATCH (a:Concept {name: '列表推导式'}), (b:Concept {name: '生成器'})
CREATE (a)-[:PREREQUISITE_OF {strength: 0.8}]->(b);

MATCH (a:Concept {name: '函数参数'}), (b:Concept {name: '装饰器'})
CREATE (a)-[:PREREQUISITE_OF {strength: 0.8}]->(b);

// ==================== 易错点节点 ====================
CREATE (:Pitfall {
    id: 'pitfall_001',
    description: '使用关键字作为变量名',
    example: 'class = "Math"  # SyntaxError',
    solution: '避免使用Python关键字，可用class_name代替',
    frequency: 'high'
});

CREATE (:Pitfall {
    id: 'pitfall_002',
    description: '忘记close文件',
    example: 'f = open("a.txt"); f.read()  # 忘记close',
    solution: '使用with语句自动管理文件关闭',
    frequency: 'high'
});

CREATE (:Pitfall {
    id: 'pitfall_003',
    description: '列表赋值是引用而非复制',
    example: 'a = [1,2,3]; b = a; b[0]=9  # a也变了',
    solution: '使用copy()或切片[:]创建副本',
    frequency: 'high'
});

CREATE (:Pitfall {
    id: 'pitfall_004',
    description: 'input返回字符串',
    example: 'age = input("年龄:"); age > 18  # TypeError',
    solution: '需要时用int()/float()转换',
    frequency: 'high'
});

// 关联易错点
MATCH (c:Concept {name: '变量与赋值'}), (p:Pitfall {id: 'pitfall_001'})
CREATE (c)-[:HAS_PITFALL]->(p);

MATCH (c:Concept {name: '文件操作'}), (p:Pitfall {id: 'pitfall_002'})
CREATE (c)-[:HAS_PITFALL]->(p);

MATCH (c:Concept {name: '列表'}), (p:Pitfall {id: 'pitfall_003'})
CREATE (c)-[:HAS_PITFALL]->(p);

MATCH (c:Concept {name: '输入与输出'}), (p:Pitfall {id: 'pitfall_004'})
CREATE (c)-[:HAS_PITFALL]->(p);

// ==================== 查询验证 ====================
MATCH (c:Concept) RETURN count(c) as concept_count;
MATCH ()-[r:PREREQUISITE_OF]->() RETURN count(r) as relation_count;
