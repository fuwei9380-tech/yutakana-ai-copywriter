import streamlit as st
import re
import json
from datetime import datetime

st.set_page_config(page_title="裕生活 AI 营销文案助手", page_icon="🌿", layout="wide")

# ============================================================
# 合规敏感词库（基于《广告法》《保健食品广告审查暂行规定》）
# ============================================================
SENSITIVE_WORDS = {
    "功效宣称（保健食品禁止）": [
        "治疗", "治愈", "根治", "药效", "疗效", "预防疾病",
        "抗癌", "防癌", "降血压", "降血糖", "降血脂",
        "减肥", "瘦身", "消炎", "杀菌", "抗病毒",
        "增强免疫力", "改善睡眠", "治疗失眠", "护肝", "补肾",
        "明目", "保护视力", "恢复视力", "抗衰老",
    ],
    "绝对化用语": [
        "最好", "最佳", "最优", "最强", "第一", "顶级",
        "国家级", "世界级", "史上最强", "独一无二", "绝无仅有",
        "100%有效", "绝对有效", "万能", "全网最低",
    ],
    "医疗暗示": [
        "处方", "临床", "医学证明", "医院推荐", "医生推荐",
        "患者反馈", "药效", "疗程", "副作用小", "无副作用",
        "药用", "医疗器械",
    ],
    "虚假承诺": [
        "立竿见影", "药到病除", "永不反弹", "保证有效",
        "立即见效", "三天见效", "一周见效", "100%见效",
        "无效退款", "无效包退",
    ],
    "保健食品特殊禁区": [
        "代替药物", "替代药物", "不用吃药", "停用西药",
        "从根本上", "彻底解决", "一劳永逸",
    ],
}

SAFE_ALTERNATIVES = {
    "降血压": "帮助维持血压健康水平",
    "降血糖": "帮助维持血糖健康水平",
    "降血脂": "帮助维持血脂健康水平",
    "改善睡眠": "帮助放松身心",
    "治疗失眠": "帮助放松入睡",
    "增强免疫力": "帮助维持身体良好状态",
    "保护视力": "帮助呵护眼部健康",
    "明目": "帮助呵护眼部舒适",
    "抗衰老": "帮助维持年轻状态",
    "减肥": "帮助管理体重",
    "瘦身": "帮助管理体态",
    "护肝": "帮助呵护身体舒适",
    "补肾": "帮助维持精力充沛",
    "消炎": "帮助舒缓不适",
    "无副作用": "温和配方",
    "最好": "备受好评",
    "最佳": "优质之选",
    "第一": "领先的",
    "100%有效": "广受用户认可",
    "立竿见影": "坚持使用感受变化",
    "保证有效": "品质值得信赖",
    "治疗": "帮助调理",
    "治愈": "帮助改善",
    "根治": "从日常习惯入手改善",
    "疗效": "使用体验",
    "预防疾病": "帮助维持健康",
}


def compliance_check(text):
    alerts = []
    for category, words in SENSITIVE_WORDS.items():
        for word in words:
            if word in text:
                suggestion = SAFE_ALTERNATIVES.get(word, "建议删除或改写该表述")
                alerts.append({
                    "category": category,
                    "word": word,
                    "suggestion": suggestion,
                })
    return alerts


# ============================================================
# 产品库（基于 Yutakana Seikatsu 实际产品线）
# ============================================================
PRODUCTS = {
    "Vision Defense × Eyes Revitalize（护眼）": {
        "ingredients": "马基莓、叶黄素、玉米黄质、越橘提取物",
        "selling_points": "日本研发、马基莓专利成分、小颗粒易吞咽、临床数据支持",
        "target_concerns": {
            "18-34岁（小红书用户）": "干眼、屏幕疲劳、眼部干涩",
            "35岁+（视频号用户）": "视力下降、眼部老化、老花预防",
        },
    },
    "Natural Relax × Deep Sleep（助眠）": {
        "ingredients": "GABA、茶氨酸、褪黑素、缬草根",
        "selling_points": "天然成分、7天感受变化、无依赖性、日本品质",
        "target_concerns": {
            "18-34岁（小红书用户）": "加班失眠、入睡困难、睡眠质量差",
            "35岁+（视频号用户）": "压力失眠、早醒、睡眠浅",
        },
    },
    "Glycation Free × Skin Rebound（抗糖护肤）": {
        "ingredients": "抗糖化专利成分、胶原蛋白、透明质酸、维生素C",
        "selling_points": "抗糖新理念、日本专利、由内而外、清洁配方",
        "target_concerns": {
            "18-34岁（小红书用户）": "暗沉、糖化老化、皮肤弹性",
            "35岁+（视频号用户）": "皱纹、胶原流失、肤色不均",
        },
    },
    "Gut Cleanse Fat Loss B3 Probio（肠道益生菌）": {
        "ingredients": "多菌株益生菌、B3烟酸、膳食纤维、酵素",
        "selling_points": "多菌株配方、肠道健康、日本研发、日常调理",
        "target_concerns": {
            "18-34岁（小红书用户）": "肠胃不适、饮食不规律、体态管理",
            "35岁+（视频号用户）": "消化问题、代谢下降、体重管理",
        },
    },
}

# ============================================================
# 预写文案库（Demo 模式用，基于真实调研数据）
# ============================================================
DEMO_COPIES = {
    ("Vision Defense × Eyes Revitalize（护眼）", "小红书 · 18-34岁"): [
        {
            "text": (
                "每天对着电脑8小时的打工人看过来💻\n"
                "眼睛干到像撒了沙子？试试这颗小马基莓护眼丸\n"
                "日本研发的配方，叶黄素+玉米黄质双重守护\n"
                "颗粒超小，随餐吃完全不卡嗓子\n"
                "坚持一个月，眼睛没那么容易累了👀\n"
                "#护眼好物 #打工人必备 #日本保健品"
            ),
            "compliant": True,
        },
        {
            "text": (
                "姐妹们！这个护眼丸真的绝了🔥\n"
                "马基莓提取物，抗氧化天花板\n"
                "吃了两周感觉眼睛没那么干了\n"
                "而且颗粒很小！怕吞药的人放心冲\n"
                "日本品质，成分党必看✨\n"
                "#护眼推荐 #马基莓 #干眼救星"
            ),
            "compliant": False,
            "issues": [
                {"word": "绝了", "category": "夸大用语", "suggestion": "改为「让人惊喜」"},
                {"word": "天花板", "category": "绝对化用语", "suggestion": "改为「优质之选」"},
            ],
        },
        {
            "text": (
                "🌿 养生女孩的护眼日常\n"
                "早餐加一颗马基莓护眼丸\n"
                "叶黄素+玉米黄质，呵护眼部健康\n"
                "日本进口，小颗粒好吞咽\n"
                "屏幕党真的需要日常呵护～\n"
                "#护眼 #日本好物 #养生日常"
            ),
            "compliant": True,
        },
    ],
    ("Vision Defense × Eyes Revitalize（护眼）", "微信视频号 · 35岁+"): [
        {
            "text": (
                "过了35岁，眼睛越来越容易疲劳。\n"
                "很多朋友开始关注眼部健康，但不知道怎么选。\n"
                "这款裕生活护眼产品，采用马基莓提取物，\n"
                "搭配叶黄素和玉米黄质，帮助呵护眼部舒适。\n"
                "日本研发，品质值得信赖。\n"
                "每天一粒，给眼睛多一份关照。"
            ),
            "compliant": True,
        },
        {
            "text": (
                "很多朋友问我，眼睛干涩怎么办？\n"
                "推荐你试试这个！效果真的最好👍\n"
                "吃了以后视力明显提升，不用戴眼镜了！\n"
                "100%有效，无效退款！\n"
                "赶紧下单吧！"
            ),
            "compliant": False,
            "issues": [
                {"word": "最好", "category": "绝对化用语", "suggestion": "改为「备受好评」"},
                {"word": "视力明显提升", "category": "功效宣称", "suggestion": "改为「感觉眼睛更舒适了」"},
                {"word": "不用戴眼镜了", "category": "功效宣称", "suggestion": "删除，不得暗示治疗"},
                {"word": "100%有效", "category": "虚假承诺", "suggestion": "改为「广受用户认可」"},
                {"word": "无效退款", "category": "虚假承诺", "suggestion": "删除"},
            ],
        },
    ],
    ("Natural Relax × Deep Sleep（助眠）", "小红书 · 18-34岁"): [
        {
            "text": (
                "加班到凌晨的打工人，你需要这个💤\n"
                "GABA+茶氨酸，帮助放松身心\n"
                "不是褪黑素那种强制关机，是自然困意～\n"
                "日本配方，温和不依赖\n"
                "坚持一周，入睡比以前顺畅多了\n"
                "#助眠好物 #打工人养生 #失眠星人"
            ),
            "compliant": True,
        },
        {
            "text": (
                "失眠的姐妹看过来！\n"
                "这个助眠丸治疗失眠真的牛🐮\n"
                "吃一颗立马睡着，根治我的失眠！\n"
                "再也不用吃药了，彻底解决！\n"
                "姐妹们冲啊！！！"
            ),
            "compliant": False,
            "issues": [
                {"word": "治疗失眠", "category": "功效宣称（保健食品禁止）", "suggestion": "改为「帮助放松入睡」"},
                {"word": "根治", "category": "功效宣称", "suggestion": "改为「从日常习惯入手改善」"},
                {"word": "立马睡着", "category": "虚假承诺", "suggestion": "改为「坚持使用感受变化」"},
                {"word": "彻底解决", "category": "保健食品特殊禁区", "suggestion": "删除"},
                {"word": "再也不用吃药了", "category": "医疗暗示", "suggestion": "删除"},
            ],
        },
    ],
    ("Natural Relax × Deep Sleep（助眠）", "微信视频号 · 35岁+"): [
        {
            "text": (
                "工作压力大，晚上翻来覆去睡不着？\n"
                "很多人选择硬扛，其实可以试试日常调理。\n"
                "裕生活助眠产品，含GABA和茶氨酸，\n"
                "帮助放松身心，维持良好睡眠节律。\n"
                "日本研发，天然成分，温和不依赖。\n"
                "好的睡眠，从每天一小步开始。"
            ),
            "compliant": True,
        },
    ],
    ("Glycation Free × Skin Rebound（抗糖护肤）", "小红书 · 18-34岁"): [
        {
            "text": (
                "奶茶戒不掉？那就从抗糖开始🧋→✨\n"
                "裕生活抗糖丸，日本专利配方\n"
                "胶原蛋白+透明质酸，由内而外呵护\n"
                "每天两颗，给皮肤多一份关爱\n"
                "清洁配方，日常安心吃～\n"
                "#抗糖 #护肤 #日本好物 #内服美容"
            ),
            "compliant": True,
        },
    ],
    ("Glycation Free × Skin Rebound（抗糖护肤）", "微信视频号 · 35岁+"): [
        {
            "text": (
                "随着年龄增长，皮肤状态大不如前。\n"
                "除了日常护肤，内调也很重要。\n"
                "裕生活抗糖护肤产品，含专利抗糖化成分，\n"
                "搭配胶原蛋白和透明质酸，帮助维持皮肤弹性。\n"
                "日本研发，清洁配方。\n"
                "爱美不分年龄，从内而外的呵护更持久。"
            ),
            "compliant": True,
        },
    ],
    ("Gut Cleanse Fat Loss B3 Probio（肠道益生菌）", "小红书 · 18-34岁"): [
        {
            "text": (
                "外卖吃多了，肠胃在抗议？🫠\n"
                "试试这个多菌株益生菌\n"
                "B3烟酸+膳食纤维+酵素，三重配方\n"
                "帮助维持肠道健康，日常调理好搭档\n"
                "日本配方，每天一条，肠胃舒服多了～\n"
                "#益生菌 #肠道健康 #打工人养生"
            ),
            "compliant": True,
        },
    ],
    ("Gut Cleanse Fat Loss B3 Probio（肠道益生菌）", "微信视频号 · 35岁+"): [
        {
            "text": (
                "过了40岁，代谢明显变慢。\n"
                "很多朋友开始关注肠道健康。\n"
                "裕生活益生菌，多菌株配方，\n"
                "搭配B3烟酸和膳食纤维，帮助日常调理。\n"
                "日本研发，品质值得信赖。\n"
                "肠道舒服了，整个人都轻松了。"
            ),
            "compliant": True,
        },
    ],
}


# ============================================================
# LLM 生成（当用户提供 API Key 时启用）
# ============================================================
def generate_copy_with_llm(product_name, platform, segment, api_key, base_url, model):
    product = PRODUCTS[product_name]
    concerns = product["target_concerns"].get(segment, "")

    if "小红书" in platform:
        tone = "轻松活泼、种草感、适当使用emoji、口语化"
        format_hint = "图文笔记风格，100字左右，带话题标签"
    else:
        tone = "专业温和、有信赖感、语速偏慢、科普向"
        format_hint = "口播脚本风格，150字左右，适合中年受众"

    prompt = f"""你是一位保健品品牌的社交媒体文案编辑。

品牌：裕生活（Yutakana Seikatsu），日本保健品品牌
产品：{product_name}
核心成分：{product['ingredients']}
产品卖点：{product['selling_points']}
目标人群：{segment}
该人群健康关注点：{concerns}
投放平台：{platform}
语气要求：{tone}
内容格式：{format_hint}

请生成3条营销文案。
重要约束：
1. 不得宣称任何功效或治疗效果
2. 不得使用绝对化用语（最好、第一、100%等）
3. 不得暗示医疗作用
4. 不得做虚假承诺（立竿见影、保证有效等）
5. 可以使用"帮助维持""呵护""日常调理"等温和表述
6. 每条文案用 --- 分隔"""

    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key, base_url=base_url)
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.8,
        )
        raw = response.choices[0].message.content
        copies = [c.strip() for c in raw.split("---") if c.strip()]
        return copies if copies else [raw]
    except Exception as e:
        return [f"API 调用失败：{str(e)}"]


# ============================================================
# Streamlit UI
# ============================================================
st.title("🌿 裕生活 AI 营销文案助手")
st.caption("Yutakana Seikatsu · 保健品合规文案生成与检测工具")

with st.sidebar:
    st.header("⚙️ 设置")
    mode = st.radio("运行模式", ["Demo 演示模式", "LLM API 模式"], index=0)

    if mode == "LLM API 模式":
        st.subheader("API 配置")
        api_key = st.text_input("API Key", type="password", value="", help="通义千问 / DeepSeek / 其他 OpenAI 兼容 API")
        base_url = st.text_input(
            "Base URL",
            value="https://dashscope.aliyuncs.com/compatible-mode/v1",
            help="通义千问默认地址，DeepSeek 用 https://api.deepseek.com/v1",
        )
        model = st.text_input("模型名称", value="qwen-plus")
    else:
        api_key = None
        base_url = None
        model = None
        st.info("💡 Demo 模式使用预写文案展示效果。\n切换到 LLM API 模式可实时生成文案。")

    st.divider()
    st.subheader("📋 合规规则")
    st.caption("基于《广告法》《保健食品广告审查暂行规定》")
    for cat, words in SENSITIVE_WORDS.items():
        with st.expander(f"{cat}（{len(words)}个）"):
            st.write("、".join(words))

st.divider()

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📝 文案输入")
    product_name = st.selectbox("选择产品", list(PRODUCTS.keys()))

    product_info = PRODUCTS[product_name]
    with st.expander("📦 产品信息"):
        st.write(f"**核心成分：** {product_info['ingredients']}")
        st.write(f"**卖点：** {product_info['selling_points']}")
        for seg, concerns in product_info["target_concerns"].items():
            st.write(f"**{seg}：** {concerns}")

    platform = st.selectbox("选择平台与人群", ["小红书 · 18-34岁", "微信视频号 · 35岁+"])

    if mode == "LLM API 模式":
        if st.button("🚀 生成文案", type="primary", use_container_width=True):
            if not api_key:
                st.error("请先填写 API Key")
            else:
                with st.spinner("正在生成文案..."):
                    copies = generate_copy_with_llm(product_name, platform, platform.split("（")[0] if "（" in platform else platform, api_key, base_url, model)
                    st.session_state["generated_copies"] = copies
    else:
        if st.button("🚀 获取示例文案", type="primary", use_container_width=True):
            key = (product_name, platform)
            if key in DEMO_COPIES:
                st.session_state["generated_copies"] = [c["text"] for c in DEMO_COPIES[key]]
            else:
                st.warning("该组合暂无预写文案，请切换到 LLM API 模式生成。")

with col2:
    st.subheader("🔍 合规检测")
    manual_text = st.text_area("手动输入文案进行检测", height=200, placeholder="在此粘贴或输入文案内容...")

    if st.button("🔎 检测合规性", use_container_width=True):
        if manual_text.strip():
            alerts = compliance_check(manual_text)
            if alerts:
                st.error(f"⚠️ 检测到 {len(alerts)} 处合规风险")
                for a in alerts:
                    st.warning(f"**「{a['word']}」** — {a['category']}\n💡 建议：{a['suggestion']}")
            else:
                st.success("✅ 未检测到合规风险")

st.divider()

if "generated_copies" in st.session_state and st.session_state["generated_copies"]:
    st.subheader("📄 生成结果与合规审核")
    for i, copy in enumerate(st.session_state["generated_copies"], 1):
        with st.container():
            st.markdown(f"**文案 {i}**")
            st.write(copy)

            alerts = compliance_check(copy)
            if alerts:
                st.error(f"⚠️ 检测到 {len(alerts)} 处合规风险")
                for a in alerts:
                    st.warning(f"**「{a['word']}」** — {a['category']}\n💡 建议：{a['suggestion']}")
            else:
                st.success("✅ 合规通过")

            st.divider()

st.divider()
st.subheader("📊 使用说明")
col_a, col_b, col_c = st.columns(3)
with col_a:
    st.metric("敏感词类别", f"{len(SENSITIVE_WORDS)} 类")
    total_words = sum(len(v) for v in SENSITIVE_WORDS.values())
with col_b:
    st.metric("敏感词总数", f"{total_words} 个")
with col_c:
    st.metric("产品数量", f"{len(PRODUCTS)} 款")

with st.expander("📖 关于合规规则"):
    st.markdown("""
**合规规则来源：**
- 《中华人民共和国广告法》（2021修正）
- 《保健食品广告审查暂行规定》
- 《食品安全法》相关条款

**保健食品广告核心禁区：**
1. 不得宣称或暗示治疗功效
2. 不得使用绝对化用语
3. 不得利用专家、患者名义做证明
4. 不得声称安全无毒副作用
5. 不得含有"无效退款""保险公司保险"等承诺

**双层审核机制：**
- 第一层：关键词规则匹配（本工具已实现）
- 第二层：LLM 语义级判断（需 API 模式，识别未命中关键词但语义违规的表述）
    """)
