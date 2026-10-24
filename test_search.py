# -*- coding: utf-8 -*-
"""mod_match 搜索匹配纯函数单元测试
运行：cd py_ctk ; python -m unittest test_search -v
覆盖：空输入、名称/文件名/路径/版本号匹配、大小写、中英文、无结果、缺失字段容错、非字符串字段容错
"""
import sys
import types
import unittest

# 测试只覆盖 mod_match 纯逻辑；环境缺 requests/customtkinter 时注入桩模块，
# 使 ModpackWizard 顶层 import 与初始化通过（不会触发任何窗口或网络调用）
try:
    import requests  # noqa: F401
except ImportError:
    _stub = types.ModuleType('requests')
    _stub.get = _stub.post = lambda *a, **k: None
    sys.modules['requests'] = _stub
try:
    import customtkinter  # noqa: F401
except ImportError:
    _ctk = types.ModuleType('customtkinter')
    _ctk.set_appearance_mode = lambda *a, **k: None
    _ctk.set_default_color_theme = lambda *a, **k: None
    _ctk.set_widget_scaling = lambda *a, **k: None
    sys.modules['customtkinter'] = _ctk
try:
    import tkinter  # noqa: F401
except ImportError:
    _tk = types.ModuleType('tkinter')

    class _StubVar:
        def __init__(self, *a, **k):
            self._v = None

        def set(self, v):
            self._v = v

        def get(self):
            return self._v
    _tk.StringVar = _tk.BooleanVar = _tk.IntVar = _tk.DoubleVar = _StubVar
    for _name in ('filedialog', 'messagebox', 'simpledialog'):
        setattr(_tk, _name, types.SimpleNamespace())
    sys.modules['tkinter'] = _tk

from ModpackWizard import (build_mod_entry, build_project_search_facets,
                           easy_switch_selectable, entry_prefix, entry_type,
                           is_current_pack_open, mod_match,
                           remove_entries_by_indices)

E = {
    'display_name': ' sodium ',
    'filename': 'sodium-fabric-0.5.3.jar',
    'path': 'mods/sodium-fabric-0.5.3.jar',
    'version': '0.5.3',
}


class TestModMatch(unittest.TestCase):
    def test_empty_keyword_returns_true(self):
        """空输入：全部通过，不做过滤"""
        self.assertTrue(mod_match(E, ''))
        self.assertTrue(mod_match(E, '   '))
        self.assertTrue(mod_match({}, None))

    def test_match_display_name(self):
        self.assertTrue(mod_match(E, 'sodium'))
        self.assertTrue(mod_match(E, 'SODIUM'))          # 大小写不敏感
        self.assertTrue(mod_match(E, 'dium'))            # 子串模糊

    def test_match_filename(self):
        self.assertTrue(mod_match(E, 'sodium-fabric'))
        self.assertTrue(mod_match(E, '.jar'))

    def test_match_version(self):
        self.assertTrue(mod_match(E, '0.5.3'))
        self.assertTrue(mod_match(E, '0.5'))

    def test_match_path(self):
        self.assertTrue(mod_match(E, 'mods/'))

    def test_chinese_keyword(self):
        e = {'display_name': '苹果', 'filename': 'apple-mod.jar', 'path': 'mods/apple-mod.jar', 'version': '1.0'}
        self.assertTrue(mod_match(e, '苹果'))
        self.assertFalse(mod_match(e, '香蕉'))

    def test_no_result(self):
        self.assertFalse(mod_match(E, 'optifine'))
        self.assertFalse(mod_match(E, '0.9.9'))

    def test_missing_fields_tolerated(self):
        """缺失字段不报错，仅按存在的字段匹配"""
        self.assertTrue(mod_match({'display_name': 'sodium'}, 'sodium'))
        self.assertFalse(mod_match({}, 'sodium'))

    def test_missing_version_field(self):
        """version 键缺失：版本关键词不命中，名称仍命中"""
        e = {'display_name': 'sodium', 'filename': 'sodium.jar',
             'path': 'mods/sodium.jar'}
        self.assertFalse(mod_match(e, '0.5.3'))
        self.assertTrue(mod_match(e, 'sodium'))

    def test_non_string_version(self):
        """version 为数字：str() 容错后按字符串匹配（其余字段不含版本词，避免误命中）"""
        e = {'display_name': 'solver', 'filename': 'solver.jar',
             'path': 'mods/solver.jar', 'version': 503}
        self.assertTrue(mod_match(e, '503'))
        self.assertTrue(mod_match(e, '50'))
        self.assertFalse(mod_match(e, '0.5.3'))

    def test_non_string_none_tolerated(self):
        """字段值为 None：不崩溃，其余字段照常匹配"""
        e = {'display_name': 'sodium', 'version': None}
        self.assertTrue(mod_match(e, 'sodium'))
        self.assertFalse(mod_match(e, 'sodium-fabric'))

class TestProjectSearchFacets(unittest.TestCase):
    def test_mod_search_filters_type_mc_and_loader(self):
        self.assertEqual(
            build_project_search_facets('mod', '1.20.1', 'fabric'),
            [['project_type:mod'], ['versions:1.20.1'], ['categories:fabric']])

    def test_resource_pack_search_omits_loader_filter(self):
        self.assertEqual(
            build_project_search_facets('rp', '1.20.1', 'fabric'),
            [['project_type:resourcepack'], ['versions:1.20.1']])

    def test_shader_search_without_mc_omits_optional_facets(self):
        self.assertEqual(
            build_project_search_facets('sp', '', 'forge'),
            [['project_type:shader']])

class TestBuildModEntry(unittest.TestCase):
    def setUp(self):
        self.version = {'files': [{
            'filename': 'pack.zip', 'url': 'https://example.test/pack.zip',
            'size': 10, 'hashes': {'sha1': 'abc', 'sha512': 'def'},
            'env': {'client': 'required'},
        }]}

    def test_csv_path_preserves_resource_pack_directory(self):
        prefix = entry_prefix(entry_type({'path': 'resourcepacks/pack.zip'}))
        self.assertEqual(build_mod_entry(self.version, prefix)['path'],
                         'resourcepacks/pack.zip')

    def test_explicit_prefix_does_not_depend_on_global_state(self):
        self.assertEqual(build_mod_entry(self.version, 'shaderpacks')['path'],
                         'shaderpacks/pack.zip')

    def test_missing_hashes_are_tolerated(self):
        version = {'files': [{'filename': 'local.jar', 'url': 'https://example.test/local.jar'}]}
        entry = build_mod_entry(version, 'mods')
        self.assertEqual(entry['hashes'], {'sha1': '', 'sha512': ''})
        self.assertEqual(entry['fileSize'], 0)

class TestPackOpenAndDuplicateRemoval(unittest.TestCase):
    def test_only_latest_pack_open_is_current(self):
        self.assertFalse(is_current_pack_open(1, 2))
        self.assertTrue(is_current_pack_open(2, 2))

    def test_duplicate_removal_uses_entry_index_not_path(self):
        keep = {'path': 'mods/shared.jar', 'id': 'keep'}
        extra = {'path': 'mods/shared.jar', 'id': 'extra'}
        other = {'path': 'mods/other.jar'}
        self.assertEqual(remove_entries_by_indices([keep, extra, other], {1}),
                         [keep, other])


class TestEasySwitchSelectable(unittest.TestCase):
    def test_ok_is_selectable(self):
        self.assertTrue(easy_switch_selectable({'status': 'ok'}))

    def test_bad_unknown_local_not_selectable(self):
        self.assertFalse(easy_switch_selectable({'status': 'bad'}))
        self.assertFalse(easy_switch_selectable({'status': 'unknown'}))
        self.assertFalse(easy_switch_selectable({'status': 'local'}))

    def test_missing_status_not_selectable(self):
        self.assertFalse(easy_switch_selectable({}))
        self.assertFalse(easy_switch_selectable(None))


if __name__ == '__main__':
    unittest.main(verbosity=2)
