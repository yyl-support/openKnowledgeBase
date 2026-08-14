# 机器可读产物（供 AI 读取）

同级目录下的 `overview.md` / `techstack.md` / `standards.md` 是给人看的。
本目录三份 JSON 是给 AI 读的，由四层流水线产出。

| 文件 | 大小 | 内容 | 产出层 |
|---|---|---|---|
| `preprocess.json` | 18 KB | 规则事实集（`rule_facts`）、解读范围划分（`core`/`auxiliary`/`excluded`）、主流程判定、文件归属核算 | Layer 1 |
| `raw.json` | 2.3 MB | UA 知识图谱转换成的 2154 个页面，含 2143 节点 / 1791 边的摘要与关系 | Layer 2 |
| `verify.json` | 9 KB | 6 处事实冲突的核验过程与修正结论（`corrections_for_refiner`） | Layer 3 |

## 读取顺序

**优先级：`verify.json` > `raw.json`。** 两者冲突时一律采用 `verify.json` 中的
`corrections_for_refiner`——`raw.json` 里已知有 6 处错误，包括把 pod 标签说成
`nodeSelector`、把「每 runner 需 2 张 NPU」说成「2 副本」。逐条修正见
上级目录的 `check.md`。

按用途选择入口：

- 只需要事实结论 → 读同级目录的三份 Markdown，最省 token
- 需要按范围定位文件 → `preprocess.json` 的 `interpret_inputs`
- 需要项目规则约束 → `preprocess.json` 的 `rule_facts`（每条含来源文件路径）
- 需要某个文件的语义摘要 → `raw.json` 的 `pages[]`，按 `path` 字段索引
- 需要知道哪些结论被修正过 → `verify.json` 的 `conflicts[]`

## 数据基准

- 目标仓库：`github.com/opensourceways/ascend-ci-deployment`
- commit：`fe1ef54cee12b2cbf8eed9a52261e307794a3eb8`（2026-08-11）
- 分析文件数：2191 / 仓库总文件 2224

**这份数据对应上述 commit。** 目标仓库有新提交后，`raw.json` 的内容即过期，
里面的行号、版本号、路径可能与实际不符。重新生成：

```bash
python pipeline.py --repo <仓库路径> --adapter ua --output-type overview
```

`UAAdapter` 会比对 `.ua/meta.json` 的 `gitCommitHash` 与仓库 HEAD，不一致时
自动重跑 UA 分析。

## 已知边界

`raw.json` 的每个页面平均只有 220 字符——它是节点摘要，不是文件原文。一个 220 行的
`values.yaml` 在这里可能只剩一句话。需要精确字面量（镜像地址、资源配额、完整配置）时，
必须回到目标仓库读源文件，不要从摘要推断。
