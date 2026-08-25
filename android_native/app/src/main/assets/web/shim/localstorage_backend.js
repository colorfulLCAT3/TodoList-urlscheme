/**
 * localStorage 后端 shim：模拟 pywebview.js_api，让现有前端在原生 WebView 里运行。
 *
 * 原理：定义 window.pywebview.api，前端 apiCall 直接调用。
 * 数据全部存 localStorage（任务/分类/标签/配置），无需 Python/SQLite。
 */

(function () {
    'use strict';

    // ---------- localStorage 数据键 ----------
    var KEY_TASKS = 'todolist_tasks';
    var KEY_CATEGORIES = 'todolist_categories';
    var KEY_SETTINGS = 'todolist_settings';

    // ---------- 工具 ----------
    function uid() {
        return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function (c) {
            var r = Math.random() * 16 | 0;
            var v = c === 'x' ? r : (r & 0x3 | 0x8);
            return v.toString(16);
        });
    }
    function nowISO() {
        return new Date().toISOString();
    }
    function load(key, fallback) {
        try {
            var raw = localStorage.getItem(key);
            if (raw) return JSON.parse(raw);
        } catch (e) { /* ignore */ }
        return fallback;
    }
    function save(key, data) {
        localStorage.setItem(key, JSON.stringify(data));
    }
    function ok(data) {
        return { success: true, data: data };
    }
    function fail(msg) {
        return { success: false, error: msg };
    }

    // ---------- 任务 CRUD ----------
    function getTasks() { return load(KEY_TASKS, []); }
    function setTasks(tasks) { save(KEY_TASKS, tasks); }

    function getCategories() { return load(KEY_CATEGORIES, []); }
    function setCategories(cats) { save(KEY_CATEGORIES, cats); }

    function getSettings() { return load(KEY_SETTINGS, {}); }
    function setSettings(s) { save(KEY_SETTINGS, s); }

    function findTask(id) {
        return getTasks().find(function (t) { return t.id === id; }) || null;
    }

    // 给任务附加 tags（从存储的 tag 名解析）
    function decorateTask(t) {
        var tags = t.tags || [];
        var resolved = tags.map(function (tagName) {
            if (typeof tagName === 'object') return tagName;
            return { id: uid(), name: tagName, color: '#6c757d', createdAt: nowISO() };
        });
        var out = Object.assign({}, t);
        out.tags = resolved;
        return out;
    }

    // ---------- 配置 ----------
    function getConfig(key) {
        var settings = getSettings();
        var value = settings[key];
        // 兼容前端 localStorage 直读键（如 todolist_theme）
        try {
            var direct = localStorage.getItem('todolist_' + key);
            if (direct !== null && value === undefined) value = direct;
        } catch (e) { /* ignore */ }
        return value;
    }

    // ---------- API 实现 ----------
    var api = {
        // 任务
        get_todos: function (page, pageSize, categoryId, status, priority, dueDate, year, month, search, customDate) {
            var tasks = getTasks();
            var filtered = tasks;

            if (categoryId && categoryId !== 'all' && categoryId !== 'uncategorized') {
                filtered = filtered.filter(function (t) { return t.categoryId === categoryId; });
            } else if (categoryId === 'uncategorized') {
                filtered = filtered.filter(function (t) { return !t.categoryId; });
            }
            if (status) {
                if (status === 'completed') filtered = filtered.filter(function (t) { return t.completed; });
                else if (status === 'uncompleted') filtered = filtered.filter(function (t) { return !t.completed; });
            }
            if (priority && priority !== 'all') {
                filtered = filtered.filter(function (t) { return t.priority === priority; });
            }
            if (search) {
                var kw = String(search).toLowerCase();
                filtered = filtered.filter(function (t) {
                    return (t.title || '').toLowerCase().indexOf(kw) !== -1 ||
                        (t.description || '').toLowerCase().indexOf(kw) !== -1;
                });
            }
            if (year) {
                filtered = filtered.filter(function (t) {
                    return t.dueDate && new Date(t.dueDate).getFullYear() === Number(year);
                });
            }

            // 排序：未完成优先，dueDate 升序，优先级
            var prioOrder = { high: 1, medium: 2, low: 3, none: 4 };
            filtered = filtered.slice().sort(function (a, b) {
                if (a.completed !== b.completed) return a.completed ? 1 : -1;
                if (a.dueDate && b.dueDate) return new Date(a.dueDate) - new Date(b.dueDate);
                if (a.dueDate) return -1;
                if (b.dueDate) return 1;
                return (prioOrder[a.priority] || 4) - (prioOrder[b.priority] || 4);
            });

            var total = filtered.length;
            var pageSizeN = pageSize || total;
            var start = (page - 1 || 0) * pageSizeN;
            var pageTasks = filtered.slice(start, start + pageSizeN).map(decorateTask);

            return ok({
                tasks: pageTasks,
                total: total,
                page: page || 1,
                page_size: pageSizeN,
                total_pages: pageSizeN > 0 ? Math.ceil(total / pageSizeN) : 0
            });
        },

        get_todo: function (id) {
            var t = findTask(id);
            return t ? ok(decorateTask(t)) : fail('任务不存在');
        },

        add_todo: function (taskData) {
            var task = Object.assign({
                id: uid(),
                title: taskData.title || '',
                description: taskData.description || '',
                completed: !!taskData.completed,
                priority: taskData.priority || 'none',
                categoryId: taskData.categoryId || null,
                dueDate: taskData.dueDate || null,
                tags: taskData.tags || [],
                isRecurring: !!taskData.isRecurring,
                parentTaskId: taskData.parentTaskId || null,
                createdAt: nowISO(),
                updatedAt: nowISO()
            }, taskData);
            task.id = task.id || uid();
            var tasks = getTasks();
            tasks.push(task);
            setTasks(tasks);
            return ok(decorateTask(task));
        },

        update_todo: function (id, taskData) {
            var tasks = getTasks();
            var idx = tasks.findIndex(function (t) { return t.id === id; });
            if (idx === -1) return fail('任务不存在');
            var updated = Object.assign({}, tasks[idx], taskData, { updatedAt: nowISO() });
            if (taskData.completed !== undefined) updated.completed = !!taskData.completed;
            if (taskData.priority !== undefined) updated.priority = taskData.priority || 'none';
            if (taskData.categoryId !== undefined) updated.categoryId = taskData.categoryId || null;
            tasks[idx] = updated;
            setTasks(tasks);
            return ok(decorateTask(updated));
        },

        delete_todo: function (id, deleteAll) {
            var tasks = getTasks();
            if (deleteAll) {
                // 删除周期性任务的整个系列（简化：删除同 title 的）
                var t = tasks.find(function (x) { return x.id === id; });
                if (t) {
                    tasks = tasks.filter(function (x) { return x.title !== t.title; });
                } else {
                    tasks = tasks.filter(function (x) { return x.id !== id; });
                }
            } else {
                tasks = tasks.filter(function (x) { return x.id !== id; });
            }
            setTasks(tasks);
            return ok(true);
        },

        toggle_todo: function (id) {
            var tasks = getTasks();
            var idx = tasks.findIndex(function (t) { return t.id === id; });
            if (idx === -1) return fail('任务不存在');
            tasks[idx].completed = !tasks[idx].completed;
            tasks[idx].updatedAt = nowISO();
            setTasks(tasks);
            return ok({ completed: tasks[idx].completed, updatedAt: tasks[idx].updatedAt });
        },

        update_todo_due_date: function (id, dueDate) {
            var tasks = getTasks();
            var idx = tasks.findIndex(function (t) { return t.id === id; });
            if (idx === -1) return fail('任务不存在');
            tasks[idx].dueDate = dueDate || null;
            tasks[idx].updatedAt = nowISO();
            setTasks(tasks);
            return ok(decorateTask(tasks[idx]));
        },

        // 周期性任务（简化：等同普通任务）
        add_recurring_todo: function (taskData) {
            return api.add_todo(taskData);
        },

        search_subtasks_by_parent_name: function (parentName, page, pageSize, categoryId, status, priority, dueDate) {
            var tasks = getTasks();
            var kw = String(parentName || '').toLowerCase();
            // 有父任务（parentTaskId 非空）且标题匹配的，作为子任务结果
            var filtered = tasks.filter(function (t) {
                if (!t.parentTaskId) return false;
                if (kw && t.title.toLowerCase().indexOf(kw) === -1) return false;
                if (categoryId && categoryId !== 'all' && t.categoryId !== categoryId) return false;
                if (status === 'completed' && !t.completed) return false;
                if (status === 'uncompleted' && t.completed) return false;
                return true;
            });
            var total = filtered.length;
            var pageSizeN = pageSize || total;
            var start = (page - 1 || 0) * pageSizeN;
            return ok({
                tasks: filtered.slice(start, start + pageSizeN).map(decorateTask),
                total: total,
                page: page || 1,
                page_size: pageSizeN,
                total_pages: pageSizeN > 0 ? Math.ceil(total / pageSizeN) : 0
            });
        },

        // 分类
        get_categories: function () {
            return ok(getCategories());
        },

        add_category: function (catData) {
            var cat = {
                id: uid(),
                name: catData.name || '',
                color: catData.color || '#007bff',
                createdAt: nowISO()
            };
            var cats = getCategories();
            cats.push(cat);
            setCategories(cats);
            return ok(cat);
        },

        update_category: function (id, catData) {
            var cats = getCategories();
            var idx = cats.findIndex(function (c) { return c.id === id; });
            if (idx === -1) return fail('分类不存在');
            cats[idx] = Object.assign({}, cats[idx], catData, { id: id });
            setCategories(cats);
            return ok(cats[idx]);
        },

        delete_category: function (id) {
            setCategories(getCategories().filter(function (c) { return c.id !== id; }));
            // 级联清空任务的分类
            var tasks = getTasks();
            tasks.forEach(function (t) {
                if (t.categoryId === id) { t.categoryId = null; t.updatedAt = nowISO(); }
            });
            setTasks(tasks);
            return ok(true);
        },

        // 标签（从任务聚合）
        get_all_tags: function () {
            var tagMap = {};
            getTasks().forEach(function (t) {
                (t.tags || []).forEach(function (tagName) {
                    var name = typeof tagName === 'object' ? tagName.name : tagName;
                    if (!name) return;
                    if (!tagMap[name]) tagMap[name] = { id: uid(), name: name, color: '#6c757d', createdAt: nowISO(), taskCount: 0 };
                    tagMap[name].taskCount++;
                });
            });
            return ok(Object.values(tagMap));
        },

        delete_tag: function (id) {
            // 简化：删除该 tag 名在任务中的引用
            var tasks = getTasks();
            tasks.forEach(function (t) {
                t.tags = (t.tags || []).filter(function (tag) {
                    var name = typeof tag === 'object' ? tag.id : null;
                    return name !== id;
                });
            });
            setTasks(tasks);
            return ok(true);
        },

        // 统计
        get_stats: function () {
            var tasks = getTasks();
            var completed = tasks.filter(function (t) { return t.completed; });
            var today = new Date().toISOString().slice(0, 10);
            var todayCompleted = completed.filter(function (t) {
                return t.updatedAt && t.updatedAt.slice(0, 10) === today;
            });
            var overdue = tasks.filter(function (t) {
                return !t.completed && t.dueDate && new Date(t.dueDate) < new Date();
            });
            return ok({
                uncompleted: tasks.length - completed.length,
                today_completed: todayCompleted.length,
                over_due: overdue.length,
                completion_rate: tasks.length > 0 ? Math.round(completed.length / tasks.length * 1000) / 10 : 0
            });
        },

        // 配置
        get_config: function (key) {
            return ok({ [key]: getConfig(key) });
        },

        set_config: function (key, value) {
            var settings = getSettings();
            settings[key] = value;
            setSettings(settings);
            try { localStorage.setItem('todolist_' + key, String(value)); } catch (e) { /* ignore */ }
            return ok(true);
        },

        // 任务关联（简化：基于 parentTaskId）
        add_task_relation: function (taskId, parentTaskId) {
            var tasks = getTasks();
            var idx = tasks.findIndex(function (t) { return t.id === taskId; });
            if (idx !== -1) { tasks[idx].parentTaskId = parentTaskId; tasks[idx].updatedAt = nowISO(); }
            setTasks(tasks);
            return ok(true);
        },

        remove_task_relation: function (taskId) {
            var tasks = getTasks();
            var idx = tasks.findIndex(function (t) { return t.id === taskId; });
            if (idx !== -1) { tasks[idx].parentTaskId = null; tasks[idx].updatedAt = nowISO(); }
            setTasks(tasks);
            return ok(true);
        },

        get_children: function (taskId) {
            return ok(getTasks().filter(function (t) { return t.parentTaskId === taskId; }).map(decorateTask));
        },

        get_parent: function (taskId) {
            var t = findTask(taskId);
            if (t && t.parentTaskId) {
                var p = findTask(t.parentTaskId);
                if (p) return ok(decorateTask(p));
            }
            return ok(null);
        },

        search_tasks_with_subtasks: function (keyword, limit) {
            var kw = String(keyword || '').toLowerCase();
            var result = getTasks().filter(function (t) {
                return t.parentTaskId && t.title.toLowerCase().indexOf(kw) !== -1;
            });
            return ok(result.slice(0, limit || 5).map(function (t) {
                var childCount = getTasks().filter(function (x) { return x.parentTaskId === t.id; }).length;
                return { id: t.id, title: t.title, priority: t.priority, dueDate: t.dueDate, completed: t.completed, subtaskCount: childCount };
            }));
        },

        // ---------- no-op 桩（前端有兜底，成功响应即可） ----------
        export_tasks_excel: function () { return ok({ message: '导出功能在 Android 端暂不支持' }); },
        open_in_browser: function () { return ok(true); },
        select_file_dialog: function () { return ok(''); },
        get_data_file_config: function () { return ok('localStorage'); },
        set_data_file_config: function () { return ok(true); },
        validate_data_file: function () { return ok(true); },
        get_webdav_config: function () { return ok({ enabled: false, sync_type: '', url: '', username: '', password: '', remote_path: '', first_sync_mode: 'remote_overwrite' }); },
        set_webdav_config: function () { return ok(true); },
        test_webdav_connection: function () { return ok(true); },
        sync_to_cloud: function () { return ok(true); },
        sync_from_cloud: function () { return ok(true); },
        trigger_upload_on_change: function () { return ok(true); },
        check_calendar_permission: function () { return ok(true); },
        add_task_reminder_to_calendar: function () { return ok(true); },
        sync_reminder_to_calendar: function () { return ok(true); },
        log: function () { return ok(true); }
    };

    // 兼容 addNewTask/update 内部用的旧名
    api.addTodo = api.add_todo;
    api.updateTodo = api.update_todo;
    api.deleteTodo = api.delete_todo;
    api.toggleTodo = api.toggle_todo;
    api.getTodos = api.get_todos;
    api.getCategories = api.get_categories;
    api.addCategory = api.add_category;
    api.updateCategory = api.update_category;
    api.deleteCategory = api.delete_category;
    api.getTags = api.get_all_tags;

    // ---------- URL scheme 推送桥 ----------
    window.__pushFromUrl = function (url) {
        try {
            var parsed = new URL(url);
            if (parsed.protocol !== 'todolist:') return;
            var dataParam = decodeURIComponent(parsed.searchParams.get('data') || '');
            var payload = JSON.parse(dataParam);
            var list = Array.isArray(payload) ? payload : (payload.tasks || [payload]);

            var added = 0;
            list.forEach(function (raw) {
                if (!raw || !raw.title) return;
                api.add_todo(raw);
                added++;
            });

            // 通知前端刷新
            if (typeof window.todoManager !== 'undefined' && window.todoManager.loadTasks) {
                window.todoManager.loadTasks();
            }
            if (typeof window.categoryManager !== 'undefined' && window.categoryManager.loadCategories) {
                window.categoryManager.loadCategories();
            }
            if (typeof window.Utils !== 'undefined' && window.Utils.showToast) {
                window.Utils.showToast('已通过链接添加 ' + added + ' 个待办', 'success');
            }
        } catch (e) {
            console.error('URL scheme 解析失败:', e);
        }
    };

    // ---------- 暴露 ----------
    window.pywebview = window.pywebview || {};
    window.pywebview.api = api;
    window.__pywebview_ready = true;
})();
