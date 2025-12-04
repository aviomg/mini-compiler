from dataclasses import dataclass, field
from typing import Iterable, List, Optional


@dataclass
class ProcedureIR:
    """IR for a single lowered procedure (one per Mini function today)."""

    name: str
    label: str
    prologue: List[str] = field(default_factory=list)
    body: List[str] = field(default_factory=list)
    epilogue: List[str] = field(default_factory=list)

    def to_lines(self) -> List[str]:
        lines: List[str] = []
        if self.label:
            lines.append(self.label)
        if self.prologue:
            lines.append("#start of prologue")
            lines.extend(self.prologue)
            lines.append("#end of prologue")
        if self.body:
            lines.append("#start of body")
            lines.extend(self.body)
            lines.append("#end of body")
        if self.epilogue:
            lines.append("#start of epilogue")
            lines.extend(self.epilogue)
            lines.append("#end of epilogue")
        return lines


@dataclass
class FunctionIR:
    name: str
    procedures: List[ProcedureIR] = field(default_factory=list)


@dataclass
class ModuleIR:
    """Container for the full IR: module -> functions -> procedures."""

    setup_lines: List[str]
    functions: List[FunctionIR] = field(default_factory=list)

    def procedures(self) -> Iterable[ProcedureIR]:
        for fn in self.functions:
            for proc in fn.procedures:
                yield proc

    def to_lines(self, end_chunks: Optional[List[str]] = None) -> List[str]:
        lines = list(self.setup_lines)
        for proc in self.procedures():
            lines.extend(proc.to_lines())
        if end_chunks:
            lines.extend(end_chunks)
        return lines


def write_module(module: ModuleIR, output_path: str, end_chunk_path: Optional[str] = None) -> List[str]:
    """Materialize a ModuleIR into an assembly file. Returns the header/setup lines."""
    end_lines: List[str] = []
    if end_chunk_path:
        with open(end_chunk_path, "r") as f:
            end_lines = f.read().splitlines()

    lines = module.to_lines(end_lines if end_lines else None)
    with open(output_path, "w") as f:
        for line in lines:
            f.write(line + "\n")
    return module.setup_lines
