"""Small actual-notebook lifecycle fixture; no scientific calculation substitutes."""


def notebook_cells():
    return [
        """import gc
import molsysviewer as msv
from IPython.display import display
view = msv.demo['dialanine']
assert view.player.n_structures == 1
created = False
display(view)
print('LIFETIME_WITNESS')
""",
        """if not created:
    import molsysmt as msm
    source = msm.systems['pentalanine']['traj_pentalanine.h5msm']
    view_B = msv.new_view(source, structure_indices=[0])
    assert view_B.player.n_structures == 1
    created = True
    display(view_B)
    print('LIFETIME_VICTIM')
else:
    print('LIFETIME_CLEARED')
""",
        """view_B.close()
assert view_B.closed and not view.closed
del view_B
gc.collect()
print('LIFETIME_CLOSED')
""",
        """view.close()
assert view.closed
print('LIFETIME_DONE')
""",
    ]
