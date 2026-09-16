# 昔涟 · 往昔的涟漪

基于《崩坏：星穹铁道》昔涟形象制作的 Q 版 Windows 桌宠。头发为粉蓝渐变：发根、头顶与刘海为粉色，长发下段渐变到天蓝色。透明背景，原生窗口；正常运行不需要网络。

## 启动

双击根目录的 **启动昔涟.vbs**，或运行 `dist/CyrenePet/CyrenePet.exe`。已打包版本无需安装 Python。移动给其他电脑时，请复制整个 `dist/CyrenePet` 文件夹。

## 互动

| 操作 | 效果 |
| --- | --- |
| 单击小人 | 摸头、开心动画、爱心 |
| 双击小人 | 睡觉 / 唤醒 |
| 按住左键拖动 | 移动桌宠，松手后保存位置 |
| 鼠标滚轮 | 缩放小人，范围 65%–160% |
| 右键小人或托盘图标 | 散步、置顶、安静陪伴、大小、隐藏、退出 |
| 点击托盘图标 | 显示隐藏的小人 |

自动散步默认开启，在所在屏幕可用区域内移动和转向，避开任务栏。休息时停止散步。安静陪伴关闭自动闲聊，手动互动仍有反馈。重复启动会显示已有桌宠。

位置和偏好保存在 `%LOCALAPPDATA%/CyreneFanProject/CyreneDesktopPet/settings.json`。屏幕布局改变或旧位置越界时自动收回可用区域，托盘菜单「回到主屏幕」也可找回小人。

## 开发

Python 3.13 / PySide6。使用 `py -3 -m venv .venv` 创建环境，然后执行 `.venv/Scripts/python.exe -m pip install -r requirements.txt`。

```powershell
.\.venv\Scripts\python.exe pet.py
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe pet.py --smoke-test
powershell -ExecutionPolicy Bypass -File build.ps1
```

`pet.py` 为窗口与交互，`core.py` 为位置和设置逻辑，`assets/` 为透明素材。`tools/prepare_assets.py` 从原始图集切出四种状态并对齐脚底，保留透明通道。动画使用状态素材配合呼吸、摆动、跳动和移动，属于四状态动画，不是逐帧骨骼动画。

素材搜索结果、出处和生成提示词见 [references/SOURCES.md](references/SOURCES.md) 与 [references/IMAGE_PROMPT.txt](references/IMAGE_PROMPT.txt)。角色及官方立绘版权属于米哈游 / HoYoverse；桌宠图集为 AI 生成的同人素材，本程序是个人同人项目。
