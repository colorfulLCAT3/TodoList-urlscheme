/**
 * 多语言配置文件
 * 支持中文和英文
 */

const Languages = {
    // 中文（默认）
    zh: {
        // 应用标题和基本界面
        appTitle: "📝 Todo List",
        settingsBtn: "设置中心",
        settings: "设置",
        save: "保存",
        cancel: "取消",
        confirm: "确认",
        delete: "删除",
        edit: "编辑",
        view: "查看",
        close: "关闭",
        loading: "加载中...",
        retry: "发生未知异常，请稍后重试！",
        itemRequired: "请填写必填项！",
        
        // 任务相关
        task: "任务",
        tasks: "任务",
        newTask: "新建任务",
        editTask: "编辑任务",
        taskTitle: "任务标题",
        taskDescription: "任务描述",
        taskPriority: "优先级",
        taskCategory: "分类",
        taskDueDate: "开始日期",
        taskDueTime: "开始时间",
        taskCreateTime: "创建时间",
        taskUpdateTime: "更新时间",
        taskTags: "标签",
        taskTag: "标签",
        taskStatus: "状态",

        // 任务详情
        noTaskTags: "无标签",
        noTaskDescription: "无描述",

        // 优先级
        priorityHigh: "高优先级",
        priorityMedium: "中优先级", 
        priorityLow: "低优先级",
        priorityNone: "无优先级",
        // 优先级-图标
        high: "高",
        medium: "中",
        low: "低",
        none: "无",
        
        // 状态
        statusCompleted: "已完成",
        statusUncompleted: "未完成",
        statusPending: "未完成未逾期",
        statusOverdue: "未完成已过期",
        
        // 统计信息
        statsTotalTasks: "总任务",
        statsCompletedTasks: "已完成",
        statsUnCompletedTasks: "未完成",
        statsCompletionRate: "完成率",
        statsNoDueDateTasks: "无开始日期",
        statsLastUpdateTime: "最后更新",
        statsTodayCompletedTasks: "今日已完成",
        statsOverDueDateTasks: "已过期",
        statsCategories: "分类数",
        
        // 分类管理
        categories: "分类",
        allCategories: "📋 全部",
        addCategory: "添加分类",
        categoryName: "分类名称",
        categoryColor: "颜色",
        uncategorized: "未分类",
        showMoreCategories: "展示更多",

        // 搜索和筛选
        searchTitle: "支持通过【#标签(空格)】或【>父任务全称】进行特性搜索",
        searchClear: "清空搜索",
        filterAll: "所有",
        filterPriority: "所有优先级",
        filterStatus: "所有状态",
        filterDueDate: "开始日期",
        
        // 日期筛选选项
        dueDateAll: "所有时间",
        dueDateToday: "今天",
        dueDateTomorrow: "明天", 
        dueDateWeek: "本周内",
        dueDateMonth: "本月内",
        dueDateNoDueDate: "无开始日期",
        
        // 视图切换
        listView: "列表视图",
        calendarView: "日历视图",
        timelineView: "时间轴视图",

        // 日历相关
        calendarMonth: "月",
        calendarWeekdays: ["日", "一", "二", "三", "四", "五", "六"],

        // 任务表头
        taskHeaderName: "任务名称",
        taskHeaderPriority: "优先级",
        taskHeaderDueDate: "到期时间",
        taskHeaderTag: "标签",
        taskHeaderAction: "操作",
        
        // 任务列表操作项提示语
        recurringTaskEditTip: "周期性任务不支持编辑",
        normalTaskEditTip: "编辑",
        taskViewTip: "查看",
        taskDeleteTip: "删除",

        // 分页
        paginationShowing: "显示",
        paginationOf: "共",
        paginationItems: "条",
        paginationPage: "页",
        paginationFirst: "首页",
        paginationPrev: "上一页", 
        paginationNext: "下一页",
        paginationLast: "末页",
        
        // 空状态
        emptyTasks: "暂无任务",
        emptyTasksMessage: "点击\"新建任务\"按钮创建你的第一个任务",
        
        // 操作提示
        taskCreated: "任务创建成功",
        taskUpdated: "任务更新成功", 
        taskDeleted: "任务删除成功",
        taskCompleted: "任务已完成",
        taskReopened: "任务已重新开启",
        darkModeSwitched: "已切换到深色主题",
        LightModeSwitched: "已切换到浅色主题",
        loadingTaskFailed: "加载任务失败",
        periodicTaskEditFailed: "周期性任务不支持编辑，请删除后重新创建",
        periodicTaskDeleted: "整个周期任务删除成功",
        operationFailed: "操作失败",
        taskTagDeleted: "标签删除成功",
        errorTagNameRequired: "请输入标签名",
        errorTagExisted: "标签已存在",
        windowOnTopSet: "窗口已设置置顶",
        windowOnTopUnset: "窗口已取消置顶",
        languageSwitchFailed: "语言切换失败",
        languageSwitchTo: "已切换到",
        initializationFailed: "应用初始化失败",
        unknownErrorOccurred: "发生了未知错误",
        refreshDataFailed: "刷新数据失败",
        refreshDataSuccess: "刷新数据成功",
        resetStateFailed: "应用状态重置失败",
        resetStateSuccess: "应用状态已重置",
        loadCategoriesFailed: "加载分类失败",
        errorCategoryNameRequired: "请输入分类名称",
        errorCategoryExisted: "分类名称已存在",
        categoryCreated: "分类创建成功",
        categoryUpdated: "分类更新成功",
        categoryDeleted: "分类删除成功",
        showTaskFor: "当前任务日期：",

        // 错误消息
        errorTitleRequired: "请输入任务标题",
        errorInvalidDateTime: "开始时间不能早于当前时间",
        errorDateTimeIncomplete: "日期和时间选择不完整",
        errorRecurrenceTypeRequired: "请选择重复周期",
        errorRecurrenceCountRequired: "请输入有效的循环次数",

        // 周期性任务
        recurringTask: "周期性任务",
        createRecurringTask: "创建为周期性任务",
        recurrenceType: "重复周期",
        recurrenceCount: "循环次数*",
        recurrenceDaily: "每天",
        recurrenceWeekly: "按周",
        recurrenceMonthly: "按月",
        recurrenceYearly: "按年",
        recurrenceCountRequired: "循环次数不能为空",
        recurrenceChoose: "请选择",
        recurringEditNotice: "非周期性任务编辑模式下不支持改周期性任务",

        // 设置中心
        settingsWindow: "通用设置",
        settingsWindowTop: "窗口置顶",
        settingsDarkTheme: "深色模式",
        settingsAutoStart: "开机启动",
        settingsApply: "应用",
        settingsData: "数据管理",
        settingsDataSync: "同步数据",
        settingsSuccess: "设置成功",
        settingsSaveSuccess: "保存成功",
        settingsFailed: "设置失败",
        settingsAutoStartEnabled: "开机启动已启用",
        settingsAutoStartDisabled: "开机启动已禁用",
        settingsRemind: "提前提醒",
        settingsRemindOffsets: "提醒时间点(分钟)",
        settingsRemindEnabled: "提前提醒已启用",
        settingsRemindDisabled: "提前提醒已禁用",
        settingsRemindApplied: "提醒设置已保存",
        settingsRemindNeedRestart: "请重启应用后生效",
        settingsRemindInvalid: "请输入有效的分钟数，逗号分隔",
        settingsAutoStartWarning: "当前平台不支持开机启动功能",
        settingsConnectSuccess: "连接成功！可以正常使用云端同步功能！",
        settingsConnectionFailed: "连接失败",
        settingsStorageWarning: "注意：这将影响所有数据的读写操作，当前数据会被移动到新文件。建议先备份重要数据。是否继续？",
        settingsSyncModeLocalWarning: "注意：当前操作将直接触发一次本地数据强制覆盖远程文件数据。建议先备份重要数据。是否继续？",
        settingsSyncModeRemoteWarning: "注意：当前操作将直接触发一次远程数据强制覆盖本地文件数据。建议先备份重要数据。是否继续？",
        settingsSyncCloseWarning: "注意：当前操作将导致无法同步云端数据，是否继续？",

        // 语言设置
        language: "语言切换",

        // 关于
        about: "关于",
        sourceCode: "源码地址",
        document: "相关文档",
        documentText: "TodoList功能介绍",
        statement: "开源声明",
        statementText: "仅供使用，勿商用",

        // 数据存储路径
        dataStoragePath: "存储路径",

        // 确认对话框
        confirmDeleteTask: "确定要删除任务",
        confirmDeleteTaskMessage: "此操作无法撤销。",
        
        // 周期性任务删除选项
        deleteSingleTask: "仅删除此任务",
        deleteSingleTaskDesc: "删除当前选中的任务，保留周期中的其他任务",
        deleteAllTasks: "删除整个周期", 
        deleteAllTasksDesc: "删除此周期内的所有任务",
        
        // 更多选项
        moreOptions: "更多选项",
        optional: "可选",
        required: "必填",
        
        // 数据同步
        dataSync: "数据云同步",
        syncType: "同步类型",
        url: "地址*",
        account: "账号*",
        password: "密码*",
        filepath: "路径*",
        firstSyncMode: "首次同步",
        firstSyncModeRemote: "远程覆盖本地",
        firstSyncModeLocal: "本地覆盖远程",
        testConnection: "测试连接",
        saveConfiguration: "保存配置",
        autoSyncNotice: "⚠️ 如云路径和本地数据存储路径存在映射关系，请勿开启云同步，避免重复更新数据；首次同步外的数据自动同步规则：存在数据更新的端点，15s内会自动同步数据到其他端点",
    },
    
    // 英文
    en: {
        // 应用标题和基本界面
        appTitle: "📝 Todo List",
        settingsBtn: "Settings",
        settings: "Settings",
        save: "Save",
        cancel: "Cancel",
        confirm: "Confirm",
        delete: "Delete",
        edit: "Edit",
        view: "View",
        close: "Close",
        loading: "Loading...",
        retry: "An unknown exception occurred. Please try again later.",
        itemRequired: "Please fill in the required fields.",
        
        // 任务相关
        task: "Task",
        tasks: "Tasks",
        newTask: "New Task",
        editTask: "Edit Task",
        taskTitle: "Task Title",
        taskDescription: "Task Description",
        taskPriority: "Priority",
        taskCategory: "Category",
        taskDueDate: "Start Date",
        taskDueTime: "Start Time",
        taskCreateTime: "Create Time",
        taskUpdateTime: "Update Time",
        taskTags: "Tags",
        taskTag: "Tag",
        taskStatus: "Status",

        // 任务详情
        noTaskTags: "(none)",
        noTaskDescription: "(none)",

        // 优先级
        priorityHigh: "High Priority",
        priorityMedium: "Medium Priority",
        priorityLow: "Low Priority", 
        priorityNone: "No Priority",
        // 优先级-图标
        high: "High",
        medium: "Medium",
        low: "Low",
        none: "None",
        
        // 状态
        statusCompleted: "Completed",
        statusUncompleted: "Uncompleted",
        statusPending: "Pending (Not Overdue)",
        statusOverdue: "Expired",
        
        // 统计信息
        statsTotalTasks: "Total Tasks",
        statsCompletedTasks: "Completed",
        statsUnCompletedTasks: "Uncompleted",
        statsCompletionRate: "Completion Rate",
        statsNoDueDateTasks: "No Start Date",
        statsLastUpdateTime: "Last Updated Time",
        statsTodayCompletedTasks: "Today Completed",
        statsOverDueDateTasks: "Expired",
        statsCategories: "Total Categories",
        
        // 分类管理
        categories: "Categories",
        allCategories: "📋 All",
        addCategory: "Add Category",
        categoryName: "Category Name",
        categoryColor: "Color",
        uncategorized: "Uncategorized",
        showMoreCategories: "More",

        // 搜索和筛选
        searchTitle: "Supports #tag(space) / <Parent-Task search",
        searchClear: "Clear Search",
        filterAll: "All",
        filterPriority: "All Priority",
        filterStatus: "All Status",
        filterDueDate: "Start Date",
        
        // 日期筛选选项
        dueDateAll: "All Time",
        dueDateToday: "Today",
        dueDateTomorrow: "Tomorrow",
        dueDateWeek: "This Week",
        dueDateMonth: "This Month",
        dueDateNoDueDate: "No Start Date",
        
        // 视图切换
        listView: "List View",
        calendarView: "Calendar View",
        timelineView: "Timeline View",
        
        // 日历相关
        calendarMonth: "Month",
        calendarWeekdays: ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"],

        // 任务表头
        taskHeaderName: "Task Name",
        taskHeaderPriority: "Priority",
        taskHeaderDueDate: "Due Date",
        taskHeaderTag: "Tag",
        taskHeaderAction: "Action",
        
        // 任务列表操作项提示语
        recurringTaskEditTip: "Periodic tasks cannot be edited",
        normalTaskEditTip: "Edit",
        taskViewTip: "View",
        taskDeleteTip: "Delete",

        // 分页
        paginationShowing: "Showing",
        paginationOf: "of",
        paginationItems: "items",
        paginationPage: "page",
        paginationFirst: "First",
        paginationPrev: "Previous",
        paginationNext: "Next",
        paginationLast: "Last",
        
        // 空状态
        emptyTasks: "No Tasks",
        emptyTasksMessage: "Click the \"New Task\" button to create your first task",
        
        // 操作提示
        taskCreated: "Task created successfully",
        taskUpdated: "Task updated successfully",
        taskDeleted: "Task deleted successfully",
        taskCompleted: "Task completed",
        taskReopened: "Task reopened",
        darkModeSwitched: "Switched to Dark mode",
        LightModeSwitched: "Switched to Light mode",
        loadingTaskFailed: "Failed to load tasks",
        periodicTaskEditFailed: "Periodic tasks cannot be edited, please delete and recreate them",
        periodicTaskDeleted: "The periodic task has been deleted successfully",
        operationFailed: "Operation failed",
        taskTagDeleted: "The tag has been deleted successfully",
        errorTagNameRequired: "Please enter a tag name",
        errorTagExisted: "The tag already exists",
        windowOnTopSet: "The window has been set to stay on top",
        windowOnTopUnset: "The window has been unset from staying on top",
        languageSwitchFailed: "Language switch failed",
        languageSwitchTo: "Switched to ",
        initializationFailed: "Application initialization failed",
        unknownErrorOccurred: "An unknown error occurred",
        refreshDataFailed: "Failed to refresh data",
        refreshDataSuccess: "Refresh data successfully",
        resetStateFailed: "Failed to reset application state",
        resetStateSuccess: "Application state has been reset",
        loadCategoriesFailed: "Failed to load categories",
        errorCategoryNameRequired: "Please enter a category name",
        errorCategoryExisted: "Category name already exists",
        categoryCreated: "Category created successfully",
        categoryUpdated: "Category updated successfully",
        categoryDeleted: "Category deleted successfully",
        showTaskFor: "Show tasks for ",

        // 错误消息
        errorTitleRequired: "Please enter task title",
        errorInvalidDateTime: "Start time cannot be earlier than current time",
        errorDateTimeIncomplete: "Date and time must be selected together",
        errorRecurrenceTypeRequired: "Please select recurrence type",
        errorRecurrenceCountRequired: "Please enter valid repeat count",

        // 周期性任务
        recurringTask: "Recurring Task",
        createRecurringTask: "Create as recurring task",
        recurrenceType: "Recurrence",
        recurrenceCount: "Repeat Count",
        recurrenceDaily: "Daily",
        recurrenceWeekly: "Weekly",
        recurrenceMonthly: "Monthly",
        recurrenceYearly: "Yearly",
        recurrenceCountRequired: "Cycle times cannot be empty",
        recurrenceChoose: "Please Choose",
        recurringEditNotice: "Periodic tasks cannot be edited in non-periodic mode",

        // 设置中心
        settingsWindow: "General Settings",
        settingsWindowTop: "Window Always On Top",
        settingsDarkTheme: "Dark Mode",
        settingsAutoStart: "Auto-start On Boot",
        settingsApply: "Apply",
        settingsData: "Data Management",
        settingsDataSync: "Synchronize Data",
        settingsSuccess: "Setting successful",
        settingsSaveSuccess: "Save successful",
        settingsFailed: "Setting failed",
        settingsAutoStartEnabled: "Auto-start on boot is enabled.",
        settingsAutoStartDisabled: "Auto-start on boot is disabled.",
        settingsRemind: "Advance Reminder",
        settingsRemindOffsets: "Reminder Minutes (comma separated)",
        settingsRemindEnabled: "Advance reminder enabled",
        settingsRemindDisabled: "Advance reminder disabled",
        settingsRemindApplied: "Reminder settings saved",
        settingsRemindNeedRestart: "Restart the app to take effect",
        settingsRemindInvalid: "Enter valid minutes, comma separated",
        settingsAutoStartWarning: "The current platform does not support the auto-start on boot feature.",
        settingsConnectSuccess: "Connection successful! The cloud synchronization feature is now available for use.",
        settingsConnectionFailed: "Connection failed",
        settingsStorageWarning: "Note: This will affect all data read and write operations, and the current data will be moved to the new file. It is recommended to back up important data first. Continue?",
        settingsSyncModeLocalWarning: "Warning: The current operation will directly trigger a local data override of the remote file data. It is recommended to back up important data first. Continue anyway?",
        settingsSyncModeRemoteWarning: "Warning: The current operation will directly trigger a remote data override of the local file data. It is recommended to back up important data first. Continue anyway?",
        settingsSyncCloseWarning: "Warning: This operation will disable cloud data synchronization. Do you wish to proceed?",

        // 语言设置
        language: "Chinese/English Switch",

        // 关于
        about: "About",
        sourceCode: "SourceCode",
        document: "Document",
        documentText: "Usage Guide",
        statement: "Statement",
        statementText: "Personal use only, not for commercial use.",

        // 数据存储路径
        dataStoragePath: "Storage Path",

        // 确认对话框
        confirmDeleteTask: "Are you sure you want to delete task",
        confirmDeleteTaskMessage: "This action cannot be undone.",
        
        // 周期性任务删除选项
        deleteSingleTask: "Delete this task only",
        deleteSingleTaskDesc: "Delete the selected task, keep other tasks in the series",
        deleteAllTasks: "Delete entire series",
        deleteAllTasksDesc: "Delete all tasks in this recurring series",
        
        // 更多选项
        moreOptions: "More Options",
        optional: "Optional",
        required: "Required",

        // 数据同步
        dataSync: "Data Sync",
        syncType: "Data Sync Type",
        url: "Server Url*",
        account: "Account*",
        password: "Password*",
        filepath: "Filepath*",
        firstSyncMode: "First Sync Mode",
        firstSyncModeRemote: "Remote Overwrite Local",
        firstSyncModeLocal: "Local Overwrite Remote",
        testConnection: "Test Connection",
        saveConfiguration: "Save Configuration",
        autoSyncNotice: "⚠️ When there is a mapping relationship between the cloud path and the local data storage path, please do not enable cloud sync to avoid redundant data updates. For automatic sync rules after the initial sync: if there is a data update on any endpoint, the data will be automatically synced to other endpoints within 15 seconds.",
    }
};

// 导出到全局
if (typeof window !== 'undefined') {
    window.Languages = Languages;
    logger.info('Languages config loaded successfully');
}