import json
import random

BEAUTY_TEMPLATES = {
    "pain_points": ["干燥", "敏感", "色斑", "皱纹", "油光", "毛孔粗大", "痘痘", "黑头", "肤色暗沉", "脱皮"],
    "benefits": ["补水保湿", "温和不刺激", "美白淡斑", "抗衰老", "控油遮瑕", "深层清洁", "舒缓修复", "提亮肤色", "紧致肌肤", "清爽控油"],
    "styles": ["精致", "专业", "温和", "信赖", "自然", "安全"],
    "products": ["精华液", "面霜", "乳液", "面膜", "爽肤水", "洁面乳", "眼霜", "防晒霜", "妆前乳", "卸妆油"],
    "copy_types": ["title", "detail", "banner", "short_video"]
}

FASHION_TEMPLATES = {
    "pain_points": ["显胖", "不合身", "起球", "褪色", "不时尚", "缩水", "掉色", "面料硬", "不透气", "开线"],
    "benefits": ["显瘦", "百搭", "耐穿", "透气", "时尚潮流", "修身", "舒适", "不易变形", "高性价比", "潮流设计"],
    "styles": ["潮流", "实用", "品质", "简约", "时尚", "优雅"],
    "products": ["连衣裙", "T恤", "牛仔裤", "外套", "衬衫", "卫衣", "短裙", "西装裤", "毛衣", "风衣"],
    "copy_types": ["title", "detail", "banner", "short_video"]
}

GAME_TEMPLATES = {
    "pain_points": ["卡顿", "掉线", "枯燥", "氪金", "画质差", "玩法单一", "升级慢", "匹配慢", "队友坑", "缺乏激情"],
    "benefits": ["流畅", "画质高清", "玩法多样", "福利多", "社交强", "升级快", "公平竞技", "热血战斗", "沉浸体验", "自由交易"],
    "styles": ["热血", "激情", "沉浸", "刺激", "荣耀", "史诗"],
    "products": ["RPG游戏", "策略游戏", "竞技游戏", "休闲游戏", "卡牌游戏", "射击游戏", "MOBA游戏", "MMORPG", "模拟经营", "动作冒险"],
    "copy_types": ["title", "detail", "banner", "short_video"]
}

LOW_CTR_TEMPLATES = {
    "beauty": [
        "这是一款很好的{product}。",
        "我们的{product}效果不错。",
        "{product}，很多人都在用。",
        "产品质量很好，推荐给大家。",
        "用了感觉还可以。",
        "价格实惠，值得购买。",
        "{product}，适合各种肤质。",
        "效果因人而异。"
    ],
    "fashion": [
        "这是一款{product}。",
        "衣服质量还可以。",
        "穿上挺好看的。",
        "尺码标准，面料普通。",
        "价格合理。",
        "挺百搭的一款{product}。",
        "适合日常穿着。",
        "没什么特别的。"
    ],
    "game": [
        "这是一款{game_type}。",
        "游戏还可以。",
        "画质一般，玩法普通。",
        "氪金程度可以接受。",
        "升级速度正常。",
        "福利活动一般。",
        "公平竞技。",
        "总体还行。"
    ]
}

HIGH_CTR_TEMPLATES = {
    "beauty": [
        "告别{point}！{product}蕴含珍稀{benefit}成分，一抹即融，深层渗透肌肤底層，重现少女般嫩滑光泽！限时折扣，倒计时开始！",
        "敏感肌也能安心用的{product}！0刺激、0添加， dermatologist推荐，专为脆弱肌研发，轻松应对{point}，让你重拾自信素颜美！",
        "{point}克星来了！{product}添加专利{benefit}配方，7天见证肌肤蜕变，真实用户亲测有效！引爆朋友圈的高口碑神器！",
        "明星同款{product}！一次解决{point}困扰，蕴含{benefit}精华，质地轻盈不黏腻，轻松打造透亮无瑕肌！限时秒杀，手慢无！",
        "解锁冻龄肌密！{product}富含6000倍活性成分，直击{point}根源，28天焕活少女肌，重回18岁紧致状态！"
    ],
    "fashion": [
        "显瘦10斤的秘密！这款{product}采用显瘦剪裁设计，轻松遮盖{point}，上身效果惊艳！{benefit}面料，舒适透气一整天，百搭所有场合！",
        "衣橱里永远缺一件的{product}！2024流行趋势，{benefit}面料升级，质感满满，轻松应对{point}问题，一件解锁N种穿搭可能！",
        "小个子显高、大个子显瘦的{product}！微胖MM最爱的遮肉神器，{benefit}面料透气不闷热，彻底告别{point}烦恼！",
        "衣柜必备的万能{product}！无论你是{point}困扰还是追求{benefit}，一件满足所有需求！搭配任何单品都高级感十足！",
        "让你美到尖叫的{product}！独特{benefit}设计，专为亚洲女性身形定制，彻底解决{point}，穿上就是高级感本人！"
    ],
    "game": [
        "告别{point}！2024必玩{game_type}，{benefit}玩法颠覆想象，超燃打击感让你欲罢不能！万元福利免费领，登录即送绝版时装！",
        "再也回不去的沉浸体验！{game_type}震撼来袭，{benefit}引擎打造极致画面，{point}？不存在的！全民狂欢，组队就送稀有道具！",
        "零氪金也能称霸全服！这款{game_type}彻底解决{point}问题，{benefit}设定让新手也能快速成长！史诗级福利，首充任意金额得20倍返还！",
        "全网玩家疯狂安利的{game_type}！{benefit}系统重磅上线，{point}已成过去式！超多副本、超强BOSS，等你来挑战！限时抢注，SSR必得！",
        "一款让人上瘾的{game_type}！{benefit}玩法嗨翻全场，{point}全部优化，体验流畅到爆炸！开服7天登录送传说英雄，快来加入！"
    ]
}

def generate_beauty_data(count=150):
    data = []
    for i in range(count):
        template_set = random.choice(LOW_CTR_TEMPLATES["beauty"])
        product = random.choice(BEAUTY_TEMPLATES["products"])
        source = template_set.format(product=product, point=random.choice(BEAUTY_TEMPLATES["pain_points"]))

        target_templates = random.choice(HIGH_CTR_TEMPLATES["beauty"])
        target = target_templates.format(
            product=product,
            point=random.choice(BEAUTY_TEMPLATES["pain_points"]),
            benefit=random.choice(BEAUTY_TEMPLATES["benefits"])
        )

        data.append({
            "id": f"beauty_{i+1:04d}",
            "source_content": source,
            "target_content": target,
            "industry_tag": "industry_beauty",
            "copy_type": random.choice(BEAUTY_TEMPLATES["copy_types"]),
            "source": "mock_data"
        })
    return data

def generate_fashion_data(count=150):
    data = []
    for i in range(count):
        template_set = random.choice(LOW_CTR_TEMPLATES["fashion"])
        product = random.choice(FASHION_TEMPLATES["products"])
        source = template_set.format(product=product, point=random.choice(FASHION_TEMPLATES["pain_points"]))

        target_templates = random.choice(HIGH_CTR_TEMPLATES["fashion"])
        target = target_templates.format(
            product=product,
            point=random.choice(FASHION_TEMPLATES["pain_points"]),
            benefit=random.choice(FASHION_TEMPLATES["benefits"])
        )

        data.append({
            "id": f"fashion_{i+1:04d}",
            "source_content": source,
            "target_content": target,
            "industry_tag": "industry_fashion",
            "copy_type": random.choice(FASHION_TEMPLATES["copy_types"]),
            "source": "mock_data"
        })
    return data

def generate_game_data(count=100):
    data = []
    for i in range(count):
        template_set = random.choice(LOW_CTR_TEMPLATES["game"])
        game_type = random.choice(GAME_TEMPLATES["products"])
        source = template_set.format(game_type=game_type, point=random.choice(GAME_TEMPLATES["pain_points"]))

        target_templates = random.choice(HIGH_CTR_TEMPLATES["game"])
        target = target_templates.format(
            game_type=game_type,
            point=random.choice(GAME_TEMPLATES["pain_points"]),
            benefit=random.choice(GAME_TEMPLATES["benefits"])
        )

        data.append({
            "id": f"game_{i+1:04d}",
            "source_content": source,
            "target_content": target,
            "industry_tag": "industry_game",
            "copy_type": random.choice(GAME_TEMPLATES["copy_types"]),
            "source": "mock_data"
        })
    return data

def main():
    all_data = []
    all_data.extend(generate_beauty_data(150))
    all_data.extend(generate_fashion_data(150))
    all_data.extend(generate_game_data(100))

    random.shuffle(all_data)

    output_file = "mock_dataset.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)

    print(f"Generated {len(all_data)} mock data entries")
    print(f"Saved to: {output_file}")
    print(f"  - Beauty: 150 entries")
    print(f"  - Fashion: 150 entries")
    print(f"  - Game: 100 entries")

    output_jsonl = "mock_dataset.jsonl"
    with open(output_jsonl, "w", encoding="utf-8") as f:
        for item in all_data:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    print(f"Also saved to: {output_jsonl}")

if __name__ == "__main__":
    main()