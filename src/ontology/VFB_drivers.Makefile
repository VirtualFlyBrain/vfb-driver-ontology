## Customize Makefile settings for VFB_drivers
##
## If you need to customize your Makefile, make
## changes here rather than in the main Makefile

.PHONY: prepare_release
prepare_release: all $(ONT)-cedar.owl $(REPORTDIR)/robot_diff.txt
	rsync -R $(RELEASE_ASSETS) $(ONT)-cedar.owl $(RELEASEDIR) &&\
	rm -f $(CLEANFILES) &&\
	echo "Release files are now in $(RELEASEDIR) - now you should commit, push and make a release on your git hosting site such as GitHub or GitLab"

CLEANFILES:=$(CLEANFILES) $(ONT)-cedar.owl $(IMPORTDIR)/*_terms_combined.txt

.PHONY: get_FB_hemidrivers
get_FB_hemidrivers: $(TMPDIR)
	# get hemidriver data from public chado
	apt-get update
	apt-get -y install postgresql-client
	psql -h chado.flybase.org -U flybase flybase -f ../sql/hemidrivers.sql > $(TMPDIR)/hemidrivers.tsv

.PHONY: update_ontology
update_ontology: get_FB_hemidrivers
	python3 -m pip install -r $(SCRIPTSDIR)/requirements.txt && \
	python3 $(SCRIPTSDIR)/update_ontology.py &&\
	$(ROBOT) template \
	--template properties_template.tsv \
	--output $(TMPDIR)/VFB_drivers-properties-tmp.owl &&\
	$(ROBOT) template \
	--input $(TMPDIR)/VFB_drivers-properties-tmp.owl \
	--template template.tsv \
	--output $(TMPDIR)/VFB_drivers-classes-tmp.owl &&\
	$(ROBOT) merge \
	--input VFB_drivers-annotations.ofn \
	--input $(TMPDIR)/VFB_drivers-properties-tmp.owl \
	--input $(TMPDIR)/VFB_drivers-classes-tmp.owl \
	--include-annotations true --collapse-import-closure false \
	--output VFB_drivers-edit.owl &&\
	echo "\nOntology source file updated!\n"
	rm template.tsv properties_template.tsv $(TMPDIR)/VFB_drivers-properties-tmp.owl $(TMPDIR)/VFB_drivers-classes-tmp.owl

$(ONT).owl: $(ONT)-full.owl
	grep -v owl:versionIRI $< > $@.tmp.owl
	$(ROBOT) annotate -i $@.tmp.owl --ontology-iri http://virtualflybrain.org/data/VFB/OWL/vfb_drivers.owl \
		convert -o $@.tmp.owl && mv $@.tmp.owl $@

LATEST_RELEASE = http://raw.githubusercontent.com/VirtualFlyBrain/vfb-driver-ontology/master/VFB_drivers.owl

$(TMPDIR)/last_released_vfb_drivers.owl:
	wget -O $@ $(LATEST_RELEASE)

reports/robot_diff.txt: $(TMPDIR)/last_released_vfb_drivers.owl $(ONT).owl
	$(ROBOT) diff --left $< --right $(ONT).owl --output $@

$(ONT)-cedar.owl: $(ONT).owl
	$(ROBOT) remove --term http://purl.obolibrary.org/obo/fbbt/vfb/VFBext_0000008 --axioms subclass --signature true --input $(ONT).owl \
	annotate --ontology-iri $(ONTBASE)/$@ $(ANNOTATE_ONTOLOGY_VERSION) \
	--annotation rdfs:comment "This release artefact does not contain the 'has hemidriver' relationships and may not be suitable for most users." \
	-output $@