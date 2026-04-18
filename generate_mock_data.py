"""
Mock Dataset Generator for LoRA Ad Creative Copy System
Generates 400 records: Beauty(150), Fashion(150), Game(100)
"""

import json
import random
from pathlib import Path

# Industry pain points and selling points
INDUSTRIES = {
    "industry_beauty": {
        "pain_points": ["干燥", "敏感", "色斑", "皱纹", "油光", "毛孔粗大", "泛红", "痘痘", "黑头", "肤色暗沉"],
        "selling_points": ["补水保湿", "温和不刺激", "美白淡斑", "抗衰老", "控油遮瑕", "舒缓修护", "深层清洁", "提亮肤色", "紧致肌肤", "清爽控油"],
        "products": ["精华液", "面霜", "乳液", "面膜", "爽肤水", "洁面乳", "眼霜", "防晒霜", "妆前乳", "卸妆油"],
        "style": ["精致", "专业", "温和", "信赖", "自然"],
        "copy_tones": ["种草推荐", "成分党", "闺蜜分享", "专家科普"]
    },
    "industry_fashion": {
        "pain_points": ["显胖", "不合身", "起球", "褪色", "不时尚", "缩水", "闷热", "掉色", "面料硬", "开线"],
        "selling_points": ["显瘦", "百搭", "耐穿", "透气", "时尚潮流", "高腰收腰", "休闲舒适", "做工精细", "修身", "不易变形"],
        "products": ["连衣裙", "T恤", "牛仔裤", "外套", "衬衫", "卫衣", "短裙", "西装裤", "毛衣", "风衣"],
        "style": ["潮流", "实用", "品质", "简约", "优雅"],
        "copy_tones": ["穿搭分享", "搭配教程", "时尚博主", "买家秀"]
    },
    "industry_game": {
        "pain_points": ["卡顿", "掉线", "枯燥", "氪金", "画质差", "玩法单一", "升级慢", "匹配慢", "队友坑", "缺乏激情"],
        "selling_points": ["流畅", "画质高清", "玩法多样", "福利多", "社交强", "零氪金", "公平竞技", "热血战斗", "沉浸体验", "自由交易"],
        "products": ["RPG游戏", "策略游戏", "竞技游戏", "休闲游戏", "卡牌游戏", "射击游戏", "MOBA游戏", "MMORPG", "模拟经营", "动作冒险"],
        "style": ["热血", "激情", "沉浸", "刺激", "荣耀"],
        "copy_tones": ["游戏主播", "攻略达人", "玩家社区", "官方爆料"]
    }
}

COPY_TYPES = ["title", "detail", "banner", "short_video"]


def generate_sample(industry: str, idx: int) -> dict:
    """Generate sample for specific industry"""
    config = INDUSTRIES[industry]
    pain = random.choice(config["pain_points"])
    sell = random.choice(config["selling_points"])
    product = random.choice(config["products"])
    style = random.choice(config["style"])
    tone = random.choice(config["copy_tones"])
    copy_type = random.choice(COPY_TYPES)

    if industry == "industry_beauty":
        low_ctr_templates = [
            f"这是一款很好的{product}。",
            f"我们的{product}效果不错。",
            f"{product}，很多人都在用。",
            f"产品质量很好，推荐给大家。",
            f"用了感觉还可以。",
            f"价格实惠，值得购买。",
            f"{product}，适合各种肤质。",
            f"效果因人而异。"
        ]
        high_ctr_templates = [
            f"告别{pain}！{product}蕴含珍稀{sell}成分，一抹即融，深层渗透肌肤底层，重现少女般嫩滑光泽！限时折扣！",
            f"敏感肌也能安心用的{product}！0刺激、0添加，dermatologist推荐，专为脆弱肌研发，轻松应对{pain}，让你重拾自信素颜美！",
            f"{pain}克星来了！{product}添加专利{sell}配方，7天见证肌肤蜕变，真实用户亲测有效！引爆朋友圈的高口碑神器！",
            f"明星同款{product}！一次解决{pain}困扰，蕴含{sell}精华，质地轻盈不黏腻，轻松打造透亮无瑕肌！限时秒杀，手慢无！",
            f"解锁冻龄肌密！{product}富含6000倍活性成分，直击{pain}根源，28天焕活少女肌，重回18岁紧致状态！",
            f"{tone}亲测！真的能{sell}，困扰多年的{pain}终于有救了！",
            f"换季必备！专为{pain}肌研发的{sell}神器，回购率超90%！",
            f"OMG！{pain}救星来了！{sell}效果绝了，用完皮肤状态美到爆炸！"
        ]

    elif industry == "industry_fashion":
        low_ctr_templates = [
            f"这是一款{product}。",
            f"衣服质量还可以。",
            f"穿上挺好看的。",
            f"尺码标准，面料普通。",
            f"价格合理。",
            f"挺百搭的一款{product}。",
            f"适合日常穿着。",
            f"没什么特别的。"
        ]
        high_ctr_templates = [
            f"显瘦10斤的秘密！这款{product}采用显瘦剪裁设计，轻松遮盖{pain}，上身效果惊艳！{sell}面料，舒适透气一整天，百搭所有场合！",
            f"衣橱里永远缺一件的{product}！2024流行趋势，{sell}面料升级，质感满满，轻松应对{pain}问题，一件解锁N种穿搭可能！",
            f"小个子显高、大个子显瘦的{product}！微胖MM最爱的遮肉神器，{sell}面料透气不闷热，彻底告别{pain}烦恼！",
            f"衣柜必备的万能{product}！无论你是{pain}困扰还是追求{sell}，一件满足所有需求！搭配任何单品都高级感十足！",
            f"让你美到尖叫的{product}！独特{sell}设计，专为亚洲女性身形定制，彻底解决{pain}，穿上就是高级感本人！",
            f"{tone}强推！谁穿谁好看的{sell}神裤，轻松驾驭各种{pain}困扰！",
            f"紧急种草！穿上秒变时髦精，{sell}效果绝了，{pain}姐妹的福音！",
            f"{tone}分享 | 这套{sell}穿搭绝了！完美解决{pain}，谁穿谁美！"
        ]

    else:  # industry_game
        game_type = product
        low_ctr_templates = [
            f"这是一款{game_type}。",
            f"游戏还可以。",
            f"画质一般，玩法普通。",
            f"氪金程度可以接受。",
            f"升级速度正常。",
            f"福利活动一般。",
            f"公平竞技。",
            f"总体还行。"
        ]
        high_ctr_templates = [
            f"告别{pain}！2024必玩{game_type}，{sell}玩法颠覆想象，超燃打击感让你欲罢不能！万元福利免费领，登录即送绝版时装！",
            f"再也回不去的沉浸体验！{game_type}震撼来袭，{sell}引擎打造极致画面，{pain}？不存在的！全民狂欢，组队就送稀有道具！",
            f"零氪金也能称霸全服！这款{game_type}彻底解决{pain}问题，{sell}设定让新手也能快速成长！史诗级福利，首充任意金额得20倍返还！",
            f"全网玩家疯狂安利的{game_type}！{sell}系统重磅上线，{pain}已成过去式！超多副本、超强BOSS，等你来挑战！",
            f"一款让人上瘾的{game_type}！{sell}玩法嗨翻全场，{pain}全部优化，体验流畅到爆炸！开服7天登录送传说英雄！",
            f"{tone}都在玩的游戏！{sell}系统让{pain}成为历史，零氪也能成大神！",
            f"画质炸裂！{style}级游戏体验，{sell}效果拉满，{pain}玩家强烈推荐！",
            f"新版本爆料！{sell}新玩法上线，解决{pain}问题，错过等一年！"
        ]

    return {
        "id": f"{industry}_{idx:04d}",
        "source_content": random.choice(low_ctr_templates),
        "target_content": random.choice(high_ctr_templates),
        "industry_tag": industry,
        "copy_type": copy_type,
        "source": "mock_data"
    }


def generate_mock_dataset(output_dir: str = "."):
    """Generate complete mock dataset"""
    dataset = []

    # Beauty: 150 samples
    for i in range(150):
        dataset.append(generate_sample("industry_beauty", i))

    # Fashion: 150 samples
    for i in range(150):
        dataset.append(generate_sample("industry_fashion", i))

    # Game: 100 samples
    for i in range(100):
        dataset.append(generate_sample("industry_game", i))

    # Shuffle dataset
    random.seed(42)
    random.shuffle(dataset)

    # Re-index after shuffle
    for idx, item in enumerate(dataset):
        item["id"] = f"sample_{idx:04d}"

    output_path = Path(output_dir)

    # Write to JSONL
    jsonl_file = output_path / "mock_dataset.jsonl"
    with open(jsonl_file, "w", encoding="utf-8") as f:
        for item in dataset:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    # Write to JSON
    json_file = output_path / "mock_dataset.json"
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(dataset, f, ensure_ascii=False, indent=2)

    # Generate statistics
    stats = {
        "total": len(dataset),
        "by_industry": {
            "industry_beauty": sum(1 for x in dataset if x["industry_tag"] == "industry_beauty"),
            "industry_fashion": sum(1 for x in dataset if x["industry_tag"] == "industry_fashion"),
            "industry_game": sum(1 for x in dataset if x["industry_tag"] == "industry_game"),
        },
        "by_copy_type": {ct: sum(1 for x in dataset if x["copy_type"] == ct) for ct in COPY_TYPES}
    }

    stats_file = output_path / "dataset_stats.json"
    with open(stats_file, "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)

    print(f"Generated {len(dataset)} mock samples:")
    print(f"  - Beauty: 150")
    print(f"  - Fashion: 150")
    print(f"  - Game: 100")
    print(f"Output: {json_file.absolute()}")
    print(f"Output: {jsonl_file.absolute()}")
    print(f"Stats: {stats_file.absolute()}")

    return dataset


if __name__ == "__main__":
    generate_mock_dataset()
