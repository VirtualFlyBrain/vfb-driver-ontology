These notes are for the EDITORS of VFB_drivers

This project was created using the [ontology development kit](https://github.com/INCATools/ontology-development-kit). See the site for details.

## Requirements

 1. A git client (we assume command line git)
 2. [docker](https://www.docker.com/get-docker) (for managing releases)

## Editors Version

Do not edit this ontology manually, it is generated automatically.

## ID Ranges

ID ranges are not necessary as no new terms should be created.

## Imports

All import modules are in the [imports/](imports/) folder.
Add new imports to the VFB_drivers-odk.yaml file then make the update_repo goal.

## Release Manager notes

These instructions assume you have
[docker](https://www.docker.com/get-docker). This folder has a script
[run.sh](run.sh) that wraps docker commands.

To release:

sh run_release.sh

Check that everything seems ok in the diff and the reports/VFB_drivers-edit.owl-obo-report.tsv file.
Push the files on a branch and merge when checks pass.

IMMEDIATELY AFTERWARDS go here:
https://github.com/VirtualFlyBrain/vfb-driver-ontology/releases/new

__IMPORTANT__: The value of the "Tag version" field MUST be

    vYYYY-MM-DD

The initial lowercase "v" is REQUIRED. The YYYY-MM-DD *must* match
what is in the `owl:versionIRI` of the derived VFB_drivers.owl. This will be today's date.

This cannot be changed after the fact, be sure to get this right!

Release title should be YYYY-MM-DD

You can also add release notes (this can also be done after the fact). These are in markdown format.
In future we will have better tools for auto-generating release notes.

Then click "publish release"

__IMPORTANT__: NO MORE THAN ONE RELEASE PER DAY.

# Continuous Integration

Checks run on GitHub Actions:
https://github.com/VirtualFlyBrain/vfb-driver-ontology/actions