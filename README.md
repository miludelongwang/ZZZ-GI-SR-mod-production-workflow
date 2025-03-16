# ZZZ-GI-SR-mod-production-workflow
绝区零-原神-星穹铁道 制作mod 工作流
***

# dds贴图批量图片替换并生成ini
## 目的
批量将DBMT里单个IB提取的贴图用自己的图片替换生成MOD

## 举例
将绝区零里的录像店贴图换成自己的准备的图片

#### 准备工作
- 文件夹结构
./
    ddslmages
    ddsinput
    ddsOutput
    clearconfig.json
    cut.py
    rename.py
    RRNTDDSINI.py
    texconv.exe
    一键清空.py
1. 用DBMT提取录像店dds贴图复制到ddsInput文件夹
2. ddslmages里放入和dds贴图同数量的想要替换的自己的图片

### 使用流程
1. 运行cut.py选择ddsImages文件夹将里面的图片批量裁剪成目标比例
2. 运行RRNTDDSINI.py文件，弹窗填入IB值，运行最终得的ddsOutput文件夹就是覆盖原贴图的mod
3. 一键清空.py用来清空弹窗选择的文件夹
***

***
# 动态贴图生成
## 作用
1. **out**存放帧生成的图片，运行视频帧生成图片.exe时自动生成，以下脚本都是对里面的图片批量操作
2. **background.png**背景图片，如相框
3. **cut.py**批量裁剪图片
4. **input.mp4**帧生成所需要的视频
5. **rename.py**批量重命名为000.png序列图片
6. **resizing.py**批量调整图片尺寸
7. **rotateimages.py**批量翻转图片
8. **separatelyMerge.py**将图片加上背景图片
9. **stitching.py**将图片按行列拼接在一起生成stitchingResult.jpg
10. **stitchingResult.jpg**按行列拼接生成的图片
11. **视频帧生成图片.exe**点击打开，将input.mp4拖入窗口运行帧生成图片存放在out内































