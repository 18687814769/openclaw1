import requests
import time
from typing import List, Dict

class NvidiaAPI:
    def __init__(self, api_key: str):
        self.api_key = api_key
        # 【关键修复】切换到 Playground v2.5，二次元风格最佳
        self.image_url = "https://ai.api.nvidia.com/v1/genai/playgroundai/playground-v2.5-1024px-aesthetic"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

    def generate_image(self, prompt: str, seed: int = 42) -> bytes:
        """调用 NVIDIA API 生成图片"""
        # 优化 Prompt，增强二次元风格
        full_prompt = f"{prompt}, masterpiece, best quality, anime style, highly detailed, 8k, cinematic lighting, dynamic composition"
        
        payload = {
            "prompt": full_prompt,
            "width": 1024,
            "height": 1024,
            "seed": seed,
            "steps": 25,
            "guidance": 7.0
        }

        try:
            response = requests.post(self.image_url, headers=self.headers, json=payload, timeout=60)
            if response.status_code == 200:
                return response.content
            else:
                raise Exception(f"API Error: {response.status_code} - {response.text[:200]}")
        except Exception as e:
            raise Exception(f"图片生成失败：{str(e)}")

    def generate_script(self, prompt: str, model: str = "moonshotai/kimi-k2.5") -> str:
        """调用 NVIDIA LLM 生成剧本"""
        url = "https://integrate.api.nvidia.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": "你是一个专业的漫剧编剧。请根据用户提示创作一个简短的漫剧剧本，包含 4 个场景。每个场景用一句话描述画面。"},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 1000
        }
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
        except Exception as e:
            return f"剧本生成失败：{str(e)}"
