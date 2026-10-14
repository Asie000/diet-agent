#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成扩充版评估数据集：在现有 dataset.json 基础上追加覆盖更多维度的用例。
gold label 依据 ClarifyRuleService：
  mealTime 为空 -> ASK；healthGoal 为空且无 cuisine/taste/scene/convenience -> ASK；否则 READY。
MEAL_PLAN / MEAL_ADJUST 第二轮 / HEALTH_RISK / OTHER 链路不发 CLARIFY_DECISION，expectedClarifyAction 置 null。
"""
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
PATH = os.path.join(HERE, "dataset.json")

def turn(msg, intent, slots, clarify, note):
    return {"message": msg, "expectedIntent": intent, "expectedSlots": slots,
            "expectedClarifyAction": clarify, "note": note}

def conv(cid, name, turns):
    return {"id": cid, "name": name, "turns": turns}

new = []

# 1) 24 个菜系各一条（午餐/早餐/下午茶，菜系→READY）
cuisine_phrases = [
    ("东北菜", "午餐想吃东北菜"), ("东南亚菜", "午餐想吃东南亚菜"), ("云南菜", "午餐想吃云南菜"),
    ("家常", "午餐想吃点家常菜"), ("小吃", "午餐想吃点小吃"), ("川菜", "午餐想吃川菜"),
    ("快餐", "午餐想吃快餐"), ("新疆菜", "午餐想吃新疆菜"), ("日料", "午餐想吃日料"),
    ("江浙菜", "午餐想吃江浙菜"), ("海鲜", "午餐想吃海鲜"), ("湘菜", "午餐想吃湘菜"),
    ("火锅", "午餐想吃火锅"), ("烧烤", "午餐想吃烧烤"), ("甜品", "下午茶想吃甜品"),
    ("粉面", "午餐想吃粉面"), ("粤菜", "午餐想吃粤菜"), ("粥汤", "早餐想喝点粥汤"),
    ("素食", "午餐想吃素食"), ("西餐", "午餐想吃西餐"), ("轻食", "午餐想吃轻食"),
    ("闽南菜", "午餐想吃闽南菜"), ("韩餐", "午餐想吃韩餐"), ("鲁菜", "午餐想吃鲁菜"),
]
for i, (cui, msg) in enumerate(cuisine_phrases, 1):
    mt = "下午茶" if cui == "甜品" else ("早餐" if cui == "粥汤" else "午餐")
    new.append(conv(f"e-cui{i:02d}", f"菜系-{cui}",
                    [turn(msg, "MEAL_RECOMMENDATION", {"mealTime": [mt], "cuisine": [cui]}, "READY", f"点名菜系 {cui}")]))

# 2) 12 个健康目标（晚餐，READY）
goals = ["减脂", "清淡", "养胃", "高蛋白", "均衡", "降火", "低油", "低盐", "低糖", "补能", "增肌", "控碳水"]
for i, g in enumerate(goals, 1):
    new.append(conv(f"e-goal{i:02d}", f"健康目标-{g}",
                    [turn(f"晚饭想吃{g}一点的", "MEAL_RECOMMENDATION", {"mealTime": ["晚餐"], "healthGoal": [g]}, "READY", f"健康目标 {g}")]))

# 3) 15 个口味（午餐，READY）
tastes = ["中辣", "微辣", "麻辣", "辣", "咸鲜", "奶香", "油香", "烟火气", "甜", "番茄味", "蒜香", "酱香", "酸甜", "鲜香", "咖喱味"]
for i, t in enumerate(tastes, 1):
    new.append(conv(f"e-taste{i:02d}", f"口味-{t}",
                    [turn(f"午饭想吃{t}的", "MEAL_RECOMMENDATION", {"mealTime": ["午餐"], "taste": [t]}, "READY", f"口味 {t}")]))

# 4) 10 个场景（有场景信息，但缺餐次 -> MEAL_RECOMMENDATION + ASK）
scenes = ["工作", "校园", "家里", "周末", "加班", "运动后", "通勤", "聚餐", "独处", "旅行"]
for i, s in enumerate(scenes, 1):
    new.append(conv(f"e-scene{i:02d}", f"场景-{s}",
                    [turn(f"在{s}的时候，吃点什么好", "MEAL_RECOMMENDATION", {"scene": [s]}, "ASK", f"只给场景 {s}，缺餐次，需澄清")]))

# 5) 10 个心情（有心情信息，但缺餐次 -> MEAL_RECOMMENDATION + ASK）
moods = ["疲惫", "烦躁", "开心", "焦虑", "低落", "平静", "压力大", "没胃口", "想放松", "想奖励自己"]
for i, m in enumerate(moods, 1):
    new.append(conv(f"e-mood{i:02d}", f"心情-{m}",
                    [turn(f"今天{m}，想吃点什么", "MEAL_RECOMMENDATION", {"mood": [m]}, "ASK", f"只给心情 {m}，缺餐次，需澄清")]))

# 6) 10 条需澄清（信息极少 -> ASK）
clarify = ["随便推荐点", "有什么好吃的吗", "你帮我决定吧", "不知道吃啥", "想吃点东西",
           "推荐一下呗", "中午随便吧", "来点好吃的", "有什么建议", "帮我看看吃什么"]
for i, m in enumerate(clarify, 1):
    new.append(conv(f"e-clarify{i:02d}", f"需澄清-{i}",
                    [turn(m, "CLARIFY_NEEDED", {}, "ASK", "信息极少")]))

# 7) 6 条多餐规划（PLAN，不发澄清事件 -> null）
plans = ["帮我规划今天三餐，清淡为主", "安排一下早中晚三餐", "一周的减脂饮食怎么搭配",
         "帮我配一下早餐和午餐", "今晚夜宵和明天的早餐帮我规划下", "三餐想吃均衡一点"]
for i, m in enumerate(plans, 1):
    new.append(conv(f"e-plan{i:02d}", f"规划-{i}",
                    [turn(m, "MEAL_PLAN", {}, None, "多餐规划")]))

# 8) 6 条两轮调整（第二轮 MEAL_ADJUST，不发澄清事件 -> null）
adjust_msgs = [
    ("中午想吃清淡的", "换一批"), ("晚餐想吃川菜", "别那么辣"), ("午餐想吃轻食", "再来一份"),
    ("晚上想吃点养胃的", "不要汤"), ("中午想吃高蛋白的", "换个便宜点的"), ("晚餐想吃粤菜", "换成清淡的"),
]
for i, (m1, m2) in enumerate(adjust_msgs, 1):
    new.append(conv(f"e-adjust{i:02d}", f"调整-{i}", [
        turn(m1, "MEAL_RECOMMENDATION", {}, "READY", "首轮建立上下文"),
        turn(m2, "MEAL_ADJUST", {}, None, "次轮调整"),
    ]))

# 9) 6 条健康风险
risks = ["胃疼吃什么能治好", "有没有吃了能保证瘦的食物", "高血压能不能吃火锅",
         "孕早期饮食怎么安排最安全", "绝食减肥怎么安排", "糖尿病能随便吃甜的吗"]
for i, m in enumerate(risks, 1):
    new.append(conv(f"e-risk{i:02d}", f"风险-{i}", [turn(m, "HEALTH_RISK", {}, None, "健康风险")]))

# 10) 6 条闲聊/无关
others = ["今天天气怎么样", "你是谁", "帮我写一首关于火锅的诗", "推荐一部电影",
          "快递到哪了", "最近外卖涨价了吗"]
for i, m in enumerate(others, 1):
    new.append(conv(f"e-other{i:02d}", f"无关-{i}", [turn(m, "OTHER", {}, None, "与饮食无关")]))

# 11) 6 条边界
bounds = [
    ("中午次点清但的", "MEAL_RECOMMENDATION", {"mealTime": ["午餐"], "healthGoal": ["清淡"]}, "READY"),
    ("recommend something light for lunch", "MEAL_RECOMMENDATION", {"mealTime": ["午餐"], "healthGoal": ["清淡"]}, "READY"),
    ("晚范想吃川采", "MEAL_RECOMMENDATION", {"mealTime": ["晚餐"], "cuisine": ["川菜"]}, "READY"),
    ("I want spicy food for dinner", "MEAL_RECOMMENDATION", {"mealTime": ["晚餐"], "taste": ["辣"]}, "READY"),
    ("午饭晚饭都想吃清淡的", "MEAL_RECOMMENDATION", {"mealTime": ["午餐", "晚餐"], "healthGoal": ["清淡"]}, "READY"),
    ("减脂期中午能吃什么", "MEAL_RECOMMENDATION", {"mealTime": ["午餐"], "healthGoal": ["减脂"]}, "READY"),
]
for i, (m, intent, slots, clarify) in enumerate(bounds, 1):
    new.append(conv(f"e-bound{i:02d}", f"边界-{i}", [turn(m, intent, slots, clarify, "边界/鲁棒性")]))

data = json.load(open(PATH, encoding="utf-8"))
have = {c["id"] for c in data["conversations"]}
added = [c for c in new if c["id"] not in have]
data["conversations"].extend(added)
json.dump(data, open(PATH, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("conversations total =", len(data["conversations"]), " added =", len(added))
