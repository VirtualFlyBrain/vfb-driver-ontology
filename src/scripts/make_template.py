import pandas as pd
from collections import OrderedDict


FB_data = pd.read_csv('tmp/FB_data_processed.tsv', sep='\t', low_memory=False)

FBco_data = FB_data[['combo_id', 'combo_name', 'combo_symbol', 'combo_synonyms', 'allele_id']]
FBco_data = FBco_data.rename(columns={'combo_id':'ID', 'combo_name':'Name', 'combo_symbol': 'Symbol', 'combo_synonyms':'Synonyms', 'allele_id':'Hemidriver'})
FBco_data['Parent'] = 'VFBext:0000010'
FBco_data['TYPE'] = 'owl:Class'
FBco_data['Xref'] = 'FlyBase'

FBal_data = FB_data[['allele_id', 'allele_name', 'allele_synonyms', 'tool_fbcv']]
FBal_data = FBal_data.rename(columns={'allele_id':'ID', 'allele_name':'Name', 'allele_synonyms':'Synonyms', 'tool_fbcv':'Parent'})
FBal_data['TYPE'] = 'owl:Class'
FBal_data['Xref'] = 'FlyBase'

template_header = pd.DataFrame({'ID':['ID'], 'TYPE': ['TYPE'], 
                        "Name": ["A rdfs:label SPLIT=|"],
                        "Definition": ["A IAO:0000115"],
                        "Synonyms": ["A oboInOwl:hasExactSynonym SPLIT=|"],
                        "Symbol": ["A IAO:0000028"], "Parent": ["C % SPLIT=|"],
                        "Hemidriver": ["C VFBext:0000008 some %"],
                        "Xref": ["A oboInOwl:hasDbXref"]})

template = pd.concat([template_header, FBco_data, FBal_data], ignore_index=True)

template.to_csv('tmp/template.tsv', sep='\t', index=None)
