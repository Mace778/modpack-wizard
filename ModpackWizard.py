#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Minecraft 整合包模组管理工具 · Modrinth（customtkinter 重构版）"""

import json, os, shutil, re, requests, threading, time, zipfile, tempfile, webbrowser, csv, hashlib
import xml.etree.ElementTree as ET
from datetime import datetime
from urllib.parse import quote
from concurrent.futures import ThreadPoolExecutor, as_completed
import customtkinter as ctk
from tkinter import filedialog, messagebox, simpledialog

# ---------- 常量 ----------
LOADER_KEYS = {"Fabric": "fabric-loader", "Forge": "forge", "NeoForge": "neoforge"}
LOADER_API = {"Fabric": "fabric", "Forge": "forge", "NeoForge": "neoforge"}
FONT = ('微软雅黑', 13)
FONT_BOLD = ('微软雅黑', 13, 'bold')
FONT_SM = ('微软雅黑', 12)
FONT_ITALIC = ('微软雅黑', 12, 'italic')
FONT_MD_BOLD = ('微软雅黑', 16, 'bold')
FONT_TITLE = ('微软雅黑', 20, 'bold')
FONT_LOG = ('Consolas', 12)

# ---------- Fluent Design 配色（Win11 风格）----------
# 亮色模式用标准高饱和 Fluent 色（白底上才显眼）
# 深色模式用降饱和降亮度变体（深底上低刺激）
C = {
    # 主强调蓝
    'accent':       ('#0078d4', '#2d7dd2'),
    'accent_hover': ('#106ebe', '#2a6cb0'),
    'accent_pressed': ('#005a9e', '#1e4f7a'),
    # 紫色强调
    'accent2':      ('#8b5cf6', '#7d5ba6'),
    'accent2_hover': ('#7c3aed', '#6b4a8f'),
    # 状态色（亮色饱和、深色降亮）
    'success':      ('#16a34a', '#3a8a3a'),
    'success_hover': ('#15803d', '#2f742f'),
    'warning':      ('#d97706', '#b08a2a'),
    'warning_hover': ('#b45309', '#8f6e1f'),
    'danger':       ('#dc2626', '#b8383d'),
    'danger_hover':  ('#b91c1c', '#97282c'),
    # 灰色按钮必须有足够对比度
    'gray':         ('#e0e0e0', '#2a2a2a'),
    'gray_hover':   ('#d0d0d0', '#3d3d3d'),
    'gray_pressed': ('#bcbcbc', '#505050'),
    # 列表专用
    'zebra':        ('#fafafa', '#1f1f1f'),
    'row_hover':    ('#e5efff', '#232c3a'),
    'selected':     ('#cce4f7', '#294058'),
    'header':       ('#e8e8e8', '#1a1a1a'),
    'border':       ('#d0d0d0', '#3a3a3a'),
    'mica':         ('#fafbfc', '#252525'),
    'mica_strong':  ('#f0f2f5', '#2d2d2d'),
    # 按钮文字颜色（自动随主题）
    'text_light':   ('#1a1a1a', '#e5e5e5'),  # 浅背景上用深字、深背景上用浅字
    'text_dark':    ('#ffffff', '#ffffff'),   # 彩色按钮一律白字
}

# ---------- 请求超时配置 ----------
REQUEST_TIMEOUT = 10  # 请求超时时间（秒）
STREAM_TIMEOUT = 60  # 流式下载超时时间（秒）
CF_WIDGET_TIMEOUT = 15  # CF widget 请求超时时间（秒）
MODRINTH_SHORT_TIMEOUT = 5  # Modrinth 短请求超时（秒）
MODRINTH_MEDIUM_TIMEOUT = 8  # Modrinth 中等请求超时（秒）
MODRINTH_LONG_TIMEOUT = 10  # Modrinth 长请求超时（秒）

# ---------- 配置管理 ----------
CONFIG_FILE = os.path.expanduser("~/.modpackwizard_config.json")

def load_config():
    default = {"language": "zh_CN", "theme": "dark", "show_log": True}
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return {**default, **json.load(f)}
    except Exception:
        return default

def save_config(cfg):
    try:
        merged = load_config()   # 合并旧配置，避免整体覆盖丢掉 show_log 等键
        merged.update(cfg)
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(merged, f, indent=2, ensure_ascii=False)
    except Exception:
        pass

# ---------- 国际化 ----------
LANG = {
'zh_CN':{
  'app_title': '⚡ 整合包模组管理工具', 'app_sub': '精简高效', 
  'file_label': '📁 文件',
  'path_label': '路径:', 
  'info_label': '📋 整合包信息',
  'info_name': '名称:', 'info_version': '版本:', 'info_mc': 'MC版本:',
  'info_loader': '加载器:', 'info_loader_ver': '加载器版本:', 'expand_btn': '▶ 展开',
  'collapse_btn': '▼ 折叠', 'compat_unknown': '⚠️ 未知', 'compat_unsupported': '⚠️ 未声明',
  'compat_compatible': '✅ 兼容', 'compat_incompatible': '❌ 不兼容', 'add_mod_label': '➕ 添加模组',
  'add_mod_placeholder': '项目链接或 ID', 'fetch_btn': '🔍 获取版本', 'modlist_label': '📦 模组列表',
  'search_project_placeholder': '输入项目名称关键词...', 'search_project_btn': '🔎 按名称搜索',
  'search_project_title': '🔎 搜索并添加项目', 'search_projecting': '正在搜索项目...',
  'search_project_no_result': '没有找到匹配的项目', 'search_project_fail': '搜索项目失败: {error}',
  'search_project_select': '选择此项目',
  'search_no_result': '未找到匹配的模组，请更换关键词', 'refresh_btn': '🔄 刷新', 'delete_btn': '🗑️ 删除',
  'folder_btn': '📂 打开文件夹', 'check_update_btn': '🧪 检查更新（实验性）',
  'backup_btn': '💾 备份', 'reload_btn': '🔄 重新加载', 'pack_btn': '📦 打包 .mrpack（含模组）',
  'export_btn': '📤 导出列表', 'import_btn': '📥 导入列表', 'log_label': '📋 日志',
  'settings_show_log': '显示日志面板',
  'status_ready': '就绪 ✅', 'status_loading': '加载中...', 'status_saved': '已保存 ✅',
  'status_backup': '已备份', 'status_packed': '打包完成',
  'status_checking': '检查更新中...', 'status_downloading': '下载中...', 'col_name': '项目名称',
  'col_filename': '文件名', 'col_version': '版本', 'col_path': '路径',
  'col_project_id': '项目 ID', 'dialog_confirm_delete': '确定删除选中的 {count} 个模组吗？', 'dialog_select_mod': '请至少选择一个模组',
  'dialog_no_mods': '没有匹配的模组', 'dialog_file_not_found': '文件不存在', 'dialog_open_mrpack_fail': '该 .mrpack 文件不包含 modrinth.index.json',
  'dialog_parse_error': '文件解析失败: {error}', 'dialog_success_open': '已打开 {file}', 
  'dialog_version_fetch': '获取版本失败: {error}', 'dialog_no_version': '该项目没有版本', 'dialog_select_version': '请先选择一个版本',
  'dialog_version_exists': '模组 {filename} 已存在，是否仍然添加？', 'dialog_dep_prompt': '模组 {filename} 有以下依赖项：',
  'dialog_dep_existing': '（已存在）', 'dialog_dep_missing': '（缺失）', 'dialog_dep_confirm': '是否补齐缺失的依赖？',
  'dialog_update_experimental': '🧪 检查更新功能目前为实验性阶段，可能存在版本检测不准确或误报的情况。\n\n建议在操作前先使用“备份”功能保存当前整合包文件，以防数据丢失。\n\n是否继续执行？', 'dialog_no_update': '所有模组都是最新版本',
  'dialog_update_found': '发现 {count} 个模组有更新（实验性检测结果）', 'dialog_update_warning': '⚠️ 该功能为实验性，版本比较可能不准确，请以 Modrinth 页面为准。', 'dialog_update_apply': '确定更新 {count} 个模组吗？（实验性功能）',
  'dialog_update_success': '成功更新 {count} 个模组', 'dialog_update_select': '请至少选择一个模组来更新', 'dialog_pack_empty': '没有模组条目，仍然打包吗？',
  'dialog_pack_success': '已生成 .mrpack 文件（含模组）:\n{path}', 'dialog_pack_fail': '打包失败: {error}', 'dialog_backup_success': '备份已保存到 {path}',
  'dialog_import_select': '请选择 CSV 文件', 'dialog_import_success': '成功导入 {count} 个模组', 'dialog_import_fail': '导入失败: {error}',
  'dialog_export_success': '已导出列表到 {path}', 'dialog_local_jar_title': '添加本地 JAR', 'dialog_local_jar_prompt': '请选择一个 JAR 文件',
  'dialog_local_jar_id': '输入 Modrinth 项目 ID（可选）:', 'dialog_detail_title': '模组详情',
  'dialog_detail_no_id': '此模组无项目 ID，仅显示本地信息。', 'log_download_done': '已下载: {filename}',
  'log_download_fail': '下载失败: {filename} - {error}', 'log_export': '已导出模组列表到 {path}', 'log_import': '从 {path} 导入 {count} 个模组',
  'log_async_pack_changed': '整合包已切换，已丢弃尚未完成的操作',
  'log_refresh': '已加载 {count} 个模组', 'log_local_jar': '已添加本地模组 {filename}', 'log_detail_view': '查看模组详情: {name}',
  
  
  'button_open_selected': '打开选中项', 'button_open_all': '打开全部',
  'button_install_missing': '补齐缺失', 'button_close': '关闭', 'button_cancel': '取消',
  'button_select_this': '选择此版本', 'button_update_selected': '更新选中项', 'button_select_all': '☑ 全选/反选',
  'button_show_all': '🔄 显示全部', 'button_show_recommended': '🔄 显示推荐/兼容', 'column_mod_name': '模组名',
  'column_current_ver': '当前版本', 'column_latest_ver': '最新版本', 'column_action': '操作',
  'dialog_confirm_overrides': '是否包含 overrides？', 'dialog_overrides_prompt': '将自定义配置文件打包到 overrides 目录？', 
  'log_no_overrides': '未选择 overrides 文件夹，仅打包 index.json', 'dialog_pack_error': '无法读取 index 文件', 'log_dep_fetch': '正在获取依赖 {name} 的最新版本...',
  'log_ov_applied': '已应用 {n} 个覆盖文件（含 {c} 个客户端专用）', 'log_ov_server': '保留 {n} 个服务端专用覆盖文件（server-overrides，未合并到工作区）',
  'log_dep_added': '已添加依赖 {name}', 'log_dep_exists': '依赖 {name} 已存在，跳过', 'dialog_dep_fetch_fail': '获取依赖 {name} 的版本失败',
  'dialog_dep_add_success': '成功添加 {count} 个依赖', 'dialog_dep_no_missing': '所有依赖均已存在，无需添加。', 'log_add_mod': '已添加模组 {filename}',
  'log_delete_mod': '已删除 {count} 个模组', 'log_pack': '已打包: {path}', 'log_update_start': '开始检查更新（实验性）...',
  'log_update_done': '所有模组均为最新版本', 'log_update_success': '成功更新 {count} 个模组', 'log_theme_switch': '主题切换为 {theme}',
  'log_lang_switch': '语言切换为 {lang}', 'dialog_open_cf_fail': '该 .zip 不是有效的 CurseForge 整合包（manifest.json 无效）', 'log_cf_open': '检测到 CurseForge 整合包，共 {count} 个模组条目',
  'log_cf_resolving': '正在解析 CurseForge 模组 {done}/{total}...', 'log_cf_done': '✅ CurseForge 模组解析完成', 'log_cf_fail': '⚠ 无法解析 CurseForge 模组 projectID={pid}，使用占位文件名',
  'log_cf_nohash': '下载 {filename} 计算哈希失败（将不含校验值）: {error}', 'export_zip_btn': '📦 导出 .zip', 'dialog_pack_success_zip': '已生成 .zip 文件:\n{path}',
  'diff_btn': '🔀 对比整合包', 'dialog_diff_pick_a': '选择第一个整合包（旧版本）', 'dialog_diff_pick_b': '选择第二个整合包（新版本）',
  'diff_title': '整合包对比结果', 'diff_only': '— 仅在 {name} 中（{count}）—', 'diff_changed': '— 版本不同（{count}）—',
  'diff_same': '两个整合包内容一致', 'log_jar_identified': '识别本地 JAR: {filename} → {project} {version}', 'log_jar_unknown': '无法从 Modrinth 识别 {filename}，按本地 JAR 处理',
  'dialog_changelog_title': '更新日志', 'dialog_changelog_none': '（无更新日志）', 
  'btn_detect_dup': '🔁 重复', 'btn_compat_check': '✅ 兼容', 'btn_stats': '📊 统计',
  'btn_backup_mgr': '💾 备份', 'btn_pre_pack': '📋 校验',
  'btn_dl_all': '⬇ 全部下载', 'btn_switch_ver': '🔄 切版本',
  'btn_easy_switch': '🔁 版本易切',
  'easy_switch_title': '版本易切 — 切换目标 MC/加载器',
  'easy_switch_target_mc': '目标 MC 版本', 'easy_switch_target_loader': '目标加载器',
  'easy_switch_search_btn': '🔍 检查兼容性', 'easy_switch_checking': '检查中... {i}/{count}',
  'easy_switch_stats': '✅ 兼容 {ok}  ❌ 不支持 {bad}  ⚠️ 无法检测 {unk}  📂 本地 {local}',
  'easy_switch_col_name': '项目名称', 'easy_switch_col_type': '类型',
  'easy_switch_col_status': '状态', 'easy_switch_col_target_ver': '目标版本',
  'easy_switch_status_ok': '✅ 兼容', 'easy_switch_status_bad': '❌ 不支持',
  'easy_switch_status_unknown': '⚠️ 未知', 'easy_switch_status_local': '📂 本地',
  'easy_switch_no_compatible': '没有可升级的模组', 'easy_switch_no_mods': '整合包中没有模组条目',
  'easy_switch_select_mc': '请选择目标 MC 版本', 'easy_switch_upgrade_btn': '⬆ 升级选中',
  'log_easy_switch_start': '版本易切开始（目标 MC={mc}，加载器={loader}）...',
  'log_easy_switch_done': '版本易切完成：兼容 {ok}，不支持 {bad}，无法检测 {unk}',
  'log_easy_switch_upgrade': '升级完成：成功 {ok}，失败 {fail}',
  'dlg_dup_title': '重复检测', 'dlg_dup_none': '未发现重复', 'dlg_dup_intro': '检测到 {count} 组重复：',
  'dlg_dup_delete_extra': '删除多余的（保留每组第一个）', 'dlg_compat_title': '兼容性体检', 'dlg_compat_ok': '所有模组兼容',
  'dlg_compat_issues': '发现 {count} 个不兼容模组：', 'dlg_compat_skip_cf': '已跳过 {count} 个 CurseForge 条目', 'dlg_stats_title': '统计面板',
  'dlg_stats_count': '模组总数', 'dlg_stats_size': '总体积', 'dlg_stats_source': '来源分布',
  'dlg_stats_no_url': '无下载链接条目', 'dlg_backups_title': '备份管理', 'dlg_backups_none': '暂无备份文件',
  'dlg_backups_restore': '恢复', 'dlg_backups_delete': '删除', 'dlg_backups_restore_confirm': '确定恢复此备份？当前 index 将被覆盖。',
  'dlg_backups_delete_confirm': '确定删除此备份？', 'dlg_switch_ver_title': '切换版本', 'dlg_switch_no_sel': '请先在列表中选中一个模组',
  'dlg_switch_no_pid': '该模组没有项目 ID，无法切换版本', 'dlg_pre_pack_title': '打包前校验',
  'dlg_pre_pack_ok': '所有条目检查通过', 'dlg_pre_pack_issues': '发现 {count} 个问题：', 'dlg_pre_pack_continue': '继续打包',
  'dlg_pre_pack_cancel': '取消',
  'dlg_dl_all_title': '下载所有模组', 'dlg_dl_all_done': '下载完成：成功 {ok}，失败 {fail}',
  'dialog_title_done': '操作完成', 'dialog_title_tip': '提示', 'dialog_title_error': '错误',
  'log_mc_fetching': '获取 Minecraft 版本列表...', 'log_mc_fetched': '✅ 获取 {count} 个 MC 版本', 'log_mc_fetch_fail': '获取 MC 版本失败',
  'log_loader_fetching': '正在获取 {loader} 版本...', 'log_loader_fetch_fail': '获取 {loader} 版本失败（网络异常？）',
  'log_mc_compat': 'MC {mc} 兼容 {count} 个 {loader} 版本', 'log_mc_compat_none': '未找到 MC {mc} 兼容版本，显示全部 {count} 个',
  'log_loader_fetched': '获取到 {count} 个 {loader} 版本', 'log_loader_compat_none': '未找到 MC {mc} 兼容的 {loader} 版本',
  'log_delete_nomatch': '未找到匹配的模组', 'dialog_open_index_first': '请先打开一个 index.json',
  'update_no_mods': '当前整合包没有模组', 'update_no_pid': '没有模组包含有效的 Modrinth 项目 ID',
  'log_update_no_pid': '没有可检查的模组（缺少项目 ID）', 'dep_none_added': '没有成功补齐任何依赖，请检查网络或手动添加。',
  'dep_select_first': '请先选择一个依赖', 'log_pack_start': '开始打包为 {path}...',
  'log_ov_dir_added': '已添加 {sub} 目录（{n} 个本地文件）', 'log_ov_files_added': '已添加覆盖文件 {n} 个: {path}',
  'dlg_overrides_dir': '选择 overrides 文件夹', 
  'stats_local': '本地', 'log_switched_to': '已切换版本 → {filename}', 'dialog_switched': '已切换到 {filename}',
  'log_entry_not_found': '未找到原条目: {path}', 'log_switch_fail': '切换版本失败: {error}',
  'log_index_saved': '整合包信息已保存', 'status_no_change': '无变化', 'status_packing': '打包中...',
  'log_meta_loading': '正在加载元数据...', 'log_list_refreshing': '正在刷新模组列表...',
  'log_add_exists': '{filename} 已存在，取消添加', 'log_delete_fail': '删除失败: {error}',
  'log_update_fail': '更新失败: {error}', 'log_cf_resolve_fail': '解析 CurseForge 条目失败: {error}',
  'log_cf_discarded': 'CF 解析完成，但已切换整合包，结果已丢弃', 'log_dl_all_start': '开始下载全部 {count} 个文件',
  'warn_need_url': '请输入项目链接或 ID', 'err_parse_pid': '无法解析项目 ID', 'log_no_link': '无下载链接: {filename}',
  'log_sha1_fail': 'SHA1 校验失败: {filename}', 'log_dl_fail': '下载 {filename} 失败: {error}',
  'dialog_open_pack_fail': '打开 .mrpack 失败:\n{error}', 'log_compare_fail': '对比失败:\n{error}',
  'log_import_write_fail': '导入写入失败: {error}', 'log_skip_nolink': '跳过 {filename}（无下载链接）',
  'log_downloading': '下载 {filename} ...', 'log_refresh_fail': '刷新列表失败: {error}', 'log_cf_check_fail': '[CF] 检查更新失败 {pid}: {error}',
  'log_read_fail': '读取失败: {error}', 'new_pack_default_name': '我的整合包', 'log_lang_rebuilt': '已用新语言重建界面',
  'dlg_open_mrpack': '选择 .mrpack 整合包', 'log_opening': '正在打开整合包: {path}', 'status_extracting': '正在解压... {c}/{t}',
  'log_loaded_info': "加载: 名称='{name}', MC='{mc}', 加载器='{loader}', 版本='{ver}'",
  'log_fetch_versions': '获取项目 {pid} 的版本...', 'selector_title': '选择版本 - {id}',
  'col_game_version': '游戏版本', 'col_loader': '加载器', 'col_date': '发布日期', 'col_recommended': '推荐',
  'selector_title_count': '{title}（{count} 个版本）', 'selector_filter': '当前筛选：Minecraft {mc}',
  'log_add_version_fail': '添加版本失败: {error}', 'log_rolled_back': '已移除下载失败的条目: {path}',
  'log_rollback_fail': '移除条目失败: {error}', 'log_dep_add_fail': '补齐依赖 {name} 失败: {error}',
  'dep_loading': '加载中... ({id})', 'log_csv_import_start': '开始从 {path} 导入...', 'csv_importing': '导入中... {i}/{count}',
  'log_no_compat_version': '无法找到兼容版本: {pid}', 'log_version_data_bad': '版本数据异常: {pid}',
  'ft_jar': '模组/资源包/光影包', 'detail_loading': '正在获取详情...',
  'detail_cf_info': '标题: {title}\n描述: {desc}\n下载量: {downloads}',
  'detail_mr_info': '标题: {title}\n作者: {author}\n描述: {desc}\n下载量: {downloads}\n最后更新: {updated}',
  'log_update_cancel': '用户取消检查更新', 'ver_unknown': '未知版本', 'update_selected': '已选 {n}/{total}', 'update_action': '⬆ 更新',
  'unknown': '未知',
  'log_read_index_fail': '读取 index 失败: {error}', 'unnamed': '未命名', 'log_entry_exists': '{path} 已存在',
  'dup_keep': '✅ 保留', 'dup_extra': '❌ 删除', 'log_dup_deleted': '已删除 {count} 个重复条目',
  'log_dup_fail': '删除重复失败: {error}', 'log_restored': '已从备份恢复: {name}', 'log_restore_fail': '恢复失败: {error}',
  'log_backup_deleted': '已删除备份: {name}', 'log_backup_delete_fail': '删除备份失败: {error}',
  'pre_issue_local_missing': '本地 JAR 文件缺失: {fn} ({path})', 'pre_issue_not_downloaded': '模组文件未下载: {fn}',
  'log_mrpack_index_updated': '已更新 .mrpack 中的 index.json', 'log_mrpack_index_fail': '更新 .mrpack 失败: {error}',
  'nav_home': '🏠 主页', 'nav_edit': '✏️ 编辑整合包', 'nav_settings': '⚙️ 设置',
  'home_import_local': '📂 导入本地整合包', 'home_import_local_desc': '选择 .mrpack / .zip 文件打开',
  'home_import_online': '🌐 通过名称导入整合包', 'home_import_online_desc': '在线搜索并下载整合包',
  'home_new_pack': '📄 新建整合包', 'home_new_pack_desc': '创建 .mrpack 或 .zip（Modrinth / CurseForge）',
  'edit_empty_hint': '请先在主页导入或新建整合包',
  'settings_title': '⚙️ 设置', 'settings_lang': '语言', 'settings_theme': '主题',
  'theme_dark': '🌙 深色', 'theme_light': '☀️ 浅色', 'lang_zh': '中文', 'lang_en': 'English',
  'type_label': '类型', 'type_mod': '🧩 模组', 'type_rp': '🎨 资源包', 'type_sp': '✨ 光影包',
  'add_local_file': '📂 添加本地文件', 'col_type': '类型', 'dlg_stats_types': '类型分布',
  'online_search_title': '🌐 通过名称导入整合包', 'online_search_placeholder': '输入整合包名称关键词...',
  'online_search_btn': '🔍 搜索', 'online_searching': '搜索中...', 'online_no_results': '没有找到匹配的整合包',
  'online_select': '选中此整合包', 'online_pick_version': '选择要下载的版本', 'online_downloading': '正在下载整合包...',
  'online_download_fail': '下载失败: {error}', 'online_by': '作者: {author} · 下载量: {dl}',
  'new_pack_title': '📄 新建整合包', 'new_pack_name': '名称', 'new_pack_version': '版本',
  'new_pack_format': '导出格式', 'fmt_modrinth': 'Modrinth (.mrpack)', 'fmt_curseforge': 'CurseForge (.zip)',
  'new_pack_create': '✅ 创建', 'new_pack_created': '✅ 已创建: {path}',
  'new_pack_loader_ver_required': '请填写 Forge/NeoForge 加载器版本（可在其官网查询）',
  'cf_export_ok': '已生成 CurseForge .zip:\n{path}',
},
'en_US':{
  'app_title': '⚡ Modpack Manager', 'app_sub': 'Lean & efficient', 
  'file_label': '📁 File',
  'path_label': 'Path:', 
  'info_label': '📋 Pack Info',
  'info_name': 'Name:', 'info_version': 'Version:', 'info_mc': 'MC version:',
  'info_loader': 'Loader:', 'info_loader_ver': 'Loader version:', 'expand_btn': '▶ Expand',
  'collapse_btn': '▼ Collapse', 'compat_unknown': '⚠️ Unknown', 'compat_unsupported': '⚠️ Unsupported',
  'compat_compatible': '✅ Compatible', 'compat_incompatible': '❌ Incompatible', 'add_mod_label': '➕ Add mod',
  'add_mod_placeholder': 'Project link or ID', 'fetch_btn': '🔍 Fetch versions', 'modlist_label': '📦 Mod list',
  'search_project_placeholder': 'Enter a project name...', 'search_project_btn': '🔎 Search by name',
  'search_project_title': '🔎 Search and add a project', 'search_projecting': 'Searching projects...',
  'search_project_no_result': 'No matching projects found', 'search_project_fail': 'Project search failed: {error}',
  'search_project_select': 'Select this project',
  'search_no_result': 'No matching mods found. Try another keyword', 'refresh_btn': '🔄 Refresh', 'delete_btn': '🗑️ Delete',
  'folder_btn': '📂 Open folder', 'check_update_btn': '🧪 Check for updates (experimental)',
  'backup_btn': '💾 Backup', 'reload_btn': '🔄 Reload', 'pack_btn': '📦 Pack .mrpack (with mods)',
  'export_btn': '📤 Export list', 'import_btn': '📥 Import list', 'log_label': '📋 Log',
  'settings_show_log': 'Show log panel',
  'status_ready': 'Ready ✅', 'status_loading': 'Loading...', 'status_saved': 'Saved ✅',
  'status_backup': 'Backed up', 'status_packed': 'Packed',
  'status_checking': 'Checking for updates...', 'status_downloading': 'Downloading...', 'col_name': 'Project Name',
  'col_filename': 'Filename', 'col_version': 'Version', 'col_path': 'Path',
  'col_project_id': 'Project ID', 'dialog_confirm_delete': 'Delete {count} selected mods?', 'dialog_select_mod': 'Please select at least one mod',
  'dialog_no_mods': 'No matching mods', 'dialog_file_not_found': 'File not found', 'dialog_open_mrpack_fail': 'The .mrpack file does not contain modrinth.index.json',
  'dialog_parse_error': 'Parse error: {error}', 'dialog_success_open': 'Opened {file}', 
  'dialog_version_fetch': 'Failed to fetch versions: {error}', 'dialog_no_version': 'No versions for this project', 'dialog_select_version': 'Please select a version first',
  'dialog_version_exists': 'Mod {filename} already exists, add anyway?', 'dialog_dep_prompt': 'Mod {filename} has the following dependencies:',
  'dialog_dep_existing': '(already exists)', 'dialog_dep_missing': '(missing)', 'dialog_dep_confirm': 'Do you want to install missing dependencies?',
  'dialog_update_experimental': 'The update check is experimental and results may be inaccurate.\n\nPlease back up your pack before proceeding.\n\nContinue?', 'dialog_no_update': 'All mods are up to date',
  'dialog_update_found': 'Found {count} mods with updates (experimental)', 'dialog_update_warning': '⚠️ Experimental, results may be inaccurate. Verify on Modrinth.', 'dialog_update_apply': 'Update {count} mods? (experimental)',
  'dialog_update_success': 'Successfully updated {count} mods', 'dialog_update_select': 'Please select at least one mod to update', 'dialog_pack_empty': 'No mods in this pack. Pack anyway?',
  'dialog_pack_success': 'Generated .mrpack file (with mod files):\n{path}', 'dialog_pack_fail': 'Pack failed: {error}', 'dialog_backup_success': 'Backup saved to {path}',
  'dialog_import_select': 'Please select a CSV file', 'dialog_import_success': 'Successfully imported {count} mods', 'dialog_import_fail': 'Import failed: {error}',
  'dialog_export_success': 'Exported list to {path}', 'dialog_local_jar_title': 'Add Local JAR', 'dialog_local_jar_prompt': 'Please select a JAR file',
  'dialog_local_jar_id': 'Enter Modrinth project ID (optional):', 'dialog_detail_title': 'Mod Details',
  'dialog_detail_no_id': 'This mod has no project ID, only local info shown.', 'log_download_done': 'Downloaded: {filename}',
  'log_download_fail': 'Download failed: {filename} - {error}', 'log_export': 'Exported mod list to {path}', 'log_import': 'Imported {count} mods from {path}',
  'log_async_pack_changed': 'Pack changed; unfinished operations were discarded',
  'log_refresh': 'Loaded {count} mods', 'log_local_jar': 'Added local mod {filename}', 'log_detail_view': 'View mod details: {name}',
  
  
  'button_open_selected': 'Open Selected', 'button_open_all': 'Open All',
  'button_install_missing': 'Install Missing', 'button_close': 'Close', 'button_cancel': 'Cancel',
  'button_select_this': 'Select This', 'button_update_selected': 'Update Selected', 'button_select_all': '☑ Select All',
  'button_show_all': '🔄 Show All', 'button_show_recommended': '🔄 Show Recommended/Compatible', 'column_mod_name': 'Mod Name',
  'column_current_ver': 'Current Version', 'column_latest_ver': 'Latest Version', 'column_action': 'Action',
  'dialog_confirm_overrides': 'Include overrides?', 'dialog_overrides_prompt': 'Pack custom config files into overrides directory?', 
  'log_no_overrides': 'No overrides folder selected, only index.json will be packed', 'dialog_pack_error': 'Cannot read index file', 'log_dep_fetch': 'Fetching latest version for dependency {name}...',
  'log_ov_applied': 'Applied {n} override files ({c} client-only)', 'log_ov_server': 'Kept {n} server-only override files (server-overrides, not merged into workspace)',
  'log_dep_added': 'Added dependency {name}', 'log_dep_exists': 'Dependency {name} already exists, skipped', 'dialog_dep_fetch_fail': 'Failed to fetch version for dependency {name}',
  'dialog_dep_add_success': 'Successfully added {count} dependencies', 'dialog_dep_no_missing': 'All dependencies already exist, nothing to add.', 'log_add_mod': 'Added mod {filename}',
  'log_delete_mod': 'Deleted {count} mods', 'log_pack': 'Packed: {path}', 'log_update_start': 'Starting update check (experimental)...',
  'log_update_done': 'All mods are up to date', 'log_update_success': 'Successfully updated {count} mods', 'log_theme_switch': 'Switched theme to {theme}',
  'log_lang_switch': 'Switched language to {lang}', 'dialog_open_cf_fail': 'This .zip is not a valid CurseForge modpack (invalid manifest.json)', 'log_cf_open': 'CurseForge modpack detected: {count} mods',
  'log_cf_resolving': 'Resolving CurseForge mods {done}/{total}...', 'log_cf_done': '✅ CurseForge mod resolution complete', 'log_cf_fail': '⚠ Cannot resolve CurseForge mod projectID={pid}, using placeholder filename',
  'log_cf_nohash': 'Failed to hash {filename} (checksum omitted): {error}', 'export_zip_btn': '📦 Export .zip', 'dialog_pack_success_zip': 'Generated .zip file:\n{path}',
  'diff_btn': '🔀 Compare packs', 'dialog_diff_pick_a': 'Select the first modpack (older)', 'dialog_diff_pick_b': 'Select the second modpack (newer)',
  'diff_title': 'Pack Comparison', 'diff_only': '— Only in {name} ({count}) —', 'diff_changed': '— Version changed ({count}) —',
  'diff_same': 'Both packs are identical', 'log_jar_identified': 'Identified local JAR: {filename} → {project} {version}', 'log_jar_unknown': 'Cannot identify {filename} on Modrinth, treating as local JAR',
  'dialog_changelog_title': 'Changelog', 'dialog_changelog_none': '(No changelog)', 
  'btn_detect_dup': '🔁 Dupes', 'btn_compat_check': '✅ Compat', 'btn_stats': '📊 Stats',
  'btn_backup_mgr': '💾 Backups', 'btn_pre_pack': '📋 Check',
  'btn_dl_all': '⬇ Download all', 'btn_switch_ver': '🔄 Switch',
  'btn_easy_switch': '🔁 Version Switch',
  'easy_switch_title': 'Version Switch — Target MC/Loader',
  'easy_switch_target_mc': 'Target MC', 'easy_switch_target_loader': 'Target Loader',
  'easy_switch_search_btn': '🔍 Check Compatibility', 'easy_switch_checking': 'Checking... {i}/{count}',
  'easy_switch_stats': '✅ OK {ok}  ❌ Bad {bad}  ⚠️ Unknown {unk}  📂 Local {local}',
  'easy_switch_col_name': 'Name', 'easy_switch_col_type': 'Type',
  'easy_switch_col_status': 'Status', 'easy_switch_col_target_ver': 'Target Ver',
  'easy_switch_status_ok': '✅ Compatible', 'easy_switch_status_bad': '❌ Unsupported',
  'easy_switch_status_unknown': '⚠️ Unknown', 'easy_switch_status_local': '📂 Local',
  'easy_switch_no_compatible': 'No upgradable mods', 'easy_switch_no_mods': 'No mod entries in pack',
  'easy_switch_select_mc': 'Please select target MC version', 'easy_switch_upgrade_btn': '⬆ Upgrade Selected',
  'log_easy_switch_start': 'Version switch started (target MC={mc}, loader={loader})...',
  'log_easy_switch_done': 'Version switch done: compatible {ok}, unsupported {bad}, unknown {unk}',
  'log_easy_switch_upgrade': 'Upgrade done: success {ok}, failed {fail}',
  'dlg_dup_title': 'Duplicate Detection', 'dlg_dup_none': 'No duplicates found', 'dlg_dup_intro': 'Found {count} duplicate groups:',
  'dlg_dup_delete_extra': 'Delete extras (keep first of each group)', 'dlg_compat_title': 'Compatibility Check', 'dlg_compat_ok': 'All mods are compatible',
  'dlg_compat_issues': 'Found {count} incompatible mods:', 'dlg_compat_skip_cf': 'Skipped {count} CurseForge mods', 'dlg_stats_title': 'Statistics',
  'dlg_stats_count': 'Total mods', 'dlg_stats_size': 'Total size', 'dlg_stats_source': 'Source distribution',
  'dlg_stats_no_url': 'Mods without a download URL', 'dlg_backups_title': 'Backup Management', 'dlg_backups_none': 'No backup files',
  'dlg_backups_restore': 'Restore', 'dlg_backups_delete': 'Delete', 'dlg_backups_restore_confirm': 'Restore this backup? Current index will be overwritten.',
  'dlg_backups_delete_confirm': 'Delete this backup?', 'dlg_switch_ver_title': 'Switch Version', 'dlg_switch_no_sel': 'Please select a mod in the list first',
  'dlg_switch_no_pid': 'This mod has no project ID, so the version cannot be switched', 'dlg_pre_pack_title': 'Pre-Pack Check',
  'dlg_pre_pack_ok': 'All mods passed the check', 'dlg_pre_pack_issues': 'Found {count} issues:', 'dlg_pre_pack_continue': 'Continue',
  'dlg_pre_pack_cancel': 'Cancel',
  'dlg_dl_all_title': 'Download All Mods', 'dlg_dl_all_done': 'Download done: success {ok}, failed {fail}',
  'dialog_title_done': 'Done', 'dialog_title_tip': 'Notice', 'dialog_title_error': 'Error',
  'log_mc_fetching': 'Fetching Minecraft versions...', 'log_mc_fetched': '✅ Fetched {count} MC versions', 'log_mc_fetch_fail': 'Failed to fetch MC versions',
  'log_loader_fetching': 'Fetching {loader} versions...', 'log_loader_fetch_fail': 'Failed to fetch {loader} versions (network issue?)',
  'log_mc_compat': 'MC {mc}: {count} compatible {loader} versions', 'log_mc_compat_none': 'No MC {mc} compatible versions found, showing all {count}',
  'log_loader_fetched': 'Fetched {count} {loader} versions', 'log_loader_compat_none': 'No MC {mc} compatible {loader} versions found',
  'log_delete_nomatch': 'No matching mods found', 'dialog_open_index_first': 'Please open an index.json first',
  'update_no_mods': 'No mods in this pack', 'update_no_pid': 'No mods contain a valid Modrinth project ID',
  'log_update_no_pid': 'No mods to check (missing project ID)', 'dep_none_added': 'No dependencies were added. Check your network or add them manually.',
  'dep_select_first': 'Select a dependency first', 'log_pack_start': 'Packing to {path}...',
  'log_ov_dir_added': 'Added {sub} directory ({n} local files)', 'log_ov_files_added': 'Added {n} override files: {path}',
  'dlg_overrides_dir': 'Select overrides folder', 
  'stats_local': 'Local', 'log_switched_to': 'Switched version → {filename}', 'dialog_switched': 'Switched to {filename}',
  'log_entry_not_found': 'Original mod not found: {path}', 'log_switch_fail': 'Failed to switch version: {error}',
  'log_index_saved': 'Pack info saved', 'status_no_change': 'No changes', 'status_packing': 'Packing...',
  'log_meta_loading': 'Loading metadata...', 'log_list_refreshing': 'Refreshing mod list...',
  'log_add_exists': '{filename} already exists, add cancelled', 'log_delete_fail': 'Delete failed: {error}',
  'log_update_fail': 'Update failed: {error}', 'log_cf_resolve_fail': 'Failed to resolve CurseForge mods: {error}',
  'log_cf_discarded': 'CF resolution finished, but the pack was switched; results were discarded', 'log_dl_all_start': 'Downloading all {count} files',
  'warn_need_url': 'Please enter a project URL or ID', 'err_parse_pid': 'Cannot parse project ID', 'log_no_link': 'No download link: {filename}',
  'log_sha1_fail': 'SHA1 mismatch: {filename}', 'log_dl_fail': 'Failed to download {filename}: {error}',
  'dialog_open_pack_fail': 'Failed to open .mrpack:\n{error}', 'log_compare_fail': 'Comparison failed:\n{error}',
  'log_import_write_fail': 'Failed to write imported data: {error}', 'log_skip_nolink': 'Skipped {filename} (no download link)',
  'log_downloading': 'Downloading {filename} ...', 'log_refresh_fail': 'Failed to refresh list: {error}', 'log_cf_check_fail': '[CF] Update check failed for {pid}: {error}',
  'log_read_fail': 'Failed to read: {error}', 'new_pack_default_name': 'My Modpack', 'log_lang_rebuilt': 'UI rebuilt with new language',
  'dlg_open_mrpack': 'Select a .mrpack file', 'log_opening': 'Opening pack: {path}', 'status_extracting': 'Extracting... {c}/{t}',
  'log_loaded_info': "Loaded: name='{name}', MC='{mc}', loader='{loader}', ver='{ver}'",
  'log_fetch_versions': 'Fetching versions for project {pid}...', 'selector_title': 'Select version - {id}',
  'col_game_version': 'Game version', 'col_loader': 'Loader', 'col_date': 'Release date', 'col_recommended': 'Featured',
  'selector_title_count': '{title} ({count} versions)', 'selector_filter': 'Filter: Minecraft {mc}',
  'log_add_version_fail': 'Failed to add version: {error}', 'log_rolled_back': 'Removed entries that failed to download: {path}',
  'log_rollback_fail': 'Failed to remove entry: {error}', 'log_dep_add_fail': 'Failed to add dependency {name}: {error}',
  'dep_loading': 'Loading... ({id})', 'log_csv_import_start': 'Importing from {path}...', 'csv_importing': 'Importing... {i}/{count}',
  'log_no_compat_version': 'No compatible version found: {pid}', 'log_version_data_bad': 'Bad version data: {pid}',
  'ft_jar': 'Mods / Resource packs / Shader packs', 'detail_loading': 'Loading details...',
  'detail_cf_info': 'Title: {title}\nSummary: {desc}\nDownloads: {downloads}',
  'detail_mr_info': 'Title: {title}\nAuthor: {author}\nSummary: {desc}\nDownloads: {downloads}\nLast updated: {updated}',
  'log_update_cancel': 'Update check cancelled', 'ver_unknown': 'Unknown version', 'update_selected': 'Selected {n}/{total}', 'update_action': '⬆ Update',
  'unknown': 'Unknown',
  'log_read_index_fail': 'Failed to read index: {error}', 'unnamed': 'Unnamed', 'log_entry_exists': '{path} already exists',
  'dup_keep': '✅ Keep', 'dup_extra': '❌ Delete', 'log_dup_deleted': 'Deleted {count} duplicate mods',
  'log_dup_fail': 'Failed to delete duplicates: {error}', 'log_restored': 'Restored from backup: {name}', 'log_restore_fail': 'Restore failed: {error}',
  'log_backup_deleted': 'Deleted backup: {name}', 'log_backup_delete_fail': 'Failed to delete backup: {error}',
  'pre_issue_local_missing': 'Local JAR file missing: {fn} ({path})', 'pre_issue_not_downloaded': 'Mod file not downloaded: {fn}',
  'log_mrpack_index_updated': 'Updated index.json inside .mrpack', 'log_mrpack_index_fail': 'Failed to update .mrpack: {error}',
  'nav_home': '🏠 Home', 'nav_edit': '✏️ Edit Pack', 'nav_settings': '⚙️ Settings',
  'home_import_local': '📂 Import Local Pack', 'home_import_local_desc': 'Open a .mrpack / .zip file',
  'home_import_online': '🌐 Import by Name', 'home_import_online_desc': 'Search & download packs online',
  'home_new_pack': '📄 New Pack', 'home_new_pack_desc': 'Create .mrpack or .zip (Modrinth / CurseForge)',
  'edit_empty_hint': 'Please import or create a pack on Home first',
  'settings_title': '⚙️ Settings', 'settings_lang': 'Language', 'settings_theme': 'Theme',
  'theme_dark': '🌙 Dark', 'theme_light': '☀️ Light', 'lang_zh': '中文', 'lang_en': 'English',
  'type_label': 'Type', 'type_mod': '🧩 Mod', 'type_rp': '🎨 Resource Pack', 'type_sp': '✨ Shader Pack',
  'add_local_file': '📂 Add Local File', 'col_type': 'Type', 'dlg_stats_types': 'Type distribution',
  'online_search_title': '🌐 Import Pack by Name', 'online_search_placeholder': 'Enter modpack name...',
  'online_search_btn': '🔍 Search', 'online_searching': 'Searching...', 'online_no_results': 'No modpacks found',
  'online_select': 'Select this pack', 'online_pick_version': 'Select version to download', 'online_downloading': 'Downloading pack...',
  'online_download_fail': 'Download failed: {error}', 'online_by': 'By {author} · Downloads: {dl}',
  'new_pack_title': '📄 New Pack', 'new_pack_name': 'Name', 'new_pack_version': 'Version',
  'new_pack_format': 'Format', 'fmt_modrinth': 'Modrinth (.mrpack)', 'fmt_curseforge': 'CurseForge (.zip)',
  'new_pack_create': '✅ Create', 'new_pack_created': '✅ Created: {path}',
  'new_pack_loader_ver_required': 'Please enter the Forge/NeoForge loader version (see their official site)',
  'cf_export_ok': 'CurseForge .zip created:\n{path}',
},
}

config = load_config()
CURRENT_LANG = config.get("language", "zh_CN")
CURRENT_THEME = config.get("theme", "dark")

def tr(key):
    return LANG[CURRENT_LANG].get(key, key)

def mod_match(entry, keyword):
    """搜索匹配纯函数：模组名称/文件名/路径/版本号，大小写不敏感、子串模糊匹配"""
    kw = (keyword or '').strip().lower()
    if not kw:
        return True
    return any(kw in str(entry.get(k, '')).lower()
               for k in ('display_name', 'filename', 'path', 'version'))

def _ver_sort_key(v):
    """'47.4.23' → (47,4,23)，用于加载器版本数值降序排序"""
    try:
        return tuple(int(x) for x in v.split('.'))
    except ValueError:
        return (0,)

# ---------- CTK 主题初始化（Fluent Design 配色）----------
ctk.set_appearance_mode(CURRENT_THEME)
try:
    ctk.set_default_color_theme({
        "blue": {"light": "#0078d4", "dark": "#60cdff"},
    })
except Exception:
    ctk.set_default_color_theme("blue")
try:
    ctk.set_widget_scaling(1.0)
except Exception:
    pass

# ---------- 缓存和API ----------
class Cache:
    def __init__(self):
        self.project_name = {}
        self.mc_versions = []
        self.fabric_versions = []
        self.fabric_mc_map = {}
        self.fabric_by_mc = {}
        self.forge_by_mc = {}
        self.neoforge_by_mc = {}

    def get_name(self, pid):
        return self.project_name.get(pid)

    def set_name(self, pid, name):
        self.project_name[pid] = name

class ModrinthAPI:
    def __init__(self, cache):
        self.cache = cache
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "MinecraftModPackWizard-GUI/1.0"})

    def fetch_fabric_versions(self, force_refresh=False):
        cached = self.cache.fabric_versions
        if cached and not force_refresh:
            return cached, self.cache.fabric_mc_map
        try:
            resp = self.session.get("https://meta.fabricmc.net/v2/versions/loader", timeout=REQUEST_TIMEOUT)
            if resp.status_code == 200:
                data = resp.json()
                versions, mc_map = [], {}
                for item in data:
                    if 'loader' in item:
                        v = item['loader']['version']
                        gvs = item.get('gameVersions', [])
                    else:
                        v = item.get('version')
                        gvs = item.get('gameVersions', [])
                    if v:
                        versions.append(v)
                        if gvs:
                            mc_map[v] = gvs
                self.cache.fabric_versions = versions
                self.cache.fabric_mc_map = mc_map
                self.cache.fabric_by_mc = {}
                return versions, mc_map
        except Exception:
            pass
        if cached:
            return cached, self.cache.fabric_mc_map
        return [], {}

    def fetch_fabric_versions_for_mc(self, mc_version, force_refresh=False):
        if not force_refresh and mc_version in self.cache.fabric_by_mc:
            return self.cache.fabric_by_mc[mc_version]
        try:
            resp = self.session.get(f"https://meta.fabricmc.net/v2/versions/loader/{mc_version}", timeout=REQUEST_TIMEOUT)
            if resp.status_code == 200:
                versions = []
                for item in resp.json():
                    if 'loader' in item:
                        v = item['loader'].get('version')
                    else:
                        v = item.get('version')
                    if v:
                        versions.append(v)
                self.cache.fabric_by_mc[mc_version] = versions
                return versions
        except Exception:
            pass
        all_versions, mc_map = self.fetch_fabric_versions(force_refresh=False)
        compatible = [v for v, supported in mc_map.items() if mc_version in supported]
        if not compatible:
            compatible = list(all_versions)
        self.cache.fabric_by_mc[mc_version] = compatible
        return compatible

    def fetch_forge_versions_for_mc(self, mc_version):
        """Forge 版本：解析 Forge maven-metadata.xml，条目形如 1.20.1-47.2.0。"""
        cached = self.cache.forge_by_mc.get(mc_version)
        if cached is not None:
            return cached
        versions = []
        try:
            resp = self.session.get(
                "https://maven.minecraftforge.net/net/minecraftforge/forge/maven-metadata.xml",
                timeout=REQUEST_TIMEOUT)
            if resp.status_code == 200:
                root = ET.fromstring(resp.text)
                prefix = mc_version + '-'
                for tag in root.iter('version'):
                    v = (tag.text or '').strip()
                    if v.startswith(prefix):
                        rest = v[len(prefix):]
                        # 只保留纯数字点分版本号，剔除带分支/时间戳后缀的构建
                        if re.fullmatch(r'\d+(\.\d+)*', rest):
                            versions.append(rest)
                versions.sort(key=_ver_sort_key, reverse=True)
        except Exception:
            pass
        self.cache.forge_by_mc[mc_version] = versions
        return versions

    def fetch_neoforge_versions_for_mc(self, mc_version):
        """NeoForge 版本：maven API JSON；版本号与 MC 对应（1.20.4→20.4.x，1.21.1→21.1.x）。"""
        cached = self.cache.neoforge_by_mc.get(mc_version)
        if cached is not None:
            return cached
        versions = []
        try:
            resp = self.session.get(
                "https://maven.neoforged.net/api/maven/versions/releases/net/neoforged/neoforge",
                timeout=REQUEST_TIMEOUT)
            if resp.status_code == 200:
                nums = mc_version.split('.')
                if len(nums) == 3:
                    prefix = f"{nums[1]}.{nums[2]}."
                elif len(nums) == 2:
                    prefix = f"{nums[1]}.0."
                else:
                    prefix = ''
                if prefix:
                    allv = resp.json().get('versions') or []
                    versions = [v for v in allv
                                if v.startswith(prefix) and re.fullmatch(r'\d+(\.\d+)*', v)]
                    versions.sort(key=_ver_sort_key, reverse=True)
        except Exception:
            pass
        self.cache.neoforge_by_mc[mc_version] = versions
        return versions

    def fetch_loader_versions_for_mc(self, loader, mc_version):
        """按加载器名称（Fabric/Forge/NeoForge）获取该 MC 版本可用的加载器版本。"""
        if loader == 'Forge':
            return self.fetch_forge_versions_for_mc(mc_version)
        if loader == 'NeoForge':
            return self.fetch_neoforge_versions_for_mc(mc_version)
        return self.fetch_fabric_versions_for_mc(mc_version)

    def fetch_project_name(self, project_id):
        if name := self.cache.get_name(project_id):
            return name
        try:
            resp = self.session.get(f"https://api.modrinth.com/v2/project/{project_id}", timeout=MODRINTH_SHORT_TIMEOUT)
            if resp.status_code == 200:
                name = resp.json().get('title', project_id)
                self.cache.set_name(project_id, name)
                return name
        except Exception:
            pass
        self.cache.set_name(project_id, project_id)
        return project_id

    def fetch_project_meta(self, project_id):
        """返回项目完整信息（含 project_type: mod/resourcepack/shader/modpack）"""
        try:
            resp = self.session.get(f"https://api.modrinth.com/v2/project/{project_id}", timeout=MODRINTH_MEDIUM_TIMEOUT)
            if resp.status_code == 200:
                data = resp.json()
                self.cache.set_name(project_id, data.get('title', project_id))
                return data
        except Exception:
            pass
        return None

    def fetch_mc_versions(self):
        if self.cache.mc_versions:
            return self.cache.mc_versions
        try:
            resp = self.session.get("https://api.modrinth.com/v2/tag/game_version", timeout=REQUEST_TIMEOUT)
            if resp.status_code == 200:
                versions = [v['version'] for v in resp.json() if v.get('version_type') in ('release','beta','alpha')]
                self.cache.mc_versions = versions
                return versions
        except Exception:
            pass
        return []

    def search_projects(self, query, add_type, mc_version, loader_api):
        resp = self.session.get(
            "https://api.modrinth.com/v2/search",
            params={'query': query, 'limit': 20,
                    'facets': json.dumps(
                        build_project_search_facets(add_type, mc_version, loader_api))},
            timeout=CF_WIDGET_TIMEOUT)
        resp.raise_for_status()
        hits = resp.json().get('hits', [])
        return hits if isinstance(hits, list) else []

    def _get_versions(self, project_id, mc_ver=None, loader_api=None, limit=100, offset=0):
        params = {'limit': limit, 'offset': offset}
        if mc_ver:
            params['game_versions'] = f'["{mc_ver}"]'
        if loader_api:
            params['loaders'] = f'["{loader_api}"]'
        try:
            resp = self.session.get(f"https://api.modrinth.com/v2/project/{project_id}/version",
                                    params=params, timeout=REQUEST_TIMEOUT)
            if resp.status_code == 200:
                return resp.json()
        except Exception:
            pass
        return []

    def get_latest_version(self, project_id, mc_ver, loader_api):
        v = self._get_versions(project_id, mc_ver, loader_api, limit=1)
        return v[0] if v else None

    def get_all_versions(self, project_id, mc_ver=None, loader_api=None):
        offset, limit, all_v = 0, 100, []
        while True:
            batch = self._get_versions(project_id, mc_ver, loader_api, limit, offset)
            if not batch or len(batch) < limit:
                all_v.extend(batch)
                break
            all_v.extend(batch)
            offset += limit
        return all_v

# ---------- 工具函数 ----------
def _normalize_version(v):
    v = v.strip()
    v = re.sub(r'^mc[\d.\-]+-', '', v)
    v = re.sub(r'[+\-]fabric.*$', '', v)
    v = re.sub(r'[+\-]forge.*$', '', v)
    v = re.sub(r'[+\-]neoforge.*$', '', v)
    v = re.sub(r'\+\d{1,3}(\.\d{1,3}){0,2}$', '', v)
    return v

def extract_version(filename):
    if m := re.search(r'(\d+(?:\.\d+)+)', filename):
        return m.group(1)
    return tr('ver_unknown')

def parse_project_id_from_url(url):
    if not url:
        return None
    if m := re.search(r"cdn\.modrinth\.com/data/([a-zA-Z0-9_-]+)", url):
        return m.group(1)
    if m := re.search(r"modrinth\.com/(?:mod|project)/([a-zA-Z0-9_-]+)", url):
        return m.group(1)
    if re.match(r"^[a-zA-Z0-9_-]+$", url.split('/')[-1]):
        return url.split('/')[-1]
    return None

# 内容类型：模组 / 资源包 / 光影包
TYPE_PREFIX = {'mod': 'mods', 'rp': 'resourcepacks', 'sp': 'shaderpacks'}
def entry_type(entry):
    p = (entry.get('path') or '').replace('\\', '/')
    if p.startswith('resourcepacks/'): return 'rp'
    if p.startswith('shaderpacks/'): return 'sp'
    return 'mod'
def entry_prefix(t):
    return TYPE_PREFIX.get(t, 'mods')

def is_current_pack_open(batch, current_batch):
    return batch == current_batch

def remove_entries_by_indices(entries, indices):
    return [entry for i, entry in enumerate(entries) if i not in indices]

def build_mod_entry(version_data, prefix='mods'):
    file_obj = version_data['files'][0]
    hashes = file_obj.get('hashes') or {}
    entry = {
        "path": f"{prefix or 'mods'}/{file_obj['filename']}",
        "hashes": {"sha1": hashes.get("sha1", ""), "sha512": hashes.get("sha512", "")},
        "downloads": [file_obj["url"]],
        "fileSize": file_obj.get("size") or 0,
    }
    if file_obj.get('env'):
        entry['env'] = file_obj['env']
    return entry
def project_type_to_add_type(pt):
    return {'resourcepack': 'rp', 'shader': 'sp'}.get(pt, 'mod')

def build_project_search_facets(add_type, mc_version, loader_api):
    project_type = {'rp': 'resourcepack', 'sp': 'shader'}.get(add_type, 'mod')
    facets = [[f'project_type:{project_type}']]
    if mc_version:
        facets.append([f'versions:{mc_version}'])
    if add_type == 'mod' and loader_api:
        facets.append([f'categories:{loader_api}'])
    return facets

def _hashfile(filepath, algo):
    h = algo()
    with open(filepath, 'rb') as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()

def compute_sha1(filepath):
    return _hashfile(filepath, hashlib.sha1)

def compute_sha512(filepath):
    return _hashfile(filepath, hashlib.sha512)

# ---------- 缓存管理 ----------
CF_WIDGET_CACHE = {}          # pid -> (timestamp, data|None)
CF_CACHE_TTL = 3600           # 缓存有效期（秒），过期自动刷新（定期更新机制）
CF_CACHE_FAIL_TTL = 300       # 获取失败的缓存有效期较短，便于重试

def cf_get_project(pid, tries=4, force_refresh=False):
    """通过 cfwidget 获取 CurseForge 项目信息。

    带 TTL 缓存：成功结果缓存 1 小时，失败结果缓存 5 分钟后自动重试；
    force_refresh=True 时强制刷新。处理网络异常与非 200 响应。
    """
    now = time.time()
    if not force_refresh and pid in CF_WIDGET_CACHE:
        ts, data = CF_WIDGET_CACHE[pid]
        ttl = CF_CACHE_TTL if data is not None else CF_CACHE_FAIL_TTL
        if now - ts < ttl:
            return data
    last_err = None
    for i in range(tries):
        try:
            resp = requests.get(f"https://api.cfwidget.com/{pid}", timeout=MODRINTH_LONG_TIMEOUT)
            if resp.status_code == 200:
                data = resp.json()
                if isinstance(data, dict) and data.get('files'):
                    CF_WIDGET_CACHE[pid] = (time.time(), data)
                    return data
                last_err = f"cfwidget {pid}: empty response"
                break
            try:
                err = resp.json().get('error', '')
            except Exception:
                err = ''
            last_err = f"cfwidget {pid}: HTTP {resp.status_code} {err}"
            if err not in ('in_queue', 'creating'):
                break
        except Exception as e:
            last_err = f"cfwidget {pid}: {e}"
            break
        time.sleep(2.5)
    if last_err:
        print(f"[CF] {last_err}")
    CF_WIDGET_CACHE[pid] = (time.time(), None)
    return None

CF_LOADER_TAGS = {'fabric': ['Fabric'], 'forge': ['Forge'], 'neoforge': ['NeoForge']}
CF_LOADER_FAMILIES = ['Fabric', 'Quilt', 'Forge', 'NeoForge']

def cf_get_project_versions(pid, mc_ver=None, loader=None, force_refresh=False):
    """获取 CurseForge 项目的版本（文件）列表。

    返回标准化列表：[{file_id, name, versions(list), filesize, released_at, url}, ...]
    mc_ver 不为空时只返回匹配该 MC 版本的文件；loader 不为空时按加载器标签过滤
    （cfwidget 文件 versions 数组同时含 MC 版本与加载器名）。失败返回空列表。
    """
    proj = cf_get_project(pid, force_refresh=force_refresh)
    if not proj:
        return []
    tags = CF_LOADER_TAGS.get(loader, []) if loader else []
    out = []
    for fo in proj.get('files', []):
        fv = fo.get('versions') or []
        if mc_ver and fv and mc_ver not in fv:
            continue
        if tags:
            if any(v in CF_LOADER_FAMILIES for v in fv) and not any(t in fv for t in tags):
                continue
        out.append({
            'file_id': fo.get('id', 0),
            'name': fo.get('name', ''),
            'versions': fv,
            'filesize': fo.get('filesize', 0),
            'released_at': fo.get('releasedAt') or fo.get('uploaded_at') or '',
            'url': cf_cdn_url(fo.get('id', 0), fo.get('name', '')),
        })
    return out

def cf_cdn_url(file_id, filename):
    return (f"https://mediafilez.forgecdn.net/files/{file_id // 1000}/"
            f"{file_id % 1000}/{quote(filename)}")

def cf_manifest_to_index(m):
    """把 CurseForge manifest.json 转成 Modrinth index 结构（files 待解析）"""
    mc = m.get('minecraft') or {}
    deps = {'minecraft': mc.get('version', '')}
    for ml in mc.get('modLoaders', []) or []:
        mid = str(ml.get('id', ''))
        if mid.startswith('fabric-'):
            deps['fabric-loader'] = mid[len('fabric-'):]
        elif mid.startswith('neoforge-'):
            deps['neoforge'] = mid[len('neoforge-'):]
        elif mid.startswith('forge-'):
            deps['forge'] = mid[len('forge-'):]
    return {'formatVersion': 1, 'game': 'minecraft',
            'name': m.get('name', ''), 'versionId': str(m.get('version', '')),
            'author': m.get('author', ''), 'files': [], 'dependencies': deps}

def compute_hashes_from_url(url):
    """流式下载并计算 sha1/sha512 与大小（用于 CurseForge 更新条目回填校验值）"""
    sha1, sha512, size = hashlib.sha1(), hashlib.sha512(), 0
    with requests.get(url, stream=True, timeout=STREAM_TIMEOUT) as resp:
        resp.raise_for_status()
        for chunk in resp.iter_content(chunk_size=65536):
            if chunk:
                sha1.update(chunk)
                sha512.update(chunk)
                size += len(chunk)
    return {'sha1': sha1.hexdigest(), 'sha512': sha512.hexdigest()}, size

def api_lookup_version_by_hash(sha1):
    """通过 sha1 反查 Modrinth 版本（用于识别本地 JAR），未命中返回 None"""
    try:
        resp = requests.get(f"https://api.modrinth.com/v2/version_file/{sha1}",
                            params={'algorithm': 'sha1'}, timeout=10)
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    return None

def merge_override_tree(extract_dir, rootname):
    """把包内 rootname/ 目录的内容合并到工作区根目录（同名文件覆盖），返回处理文件数"""
    src = os.path.join(extract_dir, rootname)
    n = 0
    if not os.path.isdir(src):
        return 0
    for r, _, fnames in os.walk(src):
        for fn in fnames:
            sp = os.path.join(r, fn)
            dp = os.path.join(extract_dir, os.path.relpath(sp, src))
            os.makedirs(os.path.dirname(dp), exist_ok=True)
            shutil.copy2(sp, dp)
            n += 1
    return n

def count_tree_files(d):
    return sum(len(fs) for _, _, fs in os.walk(d)) if os.path.isdir(d) else 0

def entry_identity_key(entry):
    """条目身份键：优先项目 ID（跨文件名匹配版本），否则退回路径"""
    cf = entry.get('cf')
    if cf:
        return ('cf', cf.get('projectID'))
    for d in entry.get('downloads', []) or []:
        pid = parse_project_id_from_url(d)
        if pid:
            return ('mr', pid)
    return ('path', entry.get('path', ''))

def diff_pack_files(files_a, files_b):
    """对比两组 index files：返回 (only_a, only_b, changed)"""
    map_a, map_b = {}, {}
    for e in files_a:
        map_a.setdefault(entry_identity_key(e), e)
    for e in files_b:
        map_b.setdefault(entry_identity_key(e), e)
    only_a = [(k, map_a[k]) for k in map_a if k not in map_b]
    only_b = [(k, map_b[k]) for k in map_b if k not in map_a]
    changed = []
    for k, ea in map_a.items():
        if k in map_b:
            eb = map_b[k]
            sig_a = (ea.get('cf') or {}).get('fileID') \
                or (ea.get('hashes') or {}).get('sha1', '')
            sig_b = (eb.get('cf') or {}).get('fileID') \
                or (eb.get('hashes') or {}).get('sha1', '')
            if sig_a and sig_b and sig_a != sig_b:
                changed.append((k, ea, eb))
    return only_a, only_b, changed

def _compare_simple(v1, v2):
    def parse(v):
        v = _normalize_version(v)
        return [int(x) for x in re.findall(r'\d+', v)]
    a, b = parse(v1), parse(v2)
    if not a and not b: return 0
    if not a: return -1
    if not b: return 1
    for i in range(max(len(a), len(b))):
        n1 = a[i] if i < len(a) else 0
        n2 = b[i] if i < len(b) else 0
        if n1 != n2:
            return n1 - n2
    return 0

# ---------- 主应用 ----------
class ModPackApp:
    def __init__(self, root):
        self.root = root
        self.root.minsize(1200, 800)
        self.root.title(tr('app_title'))
        self.root.after(100, lambda: self.root.state('zoomed'))

        self.cache = Cache()
        self.api = ModrinthAPI(self.cache)
        self.index_path = ctk.StringVar()
        self.mode = ctk.StringVar(value="existing")
        self.expanded = ctk.BooleanVar(value=False)
        self.loader_var = ctk.StringVar(value="Fabric")
        self.original_mrpack = None
        self.cf_mode = False
        self.pack_format = 'modrinth'   # 'modrinth' | 'curseforge'
        self._open_generation = 0
        self.current_page = 'home'      # 'home' | 'edit' | 'settings'
        self.add_type = ctk.StringVar(value='mod')   # 添加内容类型：mod/rp/sp
        self.all_mod_entries = []
        self._rows = []
        self._name_generation = 0
        self._last_filter_result = None
        self._render_generation = 0
        self._render_pending = False
        self.save_timer = None
        self.build_ui()
        self.root.after(150, lambda: self.entry_file.focus_set())
        self.log(tr('status_ready'))
        self.root.after(100, self.fetch_mc_versions)
        self.root.after(200, lambda: self.fetch_loader_versions(force_refresh=True))

    # ---------- UI 构造助手（Fluent Design 风格）----------
    def _btn(self, parent, text, cmd, color='gray', width=None, side='left', padx=4, fg=None):
        hover_key = f'{color}_hover'
        is_gray = color == 'gray'
        kw = dict(text=text, command=cmd, fg_color=C.get(color, color), corner_radius=8,
                  hover_color=C.get(hover_key, C.get(color, color)), font=FONT_SM,
                  height=34, border_width=0,
                  text_color=fg if fg else (C['text_light'] if is_gray else C['text_dark']))
        if width: kw['width'] = width
        btn = ctk.CTkButton(parent, **kw)
        btn.pack(side=side, padx=padx)
        return btn

    def _win(self, title, geometry):
        win = ctk.CTkToplevel(self.root)
        win.title(title)
        win.geometry(geometry)
        win.transient(self.root)
        win.grab_set()
        win.focus_force()
        return win

    def _thread(self, target, *args):
        """启动后台守护线程，避免阻塞 UI"""
        threading.Thread(target=target, args=args, daemon=True).start()

    def _index_path_or_warn(self):
        """返回当前 index 路径；不存在则弹错误并返回 None"""
        path = self.index_path.get().strip()
        if not path or not os.path.exists(path):
            messagebox.showerror(tr('dialog_title_error'),tr('dialog_file_not_found'))
            return None
        return path

    def _load_index(self, path):
        """加载 index JSON；失败时记录日志并返回 None"""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            self.log(tr('log_read_fail').format(error=str(e)), "ERROR")
            return None

    def _group(self, parent, title, expand=False, action=None):
        g = ctk.CTkFrame(parent, corner_radius=12, border_width=1, border_color=C['border'],
                         fg_color=C['mica'])
        g.pack(fill='both' if expand else 'x', expand=expand, pady=(0, 10))
        head = ctk.CTkFrame(g, fg_color="transparent")
        head.pack(fill='x', padx=14, pady=(10, 6))
        action_btn = None
        if action:
            action_btn = ctk.CTkButton(head, text=action[0], command=action[1],
                                       width=70, height=24, font=FONT_SM,
                                       fg_color=C['gray'], hover_color=C['gray_hover'],
                                       text_color=C['text_light'], border_width=0)
            action_btn.pack(side='right')
        ctk.CTkLabel(head, text=title, font=FONT_BOLD, anchor='w',
                     text_color=C['accent']).pack(side='left', fill='x')
        body = ctk.CTkFrame(g, fg_color="transparent")
        body.pack(fill='both' if expand else 'x', expand=expand, padx=14, pady=(0, 12))
        return g, body, action_btn

    def _toggle_row(self, row):
        row.selected = not row.selected
        if row.selected:
            row.configure(fg_color=C['selected'])
        else:
            row.configure(fg_color=row._base_fg if hasattr(row, '_base_fg') else "transparent")

    def _loader_api(self):
        """获取当前加载器对应的 API 标识（fabric/forge/neoforge）"""
        return LOADER_API.get(self.loader_var.get(), "fabric")

    # ---------- 页面切换 ----------
    def show_page(self, page):
        previous = self.current_page
        changed = page != previous
        if changed and previous == 'edit' and self._render_pending:
            self._render_generation += 1
        if changed and page == 'edit' and self._render_pending:
            self._last_filter_result = None
            self.root.after_idle(self.apply_filter)
        self.current_page = page
        self.pages[page].tkraise()
        for name, btn in self.nav_buttons.items():
            active = (name == page)
            btn.configure(fg_color=C['accent'] if active else 'transparent',
                          hover_color=C['accent_hover'] if active else C['gray_hover'],
                          text_color=C['text_dark'] if active else C['text_light'])

    # ---------- UI 构建 ----------
    def build_ui(self):
        main = ctk.CTkFrame(self.root, fg_color="transparent")
        main.pack(fill='both', expand=True, padx=12, pady=12)

        # 左侧导航栏
        nav = ctk.CTkFrame(main, width=170, corner_radius=12, fg_color=C['mica_strong'],
                           border_width=1, border_color=C['border'])
        nav.pack(side='left', fill='y', padx=(0, 10))
        nav.pack_propagate(False)
        ctk.CTkLabel(nav, text=tr('app_title'), font=FONT_BOLD, wraplength=150,
                     text_color=C['accent']).pack(fill='x', padx=12, pady=(16, 10))
        self.nav_buttons = {}
        for key, page in [('nav_home', 'home'), ('nav_edit', 'edit'), ('nav_settings', 'settings')]:
            b = ctk.CTkButton(nav, text='  ' + tr(key), command=lambda p=page: self.show_page(p),
                              height=44, corner_radius=8, font=FONT_SM, border_width=0, anchor='w',
                              fg_color='transparent', hover_color=C['gray_hover'], text_color=C['text_light'])
            b.pack(fill='x', padx=10, pady=4)
            self.nav_buttons[page] = b

        # 右侧内容区（三页面叠加）
        content = ctk.CTkFrame(main, fg_color="transparent")
        content.pack(side='left', fill='both', expand=True)
        content.grid_rowconfigure(0, weight=1)
        content.grid_columnconfigure(0, weight=1)
        self.pages = {}
        for name in ('home', 'edit', 'settings'):
            pg = ctk.CTkFrame(content, fg_color="transparent")
            pg.grid(row=0, column=0, sticky='nsew')
            self.pages[name] = pg
        self._build_home_page(self.pages['home'])
        self._build_edit_page(self.pages['edit'])
        self._build_settings_page(self.pages['settings'])
        self.show_page(self.current_page)

        # 底部状态栏
        status = ctk.CTkFrame(self.root, height=32, fg_color=C['mica_strong'], corner_radius=0,
                              border_width=1, border_color=C['border'])
        status.pack(fill='x', side='bottom')
        status.pack_propagate(False)
        self.status_var = ctk.StringVar(value=tr('status_ready'))
        self.status_label = ctk.CTkLabel(status, textvariable=self.status_var, anchor='w',
                                         font=FONT_SM, text_color=C['text_light'])
        self.status_label.pack(side='left', padx=12)
        # 进度条容器（百分比文字 + 进度条），初始隐藏；任务进行时整体出现于状态栏右侧
        self.progress_wrap = ctk.CTkFrame(status, fg_color="transparent")
        self.progress_pct = ctk.CTkLabel(self.progress_wrap, text="", font=FONT_SM,
                                         width=40, anchor='e', text_color=C['text_light'])
        self.progress_pct.pack(side='left', padx=(0, 8))
        self.progress = ctk.CTkProgressBar(self.progress_wrap, width=210, height=10,
                                           corner_radius=5, mode='determinate')
        self.progress.set(0)
        self.progress.pack(side='left')
        self._prog_indet = False

    # ---------- 主页 ----------
    def _build_home_page(self, pg):
        ctk.CTkLabel(pg, text=tr('app_title'), font=FONT_TITLE,
                     text_color=C['accent']).pack(pady=(60, 6))
        ctk.CTkLabel(pg, text=tr('app_sub'), font=FONT_SM,
                     text_color=('gray50', 'gray70')).pack(pady=(0, 30))
        cards = ctk.CTkFrame(pg, fg_color="transparent")
        cards.pack(pady=10)
        for title_key, desc_key, cmd, color in [
                ('home_import_local', 'home_import_local_desc', self.open_mrpack, 'accent'),
                ('home_import_online', 'home_import_online_desc', self.online_import_pack, 'accent2'),
                ('home_new_pack', 'home_new_pack_desc', self.new_pack_wizard, 'success')]:
            b = ctk.CTkButton(cards, text=f"{tr(title_key)}\n{tr(desc_key)}", command=cmd,
                              width=460, height=84, corner_radius=12, font=FONT_MD_BOLD,
                              fg_color=C[color], hover_color=C[f'{color}_hover'],
                              text_color=C['text_dark'], border_width=0)
            b.pack(pady=8)

    # ---------- 设置页 ----------
    def _build_settings_page(self, pg):
        g, body, _ = self._group(pg, tr('settings_title'))
        g.pack(fill='x', padx=40, pady=40)
        ctk.CTkLabel(body, text=tr('settings_lang'), font=FONT_BOLD, anchor='w').pack(fill='x', pady=(6, 2))
        row1 = ctk.CTkFrame(body, fg_color="transparent"); row1.pack(fill='x', pady=4)
        self.lang_var = ctk.StringVar(value=CURRENT_LANG)
        for txt, val in [(tr('lang_zh'), 'zh_CN'), (tr('lang_en'), 'en_US')]:
            ctk.CTkRadioButton(row1, text=txt, variable=self.lang_var,
                               value=val, font=FONT_SM,
                               command=lambda v=val: self._set_lang(v)).pack(side='left', padx=16)
        ctk.CTkLabel(body, text=tr('settings_theme'), font=FONT_BOLD, anchor='w').pack(fill='x', pady=(14, 2))
        row2 = ctk.CTkFrame(body, fg_color="transparent"); row2.pack(fill='x', pady=4)
        self._btn(row2, tr('theme_dark'), lambda: self._set_theme('dark'), 'gray', width=120)
        self._btn(row2, tr('theme_light'), lambda: self._set_theme('light'), 'gray', width=120)
        row3 = ctk.CTkFrame(body, fg_color="transparent"); row3.pack(fill='x', pady=(18, 4))
        self.sw_log = ctk.CTkSwitch(row3, text=tr('settings_show_log'), font=FONT_SM,
                                    command=self.toggle_log)
        (self.sw_log.select if self.log_visible else self.sw_log.deselect)()
        self.sw_log.pack(side='left', padx=16)

    def _set_lang(self, lang):
        global CURRENT_LANG
        if CURRENT_LANG == lang:
            return
        CURRENT_LANG = lang
        save_config({"language": CURRENT_LANG, "theme": CURRENT_THEME})
        self.log(tr('log_lang_switch').format(lang=CURRENT_LANG))
        self._smooth_rebuild()

    def _set_theme(self, theme):
        global CURRENT_THEME
        CURRENT_THEME = theme
        ctk.set_appearance_mode(theme)
        save_config({"language": CURRENT_LANG, "theme": theme})
        self.log(tr('log_theme_switch').format(theme=theme))

    # ---------- 编辑整合包页 ----------
    def _build_edit_page(self, pg):
        body = ctk.CTkFrame(pg, fg_color="transparent")
        body.pack(fill='both', expand=True)
        body.grid_columnconfigure(0, weight=4)
        body.grid_columnconfigure(1, weight=1)
        body.grid_rowconfigure(0, weight=1)
        self.edit_body = body
        left = ctk.CTkFrame(body, fg_color="transparent")
        left.grid(row=0, column=0, sticky='nsew', padx=(0, 4))
        right = ctk.CTkFrame(body, fg_color="transparent")
        right.grid(row=0, column=1, sticky='nsew', padx=(4, 0))
        self.right_col = right

        # 文件组
        _, file_body, _ = self._group(left, tr('file_label'))
        fr = ctk.CTkFrame(file_body, fg_color="transparent"); fr.pack(fill='x')
        ctk.CTkLabel(fr, text=tr('path_label'), font=FONT_SM).pack(side='left')
        self.entry_file = ctk.CTkEntry(fr, textvariable=self.index_path, font=FONT)
        self.entry_file.pack(side='left', padx=5, fill='x', expand=True)

        # 整合包信息组（含备份/导出按钮）
        info_group, info_body, _ = self._group(left, tr('info_label'))
        self.info_group = info_group
        ib = ctk.CTkFrame(info_body, fg_color="transparent"); ib.pack(fill='x', pady=(0, 4))
        self.btn_toggle = self._btn(ib, tr('expand_btn'), self.toggle_info, 'gray', width=90)
        for txt, cmd, color in [(tr('backup_btn'), self.manual_backup, 'gray'),
                                (tr('btn_backup_mgr'), self.manage_backups, 'gray'),
                                (tr('reload_btn'), self.reload_metadata, 'gray')]:
            self._btn(ib, txt, cmd, color, width=90)
        self.btn_pack_mrpack = self._btn(ib, tr('pack_btn'), self.pack_to_mrpack, 'accent', width=120)
        self.btn_export_zip = self._btn(ib, tr('export_zip_btn'), self.export_zip_dispatch, 'accent2', width=110)
        self.content = ctk.CTkFrame(info_body, fg_color=C['mica_strong'], height=2, corner_radius=10)
        self.content.pack(fill='x', padx=5, pady=5)
        self.content.pack_propagate(False)
        labels = [tr('info_name'), tr('info_version'), tr('info_mc'), tr('info_loader'), tr('info_loader_ver')]
        self.entry_name = ctk.CTkEntry(self.content, width=220, font=FONT)
        self.entry_name.insert(0, tr('new_pack_default_name'))
        self.entry_version = ctk.CTkEntry(self.content, width=220, font=FONT)
        self.entry_version.insert(0, "1.0.0")
        self.combo_mc = ctk.CTkComboBox(self.content, values=[], width=220, font=FONT_SM,
                                        command=lambda _v: self.schedule_save())
        self.combo_mc.set("1.20.1")
        self.combo_loader_type = ctk.CTkComboBox(self.content, values=["Fabric", "Forge", "NeoForge"],
                                                  variable=self.loader_var, width=220, font=FONT_SM,
                                                  command=lambda _v: self.schedule_save())
        self.combo_loader_ver = ctk.CTkComboBox(self.content, values=[], width=220, font=FONT_SM,
                                                command=lambda _v: self.schedule_save())
        self.combo_loader_ver.set("")
        self.compatibility_label = ctk.CTkLabel(self.content, text="", font=FONT_SM)
        widgets = [self.entry_name, self.entry_version, self.combo_mc,
                   self.combo_loader_type, self.combo_loader_ver]
        for i, (label, w) in enumerate(zip(labels, widgets)):
            ctk.CTkLabel(self.content, text=label, font=FONT_SM).grid(row=i, column=0, sticky='e', padx=4, pady=4)
            w.grid(row=i, column=1, padx=4, pady=4, sticky='w')
        self.compatibility_label.grid(row=4, column=2, padx=4, pady=4, sticky='w')
        for w in [self.entry_name, self.entry_version]:
            w.bind('<FocusOut>', lambda e: self.schedule_save())
        ctk.CTkButton(self.content, text="🔄", command=self.fetch_mc_versions, width=30,
                      fg_color=C['gray'], hover_color=C['gray_hover'], font=FONT_SM,
                      corner_radius=8, height=30, border_width=0,
                      text_color=C['text_light']).grid(row=2, column=3, padx=2)
        ctk.CTkButton(self.content, text="🔄",
                      command=lambda: self.fetch_loader_versions(force_refresh=True), width=30,
                      fg_color=C['gray'], hover_color=C['gray_hover'], font=FONT_SM,
                      corner_radius=8, height=30, border_width=0,
                      text_color=C['text_light']).grid(row=4, column=3, padx=2)
        self.toggle_info(force=True)

        # 添加模组组（类型选择 + URL + 本地文件）
        _, add_body, _ = self._group(left, tr('add_mod_label'))
        tr_row = ctk.CTkFrame(add_body, fg_color="transparent"); tr_row.pack(fill='x', pady=(0, 4))
        ctk.CTkLabel(tr_row, text=tr('type_label'), font=FONT_SM).pack(side='left', padx=(0, 8))
        for txt, val in [(tr('type_mod'), 'mod'), (tr('type_rp'), 'rp'), (tr('type_sp'), 'sp')]:
            ctk.CTkRadioButton(tr_row, text=txt, variable=self.add_type, value=val,
                               font=FONT_SM).pack(side='left', padx=10)
        ar = ctk.CTkFrame(add_body, fg_color="transparent"); ar.pack(fill='x')
        ctk.CTkLabel(ar, text=tr('add_mod_placeholder'), font=FONT_SM).pack(side='left')
        self.url_entry = ctk.CTkEntry(ar, width=360, font=FONT)
        self.url_entry.pack(side='left', padx=5, fill='x', expand=True)
        self._btn(ar, tr('fetch_btn'), self.fetch_versions_from_url, 'accent2', width=100)
        self.add_local_btn = self._btn(ar, tr('add_local_file'), self.add_local_jar, 'gray', width=120)
        srch = ctk.CTkFrame(add_body, fg_color="transparent"); srch.pack(fill='x', pady=(5, 0))
        self.project_search_entry = ctk.CTkEntry(
            srch, font=FONT, placeholder_text=tr('search_project_placeholder'))
        self.project_search_entry.pack(side='left', padx=(0, 5), fill='x', expand=True)
        self._btn(srch, tr('search_project_btn'), self.search_projects_to_add,
                  'accent2', width=120)
        self.project_search_entry.bind('<Return>', lambda e: self.search_projects_to_add())

        # 工具按钮行
        bf = ctk.CTkFrame(left, fg_color="transparent")
        bf.pack(side='bottom', pady=(6, 0))
        for txt, cmd, color in [(tr('diff_btn'), self.compare_packs, 'gray'),
                                (tr('btn_detect_dup'), self.detect_duplicates, 'gray'),
                                (tr('btn_compat_check'), self.compatibility_check, 'gray'),
                                (tr('btn_stats'), self.show_stats, 'gray'),
                                (tr('btn_pre_pack'), self.pre_pack_check, 'warning'),
                                (tr('btn_dl_all'), self.download_all_mods, 'success'),
                                (tr('btn_easy_switch'), self.easy_switch_check, 'accent2')]:
            self._btn(bf, txt, cmd, color, width=100, padx=3)

        # 模组列表组
        _, list_body, _ = self._group(left, tr('modlist_label'), expand=True)
        sr = ctk.CTkFrame(list_body, fg_color="transparent"); sr.pack(fill='x', pady=(0, 5))
        ctk.CTkLabel(sr, text="🔍", font=FONT).pack(side='left')
        self.search_var = ctk.StringVar(value="")
        self._filter_timer = None
        self.search_var.trace('w', lambda *a: self._debounce_filter())
        self.search_entry = ctk.CTkEntry(sr, textvariable=self.search_var, width=200, font=FONT)
        self.search_entry.pack(side='left', padx=5, fill='x', expand=True)
        self._btn(sr, "✕", lambda: (self.search_var.set(""), self.apply_filter()), 'gray', width=30)

        tb = ctk.CTkFrame(list_body, fg_color="transparent"); tb.pack(fill='x', pady=(0, 5))
        for txt, cmd, color in [
            (tr('refresh_btn'), self.refresh_mod_list, 'accent'),
            (tr('delete_btn'), self.delete_selected, 'danger'),
            (tr('folder_btn'), self.open_mods_folder, 'warning'),
            (tr('check_update_btn'), self.check_updates, 'accent2'),
            (tr('export_btn'), self.export_mod_list, 'gray'),
            (tr('import_btn'), self.import_mod_list, 'gray'),
            (tr('btn_switch_ver'), self.switch_mod_version, 'accent2'),
        ]:
            self._btn(tb, txt, cmd, color, width=100)

        list_wrap = ctk.CTkFrame(list_body, fg_color="transparent")
        list_wrap.pack(fill='both', expand=True)
        col_widths = [210, 180, 90, 80, 170]
        hdr = ctk.CTkFrame(list_wrap, fg_color=C['header'], corner_radius=10, height=40,
                           border_width=1, border_color=C['border'])
        hdr.pack(fill='x'); hdr.pack_propagate(False)
        for i, h in enumerate([tr('col_name'), tr('col_filename'), tr('col_version'),
                               tr('col_type'), tr('col_path')]):
            ctk.CTkLabel(hdr, text=h, font=FONT_BOLD, anchor='w', width=col_widths[i],
                         text_color=('gray30', '#e5e5e5')).pack(side='left', padx=4, pady=4)
        self.tree = ctk.CTkScrollableFrame(list_wrap, fg_color=C['zebra'], height=280, corner_radius=10)
        self.tree.pack(fill='both', expand=True)
        self._col_widths = col_widths
        self._row_cache = {}

        # 右侧日志（可整体隐藏：隐藏时连背景框一起消失，左侧列表占用该空间）
        self.log_visible = config.get('show_log', True)
        log_group, log_body, _ = self._group(right, tr('log_label'), expand=True)
        self.log_group = log_group
        self.log_body = log_body
        self.log_text = ctk.CTkTextbox(log_body, font=FONT_LOG, wrap='word')
        self.log_text.pack(fill='both', expand=True)
        self.log_text.configure(state='disabled')
        if not self.log_visible:
            self._apply_log_visibility()

    # ---------- 核心功能 ----------
    def _ui(self, fn):
        """统一的 UI 调度：主线程直接执行，子线程经 after 回到主线程（线程安全）"""
        if threading.current_thread() is threading.main_thread():
            fn()
        else:
            self.root.after(0, fn)

    def log(self, msg, level="INFO"):
        def ui():
            self.log_text.configure(state='normal')
            ts = datetime.now().strftime("%H:%M:%S")
            prefix = {"ERROR": "❌", "SUCCESS": "✅", "WARNING": "⚠️"}.get(level, "ℹ️")
            self.log_text.insert('end', f"[{ts}] {prefix} {msg}\n")
            self.log_text.see('end')
            self.log_text.configure(state='disabled')
        self._ui(ui)

    def set_status(self, msg):
        def ui():
            self.status_var.set(msg)
            self.root.update_idletasks()
        self._ui(ui)

    def _apply_log_visibility(self):
        """显示/隐藏整个日志列（含背景框），并让左侧列表伸缩补位"""
        if self.log_visible:
            self.right_col.grid(row=0, column=1, sticky='nsew', padx=(4, 0))
            self.edit_body.grid_columnconfigure(1, weight=1)
        else:
            self.right_col.grid_remove()
            self.edit_body.grid_columnconfigure(1, weight=0, minsize=0)

    def toggle_log(self):
        self.log_visible = not self.log_visible
        self._apply_log_visibility()
        if getattr(self, 'sw_log', None):
            (self.sw_log.select if self.log_visible else self.sw_log.deselect)()
        save_config({"language": CURRENT_LANG, "theme": CURRENT_THEME,
                     "show_log": self.log_visible})

    # ---------- 进度条（线程安全，经 _ui 调度；含百分比文字）----------
    def progress_show(self, indeterminate=False):
        def ui():
            self.progress.stop()
            self._prog_indet = indeterminate
            if not self.progress_wrap.winfo_manager():
                self.progress_wrap.pack(side='right', padx=12)
            if indeterminate:
                self.progress_pct.configure(text="···")
                self.progress.configure(mode='indeterminate')
                self.progress.start()
            else:
                self.progress_pct.configure(text="0%")
                self.progress.configure(mode='determinate')
                self.progress.set(0)
            self.progress_wrap.update_idletasks()
        self._ui(ui)

    def progress_set(self, done, total):
        frac = max(0.0, min(1.0, done / total)) if total else 0.0
        pct = f"{round(frac * 100)}%"
        def ui():
            if not self._prog_indet:
                self.progress.set(frac)
                self.progress_pct.configure(text=pct)
        self._ui(ui)

    def progress_hide(self):
        def ui():
            self.progress.stop()
            self._prog_indet = False
            self.progress.set(0)
            self.progress_pct.configure(text="")
            self.progress_wrap.pack_forget()
        self._ui(ui)

    def _rebuild_ui(self):
        self._rebuilding = True
        self._render_generation += 1
        for t in ('save_timer', '_filter_timer'):
            if getattr(self, t, None):
                self.root.after_cancel(getattr(self, t))
                setattr(self, t, None)
        for w in self.root.winfo_children():
            w.destroy()
        self.build_ui()
        if self.cache.mc_versions:
            self.combo_mc.configure(values=self.cache.mc_versions)
            self.combo_mc.set(self.combo_mc.get() or self.cache.mc_versions[0])
        if self.cache.fabric_versions:
            self.combo_loader_ver.configure(values=self.cache.fabric_versions)
            self.combo_loader_ver.set(self.combo_loader_ver.get() or self.cache.fabric_versions[0])
        self._rebuilding = False
        self._refresh_format_buttons()
        # 重新加载已打开整合包的元数据，避免信息区被默认值覆盖并误存
        path = self.index_path.get().strip()
        if path and os.path.exists(path):
            self.load_metadata(path)
        self.refresh_mod_list()

    def _smooth_rebuild(self, done=None):
        """在当前事件队列结束后一次性重建，避免整窗淡出/淡入造成闪断。"""
        def rebuild():
            self._rebuild_ui()
            if done:
                done()
        self.root.after_idle(rebuild)

    def toggle_info(self, force=False):
        self.expanded.set(not self.expanded.get() if not force else False)
        if self.expanded.get():
            self.content.configure(height=200)
            for w in self.content.winfo_children():
                w.grid()
            self.btn_toggle.configure(text=tr('collapse_btn'))
        else:
            self.content.configure(height=2)
            for w in self.content.winfo_children():
                w.grid_remove()
            self.btn_toggle.configure(text=tr('expand_btn'))

    # ---------- 文件操作 ----------
    def _refresh_format_buttons(self):
        """CurseForge 格式隐藏 .mrpack 打包按钮，Modrinth 格式恢复显示（保持原按钮顺序）"""
        if not hasattr(self, 'btn_pack_mrpack'):
            return
        if self.pack_format == 'curseforge':
            self.btn_pack_mrpack.pack_forget()
        elif not self.btn_pack_mrpack.winfo_manager():
            self.btn_pack_mrpack.pack(side='left', padx=4,
                                      before=self.btn_export_zip)

    def open_mrpack(self):
        path = filedialog.askopenfilename(title=tr('dlg_open_mrpack'),
                                          filetypes=[("Modrinth Modpack", "*.mrpack"), ("Zip archive", "*.zip")])
        if not path:
            return
        self._open_pack_path(path)

    def _open_pack_path(self, path):
        self._open_generation += 1
        generation = self._open_generation
        self.log(tr('log_opening').format(path=path))
        self.set_status(tr('status_loading'))
        self.progress_show()
        def task():
            extract_dir = None
            try:
                extract_dir = tempfile.mkdtemp(prefix="mrpack_")
                with zipfile.ZipFile(path, 'r') as zipf:
                    names = zipf.namelist()
                    total = len(names)
                    self.root.after(0, lambda g=generation, t=total:
                        (self.set_status(tr('status_extracting').format(c=0, t=t)),
                         self.progress_set(0, t)) if is_current_pack_open(g, self._open_generation) else None)
                    for i, name in enumerate(names):
                        zipf.extract(name, extract_dir)
                        if (i + 1) % 10 == 0 or i + 1 == total:
                            self.root.after(0, lambda c=i+1, t=total, g=generation:
                                (self.set_status(tr('status_extracting').format(c=c, t=t)),
                                 self.progress_set(c, t)) if is_current_pack_open(g, self._open_generation) else None)
                index_path = os.path.join(extract_dir, "modrinth.index.json")
                cf_pending = None
                is_cf = False
                if not os.path.exists(index_path):
                    # 通用 zip 识别：根目录无 modrinth.index.json 时尝试 CurseForge manifest.json
                    index_data, cf_pending = self._parse_cf_manifest(extract_dir)
                    is_cf = True
                    index_path = os.path.join(extract_dir, "modrinth.index.json")
                    with open(index_path, 'w', encoding='utf-8') as f:
                        json.dump(index_data, f, indent=2, ensure_ascii=False)
                # 应用覆盖文件：overrides 与客户端专用目录合并到工作区根；server-overrides 仅保留
                ov_n = merge_override_tree(extract_dir, 'overrides')
                if is_cf:
                    cli_n = merge_override_tree(extract_dir, 'clientoverrides')
                    srv_n = 0
                else:
                    cli_n = merge_override_tree(extract_dir, 'client-overrides')
                    srv_n = count_tree_files(os.path.join(extract_dir, 'server-overrides'))
                ov_counts = (ov_n + cli_n, cli_n, srv_n)
                self.root.after(0, lambda g=generation, d=extract_dir:
                    self._finish_open_mrpack(g, d, path, index_path, cf_pending, is_cf, ov_counts))
            except Exception as e:
                if extract_dir:
                    shutil.rmtree(extract_dir, ignore_errors=True)
                import traceback
                err_msg = f"{e}\n{traceback.format_exc()[-300:]}"
                self.root.after(0, lambda g=generation: self._on_open_mrpack_error(err_msg)
                                if is_current_pack_open(g, self._open_generation) else None)
        self._thread(task)

    def _finish_open_mrpack(self, generation, extract_dir, mrpack_path, index_path,
                            cf_pending, is_cf, ov_counts):
        if not is_current_pack_open(generation, self._open_generation):
            shutil.rmtree(extract_dir, ignore_errors=True)
            return
        self._after_open_mrpack(mrpack_path, index_path, cf_pending, is_cf, ov_counts)

    # ---------- 主页：在线名称导入 ----------
    def online_import_pack(self):
        win = self._win(tr('online_search_title'), "780x580")
        top = ctk.CTkFrame(win, fg_color="transparent"); top.pack(fill='x', padx=10, pady=10)
        entry = ctk.CTkEntry(top, font=FONT, placeholder_text=tr('online_search_placeholder'))
        entry.pack(side='left', fill='x', expand=True, padx=(0, 6))
        results_box = ctk.CTkScrollableFrame(win, fg_color=C['zebra'], corner_radius=10)
        results_box.pack(fill='both', expand=True, padx=10, pady=5)
        status_lb = ctk.CTkLabel(win, text="", font=FONT_SM); status_lb.pack(pady=2)

        def do_search():
            kw = entry.get().strip()
            if not kw:
                return
            status_lb.configure(text=tr('online_searching'))
            def task():
                try:
                    resp = self.api.session.get(
                        "https://api.modrinth.com/v2/search",
                        params={'query': kw, 'limit': 20, 'facets': '[["project_type:modpack"]]'},
                        timeout=15)
                    hits = resp.json().get('hits', []) if resp.status_code == 200 else []
                except Exception:
                    hits = []
                self.root.after(0, lambda: populate(hits))
            self._thread(task)

        def populate(hits):
            for w in results_box.winfo_children():
                w.destroy()
            if not hits:
                ctk.CTkLabel(results_box, text=tr('online_no_results'),
                             font=FONT_SM).pack(pady=20)
            else:
                for h in hits:
                    row = ctk.CTkFrame(results_box, fg_color="transparent", corner_radius=6)
                    row.pack(fill='x', pady=2, padx=4)
                    ctk.CTkLabel(row, text=h.get('title', '?'), font=FONT_BOLD,
                                 anchor='w').pack(fill='x', padx=6)
                    ctk.CTkLabel(row, text=tr('online_by').format(
                        author=h.get('author', '?'), dl=h.get('downloads', 0)),
                        font=FONT_SM, anchor='w', text_color=('gray40', 'gray60')).pack(fill='x', padx=6)
                    desc = (h.get('description') or '')[:90]
                    if desc:
                        ctk.CTkLabel(row, text=desc, font=FONT_SM, anchor='w',
                                     text_color=('gray40', 'gray60')).pack(fill='x', padx=6, pady=(0, 2))
                    def pick(_e=None, pid=h.get('project_id'), t=h.get('title', '?')):
                        win.destroy()
                        self._online_pick_version(pid, t)
                    row.bind('<Button-1>', pick)
                    for w in row.winfo_children():
                        w.bind('<Button-1>', pick)
            status_lb.configure(text="")

        self._btn(top, tr('online_search_btn'), do_search, 'accent2', width=100)
        entry.bind('<Return>', lambda e: do_search())

    def _online_pick_version(self, pid, title):
        self.set_status(tr('status_loading'))
        def task():
            try:
                resp = self.api.session.get(
                    f"https://api.modrinth.com/v2/project/{pid}/version", timeout=15)
                versions = resp.json() if resp.status_code == 200 else []
            except Exception:
                versions = []
            self.root.after(0, lambda: self._online_versions_ready(versions, title))
        self._thread(task)

    def _online_versions_ready(self, versions, title):
        self.set_status(tr('status_ready'))
        if not versions:
            messagebox.showinfo(tr('online_search_title'), tr('online_no_results'))
            return
        self._version_table(tr('online_pick_version'), versions[:5], versions, '', None,
                            lambda v: self._online_download(v, title), 'button_cancel')

    def _online_download(self, version, title):
        files = version.get('files') or []
        if not files:
            messagebox.showerror(tr('dialog_title_error'),tr('online_no_results'))
            return
        f0 = files[0]
        url, fname = f0.get('url', ''), f0.get('filename', f"{title}.mrpack")
        save_path = filedialog.asksaveasfilename(
            defaultextension=".mrpack", filetypes=[("Modrinth Modpack", "*.mrpack")],
            initialfile=fname)
        if not save_path:
            return
        self.set_status(tr('online_downloading'))
        def task():
            try:
                with requests.get(url, stream=True, timeout=STREAM_TIMEOUT) as resp:
                    resp.raise_for_status()
                    with open(save_path, 'wb') as f:
                        for chunk in resp.iter_content(8192):
                            f.write(chunk)
                self.root.after(0, lambda: self._open_pack_path(save_path))
            except Exception as e:
                err = str(e)
                self.root.after(0, lambda: messagebox.showerror(
                    tr('dialog_title_error'), tr('online_download_fail').format(error=err)))
                self.root.after(0, lambda: self.set_status(tr('status_ready')))
        self._thread(task)

    # ---------- 主页：新建整合包 ----------
    def new_pack_wizard(self):
        win = self._win(tr('new_pack_title'), "500x520")
        fr = ctk.CTkFrame(win, fg_color="transparent")
        fr.pack(fill='both', expand=True, padx=24, pady=18)

        def makerow(label):
            r = ctk.CTkFrame(fr, fg_color="transparent"); r.pack(fill='x', pady=5)
            ctk.CTkLabel(r, text=label, font=FONT_SM, width=110, anchor='w').pack(side='left')
            return r

        r = makerow(tr('new_pack_name'))
        e_name = ctk.CTkEntry(r, font=FONT); e_name.pack(side='left', fill='x', expand=True)
        e_name.insert(0, tr('new_pack_default_name'))
        r = makerow(tr('new_pack_version'))
        e_ver = ctk.CTkEntry(r, font=FONT); e_ver.pack(side='left', fill='x', expand=True)
        e_ver.insert(0, "1.0.0")
        r = makerow(tr('new_pack_format'))
        fmt = ctk.StringVar(value='modrinth')
        for txt, val in [(tr('fmt_modrinth'), 'modrinth'), (tr('fmt_curseforge'), 'curseforge')]:
            ctk.CTkRadioButton(r, text=txt, variable=fmt, value=val,
                               font=FONT_SM).pack(side='left', padx=8)
        mc_values = self.cache.mc_versions or ["1.20.1"]
        r = makerow(tr('info_mc'))
        c_mc = ctk.CTkComboBox(r, values=mc_values, font=FONT_SM)
        c_mc.pack(side='left', fill='x', expand=True); c_mc.set(mc_values[0])
        r = makerow(tr('info_loader'))
        c_lt = ctk.CTkComboBox(r, values=["Fabric", "Forge", "NeoForge"], font=FONT_SM)
        c_lt.pack(side='left', fill='x', expand=True); c_lt.set("Fabric")
        r = makerow(tr('info_loader_ver'))
        c_lv = ctk.CTkComboBox(r, values=list(self.cache.fabric_versions or []), font=FONT_SM)
        c_lv.pack(side='left', fill='x', expand=True)

        def fill_loader(_=None):
            # Fabric/Forge/NeoForge 均在线获取对应 MC 版本的加载器版本；
            # 取不到时下拉留空，组合框可手填
            mc_v = c_mc.get().strip()
            loader = c_lt.get()
            c_lv.set("...")
            def task():
                vs = self.api.fetch_loader_versions_for_mc(loader, mc_v)
                self.root.after(0, lambda: (c_lv.configure(values=vs),
                                            c_lv.set(vs[0] if vs else "")))
            self._thread(task)

        c_mc.configure(command=lambda _v: fill_loader())
        c_lt.configure(command=fill_loader)
        fill_loader()

        def create():
            name = e_name.get().strip() or tr('new_pack_default_name')
            ver = e_ver.get().strip() or "1.0.0"
            mc = c_mc.get().strip()
            lt = c_lt.get()
            lv = c_lv.get().strip()
            if not lv or lv == "...":  # 在线版本未返回时的占位符不可写进模板
                if lt == "Fabric":
                    lv = "0.15.11"
                else:
                    messagebox.showwarning(tr('dialog_title_tip'),tr('new_pack_loader_ver_required'))
                    return
            ftype = fmt.get()
            ext = ".mrpack" if ftype == "modrinth" else ".zip"
            label = "Modrinth Modpack" if ftype == "modrinth" else "CurseForge Modpack"
            path = filedialog.asksaveasfilename(defaultextension=ext,
                                                 filetypes=[(label, f"*{ext}"), ("All files", "*.*")],
                                                 initialfile=name + ext)
            if not path:
                return
            try:
                if ftype == "modrinth":
                    template = {"game": "minecraft", "formatVersion": 1, "versionId": ver,
                                "name": name, "summary": "", "files": [],
                                "dependencies": {"minecraft": mc,
                                                 LOADER_KEYS.get(lt, "fabric-loader"): lv}}
                    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as z:
                        z.writestr("modrinth.index.json",
                                   json.dumps(template, indent=2, ensure_ascii=False))
                else:
                    loader_key = LOADER_KEYS.get(lt, "fabric-loader")
                    prefix = "fabric" if loader_key == "fabric-loader" else (
                        "neoforge" if loader_key == "neoforge" else "forge")
                    manifest = {
                        "minecraft": {"version": mc,
                                      "modLoaders": [{"id": f"{prefix}-{lv}", "primary": True}]},
                        "manifestType": "minecraftModpack", "manifestVersion": 1,
                        "name": name, "version": ver, "files": [], "overrides": "overrides"}
                    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as z:
                        z.writestr("manifest.json",
                                   json.dumps(manifest, indent=2, ensure_ascii=False))
                self.log(tr('new_pack_created').format(path=path), "SUCCESS")
                win.destroy()
                self._open_pack_path(path)
            except Exception as e:
                messagebox.showerror(tr('dialog_title_error'),str(e))
        self._btn(fr, tr('new_pack_create'), create, 'success', width=180, side='top', padx=0)

    # ---------- CurseForge 格式导出 ----------
    def export_cf_zip(self):
        path = self._index_path_or_warn()
        if not path:
            return
        data = self._load_index(path)
        if data is None:
            return
        save_path = filedialog.asksaveasfilename(
            defaultextension=".zip", filetypes=[("Zip Archive", "*.zip")],
            initialfile=f"{data.get('name', 'modpack')}.zip")
        if not save_path:
            return
        include_overrides = messagebox.askyesno(tr('dialog_confirm_overrides'),
                                                tr('dialog_overrides_prompt'))
        overrides_dir = filedialog.askdirectory(title=tr('dlg_overrides_dir')) if include_overrides else None
        self.set_status(tr('status_loading'))

        def task():
            tmp_files = []
            try:
                base_dir = os.path.dirname(path)
                deps = data.get('dependencies', {})
                mod_loaders = []
                for key, prefix in (('fabric-loader', 'fabric'), ('forge', 'forge'),
                                    ('neoforge', 'neoforge')):
                    if deps.get(key):
                        mod_loaders.append({'id': f"{prefix}-{deps[key]}", 'primary': True})
                manifest = {'minecraft': {'version': deps.get('minecraft', ''),
                                          'modLoaders': mod_loaders},
                            'manifestType': 'minecraftModpack', 'manifestVersion': 1,
                            'name': data.get('name', 'modpack'),
                            'version': data.get('versionId', '1.0.0'),
                            'files': [], 'overrides': 'overrides'}
                extra = []
                cf_files = data.get('files', [])
                cf_total = len(cf_files)
                self.progress_show()
                for ei, e in enumerate(cf_files, 1):
                    self.progress_set(ei, cf_total)
                    cf = e.get('cf')
                    if cf:
                        manifest['files'].append({'projectID': cf.get('projectID'),
                                                  'fileID': cf.get('fileID'),
                                                  'required': cf.get('required', True)})
                        continue
                    rel = (e.get('path') or '').replace('\\', '/')
                    if not rel:
                        continue
                    src = os.path.join(base_dir, rel)
                    if os.path.exists(src):
                        extra.append((f"overrides/{rel}", src, False))
                    elif e.get('downloads'):
                        fn = os.path.basename(rel)
                        try:
                            self.root.after(0, lambda f=fn: self.log(tr('log_downloading').format(filename=f)))
                            with requests.get(e['downloads'][0], stream=True, timeout=STREAM_TIMEOUT) as resp:
                                resp.raise_for_status()
                                fd, tmp = tempfile.mkstemp(suffix=os.path.splitext(fn)[1])
                                os.close(fd)
                                with open(tmp, 'wb') as f:
                                    for chunk in resp.iter_content(8192):
                                        f.write(chunk)
                            tmp_files.append(tmp)
                            extra.append((f"overrides/{rel}", tmp, True))
                        except Exception as ex:
                            self.root.after(0, lambda f=fn, err=str(ex): self.log(
                                tr('log_download_fail').format(filename=f, error=err), "ERROR"))
                with zipfile.ZipFile(save_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                    zf.writestr('manifest.json', json.dumps(manifest, indent=2, ensure_ascii=False))
                    for zn, src, _ in extra:
                        zf.write(src, zn)
                    if overrides_dir and os.path.isdir(overrides_dir):
                        cnt = self._write_overrides_tree(zf, overrides_dir, 'curseforge')
                        self.root.after(0, lambda d=overrides_dir, n=cnt: self.log(
                                tr('log_ov_files_added').format(n=n, path=d), "SUCCESS"))
                self.root.after(0, lambda: self.log(tr('log_pack').format(path=save_path), "SUCCESS"))
                self.root.after(0, lambda: messagebox.showinfo(
                    tr('dialog_title_done'), tr('cf_export_ok').format(path=save_path)))
            except Exception as e:
                err = str(e)
                self.root.after(0, lambda: self.log(
                    tr('dialog_pack_fail').format(error=err), "ERROR"))
                self.root.after(0, lambda: messagebox.showerror(
                    tr('dialog_title_error'), tr('dialog_pack_fail').format(error=err)))
            finally:
                for tmp in tmp_files:
                    try:
                        os.remove(tmp)
                    except OSError:
                        pass
                self.progress_hide()
                self.root.after(0, lambda: self.set_status(tr('status_ready')))
        self._thread(task)

    def _after_open_mrpack(self, mrpack_path, index_path, cf_pending=None, is_cf=False, ov_counts=None):
        self.progress_hide()
        self.original_mrpack = mrpack_path
        self.cf_mode = is_cf
        self.pack_format = 'curseforge' if is_cf else 'modrinth'
        self._refresh_format_buttons()
        self.index_path.set(index_path)
        self.search_var.set("")   # 新包不沿用上一包的搜索词，避免打开即空状态
        self.set_status(tr('log_meta_loading'))
        self.root.update_idletasks()
        self.load_metadata(index_path)
        self.set_status(tr('log_list_refreshing'))
        self.root.update_idletasks()
        self.refresh_mod_list()
        self.set_status(tr('status_ready'))
        self.show_page('edit')
        if ov_counts:
            total, cli, srv = ov_counts
            if total:
                self.log(tr('log_ov_applied').format(n=total, c=cli), "SUCCESS")
            if srv:
                self.log(tr('log_ov_server').format(n=srv), "WARNING")
        if cf_pending:
            self.log(tr('log_cf_open').format(count=len(cf_pending)))
            self._thread(self._resolve_cf_entries, cf_pending,)
        messagebox.showinfo(tr('dialog_title_done'), tr('dialog_success_open').format(file=os.path.basename(mrpack_path)))

    def _parse_cf_manifest(self, extract_dir):
        """解析 extract_dir 下的 CurseForge manifest.json → (index_data, pending)，无效则抛异常"""
        manifest_path = os.path.join(extract_dir, "manifest.json")
        if not os.path.exists(manifest_path):
            raise Exception(tr('dialog_open_mrpack_fail'))
        try:
            with open(manifest_path, 'r', encoding='utf-8') as f:
                manifest = json.load(f)
        except Exception:
            raise Exception(tr('dialog_open_cf_fail'))
        if not isinstance(manifest, dict) or not manifest.get('minecraft'):
            raise Exception(tr('dialog_open_cf_fail'))
        index_data = cf_manifest_to_index(manifest)
        pending = [{'projectID': int(x.get('projectID', 0)),
                    'fileID': int(x.get('fileID', 0)),
                    'required': x.get('required', True)}
                   for x in manifest.get('files', [])]
        return index_data, pending

    def _resolve_cf_item(self, item):
        """解析单个 CF pending 项 → (entry, title, filename_found)"""
        proj = cf_get_project(item['projectID'])
        filename, filesize, title = None, 0, None
        if proj:
            title = proj.get('title')
            for fobj in proj.get('files', []):
                if fobj.get('id') == item['fileID']:
                    filename = fobj.get('name')
                    filesize = fobj.get('filesize', 0)
                    break
        found = bool(filename)
        if not filename:
            filename = f"cf-{item['fileID']}.jar"
        entry = {'path': f'mods/{filename}', 'hashes': {},
                 'downloads': [cf_cdn_url(item['fileID'], filename)],
                 'fileSize': filesize,
                 'cf': {'projectID': item['projectID'], 'fileID': item['fileID'],
                        'required': item['required']}}
        return entry, title, found

    def _resolve_cf_entries(self, pending):
        """后台解析 CurseForge projectID/fileID → 文件名 + forgecdn 直链。
        结果先攒在局部列表，全部完成后一次性写回：避免每条全量重写 index 的 O(N²) IO，
        也避免解析期间切换整合包时旧包条目混入新包"""
        total = len(pending)
        start_path = self.index_path.get().strip()
        resolved = []
        for i, item in enumerate(pending, 1):
            self.root.after(0, lambda c=i, t=total: self.set_status(
                tr('log_cf_resolving').format(done=c, total=t)))
            entry, title, found = self._resolve_cf_item(item)
            if not found:
                self.root.after(0, lambda pid=item['projectID']: self.log(
                    tr('log_cf_fail').format(pid=pid), "WARNING"))
            if title:
                self.cache.set_name(item['projectID'], title)
            resolved.append(dict(entry))
        self.root.after(0, lambda: self._commit_cf_entries(resolved, start_path))

    def _commit_cf_entries(self, resolved, start_path):
        cur_path = self.index_path.get().strip()
        if cur_path != start_path or not start_path or not os.path.exists(start_path):
            self.log(tr('log_cf_discarded'), "WARNING")
        else:
            try:
                with open(start_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                data.setdefault('files', []).extend(resolved)
                with open(start_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
            except Exception as e:
                self.log(tr('log_cf_resolve_fail').format(error=str(e)), "ERROR")
        self.set_status(tr('status_ready'))
        self.log(tr('log_cf_done'), "SUCCESS")
        self.refresh_mod_list()

    def _on_open_mrpack_error(self, err):
        self.progress_hide()
        self.log(tr('dialog_open_pack_fail').format(error=err), "ERROR")
        self.set_status(tr('status_ready'))
        messagebox.showerror(tr('dialog_title_error'), tr('dialog_open_pack_fail').format(error=err))

    def load_metadata(self, path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            name = data.get('name', '')
            mc = data.get('dependencies', {}).get('minecraft', '')
            self.entry_name.delete(0, 'end'); self.entry_name.insert(0, name)
            self.entry_version.delete(0, 'end'); self.entry_version.insert(0, data.get('versionId', ''))
            self.combo_mc.set(mc)
            deps = data.get('dependencies', {})
            loader_ver = None
            loader_name = "Fabric"
            for ln in ["Fabric", "Forge", "NeoForge"]:
                lk = LOADER_KEYS[ln]
                if lk in deps:
                    loader_name = ln
                    loader_ver = deps[lk]
                    break
            self.combo_loader_type.set(loader_name)
            if loader_ver:
                self.combo_loader_ver.set(str(loader_ver))
            self.check_loader_compatibility()
            self.log(tr('log_loaded_info').format(name=name, mc=mc, loader=loader_name, ver=loader_ver))
        except Exception as e:
            self.log(tr('dialog_parse_error').format(error=str(e)), "ERROR")
            messagebox.showerror(tr('dialog_title_error'),tr('dialog_parse_error').format(error=str(e)))

    def reload_metadata(self):
        path = self.index_path.get().strip()
        if path and os.path.exists(path):
            self.load_metadata(path)
            self.refresh_mod_list()
        else:
            messagebox.showerror(tr('dialog_title_error'),tr('dialog_file_not_found'))

    def manual_backup(self):
        path = self._index_path_or_warn()
        if not path:
            return
        backup = f"{path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        shutil.copy2(path, backup)
        self.log(tr('dialog_backup_success').format(path=backup), "SUCCESS")
        self.set_status(tr('status_backup'))

    # ---------- 模组列表（自绘） ----------
    def refresh_mod_list(self):
        path = self.index_path.get().strip()
        if not path or not os.path.exists(path):
            return
        self._render_generation += 1
        self._name_generation += 1
        self._hide_visible_rows()
        self._last_filter_result = None
        self._render_pending = False
        self.all_mod_entries = []
        name_entries = {}
        path_occurrences = {}
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            for entry in data.get('files', []):
                path_str = entry.get('path', '')
                filename = os.path.basename(path_str)
                version = extract_version(filename)
                project_id = None
                display_name = filename
                if entry.get('cf'):
                    # CurseForge 条目：显示名取自 cfwidget 项目标题缓存
                    display_name = self.cache.get_name(entry['cf'].get('projectID')) or filename
                else:
                    if downloads := entry.get('downloads', []):
                        if pid := parse_project_id_from_url(downloads[0]):
                            project_id = pid
                    if project_id:
                        display_name = self.cache.get_name(project_id) or filename
                etype = entry_type(entry)
                occurrence = path_occurrences.get(path_str, 0)
                path_occurrences[path_str] = occurrence + 1
                mod_entry = {'path': path_str, 'filename': filename, 'version': version,
                             'display_name': display_name, 'project_id': project_id,
                             'etype': etype, 'raw_entry': entry,
                             '_row_key': (path_str, occurrence)}
                self.all_mod_entries.append(mod_entry)
                if project_id and not self.cache.get_name(project_id):
                    name_entries.setdefault(project_id, []).append(mod_entry)
            self.apply_filter()
            if name_entries:
                self._fetch_mod_names(name_entries, self._name_generation)
            self.log(tr('log_refresh').format(count=len(self.all_mod_entries)), "SUCCESS")
        except Exception as e:
            self.log(tr('log_refresh_fail').format(error=str(e)), "ERROR")

    def _fetch_mod_names(self, project_entries, generation):
        def task():
            results = {}
            with ThreadPoolExecutor(max_workers=8) as executor:
                futures = {executor.submit(self.api.fetch_project_name, pid): pid
                           for pid in project_entries}
                for future in as_completed(futures):
                    pid = futures[future]
                    try:
                        results[pid] = future.result()
                    except Exception:
                        results[pid] = pid
            if self.root.winfo_exists():
                self.root.after(0, lambda: self._apply_mod_names(generation, results))
        self._thread(task)

    def _apply_mod_names(self, generation, results):
        if generation != self._name_generation or getattr(self, '_rebuilding', False):
            return
        for entry in self.all_mod_entries:
            if entry.get('project_id') in results:
                entry['display_name'] = results[entry['project_id']]
        self.apply_filter()

    def _debounce_filter(self):
        if self._filter_timer:
            self.root.after_cancel(self._filter_timer)
        self._filter_timer = self.root.after(300, self.apply_filter)

    def apply_filter(self):
        if getattr(self, '_rebuilding', False):
            return
        keyword = self.search_var.get().strip().lower()
        filtered = self.all_mod_entries if not keyword else [
            e for e in self.all_mod_entries if mod_match(e, keyword)]
        active_keys = {e['_row_key'] for e in self.all_mod_entries}
        for key in self._row_cache.keys() - active_keys:
            self._row_cache.pop(key).destroy()
        signature = [(e.get('path'), e.get('display_name')) for e in filtered]
        if getattr(self, '_empty_lb', None):
            self._empty_lb.destroy()
            self._empty_lb = None
        if not filtered and keyword:
            self._hide_visible_rows()
            self._render_generation += 1
            self._render_pending = False
            self._empty_lb = ctk.CTkLabel(self.tree, text=tr('search_no_result'),
                                          font=FONT_SM, height=60)
            self._empty_lb.pack(pady=24)
            self._last_filter_result = 'empty'
            return
        if self._last_filter_result == signature:
            return
        self._last_filter_result = signature
        self._hide_visible_rows()
        self._render_generation += 1
        generation = self._render_generation
        chunk_size = 32
        self._render_pending = bool(filtered)

        def render_chunk(start=0):
            if generation != self._render_generation or not self.tree.winfo_exists():
                return
            end = min(start + chunk_size, len(filtered))
            for idx in range(start, end):
                entry = filtered[idx]
                key = entry['_row_key']
                row = self._row_cache.get(key)
                if row is None or not row.winfo_exists():
                    row = self._create_mod_row(entry)
                    self._row_cache[key] = row
                self._update_mod_row(row, entry, idx)
                row.pack(fill='x', pady=0)
                self._rows.append(row)
            if end < len(filtered):
                self.root.after(8, lambda: render_chunk(end))
            else:
                self._render_pending = False

        render_chunk()

    def _hide_visible_rows(self):
        for row in self._rows:
            row.selected = False
            row.configure(fg_color=row._base_fg)
            row.pack_forget()
        self._rows = []

    def _create_mod_row(self, entry):
        row = ctk.CTkFrame(self.tree, fg_color="transparent", corner_radius=4, height=32)
        row.raw = entry
        row.selected = False
        row.labels = []
        row._base_fg = "transparent"

        def on_enter(_event, target=row):
            if not target.selected:
                target.configure(fg_color=C['row_hover'])

        def on_leave(_event, target=row):
            if not target.selected:
                target.configure(fg_color=target._base_fg)

        row.bind('<Enter>', on_enter)
        row.bind('<Leave>', on_leave)
        for width in self._col_widths:
            label = ctk.CTkLabel(row, text="", anchor='w', font=FONT_SM, width=width)
            label.pack(side='left', padx=4, pady=4)
            label.bind('<Double-Button-1>',
                       lambda event, target=row: self.show_mod_detail_row(target))
            label.bind('<Button-1>', lambda event, target=row: self._toggle_row(target))
            label.bind('<Enter>', on_enter)
            label.bind('<Leave>', on_leave)
            row.labels.append(label)
        row.bind('<Double-Button-1>',
                 lambda event, target=row: self.show_mod_detail_row(target))
        row.bind('<Button-1>', lambda event, target=row: self._toggle_row(target))
        return row

    def _update_mod_row(self, row, entry, index):
        row.raw = entry
        row._base_fg = C['zebra'] if index % 2 == 1 else "transparent"
        row.configure(fg_color=row._base_fg)
        type_labels = {'mod': tr('type_mod'), 'rp': tr('type_rp'), 'sp': tr('type_sp')}
        values = [entry.get('display_name', entry.get('filename', tr('unknown'))),
                  entry.get('filename', ''), entry.get('version', ''),
                  type_labels.get(entry.get('etype', 'mod'), '?'), entry.get('path', '')]
        for label, value in zip(row.labels, values):
            text = str(value)
            if label.cget('text') != text:
                label.configure(text=text)

    def delete_selected(self):
        selected_rows = [r for r in self._rows if getattr(r, 'selected', False)]
        if not selected_rows:
            messagebox.showinfo(tr('dialog_title_tip'),tr('dialog_select_mod'))
            return
        if not messagebox.askyesno(tr('dialog_title_tip'),
                                   tr('dialog_confirm_delete').format(count=len(selected_rows))):
            return
        path = self._index_path_or_warn()
        if not path:
            return
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            files = data.get('files', [])
            paths_to_delete = [r.raw['path'] for r in selected_rows]
            new_files = [f for f in files if f.get('path') not in paths_to_delete]
            if len(new_files) == len(files):
                messagebox.showinfo(tr('dialog_title_tip'), tr('log_delete_nomatch'))
                return
            data['files'] = new_files
            self._save_index(data)
            self.log(tr('log_delete_mod').format(count=len(files) - len(new_files)), "SUCCESS")
            self.refresh_mod_list()
            self.reload_metadata()
        except Exception as e:
            self.log(tr('log_delete_fail').format(error=str(e)), "ERROR")
            messagebox.showerror(tr('dialog_title_error'), tr('log_delete_fail').format(error=str(e)))

    def open_mods_folder(self):
        path = self.index_path.get().strip()
        if not path:
            messagebox.showinfo(tr('dialog_title_tip'), tr('dialog_open_index_first'))
            return
        base_dir = os.path.dirname(path)
        sub = entry_prefix(self.add_type.get())
        target = os.path.join(base_dir, sub)
        os.startfile(target if os.path.isdir(target) else base_dir)

    # ---------- 版本获取 ----------
    def fetch_mc_versions(self):
        self.log(tr('log_mc_fetching'))
        self.set_status(tr('status_loading'))
        def task():
            versions = self.api.fetch_mc_versions()
            if versions:
                self.root.after(0, lambda: self.combo_mc.configure(values=versions))
                # 保留当前已选 MC 版本（打开整合包后刷新不应覆盖包内版本）
                self.root.after(0, lambda: self.combo_mc.set(
                    current_mc if current_mc else versions[0]))
                self.root.after(0, lambda: self.log(tr('log_mc_fetched').format(count=len(versions)), "SUCCESS"))
                mc_ver = current_mc
                if mc_ver and mc_ver in versions:
                    self.root.after(0, lambda: self.update_loader_dropdown_for_mc(mc_ver))
            else:
                self.root.after(0, lambda: self.log(tr('log_mc_fetch_fail'), "ERROR"))
            self.root.after(0, lambda: self.set_status(tr('status_ready')))
        current_mc = self.combo_mc.get().strip()
        self._thread(task)

    def fetch_loader_versions(self, force_refresh=False):
        """按当前加载器获取版本表（Fabric 走 meta API，Forge/NeoForge 走各自源），
        避免把 Fabric 版本写进其他加载器的依赖"""
        loader_name = self.loader_var.get()
        self.log(tr('log_loader_fetching').format(loader=loader_name))
        self.set_status(tr('status_loading'))
        def task():
            mc_ver = current_mc
            if loader_name == 'Fabric':
                versions, _mc_map = self.api.fetch_fabric_versions(force_refresh=force_refresh)
                compatible = self.api.fetch_fabric_versions_for_mc(mc_ver, force_refresh=force_refresh) if mc_ver else []
                if not versions and not compatible:
                    self.root.after(0, lambda: self.log(tr('log_loader_fetch_fail').format(loader=loader_name), "ERROR"))
                    self.root.after(0, lambda: self.set_status(tr('status_ready')))
                    return
            else:
                versions = []
                compatible = self.api.fetch_loader_versions_for_mc(loader_name, mc_ver) if mc_ver else []
                if not compatible:
                    self.root.after(0, lambda: self.log(tr('log_loader_fetch_fail').format(loader=loader_name), "ERROR"))
                    self.root.after(0, lambda: self.set_status(tr('status_ready')))
                    return
            self.root.after(0, lambda: self._apply_loader_versions(versions, compatible, mc_ver))
        current_mc = self.combo_mc.get().strip()
        self._thread(task)

    def _apply_loader_versions(self, all_versions, compatible, mc_ver):
        loader_name = self.loader_var.get()
        self.set_status(tr('status_ready'))
        cur = self.combo_loader_ver.get().strip()
        if mc_ver and compatible:
            self.combo_loader_ver.configure(values=compatible)
            self.combo_loader_ver.set(cur if cur in compatible else compatible[0])
            self.log(tr('log_mc_compat').format(mc=mc_ver, count=len(compatible), loader=loader_name), "INFO")
        else:
            self.combo_loader_ver.configure(values=all_versions)
            self.combo_loader_ver.set(cur if cur in all_versions else (all_versions[0] if all_versions else ''))
            if mc_ver and not compatible:
                self.log(tr('log_mc_compat_none').format(mc=mc_ver, count=len(all_versions)), "WARNING")
            else:
                self.log(tr('log_loader_fetched').format(count=len(all_versions), loader=loader_name), "SUCCESS")
        self.check_loader_compatibility()

    def update_loader_dropdown_for_mc(self, mc_ver):
        """MC 版本变化后按当前加载器刷新版本下拉（不再硬编码 Fabric）"""
        loader_name = self.loader_var.get()
        def task():
            compatible = self.api.fetch_loader_versions_for_mc(loader_name, mc_ver)
            if not compatible:
                self.root.after(0, lambda: self.log(tr('log_loader_compat_none').format(mc=mc_ver, loader=loader_name), "WARNING"))
                return
            self.root.after(0, lambda: self.combo_loader_ver.configure(values=compatible))
            self.root.after(0, lambda: self.combo_loader_ver.set(compatible[0] if compatible else ""))
            self.root.after(0, lambda: self.check_loader_compatibility())
        self._thread(task)

    def check_loader_compatibility(self):
        mc_ver = self.combo_mc.get().strip()
        loader_name = self.loader_var.get()
        if not mc_ver or not loader_name:
            return
        def task():
            compatible = self.api.fetch_loader_versions_for_mc(loader_name, mc_ver)
            self.root.after(0, lambda: self._apply_compat(compatible, current_ver))
        current_ver = self.combo_loader_ver.get().strip()
        self._thread(task)

    def _apply_compat(self, compatible, current):
        if not compatible:
            key, color = 'compat_unknown', C['warning']
        elif not current:
            key, color = 'compat_unsupported', C['warning']
        elif current in compatible:
            key, color = 'compat_compatible', C['success']
        else:
            key, color = 'compat_incompatible', C['danger']
        self.compatibility_label.configure(text=tr(key), text_color=color)

    def fetch_versions_from_url(self):
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning(tr('dialog_title_tip'), tr('warn_need_url'))
            return
        project_id = self.parse_project_id(url)
        if not project_id:
            messagebox.showerror(tr('dialog_title_error'), tr('err_parse_pid'))
            return
        self.log(tr('log_fetch_versions').format(pid=project_id))
        self.set_status(tr('status_loading'))
        mc_ver = self.combo_mc.get().strip()
        loader_api = self._loader_api()
        sel_type = self.add_type.get()  # 主线程取值，避免跨线程访问 Tk 变量
        pack_path = self.index_path.get().strip()

        def task():
            # 先查项目类型：resourcepack/shader 不按 loader 过滤，且路径前缀不同
            meta = self.api.fetch_project_meta(project_id)
            ptype = (meta or {}).get('project_type', 'mod')
            add_type = project_type_to_add_type(ptype)
            if add_type == 'mod':
                add_type = sel_type
            use_loader = loader_api if add_type == 'mod' else None
            all_v = self.api.get_all_versions(project_id, mc_ver, use_loader)
            if not all_v:
                def no_versions():
                    if self.index_path.get().strip() == pack_path:
                        messagebox.showerror(tr('dialog_title_error'),tr('dialog_no_version'))
                        self.set_status(tr('status_ready'))
                self.root.after(0, no_versions)
                return
            default_v = [v for v in all_v if v.get('featured')] or all_v[:1]
            def show_picker():
                if self.index_path.get().strip() != pack_path:
                    self.log(tr('log_async_pack_changed'), "WARNING")
                    return
                if ptype != 'mod':
                    self.add_type.set(add_type)
                self.show_selector(default_v, all_v, project_id, mc_ver, use_loader,
                                   entry_prefix(add_type), pack_path)
                self.set_status(tr('status_ready'))
            self.root.after(0, show_picker)
        self._thread(task)

    def search_projects_to_add(self):
        initial_query = self.project_search_entry.get().strip()
        win = self._win(tr('search_project_title'), "760x600")
        top = ctk.CTkFrame(win, fg_color="transparent")
        top.pack(fill='x', padx=10, pady=10)
        entry = ctk.CTkEntry(top, font=FONT, placeholder_text=tr('search_project_placeholder'))
        entry.pack(side='left', fill='x', expand=True, padx=(0, 6))
        if initial_query:
            entry.insert(0, initial_query)
        results_box = ctk.CTkScrollableFrame(win, fg_color=C['zebra'], corner_radius=10)
        results_box.pack(fill='both', expand=True, padx=10, pady=5)
        status_lb = ctk.CTkLabel(win, text="", font=FONT_SM)
        status_lb.pack(pady=2)
        request_id = 0

        def populate(token, hits, error, add_type, pack_path):
            if token != request_id or not win.winfo_exists():
                return
            if self.index_path.get().strip() != pack_path:
                self.log(tr('log_async_pack_changed'), "WARNING")
                return
            for widget in results_box.winfo_children():
                widget.destroy()
            if error:
                status_lb.configure(text=tr('search_project_fail').format(error=error))
            elif not hits:
                status_lb.configure(text=tr('search_project_no_result'))
            else:
                status_lb.configure(text="")
                for hit in hits:
                    title = hit.get('title') or '?'
                    row = ctk.CTkFrame(results_box, fg_color="transparent", corner_radius=6)
                    row.pack(fill='x', pady=3, padx=4)
                    ctk.CTkLabel(row, text=title, font=FONT_BOLD, anchor='w').pack(
                        fill='x', padx=6, pady=(4, 0))
                    ctk.CTkLabel(row, text=tr('online_by').format(
                        author=hit.get('author') or '?', dl=hit.get('downloads', 0)),
                        font=FONT_SM, anchor='w',
                        text_color=('gray40', 'gray60')).pack(fill='x', padx=6)
                    desc = str(hit.get('description') or '')[:140]
                    if desc:
                        ctk.CTkLabel(row, text=desc, font=FONT_SM, anchor='w',
                                     text_color=('gray40', 'gray60')).pack(
                                         fill='x', padx=6, pady=(0, 2))
                    def pick(pid=hit.get('project_id'), selected_type=add_type,
                             expected_path=pack_path):
                        if not pid:
                            return
                        if self.index_path.get().strip() != expected_path:
                            self.log(tr('log_async_pack_changed'), "WARNING")
                            return
                        self.add_type.set(selected_type)
                        win.destroy()
                        self.url_entry.delete(0, 'end')
                        self.url_entry.insert(0, pid)
                        self.fetch_versions_from_url()
                    self._btn(row, tr('search_project_select'), pick, 'accent2',
                              width=140, side='left', padx=6)

        def do_search():
            nonlocal request_id
            query = entry.get().strip()
            if not query:
                return
            request_id += 1
            token = request_id
            add_type = self.add_type.get()
            pack_path = self.index_path.get().strip()
            mc_version = self.combo_mc.get().strip()
            loader_api = self._loader_api() if add_type == 'mod' else None
            status_lb.configure(text=tr('search_projecting'))
            for widget in results_box.winfo_children():
                widget.destroy()

            def task():
                try:
                    hits = self.api.search_projects(query, add_type, mc_version, loader_api)
                    error = None
                except Exception as exc:
                    hits, error = [], str(exc)
                self.root.after(0, lambda: populate(token, hits, error, add_type, pack_path))
            self._thread(task)

        self._btn(top, tr('search_project_btn'), do_search, 'accent2', width=120)
        entry.bind('<Return>', lambda e: do_search())
        entry.focus_set()
        if initial_query:
            do_search()

    def _fetch_versions_and_show(self, project_id, mc_ver, loader_api, on_ready, *extra):
        """后台获取项目版本；on_ready(default_v, all_v, project_id, mc_ver, loader_api, *extra)"""
        def task():
            all_v = self.api.get_all_versions(project_id, mc_ver, loader_api)
            if not all_v:
                self.root.after(0, lambda: messagebox.showerror(tr('dialog_title_error'),tr('dialog_no_version')))
                self.root.after(0, lambda: self.set_status(tr('status_ready')))
                return
            default_v = [v for v in all_v if v.get('featured')] or all_v[:1]
            self.root.after(0, lambda: on_ready(default_v, all_v, project_id, mc_ver, loader_api, *extra))
            self.root.after(0, lambda: self.set_status(tr('status_ready')))
        self._thread(task)

    def parse_project_id(self, url):
        # 与列表解析保持一致：支持 modrinth.com 页面链接、CDN 链接和裸项目 ID
        return parse_project_id_from_url(url)

    def show_selector(self, default_versions, all_versions, project_id, mc_ver, loader_api,
                      prefix='mods', expected_path=None):
        self._version_table(tr('selector_title').format(id=project_id), default_versions, all_versions,
                            mc_ver, loader_api,
                            lambda version: self.add_version(version, prefix, expected_path),
                            'button_cancel')

    def _version_table(self, title, default_versions, all_versions, mc_ver, loader_api,
                       on_pick, close_key='button_close'):
        """通用版本选择表格：标题、表格行、显示全部/推荐切换、选择此版本 + 关闭"""
        win = self._win(title, "1000x650")
        col_widths = [200, 200, 180, 140, 60]
        headers = [tr('col_version'), tr('col_game_version'), tr('col_loader'),
                   tr('col_date'), tr('col_recommended')]
        hdr = ctk.CTkFrame(win, fg_color=C['header'], corner_radius=10, height=40,
                           border_width=1, border_color=C['border'])
        hdr.pack(side='top', fill='x', padx=10, pady=(10, 4))
        hdr.pack_propagate(False)
        for i, h in enumerate(headers):
            ctk.CTkLabel(hdr, text=h, font=FONT_BOLD, anchor='w' if i < 4 else 'center',
                         width=col_widths[i], text_color=('gray30', '#e5e5e5')).pack(side='left', padx=4, pady=4)
        rows_ref = {'cur': None, 'all': []}
        scroll = ctk.CTkScrollableFrame(win, fg_color=C['zebra'], corner_radius=10)
        scroll.pack(side='top', fill='both', expand=True, padx=10, pady=5)

        def populate(vlist):
            for r in rows_ref['all']:
                r.destroy()
            rows_ref['all'] = []
            rows_ref['cur'] = None
            for v in vlist:
                row = ctk.CTkFrame(scroll, fg_color="transparent", corner_radius=4)
                row.version = v
                vals = [v.get('version_number', 'N/A'),
                        ', '.join(v.get('game_versions', [])),
                        ', '.join(v.get('loaders', [])),
                        v.get('date_published', '')[:10],
                        '⭐' if v.get('featured') else '']
                for i, val in enumerate(vals):
                    lb = ctk.CTkLabel(row, text=str(val), anchor='w' if i < 4 else 'center',
                                      font=FONT_SM, width=col_widths[i])
                    lb.pack(side='left', padx=4, pady=2)
                    lb.bind('<Button-1>', lambda e, r=row: select(r))
                row.bind('<Button-1>', lambda e, r=row: select(r))
                row.pack(fill='x', pady=1)
                rows_ref['all'].append(row)
            win.title(tr('selector_title_count').format(title=title, count=len(vlist)))

        def select(row):
            if rows_ref['cur']:
                rows_ref['cur'].configure(fg_color="transparent")
            rows_ref['cur'] = row
            row.configure(fg_color=C['accent'])

        def on_select():
            if not rows_ref['cur']:
                messagebox.showwarning(tr('dialog_title_tip'),tr('dialog_select_version'))
                return
            win.destroy()
            on_pick(rows_ref['cur'].version)

        def toggle():
            if getattr(toggle, 'state', 'default') == 'default':
                populate(all_versions)
                toggle.state = 'all'
                toggle_btn.configure(text=tr('button_show_recommended'))
            else:
                populate(default_versions)
                toggle.state = 'default'
                toggle_btn.configure(text=tr('button_show_all'))
        toggle.state = 'default'

        if mc_ver or loader_api:
            filter_txt = tr('selector_filter').format(mc=mc_ver) + (f" + {loader_api}" if loader_api else "")
            ctk.CTkLabel(win, text=filter_txt,
                        font=FONT_SM, text_color='gray60').pack(side='bottom', pady=(0, 2))
        bf = ctk.CTkFrame(win, fg_color="transparent")
        bf.pack(side='bottom', pady=(4, 10))
        self._btn(bf, tr('button_select_this'), on_select, 'success', width=120, padx=5)
        toggle_btn = self._btn(bf, tr('button_show_all'), toggle, 'accent2', width=140, padx=5)
        self._btn(bf, tr(close_key), win.destroy, 'gray', width=100, padx=5)
        populate(default_versions)

    def add_version(self, version_data, prefix='mods', expected_path=None):
        try:
            file_obj = version_data["files"][0]
            filename = file_obj['filename']
            if expected_path is not None and self.index_path.get().strip() != expected_path:
                self.log(tr('log_async_pack_changed'), "WARNING")
                return
            entry = build_mod_entry(version_data, prefix)
            path = self.index_path.get().strip()
            if path and os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    if any(fe.get("path") == entry["path"] for fe in json.load(f).get('files', [])):
                        if not messagebox.askyesno(tr('dialog_title_tip'),
                                                    tr('dialog_version_exists').format(filename=filename)):
                            self.log(tr('log_add_exists').format(filename=filename), "WARNING")
                            return
            if not self.add_entry_to_index(entry, force=True):
                return
            path = self.index_path.get().strip()
            deps = version_data.get('dependencies', [])
            if deps:
                dep_ids = [dep.get('project_id') for dep in deps if dep.get('project_id')]
                if dep_ids:
                    self.show_dependency_dialog(dep_ids, filename)
            def _dl_task(_entry=entry, _fn=filename, _path=path):
                if not self._download_single_mod(_entry, _fn, _path):
                    self.root.after(0, lambda: self._rollback_entry(_entry["path"], _path))
            self._thread(_dl_task)
        except Exception as e:
            self.log(tr('log_add_version_fail').format(error=str(e)), "ERROR")
            messagebox.showerror(tr('dialog_title_error'), tr('dialog_version_fetch').format(error=str(e)))

    def _download_single_mod(self, entry, filename, index_path=None):
        path = index_path or self.index_path.get().strip()
        if not path:
            return False
        # 按条目路径前缀落到 mods/resourcepacks/shaderpacks 目录
        dest = os.path.join(os.path.dirname(path), entry.get('path', f'mods/{filename}'))
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        if os.path.exists(dest):
            return True
        download_url = entry['downloads'][0] if entry.get('downloads') else ''
        if not download_url:
            self.root.after(0, lambda: self.log(tr('log_no_link').format(filename=filename), "WARNING"))
            return False
        try:
            with requests.get(download_url, stream=True, timeout=STREAM_TIMEOUT) as resp:
                resp.raise_for_status()
                with open(dest, 'wb') as f:
                    for chunk in resp.iter_content(chunk_size=8192):
                        f.write(chunk)
            expected_sha1 = entry.get('hashes', {}).get('sha1')
            if expected_sha1 and compute_sha1(dest) != expected_sha1:
                os.remove(dest)
                self.root.after(0, lambda: self.log(tr('log_sha1_fail').format(filename=filename), "ERROR"))
                return False
            return True
        except Exception as e:
            err = str(e)
            self.root.after(0, lambda: self.log(tr('log_dl_fail').format(filename=filename, error=err), "ERROR"))
            return False

    def _rollback_entry(self, entry_path, expected_path=None):
        if expected_path is not None and self.index_path.get().strip() != expected_path:
            self.log(tr('log_async_pack_changed'), "WARNING")
            return
        path = expected_path or self.index_path.get().strip()
        if not path or not os.path.exists(path):
            return
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            before = len(data.get('files', []))
            data['files'] = [e for e in data.get('files', []) if e.get('path') != entry_path]
            if len(data['files']) != before:
                self._save_index(data)
                self.log(tr('log_rolled_back').format(path=entry_path), "WARNING")
                self.refresh_mod_list()
        except Exception as e:
            self.log(tr('log_rollback_fail').format(error=str(e)), "ERROR")

    # ---------- 依赖补齐 ----------
    def show_dependency_dialog(self, dep_ids, filename):
        win = self._win(tr('dialog_dep_prompt').format(filename=filename), "700x500")
        ctk.CTkLabel(win, text=tr('dialog_dep_prompt').format(filename=filename),
                     font=FONT_BOLD).pack(side='top', pady=10)
        path = self.index_path.get().strip()
        pack_path = path
        installed_ids = set()
        if path and os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    for entry in json.load(f).get('files', []):
                        for dl in entry.get('downloads', ['']):
                            if pid := parse_project_id_from_url(dl):
                                installed_ids.add(pid)
                                break
            except Exception:
                pass
        dep_status = []
        rows, labels = [], []

        cur = {'i': None}
        def select_dep(i):
            if cur['i'] is not None:
                rows[cur['i']].configure(fg_color="transparent")
            cur['i'] = i
            rows[i].configure(fg_color=C['accent'])

        def open_selected():
            if cur['i'] is None:
                messagebox.showinfo(tr('dialog_title_tip'), tr('dep_select_first'))
                return
            dep_id = dep_status[cur['i']][1]
            webbrowser.open(f"https://modrinth.com/mod/{dep_id}")

        def open_all():
            for _, dep_id, _ in dep_status:
                webbrowser.open(f"https://modrinth.com/mod/{dep_id}")

        def install_missing():
            missing = [(name, dep_id) for name, dep_id, installed in dep_status if not installed]
            if not missing:
                messagebox.showinfo(tr('dialog_title_tip'),tr('dialog_dep_no_missing'))
                return
            if not messagebox.askyesno(tr('dialog_title_tip'), tr('dialog_dep_confirm')):
                return
            mc_ver = self.combo_mc.get().strip()
            loader_api = self._loader_api()
            self.set_status(tr('status_loading'))
            dep_total = len(missing)
            self.progress_show()
            def task():
                # 仅网络请求在工作线程执行，避免冻结 UI
                fetched = []
                for di, (name, dep_id) in enumerate(missing, 1):
                    self.progress_set(di, dep_total)
                    self.root.after(0, lambda n=name: self.log(tr('log_dep_fetch').format(name=n)))
                    try:
                        latest = self.api.get_latest_version(dep_id, mc_ver, loader_api)
                        if not latest:
                            self.root.after(0, lambda n=name: self.log(
                                tr('dialog_dep_fetch_fail').format(name=n), "WARNING"))
                            continue
                        entry = build_mod_entry(latest, 'mods')
                        fetched.append((name, entry, latest['files'][0]['filename']))
                    except Exception as e:
                        self.root.after(0, lambda n=name, err=e: self.log(
                            tr('log_dep_add_fail').format(name=n, error=str(err)), "ERROR"))
                self.root.after(0, lambda: apply_installs(fetched))
            self._thread(task)

        def apply_installs(fetched):
            self.progress_hide()
            if self.index_path.get().strip() != pack_path:
                self.log(tr('log_async_pack_changed'), "WARNING")
                self.set_status(tr('status_ready'))
                return
            success_count = 0
            for name, entry, fn in fetched:
                path = self.index_path.get().strip()
                if path and os.path.exists(path):
                    with open(path, 'r', encoding='utf-8') as f:
                        if any(fe.get("path") == entry["path"] for fe in json.load(f).get('files', [])):
                            self.log(tr('log_dep_exists').format(name=name), "WARNING")
                            continue
                if self.add_entry_to_index(entry):
                    success_count += 1
                    self.log(tr('log_dep_added').format(name=name), "SUCCESS")

                    def _dep_dl(_e=entry, _fn=fn, _path=pack_path):
                        self._download_single_mod(_e, _fn, _path)
                    self._thread(_dep_dl)
            if success_count > 0:
                messagebox.showinfo(tr('dialog_title_done'),
                                    tr('dialog_dep_add_success').format(count=success_count))
                self.refresh_mod_list()
                win.destroy()
            else:
                messagebox.showerror(tr('dialog_title_error'), tr('dep_none_added'))
            self.set_status(tr('status_ready'))

        bf = ctk.CTkFrame(win, fg_color="transparent")
        bf.pack(side='bottom', pady=10)
        self._btn(bf, tr('button_open_selected'), open_selected, 'accent', width=120, padx=5)
        self._btn(bf, tr('button_open_all'), open_all, 'accent2', width=100, padx=5)
        self._btn(bf, tr('button_install_missing'), install_missing, 'success', width=120, padx=5)
        self._btn(bf, tr('button_close'), win.destroy, 'gray', width=80, padx=5)

        scroll = ctk.CTkScrollableFrame(win, fg_color=C['zebra'], corner_radius=10)
        scroll.pack(side='top', fill='both', expand=True, padx=10, pady=5)

        for dep_id in dep_ids:
            installed = dep_id in installed_ids
            dep_status.append((dep_id, dep_id, installed))
            row = ctk.CTkFrame(scroll, fg_color="transparent", corner_radius=4)
            txt = tr('dep_loading').format(id=dep_id) + (tr('dialog_dep_existing') if installed else tr('dialog_dep_missing'))
            lb = ctk.CTkLabel(row, text=txt, anchor='w', font=FONT_SM,
                              text_color=('gray20', 'gray80') if installed else C['warning'])
            lb.pack(fill='x', padx=4, pady=2)
            row.bind('<Button-1>', lambda e, i=len(rows): select_dep(i))
            lb.bind('<Button-1>', lambda e, i=len(rows): select_dep(i))
            row.pack(fill='x', pady=1)
            rows.append(row)
            labels.append(lb)

        def fetch_names():
            with ThreadPoolExecutor(max_workers=8) as ex:
                futs = {ex.submit(self.api.fetch_project_name, dep_status[i][1]): i
                        for i in range(len(dep_status))}
                for fut in as_completed(futs):
                    i = futs[fut]
                    try:
                        name = fut.result()
                        dep_status[i] = (name, dep_status[i][1], dep_status[i][2])
                        installed = dep_status[i][2]
                        txt = f"{name} ({dep_status[i][1]}) " + (tr('dialog_dep_existing') if installed else tr('dialog_dep_missing'))
                        self.root.after(0, lambda t=txt, lb=labels[i]: lb.winfo_exists() and lb.configure(text=t))
                    except Exception:
                        pass
        self._thread(fetch_names)

    # ---------- 导出/导入模组列表 ----------
    def export_mod_list(self):
        if not self.all_mod_entries:
            messagebox.showinfo(tr('dialog_title_tip'),tr('dialog_no_mods'))
            return
        path = filedialog.asksaveasfilename(defaultextension=".csv",
                                            filetypes=[("CSV files", "*.csv")],
                                            initialfile="modlist.csv")
        if path:
            try:
                with open(path, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(['Display Name', 'Project ID', 'Filename', 'Version', 'Path'])
                    for mod in self.all_mod_entries:
                        writer.writerow([mod.get('display_name', ''), mod.get('project_id', ''),
                                         mod.get('filename', ''), mod.get('version', ''), mod.get('path', '')])
                self.log(tr('log_export').format(path=path), "SUCCESS")
                messagebox.showinfo(tr('dialog_title_done'), tr('dialog_export_success').format(path=path))
            except Exception as e:
                messagebox.showerror(tr('dialog_title_error'), str(e))

    def import_mod_list(self):
        index_path = self.index_path.get().strip()
        if not index_path or not os.path.exists(index_path):
            messagebox.showerror(tr('dialog_title_error'),tr('dialog_file_not_found'))
            return
        csv_path = filedialog.askopenfilename(title=tr('dialog_import_select'),
                                              filetypes=[("CSV files", "*.csv")])
        if not csv_path:
            return
        self.log(tr('log_csv_import_start').format(path=csv_path))
        self.set_status(tr('status_loading'))
        self.progress_show()
        mc_ver = self.combo_mc.get().strip()
        loader_api = self._loader_api()
        def task():
            new_entries = []
            try:
                with open(csv_path, 'r', encoding='utf-8') as f:
                    rows = list(csv.DictReader(f))
            except Exception as e:
                err = str(e)
                self.root.after(0, lambda: messagebox.showerror(
                    tr('dialog_import_fail'), tr('dialog_import_fail').format(error=err)))
                self.root.after(0, lambda: self.set_status(tr('status_ready')))
                self.progress_hide()
                return
            total = len(rows)
            for i, row in enumerate(rows, 1):
                pid = (row.get('Project ID') or row.get('project_id') or '').strip()
                if not pid:
                    continue
                csv_path_value = (row.get('Path') or row.get('path') or '').replace('\\', '/')
                prefix = entry_prefix(entry_type({'path': csv_path_value}))
                use_loader = loader_api if prefix == 'mods' else None
                self.root.after(0, lambda cur=i, t=total: self.set_status(tr('csv_importing').format(i=cur, count=t)))
                self.progress_set(i, total)
                try:
                    latest = self.api.get_latest_version(pid, mc_ver, use_loader)
                except Exception:
                    latest = None
                if not latest:
                    self.root.after(0, lambda p=pid: self.log(tr('log_no_compat_version').format(pid=p), "WARNING"))
                    continue
                try:
                    entry = build_mod_entry(latest, prefix)
                except Exception:
                    self.root.after(0, lambda p=pid: self.log(tr('log_version_data_bad').format(pid=p), "WARNING"))
                    continue
                if not any(e.get("path") == entry["path"] for e in new_entries):
                    new_entries.append(entry)

            def apply_import():
                self.progress_hide()
                added = 0
                if self.index_path.get().strip() != index_path:
                    self.log(tr('log_async_pack_changed'), "WARNING")
                    self.set_status(tr('status_ready'))
                    return
                try:
                    with open(index_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    existing_paths = {fe.get("path") for fe in data.get('files', [])}
                    to_add = [e for e in new_entries if e["path"] not in existing_paths]
                    if to_add:
                        self.manual_backup()
                        data.setdefault('files', []).extend(to_add)
                        self._save_index(data)
                        added = len(to_add)
                        self.log(tr('log_import').format(path=csv_path, count=added), "SUCCESS")

                        def _dl_all(entries, target_path=index_path):
                            for e in entries:
                                fn = os.path.basename(e["path"])
                                if not self._download_single_mod(e, fn, target_path):
                                    self.root.after(0, lambda ep=e["path"], p=target_path:
                                                    self._rollback_entry(ep, p))
                        self._thread(_dl_all, to_add,)
                    self.refresh_mod_list()
                    messagebox.showinfo(tr('dialog_title_done'),
                                        tr('dialog_import_success').format(count=added))
                    self.set_status(tr('status_ready'))
                except Exception as e:
                    self.log(tr('log_import_write_fail').format(error=str(e)), "ERROR")
                    messagebox.showerror(tr('dialog_title_error'),
                                         tr('dialog_import_fail').format(error=str(e)))
                    self.set_status(tr('status_ready'))
            self.root.after(0, apply_import)
        self._thread(task)

    # ---------- 添加本地 JAR ----------
    def add_local_jar(self):
        filepath = filedialog.askopenfilename(title=tr('dialog_local_jar_prompt'),
                                              filetypes=[(tr('ft_jar'), "*.jar *.zip")])
        if not filepath:
            return
        filename = os.path.basename(filepath)
        path = self._index_path_or_warn()
        if not path:
            return
        # 按当前类型选择器决定目录前缀；哈希命中后若项目类型不同再修正
        prefix = entry_prefix(self.add_type.get())
        self.set_status(tr('status_loading'))
        def task():
            sha1 = compute_sha1(filepath)
            latest = api_lookup_version_by_hash(sha1)
            meta = None
            if latest:
                try:
                    meta = self.api.fetch_project_meta(latest.get('project_id', ''))
                except Exception:
                    meta = None
            self.root.after(0, lambda: self._after_jar_lookup(
                filepath, filename, path, sha1, latest, meta, prefix))
        self._thread(task)

    def _after_jar_lookup(self, filepath, filename, path, sha1, latest, meta=None, prefix='mods'):
        if self.index_path.get().strip() != path:
            self.log(tr('log_async_pack_changed'), "WARNING")
            return
        self.set_status(tr('status_ready'))
        if latest:
            if meta and meta.get('project_type', 'mod') != 'mod':
                at = project_type_to_add_type(meta['project_type'])
                prefix = entry_prefix(at)
                self.add_type.set(at)
            entry = build_mod_entry(latest, prefix)
            self.log(tr('log_jar_identified').format(
                filename=filename,
                project=latest.get('project_id', '?'),
                version=latest.get('version_number', '?')), "SUCCESS")
            if self.add_entry_to_index(entry):
                self.refresh_mod_list()
            return
        self.log(tr('log_jar_unknown').format(filename=filename), "WARNING")
        project_id = simpledialog.askstring(tr('dialog_local_jar_title'), tr('dialog_local_jar_id'))
        prefix = entry_prefix(self.add_type.get())
        dest_dir = os.path.join(os.path.dirname(path), prefix)
        os.makedirs(dest_dir, exist_ok=True)
        dest = os.path.join(dest_dir, filename)
        shutil.copy2(filepath, dest)
        entry = {
            "path": f"{prefix}/{filename}",
            "hashes": {"sha1": sha1, "sha512": compute_sha512(dest)},
            "downloads": [], "fileSize": os.path.getsize(dest)
        }
        if project_id:
            entry['project_id'] = project_id
        if self.add_entry_to_index(entry):
            self.log(tr('log_local_jar').format(filename=filename), "SUCCESS")
            self.refresh_mod_list()

    # ---------- 整合包对比 ----------
    def compare_packs(self):
        path_a = filedialog.askopenfilename(title=tr('dialog_diff_pick_a'),
                                            filetypes=[("Modpack", "*.mrpack *.zip")])
        if not path_a:
            return
        path_b = filedialog.askopenfilename(title=tr('dialog_diff_pick_b'),
                                            filetypes=[("Modpack", "*.mrpack *.zip")])
        if not path_b:
            return
        self.set_status(tr('status_loading'))
        self.progress_show(indeterminate=True)
        def task():
            try:
                data_a = self._load_pack_data_from_file(path_a)
                data_b = self._load_pack_data_from_file(path_b)
                only_a, only_b, changed = diff_pack_files(data_a['files'], data_b['files'])
                self.root.after(0, lambda: self._show_diff_result(
                    data_a, data_b, only_a, only_b, changed))
            except Exception as e:
                err = str(e)
                self.root.after(0, lambda: self.log(tr('log_compare_fail').format(error=err), "ERROR"))
                self.root.after(0, lambda: messagebox.showerror(tr('dialog_title_error'), tr('log_compare_fail').format(error=err)))
            finally:
                self.progress_hide()
                self.root.after(0, lambda: self.set_status(tr('status_ready')))
        self._thread(task)

    def _load_pack_data_from_file(self, filepath):
        """解析 .mrpack/.zip → {'name','versionId','files'}（独立于当前打开状态，含 CF 解析）"""
        extract_dir = tempfile.mkdtemp(prefix="mwdiff_")
        try:
            with zipfile.ZipFile(filepath, 'r') as zipf:
                zipf.extractall(extract_dir)
            index_path = os.path.join(extract_dir, "modrinth.index.json")
            if os.path.exists(index_path):
                with open(index_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            else:
                data, pending = self._parse_cf_manifest(extract_dir)
                data['files'] = [self._resolve_cf_item(item)[0] for item in pending]
            return {'name': data.get('name') or os.path.basename(filepath),
                    'versionId': data.get('versionId', ''),
                    'files': data.get('files', [])}
        finally:
            shutil.rmtree(extract_dir, ignore_errors=True)

    def _text_popup(self, title, geometry, text, header=None):
        """通用文本弹窗：标题 + 可选头部标签 + 只读文本框 + 关闭按钮"""
        win = self._win(title, geometry)
        if header:
            ctk.CTkLabel(win, text=header, font=FONT_MD_BOLD).pack(pady=6)
        tb = ctk.CTkTextbox(win, font=FONT_SM)
        tb.pack(fill='both', expand=True, padx=10, pady=(0, 10))
        tb.insert('1.0', text)
        tb.configure(state='disabled')
        self._btn(win, tr('button_close'), win.destroy, 'gray', width=100, padx=0)
        return win

    def _show_diff_result(self, data_a, data_b, only_a, only_b, changed):
        fname = lambda e: os.path.basename(e.get('path', '')) or '(?)'
        fver = lambda e: extract_version(os.path.basename(e.get('path', '')))
        lines = []
        if not only_a and not only_b and not changed:
            lines.append(tr('diff_same'))
        if only_a:
            lines.append(tr('diff_only').format(name=f"{data_a['name']} (A)", count=len(only_a)))
            lines.extend(f"  - {fname(e)}  [{fver(e)}]" for _, e in only_a)
            lines.append("")
        if changed:
            lines.append(tr('diff_changed').format(count=len(changed)))
            lines.extend(f"  ~ {fname(ea)}: {fver(ea)} → {fver(eb)}" for _, ea, eb in changed)
            lines.append("")
        if only_b:
            lines.append(tr('diff_only').format(name=f"{data_b['name']} (B)", count=len(only_b)))
            lines.extend(f"  + {fname(e)}  [{fver(e)}]" for _, e in only_b)
        self._text_popup(tr('diff_title'), "640x560", "\n".join(lines),
                         header=f"A: {data_a['name']}  ⇄  B: {data_b['name']}")

    # ---------- 模组详情 ----------
    def show_mod_detail_row(self, row):
        mod = row.raw
        project_id = mod.get('project_id')
        name = mod.get('display_name', tr('unknown'))
        self.log(tr('log_detail_view').format(name=name))
        win = self._win(tr('dialog_detail_title'), "500x400")
        ctk.CTkLabel(win, text=f"{tr('col_name')}: {name}", font=FONT_BOLD).pack(pady=5)
        ctk.CTkLabel(win, text=f"{tr('col_filename')}: {mod['filename']}", anchor='w').pack(fill='x', padx=20)
        ctk.CTkLabel(win, text=f"{tr('col_version')}: {mod['version']}", anchor='w').pack(fill='x', padx=20)
        ctk.CTkLabel(win, text=f"{tr('col_path')}: {mod['path']}", anchor='w').pack(fill='x', padx=20)
        cf = (mod.get('raw_entry') or {}).get('cf')
        if cf:
            # CurseForge 条目：从 cfwidget 获取项目信息
            ctk.CTkLabel(win, text=f"{tr('col_project_id')}: CF-{cf.get('projectID')}",
                         anchor='w').pack(fill='x', padx=20)
            loading = ctk.CTkLabel(win, text=tr('detail_loading'))
            loading.pack(pady=5)
            def fetch_cf_detail(cf=cf):
                proj = cf_get_project(cf.get('projectID'))
                if proj:
                    win.after(0, lambda p=proj: self._update_cf_detail(win, loading, p))
            self._thread(fetch_cf_detail)
        elif project_id:
            ctk.CTkLabel(win, text=f"{tr('col_project_id')}: {project_id}", anchor='w').pack(fill='x', padx=20)
            def fetch_detail():
                try:
                    resp = requests.get(f"https://api.modrinth.com/v2/project/{project_id}", timeout=5)
                    if resp.status_code == 200:
                        data = resp.json()
                        try:
                            mresp = requests.get(
                                f"https://api.modrinth.com/v2/project/{project_id}/members", timeout=5)
                            if mresp.status_code == 200:
                                data['_authors'] = ", ".join(
                                    m.get('user', {}).get('username', '?') for m in mresp.json())
                        except Exception:
                            pass
                        win.after(0, lambda: self._update_detail(win, data))
                except Exception:
                    pass
            self._thread(fetch_detail)
            loading = ctk.CTkLabel(win, text=tr('detail_loading'))
            loading.pack(pady=5)
        else:
            ctk.CTkLabel(win, text=tr('dialog_detail_no_id'), text_color=C['warning']).pack(pady=5)
        self._btn(win, tr('button_close'), win.destroy, 'gray', width=100, padx=0)

    def _update_cf_detail(self, win, loading, proj):
        try:
            loading.destroy()
        except Exception:
            pass
        text = tr('detail_cf_info').format(
            title=proj.get('title', 'N/A'), desc=str(proj.get('summary', 'N/A'))[:200],
            downloads=proj.get('downloads', 0))
        ctk.CTkLabel(win, text=text, justify='left', font=FONT_SM, anchor='w').pack(
            fill='x', pady=5, padx=20)

    def _update_detail(self, win, data):
        for widget in win.winfo_children():
            if isinstance(widget, ctk.CTkLabel) and widget.cget('text') == tr('detail_loading'):
                widget.destroy()
        text = tr('detail_mr_info').format(
            title=data.get('title', 'N/A'), author=data.get('_authors', 'N/A'),
            desc=str(data.get('description', 'N/A'))[:200], downloads=data.get('downloads', 0),
            updated=str(data.get('updated', 'N/A'))[:10])
        ctk.CTkLabel(win, text=text, justify='left', font=FONT_SM, anchor='w').pack(
            fill='x', pady=5, padx=20)

    # ---------- 检查更新 ----------
    def check_updates(self):
        if not messagebox.askyesno(tr('dialog_title_tip'),
                                   tr('dialog_update_experimental'), icon='warning'):
            self.log(tr('log_update_cancel'), "WARNING")
            return
        path = self._index_path_or_warn()
        if not path:
            return
        data = self._load_index(path)
        if data is None:
            return
        files = data.get('files', [])
        if not files:
            messagebox.showinfo(tr('dialog_title_tip'), tr('update_no_mods'))
            return
        mc_ver = self.combo_mc.get().strip()
        loader_api = self._loader_api()
        mods_to_check = []
        for entry in files:
            etype = entry_type(entry)
            if entry.get('cf'):
                # CurseForge 条目：按 fileID 比较（cfwidget）
                mods_to_check.append({'cf': True, 'entry': entry, 'etype': etype,
                                       'filename': os.path.basename(entry.get('path', ''))})
                continue
            project_id = parse_project_id_from_url(entry.get('downloads', [''])[0]) if entry.get('downloads') else None
            if project_id:
                mods_to_check.append({'project_id': project_id, 'entry': entry,
                                       'filename': os.path.basename(entry.get('path', '')),
                                       'etype': etype})
        if not mods_to_check:
            self.log(tr('log_update_no_pid'), "WARNING")
            messagebox.showinfo(tr('dialog_title_tip'), tr('update_no_pid'))
            return
        self.log(tr('log_update_start'))
        self.set_status(tr('status_checking'))
        self.progress_show()
        total = len(mods_to_check)
        def task():
            updates, completed = [], 0
            with ThreadPoolExecutor(max_workers=20) as executor:
                future_to_mod = {executor.submit(
                    self._check_single_mod, m, mc_ver,
                    loader_api if m.get('etype', 'mod') == 'mod' else None): m
                    for m in mods_to_check}
                for future in as_completed(future_to_mod):
                    completed += 1
                    self.root.after(0, lambda c=completed, t=total: self.set_status(
                        f"{tr('status_checking')}... {c}/{t}"))
                    self.progress_set(completed, total)
                    if result := future.result():
                        updates.append(result)
            self.root.after(0, lambda u=updates, p=path: self._on_check_updates_done(u, p))
        self._thread(task)

    def _on_check_updates_done(self, updates, expected_path=None):
        if expected_path is not None and self.index_path.get().strip() != expected_path:
            self.log(tr('log_async_pack_changed'), "WARNING")
            return
        self.progress_hide()
        self.set_status(tr('status_ready'))
        if not updates:
            messagebox.showinfo(tr('dialog_no_update'), tr('dialog_no_update'))
            self.log(tr('log_update_done'), "SUCCESS")
            return
        self.show_update_dialog(updates, expected_path)

    def _check_single_mod(self, mod_info, mc_ver, loader_api):
        if mod_info.get('cf'):
            return self._check_single_cf_mod(mod_info, mc_ver, loader_api)
        project_id = mod_info['project_id']
        entry = mod_info['entry']
        filename = mod_info['filename']
        try:
            latest = self.api.get_latest_version(project_id, mc_ver, loader_api)
            if not latest:
                return None
            current_ver = extract_version(filename)
            latest_ver = latest.get('version_number', '')
            if current_ver == tr('ver_unknown') or not latest_ver:
                return None
            current_url = (entry.get('downloads') or [''])[0]
            latest_url = ''
            if latest.get('files'):
                latest_url = latest['files'][0].get('url', '')
            if current_url and latest_url and current_url == latest_url:
                return None
            if _compare_simple(latest_ver, current_ver) > 0:
                name = self.api.fetch_project_name(project_id)
                norm_current = _normalize_version(current_ver)
                norm_latest = _normalize_version(latest_ver)
                return {'project_id': project_id, 'name': name, 'current_ver': norm_current,
                        'latest_ver': norm_latest, 'current_entry': entry, 'latest_data': latest}
        except Exception:
            pass
        return None

    def _check_single_cf_mod(self, mod_info, mc_ver, loader=None):
        entry = mod_info['entry']
        cf = entry.get('cf') or {}
        pid = cf.get('projectID')
        current_fid = cf.get('fileID', 0)
        try:
            versions = cf_get_project_versions(pid, mc_ver=mc_ver, loader=loader)
            if not versions:
                return None
            cands = [v for v in versions if v['file_id'] > current_fid]
            if not cands:
                return None
            latest = max(cands, key=lambda v: v['file_id'])
            current_ver = extract_version(mod_info['filename'])
            latest_ver = extract_version(latest['name'])
            name = self.cache.get_name(pid) or mod_info['filename']
            return {'cf': True, 'project_id': pid, 'name': name,
                    'current_ver': current_ver,
                    'latest_ver': latest_ver if latest_ver != tr('ver_unknown') else f"fileID {latest['file_id']}",
                    'current_entry': entry,
                    'latest_data': {'cfProjectID': pid, 'cfFileID': latest['file_id'],
                                    'filename': latest['name'], 'filesize': latest['filesize']}}
        except Exception as e:
            msg = tr('log_cf_check_fail').format(pid=pid, error=str(e))
            self.root.after(0, lambda: self.log(msg, "WARNING"))
        return None

    def show_update_dialog(self, updates, expected_path=None):
        win = self._win(tr('dialog_update_found').format(count=len(updates)), "800x520")
        ctk.CTkLabel(win, text=tr('dialog_update_found').format(count=len(updates)),
                     font=FONT_MD_BOLD).pack(side='top', pady=10)
        ctk.CTkLabel(win, text=tr('dialog_update_warning'),
                     font=FONT_ITALIC, text_color=C['warning']).pack(side='top', pady=2)
        headers = [tr('column_mod_name'), tr('column_current_ver'),
                   tr('column_latest_ver'), tr('column_action'), '']
        col_widths = [240, 150, 150, 64, 46]
        hdr = ctk.CTkFrame(win, fg_color=C['header'], corner_radius=10, height=40,
                           border_width=1, border_color=C['border'])
        hdr.pack(side='top', fill='x', padx=10, pady=(10, 4))
        hdr.pack_propagate(False)
        for i, h in enumerate(headers):
            ctk.CTkLabel(hdr, text=h, font=FONT_BOLD, anchor='w' if i < 3 else 'center',
                         width=col_widths[i], text_color=('gray30', '#e5e5e5')).pack(side='left', padx=4, pady=4)

        count_var = ctk.StringVar(value=tr('update_selected').format(n=0, total=len(updates)))

        def refresh_count():
            count_var.set(tr('update_selected').format(
                n=sum(1 for r in rows if r.selected), total=len(updates)))

        def toggle(row):
            row.selected = not row.selected
            row.configure(fg_color=C['accent'] if row.selected else "transparent")
            children = [c for c in row.winfo_children() if isinstance(c, ctk.CTkLabel)]
            if len(children) >= 4:
                children[3].configure(text=tr('update_action') if row.selected else "")
            refresh_count()

        def select_all_toggle():
            target = not all(r.selected for r in rows)
            for r in rows:
                r.selected = target
                r.configure(fg_color=C['accent'] if target else "transparent")
                children = [c for c in r.winfo_children() if isinstance(c, ctk.CTkLabel)]
                if len(children) >= 4:
                    children[3].configure(text=tr('update_action') if target else "")
            refresh_count()

        def apply_updates():
            to_update = [r for r in rows if r.selected]
            if not to_update:
                messagebox.showinfo(tr('dialog_title_tip'), tr('dialog_update_select'))
                return
            if not messagebox.askyesno(tr('dialog_title_tip'),
                                       tr('dialog_update_apply').format(count=len(to_update))):
                return
            if expected_path is not None and self.index_path.get().strip() != expected_path:
                self.log(tr('log_async_pack_changed'), "WARNING")
                win.destroy()
                return
            if any(r.upd.get('cf') for r in to_update):
                # CurseForge 更新需下载新文件计算哈希，放入后台线程避免冻结 UI
                self._apply_cf_updates(to_update, win, expected_path)
                return
            built = [(r.upd['current_entry'].get('path'),
                      build_mod_entry(
                          r.upd['latest_data'],
                          (r.upd['current_entry'].get('path') or 'mods/').split('/')[0]))
                     for r in to_update]
            self._replace_entries(built, win, expected_path)

        ctk.CTkLabel(win, textvariable=count_var, font=FONT_BOLD,
                     text_color=C['accent']).pack(side='bottom', pady=(4, 4))
        bf = ctk.CTkFrame(win, fg_color="transparent")
        bf.pack(side='bottom', pady=(4, 10))
        self._btn(bf, tr('button_select_all'), select_all_toggle, 'accent2', width=140, padx=5)
        self._btn(bf, tr('button_update_selected'), apply_updates, 'success', width=140, padx=5)
        self._btn(bf, tr('button_close'), win.destroy, 'gray', width=80, padx=5)

        scroll = ctk.CTkScrollableFrame(win, fg_color=C['zebra'], corner_radius=10)
        scroll.pack(side='top', fill='both', expand=True, padx=10, pady=5)

        rows = []
        for idx, upd in enumerate(updates):
            row = ctk.CTkFrame(scroll, fg_color="transparent", corner_radius=4)
            row.upd = upd
            row.selected = False
            vals = [upd['name'], upd['current_ver'], upd['latest_ver'], ""]
            for i, val in enumerate(vals):
                lb = ctk.CTkLabel(row, text=str(val), anchor='w' if i < 3 else 'center',
                                  font=FONT_SM, width=col_widths[i])
                lb.pack(side='left', padx=4, pady=2)
                lb.bind('<Button-1>', lambda e, r=row: toggle(r))
            row.bind('<Button-1>', lambda e, r=row: toggle(r))
            ctk.CTkButton(row, text="📄", width=46, font=FONT_SM,
                          fg_color="transparent", hover_color=C['selected'],
                          command=lambda u=upd: self.show_changelog(u)).pack(side='left', padx=2)
            row.pack(fill='x', pady=1)
            rows.append(row)

    def show_changelog(self, upd):
        """查看更新日志（Modrinth version 自带 changelog 字段；CF 暂无数据源）"""
        ld = upd.get('latest_data') or {}
        text = (ld.get('changelog') or '').strip()
        self._text_popup(tr('dialog_changelog_title'), "560x420",
                         text[:6000] if text else tr('dialog_changelog_none'),
                         header=f"{upd.get('name', '')}  {upd.get('latest_ver', '')}")

    def _apply_cf_updates(self, to_update, win, expected_path=None):
        """CurseForge 条目更新：下载新文件计算 sha1/sha512 后替换（后台线程）"""
        def task():
            built = []
            for r in to_update:
                upd = r.upd
                if upd.get('cf'):
                    ld = upd['latest_data']
                    url = cf_cdn_url(ld['cfFileID'], ld['filename'])
                    hashes, size = {}, ld.get('filesize', 0)
                    try:
                        hashes, size = compute_hashes_from_url(url)
                    except Exception as e:
                        self.root.after(0, lambda fn=ld.get('filename'), err=str(e): self.log(
                            tr('log_cf_nohash').format(filename=fn, error=err), "WARNING"))
                    old_cf = (upd['current_entry'].get('cf') or {})
                    old_prefix = (upd['current_entry'].get('path') or 'mods/').split('/')[0]
                    built.append((upd['current_entry'].get('path'), {
                        'path': f"{old_prefix}/{ld['filename']}", 'hashes': hashes,
                        'downloads': [url], 'fileSize': size,
                        'cf': {'projectID': ld['cfProjectID'], 'fileID': ld['cfFileID'],
                               'required': old_cf.get('required', True)}}))
                else:
                    old_prefix = (upd['current_entry'].get('path') or 'mods/').split('/')[0]
                    built.append((upd['current_entry'].get('path'),
                                  build_mod_entry(upd['latest_data'], old_prefix)))
            self.root.after(0, lambda b=built, p=expected_path:
                            self._replace_entries(b, win, p))
        self.set_status(tr('status_downloading'))
        self._thread(task)

    def _replace_entries(self, built, win, expected_path=None):
        try:
            path = self._index_path_or_warn()
            if not path:
                return
            if expected_path is not None and path != expected_path:
                self.log(tr('log_async_pack_changed'), "WARNING")
                win.destroy()
                return
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            files = data.get('files', [])
            path_to_idx = {f.get('path'): i for i, f in enumerate(files)}
            replaced = 0
            for old_path, new_entry in built:
                idx = path_to_idx.get(old_path)
                if idx is not None:
                    files[idx] = new_entry
                    replaced += 1
            data['files'] = files
            self._save_index(data)
            self.log(tr('log_update_success').format(count=replaced), "SUCCESS")
            win.destroy()
            self.refresh_mod_list()
            self.reload_metadata()
            messagebox.showinfo(tr('dialog_title_done'),
                                tr('dialog_update_success').format(count=replaced))
        except Exception as e:
            self.log(tr('log_update_fail').format(error=str(e)), "ERROR")
            messagebox.showerror(tr('dialog_title_error'), tr('log_update_fail').format(error=str(e)))
        finally:
            self.set_status(tr('status_ready'))

    # ---------- 打包 .mrpack ----------
    def pack_to_mrpack(self, as_zip=False):
        path = self._index_path_or_warn()
        if not path:
            return
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            self.log(tr('log_read_index_fail').format(error=str(e)), "ERROR")
            messagebox.showerror(tr('dialog_title_error'),tr('dialog_pack_error'))
            return
        if not data.get('files', []):
            if not messagebox.askyesno(tr('dialog_title_tip'), tr('dialog_pack_empty')):
                return
        self._continue_pack(data, path, as_zip=as_zip)

    def export_zip_dispatch(self):
        """按整合包格式选择导出方式：CurseForge → manifest.zip；Modrinth → 含 index 的 .zip"""
        if self.pack_format == 'curseforge':
            self.export_cf_zip()
        else:
            self.pack_to_mrpack(as_zip=True)

    def _write_overrides_tree(self, zf, ov_dir, fmt):
        """把用户选择的覆盖文件夹写入 zip：
        顶层名为 client-overrides/server-overrides（Modrinth）或 clientoverrides（CF）的子目录
        原样映射到包内同名根目录，其余内容统一进 overrides/；返回写入文件数"""
        specials = ('client-overrides', 'server-overrides') if fmt == 'modrinth' else ('clientoverrides',)
        n = 0
        for r, _, fnames in os.walk(ov_dir):
            for fn in fnames:
                full = os.path.join(r, fn)
                rel = os.path.relpath(full, ov_dir).replace('\\', '/')
                parts = rel.split('/')
                if len(parts) == 1 and parts[0] in ('modrinth.index.json', 'manifest.json'):
                    continue  # 防止误把清单本身打进 overrides
                arc = rel if parts[0] in specials else f'overrides/{rel}'
                zf.write(full, arc)
                n += 1
        return n

    def _continue_pack(self, data, path, zip_index_path=None, as_zip=False):
        ext = ".zip" if as_zip else ".mrpack"
        filetypes = [("Zip Archive", "*.zip")] if as_zip else [("Modrinth Modpack", "*.mrpack")]
        save_path = filedialog.asksaveasfilename(
            defaultextension=ext, filetypes=filetypes,
            initialfile=f"{data.get('name', 'modpack')}{ext}")
        if not save_path:
            if zip_index_path:
                try: os.remove(zip_index_path)
                except OSError: pass
            return
        include_overrides = messagebox.askyesno(tr('dialog_confirm_overrides'),
                                                tr('dialog_overrides_prompt'))
        overrides_dir = filedialog.askdirectory(title=tr('dlg_overrides_dir')) if include_overrides else None
        if include_overrides and not overrides_dir:
            self.log(tr('log_no_overrides'), "WARNING")
        self.log(tr('log_pack_start').format(path=save_path))
        self.set_status(tr('status_loading'))
        self.progress_show(indeterminate=True)
        def task():
            try:
                base_dir = os.path.dirname(path)
                with zipfile.ZipFile(save_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                    zf.write(zip_index_path or path, "modrinth.index.json")
                    # index 中带下载链接的条目由安装器下载，不再放入 overrides（避免重复/旧版残留）；
                    # 仅本地条目（downloads 为空，如未识别的本地 jar/zip）才进 overrides
                    indexed = {e.get('path', '').replace('\\', '/'): e
                               for e in data.get('files', [])}
                    for sub in ('mods', 'resourcepacks', 'shaderpacks'):
                        sub_dir = os.path.join(base_dir, sub)
                        if os.path.exists(sub_dir):
                            added = 0
                            for root, _, files in os.walk(sub_dir):
                                for fname in files:
                                    full = os.path.join(root, fname)
                                    rel = f"{sub}/{os.path.relpath(full, sub_dir)}".replace('\\', '/')
                                    ent = indexed.get(rel)
                                    if ent is not None and ent.get('downloads'):
                                        continue
                                    if ent is None:
                                        continue  # 未登记文件（如切版本后的旧版残留）不打包
                                    zf.write(full, f"overrides/{rel}")
                                    added += 1
                            self.root.after(0, lambda s=sub, n=added: self.log(
                                tr('log_ov_dir_added').format(sub=s, n=n), "SUCCESS"))
                    if overrides_dir and os.path.isdir(overrides_dir):
                        cnt = self._write_overrides_tree(zf, overrides_dir, 'modrinth')
                        self.root.after(0, lambda d=overrides_dir, n=cnt: self.log(
                                tr('log_ov_files_added').format(n=n, path=d), "SUCCESS"))
                self.root.after(0, lambda: self.log(tr('log_pack').format(path=save_path), "SUCCESS"))
                self.root.after(0, lambda: self.set_status(tr('status_packed')))
                msg_key = 'dialog_pack_success_zip' if as_zip else 'dialog_pack_success'
                self.root.after(0, lambda: messagebox.showinfo(
                    tr('status_packed'), tr(msg_key).format(path=save_path)))
            except Exception as e:
                err = str(e)
                self.root.after(0, lambda: self.log(
                    tr('dialog_pack_fail').format(error=err), "ERROR"))
                self.root.after(0, lambda: messagebox.showerror(
                    tr('dialog_title_error'), tr('dialog_pack_fail').format(error=err)))
            finally:
                if zip_index_path:
                    try: os.remove(zip_index_path)
                    except OSError: pass
                self.progress_hide()
                self.root.after(0, lambda: self.set_status(tr('status_ready')))
        self._thread(task)
        self.set_status(tr('status_packing'))

    # ---------- 保存 ----------
    def _save_index(self, data):
        path = self.index_path.get().strip()
        if not path:
            return
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        if self.original_mrpack:
            if getattr(self, 'cf_mode', False):
                # CurseForge 包不自动写回（内部为转换后的 Modrinth index，写回会破坏 manifest）
                return
            self.update_mrpack_index(self.original_mrpack, data)

    def schedule_save(self):
        if self.save_timer:
            self.root.after_cancel(self.save_timer)
        self.save_timer = self.root.after(1000, self.save_current_index)

    def save_current_index(self):
        if getattr(self, 'cf_mode', False):
            # CurseForge 包不自动写回（内部为转换后的 Modrinth index，写回会破坏 manifest）
            self.save_timer = None
            return
        self.save_timer = None
        path = self.index_path.get().strip()
        if not path or not os.path.exists(path):
            return
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception:
            return
        changed = False
        new_name = self.entry_name.get().strip() or tr('unnamed')
        if data.get('name') != new_name:
            data['name'] = new_name; changed = True
        new_ver = self.entry_version.get().strip() or "1.0.0"
        if data.get('versionId') != new_ver:
            data['versionId'] = new_ver; changed = True
        deps = data.get('dependencies', {})
        new_mc = self.combo_mc.get().strip() or "1.20.1"
        if deps.get('minecraft') != new_mc:
            deps['minecraft'] = new_mc; changed = True
        loader_key = LOADER_KEYS.get(self.loader_var.get(), "fabric-loader")
        new_loader = self.combo_loader_ver.get().strip()
        if not new_loader:
            # 仅 Fabric 给默认值；Forge/NeoForge 保留原值，绝不写入 Fabric 的版本号
            new_loader = "0.15.11" if loader_key == "fabric-loader" else deps.get(loader_key, "")
        for old_key in ['fabric-loader', 'forge', 'neoforge']:
            if old_key != loader_key and old_key in deps:
                del deps[old_key]; changed = True
        if new_loader and deps.get(loader_key) != new_loader:
            deps[loader_key] = new_loader; changed = True
        if changed:
            data['dependencies'] = deps
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            self.log(tr('log_index_saved'), "SUCCESS")
            self.set_status(tr('status_saved'))
            if self.original_mrpack and os.path.exists(self.original_mrpack):
                self.update_mrpack_index(self.original_mrpack, data)
        else:
            self.set_status(tr('status_no_change'))

    def add_entry_to_index(self, entry, force=False):
        path = self._index_path_or_warn()
        if not path:
            return False
        data = self._load_index(path)
        if data is None:
            return False
        files = data.setdefault('files', [])
        dup = any(f.get("path") == entry["path"] for f in files)
        if dup and not force:
            self.log(tr('log_entry_exists').format(path=entry['path']), "WARNING")
            return False
        self.manual_backup()
        if dup:  # 用户确认仍要添加：替换同路径旧条目，避免重复登记
            files[:] = [f for f in files if f.get("path") != entry["path"]]
        files.append(entry)
        self._save_index(data)
        self.log(tr('log_add_mod').format(filename=os.path.basename(entry['path'])), "SUCCESS")
        self.refresh_mod_list()
        return True

    # ---------- 重复检测 ----------
    def detect_duplicates(self):
        path = self._index_path_or_warn()
        if not path:
            return
        data = self._load_index(path)
        if data is None:
            return
        files = data.get('files', [])
        groups = {}
        for idx, entry in enumerate(files):
            keys = set()
            for d in entry.get('downloads', []) or []:
                pid = parse_project_id_from_url(d)
                if pid:
                    keys.add(f"pid:{pid}")
            sha1 = entry.get('hashes', {}).get('sha1')
            if sha1:
                keys.add(f"sha1:{sha1}")
            if not keys:
                keys.add(f"path:{entry.get('path', '')}")
            for k in keys:
                groups.setdefault(k, []).append((idx, entry))
        dup_groups, seen_paths = [], set()
        for k, lst in groups.items():
            if len(lst) > 1:
                paths = tuple(e.get('path') for _, e in lst)
                if paths in seen_paths:
                    continue
                seen_paths.add(paths)
                dup_groups.append(lst)
        win = self._win(tr('dlg_dup_title'), "720x520")
        if not dup_groups:
            ctk.CTkLabel(win, text=tr('dlg_dup_none'), font=FONT_MD_BOLD).pack(pady=20)
            self._btn(win, tr('button_close'), win.destroy, 'gray', width=100, padx=0)
            return
        ctk.CTkLabel(win, text=tr('dlg_dup_intro').format(count=len(dup_groups)),
                     font=FONT_MD_BOLD).pack(pady=8)
        scroll = ctk.CTkScrollableFrame(win, fg_color=C['zebra'], corner_radius=10)
        scroll.pack(side='top', fill='both', expand=True, padx=10, pady=5)
        indices_to_delete = set()
        for group in dup_groups:
            gframe = ctk.CTkFrame(scroll, fg_color="transparent", corner_radius=4,
                                  border_width=1, border_color=C['border'])
            gframe.pack(fill='x', pady=4, padx=4)
            for i, (entry_index, entry) in enumerate(group):
                fn = os.path.basename(entry.get('path', ''))
                keep = i == 0
                lb = ctk.CTkLabel(gframe, text=f"{tr('dup_keep') if keep else tr('dup_extra')}  {fn}",
                                  anchor='w', font=FONT_SM,
                                  text_color=C['success'] if keep else C['danger'])
                lb.pack(fill='x', padx=4, pady=2)
                if not keep:
                    indices_to_delete.add(entry_index)

        def do_delete():
            if not indices_to_delete:
                win.destroy()
                return
            if not messagebox.askyesno(tr('dialog_title_tip'),
                                       tr('dialog_confirm_delete').format(count=len(indices_to_delete))):
                return
            if self.index_path.get().strip() != path:
                self.log(tr('log_async_pack_changed'), "WARNING")
                win.destroy()
                return
            self.manual_backup()
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                data['files'] = remove_entries_by_indices(data.get('files', []), indices_to_delete)
                self._save_index(data)
                self.log(tr('log_dup_deleted').format(count=len(indices_to_delete)), "SUCCESS")
                self.refresh_mod_list()
                win.destroy()
            except Exception as e:
                self.log(tr('log_dup_fail').format(error=str(e)), "ERROR")

        bf = ctk.CTkFrame(win, fg_color="transparent")
        bf.pack(side='bottom', pady=8)
        self._btn(bf, tr('dlg_dup_delete_extra'), do_delete, 'danger', width=240, padx=5)
        self._btn(bf, tr('button_close'), win.destroy, 'gray', width=100, padx=5)

    # ---------- 兼容性体检 ----------
    def compatibility_check(self):
        path = self._index_path_or_warn()
        if not path:
            return
        data = self._load_index(path)
        if data is None:
            return
        files = data.get('files', [])
        mc_ver = self.combo_mc.get().strip()
        loader_api = self._loader_api()
        to_check, cf_count = [], 0
        for entry in files:
            if entry.get('cf'):
                cf_count += 1
                continue
            sha1 = entry.get('hashes', {}).get('sha1')
            pid = None
            for d in entry.get('downloads', []) or []:
                pid = parse_project_id_from_url(d)
                if pid:
                    break
            if sha1:
                to_check.append({'sha1': sha1, 'pid': pid, 'etype': entry_type(entry),
                                 'filename': os.path.basename(entry.get('path', ''))})
        if not to_check:
            messagebox.showinfo(tr('dlg_compat_title'), tr('dlg_compat_ok'))
            return
        self.set_status(tr('status_loading'))
        self.progress_show()
        compat_total = len(to_check)

        def task():
            issues = []
            compat_done = 0
            with ThreadPoolExecutor(max_workers=10) as ex:
                futs = {ex.submit(api_lookup_version_by_hash, item['sha1']): item
                        for item in to_check}
                for fut in as_completed(futs):
                    item = futs[fut]
                    compat_done += 1
                    self.progress_set(compat_done, compat_total)
                    try:
                        version = fut.result()
                    except Exception:
                        version = None
                    if not version:
                        continue
                    gv = version.get('game_versions', [])
                    loaders = [l.lower() for l in version.get('loaders', [])]
                    reasons = []
                    if mc_ver and gv and mc_ver not in gv:
                        reasons.append(f"MC {mc_ver} not in [{','.join(gv[:3])}]")
                    if item.get('etype', 'mod') == 'mod' and loader_api and loaders and loader_api not in loaders:
                        reasons.append(f"{loader_api} not in [{','.join(loaders)}]")
                    if reasons:
                        name = self.cache.get_name(item['pid']) or item['filename']
                        issues.append({'name': name, 'filename': item['filename'],
                                       'reason': '; '.join(reasons)})
            self.root.after(0, lambda: self._show_compat_result(issues, cf_count))
        self._thread(task)

    def _show_compat_result(self, issues, cf_count):
        self.progress_hide()
        self.set_status(tr('status_ready'))
        win = self._win(tr('dlg_compat_title'), "720x520")
        if cf_count:
            ctk.CTkLabel(win, text=tr('dlg_compat_skip_cf').format(count=cf_count),
                         font=FONT_ITALIC, text_color=C['warning']).pack(pady=4)
        if not issues:
            ctk.CTkLabel(win, text=tr('dlg_compat_ok'), font=FONT_MD_BOLD,
                         text_color=C['success']).pack(pady=20)
            self._btn(win, tr('button_close'), win.destroy, 'gray', width=100, padx=0)
            return
        ctk.CTkLabel(win, text=tr('dlg_compat_issues').format(count=len(issues)),
                     font=FONT_MD_BOLD, text_color=C['warning']).pack(pady=6)
        scroll = ctk.CTkScrollableFrame(win, fg_color=C['zebra'], corner_radius=10)
        scroll.pack(side='top', fill='both', expand=True, padx=10, pady=5)
        for iss in issues:
            row = ctk.CTkFrame(scroll, fg_color="transparent", corner_radius=4)
            lb = ctk.CTkLabel(row, text=f"{iss['name']}  [{iss['filename']}]  ❌ {iss['reason']}",
                              anchor='w', font=FONT_SM, text_color=C['danger'])
            lb.pack(fill='x', padx=4, pady=2)
            row.pack(fill='x', pady=1)
        self._btn(win, tr('button_close'), win.destroy, 'gray', width=100, padx=0)

    def easy_switch_check(self):
        """版本易切：检查当前整合包切换目标 MC/加载器后的兼容性并支持升级"""
        path = self._index_path_or_warn()
        if not path:
            return
        data = self._load_index(path)
        if data is None:
            return
        files = data.get('files', [])
        if not files:
            messagebox.showinfo(tr('dialog_title_tip'), tr('easy_switch_no_mods'))
            return
        expected_path = path

        # 弹窗：目标 MC + 加载器选择
        win = self._win(tr('easy_switch_title'), "760x560")
        self.easy_win = win
        form = ctk.CTkFrame(win, fg_color="transparent")
        form.pack(fill='x', padx=12, pady=(10, 4))
        ctk.CTkLabel(form, text=tr('easy_switch_target_mc'), font=FONT_SM,
                     text_color=C['muted']).pack(side='left')
        self.easy_mc_var = ctk.StringVar(value=self.combo_mc.get().strip() or "1.20.1")
        ctk.CTkEntry(form, textvariable=self.easy_mc_var, width=140,
                     font=FONT_SM).pack(side='left', padx=(4, 16))
        ctk.CTkLabel(form, text=tr('easy_switch_target_loader'), font=FONT_SM,
                     text_color=C['muted']).pack(side='left')
        self.easy_loader_var = ctk.StringVar(value=self.loader_var.get())
        ctk.CTkComboBox(form, values=["Fabric", "Forge", "NeoForge"],
                        variable=self.easy_loader_var, width=120,
                        font=FONT_SM, state="readonly").pack(side='left', padx=4)
        self._btn(form, tr('easy_switch_search_btn'), self._easy_switch_start,
                  'accent2', width=150, padx=12)

        # 状态 + 统计
        self.easy_status_lbl = ctk.CTkLabel(win, text=tr('easy_switch_stats').format(ok='-', bad='-',
            unk='-', local='-'), font=FONT_SM, text_color=C['muted'])
        self.easy_status_lbl.pack(fill='x', pady=2)
        self.easy_stats_lbl = ctk.CTkLabel(win, text="", font=FONT_BOLD, text_color=C['accent'])
        self.easy_stats_lbl.pack(fill='x', pady=2)

        # 结果列表
        self.easy_scroll = ctk.CTkScrollableFrame(win, fg_color=C['zebra'], corner_radius=10)
        self.easy_scroll.pack(fill='both', expand=True, padx=10, pady=4)

        btns = ctk.CTkFrame(win, fg_color="transparent")
        btns.pack(fill='x', pady=8)
        self._btn(btns, tr('button_select_all'), self._easy_switch_toggle_all, 'gray', width=140, padx=6)
        self._btn(btns, tr('easy_switch_upgrade_btn'), self._easy_switch_upgrade, 'success', width=140, padx=6)
        self._btn(btns, tr('button_close'), win.destroy, 'gray', width=80, padx=6)

        self.easy_rows = []
        self.easy_results = []
        self.easy_expected_path = expected_path
        self._easy_switch_start()

    def _easy_switch_start(self):
        """后台并发检查兼容性"""
        target_mc = self.easy_mc_var.get().strip()
        target_loader = LOADER_API.get(self.easy_loader_var.get(), "fabric")
        if not target_mc:
            messagebox.showinfo(tr('dialog_title_tip'), tr('easy_switch_select_mc'))
            return
        self.log(tr('log_easy_switch_start').format(mc=target_mc, loader=target_loader))
        self.set_status(tr('status_loading'))
        self.progress_show()
        todo = []
        for entry in self._load_index(self.easy_expected_path).get('files', []):
            pid = parse_project_id_from_url((entry.get('downloads') or [None])[0] or '')
            todo.append({
                'pid': pid, 'cf': entry.get('cf'), 'entry': entry,
                'etype': entry_type(entry),
                'filename': os.path.basename(entry.get('path', ''))
            })

        def task():
            results = []
            total = len(todo)
            done = 0
            with ThreadPoolExecutor(max_workers=20) as ex:
                futs = {ex.submit(self._easy_switch_check_one, m, target_mc, target_loader): m
                        for m in todo}
                for fut in as_completed(futs):
                    m = futs[fut]
                    done += 1
                    self.root.after(0, lambda d=done, t=total: self.progress_set(d, t))
                    try:
                        res = fut.result()
                    except Exception:
                        res = {'entry': m['entry'], 'etype': m['etype'],
                               'filename': m['filename'], 'status': 'unknown'}
                    results.append(res)
            self.root.after(0, lambda: self._easy_switch_done(results))
        self._thread(task)

    def _easy_switch_check_one(self, m, target_mc, target_loader):
        """检查单个条目标 MC/loader 下的兼容性"""
        res = {'entry': m['entry'], 'etype': m['etype'],
               'filename': m['filename'], 'status': 'local',
               'target_ver': '', 'latest_data': None, 'name': None}
        try:
            if m.get('cf'):
                vs = cf_get_project_versions(m['cf']['projectID'], target_mc,
                                              target_loader if m['etype'] == 'mod' else None)
                if vs:
                    latest = max(vs, key=lambda v: v['file_id'])
                    name = self.cache.get_name(m['cf']['projectID']) or m['filename']
                    res['name'] = name
                    res['target_ver'] = extract_version(latest.get('name', ''))
                    res['latest_data'] = {'cfProjectID': m['cf']['projectID'],
                                          'cfFileID': latest['file_id'],
                                          'filename': latest.get('name', ''),
                                          'filesize': latest.get('filesize', 0)}
                    # CF 兼容判定：有版本即可升级，不做 mc/loader 过滤（cf_get_project_versions 已过滤）
                    res['status'] = 'ok'
                else:
                    res['status'] = 'bad'
            elif m.get('pid'):
                vs = self.api.get_all_versions(m['pid'], target_mc,
                                               target_loader if m['etype'] == 'mod' else None)
                if vs:
                    latest = vs[0]
                    res['name'] = self.cache.get_name(m['pid']) or m['filename']
                    res['target_ver'] = latest.get('version_number') or extract_version(latest.get('name', ''))
                    res['latest_data'] = latest
                    res['status'] = 'ok'
                else:
                    res['status'] = 'bad'
        except Exception:
            res['status'] = 'unknown'
        return res

    def _easy_switch_done(self, results):
        """渲染版本易切检查结果"""
        self.progress_hide()
        self.set_status(tr('status_ready'))
        self.easy_results = results
        if not results:
            return
        ok = sum(1 for r in results if r['status'] == 'ok')
        bad = sum(1 for r in results if r['status'] == 'bad')
        unk = sum(1 for r in results if r['status'] == 'unknown')
        self.log(tr('log_easy_switch_done').format(ok=ok, bad=bad, unk=unk),
            'WARNING' if bad else 'SUCCESS')

        # 清空列表
        for w in self.easy_scroll.winfo_children():
            w.destroy()
        self.easy_rows = []
        self._easy_switch_update_stats()

        status_map = {'ok': tr('easy_switch_status_ok'),
                      'bad': tr('easy_switch_status_bad'),
                      'unknown': tr('easy_switch_status_unknown'),
                      'local': tr('easy_switch_status_local')}
        for r in results:
            wrap = ctk.CTkFrame(self.easy_scroll, fg_color="transparent", corner_radius=4)
            wrap.pack(fill='x', pady=1)
            row = ctk.CTkFrame(wrap, fg_color="transparent", corner_radius=4)
            row.pack(fill='x', padx=2)
            row._res = r
            row._selected = (r['status'] == 'ok')

            name = r.get('name') or r['filename']
            status_txt = status_map.get(r['status'], r['status'])
            target = r.get('target_ver') or '-'
            path = r['entry'].get('path', '')

            ctk.CTkLabel(row, text=name, width=200, anchor='w',
                         font=FONT_SM).pack(side='left', padx=4)
            ctk.CTkLabel(row, text={'mod': tr('type_mod'), 'rp': tr('type_rp'), 'sp': tr('type_sp')}.get(r['etype'], r['etype']), width=60,
                         font=FONT_SM).pack(side='left')
            ctk.CTkLabel(row, text=status_txt, width=100,
                         font=FONT_SM).pack(side='left')
            ctk.CTkLabel(row, text=target, width=120,
                         font=FONT_SM).pack(side='left')
            ctk.CTkLabel(row, text=path, anchor='w',
                         font=FONT_SM, text_color=C['muted']).pack(side='left', padx=4, fill='x')

            def toggle(_e=None, row=row):
                if row._res['status'] in ('ok', 'unknown', 'local'):
                    row._selected = not row._selected
                    row.configure(fg_color=C['selected'] if row._selected else "transparent")
                    self._easy_switch_update_stats()

            row.bind('<Button-1>', toggle)
            for w in row.winfo_children():
                w.bind('<Button-1>', toggle)
            if row._selected:
                row.configure(fg_color=C['selected'])

            self.easy_rows.append(row)

    def _easy_switch_update_stats(self):
        if not self.easy_results:
            return
        ok = sum(1 for r in self.easy_results if r['status'] == 'ok')
        bad = sum(1 for r in self.easy_results if r['status'] == 'bad')
        unk = sum(1 for r in self.easy_results if r['status'] == 'unknown')
        self.easy_status_lbl.configure(
            text=tr('easy_switch_stats').format(ok=ok, bad=bad, unk=unk, local=sum(1 for r in self.easy_results if r['status'] == 'local')))
        total_upg = sum(1 for r in self.easy_rows
                        if r._res['status'] in ('ok', 'unknown', 'local'))
        selected = sum(1 for r in self.easy_rows if r._selected)
        self.easy_stats_lbl.configure(
            text=tr('update_selected').format(n=selected, total=total_upg))

    def _easy_switch_toggle_all(self):
        target = not all(r._selected for r in self.easy_rows
                         if r._res['status'] in ('ok', 'unknown', 'local'))
        for r in self.easy_rows:
            if r._res['status'] in ('ok', 'unknown', 'local'):
                r._selected = target
                r.configure(fg_color=C['selected'] if target else "transparent")
        self._easy_switch_update_stats()

    def _easy_switch_upgrade(self):
        sel = [r for r in self.easy_rows if r._selected]
        if not sel:
            messagebox.showinfo(tr('dialog_title_tip'), tr('easy_switch_no_compatible'))
            return
        if self.index_path.get().strip() != self.easy_expected_path:
            self.log(tr('log_async_pack_changed'), 'WARNING')
            return
        if not messagebox.askyesno(tr('dialog_title_tip'),
                                   tr('dialog_update_apply').format(count=len(sel))):
            return
        try:
            with open(self.easy_expected_path, 'r', encoding='utf-8') as f:
                pack = json.load(f)
        except Exception as e:
            self.log(tr('log_read_fail').format(error=str(e)), 'ERROR')
            return
        files = pack.get('files', [])
        path_to_idx = {f.get('path'): i for i, f in enumerate(files)}
        ok = 0
        for row in sel:
            res = row._res
            idx = path_to_idx.get(res['entry'].get('path'))
            if idx is None or not res.get('latest_data'):
                continue
            try:
                if res['status'] == 'ok':
                    ld = res['latest_data']
                    old_prefix = (res['entry'].get('path', 'mods/').split('/')[0])
                    if 'cfProjectID' in ld:
                        # CF 条目：构造 cf_cdn_url + cf 字段
                        pid_fid_url = f"https://mediafilez.forgecdn.net/files/{ld['cfFileID'] // 1000}/{ld['cfFileID'] % 1000}/{ld['filename']}"
                        old_cf = res['entry'].get('cf', {})
                        files[idx] = {
                            'path': f"{old_prefix}/{ld['filename']}",
                            'hashes': {}, 'env': res['entry'].get('env', {}),
                            'downloads': [pid_fid_url],
                            'fileSize': ld.get('filesize', 0),
                            'cf': {'projectID': ld['cfProjectID'], 'fileID': ld['cfFileID'],
                                   'required': old_cf.get('required', True)}}
                    else:
                        files[idx] = build_mod_entry(ld, old_prefix)
                    ok += 1
            except Exception:
                pass
        pack['files'] = files
        try:
            with open(self.easy_expected_path, 'w', encoding='utf-8') as f:
                json.dump(pack, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.log(tr('log_update_entry_fail').format(
                filename=res['filename'], error=str(e)), 'ERROR')
            return
        self.log(tr('log_easy_switch_upgrade').format(ok=ok, fail=len(sel) - ok),
                 'SUCCESS' if ok else 'ERROR')
        self.refresh_mod_list()
        messagebox.showinfo(tr('dialog_title_done'),
                            tr('dialog_update_success').format(count=ok))
        try:
            self.easy_win.destroy()
        except Exception:
            pass

    # ---------- 统计面板 ----------
    def show_stats(self):
        path = self._index_path_or_warn()
        if not path:
            return
        data = self._load_index(path)
        if data is None:
            return
        files = data.get('files', [])
        total_size = sum(e.get('fileSize', 0) for e in files)
        mr_count = cf_count = local_count = no_url = 0
        type_counts = {'mod': 0, 'rp': 0, 'sp': 0}
        for e in files:
            type_counts[entry_type(e)] += 1
            if e.get('cf'):
                cf_count += 1
                continue
            dls = e.get('downloads', []) or []
            if not dls or not any(d for d in dls):
                local_count += 1
                no_url += 1
            else:
                mr_count += 1

        def hsize(n):
            for unit in ['B', 'KB', 'MB', 'GB']:
                if n < 1024:
                    return f"{n:.1f} {unit}"
                n /= 1024
            return f"{n:.1f} TB"

        win = self._win(tr('dlg_stats_title'), "500x400")
        ctk.CTkLabel(win, text=f"{tr('dlg_stats_count')}: {len(files)}",
                     font=FONT_MD_BOLD).pack(pady=6)
        ctk.CTkLabel(win, text=f"{tr('dlg_stats_size')}: {hsize(total_size)}",
                     font=FONT_MD_BOLD).pack(pady=6)
        ctk.CTkLabel(win, text=tr('dlg_stats_source'), font=FONT_BOLD).pack(pady=(10, 2))
        ctk.CTkLabel(win, text=f"Modrinth: {mr_count}    CurseForge: {cf_count}    {tr('stats_local')}: {local_count}",
                     font=FONT_SM).pack(pady=2)
        ctk.CTkLabel(win, text=f"{tr('dlg_stats_types')}: "
                     f"{tr('type_mod')} {type_counts['mod']} · {tr('type_rp')} {type_counts['rp']} · "
                     f"{tr('type_sp')} {type_counts['sp']}", font=FONT_SM).pack(pady=2)
        ctk.CTkLabel(win, text=f"{tr('dlg_stats_no_url')}: {no_url}", font=FONT_SM).pack(pady=2)
        self._btn(win, tr('button_close'), win.destroy, 'gray', width=100, padx=0)

    # ---------- 备份历史管理 ----------
    def manage_backups(self):
        path = self._index_path_or_warn()
        if not path:
            return
        base_dir = os.path.dirname(path)
        fname = os.path.basename(path)
        backups = []
        try:
            for fn in os.listdir(base_dir):
                if fn.startswith(f"{fname}.backup_"):
                    full = os.path.join(base_dir, fn)
                    if os.path.isfile(full):
                        backups.append((os.path.getmtime(full), fn, full))
        except Exception:
            pass
        backups.sort(reverse=True)
        win = self._win(tr('dlg_backups_title'), "600x480")
        if not backups:
            ctk.CTkLabel(win, text=tr('dlg_backups_none'), font=FONT_MD_BOLD).pack(pady=20)
            self._btn(win, tr('button_close'), win.destroy, 'gray', width=100, padx=0)
            return
        scroll = ctk.CTkScrollableFrame(win, fg_color=C['zebra'], corner_radius=10)
        scroll.pack(side='top', fill='both', expand=True, padx=10, pady=5)
        cur = {'i': None}
        rows = []

        def select(i):
            if cur['i'] is not None:
                rows[cur['i']].configure(fg_color="transparent")
            cur['i'] = i
            rows[i].configure(fg_color=C['accent'])

        for i, (mtime, fn, _) in enumerate(backups):
            row = ctk.CTkFrame(scroll, fg_color="transparent", corner_radius=4)
            ts = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')
            lb = ctk.CTkLabel(row, text=f"🕒 {ts}   {fn}", anchor='w', font=FONT_SM)
            lb.pack(fill='x', padx=4, pady=2)
            lb.bind('<Button-1>', lambda e, idx=i: select(idx))
            row.bind('<Button-1>', lambda e, idx=i: select(idx))
            row.pack(fill='x', pady=1)
            rows.append(row)

        def do_restore():
            if cur['i'] is None:
                return
            if not messagebox.askyesno(tr('dlg_backups_restore'),
                                       tr('dlg_backups_restore_confirm')):
                return
            backup_path = backups[cur['i']][2]
            try:
                shutil.copy2(backup_path, path)
                self.log(tr('log_restored').format(name=backups[cur['i']][1]), "SUCCESS")
                self.refresh_mod_list()
                self.reload_metadata()
                win.destroy()
            except Exception as e:
                self.log(tr('log_restore_fail').format(error=str(e)), "ERROR")

        def do_delete():
            if cur['i'] is None:
                return
            if not messagebox.askyesno(tr('dlg_backups_delete'),
                                       tr('dlg_backups_delete_confirm')):
                return
            backup_path = backups[cur['i']][2]
            try:
                os.remove(backup_path)
                self.log(tr('log_backup_deleted').format(name=backups[cur['i']][1]), "SUCCESS")
                win.destroy()
                self.manage_backups()
            except Exception as e:
                self.log(tr('log_backup_delete_fail').format(error=str(e)), "ERROR")

        bf = ctk.CTkFrame(win, fg_color="transparent")
        bf.pack(side='bottom', pady=8)
        self._btn(bf, tr('dlg_backups_restore'), do_restore, 'success', width=100, padx=5)
        self._btn(bf, tr('dlg_backups_delete'), do_delete, 'danger', width=100, padx=5)
        self._btn(bf, tr('button_close'), win.destroy, 'gray', width=100, padx=5)

    # ---------- 单模组切版本 ----------
    def switch_mod_version(self):
        selected_rows = [r for r in self._rows if getattr(r, 'selected', False)]
        if len(selected_rows) != 1:
            messagebox.showinfo(tr('dlg_switch_ver_title'), tr('dlg_switch_no_sel'))
            return
        mod = selected_rows[0].raw
        project_id = mod.get('project_id')
        if not project_id:
            messagebox.showinfo(tr('dlg_switch_ver_title'), tr('dlg_switch_no_pid'))
            return
        old_path = mod.get('path')
        self.set_status(tr('status_loading'))
        loader_api = self._loader_api() if mod.get('etype', 'mod') == 'mod' else None
        self._fetch_versions_and_show(project_id, self.combo_mc.get().strip(),
                                       loader_api,
                                       self._show_switch_selector, old_path)

    def _show_switch_selector(self, default_versions, all_versions, project_id,
                              mc_ver, loader_api, old_path):
        def on_pick(ver):
            # 保留原条目的目录前缀（mods/resourcepacks/shaderpacks）
            prefix = old_path.replace('\\', '/').split('/')[0] if '/' in old_path else 'mods'
            new_entry = build_mod_entry(ver, prefix)
            idx_path = self.index_path.get().strip()
            if not idx_path or not os.path.exists(idx_path):
                messagebox.showerror(tr('dialog_title_error'),tr('dialog_file_not_found'))
                return
            self.manual_backup()
            try:
                with open(idx_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                files = data.get('files', [])
                replaced = False
                for i, e in enumerate(files):
                    if e.get('path') == old_path:
                        files[i] = new_entry
                        replaced = True
                        break
                if replaced:
                    data['files'] = files
                    self._save_index(data)
                    fn_new = os.path.basename(new_entry['path'])
                    self.log(tr('log_switched_to').format(filename=fn_new), "SUCCESS")
                    def _dl(_e=new_entry, _fn=fn_new):
                        if not self._download_single_mod(_e, _fn):
                            self.root.after(0, lambda p=_e['path']: self._rollback_entry(p))
                    self._thread(_dl)
                    self.refresh_mod_list()
                    self.reload_metadata()
                    messagebox.showinfo(tr('dlg_switch_ver_title'),
                                        tr('dialog_switched').format(filename=fn_new))
                else:
                    self.log(tr('log_entry_not_found').format(path=old_path), "WARNING")
            except Exception as e:
                self.log(tr('log_switch_fail').format(error=str(e)), "ERROR")
            finally:
                self.set_status(tr('status_ready'))
        self._version_table(f"{tr('dlg_switch_ver_title')} - {project_id}",
                            default_versions, all_versions, mc_ver, loader_api,
                            on_pick, 'button_close')

    # ---------- 打包前校验 ----------
    def pre_pack_check(self):
        path = self._index_path_or_warn()
        if not path:
            return None
        data = self._load_index(path)
        if data is None:
            return None
        base_dir = os.path.dirname(path)
        issues = []
        for entry in data.get('files', []):
            p = entry.get('path', '')
            fn = os.path.basename(p)
            local_path = os.path.join(base_dir, p)
            dls = entry.get('downloads', []) or []
            if not dls:
                if not os.path.exists(local_path):
                    issues.append(tr('pre_issue_local_missing').format(fn=fn, path=p))
            else:
                if not os.path.exists(local_path):
                    issues.append(tr('pre_issue_not_downloaded').format(fn=fn))
        if not issues:
            messagebox.showinfo(tr('dlg_pre_pack_title'), tr('dlg_pre_pack_ok'))
            return True
        win = self._win(tr('dlg_pre_pack_title'), "600x480")
        ctk.CTkLabel(win, text=tr('dlg_pre_pack_issues').format(count=len(issues)),
                     font=FONT_MD_BOLD, text_color=C['warning']).pack(pady=8)
        scroll = ctk.CTkScrollableFrame(win, fg_color=C['zebra'], corner_radius=10)
        scroll.pack(side='top', fill='both', expand=True, padx=10, pady=5)
        for iss in issues:
            lb = ctk.CTkLabel(scroll, text=f"⚠️ {iss}", anchor='w', font=FONT_SM,
                              text_color=C['warning'])
            lb.pack(fill='x', padx=4, pady=2)
        result = {'continue': False}

        def do_continue():
            result['continue'] = True
            win.destroy()

        bf = ctk.CTkFrame(win, fg_color="transparent")
        bf.pack(side='bottom', pady=8)
        self._btn(bf, tr('dlg_pre_pack_continue'), do_continue, 'success', width=120, padx=5)
        self._btn(bf, tr('dlg_pre_pack_cancel'), win.destroy, 'gray', width=100, padx=5)
        self.root.wait_window(win)
        return result['continue']

    # ---------- 一键下载全部模组 ----------
    def download_all_mods(self):
        path = self._index_path_or_warn()
        if not path:
            return
        data = self._load_index(path)
        if data is None:
            return
        files = data.get('files', [])
        if not files:
            messagebox.showinfo(tr('dlg_dl_all_title'), tr('dialog_no_mods'))
            return
        base_dir = os.path.dirname(path)
        total = len(files)
        self.set_status(tr('status_downloading'))
        self.progress_show()
        self.log(tr('log_dl_all_start').format(count=total))

        def task():
            ok = fail = 0
            for i, entry in enumerate(files, 1):
                fn = os.path.basename(entry.get('path', ''))
                dls = entry.get('downloads', []) or []
                url = dls[0] if dls else ''
                dest = os.path.join(base_dir, entry.get('path', f'mods/{fn}'))
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                if os.path.exists(dest):
                    ok += 1
                elif not url:
                    self.root.after(0, lambda f=fn: self.log(
                        tr('log_skip_nolink').format(filename=f), "WARNING"))
                    fail += 1
                else:
                    try:
                        with requests.get(url, stream=True, timeout=STREAM_TIMEOUT) as resp:
                            resp.raise_for_status()
                            with open(dest, 'wb') as f:
                                for chunk in resp.iter_content(chunk_size=8192):
                                    f.write(chunk)
                        sha1 = entry.get('hashes', {}).get('sha1')
                        if sha1 and compute_sha1(dest) != sha1:
                            os.remove(dest)
                            raise Exception("SHA1 mismatch")
                        ok += 1
                        self.root.after(0, lambda f=fn: self.log(
                            tr('log_download_done').format(filename=f), "SUCCESS"))
                    except Exception as e:
                        fail += 1
                        self.root.after(0, lambda f=fn, err=str(e): self.log(
                            tr('log_download_fail').format(filename=f, error=err), "ERROR"))
                self.root.after(0, lambda c=i, t=total: self.set_status(
                    f"{tr('status_downloading')} {c}/{t}"))
                self.progress_set(i, total)
            self.root.after(0, lambda: self._after_dl_all(ok, fail))
        self._thread(task)

    def _after_dl_all(self, ok, fail):
        self.progress_hide()
        self.set_status(tr('status_ready'))
        self.log(tr('dlg_dl_all_done').format(ok=ok, fail=fail),
                 "SUCCESS" if fail == 0 else "WARNING")
        messagebox.showinfo(tr('dlg_dl_all_title'),
                            tr('dlg_dl_all_done').format(ok=ok, fail=fail))

    def update_mrpack_index(self, mrpack_path, data):
        temp = mrpack_path + '.tmp'
        try:
            with zipfile.ZipFile(mrpack_path, 'r') as zin:
                with zipfile.ZipFile(temp, 'w', zipfile.ZIP_DEFLATED) as zout:
                    for item in zin.infolist():
                        if item.filename != 'modrinth.index.json':
                            zout.writestr(item, zin.read(item.filename))
                    zout.writestr('modrinth.index.json',
                                   json.dumps(data, indent=2, ensure_ascii=False))
            os.replace(temp, mrpack_path)
            self.log(tr('log_mrpack_index_updated'), "SUCCESS")
        except Exception as e:
            self.log(tr('log_mrpack_index_fail').format(error=str(e)), "ERROR")
            # 写入或替换失败时清理临时文件，避免残留
            try:
                if os.path.exists(temp):
                    os.remove(temp)
            except OSError:
                pass

if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    root = ctk.CTk()
    root.option_add('*Font', '微软雅黑 13')
    root.option_add('*TkFixedFont', 'Consolas 12')
    app = ModPackApp(root)
    root.mainloop()
