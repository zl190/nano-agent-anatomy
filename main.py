"""
A study notebook for production AI agent architecture.
5 files, 500 lines, 5 layers of a production agent system.

Usage:
    python main.py                        # Basic agent (loop only)
    python main.py --memory               # With persistent memory
    python main.py --memory --compress    # With context compression
    python main.py --coordinate "task"    # Multi-agent mode
"""

import argparse

from loop import agent_loop  # noqa: E402
from memory import MemoryStore  # noqa: E402
from context import ContextCompressor  # noqa: E402
from coordinator import coordinate  # noqa: E402
from permissions import PermissionMode  # noqa: E402

PERMISSION_MODES = {
    "read": PermissionMode.READ_ONLY,
    "write": PermissionMode.WORKSPACE_WRITE,
    "full": PermissionMode.DANGER_FULL_ACCESS,
}


def main():
    parser = argparse.ArgumentParser(description="agent anatomy study notebook")
    parser.add_argument("--memory", action="store_true", help="Enable persistent memory")
    parser.add_argument("--compress", action="store_true", help="Enable context compression")
    parser.add_argument("--coordinate", type=str, help="Multi-agent mode: delegate task to workers")
    parser.add_argument("--model", default="claude-sonnet-4-6", help="Model to use")
    parser.add_argument("--permission", choices=["read", "write", "full"], default="full",
                        help="Permission mode (default: full)")
    args = parser.parse_args()

    memory = MemoryStore() if args.memory else None
    compressor = ContextCompressor() if args.compress else None
    perm_mode = PERMISSION_MODES[args.permission]

    if args.coordinate:
        result = coordinate(args.coordinate, model=args.model, memory=memory)
        print(result)
    else:
        agent_loop(model=args.model, memory=memory, compressor=compressor,
                   permission_mode=perm_mode)


if __name__ == "__main__":
    main()
