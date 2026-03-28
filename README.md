# AI锁屏图片生成器

荣耀魔法画报 · 智能内容生产平台

批量输入中文文章标题，自动生成符合荣耀手机锁屏规范的AI高清壁纸。

## 功能

- 批量输入中文文章标题（最多20条），自动生成9:16手机锁屏壁纸
- 智能中文→英文提示词转换，优化AI生图效果
- 内置荣耀内容安全审核规则，自动检测敏感内容
- 支持单张重新生成
- 实时生成进度显示

## 部署到 Render

1. Fork 本仓库
2. 在 [Render](https://render.com) 创建 Web Service，关联此仓库
3. 设置环境变量：
   - `MULEROUTER_API_KEY` = 你的API密钥（[获取地址](https://www.mulerouter.ai/app/api-keys)）
   - `MULEROUTER_BASE_URL` = `https://api.mulerun.com`
4. 部署即可

## 本地运行

```bash
pip install -r requirements.txt
export MULEROUTER_API_KEY="your-api-key"
export MULEROUTER_BASE_URL="https://api.mulerun.com"
python app.py
```

浏览器打开 http://localhost:8080

## 技术架构

- **前端**: 单HTML文件，深色主题，毛玻璃效果
- **后端**: Flask + Gunicorn
- **AI模型**: Google Nano-Banana Pro (2K分辨率)
- **API**: MuleRouter / MuleRun
