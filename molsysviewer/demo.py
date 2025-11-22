from .viewer import MolSysView


def demo(with_molsysmt=True):
    view = MolSysView()
    if with_molsysmt is False:
        from .loaders import load_pdb_id
        load_pdb_id(view, pdb_id="1TCD")
    else:
        view.load("1TCD")
    return view.show()
