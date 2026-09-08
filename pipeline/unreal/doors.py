"""Attach imported hinge hierarchies to the compiled interactive door actor."""

import unreal
import re


def configure(actors):
    subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    door_class = unreal.load_class(None, "/Script/ClevelandReal.OperableDoor")
    if not door_class:
        raise RuntimeError("Compile the ClevelandReal runtime module before configuring doors")
    hinges = [
        component
        for actor in actors
        for component in actor.get_components_by_class(unreal.SceneComponent)
        if "_hinge" in component.get_name().lower()
        and "shower" not in component.get_name().lower()
        and component.get_class() == unreal.SceneComponent.static_class()
    ]
    configured = []
    for hinge in hinges:
        name = hinge.get_name()
        base = re.sub(r"_\d+$", "", name)
        paired = sum(re.sub(r"_\d+$", "", h.get_name()) == base for h in hinges) == 2
        angle = -95.0 if paired and name.endswith("_1") else 95.0
        parent = hinge.get_attach_parent()
        if parent and parent.get_owner().get_class() == door_class:
            door = parent.get_owner()
            door.set_editor_property("open_angle", angle)
            location = door.get_actor_location()
            configured.append({"hinge": name, "positionCm": [location.x, location.y, location.z]})
            continue
        door = subsystem.spawn_actor_from_class(door_class, hinge.get_world_location())
        door.set_actor_label("Operable " + name)
        door.set_actor_transform(hinge.get_world_transform(), False, True)
        door.set_editor_property("open_angle", angle)
        for component in [hinge, *hinge.get_children_components(True)]:
            component.set_mobility(unreal.ComponentMobility.MOVABLE)
        hinge.attach_to_component(
            door.get_editor_property("root_component"),
            "",
            unreal.AttachmentRule.KEEP_WORLD,
            unreal.AttachmentRule.KEEP_WORLD,
            unreal.AttachmentRule.KEEP_WORLD,
            False,
        )
        location = door.get_actor_location()
        configured.append({"hinge": name, "positionCm": [location.x, location.y, location.z]})
    if not any("study_rear_door" in record["hinge"] for record in configured):
        raise RuntimeError(f"The real rear door was not configured: {configured}")
    return configured
