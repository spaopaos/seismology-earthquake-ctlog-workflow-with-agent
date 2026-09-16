# Runtime snapshot provenance

These archives snapshot existing, explicitly reused scientific environments. No dependency installation or upgrade was performed for this release. The original environments were not repaired or rebuilt.

The phasenet_plus and phasenet2 snapshots passed conda-pack's normal missing-file checks. The plam environment contained Conda records with Python 3.1 paths although Python 3.11 is installed, and obsolete setuptools metadata from a Conda/pip mismatch. The packaging adapter corrects proven path spellings in memory and checks every missing-file exception against a narrow list of installer packages: setuptools, pip, wheel and packaging. No missing scientific package file is accepted. Actual installed files are retained and then import-tested after extraction to a different path.

Actual installed setuptools in the MESS snapshot is 80.10.1; the obsolete Conda record says 83.0.0. Use installed.json to identify actual Python distributions. Explicit Conda inventories alone do not represent a validated reconstruction of this snapshot. The offline snapshots are the tested deployment path.

The runtime archives are checksummed. Model weights and source/binary identities are checked separately. Package portability is bounded by the declared operating system/architecture and host runtime compatibility, and requires destination preflight.
