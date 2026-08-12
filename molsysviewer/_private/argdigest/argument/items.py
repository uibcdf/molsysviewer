from molsysviewer._private.exceptions import ArgumentError

#: `items` means two unrelated things in this library, and only the caller tells them
#: apart. Everywhere else it is MolSysMT's sense -- molecular systems to be combined,
#: whose forms this digester resolves. In `scene.set_legend` it is a list of
#: `{"label", "color"}` entries for a colour key, which has no form at all.
#:
#: Resolving legend entries as molecular items fails on the first one. The real fix is a
#: name that does not collide, which is a public API change; this is the honest patch
#: until that is decided.
_LEGEND_ENTRY_CALLERS = frozenset({
    "molsysviewer.scene.set_legend",
    "molsysviewer.scene.SceneManager.set_legend",
})


def digest_items(items, forms=None, caller=None):

    if caller in _LEGEND_ENTRY_CALLERS:
        return items

    from molsysmt.basic import get_form

    if items is None:
        return []

    aux_items = items

    if not isinstance(items, (list, tuple)):
        aux_items = [items]

    in_forms = []
    output = True

    for item in aux_items:
        try:
            in_forms.append(get_form(item))
        except:
            output = False
            break

    if output:
        if forms is not None:
            if isinstance(forms, str):
                forms = [forms]
            for in_form, form in zip(in_forms, forms):
                if in_form!=form:
                    raise ArgumentError('item', value=item, caller=caller, message=None)
        return aux_items

    raise ArgumentError('items', value=items, caller=caller, message=None)
