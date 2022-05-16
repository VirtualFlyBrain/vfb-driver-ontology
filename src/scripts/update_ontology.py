#!/usr/bin/env python
# coding: utf-8

from vfb_connect.neo.neo4j_tools import Neo4jConnect, dict_cursor
import pandas as pd
import numpy as np
import json
from collections import OrderedDict

# NB: KB may contain some new classes not in PDB
# KB does not have all classes in PDB
# KB does not have all synonyms in PDB
# KB could have some classes maked as obsolete that are not obsolete in PDB

kb = Neo4jConnect('http://kb.virtualflybrain.org', 'neo4j', 'neo4j')
pdb = Neo4jConnect('http://pdb-dev.virtualflybrain.org', 'neo4j', 'neo4j')

def get_all_drivers(server):
    """
    Input is a Neo4jConnect object corresponding to a VFB server.
    Output is three dataframes:
      [0] :Split classes
      [1] hemidrivers that comprise the :Split classes
      [2] 'FBti' and 'FBtp' classes
    """
    iep = "http://purl.obolibrary.org/obo/fbbt/vfb/VFBext_0000010"
    hh = "http://purl.obolibrary.org/obo/fbbt/vfb/VFBext_0000008"

    def synonym_fix(x):
        """Fixes oddly-formatted synonyms."""
        if type(x) == list and len(x) > 0:
            try:
                synonyms = []
                for i in x:
                    syn = json.loads(i)
                    synonyms.append(syn['value'])
                return synonyms
            except:
                return x
        else:
            return x

    # splits
    query = ("MATCH (c)-[:SUBCLASSOF]->(iep) WHERE iep.iri = \"%s\" "
             "OPTIONAL MATCH (c)-[r]->(h) WHERE r.iri = \"%s\" "
             "OPTIONAL MATCH (c)-[x:database_cross_reference]->"
             "(:Site {short_form:\"FlyLightSplit\"}) "
             "RETURN c.iri, c.label, c.has_exact_synonym, "
             "c.synonyms, x.accession, c.description, c.deprecated, "
             "COLLECT(h.iri)"
             % (iep, hh))
    q = server.commit_list([query])
    splits = dict_cursor(q)
    splits_df = pd.DataFrame.from_dict(splits)
    splits_df.set_index('c.iri', inplace=True)
    splits_df['c.has_exact_synonym'] = splits_df['c.has_exact_synonym'].apply(synonym_fix)
    splits_df['c.synonyms'] = splits_df['c.synonyms'].apply(synonym_fix)

    # hemidrivers
    query = ("MATCH (c)<-[r]-(s)-[:SUBCLASSOF]->(iep) WHERE iep.iri = \"%s\" "
             "AND r.iri = \"%s\" "
             "RETURN DISTINCT c.iri, c.label, c.has_exact_synonym, "
             "c.synonyms, c.deprecated"
             % (iep, hh))
    q = server.commit_list([query])
    hemidrivers = dict_cursor(q)
    hemidrivers_df = pd.DataFrame.from_dict(hemidrivers)
    hemidrivers_df.set_index('c.iri', inplace=True)
    hemidrivers_df['c.has_exact_synonym'] = hemidrivers_df['c.has_exact_synonym'].apply(synonym_fix)
    hemidrivers_df['c.synonyms'] = hemidrivers_df['c.synonyms'].apply(synonym_fix)

    # features
    query = ("MATCH (c:Feature) WHERE c.iri CONTAINS \"FBti\" "
             "RETURN DISTINCT c.iri, c.label, c.synonyms, "
             "c.has_exact_synonym, c.deprecated")
    q = server.commit_list([query])
    features_1 = dict_cursor(q)
    features_1_df = pd.DataFrame.from_dict(features_1)

    query = ("MATCH (c:Feature) WHERE c.iri CONTAINS \"FBtp\" "
             "RETURN DISTINCT c.iri, c.label, c.synonyms, "
             "c.has_exact_synonym, c.deprecated")
    q = server.commit_list([query])
    features_2 = dict_cursor(q)
    features_2_df = pd.DataFrame.from_dict(features_2)

    features_df = pd.concat([features_1_df, features_2_df], ignore_index = True)
    features_df = features_df[~features_df["c.iri"].isin(hemidrivers_df.index)]
    features_df.set_index('c.iri', inplace=True)
    features_df['c.has_exact_synonym'] = features_df['c.has_exact_synonym'].apply(synonym_fix)
    features_df['c.synonyms'] = features_df['c.synonyms'].apply(synonym_fix)

    return splits_df, hemidrivers_df, features_df

KB_drivers = get_all_drivers(kb)
PDB_drivers = get_all_drivers(pdb)

def update_old_driver_df(df_old, df_new, obs_col):
    """Add rows of new_df to old_df, then remove obsoletes in obs_col.
    IDs should be indices of dfs."""
    df_old.update(df_new, overwrite=False) # update PDB NAs with KB values

    to_add = df_new[~df_new.index.isin(df_old.index)]
    df_updated = pd.concat([df_old, to_add])

    # obs_col will either be NA or list of boolean(s)
    def process_obs_col(x):
        if type(x)==list:
            if True in x:
                return True
            else:
                return False
        else:
            return False

    df_updated[obs_col] = df_updated[obs_col].apply(process_obs_col)
    df_updated_no_obsoletes = df_updated[df_updated[obs_col]==False]
    return df_updated_no_obsoletes

splits_df_combined = update_old_driver_df(PDB_drivers[0], KB_drivers[0], 'c.deprecated')
hemidrivers_df_combined = update_old_driver_df(PDB_drivers[1], KB_drivers[1], 'c.deprecated')
features_df_combined = update_old_driver_df(PDB_drivers[2], KB_drivers[2], 'c.deprecated')

# ROBOT template columns
template_seed = OrderedDict([('ID' , 'ID'), ('TYPE' , 'TYPE' )])

#label, description, synonyms:
template_seed.update([("Name" , "A rdfs:label"),
                      ("Definition" , "A IAO:0000115"),
                      ("Synonyms" , "A oboInOwl:hasExactSynonym SPLIT=|"),
                      ("Symbol" , "A IAO:0000028")])

# Relationships:
template_seed.update([("Parent" , "C %"),
                      ("Hemidrivers" , "C has_hemidriver some % SPLIT=|")])

# Create dataFrame for template
template = pd.DataFrame.from_records([template_seed])

#add row for has_hemidriver relationship
row_od = OrderedDict([]) #new template row as an empty ordered dictionary
for c in template.columns: #make columns and blank data for new template row
    row_od.update([(c , "")])

row_od["TYPE"] = "owl:ObjectProperty"
row_od["ID"] = "http://purl.obolibrary.org/obo/fbbt/vfb/VFBext_0000008"
row_od["Name"] = "has_hemidriver"

#make new row into a DataFrame and add it to template
new_row = pd.DataFrame.from_records([row_od])
template = pd.concat([template, new_row], ignore_index=True, sort=False)

#add row for symbol AP
row_od = OrderedDict([]) #new template row as an empty ordered dictionary
for c in template.columns: #make columns and blank data for new template row
    row_od.update([(c , "")])

row_od["TYPE"] = "owl:AnnotationProperty"
row_od["ID"] = "http://purl.obolibrary.org/obo/IAO_0000028"
row_od["Name"] = "symbol"

#make new row into a DataFrame and add it to template
new_row = pd.DataFrame.from_records([row_od])
template = pd.concat([template, new_row], ignore_index=True, sort=False)


def add_template_rows(template, data, dataframe, parent_class, hemidrivers=False):
    problems = []
    for i in dataframe.index:
        try:
            row_od = OrderedDict([]) #new template row as an empty ordered dictionary
            for c in template.columns: #make columns and blank data for new template row
                row_od.update([(c , "")])

            # these are the same in each row
            row_od["TYPE"] = "owl:Class"
            row_od["Parent"] = parent_class

            # easy to generate data
            row_od["ID"] = i
            row_od["Name"] = dataframe["c.label"][i]
            if "c.description" in dataframe.columns:
                row_od["Definition"] = dataframe["c.description"][i][0]
            if hemidrivers:
                row_od["Hemidrivers"] = '|'.join(dataframe["COLLECT(h.iri)"][i])

            # synonyms - if any
            esyn = dataframe["c.has_exact_synonym"][i]
            syns = dataframe["c.synonyms"][i]
            if type(esyn)==list and esyn:
                row_od["Synonyms"] = '|'.join(esyn)
                if type(syns)==list and syns:
                    row_od["Synonyms"] += '|' + '|'.join(syns)
            elif type(syns)==list and syns:
                row_od["Synonyms"] = '|'.join(syns)

            # Symbol - if any
            try:
                row_od["Symbol"] = dataframe["x.accession"][i][0]
            except:
                pass

            # make new row into a DataFrame and add it to template
            new_row = pd.DataFrame.from_records([row_od])
            template = pd.concat([template, new_row], ignore_index=True, sort=False)
        except:
            print("WARNING could not create template row for %s" % i)
            problems.append(i)
    if problems:
        print("WARNING %s classes could not be created for %s." % (len(set(problems)), data))
    else:
        print("All classes created successfully for %s." % data)
    return template

template = add_template_rows(template, 'splits', splits_df_combined, 'http://purl.obolibrary.org/obo/fbbt/vfb/VFBext_0000010', True)
template = add_template_rows(template, 'hemidrivers', hemidrivers_df_combined, 'http://purl.obolibrary.org/obo/SO_0000110', False)
template = add_template_rows(template, 'features', features_df_combined, 'http://purl.obolibrary.org/obo/SO_0000110', False)

template.to_csv('template.tsv', sep='\t', index=False)
