#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""卫生用品标签 / 宣传物料违禁词扫描器（第一道筛子，非最终合规结论）

用法:
    python3 label_scan.py <产品类别> <文本文件或目录> [...] [-o 报告路径]

产品类别（必填，决定用哪套禁词表）:
    pad      卫生巾/护垫/卫生纸/尿布尿裤/隔尿垫/护理垫
    wetwipe  普通湿巾（人体用）
    wettoilet 湿厕纸/擦便式湿巾（不是消毒产品，杀菌宣称按 T/CTAPI 009 / T/CNITA 09113 双线判定）
    sanit    卫生湿巾
    antibac  抗（抑）菌制剂、抗菌/抑菌卫生用品
    ad       广告/直播口播/详情页文案（仅跑广告法通用规则，不选品类禁词）

示例:
    python3 label_scan.py pad label.txt detail_page.html
    python3 label_scan.py antibac /tmp/product-copy/ -o report.txt
    python3 label_scan.py ad livestream_script.txt   # 直播口播稿

判定原则:
    禁词表命中 = 必须人工复核的候选违规，不是终局结论（如「伤口」可能出现在
    正常注意事项中）。反向扫描只能抓"写了不该写的"，抓不到"漏写必标项"——
    必标项仍按 references/audit-checklist.md 逐项核对；宣称权限与罚则见
    references/advertising-claims.md。

禁则依据:
    GB 15979-2024 / GB 38598-2020 / 卫监督发〔2005〕426号 标签禁则
    《广告法》第九条（绝对化用语）、第十七条（医疗用语）、第二十八条（虚假广告）
    《消毒管理办法》第三十一条第二款（不得暗示疾病治疗效果）
    中国广告协会《卫生巾广告自律规则》（中广协〔2008〕62号）
"""
import re
import sys
import os

BANNED = {
    "pad": {
        "GB38598 卫生巾类标签禁词": ["消毒", "灭菌", "除菌", "杀菌"],
        "药物/医疗暗示": ["药物", "药妆", "药用级"],
        "功效禁词": ["止带", "除湿", "润燥", "止痒", "抗炎", "消炎", "杀精子", "避孕"],
        "疗效夸大": ["疗效", "治疗"],
    },
    "wetwipe": {
        "GB38598 湿巾标签禁词": ["消毒", "灭菌", "除菌", "杀菌"],
        "抗（抑）菌宣称": ["抗菌", "抑菌"],
        "功效禁词/医疗": ["药物", "高效", "预防性病", "治疗疾病", "抗炎", "消炎", "缓解症状"],
    },
    "wettoilet": {
        # 湿厕纸（擦便式湿巾）：不是消毒产品、不打"消"字号，因此**不适用**
        # GB 38598 湿巾/卫生湿巾的"杀菌/抗菌/抑菌"标签禁则；杀菌宣称走
        # T/CTAPI 009-2026 / T/CNITA 09113-2024 的杀菌率双线判定（载体法 ≥90%
        # 或悬液法 ≥99%），有报告即可标，不能拿消毒产品禁词表判死。
        # 真正要抓的是：① 自称消毒产品 / 暗示医疗；② 品类名误用（把不可
        # 冲散产品标成"湿厕纸"，T/CNITA 09113 4.2.2）；③ 医疗与疗效暗示。
        "消毒产品身份误用": ["卫消证字", "消字号", "卫生湿巾", "消毒湿巾"],
        "医疗用语/混淆": ["医用级", "医学级", "医护级", "临床验证", "临床证明"],
        "功效禁词/医疗": ["药物", "药妆", "药用级", "高效", "预防性病", "治疗疾病",
                        "抗炎", "消炎", "缓解症状", "止痒"],
        "疗效夸大": ["疗效", "治愈"],
        "不可冲散却标湿厕纸": ["可冲散性", "可丢入马桶", "倒入马桶", "直冲马桶", "马桶可冲"],
    },
    "sanit": {
        "GB38598 卫生湿巾标签禁词": ["消毒", "灭菌", "抑菌", "除菌"],
        "功效禁词/医疗": ["药物", "高效", "预防性病", "治疗疾病", "抗炎", "消炎", "缓解症状"],
        "名称禁含抗菌": ["抗菌"],
    },
    "antibac": {
        "医疗/疗效": ["抗炎", "消炎", "治疗", "疗效", "缓解症状", "疾病症状", "预防性病", "治愈"],
        "消毒/杀菌夸大": ["高效", "消毒", "灭菌", "除菌", "广谱", "速效", "杀精子", "避孕"],
        "禁用药物成分": ["抗生素", "激素", "抗真菌药"],
        "禁用部位": ["足部", "眼睛", "指甲", "腋部", "头皮", "头发", "鼻黏膜", "肛肠"],
        "疗程暗示": ["为一疗程", "遵医嘱", "防止复发", "伤口愈合", "辅助配合药物"],
        "破损皮肤黏膜": ["破损皮肤", "破损黏膜", "伤口"],
    },
    "ad": {},  # 仅广告法通用规则
}

# 通用规则：全品类 / 全场景都要扫（标签、详情页、直播口播）
GENERIC_WORDS = {
    "广告法第九条 绝对化用语": [
        "最佳", "最高级", "国家级", "顶级", "最强", "最好", "最优",
        "销量第一", "全网第一", "最安全", "最舒适", "最透气", "最强吸收",
        "最",   # 兜底：命中后人工复核（可能出现在检测结论等正常语境）
    ],
    "疾病名称": ["牛皮癣", "神经性皮炎", "脂溢性皮炎", "阴道炎", "宫颈炎", "宫颈糜烂", "湿疹", "脚气", "痔疮"],
    "医疗用语/混淆": ["医护级", "医用级", "医学级", "临床验证", "临床证明", "医院同款", "药物卫生巾"],
    "无依据抑菌宣称": ["抑菌透气", "抗菌防臭", "抗菌防异味"],
    "菌群/生态无依据宣称": ["菌群平衡", "平衡菌群", "微生态", "有益菌", "益生菌", "后生元", "促生弱酸"],
    "祛味除臭宣称": ["祛味", "除臭", "防异味", "去异味"],
    "物理隔菌与抑菌混淆": ["物理隔菌", "隔菌", "阻隔有害菌"],
    "自造概念误导": ["食品级", "可食用级", "食用级"],
    "同业贬低（商业诋毁）": ["别家", "其他品牌都", "别人家都有", "只有我们"],
    "特定人群无依据": ["孕妇专用", "婴儿也能用", "产妇可用"],
    "零添加/绝对化否定": ["零添加", "无任何化学成分", "纯天然无添加"],
}

GENERIC_REGEX = {
    # 「动词 + 妇科/炎症/感染/瘙痒/异味/白带/痛经」等疗效暗示组合（广告法第十七条第一层）
    "妇科疗效暗示": r"(预防|改善|缓解|治疗|消除|摆脱|告别)[^。；，,！!\n]{0,8}(妇科|炎症|感染|瘙痒|异味|白带|宫颈|宫寒|痛经)|(消炎|止痒|抗炎)",
    # 「调节/平衡 + 菌群/微生态/酸碱/私处」等暗示生理功效的组合
    "生理功效暗示": r"(调节|平衡|改善|调理)[^。；，,！!\n]{0,4}(菌群|微生态|酸碱|私处|阴道|生理)",
    # 医疗背书 / 人设暗示
    "医疗背书暗示": r"(医生|医师|医院|专家)(推荐|认证|背书|同款)|临床(验证|证明|测试)[^。；，,\n]{0,6}(治疗|疗效|抑菌|杀菌)",
    # 长效抑菌（需长效抑菌性能报告支撑）
    "长效抑菌宣称": r"长效抑菌|持久抑菌|持续抑菌|全天抑菌|24\s*小时抑菌",
    # 「修复/愈合」等医疗用语（注意排除"再生纤维素/再生纸/再生纤维"等原料正式名称）
    "修复愈合用语": r"(私处|私密|黏膜|皮肤)?(修复|自愈|愈合)",
    # 「再生」类宣称（排除再生纤维素、再生纸、再生纤维三项法定原料名称）
    "组织再生宣称": r"再生(?!素|纸|纤维)",
}

EXTS = (".txt", ".md", ".html", ".htm", ".csv", ".json", ".py", ".doc", ".docx")

# 否定语境标记：命中词紧邻这些字时属合法提示语（如"不可丢入马桶"是 T/CNITA
# 09113 与 GB/T 40181 语境下必须印的警示语），不算违规候选。
NEGATION_PREFIX = ("不", "勿", "禁", "非", "否", "杜绝", "避免")


def is_negated(line, idx):
    """判断 line[idx] 处的命中词是否处于否定语境（前 4 个字符内出现否定标记）。"""
    window = line[max(0, idx - 4):idx]
    return any(n in window for n in NEGATION_PREFIX)


def read_lines(path):
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read().splitlines()
    except Exception:
        return None


def collect_files(targets):
    files = []
    for t in targets:
        if os.path.isdir(t):
            for root, _, fs in os.walk(t):
                for f in fs:
                    if f.lower().endswith(EXTS):
                        files.append(os.path.join(root, f))
        else:
            files.append(t)
    return files


def scan_file(path, word_tables, regex_tables):
    lines = read_lines(path)
    if lines is None:
        return None
    hits = []
    for ln, line in enumerate(lines, 1):
        for rule, words in word_tables.items():
            for w in words:
                start = 0
                while True:
                    idx = line.find(w, start)
                    if idx < 0:
                        break
                    # 湿厕纸的可冲散词表扫的是"不可冲散却标可冲散"，否定语境
                    # （不可/勿/禁止）正好是法定警示语，不列为候选违规。
                    if rule == "不可冲散却标湿厕纸" and is_negated(line, idx):
                        start = idx + 1
                        continue
                    hits.append({"file": path, "line": ln, "match": w,
                                 "rule": rule, "text": line.strip()[:120]})
                    start = idx + len(w)
        for rule, pat in regex_tables.items():
            for m in re.finditer(pat, line):
                hits.append({"file": path, "line": ln, "match": m.group(0),
                             "rule": rule, "text": line.strip()[:120]})
    return hits


def main():
    args = sys.argv[1:]
    if len(args) < 2:
        print(__doc__)
        return 2

    cat = args[0]
    if cat not in BANNED:
        print("未知类别: %s（可选: %s）" % (cat, "/".join(sorted(BANNED))))
        return 2

    out_path = None
    if "-o" in args:
        i = args.index("-o")
        if i + 1 >= len(args):
            print("-o 后必须跟报告路径")
            return 2
        out_path = args[i + 1]
        args = args[:i] + args[i + 2:]

    word_tables = dict(BANNED[cat])
    word_tables.update(GENERIC_WORDS)

    files = collect_files(args[1:])
    all_hits = []
    unreadable = []
    for fp in files:
        hits = scan_file(fp, word_tables, GENERIC_REGEX)
        if hits is None:
            unreadable.append(fp)
            continue
        all_hits += hits

    out = []
    out.append("产品类别: %s" % cat)
    out.append("扫描文件: %d 个（不可读 %d 个）" % (len(files), len(unreadable)))
    out.append("命中: %d 处（全部为待人工复核的候选违规）" % len(all_hits))
    out.append("=" * 60)

    if not all_hits:
        out.append("PASS：文本扫描未命中禁则")
        out.append("注意：必标项、检测项、宣称依据仍须按 checklist 与 advertising-claims.md 逐项核对")
    else:
        by_rule = {}
        for h in all_hits:
            by_rule.setdefault(h["rule"], []).append(h)
        for rule in sorted(by_rule):
            hs = by_rule[rule]
            out.append("【%s】%d 处" % (rule, len(hs)))
            seen = set()
            for h in hs:
                key = (h["match"], h["file"], h["line"])
                if key in seen:
                    continue
                seen.add(key)
                out.append("  L%-5d 「%s」  %s" % (h["line"], h["match"], h["text"]))
            out.append("")

    text = "\n".join(out)
    print(text)
    if out_path:
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(text)
        print("已写入 %s" % out_path)
    return 1 if all_hits else 0


if __name__ == "__main__":
    sys.exit(main())