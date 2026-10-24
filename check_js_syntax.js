// 临时提取ModpackWizard.html的JavaScript部分进行语法检查
const fs = require('fs');
const path = 'c:\\Users\\zxt11\\Documents\\trae_projects\\Modpack Tools\\web\\ModpackWizard.html';

// 读取HTML文件
const html = fs.readFileSync(path, 'utf8');

// 提取<script>标签内容
const scriptMatch = html.match(/<script[^>]*>([\s\S]*?)<\/script>/);
if (scriptMatch) {
    const jsCode = scriptMatch[1];
    
    // 创建临时JS文件
    const tempJsPath = 'temp_check.js';
    fs.writeFileSync(tempJsPath, jsCode);
    
    try {
        // 检查语法
        require('vm').runInNewContext(jsCode, { console, setTimeout, Promise, Array, Object, String, Number, Boolean });
        console.log('✅ JavaScript语法检查通过');
    } catch (error) {
        console.error('❌ JavaScript语法错误:', error.message);
        console.error('错误位置:', error.stack?.split('\n')[1] || '未知');
    } finally {
        // 清理临时文件
        if (fs.existsSync(tempJsPath)) {
            fs.unlinkSync(tempJsPath);
        }
    }
} else {
    console.error('未找到<script>标签');
}