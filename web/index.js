import { app } from "../../../scripts/app.js";

// 🍂 叶落归仓 — 外观层（只做美化，不做功能；任何异常都静默降级）。
// 功能完全在 __init__.py 里，本文件即使整段失效也不影响节点运行。

const NODE_ID = "JinYeGuiCang";

app.registerExtension({
    name: "JinYeGuiCang.theme",

    async setup() {
        try {
            const link = document.createElement("link");
            link.rel = "stylesheet";
            link.href = new URL("./style.css", import.meta.url).href;
            document.head.appendChild(link);
        } catch (e) {
            /* 样式加载失败 → 原生外观，功能不受影响 */
        }
    },

    async nodeCreated(node) {
        if (node.comfyClass !== NODE_ID) return;
        try {
            // 低饱和深灰配色（公开属性 API，跨版本稳定；右键改色仍可覆盖）。
            node.color = "#2e2f31";
            node.bgcolor = "#3a3c3e";

            // 打标记，供 style.css 作用域命中；命中不到也只是没配色。
            node.constructor.prototype && (node._jyjc = true);

            // 尝试给 DOM 里的布尔开关容器加类以扩热区。
            // 完全依赖前端内部结构，找不到就放弃，绝不影响功能。
            const decorate = () => {
                try {
                    const el = node.domElement;
                    if (!el) return;
                    el.classList.add("jyjc-hooked");
                    const toggles = el.querySelectorAll(
                        'input[type="checkbox"], [role="checkbox"], .toggle, [data-testid*="toggle"]'
                    );
                    toggles.forEach((t) => {
                        const box = t.closest("label") || t.parentElement;
                        if (box && !box.classList.contains("jyjc-boolean-toggle")) {
                            box.classList.add("jyjc-boolean-toggle");
                        }
                    });
                } catch (e) {
                    /* 前端结构变化 → 跳过热区外扩 */
                }
            };
            decorate();
            setTimeout(decorate, 0);
        } catch (e) {
            /* 外观层任何异常都吞掉 */
        }
    },
});
