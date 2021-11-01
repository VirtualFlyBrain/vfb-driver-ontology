## Customize Makefile settings for VFB_drivers
## 
## If you need to customize your Makefile, make
## changes here rather than in the main Makefile


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
	

