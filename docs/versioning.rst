========================
Versioning and Releasing
========================

Version Scheme
==============

The project uses a date-based version scheme conforming to PEP440_. The
identifiers of official releases follow the "YY.MM" form (e.g., "16.10" for the
version released on October, 2016), while development versions between two
releases append a "+n.commit" suffix to the identifier of the last official
release (counting the additional commits on top of the release and naming the
topmost commit).

(Alpha, beta, RC, and dev release version identifiers are not planned as of yet,
as they would require the knowledge of the release date of the next official
release in advance - however, the project follows the "it will be released when
it's ready, whenever that is" ideology.)

.. _PEP440: https://www.python.org/dev/peps/pep-0440/


Commits in the Repository
=========================

For any official release, there should be exactly one commit in the repository
that makes the project identify itself as the released version, which is ensured
by tagging that commit with the version ID.


Release Steps
=============

The release of a new version happens along the following steps.

.. code-block:: bash

    # add release notes for new version YY.MM, create a commit for the release,
    # tag it, and push it to the public repository (which will automatically
    # upload the release to PyPI)
    nano RELNOTES.rst
    git add RELNOTES.rst
    git commit -m "YY.MM release"
    git tag YY.MM
    git push origin master YY.MM
