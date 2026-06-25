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

MolSysView: core operations & loading
-------------------------------------

.. autosummary::
   :toctree: autosummary
   :nosignatures:

   molsysviewer.MolSysView.load
   molsysviewer.MolSysView.reset_viewer
   molsysviewer.MolSysView.zoom
   molsysviewer.MolSysView.focus_selection
   molsysviewer.MolSysView.focus_region
   molsysviewer.MolSysView.reset_camera
   molsysviewer.MolSysView.get_camera_snapshot
   molsysviewer.MolSysView.set_camera_snapshot
   molsysviewer.MolSysView.clear_decorations

MolSysView: trajectory navigation & playback
--------------------------------------------

.. autosummary::
   :toctree: autosummary
   :nosignatures:

   molsysviewer.MolSysView.play
   molsysviewer.MolSysView.pause
   molsysviewer.MolSysView.set_play_speed
   molsysviewer.MolSysView.current_structure_index
   molsysviewer.MolSysView.get_coordinates
   molsysviewer.MolSysView.set_coordinates

MolSysView: query & live operations
-----------------------------------

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

MolSysView: state management & callbacks
----------------------------------------

.. autosummary::
   :toctree: autosummary
   :nosignatures:

   molsysviewer.MolSysView.export_state
   molsysviewer.MolSysView.import_state
   molsysviewer.MolSysView.on_hover
   molsysviewer.MolSysView.off_hover
   molsysviewer.MolSysView.on_click
   molsysviewer.MolSysView.off_click
   molsysviewer.MolSysView.on_context
   molsysviewer.MolSysView.off_context

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

.. data:: molsysviewer.config.user_presets

   Registry of user-defined representation presets.

   The registry is a mapping from preset name to configuration dict.
   Each configuration typically contains 'base', optional 'options', and a list
   of 'rules' (by selection or atom indices).

   See :func:`load_user_presets` for the expected file structure.

Scene management & objects
--------------------------

.. autosummary::
   :toctree: autosummary
   :nosignatures:

   molsysviewer.whole.Whole
   molsysviewer.regions.RegionsManager
   molsysviewer.regions.Region
   molsysviewer.layers.Layer
   molsysviewer.styles.StylesManager
   molsysviewer.styles.Style
   molsysviewer.selections.SelectionsManager
   molsysviewer.selections.Selection
   molsysviewer.annotations.AnnotationsManager
   molsysviewer.measurements.MeasurementsManager

Loaders
-------

.. autosummary::
   :toctree: autosummary
   :nosignatures:

   molsysviewer.loaders
   molsysviewer.loaders.load_from_molsysmt

Shapes, timeline & export namespaces
------------------------------------

.. autosummary::
   :toctree: autosummary
   :nosignatures:

   molsysviewer.shapes
   molsysviewer.shapes.ShapesManager
   molsysviewer.viewer.movie.MovieManager
   molsysviewer.exports.ExportManager
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
