import dataclasses


@dataclasses.dataclass
class StopResult:
    force_killed: bool
