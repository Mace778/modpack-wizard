// match_entry 搜索匹配纯函数单元测试（node test_search.js）
// 从 ModpackWizard.html 提取内联的 match_entry 源码执行，保证测的是真实实现
// 提取采用花括号计数定位函数体结尾，避免依赖"函数恰好在行尾结束"的脆弱假设
const fs = require('fs');
const path = require('path');
const html = fs.readFileSync(path.join(__dirname, 'ModpackWizard.html'), 'utf8');

function extractFunction(signature, marker) {
  const start = html.indexOf(signature);
  if (start < 0) { console.error(`FATAL: ${marker} not found in ModpackWizard.html`); process.exit(1); }
  let depth = 0, end = -1;
  for (let i = start + signature.length - 1; i < html.length; i++) {
    const ch = html[i];
    if (ch === '{') depth++;
    else if (ch === '}') { depth--; if (depth === 0) { end = i + 1; break; } }
  }
  if (end < 0) { console.error(`FATAL: ${marker} braces unbalanced`); process.exit(1); }
  return html.slice(start, end);
}
const src = extractFunction('function match_entry(e,kw){', 'match_entry');
if (!/return f\.some/.test(src)) { console.error('FATAL: extracted code incomplete'); process.exit(1); }
const match_entry = new Function('return ' + src)();
const build_project_search_facets = new Function('return ' +
  extractFunction('function build_project_search_facets(add_type,mc_version,loader_api){',
    'build_project_search_facets'))();
const entry_type = new Function('return ' +
  extractFunction('function entry_type(e){', 'entry_type'))();
const entry_prefix = new Function('TYPE_PREFIX', 'return ' +
  extractFunction('function entry_prefix(t){', 'entry_prefix'))(
  { mod: 'mods', rp: 'resourcepacks', sp: 'shaderpacks' });
const build_mod_entry = new Function('return ' +
  extractFunction('function build_mod_entry(version_data,prefix=', 'build_mod_entry'))();
const begin_pack_open = new Function('return ' +
  extractFunction('function begin_pack_open(){', 'begin_pack_open'))();
const is_current_pack_open = new Function('return ' +
  extractFunction('function is_current_pack_open(batch){', 'is_current_pack_open'))();
const remove_duplicate_entry = new Function('return ' +
  extractFunction('function remove_duplicate_entry(pack,entry,local_jars,override_files){',
    'remove_duplicate_entry'))();

const E = {
  display_name: ' sodium ',
  filename: 'sodium-fabric-0.5.3.jar',
  path: 'mods/sodium-fabric-0.5.3.jar',
  version: '0.5.3',
};

let passed = 0, failed = 0;
function t(name, actual, expected) {
  const ok = actual === expected;
  ok ? passed++ : failed++;
  console.log((ok ? 'ok ' : 'FAIL ') + name + (ok ? '' : `  (got ${actual}, want ${expected})`));
}
// 断言"不抛异常且返回期望值"（等价于 t()，抛异常时记失败并继续）
function ts(name, fn, expected) {
  try { t(name, fn(), expected); }
  catch (err) { failed++; console.log('FAIL ' + name + '  (threw: ' + err.message + ')'); }
}

t('空输入返回 true', match_entry(E, ''), true);
t('null 关键词返回 true', match_entry(E, null), true);
t('名称匹配', match_entry(E, 'sodium'), true);
t('名称大小写不敏感', match_entry(E, 'SODIUM'), true);
t('名称子串模糊', match_entry(E, 'dium'), true);
t('文件名匹配', match_entry(E, 'sodium-fabric'), true);
t('版本号匹配', match_entry(E, '0.5.3'), true);
t('版本号部分匹配', match_entry(E, '0.5'), true);
t('路径匹配', match_entry(E, 'mods/'), true);
t('中文关键词', match_entry({ display_name: '苹果' }, '苹果'), true);
t('无结果', match_entry(E, 'optifine'), false);
t('无结果(版本)', match_entry(E, '0.9.9'), false);
t('缺失字段容错(命中)', match_entry({ display_name: 'sodium' }, 'sodium'), true);
t('缺失字段容错(不命中)', match_entry({}, 'sodium'), false);
// 边界：version 键缺失
ts('version 缺失(版本词不命中)', () => match_entry(
  { display_name: 'sodium', filename: 'sodium.jar', path: 'mods/sodium.jar' }, '0.5.3'), false);
ts('version 缺失(名称仍命中)', () => match_entry(
  { display_name: 'sodium', filename: 'sodium.jar', path: 'mods/sodium.jar' }, 'sodium'), true);
// 边界：version 为数字（不得抛 TypeError；其余字段不含版本词，避免误命中）
ts('数字版本(全匹配)', () => match_entry(
  { display_name: 'solver', filename: 'solver.jar', path: 'mods/solver.jar', version: 503 }, '503'), true);
ts('数字版本(部分匹配)', () => match_entry(
  { display_name: 'solver', filename: 'solver.jar', path: 'mods/solver.jar', version: 503 }, '50'), true);
ts('数字版本(不误命中)', () => match_entry(
  { display_name: 'solver', filename: 'solver.jar', path: 'mods/solver.jar', version: 503 }, '0.5.3'), false);
// 边界：字段值为 null/undefined（不得抛异常）
ts('字段为 null 不崩溃', () => match_entry({ display_name: 'sodium', version: null }, 'sodium'), true);
ts('字段为 undefined 不崩溃', () => match_entry({ display_name: 'sodium', version: undefined }, 'sodium'), true);
t('搜索 facet 限定 mod、MC 和加载器', JSON.stringify(
  build_project_search_facets('mod', '1.20.1', 'fabric')),
JSON.stringify([['project_type:mod'], ['versions:1.20.1'], ['categories:fabric']]));
t('资源包搜索不附加加载器 facet', JSON.stringify(
  build_project_search_facets('rp', '1.20.1', 'fabric')),
JSON.stringify([['project_type:resourcepack'], ['versions:1.20.1']]));
t('光影搜索不附加加载器 facet', JSON.stringify(
  build_project_search_facets('sp', '', 'forge')),
JSON.stringify([['project_type:shader']]));
const version = { files: [{ filename: 'pack.zip', url: 'https://example.test/pack.zip',
  size: 10, hashes: { sha1: 'abc', sha512: 'def' }, env: { client: 'required' } }] };
const rpEntry = build_mod_entry(version, entry_prefix(entry_type({ path: 'resourcepacks/pack.zip' })));
t('CSV 导入路径可保留资源包目录', rpEntry.path, 'resourcepacks/pack.zip');
t('条目保留 Modrinth 环境元数据', JSON.stringify(rpEntry.env), JSON.stringify({ client: 'required' }));
t('显式路径前缀不依赖其他添加类型', build_mod_entry(version, 'shaderpacks').path, 'shaderpacks/pack.zip');
const sparseEntry = build_mod_entry({ files: [{ filename: 'local.jar', url: 'https://example.test/local.jar' }] }, 'mods');
t('缺失哈希与文件大小时使用安全默认值', JSON.stringify(
  [sparseEntry.hashes, sparseEntry.fileSize]), JSON.stringify([{ sha1: '', sha512: '' }, 0]));
global.PACK_OPEN_BATCH = 0;
const firstOpen = begin_pack_open(), secondOpen = begin_pack_open();
t('较早打开请求被新请求作废', is_current_pack_open(firstOpen), false);
t('最新打开请求保持有效', is_current_pack_open(secondOpen), true);
const keptDuplicate = { path: 'mods/shared.jar' };
const removedDuplicate = { path: 'mods/shared.jar' };
const dupPack = { files: [keptDuplicate, removedDuplicate] };
const localSources = new Map([[keptDuplicate.path, { file: 'local' }]]);
const overrideSources = new Map([[keptDuplicate.path, { file: 'override' }]]);
remove_duplicate_entry(dupPack, removedDuplicate, localSources, overrideSources);
t('删除同路径重复项保留条目与源文件', dupPack.files.length, 1);
t('同路径保留项的本地源不被清理', localSources.has(keptDuplicate.path), true);
t('同路径保留项的覆盖源不被清理', overrideSources.has(keptDuplicate.path), true);
const lastPathPack = { files: [{ path: 'mods/deleted.jar' }] };
const deletedPath = lastPathPack.files[0];
const staleOverrides = new Map([[deletedPath.path, { file: 'stale' }]]);
remove_duplicate_entry(lastPathPack, deletedPath, new Map(), staleOverrides);
t('删除最后一个路径条目时清理覆盖源', staleOverrides.has(deletedPath.path), false);

console.log(`\n${passed} passed, ${failed} failed`);
process.exit(failed ? 1 : 0);
