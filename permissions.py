"""
Layer 5: Permission System — fail-secure by default.
Production equivalent: permissions.rs (232 lines).

Key insight from production: unknown tools default to HIGHEST permission,
not lowest. This is fail-secure: block unknown tools rather than silently allow.

The deny reason is returned as an is_error=true tool_result so the LLM
can perceive the rejection and choose a fallback strategy.
"""

from enum import IntEnum


class PermissionMode(IntEnum):
    """Ordered permission levels. Higher = more access."""
    READ_ONLY = 0
    WORKSPACE_WRITE = 1
    DANGER_FULL_ACCESS = 2


# Per-tool permission requirements.
# Unregistered tools default to DANGER_FULL_ACCESS (fail-secure).
TOOL_PERMISSIONS = {
    "read_file": PermissionMode.READ_ONLY,
    "write_file": PermissionMode.WORKSPACE_WRITE,
    "bash": PermissionMode.DANGER_FULL_ACCESS,
}


class PermissionPolicy:
    """
    Runtime permission policy. Checks tool access against current mode.

    Production pattern: PermissionPrompter is a trait (can be TUI, headless,
    or test mock). We simplify to a callback. None = headless (auto-deny).
    """

    def __init__(self, mode: PermissionMode, prompter=None):
        self.mode = mode
        self.prompter = prompter  # callable(tool_name, required) -> bool

    def authorize(self, tool_name: str, _tool_input: dict) -> tuple[bool, str]:
        """
        Check if a tool call is allowed.

        Returns (allowed: bool, reason: str).
        Reason is always populated — on deny, it goes into tool_result
        so the LLM can perceive the rejection.
        """
        required = TOOL_PERMISSIONS.get(tool_name, PermissionMode.DANGER_FULL_ACCESS)

        if self.mode >= required:
            return True, "allowed"

        # Prompt user if available (production: workspace-write → danger boundary)
        if self.prompter and required == PermissionMode.DANGER_FULL_ACCESS:
            if self.prompter(tool_name, required):
                return True, "user approved"

        reason = (
            f"tool '{tool_name}' requires {required.name} "
            f"but current mode is {self.mode.name}"
        )
        return False, reason
