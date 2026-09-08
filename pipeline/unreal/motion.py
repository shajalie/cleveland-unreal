"""Wire modeled fan assemblies to their compiled, pausable runtime actor."""

import unreal


def configure_fans(actors):
    actor_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    fan_class = unreal.load_class(None, "/Script/ClevelandReal.CeilingFan")
    if not fan_class:
        raise RuntimeError("Compile the runtime before configuring fan motion")
    names = ["Primary_ceiling_fan", "Sunroom_ceiling_fan", "Blue_bedroom_fan"]
    result = []
    for actor in actors:
        for component in actor.get_components_by_class(unreal.SceneComponent):
            if component.get_class() != unreal.SceneComponent.static_class():
                continue
            if not any(component.get_name() == name for name in names):
                continue
            fan = actor_api.spawn_actor_from_class(fan_class, component.get_world_location())
            fan.set_actor_transform(component.get_world_transform(), False, True)
            fan.set_actor_label("Moving " + component.get_name())
            for child in [component, *component.get_children_components(True)]:
                child.set_mobility(unreal.ComponentMobility.MOVABLE)
            component.attach_to_component(
                fan.get_root_component(),
                "",
                unreal.AttachmentRule.KEEP_WORLD,
                unreal.AttachmentRule.KEEP_WORLD,
                unreal.AttachmentRule.KEEP_WORLD,
                False,
            )
            result.append(component.get_name())
    return result
