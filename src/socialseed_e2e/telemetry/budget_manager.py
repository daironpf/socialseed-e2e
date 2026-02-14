"""Token Budget Manager.

Manages token budgets per issue/task to prevent runaway costs
during autonomous programming.
"""

import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from socialseed_e2e.telemetry.models import LLMCall, TokenBudget, TokenUsage


class BudgetBreach(Exception):
    """Exception raised when token budget is exceeded."""

    def __init__(self, budget: TokenBudget, attempted_usage: TokenUsage):
        self.budget = budget
        self.attempted_usage = attempted_usage
        super().__init__(
            f"Budget '{budget.name}' exceeded: "
            f"{attempted_usage.total_tokens} tokens attempted, "
            f"{budget.max_total_tokens} limit"
        )


class BudgetManager:
    """Manages token budgets for different scopes."""

    def __init__(self):
        self.budgets: Dict[str, TokenBudget] = {}
        self.call_history: Dict[str, List[LLMCall]] = {}

    def create_budget(
        self,
        name: str,
        scope_type: str,
        scope_id: Optional[str] = None,
        description: Optional[str] = None,
        max_input_tokens: Optional[int] = None,
        max_output_tokens: Optional[int] = None,
        max_total_tokens: Optional[int] = None,
        max_cost_usd: Optional[float] = None,
        time_window_minutes: Optional[int] = None,
        on_budget_breach: str = "warn",
    ) -> TokenBudget:
        """Create a new token budget."""
        budget_id = str(uuid.uuid4())[:8]

        budget = TokenBudget(
            budget_id=budget_id,
            name=name,
            description=description,
            max_input_tokens=max_input_tokens,
            max_output_tokens=max_output_tokens,
            max_total_tokens=max_total_tokens,
            max_cost_usd=max_cost_usd,
            time_window_minutes=time_window_minutes,
            scope_type=scope_type,
            scope_id=scope_id,
            on_budget_breach=on_budget_breach,
            is_active=True,
        )

        self.budgets[budget_id] = budget
        self.call_history[budget_id] = []

        return budget

    def track_call(self, call: LLMCall) -> bool:
        """Track an LLM call against applicable budgets.

        Returns True if within budget, False if budget exceeded (and on_budget_breach is not 'block').
        Raises BudgetBreach if on_budget_breach is 'block'.
        """
        # Find applicable budgets
        applicable_budgets = self._get_applicable_budgets(call)

        for budget in applicable_budgets:
            if not budget.is_active:
                continue

            # Update usage
            budget.current_usage.input_tokens += call.token_usage.input_tokens
            budget.current_usage.output_tokens += call.token_usage.output_tokens
            budget.current_usage.total_tokens += call.token_usage.total_tokens
            budget.current_cost_usd += call.cost.total_cost_usd

            # Track call
            self.call_history[budget.budget_id].append(call)

            # Check budget breach
            breach = self._check_budget_breach(budget)

            if breach:
                if budget.on_budget_breach == "block":
                    raise BudgetBreach(budget, call.token_usage)
                elif budget.on_budget_breach == "warn":
                    # Just warn, don't block
                    pass
                elif budget.on_budget_breach == "alert":
                    # Would trigger alerts in real implementation
                    pass

        return True

    def _get_applicable_budgets(self, call: LLMCall) -> List[TokenBudget]:
        """Get budgets applicable to a call."""
        applicable = []

        for budget in self.budgets.values():
            if not budget.is_active:
                continue

            # Check scope match
            if budget.scope_type == "global":
                applicable.append(budget)
            elif budget.scope_type == "issue" and call.issue_id:
                if budget.scope_id == call.issue_id:
                    applicable.append(budget)
            elif budget.scope_type == "task" and call.task_id:
                if budget.scope_id == call.task_id:
                    applicable.append(budget)
            elif budget.scope_type == "test_case" and call.test_case_id:
                if budget.scope_id == call.test_case_id:
                    applicable.append(budget)
            elif budget.scope_type == "agent" and call.agent_name:
                if budget.scope_id == call.agent_name:
                    applicable.append(budget)

        return applicable

    def _check_budget_breach(self, budget: TokenBudget) -> bool:
        """Check if budget has been breached."""
        # Check token limits
        if (
            budget.max_input_tokens
            and budget.current_usage.input_tokens > budget.max_input_tokens
        ):
            return True

        if (
            budget.max_output_tokens
            and budget.current_usage.output_tokens > budget.max_output_tokens
        ):
            return True

        if (
            budget.max_total_tokens
            and budget.current_usage.total_tokens > budget.max_total_tokens
        ):
            return True

        # Check cost limit
        if budget.max_cost_usd and budget.current_cost_usd > budget.max_cost_usd:
            return True

        return False

    def get_budget_status(self, budget_id: str) -> Optional[Dict]:
        """Get current status of a budget."""
        budget = self.budgets.get(budget_id)
        if not budget:
            return None

        # Calculate usage percentages
        input_pct = (
            (budget.current_usage.input_tokens / budget.max_input_tokens * 100)
            if budget.max_input_tokens
            else None
        )
        output_pct = (
            (budget.current_usage.output_tokens / budget.max_output_tokens * 100)
            if budget.max_output_tokens
            else None
        )
        total_pct = (
            (budget.current_usage.total_tokens / budget.max_total_tokens * 100)
            if budget.max_total_tokens
            else None
        )
        cost_pct = (
            (budget.current_cost_usd / budget.max_cost_usd * 100)
            if budget.max_cost_usd
            else None
        )

        return {
            "budget_id": budget_id,
            "name": budget.name,
            "scope": f"{budget.scope_type}:{budget.scope_id or 'all'}",
            "is_active": budget.is_active,
            "usage": {
                "input_tokens": budget.current_usage.input_tokens,
                "output_tokens": budget.current_usage.output_tokens,
                "total_tokens": budget.current_usage.total_tokens,
                "cost_usd": budget.current_cost_usd,
            },
            "limits": {
                "max_input_tokens": budget.max_input_tokens,
                "max_output_tokens": budget.max_output_tokens,
                "max_total_tokens": budget.max_total_tokens,
                "max_cost_usd": budget.max_cost_usd,
            },
            "percentages": {
                "input": input_pct,
                "output": output_pct,
                "total": total_pct,
                "cost": cost_pct,
            },
            "breached": self._check_budget_breach(budget),
        }

    def get_all_budgets_status(self) -> List[Dict]:
        """Get status of all budgets."""
        return [self.get_budget_status(bid) for bid in self.budgets.keys()]

    def deactivate_budget(self, budget_id: str):
        """Deactivate a budget."""
        if budget_id in self.budgets:
            self.budgets[budget_id].is_active = False

    def reset_budget(self, budget_id: str):
        """Reset a budget's usage counters."""
        if budget_id in self.budgets:
            budget = self.budgets[budget_id]
            budget.current_usage = TokenUsage(
                input_tokens=0, output_tokens=0, total_tokens=0
            )
            budget.current_cost_usd = 0.0
            self.call_history[budget_id] = []

    def delete_budget(self, budget_id: str):
        """Delete a budget."""
        if budget_id in self.budgets:
            del self.budgets[budget_id]
            del self.call_history[budget_id]

    def get_budgets_by_scope(
        self, scope_type: str, scope_id: Optional[str] = None
    ) -> List[TokenBudget]:
        """Get budgets by scope."""
        matching = []
        for budget in self.budgets.values():
            if budget.scope_type == scope_type:
                if scope_id is None or budget.scope_id == scope_id:
                    matching.append(budget)
        return matching

    def check_global_budget(self) -> Optional[Dict]:
        """Check global budget status if one exists."""
        global_budgets = self.get_budgets_by_scope("global")
        if global_budgets:
            return self.get_budget_status(global_budgets[0].budget_id)
        return None
