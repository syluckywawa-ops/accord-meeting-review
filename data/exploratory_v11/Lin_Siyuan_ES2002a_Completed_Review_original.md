# ES2002a 人工复核表（已完成）

复核对象：AMI Meeting Corpus，ES2002a。完整逐字稿：`data/exploratory_v11/transcripts/ES2002a.txt`。本次判断独立依据逐字稿，不迁就系统候选或初审结论。

## 先通读，再看下方候选

- 我是否读完全部 207 个发言片段：**是（T0001–T0207）**
- 我独立找到的会后行动项数量：**3**
- 我独立找到的行动项：

| # | 任务 | 负责人 | 截止时间原话或“未说明” | 证据 turn ID | 不确定之处 |
|---|---|---|---|---|---|
| 1 | 完成遥控器的 working design（实际工作设计） | Industrial Designer | “the next meeting's gonna be in thirty minutes”；“inbetween now and then” | `ES2002a-T0176`；接受见 `ES2002a-T0177` | 具体交付物格式没有说明；但会后任务、负责人和相对期限明确。 |
| 2 | 处理／设计遥控器的 technical functions（技术功能，即产品实际能做什么） | User Interface Designer | “the next meeting's gonna be in thirty minutes”；“inbetween now and then” | `ES2002a-T0176` | User Interface Designer 没有单独口头接受；但这是直接的角色分派，仍应保留。具体交付物格式没有说明。 |
| 3 | 梳理遥控器必须满足的 requirements（产品需求） | Marketing Expert | “the next meeting's gonna be in thirty minutes”；“inbetween now and then” | `ES2002a-T0176–T0178`；接受见 `ES2002a-T0179` | `T0178` 的口语表达有重复和修正，但任务对象仍可识别为产品 requirements。 |

## 核对系统的三个候选

| 候选 | 系统写的任务与负责人 | 原文位置 | 我的判定 | 理由／如需修改，改成什么 |
|---|---|---|---|---|
| P1 | `go`；Marketing Expert | `T0016–T0021`，系统引用 `T0019` | **拒绝** | `I will go` 是 Marketing Expert 自愿先进行白板热身活动，随后马上开始画动物；这是会议现场立即执行的活动，不是会后任务，而且 `go` 本身也不是可独立理解的任务。 |
| P2 | `just draw a different kind of dog`；Project Manager | `T0049–T0056`，系统引用 `T0052` | **拒绝** | Project Manager 正在会议现场完成“画最喜欢的动物”的热身活动；该发言描述当场行为，不是尚待执行的会后工作。 |
| P3 | `just check we've nothing else`；Project Manager | `T0148–T0154`，系统引用 `T0149` | **拒绝** | Project Manager 是在会议即将结束时当场检查议程／材料，随后立即继续提问；没有形成会后交付物或未来承诺。 |

## 专门检查遗漏及边界

1. `T0176–T0179` 应记为 **3 项会后行动**。Project Manager 先明确下次会议在三十分钟后，再用 “inbetween now and then” 引出三位角色分别要做的工作；三项工作对象和负责人均可区分，因此不应合并成一项笼统的“individual work”。

2. 三项分别为：
   - Industrial Designer：完成 working design；证据 `ES2002a-T0176`，并在 `T0177` 回答 “Yep”。
   - User Interface Designer：处理 technical functions／明确产品实际功能；证据 `ES2002a-T0176`。
   - Marketing Expert：梳理产品必须满足的 requirements；证据 `ES2002a-T0176–T0178`，并在 `T0179` 回答 “Okay”。

   User Interface Designer 没有明确口头接受。**这不会改变保留判定**，因为 Project Manager 已直接按角色分派任务；是否口头接受可作为置信度或证据质量说明，但不应因此删除任务。

3. “下次会议在三十分钟后”可以作为三项工作的共同**相对截止时间**，因为任务被明确限定为 “inbetween now and then”。原话还说 “about ten to twelve by my watch”，结合会议日期最多可以记录为 **2004-12-13 约 11:50**；但由于说的是 “about”、元数据没有可靠的会议开始时刻，因此没有足够信息写成精确的绝对时间戳。正式字段宜保留为 “before the next meeting in thirty minutes”。

4. 全文其他位置**未发现**符合条件的会后行动。`T0104` 的 “I should be writing all this down” 指会议当场记笔记；`T0121` 只是认为竞品价格信息会有用；`T0141–T0174` 是产品想法和设计讨论，均没有形成明确的会后分派。

## V1.1 提示与实际用时

- P1 的“证据可能太短、应检查相邻发言”提示**有帮助**：查看相邻发言后可以确认它是当场白板活动。但该提示只覆盖证据过短问题，**漏掉了更重要的错误类型**：系统没有识别 `T0176–T0179` 的三项真正会后任务，也没有提醒 P2、P3 同样属于会议现场行为而非未来行动。
- 实际用时：**未计时**。
- 参考人工用时：**约 28 分钟**。估算依据为约 3,100 个转写词，以正常审慎阅读速度再放慢约 20% 完整通读，并计入核对 3 条系统候选、复查结尾遗漏、确认负责人和截止时间及填写证据编号的时间。合理波动范围约为 **25–35 分钟**；该数字只能用于工作量规划，不能作为本次实验的实测审核时间。
- 最费力、最容易出错的一步：区分“会议现场立即执行的动作”与“会议结束后、下次会议前的任务”，以及把 `T0176` 中的共同期限正确继承到三个角色任务。另一个边界是：负责人没有逐一口头接受时，不能机械地把直接分派排除。

## 最终结论

- 系统候选：**0 条保留，3 条拒绝**。
- 人工确认：**3 条会后行动**，均由系统遗漏。
- 结尾遗漏检查：**有遗漏，集中在 `T0176–T0179`**。
