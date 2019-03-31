========================
Versioning and Releasing
========================

Version Scheme
==============

The project uses a date-based version scheme conforming to PEP440_. The
identifiers of official releases follow the "YY.MM" form (e.g., "16.10" for the
version released on October, 2016), while development versions between two
releases append a "+x" suffix to the identifier of the last official release
(e.g., "16.10+x" for snapshots that contain changes on top of the "16.10"
release).

(Alpha, beta, RC, and dev release version identifiers are not planned as of yet,
as they would require the knowledge of the release date of the next official
release in advance - however, the project follows the "it will be released when
it's ready, whenever that is" ideology.)

.. _PEP440: https://www.python.org/dev/peps/pep-0440/


Commits in the Repository
=========================

For any official release, there should be exactly one commit in the repository
that makes the project identify itself as the released version, and that commit
should also be tagged with the version ID. Thus, the first commit after a
release has to be a bump to a "+x"-suffixed snapshot version.


Release Steps
=============

The release of a new version happens along the following steps.

.. code-block:: bash

    # name the new version YY.MM and add release notes
    nano fuzzinator/PKGDATA.json
    nano RELNOTES.rst

    # create a commit for the release, tag it, and push it to the public
    # repository (which will automatically upload the release to PyPI)
    git add fuzzinator/PKGDATA.json RELNOTES.rst
    git commit -m "YY.MM release"
    git tag YY.MM
    git push origin master YY.MM

Before landing anything in the repository after a release, the version should be
bumped.

.. code-block:: bash

    # bump version to YY.MM+x
    nano fuzzinator/PKGDATA.json
    git add fuzzinator/PKGDATA.json
    git commit -m "Change to post-release version YY.MM+x"
    git push origin master
