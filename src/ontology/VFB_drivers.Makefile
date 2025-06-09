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

.PHONY: get_flybase_data
get_flybase_data: | $(TMPDIR)
	apt-get update
	apt-get -y install postgresql-client
	psql -h chado.flybase.org -U flybase flybase -f ../sql/FBco_query.sql > $(TMPDIR)/FBco_data.tsv
	psql -h chado.flybase.org -U flybase flybase -f ../sql/expression_allele_query.sql > $(TMPDIR)/FBal_data.tsv
	python3 $(SCRIPTSDIR)/print_extra_allele_query.py &&\
	psql -h chado.flybase.org -U flybase flybase -f ../sql/extra_allele_query.sql > $(TMPDIR)/extra_allele_data.tsv

$(TMPDIR)/template.tsv: | $(TMPDIR)
	python3 $(SCRIPTSDIR)/process_FB_data.py &&\
	python3 $(SCRIPTSDIR)/make_template.py

$(SRC): get_flybase_data $(TMPDIR)/template.tsv
	$(ROBOT) template \
	--merge-before \
	--input VFB_drivers-annotations.ofn \
	--prefix "FlyBase: http://flybase.org/reports/" \
	--prefix "VFBext: http://purl.obolibrary.org/obo/fbbt/vfb/VFBext_" \
	--template $(TMPDIR)/template.tsv \
	--include-annotations true \
	--collapse-import-closure false \
	convert -f ofn \
	--output $@ &&\
	echo "\nOntology source file updated!\n"

$(ONT).owl: $(ONT)-full.owl
	grep -v owl:versionIRI $< > $@.tmp.owl
	$(ROBOT) annotate -i $@.tmp.owl --ontology-iri http://virtualflybrain.org/data/VFB/OWL/VFB_drivers.owl \
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