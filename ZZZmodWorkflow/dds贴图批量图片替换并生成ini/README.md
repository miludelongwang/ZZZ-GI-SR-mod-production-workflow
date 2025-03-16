# 目的
批量将DBMT里单个IB提取的贴图用自己的图片替换生成MOD
***

# 举例
将绝区零里的录像店贴图换成自己的准备的图片

## 准备工作
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

## 使用流程
1. 运行cut.py选择ddsImages文件夹将里面的图片批量裁剪成目标比例
2. 运行RRNTDDSINI.py文件，弹窗填入IB值，运行最终得的ddsOutput文件夹就是覆盖原贴图的mod
3. 一键清空.py用来清空弹窗选择的文件夹
