# LcL Tools - Blender插件

LcL工具包是一个功能丰富的Blender插件，包含网格相交检测和BlenderToMax同步工具。

## 项目结构

```
g136_tools/
├── intersection_checker/           # 相交检测功能模块
│   ├── __init__.py                 # 模块初始化
│   ├── operators.py                # 相交检测操作符
│   ├── properties.py               # 相交检测属性定义
│   ├── ui.py                      # 相交检测UI界面
│   └── mesh_helpers.py            # 网格处理辅助函数
├── blender_to_max/                 # BlenderToMax同步功能模块
│   ├── __init__.py                # 模块初始化
│   ├── operators.py               # 同步操作符
│   ├── properties.py              # 同步属性定义
│   ├── ui.py                     # 同步UI界面
│   └── sync_utils.py             # 同步工具函数
├── __init__.py                    # 插件主入口
├── blender_manifest.toml          # Blender 4.2+ 插件清单
├── test_fbx_import.py            # FBX导入测试脚本
└── test_export.py                # FBX导出测试脚本
```

## 功能模块

### 1. 相交检测器 (Intersection Detector)
- **自相交检测**: 检测单个网格的自相交面
- **对象间相交检测**: 检测多个对象之间的相交
- **全面检测**: 同时检测自相交和对象间相交
- **实时颜色显示**: 在视口中高亮显示相交区域
- **自动更新**: 编辑模式下自动更新相交检测
- **面选择**: 快速选择相交面进行编辑

### 2. BlenderToMax同步 (BlenderToMax)
- **FBX导入**: 从Max导出的FBX文件导入到Blender
- **FBX导出**: 将对象导出为FBX文件到Max交换目录
  - 支持三种导出范围：所有对象、选中对象、可见对象
  - 默认导出所有场景中的网格和骨架对象
  - 可配置导出的对象类型（网格、骨架、曲线、曲面、空对象）
  - 可配置导出选项（修改器应用、动画数据、全局缩放）
- **智能文件检测**: 自动检测交换目录中的FBX文件
- **状态显示**: 实时显示文件存在性、大小信息和导出对象统计
- **UI设置面板**: 可展开的详细设置界面，便于快速调整导出参数
- **路径管理**: 自动管理临时交换目录，确保目录存在
- **格式兼容**: 使用与Max兼容的FBX导出设置

## 安装和使用

1. 将整个`g136_tools`文件夹放入Blender插件目录
2. 在Blender偏好设置中启用"LcL Tools"插件
3. 在3D视图侧栏的"LcL"标签页中使用功能

## 开发说明

### 模块化设计
- 每个功能模块独立管理自己的操作符、属性和UI
- 模块间通过明确的接口进行交互
- 便于功能扩展和维护

### 文件组织原则
- `operators.py`: 包含所有Blender操作符定义
- `properties.py`: 包含属性组和设置定义
- `ui.py`: 包含UI面板定义
- `*_helpers.py` / `*_utils.py`: 包含辅助函数和工具

### 扩展新功能
1. 在相应模块文件夹中创建新的功能文件
2. 在模块的`__init__.py`中注册新功能
3. 在主`__init__.py`中按需调整模块注册顺序

## 版本信息
- **版本**: 1.0.0
- **支持的Blender版本**: 4.0.0+
- **作者**: LcL Team
