"""Lost/evicted dispatches use production journal, provider and fresh worker gates."""

import pytest
from test_profile_lifecycle import context
from test_profile_lifecycle import published_profile as published_profile

from cg_release.composition_journal import CompositionJournal
from cg_release.events import ControllerError
from cg_release.models import canonical_bytes
from cg_release.profile_docs import docs_step
from cg_release.profile_worker import current_ticket, register


@pytest.mark.parametrize("conclusion", ["failure", "cancelled", "timed_out"])
def test_valid_policy_retries_failed_composition_then_stops(
    published_profile, tmp_path, conclusion
):
    world, locator = published_profile
    ctx = context(world, locator, tmp_path)
    for attempt in range(4):
        item = CompositionJournal(ctx.journal).records()[-1]
        world.begin_docs(item, 55 + attempt)
        world.docs_runs[55 + attempt].update(status="completed", conclusion=conclusion)
        if attempt == 3:
            with pytest.raises(ControllerError, match="budget"):
                docs_step(ctx, ctx.journal.get(locator))
        else:
            assert docs_step(ctx, ctx.journal.get(locator)) is None
    assert len(CompositionJournal(ctx.journal).records()) == 4
    assert ctx.journal.get(locator).state == "published"


def test_pending_evicted_run_and_late_registration_cannot_steal_new_ticket(
    published_profile, tmp_path
):
    world, locator = published_profile
    ctx = context(world, locator, tmp_path)
    store = CompositionJournal(ctx.journal)
    item = store.records()[-1]
    world.begin_docs(item)
    world.docs_runs[55]["status"] = "pending"
    before = world.writes
    assert docs_step(ctx, ctx.journal.get(locator)) is None
    assert world.writes == before
    world.docs_runs[55].update(status="completed", conclusion="cancelled")
    assert docs_step(ctx, ctx.journal.get(locator)) is None
    assert len(store.records()) == 2
    before = world.writes
    with pytest.raises(ControllerError):
        register(ctx, ctx.journal.get(locator), item.ticket["nonce"], {})
    assert world.writes == before


def test_uncertain_dispatch_requires_two_bounded_absence_observations(
    published_profile, tmp_path
):
    world, locator = published_profile
    ctx = context(world, locator, tmp_path)
    store = CompositionJournal(ctx.journal)
    first = store.records()[-1]
    original = canonical_bytes(ctx.journal.get(locator))
    assert docs_step(ctx, ctx.journal.get(locator)) is None
    assert len(store.records()) == 1
    world.wall_time += 121
    assert docs_step(ctx, ctx.journal.get(locator)) is None
    assert "absence-first" in store.records()[-1].evidence and len(store.records()) == 1
    assert docs_step(ctx, ctx.journal.get(locator)) is None
    world.wall_time += 121
    assert docs_step(ctx, ctx.journal.get(locator)) is None
    assert len(store.records()) == 2 and "absence" in store.records()[0].evidence
    assert canonical_bytes(ctx.journal.get(locator)) == original
    with pytest.raises(ControllerError):
        current_ticket(
            ctx.journal.get(locator), first.ticket["nonce"], journal=ctx.journal
        )


def test_changed_policy_cannot_refresh_or_waive_original_profile(
    published_profile, tmp_path
):
    from cg_release.models import Policy, load_record
    from cg_release.recovery import finish_published

    world, locator = published_profile
    ctx = context(world, locator, tmp_path)
    raw = ctx.policy.model_dump(mode="json")
    raw.update(gpid_profile=None, profile=None)
    ctx.policy = load_record(Policy, canonical_bytes(raw))
    before = world.writes
    with pytest.raises(ControllerError, match="policy"):
        finish_published(ctx, ctx.journal.get(locator))
    assert world.writes == before and ctx.journal.get(locator).state == "published"


def test_repeated_actual_refreshes_do_not_grow_release_record(
    published_profile, tmp_path
):
    world, locator = published_profile
    ctx = context(world, locator, tmp_path)
    original = canonical_bytes(ctx.journal.get(locator))
    store = CompositionJournal(ctx.journal)
    for number in range(1, 49):
        item = store.records()[-1]
        world.begin_docs(item, 100 + number)
        world.docs_runs[100 + number].update(status="completed", conclusion="cancelled")
        world.branches["dev"] = f"{number:040x}"
        ctx.api.deadline = world.clock() + 120
        assert docs_step(ctx, ctx.journal.get(locator)) is None
    records = store.records()
    assert len(records) == 49
    assert sum(len(canonical_bytes(r)) for r in records) > 65536
    assert all(len(canonical_bytes(r)) < 65536 for r in records)
    assert canonical_bytes(ctx.journal.get(locator)) == original
    assert ctx.journal.reservations() == ["1.1.0"]


@pytest.mark.parametrize("exhausted", [False, True])
def test_absence_checkpoint_reentry_preserves_bytes_before_replacement(
    published_profile, tmp_path, exhausted
):
    from cg_release.profile_dispatch import recover_dispatch

    world, locator = published_profile
    ctx = context(world, locator, tmp_path)
    store = CompositionJournal(ctx.journal)
    record = ctx.journal.get(locator)
    if exhausted:
        for index in range(ctx.policy.profile.composition_retries):
            world.begin_docs(store.records()[-1], 55 + index)
            world.docs_runs[55 + index].update(
                status="completed", conclusion="cancelled"
            )
            assert docs_step(ctx, record) is None
    original_count = len(store.records())
    world.wall_time += 121
    item, _, safe = recover_dispatch(ctx, record, store.records()[-1])
    assert not safe
    world.wall_time += 121
    item, _, safe = recover_dispatch(ctx, record, item)
    assert safe
    before = canonical_bytes(item)
    world.wall_time += 1
    again, _, safe = recover_dispatch(ctx, record, item)
    assert safe and canonical_bytes(again) == before
    if exhausted:
        for _ in range(2):
            world.wall_time += 1
            with pytest.raises(ControllerError) as error:
                docs_step(ctx, record)
            assert error.value.code == "E_RETRY_BUDGET"
            assert canonical_bytes(store.records()[-1]) == before
    world.branches["dev"] = "e" * 40
    assert docs_step(ctx, record) is None
    assert len(store.records()) == original_count + 1
    assert canonical_bytes(store.records()[-2]) == before
