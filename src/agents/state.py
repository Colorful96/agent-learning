from dataclasses import dataclass, field


@dataclass
class AgentState:
    """保存 Agent 执行任务时的状态。"""

    # 用户最初提出的任务
    task: str

    # 当前执行的工作流名称
    workflow_name: str = ""

    # Agent 制定的任务计划
    plan: list[str] = field(default_factory=list)

    # 已经完成的步骤
    completed_steps: list[str] = field(default_factory=list)

    # 当前正在执行的步骤
    current_step: str = ""

    # 当前任务状态
    status: str = "pending"

    # 每个步骤的失败次数
    retry_count: int = 0

    # 重新规划的次数
    replan_count: int = 0

    # 最终回答
    final_answer: str = ""

    def start(self):
        """开始执行任务。"""

        self.status = "running"

    def complete_step(self, step):
        """记录一个已经完成的步骤。"""

        self.completed_steps.append(step)
        self.current_step = ""

    def fail(self):
        """记录一次失败。"""

        self.retry_count += 1

    def finish(self, answer):
        """结束任务并保存最终答案。"""

        self.status = "completed"
        self.final_answer = answer

    def to_dict(self):
        """把当前状态转换成可保存的字典。"""

        return {
            "task": self.task,
            "workflow_name": self.workflow_name,
            "plan": list(self.plan),
            "completed_steps": list(self.completed_steps),
            "current_step": self.current_step,
            "status": self.status,
            "retry_count": self.retry_count,
            "replan_count": self.replan_count,
            "final_answer": self.final_answer,
        }
