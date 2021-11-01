#!/usr/bin/env python
# coding: utf-8

from vfb_connect.neo.neo4j_tools import Neo4jConnect, dict_cursor
import pandas as pd
from collections import OrderedDict
import json

nc = Neo4jConnect('http://pdb.virtualflybrain.org', 'neo4j', 'neo4j')

query = ("MATCH (s:Split:Class) OPTIONAL MATCH (s)-[:has_hemidriver]->(h) "
         "RETURN DISTINCT s.label, s.iri, s.has_exact_synonym, s.description, COLLECT(h.iri)")
q = nc.commit_list([query])
splits = dict_cursor(q)
splits_df = pd.DataFrame.from_dict(splits)

query = "MATCH (s:Split:Class)-[:has_hemidriver]->(h) RETURN DISTINCT h.label, h.iri, h.synonyms"
q = nc.commit_list([query])
hemidrivers = dict_cursor(q)
hemidrivers_df = pd.DataFrame.from_dict(hemidrivers)

# ROBOT template columns
template_seed = OrderedDict([('ID' , 'ID'), ('TYPE' , 'TYPE' )])

#label, description, synonyms:
template_seed.update([("Name" , "A rdfs:label"), ("Definition" , "A IAO:0000115"), ("Synonyms" , "A oboInOwl:hasExactSynonym SPLIT=|")])

# Relationships:
template_seed.update([("Parent" , "C %"), ("Hemidrivers" , "C has_hemidriver some % SPLIT=|")])

# Create dataFrame for template
template = pd.DataFrame.from_records([template_seed])


#add relationship
row_od = OrderedDict([]) #new template row as an empty ordered dictionary
for c in template.columns: #make columns and blank data for new template row
    row_od.update([(c , "")])

row_od["TYPE"] = "owl:ObjectProperty"
row_od["ID"] = "http://purl.obolibrary.org/obo/fbbt/vfb/VFBext_0000008"
row_od["Name"] = "has_hemidriver"

#make new row into a DataFrame and add it to template
new_row = pd.DataFrame.from_records([row_od])
template = pd.concat([template, new_row], ignore_index=True, sort=False)

# add rows for splits
for i in splits_df.index:

    row_od = OrderedDict([]) #new template row as an empty ordered dictionary
    for c in template.columns: #make columns and blank data for new template row
        row_od.update([(c , "")])
    
    #these are the same in each row
    row_od["TYPE"] = "owl:Class"
    row_od["Parent"] = "http://purl.obolibrary.org/obo/fbbt/vfb/VFBext_0000010"

    #easy to generate data
    row_od["ID"] = splits_df["s.iri"][i]
    row_od["Definition"] = splits_df["s.description"][i][0]
    row_od["Name"] = splits_df["s.label"][i]
    row_od["Hemidrivers"] = '|'.join(splits_df["COLLECT(h.iri)"][i])
    
    #synonyms - if not None
    try:
        synonyms = json.loads(splits_df["s.has_exact_synonym"][i][0])
        row_od["Synonyms"] = synonyms['value']
    except TypeError:
        pass
    
    #make new row into a DataFrame and add it to template
    new_row = pd.DataFrame.from_records([row_od])
    template = pd.concat([template, new_row], ignore_index=True, sort=False)

# add rows for hemidrivers
for i in hemidrivers_df.index:

    row_od = OrderedDict([]) #new template row as an empty ordered dictionary
    for c in template.columns: #make columns and blank data for new template row
        row_od.update([(c , "")])
    
    #these are the same in each row
    row_od["TYPE"] = "owl:Class"
    row_od["Parent"] = "http://purl.obolibrary.org/obo/SO_0000110"

    #easy to generate data
    row_od["ID"] = hemidrivers_df["h.iri"][i]
    row_od["Name"] = hemidrivers_df["h.label"][i]
    
    #synonyms - if not None
    try:
        row_od["Synonyms"] = '|'.join(hemidrivers_df["h.synonyms"][i])
    except TypeError:
        pass

    #make new row into a DataFrame and add it to template
    new_row = pd.DataFrame.from_records([row_od])
    template = pd.concat([template, new_row], ignore_index=True, sort=False)

template.to_csv('template.tsv', sep='\t', index=False)
