from molsysviewer.tags import TagsManager


def test_tags_manager_queries_registry_and_skips_existing_generated_tag():
    registry = {"shape1"}
    manager = TagsManager("shape", "shape", lambda: registry)

    assert manager.allocate() == "shape2"
    registry.add("shape2")
    assert manager.allocate() == "shape3"


def test_tags_manager_observes_explicit_tags_and_restores_monotonically():
    manager = TagsManager("measurement", "measurement", lambda: ())

    manager.observe("measurement7")
    manager.restore(3)

    assert manager.high_water_mark == 7
    assert manager.allocate() == "measurement8"


def test_tags_manager_rejects_duplicate_within_its_domain():
    manager = TagsManager("region", "region", lambda: ("site",))

    try:
        manager.validate("site")
    except ValueError as error:
        assert "Region tag 'site' already exists" in str(error)
    else:
        raise AssertionError("duplicate domain tag was accepted")
