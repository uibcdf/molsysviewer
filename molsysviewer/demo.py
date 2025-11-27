from .viewer import MolSysView


def demo(with_molsysmt=True):
    view = MolSysView()
    if with_molsysmt is False:
        from .loaders import load_pdb_id
        load_pdb_id(pdb_id="1TCD", view=view)
    else:
        view.load("1TCD")
    return view.show()
