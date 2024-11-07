import pandas as pd
from oaklib import get_adapter
import re

FBco_data = pd.read_csv('tmp/FBco_data.tsv', sep='\t', low_memory=False)
FBal_data = pd.read_csv('tmp/FBal_data.tsv', sep='\t', low_memory=False)
extra_allele_data = pd.read_csv('tmp/extra_allele_data.tsv', sep='\t', low_memory=False)

FBal_data = pd.concat([FBal_data, extra_allele_data]).drop_duplicates()

# check that each FBco has at least two alleles (rows)
# NB not restricting to exactly two
if len(FBco_data[~FBco_data['combo_id'].duplicated(keep=False)]) > 0:
    raise ValueError('Single allele combinations present:', FBco_data[~FBco_data['combo_id'].duplicated(keep=False)]['combo_id'].to_list())

# drop alleles that are duplicated between FBco_data / FBal_data
FBal_data = FBal_data[~FBal_data['allele_id'].isin(FBco_data['allele_id'])]

# Check that only one label per FBco and FBal
if len(FBco_data[FBco_data['combo_name'].str.contains('\|')]) > 0:
    raise ValueError('Multiple labels for combination:', FBco_data[FBco_data['combo_name'].str.contains('\|')][['combo_id', 'combo_name']])

if len(FBco_data[FBco_data['allele_name'].str.contains('\|')]) > 0:
    raise ValueError('Multiple labels for allele:', FBco_data[FBco_data['allele_name'].str.contains('\|')][['allele_id', 'allele_name']])

if len(FBal_data[FBal_data['allele_name'].str.contains('\|')]) > 0:
    raise ValueError('Multiple labels for allele:', FBal_data[FBal_data['allele_name'].str.contains('\|')][['allele_id', 'allele_name']])

# remove any synonyms that are duplicates of the label
def process_synonyms(object_name: str, synonyms: str):
    """Remove object_name from synonyms if possible, otherwise do nothing."""
    try:
        synonyms = synonyms.split('|')
        synonyms.remove(object_name)
        return '|'.join(synonyms)
    except:
        pass

FBco_data['combo_synonyms'] = FBco_data.apply(lambda x: process_synonyms(x.combo_name, x.combo_synonyms), axis=1)
FBco_data['allele_synonyms'] = FBco_data.apply(lambda x: process_synonyms(x.allele_name, x.allele_synonyms), axis=1)
FBal_data['allele_synonyms'] = FBal_data.apply(lambda x: process_synonyms(x.allele_name, x.allele_synonyms), axis=1)

# replace INTERSECTION with symbol in split names
FBco_data['combo_name'] = FBco_data['combo_name'].map(lambda x: x.replace('INTERSECTION', '∩'))

# merge direct and indirect tools and FBcv terms
def join_direct_and_indirect(allele: str, direct: str, indirect: str):
    try:
        return '|'.join([direct, indirect])
    except TypeError:
        if type(direct) == str:
            return direct
        elif type(indirect) == str:
            return indirect
        else:
            raise ValueError(f'No direct or indirect tools for {allele}')

FBco_data['tool_id'] = FBco_data.apply(lambda x: join_direct_and_indirect(x.allele_id, x.direct_tool_id, x.indirect_tool_id), axis=1)
FBco_data['tool_fbcv'] = FBco_data.apply(lambda x: join_direct_and_indirect(x.allele_id, x.direct_tool_fbcv, x.indirect_tool_fbcv), axis=1)
FBco_data = FBco_data.drop(['direct_tool_id', 'indirect_tool_id', 'direct_tool_fbcv', 'indirect_tool_fbcv'], axis=1)

# remove any FBcv terms that are not SC FBcv_0009027 'split driver fragment'
FBcv_adapter = get_adapter("sqlite:obo:fbcv")
split_IDs = [i for i in FBcv_adapter.descendants('FBcv:0009027')]

def process_split_cv_terms(cv_terms: str, allele_ID: str, ID_list=split_IDs):
    """Keep only FBcv terms that define split components, error if there are none."""
    cv_terms = cv_terms.split('|')
    cv_terms = [c for c in cv_terms if c in ID_list]
    if cv_terms:
        return '|'.join(cv_terms)
    else:
        raise ValueError(f"No valid FBcv terms for {allele_ID}")

FBco_data['tool_fbcv'] = FBco_data.apply(lambda x: process_split_cv_terms(x.tool_fbcv, x.allele_id), axis=1)

# try to choose a symbol for each FBco

symbol_pattern = re.compile('^([A-Z]{2}[0-9]+)[A-Z]?$')
def choose_symbol(synonyms: str):
    """Pick a symbol from the among synonyms if a single suitable synonym exists."""
    try:
        synonyms = synonyms.split('|')
    except AttributeError:
        return ""
    matches = [symbol_pattern.match(s) for s in synonyms if symbol_pattern.match(s)]
    if len(matches)==1:
        return matches[0].group(0)
    elif len(matches)>1:
        matches_shortened = list(set([m.group(1) for m in matches]))
        if len(matches_shortened)==1:
            return matches_shortened[0]
        else:
            return ""
    else:
        return ""

FBco_data['combo_symbol'] = FBco_data.apply(lambda x: choose_symbol(x.combo_synonyms), axis=1)

FBco_data.to_csv('tmp/FBco_data_processed.tsv', sep='\t', index=None)
FBal_data.to_csv('tmp/FBal_data_processed.tsv', sep='\t', index=None)
