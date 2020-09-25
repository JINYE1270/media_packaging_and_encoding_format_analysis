# package_format_and_encoding_analysis
视频封装格式和编码格式解析系统，目前支持从ts文件中解析mpeg-ts封装格式信息和提取es层的.h264文件；支持sm4-cbc模式解密。

参考标准：</br>
H264 https://www.itu.int/rec/T-REC-H.264/en </br>
其中：</br> 
英文版 H.264 (06/19)https://www.itu.int/rec/T-REC-H.264-201906-I/en </br> 
中文版 H.264 (03/05)https://www.itu.int/rec/T-REC-H.264-200503-S/en </br>

使用：</br>
1.解析 mpeg-ts 封装格式，并提取ES层.h264数据</br>
python parse_ts.py </br>
2.SM4解密 </br>
python parse_h264.py </br>
