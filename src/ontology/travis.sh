# Running release pipeline for TRAVIS
set -e

sh run.sh make update_ontology -B

sh run.sh make IMP=false prepare_release -B
