## Customize Makefile settings for VFB_drivers
##
## If you need to customize your Makefile, make
## changes here rather than in the main Makefile

.PHONY: prepare_release
prepare_release: all $(ONT)-cedar.owl reports/robot_diff.txt
	rsync -R $(RELEASE_ASSETS) $(ONT)-cedar.owl $(RELEASEDIR) &&\
	rm -f $(CLEANFILES) $(ONT)-cedar.owl &&\
	echo "Release files are now in $(RELEASEDIR) - now you should commit, push and make a release on your git hosting site such as GitHub or GitLab"

update_ontology:
	python3 -m pip install -r ../scripts/requirements.txt && \
	python3 ../scripts/update_ontology.py &&\
	$(ROBOT) template --template template.tsv \
	--output ./tmp/VFB_drivers-edit-tmp.owl &&\
	$(ROBOT) merge --input VFB_drivers-annotations.ofn --input ./tmp/VFB_drivers-edit-tmp.owl \
	--include-annotations true --collapse-import-closure false \
	--output VFB_drivers-edit.owl &&\
	echo "\nOntology source file updated!\n" &&\
	rm template.tsv ./tmp/VFB_drivers-edit-tmp.owl

$(ONT).owl: $(ONT)-full.owl
	grep -v owl:versionIRI $< > $@.tmp.owl
	$(ROBOT) annotate -i $@.tmp.owl --ontology-iri http://virtualflybrain.org/data/VFB/OWL/vfb_drivers.owl \
		convert -o $@.tmp.owl && mv $@.tmp.owl $@

LATEST_RELEASE = http://raw.githubusercontent.com/VirtualFlyBrain/vfb-driver-ontology/master/VFB_drivers.owl

tmp/last_released_vfb_drivers.owl:
	wget -O $@ $(LATEST_RELEASE)

reports/robot_diff.txt: tmp/last_released_vfb_drivers.owl $(ONT).owl
	$(ROBOT) diff --left $< --right $(ONT).owl --output $@

$(ONT)-cedar.owl: $(ONT).owl
	$(ROBOT) remove --term http://purl.obolibrary.org/obo/fbbt/vfb/VFBext_0000008 --axioms subclass --signature true --input $(ONT).owl \
	annotate --ontology-iri $(ONTBASE)/$@ $(ANNOTATE_ONTOLOGY_VERSION) \
	--annotation rdfs:comment "This release artefact does not contain the 'has hemidriver' relationships and may not be suitable for most users." \
	-output $@