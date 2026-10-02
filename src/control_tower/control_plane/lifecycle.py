"""Pure state machine. Explicit human authorization, no registry writes or runtime actions."""
from .registry import LifecycleState as State

ALLOWED_TRANSITIONS = {
    State.DRAFT: frozenset({State.PILOT}),
    State.PILOT: frozenset({State.ACTIVE, State.REVIEW, State.RETIRED}),
    State.ACTIVE: frozenset({State.REVIEW, State.PAUSED}),
    State.REVIEW: frozenset({State.ACTIVE, State.PAUSED, State.RETIRED}),
    State.PAUSED: frozenset({State.ACTIVE, State.RETIRED}),
    State.RETIRED: frozenset(),
}


def can_transition(current: State, target: State) -> bool:
    return target in ALLOWED_TRANSITIONS[State(current)]


def transition(current: State, target: State, *, human_authorized: bool = False) -> State:
    """Validate and return a new state value; caller's registry is never mutated/persisted."""
    if not can_transition(current, target):
        raise ValueError('Lifecycle transition not allowed')
    if human_authorized is not True:
        raise PermissionError('Recommendation is not authorization')
    return State(target)
