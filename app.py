import streamlit as st
import os
import io
import numpy as np
import imageio
from PIL import Image, ImageDraw, ImageFont
from utils.nvidia_api import NvidiaAPI

# --- 页面配置 ---
st.set_page_config(page_title="小景漫剧工厂", page_icon="🎬", layout="wide")

# --- 自定义 CSS ---
st.markdown("""
<style>
    .stApp { background-color: #0e1117; color: #fafafa; }
    h1 { text-align: center; color: #76b900; }
    .stButton>button { background-color: #76b900; color: white; border-radius: 8px; border: none; font-size: 1.2rem; width: 100%; padding: 10px; }
    .stButton>button:hover { background-color: #5a8f00; }
</style>
""", unsafe_allow_html=True)

# --- 核心函数：添加字幕 ---
def add_caption(image_bytes, text):
    image = Image.open(io.BytesIO(image_bytes))
    draw = ImageDraw.Draw(image)
    try:
        font = ImageFont.truetype("arial.ttf", 40)
    except:
        font = ImageFont.load_default()
    
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    x = (image.width - text_w) // 2
    y = image.height - text_h - 50
    
    draw.rectangle([x-10, y-10, x+text_w+10, y+text_h+10], fill=(0, 0, 0, 180))
    draw.text((x, y), text, font=font, fill=(255, 255, 255))
    
    buf = io.BytesIO()
    image.save(buf, format='PNG')
    return buf.getvalue()

# --- 核心函数：合成视频 (纯 Python) ---
def create_video(frames_data, captions, output_path="output.mp4", fps=24, duration_per_frame=3):
    all_frames = []
    for i, img_data in enumerate(frames_data):
        img_with_text = add_caption(img_data, captions[i])
        img_np = np.array(Image.open(io.BytesIO(img_with_text)))
        for _ in range(duration_per_frame * fps):
            all_frames.append(img_np)
    
    try:
        with imageio.get_writer(output_path, fps=fps, codec='libx264', quality=8) as writer:
            for frame in all_frames:
                writer.append_data(frame)
        return output_path
    except Exception as e:
        st.warning(f"MP4 编码失败 ({str(e)})，尝试生成 GIF...")
        gif_path = output_path.replace(".mp4", ".gif")
        low_res_frames = all_frames[::12]
        with imageio.get_writer(gif_path, fps=10) as writer:
            for frame in low_res_frames:
                writer.append_data(frame)
        return gif_path

# --- 主界面 ---
st.title("🎬 小景漫剧工厂 v4.0 (云端版)")
st.markdown("### 🌟 输入故事，一键生成高清动态漫剧 (纯云端运行)")

# 侧边栏配置 API Key
with st.sidebar:
    st.header("⚙️ 配置")
    api_key = st.text_input("NVIDIA API Key", type="password", help="从 build.nvidia.com 获取")
    if api_key:
        st.success("✅ API Key 已设置")
    st.info("提示：本应用完全在云端运行，无需本地 GPU！")

story = st.text_area("请输入小说片段 (支持长文本)", height=200, placeholder="从前有个少年...")

if st.button("🚀 开始生成漫剧"):
    if not api_key:
        st.error("请先在左侧设置 API Key！")
    elif not story:
        st.warning("请输入故事内容！")
    else:
        nvidia = NvidiaAPI(api_key)
        progress = st.progress(0)
        status = st.empty()
        
        # 1. 生成剧本 (简化版，直接拆分为 4 段)
        status.text("🤖 正在分析故事并生成 4 个分镜...")
        # 这里为了演示，简单将故事拆分为 4 个提示词。实际可调用 LLM 生成
        base_prompts = [
            f"{story} -- wide shot, establishing scene, anime style",
            f"{story} -- close up, character expression, dramatic lighting",
            f"{story} -- action scene, dynamic angle, intense",
            f"{story} -- epic finale, masterpiece, emotional"
        ]
        captions = ["第一幕：起始", "第二幕：发展", "第三幕：高潮", "第四幕：结局"]
        
        image_data_list = []
        image_preview = st.columns(4)
        
        # 2. 生成 4 张图
        for i in range(4):
            status.text(f"🎨 正在绘制第 {i+1} 张分镜 (SDXL)...")
            progress.progress((i+1) * 20)
            try:
                img_bytes = nvidia.generate_image(base_prompts[i], seed=123+i)
                image_data_list.append(img_bytes)
                image_preview[i].image(img_bytes, caption=f"分镜 {i+1}", use_container_width=True)
            except Exception as e:
                st.error(f"第 {i+1} 张图生成失败：{str(e)}")
                st.stop()
        
        # 3. 合成视频
        status.text("🎬 正在合成视频...")
        try:
            video_file = create_video(image_data_list, captions)
            progress.progress(100)
            status.text("✅ 生成成功！")
            
            if video_file.endswith(".mp4"):
                st.video(video_file)
                with open(video_file, "rb") as f:
                    st.download_button("📥 下载 MP4 视频", f, "manhua.mp4")
            else:
                st.image(video_file)
                st.info("已生成 GIF 版本。")
                with open(video_file, "rb") as f:
                    st.download_button("📥 下载 GIF", f, "manhua.gif")
        except Exception as e:
            st.error(f"视频合成出错：{str(e)}")

st.markdown("---")
st.caption("© 2026 小景漫剧工厂 | Powered by NVIDIA SDXL & Streamlit Cloud")
