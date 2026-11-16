# -*- coding: utf-8 -*-
"""🍂 叶落归仓 — 单节点、通用、极轻的显存/内存疏通节点。

设计依据：PRD.md（2026-11-16 定稿）。零第三方依赖，只用 ComfyUI 自带模块。
"""

import gc  # noqa: F401  保留以兼容可能的未来扩展，当前不主动调用
import threading

import comfy.model_management

try:
    from server import PromptServer
except Exception:  # 独立导入/测试环境下无 PromptServer，功能降级但不报错
    PromptServer = None


class AnyType(str):
    """万能口：与任何类型比较都相等，实现任意数据原样直通。"""

    def __eq__(self, other):
        return True

    def __ne__(self, other):
        return False


ANY = AnyType("*")

# 纯内存间隔计数：不落盘、不读写文件。重启 ComfyUI 后自然归零。
_COUNTS = {}
_LOCK = threading.Lock()


class JinYeGuiCang:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "interval": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 100000,
                    "step": 1,
                    "label": "间隔（0=每次清）",
                }),
                "unload_model": ("BOOLEAN", {
                    "default": True,
                    "label": "卸载模型",
                    "label_on": "开",
                    "label_off": "关",
                }),
                "free_memory": ("BOOLEAN", {
                    "default": True,
                    "label": "回收内存",
                    "label_on": "开",
                    "label_off": "关",
                }),
                "empty_cache": ("BOOLEAN", {
                    "default": True,
                    "label": "清显存缓存",
                    "label_on": "开",
                    "label_off": "关",
                }),
            },
            "optional": {
                "anything": (ANY, {}),
            },
            "hidden": {
                "unique_id": "UNIQUE_ID",
                "extra_pnginfo": "EXTRA_PNGINFO",
            },
        }

    RETURN_TYPES = (ANY,)
    RETURN_NAMES = ("output",)
    FUNCTION = "run"
    OUTPUT_NODE = True
    CATEGORY = "🍂 叶落归仓"

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        # 每次都执行，间隔计数才会累加；NaN 与自身不等，ComfyUI 视为始终变化。
        return float("nan")

    @staticmethod
    def _workflow_key(unique_id, extra_pnginfo):
        """计数维度：工作流名 + 节点 ID，取不到也能工作。"""
        name = "default"
        try:
            if isinstance(extra_pnginfo, dict):
                wf = extra_pnginfo.get("workflow") or {}
                if isinstance(wf, dict):
                    name = wf.get("name") or wf.get("id") or name
        except Exception:
            pass
        return (str(name), str(unique_id))

    @staticmethod
    def _set_flags(unload, free):
        """双 flag 必须显式写：OFF 也写 False，避免 free_memory 偷带卸载。"""
        try:
            if PromptServer is None or PromptServer.instance is None:
                return
            queue = getattr(PromptServer.instance, "prompt_queue", None)
            if queue is None or not hasattr(queue, "set_flag"):
                return
            queue.set_flag("unload_models", bool(unload))
            queue.set_flag("free_memory", bool(free))
        except Exception:
            pass

    def run(self, interval, unload_model, free_memory, empty_cache,
            anything=None, unique_id=None, extra_pnginfo=None):
        try:
            key = self._workflow_key(unique_id, extra_pnginfo)
            with _LOCK:
                count = _COUNTS.get(key, 0) + 1
                _COUNTS[key] = count

            step = 0
            try:
                step = max(0, int(interval))
            except Exception:
                step = 0

            if step == 0 or count % step == 0:
                # 开关 1/2：交给 ComfyUI worker 在出片后统一处理
                self._set_flags(unload_model, free_memory)
                # 开关 3：即时轻清，安全、不卸载模型
                if empty_cache:
                    try:
                        comfy.model_management.soft_empty_cache()
                    except Exception:
                        pass
        except Exception:
            # 最坏情况仅「这次没清成」，绝不报错中断工作流
            pass

        # 万能口原样直通；即使上面全异常也照常输出。
        return (anything,)


NODE_CLASS_MAPPINGS = {
    "JinYeGuiCang": JinYeGuiCang,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "JinYeGuiCang": "🍂 叶落归仓",
}

WEB_DIRECTORY = "./web"

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]
