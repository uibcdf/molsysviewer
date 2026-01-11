Public API
==========

This section documents the supported, user-facing Python API.

Core entrypoints
----------------

.. autosummary::
   :toctree: autosummary
   :nosignatures:

   molsysviewer.MolSysView
   molsysviewer.new_view
   molsysviewer.demo

MolSysView: query and live operations
-------------------------------------

.. autosummary::
   :toctree: autosummary
   :nosignatures:

   molsysviewer.MolSysView.select
   molsysviewer.MolSysView.get
   molsysviewer.MolSysView.info
   molsysviewer.MolSysView.append_structures
   molsysviewer.MolSysView.set
   molsysviewer.MolSysView.add
   molsysviewer.MolSysView.remove

Version
-------

The installed package version is available as ``molsysviewer.__version__``.

Configuration
-------------

.. autosummary::
   :toctree: autosummary
   :nosignatures:

   molsysviewer.config
   molsysviewer.config.show_controls
   molsysviewer.config.autohide_controls
   molsysviewer.config.controls_position
   molsysviewer.config.controls_position_fullscreen
   molsysviewer.config.load_user_presets

User presets registry
---------------------

.. autodata:: molsysviewer.config.user_presets

Scene management
----------------

.. autosummary::
   :toctree: autosummary
   :nosignatures:

   molsysviewer.whole.Whole
   molsysviewer.regions.Region
   molsysviewer.layers.Layer

Loaders
-------

.. autosummary::
   :toctree: autosummary
   :nosignatures:

   molsysviewer.loaders
   molsysviewer.loaders.load_from_molsysmt

Shapes and overlays
-------------------

.. autosummary::
   :toctree: autosummary
   :nosignatures:

   molsysviewer.shapes
   molsysviewer.shapes.ShapesManager
   molsysviewer.shapes.SphereShapes
   molsysviewer.shapes.PocketSurfaces
   molsysviewer.shapes.PocketBlobs
   molsysviewer.shapes.ChannelTubes
   molsysviewer.shapes.AnisotropyEllipsoids
   molsysviewer.shapes.PharmacophoreShapes
   molsysviewer.shapes.LinkShapes
   molsysviewer.shapes.DisplacementVectors
   molsysviewer.shapes.TriangleFaces
   molsysviewer.shapes.Tetrahedra

Documentation helpers
---------------------

.. autosummary::
   :toctree: autosummary
   :nosignatures:

   molsysviewer.thirds.jupyter.load_html_in_notebook
