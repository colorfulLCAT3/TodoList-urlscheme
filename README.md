# TodoList 跨平台待办事项应用

一个功能完善的待办事项管理应用，支持桌面端和安卓移动端，帮助用户高效管理日常任务和项目。本项目使用了ai辅助。

## 📋 项目简介

TodoList是一款真正跨平台的待办事项管理应用，基于Python和Web技术开发，同时支持桌面端（Windows）和移动端（Android），提供直观的用户界面和丰富的功能，帮助用户在不同设备上无缝管理个人任务。

本项目基于 [TangStudy 的 TodoList 开源项目](https://github.com/TangIsLearning/TodoList) 二次开发，在保留原有功能的基础上，针对实际使用场景做了大量改进与优化。

## ✨ 核心功能

### 基础功能
- **任务管理**：创建、编辑、删除任务，标记完成/未完成；移动端支持左滑任务查看/编辑/删除
- **任务分类**：创建分类、为任务添加分类、按分类筛选
- **优先级管理**：高、中、低、无优先级设置
- **开始时间**：设置任务开始日期时间，支持按列表/日历/时间轴视图查看
- **搜索与筛选**：关键词搜索、按状态/日期/标签筛选
- **统计报表**：任务完成统计和分析
- **任务提醒**：系统通知提醒，时间点可自定义（如 30/10/5 分钟前），Android 端支持后台准点提醒
- **备注折叠**：描述中 `{原文}` 包裹的内容折叠显示，点击展开

### 高级功能
- **URL Scheme 推送**：通过 `todolist://add?data=<json>` 从网页/脚本/其他应用一键推送待办（详见 [url调用方法.md](url调用方法.md)）
- **响应式设计**：适配不同屏幕尺寸
- **深色/浅色主题**：保护眼睛，支持主题切换
- **国际化功能**：支持快速切换语言，目前支持简体中文和英语
- **桌面端特色功能-窗口置顶**：支持窗口置顶功能
- **桌面端特色功能-开机自启动**：支持配置开机自启动
- **桌面端特色功能-数据自定义存储**：支持自定义配置数据文件存储路径
- **移动端特色功能-后台提醒**：使用系统精确闹钟（setAlarmClock），即使应用在后台/锁屏也能准点提醒
- **移动端特色功能-权限引导**：按手机品牌（ColorOS/MIUI/EMUI/OriginOS 等）自动检测并引导后台运行/自启动权限

### 支持平台
- **桌面端**：Windows
- **移动端**：Android

*\*说明：原项目理论上支持 macOS、Linux 和 iOS，但当前维护者仅在 Windows 与 Android 上测试，其余平台请自行验证。*

## 🚀 快速开始

### 安装方法

#### 桌面端安装

**环境要求**：
- Python >= 3.10.9

**安装步骤**：
```bash
# 1. 克隆项目
git clone https://github.com/colorfulLCAT3/TodoList-urlscheme.git
cd TodoList

# 2. 安装Python依赖
pip install -r requirements.txt

# 3. 启动应用
python main.py

# 4. 打包应用生成exe(可选)
python build.py
```

*\*说明：构建脚本使用默认图标，可通过 `scripts/utils/create_icon.py` 生成自定义图标置于根目录即可自动打包到 exe 中。*

#### 安卓移动端安装

**方式一：使用预构建APK**
1. 从项目发布页面下载最新的APK文件
2. 在安卓设备上启用「未知来源」安装
3. 安装下载的APK文件
4. 打开应用开始使用

**方式二：使用 Android Studio 构建**

> ⚠️ **注意**：当前 Android 端使用 **Android Studio 原生工程**（`android_native/`），已弃用 Buildozer / python-for-android 方案。可直接用 Android Studio 打开 `android_native/` 文件夹完成构建。

**环境要求**：
- Android Studio（含 Android SDK）
- JDK 17+
- Gradle 8.14.3（工程自带 wrapper）

**构建步骤**：
```bash
# 1. 用 Android Studio 打开 android_native/ 目录
# 2. 等待 Gradle 同步完成
# 3. 点击 Run ▶ 或构建 APK
```

或使用命令行：
```bash
cd android_native
./gradlew assembleDebug   # Windows 下为 gradlew.bat assembleDebug
```

**APK 产物**：`android_native/app/build/outputs/apk/debug/app-debug.apk`

*\*说明：Android 端通过 `assets/web/` 下的前端 + `shim/localstorage_backend.js` 在原生 WebView 中运行，数据存于 localStorage，无需 Python 后端。*

## 🔧 技术栈

- **前端**：HTML5 + CSS3 + JavaScript (ES6+)
- **桌面框架**：Python + PyWebView
- **后端**：Python 3.10.9+
- **数据库**：SQLite（本地存储）
- **Android**：Android Studio（Kotlin + WebView）+ localStorage shim
- **构建工具**：PyInstaller(桌面构建) + Gradle(Android 构建)

## 📁 项目结构

```
TodoList/
├── backend/            # 后端API和数据库操作
├── frontend/           # 前端界面和交互逻辑
├── android_native/     # Android Studio 原生工程（WebView + localStorage shim）
├── data/               # 数据库文件
├── docs/               # 项目文档资料
├── scripts/            # 脚本归档
├── tests/              # 测试（含 URL scheme 测试页）
├── TodoList.spec       # PyInstaller配置文件（用于桌面构建）
├── build.py            # 桌面端应用构建脚本
├── main.py             # 桌面端应用启动脚本
├── requirements.txt    # 项目所需的依赖包
├── url调用方法.md       # URL Scheme 推送调用说明
└── README.md           # 项目说明
```

*\*说明：启动桌面端核心仅需要 backend 目录、frontend 目录和 main.py；Android 端使用 android_native 目录。*

## 🛠️ 故障排除

### 桌面端常见问题

1. **应用无法启动**
   - 尝试: `python main.py`
   - 检查Python版本是否 >= 3.10.9
   - 确认依赖包已安装: `pip install pywebview`

2. **URL Scheme 无法唤起**
   - 确认已至少启动过一次应用（用于注册协议）
   - 检查注册表 `HKCU\Software\Classes\todolist` 是否存在
   - 尝试在命令行执行 `start todolist://add?data=...`

3. **数据同步失败**
   - 确保设备在同一局域网
   - 检查防火墙设置
   - 确认目标设备已启动共享

4. **数据库错误**
   - 检查data目录是否存在且可写
   - 删除data/todo.db重新初始化

### 安卓移动端常见问题

1. **APK安装失败**
   - 确保已启用「未知来源」安装
   - 检查设备存储空间是否充足
   - 尝试下载最新版本的APK

2. **后台提醒不生效**
   - 在「设置 → 权限申请」中完成通知/电池优化授权
   - 按手机品牌引导开启自启动（OPPO/realme 等系统会冻结后台应用）
   - 使用「设置 → 调试模式 → 发送测试闹钟」验证提醒链路

3. **应用崩溃**
   - 清理应用缓存
   - 检查安卓系统版本是否兼容
   - 尝试重新安装应用

4. **构建APK失败**
   - 确认 Android Studio / Gradle 环境正确
   - 参考 [构建配置](android_native/README.md)（如有）或查看 Gradle 日志

## 🤝 贡献指南

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/xxx`)
3. 提交更改 (`git commit -m 'Add some xxx'`)
4. 推送到分支 (`git push origin feature/xxx`)
5. 打开 Pull Request

## 📄 许可证

本项目采用 GPLv3 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。
原项目版权归 [TangStudy](https://github.com/TangIsLearning/TodoList) 所有，本项目在 GPLv3 协议下对其进行了二次开发。

## 📞 联系方式

如有问题或建议，请通过以下方式联系：
- 提交 [Issue](https://github.com/colorfulLCAT3/TodoList-urlscheme/issues)
- 邮件联系：colorfulLCAThsfx@gmail.com
- 作者：colorfulLCAT
